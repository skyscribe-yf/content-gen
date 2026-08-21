#!/usr/bin/env python3
# gen_charts for 多维高斯注解 2026-08-21
import os
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

OUT = Path("content/2026-08-21-多维高斯注解")
OUT.mkdir(parents=True, exist_ok=True)

# fonts
for f in ["/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc", "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"]:
    if os.path.exists(f):
        font_manager.fontManager.addfont(f)
plt.rcParams["font.family"] = "Noto Sans CJK SC"
plt.rcParams["axes.unicode_minus"] = False

BLUE="#2a6fdb"
GOLD="#e0a82e"
PURPLE="#8a4fd8"
GRAY="#555555"
GREEN="#2e7d32"

def fig_mean_evolution():
    fig, axes = plt.subplots(1,3, figsize=(12,4.2), dpi=160)
    titles=["有限离散：求和平均","无限离散：无穷级数极限","连续：求和→积分"]
    for ax, title in zip(axes, titles):
        ax.set_xlim(0,10); ax.set_ylim(0,6); ax.axis("off")
        ax.text(5,5.2,title,ha="center",fontsize=11, color=GRAY)
    # Panel1: dots averaging
    ax=axes[0]
    xs=np.array([2,4,6,8])
    ys=np.array([2,4,3,5])
    ax.scatter(xs, ys, c=BLUE, s=70, zorder=3)
    ax.plot([1,9],[3.5,3.5], color=GOLD, ls="--", lw=2)
    ax.text(5,3.8,"$\\mu=\\frac{1}{n}\\sum x_i$",ha="center",fontsize=11, color=BLUE)
    ax.text(5,1.2,"n=4 个样本点\n取平均",ha="center",fontsize=9, color=GRAY)
    # Panel2: infinite series
    ax=axes[1]
    ax.text(5,4.5,"$\\mu=\\lim_{n\\to\\infty}\\frac{1}{n}\\sum_{i=1}^n x_i$",ha="center",fontsize=10, color=BLUE)
    ax.text(5,3.8,"$=\\sum_k x_k P(X=x_k)$",ha="center",fontsize=10, color=BLUE)
    # draw dots fading
    for i in range(8):
        ax.scatter(2+i*0.8, 2+ np.sin(i)*0.3, c=BLUE, alpha=0.3+0.7*(i/8), s=45)
    ax.text(5,1.2,"样本数→$\\infty$\n极限稳定",ha="center",fontsize=9, color=GRAY)
    # Panel3: integral
    ax=axes[2]
    x=np.linspace(0.5,9.5,200)
    y= np.exp(-0.5*((x-5)/1.8)**2)*2+1
    ax.plot(x,y,color=BLUE,lw=1.8)
    ax.fill_between(x,y,1, color=BLUE, alpha=0.15)
    ax.text(5,4.6,"$E[X]=\\int x f(x)dx$",ha="center",fontsize=11, color=BLUE)
    ax.text(5,1.2,"达布·黎曼·柯西\n求和的极限",ha="center",fontsize=9, color=GRAY)
    fig.suptitle("一维均值：有限求和 → 无穷级数 → 积分", fontsize=14, y=1.02)
    fig.tight_layout()
    fig.savefig(OUT/"01-mean-evolution.png", bbox_inches="tight")
    plt.close(fig)

