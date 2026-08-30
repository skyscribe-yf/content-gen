#!/usr/bin/env python3
"""大数定律收敛曲线（脚本画图，数字由脚本承载，AI 不碰数字）"""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
import os

for f in [
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
]:
    if os.path.exists(f):
        font_manager.fontManager.addfont(f)
plt.rcParams["font.family"] = "Noto Sans CJK SC"
plt.rcParams["axes.unicode_minus"] = False

rng = np.random.default_rng(42)
N = 20000
rolls = rng.integers(1, 7, size=N).astype(float)  # 骰子 1-6
means = np.cumsum(rolls) / np.arange(1, N + 1)

fig, ax = plt.subplots(figsize=(9, 5.2), dpi=150)
ax.plot(np.arange(1, N + 1), means, color="#0F4C81", lw=1.6, label="样本均值（每次新掷一粒骰子）")
ax.axhline(3.5, color="#E8A33D", lw=1.8, ls="--", label="期望 E[X] = 3.5")

for n in (10, 100, 1000, 10000, 20000):
    ax.axvline(n, color="#CCCCCC", lw=0.6, ls=":")
ax.annotate("10 次\n平均还飘着", xy=(10, means[9]), xytext=(60, 4.6),
            arrowprops=dict(arrowstyle="->", color="#666666"), fontsize=11, color="#444444")
ax.annotate("1 万次\n几乎贴住 3.5", xy=(10000, means[9999]), xytext=(10500, 2.6),
            arrowprops=dict(arrowstyle="->", color="#666666"), fontsize=11, color="#444444")

ax.set_xscale("log")
ax.set_xlim(1, 40000)
ax.set_ylim(1.5, 5.5)
ax.set_xlabel("采样次数 n（对数坐标）", fontsize=12)
ax.set_ylabel("样本均值", fontsize=12)
ax.set_title("单次掷骰子完全随机，一万次平均几乎必然贴着 3.5", fontsize=13)
ax.legend(loc="upper right", fontsize=11)
ax.grid(True, which="both", alpha=0.25)
fig.tight_layout()
fig.savefig("content/2026-08-30-大数定律/02-lln-convergence.png")
print("saved")
