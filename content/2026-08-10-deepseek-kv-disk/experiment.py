#!/usr/bin/env python3
"""
KV 落盘篇机制实验（自包含 NumPy，机制演示，不代表官方性能基准）
实验 1：磁盘读盘 vs 重算 prefill 的权衡曲线（交叉点）
实验 2：SWA 三策略的存储 × 重算二维对比
实验 3：lcm(m, m') 块对齐的检索开销对比
"""
import numpy as np

# ---------- 参数（量级估算，正文标注口径） ----------
DISK_BW = 5.0e9          # NVMe SSD 顺序读 ~5 GB/s
GPU_FLOP = 1.0e15         # 单卡 ~1 PFLOPS（FP8，量级）
KV_PER_TOKEN = 10240.0    # 压缩后每 token KV 字节（V4 量级）
L = 61                    # V4-Pro 层数
NWIN = 128                # 滑动窗口（V4-Flash 配置）
M, MP = 4, 128            # CSA / HCA 压缩比（V4-Flash 配置）

# 有效 prefill 算力模型：flops(n) ≈ L * c * n^2。
# V4 稀疏注意力大幅压低有效计算量，c 取量级使 1M token prefill ≈ 60s（满配单卡）。
ATTN_C = 1000.0

def prefill_time(n_tokens):
    return L * ATTN_C * n_tokens ** 2 / GPU_FLOP

def disk_read_time(kv_bytes):
    return kv_bytes / DISK_BW

def exp1_tradeoff(max_len=1_000_000, n=200):
    """实验 1：交叉点。前缀 n 命中时：读盘 vs 重算。"""
    lens = np.linspace(1000, max_len, n).astype(int)
    t_read = np.array([disk_read_time(KV_PER_TOKEN * l) for l in lens])
    t_recomp = np.array([prefill_time(l) for l in lens])
    cross = lens[np.argmax(t_recomp > t_read)]
    gain = t_recomp[-1] / t_read[-1]
    print(f"[实验1] 权衡曲线：读盘 vs 重算 prefill")
    print(f"  交叉点：前缀 ≈ {cross/1000:.0f}K token（此前重算便宜，此后读盘赢）")
    print(f"  1M token：读盘 {t_read[-1]:.1f}s vs 重算 {t_recomp[-1]:.0f}s → 读盘快 {gain:.0f} 倍")
    return lens, t_read, t_recomp

def exp2_swa_strategies(n_total=1_000_000, p=8192):
    """实验 2：SWA 三策略。存储成本（GB）vs 重算成本（秒）。"""
    swa_per_token = KV_PER_TOKEN * 8  # SWA 是压缩 KV 的 8 倍
    full_gb = swa_per_token * n_total / 1e9
    # 每个 checkpoint 保存最近 n_win 个 token 的 SWA KV；每 p 个 token 存一份
    n_ckpt = n_total // p
    periodic_gb = swa_per_token * NWIN * n_ckpt / 1e9
    periodic_recomp = prefill_time(p)          # 加载最近检查点后重算 ≤ p 个 token
    zero_recomp = prefill_time(NWIN * L)       # 完全不存：重算 n_win*L 个 token（有界）
    print(f"[实验2] SWA 三策略（1M token；SWA 为压缩 KV 的 8 倍；p={p}）")
    print(f"  Full    : 存储 {full_gb:7.1f} GB, 重算 0.00s")
    print(f"  Periodic: 存储 {periodic_gb:7.2f} GB, 重算 {periodic_recomp:.3f}s")
    print(f"  Zero    : 存储 {0:7.1f} GB, 重算 {zero_recomp:.3f}s（有界，n_win×L={NWIN*L} token）")

def exp3_lcm_alignment(hit_len=300_000, m=6, mp=10):
    """实验 3：块边界对齐。演示用 m=6/m'=10（lcm=30），V4 实际 m=4/m'=128。
    前缀命中 hit_len 个原始 token，检索需要读的「块数」：
    - lcm 对齐：块边界同时是两分支边界，命中段恰好落在整数块上
    - 单分支对齐：另一分支的条目跨块，命中段要多读边界块（padding 浪费）
    """
    lcm_ = np.lcm(m, mp)
    print(f"[实验3] lcm 对齐（演示 m={m}, m'={mp} → lcm={lcm_}；V4 实际 m=4, m'=128 → lcm=128）")
    for name, bs in [("CSA对齐", m), ("HCA对齐", mp), ("lcm对齐", lcm_)]:
        # 每块覆盖 bs 个原始 token；块内两分支条目数按比例
        k_csa = bs / m
        k_hca = bs / mp
        # 命中段覆盖的块数：CSA/HCA 各自条目跨过的物理块的最大值（边界块多读 = padding 浪费）
        blocks_csa = np.ceil(hit_len / (m * bs))  # 每块含 k_csa 个 CSA 条目 → 每块覆盖 m*bs 原始 token
        blocks_hca = np.ceil(hit_len / (mp * bs))
        total = int(blocks_csa + blocks_hca)
        print(f"  {name} (块={bs:>2} token): 检索 {hit_len/1000:.0f}K token 前缀需读 {total} 块")
    print(f"  → lcm 对齐时 CSA/HCA 条目共边，块数最少；单分支对齐要多读边界块")

if __name__ == "__main__":
    print("=" * 56)
    exp1_tradeoff()
    print("-" * 56)
    exp2_swa_strategies()
    print("-" * 56)
    exp3_lcm_alignment()
    print("=" * 56)