def fig_variance_why_square():
    fig, axes = plt.subplots(1,3, figsize=(12,4.4), dpi=160)
    fig.suptitle("方差为什么用平方？三点：抵消 / 不可导 / 可加性", fontsize=14, y=1.02)
    # Panel1: cancellation
    ax=axes[0]
    ax.set_xlim(-2,2); ax.set_ylim(-0.2,2.5); ax.axis("off")
    ax.set_title("不取平方：正负抵消", fontsize=11)
    # Show deviations
    devs=[-1.5,-0.5,0.5,1.5]
    for d in devs:
        color= BLUE if d>0 else GOLD
        ax.arrow(0,1, d,0, head_width=0.08, head_length=0.12, color=color, lw=2)
    ax.plot([-2,2],[1,1], color=GRAY, lw=0.8)
    ax.text(0,2.2,"$E[X-\\mu]=0$ 恒零\n量不出分散",ha="center",fontsize=9, color=GRAY)
    ax.text(0,0.4,"$\\sum (x_i-\\mu)=0$",ha="center",fontsize=10, color=BLUE)
    # Panel2: absolute not differentiable
    ax=axes[1]
    ax.set_title("|x| 在0不可导", fontsize=11)
    x=np.linspace(-2,2,200)
    ax.plot(x, np.abs(x), color=GOLD, lw=2)
    ax.plot(x, x**2, color=BLUE, lw=2, ls="--")
    ax.set_xlim(-2,2); ax.set_ylim(-0.1,2.1)
    ax.text(-1.2,0.3,"|x| 尖点",ha="center",fontsize=9, color=GOLD)
    ax.text(1.0,1.6,"$x^2$ 光滑",ha="center",fontsize=9, color=BLUE)
    ax.text(0,2.0,"优化: 梯度断裂 vs 光滑",ha="center",fontsize=8, color=GRAY)
    for s in ax.spines.values(): s.set_visible(False)
    ax.set_xticks([]); ax.set_yticks([])
    # Panel3: additivity
    ax=axes[2]
    ax.axis("off")
    ax.set_title("独立可加性", fontsize=11)
    ax.text(5,8,"$Var(X+Y)$",ha="center",fontsize=12, color=BLUE)
    ax.text(5,6.5,"$=$",ha="center",fontsize=14)
    ax.text(2,5,"$Var(X)$",ha="center",fontsize=11, color=BLUE)
    ax.text(8,5,"$Var(Y)$",ha="center",fontsize=11, color=BLUE)
    ax.text(5,5,"+",ha="center",fontsize=14, color=GOLD)
    ax.text(5,3.5,"若 $X\\perp Y$",ha="center",fontsize=9, color=GRAY)
    ax.text(5,2.5,"$E[|X|]$ 无此性质\n$|X+Y|\\neq|X|+|Y|$",ha="center",fontsize=8, color=GOLD)
    ax.set_xlim(0,10); ax.set_ylim(0,9)
    fig.tight_layout()
    fig.savefig(OUT/"02-variance-why-square.png", bbox_inches="tight")
    plt.close(fig)

def fig_mean_vector():
    fig, ax = plt.subplots(figsize=(10,5), dpi=160)
    ax.set_xlim(0,12); ax.set_ylim(0,6); ax.axis("off")
    ax.text(6,5.4,"均值向量：每维单独取均值，再堆成向量", ha="center", fontsize=14)
    # Draw 3 vectors stacked
    for i, (y, col, label) in enumerate([(3.8, BLUE, "$X_1$"), (2.6, GOLD, "$X_2$"), (1.4, PURPLE, "$X_d$")]):
        ax.add_patch(FancyBboxPatch((1,y), 3,0.9, boxstyle="round,pad=0.02,rounding_size=0.08", fc="#eef3fc" if col==BLUE else "#fdf3d7" if col==GOLD else "#f2e7fb", ec=col, lw=1.6))
        ax.text(2.5,y+0.45,label,ha="center",va="center",fontsize=12, color=col)
        ax.text(4.8,y+0.45,"→  $E[X_i]=\\mu_i$",ha="left",va="center",fontsize=10, color=GRAY)
    # Arrow to vector
    ax.add_patch(FancyArrowPatch((6,2.6),(7.8,2.6), arrowstyle="-|>", mutation_scale=16, color=GRAY, lw=1.6))
    ax.add_patch(FancyBboxPatch((7.8,1.2),2.2,2.8, boxstyle="round,pad=0.02,rounding_size=0.08", fc="#e8f5e9", ec=GREEN, lw=1.6))
    ax.text(8.9,3.4,"$\\boldsymbol{\\mu}$",ha="center",fontsize=16, color=GREEN)
    ax.text(8.9,2.7,"$=(\\mu_1,\\mu_2,\\dots,\\mu_d)^\\top$",ha="center",fontsize=9, color=GREEN)
    ax.text(8.9,2.0,"$E[\\mathbf{X}]$",ha="center",fontsize=10, color=GREEN)
    ax.text(8.9,1.5,"云的中心",ha="center",fontsize=9, color=GRAY)
    fig.tight_layout()
    fig.savefig(OUT/"03-mean-vector.png", bbox_inches="tight")
    plt.close(fig)

