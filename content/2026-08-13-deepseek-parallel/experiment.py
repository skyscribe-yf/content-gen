#!/usr/bin/env python3
"""
并行账本计算器 — DeepSeek-V4-Pro 五维并行策略的显存与通信量估算。

纯 Python 无依赖。所有常量标注来源（V4 技术报告 §4.2.1 / §3.1 / §3.4.3、
V3 技术报告 §3.5、HF config.json），输出三张可直接进正文的表格。

口径说明（重要假设）：
- 长上下文训练场景：序列 1M token、CP=8 → 每 rank 125K token。
- EP 通信：dispatch FP8(1B) + combine BF16(2B)，每 token topk=6 个专家对；
  通信量按每 rank 的 token 数计（EP 组 64 路，token 均摊）。
- CP 通信：阶段2 all-gather 每 rank 发送自己的本地压缩 KV 分片；
  KV entry 576B（64 维 BF16 + 448 维 FP8）；CSA/HCA 交错近似各半。
- DP：梯度同步按 PP×EP 分片后每卡持有参数（1.6T/1024）计，all-reduce 系数 ×2。
- IB 取 V3 披露的 50GB/s（400Gbps）作时间账，正文注明 V4 实际带宽未披露。
"""

# ── V4-Pro 模型配置（V4 报告 §4.2.1 + HF config.json）──
N_LAYER = 61
HIDDEN = 7168
N_ROUTED = 384          # 路由专家（另有 1 个共享专家）
TOP_K = 6
INTER_DIM = 3072        # 专家中间维度
TOTAL_PARAMS = 1.6e12   # 1.6T 总参数
ACTIVE_PARAMS = 49e9    # 每 token 激活 49B

# ── 精度与字节 ──
FP8_B = 1.0             # 字节/元素
BF16_B = 2.0
FP32_B = 4.0
FP4_B = 0.5             # MXFP4 专家权重（后训练 FP4-QAT，08-09 篇）

# KV entry 尺寸（V4 §2.3.3：RoPE 64 维 BF16 + 其余 FP8；KV 共享单流 512 维）
KV_ENTRY_B = 64 * BF16_B + (512 - 64) * FP8_B   # 576 B/entry
CSA_M = 4               # CSA 压缩率
HCA_MP = 128            # HCA 压缩率

# ── 硬件与并行配置（V3 报告披露：2048×H800；V4 继承框架）──
H800_MEM_GB = 80
NV_LINK_GBS = 900       # 8 卡节点内
IB_GBS = 50             # 跨节点 400Gbps
PP_SIZE = 16            # V3 披露（V4 继承，§3.4「built upon V3」）
EP_SIZE = 64
CP_SIZE = 8             # V4 长上下文训练
TP_SIZE = 1             # V4 关闭 TP
DP_TOTAL = 128          # = EP 64 × 副本 2（V3 口径）
CARDS = PP_SIZE * DP_TOTAL   # 2048

SEQ_1M = 1_000_000
TOKENS_PER_RANK = SEQ_1M // CP_SIZE   # 125K

def gb(x): return x / 1e9

def mem_ledger():
    """表 1：显存账 — 1.6T 参数推理/训练各要多少块 H800。"""
    rows = []
    # 推理 1：全 FP8（1B/参数）
    w_fp8 = TOTAL_PARAMS * FP8_B
    rows.append(("推理：全 FP8 权重", w_fp8, w_fp8 / H800_MEM_GB / 1e9))
    # 推理 2：FP4 专家（1.55T×0.5B）+ dense FP8（~50B×1B）——FP4-QAT 篇部署口径
    exp_per_layer = N_ROUTED * (2 * INTER_DIM * HIDDEN + HIDDEN * INTER_DIM)  # w1/w3 + w2
    dense = TOTAL_PARAMS - exp_per_layer * N_LAYER
    w_deploy = dense * FP8_B + exp_per_layer * N_LAYER * FP4_B
    rows.append(("推理：FP4 专家 + FP8 其余（部署口径）", w_deploy, w_deploy / H800_MEM_GB / 1e9))
    # 训练：PP×EP 分片后每卡状态（1.6T/1024 参数）
    per_card_params = TOTAL_PARAMS / (PP_SIZE * EP_SIZE)
    state_per_card = per_card_params * (FP8_B + FP8_B + FP32_B + FP32_B)  # 权重+梯度+master+动量
    rows.append(("训练：PP×EP 分片后每卡状态（权重+梯度+master+动量）", state_per_card, state_per_card / H800_MEM_GB / 1e9))
    return rows, per_card_params

def ep_comm_per_layer(tokens):
    """EP：每 MoE 层 all-to-all 字节 = tokens×topk×(dispatch FP8 1B + combine BF16 2B)。"""
    return tokens * TOP_K * HIDDEN * (FP8_B + BF16_B)

