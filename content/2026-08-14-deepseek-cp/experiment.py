#!/usr/bin/env python3
"""
「切了会坏」模拟器 — 验证 DeepSeek-V4 两阶段 CP 的正确性。

模拟 packed sequences（多序列打包，长度不均）切成 8 个 CP rank 后：
- 朴素 CP：各 rank 只压本地完整块 → 跨 rank 边界的压缩块消失（缺块），
  段首残块还可能和后续 token 凑成基准中不存在的块（错块）
- 两阶段 CP：阶段1 边界原料交换 + 阶段2 all-gather + select-and-pad → 与单卡基准完全一致（对）

压缩模型：m 个连续 KV entry 压成 1 个 entry（指纹求和），压缩必须落在同一序列内，
序列尾部不足 m 的 token 丢弃（不产生 compressed KV）。

纯 Python 无依赖。断言驱动：E_two == E_ref 必须成立，E_naive != E_ref 必须成立。
"""

import random

# ── 可调参数 ──
K = 8                    # CP ranks（V4 长上下文训练配置，同 parallel 篇口径）
TOKENS_PER_RANK = 140    # 每 rank 连续 token 数 s
M_CSA = 4                # CSA 压缩比（V4-Pro config.json compress_ratios）
M_HCA = 128              # HCA 压缩比（V4-Pro config.json compress_ratios）
SEQ_LEN_RANGE = (37, 210)  # packed 序列长度范围（故意不均，制造尾部残块）


def gen_packed_stream(rng, total_tokens):
    """生成 packed token 流 + 序列边界标记。返回 (tokens, seq_ids)。"""
    tokens, seq_ids = [], []
    sid = 0
    while len(tokens) < total_tokens:
        ln = rng.randint(*SEQ_LEN_RANGE)
        tokens += [rng.randint(0, 99) for _ in range(ln)]
        seq_ids += [sid] * ln
        sid += 1
    return tokens[:total_tokens], seq_ids[:total_tokens]


def compress_stream(tokens, seq_ids, m, skip_head=0):
    """按序列边界压缩：每序列内 m 个连续 KV entry → 1 个（指纹求和）。尾残块丢弃。

    skip_head：段首前几个 token 属于跨边界的压缩块（右半），不参与本地压缩。
    返回 (entries, boundaries)：entries 是 compressed entry 列表；
    boundaries 记录每个 entry 覆盖的 token 范围 [start, end)，用于断言比对。
    """
    entries, boundaries = [], []
    i, n = skip_head, len(tokens)
    while i < n:
        if i + m <= n and seq_ids[i] == seq_ids[i + m - 1]:
            entries.append(sum(tokens[i:i + m]))
            boundaries.append((i, i + m))
            i += m
        else:
            i += 1  # 尾残块或跨序列残块：丢弃
    return entries, boundaries


# ══════════════════════════════════════════════════════════════
# 三种做法
# ══════════════════════════════════════════════════════════════

def baseline(tokens, seq_ids, m):
    """单卡基准：整条流在单卡上按序列边界压缩。"""
    return compress_stream(tokens, seq_ids, m)


def naive_cp(tokens, seq_ids, m, k):
    """朴素 CP：每 rank 只压自己段内的完整块，跨 rank 边界块丢失或错位。"""
    n = len(tokens)
    s = n // k
    entries, boundaries = [], []
    for r in range(k):
        seg_tokens = tokens[r * s:(r + 1) * s]
        seg_seqs = seq_ids[r * s:(r + 1) * s]
        e, b = compress_stream(seg_tokens, seg_seqs, m)
        entries += e
        boundaries += [(r * s + x, r * s + y) for x, y in b]
    return entries, boundaries


