#!/usr/bin/env python3
import os, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
FP = FontProperties(fname='/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc')
D = "content/2026-10-20-ai-native-sdlc-landing"

# 01 feedback latency four tiers
fig, ax = plt.subplots(figsize=(9, 5))
ax.axis('off')
rows = [("亚秒","TDD 实践者：改一次查一次","lint / typecheck / 单测"),
        ("几秒~1 分钟","小批次提交","模块内纠正"),
        ("5–10 分钟","开头跑一次、结尾跑一次","中间「蒙一把」"),
        ("20 分钟+","「投机者」","整个会话只跑一两次")]
y=0.85
for a,b,c in rows:
    ax.text(0.05, y, a, fontsize=13, fontweight='bold', color='#E8A317', fontproperties=FP)
    ax.text(0.30, y, b, fontsize=11, fontproperties=FP)
    ax.text(0.72, y, c, fontsize=10, fontproperties=FP)
    y -= 0.18
ax.text(0.5, 0.95, "反馈延迟 → agent 行为形态", fontsize=14, fontweight='bold', ha='center', fontproperties=FP)
plt.tight_layout()
plt.savefig(os.path.join(D,'01-feedback-latency.png'), dpi=150, bbox_inches='tight')
plt.close()

# 02 NFR three layers
fig, ax = plt.subplots(figsize=(9, 4.5))
ax.axis('off')
layers = [("层 1","可单一数值化","预算 + 基线","p99 延迟、内存峰值"),
          ("层 2","可结构规则化","fitness function 进 CI","分层/依赖方向、无循环依赖"),
          ("层 3","不可数值化","限制产量 + 人工读","抽象是否恰当")]
y=0.8
for a,b,c,d in layers:
    ax.text(0.05, y, a, fontsize=13, fontweight='bold', color='#E8A317', fontproperties=FP)
    ax.text(0.22, y, b, fontsize=12, fontweight='bold', fontproperties=FP)
    ax.text(0.52, y, c, fontsize=10, fontproperties=FP)
    ax.text(0.52, y-0.1, d, fontsize=9, fontproperties=FP)
    y -= 0.25
ax.text(0.5, 0.95, "非功能约束 NFR 三层定义", fontsize=14, fontweight='bold', ha='center', fontproperties=FP)
plt.tight_layout()
plt.savefig(os.path.join(D,'02-nfr-layers.png'), dpi=150, bbox_inches='tight')
plt.close()

# 03 cost cliff tiered pricing
fig, ax = plt.subplots(figsize=(9, 4.5))
ax.axis('off')
tiers = [("0–32K","$0.144","$0.574"),
         ("32K–128K","$0.216","$0.861"),
         ("128K–256K","$0.359","$1.434"),
         ("256K–1M","$0.717","$3.584")]
ax.text(0.15, 0.9, "输入区间", fontsize=11, fontweight='bold', fontproperties=FP)
ax.text(0.45, 0.9, "输入 $/M", fontsize=11, fontweight='bold', fontproperties=FP)
ax.text(0.72, 0.9, "输出 $/M", fontsize=11, fontweight='bold', fontproperties=FP)
y=0.78
for a,b,c in tiers:
    ax.text(0.15, y, a, fontsize=11, fontproperties=FP)
    ax.text(0.45, y, b, fontsize=11, fontproperties=FP)
    ax.text(0.72, y, c, fontsize=11, fontproperties=FP)
    y -= 0.14
ax.text(0.5, 0.2, "整单跳档：输入长度决定档位，输出单价也由输入长度决定", fontsize=10, ha='center', fontproperties=FP)
ax.text(0.5, 0.95, "阶梯计费 cliffs（qwen3-coder-flash 示例）", fontsize=14, fontweight='bold', ha='center', fontproperties=FP)
plt.tight_layout()
plt.savefig(os.path.join(D,'03-cost-cliff.png'), dpi=150, bbox_inches='tight')
plt.close()

# 04 n_eff + beta
fig, ax = plt.subplots(figsize=(9, 4.5))
ax.axis('off')
ax.text(0.5, 0.85, r"$n_{\mathrm{eff}} = \frac{k}{1+(k-1)\bar{\phi}}$", fontsize=26, ha='center')
ax.text(0.5, 0.6, "k=9, φ̄=0.39  ⇒  n_eff = 2.18", fontsize=13, ha='center', fontproperties=FP)
ax.text(0.5, 0.45, "全票一致错误率 9.1% vs 独立假设 0.02%（差 ~455 倍）", fontsize=12, ha='center', fontproperties=FP)
ax.text(0.5, 0.3, r"$\beta = P(\mathrm{池中所有模型都错})$  ⇒  精度上限 = $1-\beta$", fontsize=13, ha='center', fontproperties=FP)
ax.text(0.5, 0.12, "确定性检查是唯一不与模型共享 φ̄ 的验证层", fontsize=11, ha='center', fontproperties=FP)
plt.tight_layout()
plt.savefig(os.path.join(D,'04-neff-beta.png'), dpi=150, bbox_inches='tight')
plt.close()
print("done")
