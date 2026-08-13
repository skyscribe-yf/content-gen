#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
experiment.py — DeepEP 与 DualPipe 篇的机制演示账本（纯 Python 无依赖）
=====================================================================
三部分：
  1. 气泡账本：1F1B / ZB1P / DualPipe 的流水线气泡公式对比（V3 报告 Table 2）
  2. C/B 判据：V4-Pro 的「通信藏得满吗」不等式（V4 报告 §2.1）+ H800 硬件代入
  3. 重叠时间线：两个 micro-batch 串行等通信 vs 双流重叠的总时长对比（机制演示）

⚠️ 全部数字均为机制演示：公式来自 V3/V4 报告原文，演示值（F/B/W、毫秒数）
为说明机制而设，不代表官方性能。仅用于帮助理解，不可作为性能依据。
"""

# ─────────────────────────────────────────────────────────────
# Part 1: 气泡账本（V3 报告 §3.2.1 Table 2）
# ─────────────────────────────────────────────────────────────
# 符号（V3 报告原义）：
#   F   = forward chunk 耗时
#   B   = full backward chunk 耗时
#   W   = backward-for-weights chunk 耗时
#   F&B = overlapped forward/backward chunk 耗时（前向/反向重叠块）
# 演示值：B ≈ 2F（反向约两倍前向是常见经验），W 取 0.8F，
#         F&B 取 F+B−0.8（重叠省掉 W 的量，示意）。
F, B, W, FnB = 1.0, 2.0, 0.8, 2.2

def bubble_1f1b(pp):
    return (pp - 1) * (F + B)

def bubble_zb1p(pp):
    return (pp - 1) * (F + B - 2 * W)

def bubble_dualpipe(pp):
    return (pp / 2 - 1) * (FnB + B - 3 * W)

print("=" * 66)
print("Part 1  气泡账本（演示值 F=1, B=2, W=0.8, F&B=2.2）")
print("=" * 66)
print(f"{'PP':>4} | {'1F1B':>10} | {'ZB1P':>10} | {'DualPipe':>10} | {'DualPipe/1F1B':>12}")
for pp in (4, 8, 16, 32):
    b1, bz, bd = bubble_1f1b(pp), bubble_zb1p(pp), bubble_dualpipe(pp)
    print(f"{pp:>4} | {b1:>10.2f} | {bz:>10.2f} | {bd:>10.2f} | {bd/b1:>11.1%}")

# 关键结论句（PP=16）
pp = 16
b1, bd = bubble_1f1b(pp), bubble_dualpipe(pp)
print(f"\nPP={pp}：气泡从 1F1B 的 {b1:.1f} 降到 DualPipe 的 {bd:.1f}（{bd/b1:.0%}），"
      f"块数从 (PP−1)={pp-1} 降到 (PP/2−1)={pp//2-1}。")
print("另有计算-通信重叠（attention 计算时跑 all-to-all），报告称 near-zero all-to-all overhead。")

# ─────────────────────────────────────────────────────────────
# Part 2: C/B 判据 ——「通信藏得满吗？」（V4 报告 §2.1）
# ─────────────────────────────────────────────────────────────
print("\n" + "=" * 66)
print("Part 2  C/B 判据（V4 报告 §2.1 原文公式）")
print("=" * 66)

# V4-Pro 真值（HF config.json）
h = 7168      # d_model
d = 3072      # inter_dim
print(f"\nV4-Pro：h(d_model)={h}，d(inter_dim)={d}")
print("每个 token-expert 对：计算 6hd FLOPs（SwiGLU gate/up/down 三个投影 ×2）")
print("                    通信 3h bytes（FP8 dispatch 1 字节 + BF16 combine 2 字节）")
v_ratio = 6 * h * d / (3 * h)          # Vcomp / Vcomm
print(f"Vcomp/Vcomm = 6hd / 3h = 2d = {v_ratio:.0f} FLOPs/Byte")
print("=> 通信能藏满 ⇔ 硬件 C/B ≤ 6144 FLOPs/Byte")

# H800 硬件侧（估算口径，标注假设）
compute_h800 = 1.98e15          # FP8 峰值 ~1.98 PFLOPS（H800 与 H100 SXM 同代口径）
nvlink_bw = 900e9               # 节点内 NVLink 900 GB/s（每卡）
ib_bw = 50e9                    # 跨节点 IB 50 GB/s/卡（V3 披露 3.2Tbps/节点 ÷ 8 卡）

def cb(compute, bw):
    return compute / bw

cb_nv, cb_ib = cb(compute_h800, nvlink_bw), cb(compute_h800, ib_bw)
print(f"\nH800 硬件 C/B（估算）：")
print(f"  节点内 NVLink：{cb_nv/1e3:,.0f}k FLOPs/Byte → {'藏得满 ✓' if cb_nv <= v_ratio else '藏不满 ✗'}")
print(f"  跨节点 IB   ：{cb_ib/1e3:,.0f}k FLOPs/Byte → {'藏得满 ✓' if cb_ib <= v_ratio else '藏不满 ✗'}")
print(f"\n结论：单个 token-expert 对的通信在节点内可以藏满，跨节点藏不满。")
print("所以需要把一次通信摊到一大批计算上——DualPipe 跨 micro-batch、MegaMoE 跨 wave，")
print("都是放大有效 Vcomp/Vcomm 的手段。")

# ─────────────────────────────────────────────────────────────
# Part 3: 重叠时间线 —— 串行等通信 vs 双流重叠（机制演示）
# ─────────────────────────────────────────────────────────────
print("\n" + "=" * 66)
print("Part 3  重叠时间线（演示值，机制演示）")
print("=" * 66)

# 演示值：一个 MoE 层 = Attention 10ms + all-to-all 5ms + 专家计算 10ms + combine 5ms
attn, a2a, moe, comb = 10.0, 5.0, 10.0, 5.0
layer_serial = attn + a2a + moe + comb          # 串行：30ms
layer_ovlp = attn + max(a2a, moe) + comb        # 重叠：all-to-all 藏在专家计算里
print(f"\n单个 micro-batch 的 MoE 层：Attention {attn}ms + all-to-all {a2a}ms + 专家 {moe}ms + combine {comb}ms")
print(f"  串行（通信与计算排队）：{layer_serial:.0f} ms")
print(f"  重叠（通信藏在计算里）：{layer_ovlp:.0f} ms")

# 两个 micro-batch：串行等 vs DualPipe 交错
def two_serial():
    # mb0 整层跑完再跑 mb1
    return 2 * layer_serial

def two_overlap():
    # 交错：mb1 的 Attention 藏在 mb0 的 all-to-all + 专家计算里
    # 时间线：attn0 | (a2a0+moe0 与 attn1 并行) | comb0 | (a2a1+moe1) | comb1
    return attn + max(a2a + moe, attn) + comb + max(a2a + moe, 0) + comb

s, o = two_serial(), two_overlap()
print(f"\n两个 micro-batch：")
print(f"  串行排队：{s:.0f} ms")
print(f"  交错重叠：{o:.0f} ms（省下 {s-o:.0f} ms，{o/s:.0%}）")
print(f"\n⚠️ 以上毫秒数为机制演示值，非官方性能数据。")