def cp_comm_per_layer():
    """CP 阶段2：all-gather 每 rank 发送本地压缩 KV 分片（CSA/HCA 交错各半）。"""
    csa = (TOKENS_PER_RANK / CSA_M) * KV_ENTRY_B
    hca = (TOKENS_PER_RANK / HCA_MP) * KV_ENTRY_B
    return (csa + hca) / 2

def pp_comm_per_microbatch(micro_tokens):
    """PP：stage 边界激活传递 = tokens×hidden×2B。"""
    return micro_tokens * HIDDEN * BF16_B

def dp_comm_per_step(per_card_params):
    """DP：每 step 梯度 all-reduce = 每卡梯度 ×2（all-reduce 系数）。"""
    return per_card_params * FP8_B * 2

def comm_ledger(per_card_params):
    """表 2：1M 上下文下通信量对比（每 rank 125K token，同口径）。"""
    ep = ep_comm_per_layer(TOKENS_PER_RANK)
    cp = cp_comm_per_layer()
    pp = pp_comm_per_microbatch(TOKENS_PER_RANK)
    dp = dp_comm_per_step(per_card_params)
    rows = [
        ("EP 专家并行（all-to-all）", ep, "每 MoE 层", "IB 跨节点", ep / IB_GBS / 1e9),
        ("CP 上下文并行（all-gather 分片）", cp, "每层", "NVLink 节点内", cp / NV_LINK_GBS / 1e9),
        ("PP 流水线（激活传递）", pp, "每 micro-batch 边界", "IB/任意", pp / IB_GBS / 1e9),
        ("DP（ZeRO-1 梯度同步）", dp, "每优化器 step", "IB", dp / IB_GBS / 1e9),
    ]
    return rows, ep, cp

def main():
    import math
    mem_rows, per_card = mem_ledger()
    print("=" * 74)
    print("表 1：V4-Pro 1.6T 参数 · 显存账（H800 80GB）")
    print("=" * 74)
    print(f"{'口径':<40}{'总字节':>12}{'需卡数':>10}")
    for name, b, cards in mem_rows:
        if "训练" in name:
            print(f"{name:<40}{gb(b):>10.1f} GB{cards:>9.1f} 块/卡")
        else:
            print(f"{name:<40}{gb(b):>10.0f} GB{math.ceil(cards):>8.0f} 块")
    print(f"  训练注：分片后每卡仅 ~{gb(mem_rows[-1][1]):.0f}GB 状态，显存不是瓶颈；")
    print(f"  2048 卡的动机是算力（94.4M tokens/step 的 batch，V4 §4.2.2）+ 激活值空间。")

    print()
    print("=" * 74)
    print("表 2：1M 上下文训练 · 通信量对比（每 rank 125K token，同口径）")
    print("=" * 74)
    rows, ep, cp = comm_ledger(per_card)
    print(f"{'并行维度':<30}{'字节':>11}{'频次':>16}{'总线':>14}{'耗时@带宽':>12}")
    for name, b, freq, bus, t in rows:
        size = f"{gb(b):.0f} GB" if b >= 1e9 else f"{b/1e6:.0f} MB"
        print(f"{name:<30}{size:>11}{freq:>14}{bus:>12}{t:>10.2f} s")
    print(f"\n结论：EP/CP 通信量比 = {ep/cp:.0f} 倍（EP 单层 16GB vs CP 单层 9MB）→ EP 是训练系统真正的带宽瓶颈")
    print(f"  EP 单层 {gb(ep):.1f}GB；61 层全模型 EP 通信 ≈ {gb(ep*N_LAYER):.0f}GB/step（未 overlap 时）")
    print(f"  MegaMoE 融合 kernel 的意义：把这段通信藏进计算（V4 §3.1，1.50~1.73×）")

    print()
    print("=" * 74)
    print("表 3：每 token 通信字节（归一化视角）")
    print("=" * 74)
    ep_per_tok = TOP_K * HIDDEN * (FP8_B + BF16_B)
    csa_per_tok = KV_ENTRY_B / CSA_M
    hca_per_tok = KV_ENTRY_B / HCA_MP
    avg_per_tok = (csa_per_tok + hca_per_tok) / 2
    print(f"  EP：{TOP_K} 专家对 × {HIDDEN} 维 × 3B = {ep_per_tok/1e3:.0f} KB/token（每层）")
    print(f"  CP：压缩 KV = CSA {csa_per_tok:.0f}B/token（HCA {hca_per_tok:.1f}B），平均 ~{avg_per_tok:.0f}B/token")
    print(f"  每 token 比值：EP/CP ≈ {ep_per_tok/avg_per_tok:.0f} 倍（CSA 层 {ep_per_tok/csa_per_tok:.0f} 倍）")

if __name__ == "__main__":
    main()