def fig_cov_heatmap():
    fig, axes = plt.subplots(1,2, figsize=(12,4.8), dpi=160)
    fig.suptitle("协方差矩阵：对角是方差，非对角是协作", fontsize=14, y=1.02)
    # Example 3x3 cov
    cov = np.array([[1.0, 0.6, -0.3],[0.6,2.0,0.4],[-0.3,0.4,1.5]])
    for ax, title, mat in zip(axes, ["满协方差：各处相关", "对角化：线性不相关"], [cov, np.diag(np.diag(cov))]):
        im=ax.imshow(mat, vmin=-1, vmax=2, cmap="RdYlBu_r")
        ax.set_xticks([0,1,2]); ax.set_yticks([0,1,2])
        ax.set_xticklabels(["$X_1$","$X_2$","$X_3$"]); ax.set_yticklabels(["$X_1$","$X_2$","$X_3$"])
        ax.set_title(title, fontsize=11)
        for i in range(3):
            for j in range(3):
                ax.text(j,i, f"{mat[i,j]:.1f}", ha="center", va="center", fontsize=10, color="white" if abs(mat[i,j])>1 else "black")
        # Colorbar
    fig.tight_layout()
    fig.savefig(OUT/"04-cov-heatmap.png", bbox_inches="tight")
    plt.close(fig)

def fig_corr_standardize():
    fig, axes = plt.subplots(1,2, figsize=(12,4.8), dpi=160)
    fig.suptitle("相关矩阵：标准化到 [-1,1] 的皮尔森系数", fontsize=14, y=1.02)
    # Left: raw cov values heterogeneous
    ax=axes[0]
    ax.set_title("协方差：量纲混杂 $0.01$ vs $100$", fontsize=11)
    cov_raw=np.array([[0.01, 0.02],[0.02,100]])
    im=ax.imshow(cov_raw, cmap="RdYlBu_r", vmin=-5, vmax=100)
    ax.set_xticks([0,1]); ax.set_yticks([0,1]); ax.set_xticklabels(["改行数","测试时长"]); ax.set_yticklabels(["改行数","测试时长"])
    for i in range(2):
        for j in range(2):
            ax.text(j,i, f"{cov_raw[i,j]:.2f}", ha="center", va="center", fontsize=11, color="white" if cov_raw[i,j]>50 else "black")
    ax.text(0.5,-0.6,"尺度差 $10^4$ 倍\n梯度被撕碎", ha="center", fontsize=9, color=GRAY, transform=ax.transAxes)
    # Right: correlation
    ax=axes[1]
    ax.set_title("相关矩阵：$\\rho\\in[-1,1]$ 统一尺度", fontsize=11)
    corr=np.array([[1,0.02],[0.02,1]])
    im2=ax.imshow(corr, cmap="RdYlBu_r", vmin=-1, vmax=1)
    ax.set_xticks([0,1]); ax.set_yticks([0,1]); ax.set_xticklabels(["改行数","测试时长"]); ax.set_yticklabels(["改行数","测试时长"])
    for i in range(2):
        for j in range(2):
            ax.text(j,i, f"{corr[i,j]:.2f}", ha="center", va="center", fontsize=11, color="black" if corr[i,j]==1 else "white")
    ax.text(0.5,-0.6,"1=正相关 -1=负相关\n对角线恒为1", ha="center", fontsize=9, color=GRAY, transform=ax.transAxes)
    fig.tight_layout()
    fig.savefig(OUT/"05-correlation.png", bbox_inches="tight")
    plt.close(fig)

if __name__=="__main__":
    fig_mean_evolution()
    fig_variance_why_square()
    fig_mean_vector()
    fig_cov_heatmap()
    fig_corr_standardize()
    print("charts done")
