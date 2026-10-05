#!/usr/bin/env python3
"""本篇脚本配图（数字/结构图）。数字全部取自 data/results.json 与正文红线。
禁止 AI 图承载数字；此文件只产脚本图。"""
import json, numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

plt.rcParams["font.sans-serif"] = ["Noto Sans CJK SC", "WenQuanYi Zen Hei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

OUT = "content/2026-10-06-deepseek-synthetic-data/"
R = json.load(open(OUT + "data/results.json"))

# ---------- 01 预训练 vs 后训练 ----------
fig, ax = plt.subplots(figsize=(9, 5))
cats = ["预训练\n(V3-Base)", "后训练\n(R1)"]
vals = [0, 60]
bars = ax.bar(cats, vals, width=0.5, color=["#9aa5b1", "#0F4C81"])
bars[0].set_height(0.0)
ax.text(0, 1.5, "0 份合成数据", ha="center", fontsize=16, color="#52606d", fontweight="bold")
ax.text(1, 61.5, "60 万道 AI 自出的推理题", ha="center", fontsize=16, color="#0F4C81", fontweight="bold")
ax.set_ylabel("合成数据量（万道）", fontsize=12)
ax.set_ylim(0, 75)
ax.set_title("同一家 DeepSeek，两套规矩", fontsize=16, fontweight="bold")
for s in ["top", "right"]:
    ax.spines[s].set_visible(False)
plt.tight_layout()
plt.savefig(OUT + "01-two-halves.png", dpi=160)
plt.close()

# ---------- 02 迭代训练下分布尾巴收缩 ----------
rng = np.random.default_rng(20261006)
x = np.linspace(-6, 6, 600)
def gauss(mu, s): return np.exp(-((x-mu)**2)/(2*s*s))/(s*np.sqrt(2*np.pi))
true = 0.5*gauss(-1.6, 0.55) + 0.5*gauss(1.6, 0.55)
cur = true.copy()
cur = cur/cur.sum()
fig, ax = plt.subplots(figsize=(9, 5))
ax.plot(x, true, "--", color="#52606d", lw=2.5, label="原始分布（真实数据）")
colors = ["#0F4C81", "#e07a2f", "#c0392b"]
for g in range(3):
    # 反复拟合再采样 => 尾部被削
    cur = cur ** (1.0 / (1 + 0.9*g))
    cur = cur / cur.sum()
    ax.plot(x, cur, color=colors[g], lw=2.2, label=f"第 {g+1} 代（只吃自己的输出）")
ax.set_xlabel("样本取值", fontsize=12)
ax.set_ylabel("密度", fontsize=12)
ax.set_title("一代代只吃自己的输出，尾巴先消失", fontsize=16, fontweight="bold")
ax.legend(fontsize=11, frameon=False)
for s in ["top", "right"]:
    ax.spines[s].set_visible(False)
plt.tight_layout()
plt.savefig(OUT + "02-tail-collapse.png", dpi=160)
plt.close()

# ---------- 03 通过率 + 错误答案 ----------
fig, (a1, a2) = plt.subplots(1, 2, figsize=(10, 5), gridspec_kw={"width_ratios": [1, 1.5]})
a1.bar(["通过", "被筛掉"], [R["passed"], R["failed"]], color=["#0F4C81", "#c0392b"], width=0.55)
a1.text(0, R["passed"]+2, f'{R["passed"]}', ha="center", fontsize=18, fontweight="bold", color="#0F4C81")
a1.text(1, R["failed"]+2, f'{R["failed"]}', ha="center", fontsize=18, fontweight="bold", color="#c0392b")
a1.set_ylim(0, 108)
a1.set_title("100 次采样：93 通过 / 7 被筛", fontsize=14, fontweight="bold")
for s in ["top", "right"]:
    a1.spines[s].set_visible(False)

wa = R["wrong_answers"]
ks = list(wa.keys())
vs = list(wa.values())
a2.barh(ks[::-1], vs[::-1], color="#c0392b")
for i, v in enumerate(vs[::-1]):
    a2.text(v+0.05, i, str(v), va="center", fontsize=12)
a2.set_xlabel("出现次数", fontsize=12)
a2.set_title("被筛掉的都是什么答案", fontsize=14, fontweight="bold")
a2.set_xlim(0, 3.6)
for s in ["top", "right"]:
    a2.spines[s].set_visible(False)
plt.tight_layout()
plt.savefig(OUT + "03-pass-rate.png", dpi=160)
plt.close()

# ---------- 04 93 条正确答案 → 1 类方法 ----------
fig, ax = plt.subplots(figsize=(9, 5))
labels = ["模5生成函数 / 循环卷积", "等价的余数计数"]
vals = [R["correct_method_breakdown"]["generating_function_cyclic_convolution"],
        R["correct_method_breakdown"]["residue_class_direct_count"]]
bars = ax.barh(labels[::-1], vals[::-1], color=["#9aa5b1", "#0F4C81"])
for i, v in enumerate(vals[::-1]):
    ax.text(v+1, i, str(v), va="center", fontsize=16, fontweight="bold", color="#0F4C81")
ax.set_xlim(0, 105)
ax.set_xlabel("正确答案条数", fontsize=12)
ax.set_title("筛完只剩正确答案，93 条里只有 1 条路", fontsize=15, fontweight="bold")
for s in ["top", "right"]:
    ax.spines[s].set_visible(False)
plt.tight_layout()
plt.savefig(OUT + "04-one-path.png", dpi=160)
plt.close()

print("charts done:", OUT)