def two_stage_cp(tokens, seq_ids, m, k):
    """两阶段 CP：阶段1 边界原料交换 + 阶段2 all-gather + select-and-pad。

    阶段1：跨边界的序列块，其「左尾残块」由左侧 rank 交给右侧 rank（原料），
           右侧 rank 与本地开头拼成完整块压缩——右侧是最终产出者。
    阶段2：各 rank 产出本地压缩 KV（pad 到统一上界）→ all-gather →
           select-and-pad 去 padding、尾对齐 → 全局 entry 序列。
    """
    n = len(tokens)
    s = n // k

    # ── 阶段1：找出每个边界的跨边界块，计算补块需求 ──
    # need[r] = 左尾贡献的 token 数 lm（0<lm<m 时需补，None 表示无需补）
    need = [None] * (k - 1)
    for r in range(k - 1):
        b = (r + 1) * s
        if seq_ids[b - 1] != seq_ids[b]:
            continue  # 边界两侧不同序列，无跨边界块
        l = 0  # 左尾连续同序列 token 数
        while b - 1 - l >= 0 and seq_ids[b - 1 - l] == seq_ids[b - 1]:
            l += 1
        lm = l % m
        if lm != 0:
            need[r] = lm  # 左尾贡献 lm 个，右头需补 m-lm 个

    # ── 阶段1 执行：右侧 rank 承接跨边界块 ──
    extra = [[] for _ in range(k)]   # 每 rank 承接的跨边界块 (sum, start, end)
    skip_head = [0] * k              # 每 rank 段首属于跨边界块右半的 token 数
    for r in range(k - 1):
        lm = need[r]
        if lm is None:
            continue
        b = (r + 1) * s
        need_right = m - lm
        # 右头必须足够且同序列；不足则左尾残块与右头残块合计 < m，基准中同样丢弃
        if b + need_right <= n and seq_ids[b] == seq_ids[b + need_right - 1]:
            blk = tokens[b - lm:b] + tokens[b:b + need_right]
            extra[r + 1].append((sum(blk), b - lm, b + need_right))
            skip_head[r + 1] = need_right

    # ── 阶段2：本地压缩 + pad + all-gather + select-and-pad ──
    local_entries = []   # 每 rank: (compressed, start, end)
    for r in range(k):
        seg_tokens = tokens[r * s:(r + 1) * s]
        seg_seqs = seq_ids[r * s:(r + 1) * s]
        e, b = compress_stream(seg_tokens, seg_seqs, m, skip_head=skip_head[r])
        loc = [(v, r * s + x, r * s + y) for v, (x, y) in zip(e, b)]
        loc += extra[r]  # 承接的跨边界块
        loc.sort(key=lambda x: x[1])  # 按 token 起始位置排序（跨边界块在段首之前）
        local_entries.append(loc)
    max_len = max(len(x) for x in local_entries) or 1
    padded = [x + [None] * (max_len - len(x)) for x in local_entries]
    # all-gather：每个 rank 拿到 k 行 × padded_len 的 blob（此处模拟单 rank 视图）
    gathered = list(zip(*padded))
    # select-and-pad：去 padding、尾对齐。
    # 拼接顺序是 rank-major（rank 0 全部 valid → rank 1 全部 valid → …），
    # 与每 rank 内部按位置排序叠加 = 全局 token 顺序；padding 集中在尾部。
    valid = [v for row in padded for v in row if v is not None]
    return [v[0] for v in valid], [(v[1], v[2]) for v in valid]


def report(rng, m, label):
    n = K * TOKENS_PER_RANK
    tokens, seq_ids = gen_packed_stream(rng, n)

    e_ref, b_ref = baseline(tokens, seq_ids, m)
    e_nv, b_nv = naive_cp(tokens, seq_ids, m, K)
    e_ts, b_ts = two_stage_cp(tokens, seq_ids, m, K)

    ok_ts = e_ts == e_ref
    ok_nv = e_nv != e_ref
    diff = len(e_ref) - len(e_nv)
    sign = "缺" if diff > 0 else ("多" if diff < 0 else "持平")

    print(f"── {label}（m={m}，{K} ranks × {TOKENS_PER_RANK} tokens，{len(set(seq_ids))} 个 packed 序列）──")
    print(f"  单卡基准 compressed entries : {len(e_ref)}")
    print(f"  朴素 CP  entries            : {len(e_nv)}（{sign} {abs(diff)} 个，跨边界块丢失/错位）")
    print(f"  两阶段 CP entries           : {len(e_ts)}（含 select-and-pad 去 padding）")
    print(f"  断言 两阶段 == 单卡基准     : {'✅ PASS' if ok_ts else '❌ FAIL'}")
    print(f"  断言 朴素   != 单卡基准     : {'✅ PASS' if ok_nv else '❌ FAIL'}")
    if not ok_ts:
        for i, (a, b) in enumerate(zip(e_ts, e_ref)):
            if a != b:
                print(f"    首个不一致 @ entry {i}: 两阶段={a} 基准={b}")
                break
    return ok_ts and ok_nv, len(e_ref), len(e_nv), len(e_ts)


def select_and_pad_demo():
    """正文用的小例子：cp_size=2, m=4，展示 pad → all-gather → select-and-pad。"""
    rank0 = ["C0"]                                      # 本地产出 1 个
    rank1 = ["C1", "C2", "C3"]                          # 承接跨边界块后 3 个
    max_len = 4
    padded = [rank0 + ["PAD"] * (max_len - len(rank0)),
              rank1 + ["PAD"] * (max_len - len(rank1))]
    gathered = list(zip(*padded))
    valid = [v for row in padded for v in row if v != "PAD"]
    print("── select-and-pad 演示（cp_size=2, m=4）──")
    print("  Rank 0 sends: [C0, PAD, PAD, PAD]    valid_count = 1")
    print("  Rank 1 sends: [C1, C2, C3, PAD]    valid_count = 3")
    print("  gathered  = 2 × 4 × d_KV 的整齐 blob（每个 rank 持有一份，但有洞）")
    print(f"  select-and-pad 后 valid entries = {valid}")
    return len(valid) == 4


def comm_ledger():
    """通信量账（正文第 6 节）：V4-Pro 真实口径，1M 序列、CP=8、每 rank 125K token。"""
    T = 1_000_000
    K_ = 8
    per_rank = T // K_
    KV_ENTRY_B = 576   # 64 维 RoPE BF16(128B) + 448 维 FP8(448B)，parallel 篇口径
    M_CSA, M_HCA = 4, 128

    s1_csa = M_CSA * KV_ENTRY_B
    s1_hca = M_HCA * KV_ENTRY_B
    s2_csa = per_rank / M_CSA * KV_ENTRY_B
    s2_hca = per_rank / M_HCA * KV_ENTRY_B
    s2_avg = (s2_csa + s2_hca) / 2
    raw = per_rank * KV_ENTRY_B

    print("── 通信量账（1M 序列 · CP=8 · 每 rank 125K token · KV entry 576B）──")
    print(f"  阶段1 边界原料：CSA 层 {s1_csa/1e3:.1f} KB | HCA 层 {s1_hca/1e3:.0f} KB（与序列长度 T 无关）")
    print(f"  阶段2 all-gather 分片：CSA 层 {s2_csa/1e6:.0f} MB | HCA 层 {s2_hca/1e6:.2f} MB | 平均 ≈{s2_avg/1e6:.0f} MB/层")
    print(f"  假想 all-gather 未压缩 KV：{raw/1e6:.0f} MB/层")
    print(f"  压缩节省：平均 ≈{raw/s2_avg:.0f} 倍 | HCA 层 ≈{raw/s2_hca:.0f} 倍 | CSA 层 ≈{raw/s2_csa:.0f} 倍")
    return raw / s2_avg


def main():
    rng = random.Random(42)
    all_ok = True
    all_ok &= select_and_pad_demo()
    print()
    ok, *_ = report(rng, M_CSA, "CSA 场景")
    all_ok &= ok
    print()
    ok, *_ = report(rng, M_HCA, "HCA 场景")
    all_ok &= ok
    print()
    comm_ledger()
    print()
    print("✅ 全部断言通过：两阶段 CP 与单卡基准一致，朴素 CP 确实『切了会坏』。" if all_ok
          else "❌ 存在失败断言，请检查模拟器实现。")


if __name__ == "__main__":
    main()
