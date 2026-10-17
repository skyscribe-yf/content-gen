#!/usr/bin/env python3
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import os
from matplotlib.font_manager import FontProperties
FP = FontProperties(fname='/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc')
FPB = FontProperties(fname='/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc')
D = "content/2026-10-18-ai-native-sdlc-diagnosis"

# 01 six stages
fig, ax = plt.subplots(figsize=(10, 6))
ax.axis('off')
stages = [("Plan","委员会收需求","Claude 综合痛点落成 intent.md"),
          ("Design","分析师写 spec","需求与设计压缩成一次会话"),
          ("Build","代码与测试手写","先有被接受的 plan 才动手"),
          ("Test","QA 作为闸门","evals 织进实现过程"),
          ("Deploy","人逐行 review","多层 agentic review"),
          ("Maintain","人盯生产 bug","agent 盯线上，控制带突破写 intent.md")]
cols = ["阶段","传统","AI-native"]
# header
for j,h in enumerate(cols):
    ax.text(0.05 + j*0.32, 0.95, h, fontsize=13, fontweight='bold', fontproperties=FP, ha='left', va='top')
y=0.86
for s,t,a in stages:
    ax.text(0.05, y, s, fontsize=12, fontweight='bold', fontproperties=FP, ha='left', va='top', color='#E8A317')
    ax.text(0.37, y, t, fontsize=11, ha='left', fontproperties=FP, va='top')
    ax.text(0.69, y, a, fontsize=11, ha='left', fontproperties=FP, va='top')
    y -= 0.13
plt.tight_layout()
plt.savefig(os.path.join(D,'01-six-stages.png'), dpi=150, bbox_inches='tight')
plt.close()

# 02 MECE six
fig, ax = plt.subplots(figsize=(10, 5))
ax.axis('off')
cells = [("能","高","跨 harness 原语不对称"),
         ("值","近零","成本结构、验证成本"),
         ("该","仅内部治理","外部监管、责任、IP"),
         ("愿","近零","变更管理、采纳阻力"),
         ("撑","零","人、junior、技术债"),
         ("知","度量未被质疑","相关性失效、长尺度")]
for i,(a,b,c) in enumerate(cells):
    x = 0.05 + (i%3)*0.33
    y = 0.7 - (i//3)*0.4
    ax.text(x, y, a, fontsize=16, fontweight='bold', fontproperties=FP, color='#E8A317')
    ax.text(x, y-0.12, b, fontsize=11, fontweight='bold', fontproperties=FP)
    ax.text(x, y-0.24, c, fontsize=9, fontproperties=FP)
ax.text(0.5, 0.95, "MECE 六问：playbook 覆盖度", fontsize=14, fontweight='bold', fontproperties=FP, ha='center')
plt.tight_layout()
plt.savefig(os.path.join(D,'02-mece-six.png'), dpi=150, bbox_inches='tight')
plt.close()

# 03 n_eff formula
fig, ax = plt.subplots(figsize=(8, 4))
ax.axis('off')
ax.text(0.5, 0.7, r"$n_{\mathrm{eff}} = \frac{k}{1+(k-1)\bar{\phi}}$", fontsize=28, ha='center', fontproperties=FP)
ax.text(0.5, 0.45, "k=9, φ̄=0.39  ⇒  n_eff = 2.18  (9 判官 = 2.2 票)", fontsize=13, ha='center', fontproperties=FP)
ax.text(0.5, 0.25, "β = P(池中所有模型都错)  ⇒  精度上限 = 1-β", fontsize=13, ha='center', fontproperties=FP)
plt.tight_layout()
plt.savefig(os.path.join(D,'03-neff.png'), dpi=150, bbox_inches='tight')
plt.close()
print("done")

# 04 artifact chain
fig, ax = plt.subplots(figsize=(10, 3))
ax.axis('off')
chain = ["intent.md","spec.md","plan.md","diff+tests","PR+review","incident"]
x=0.05
for i,c in enumerate(chain):
    ax.text(x, 0.5, c, fontsize=11, fontweight='bold', ha='left', va='center', fontproperties=FP,
            bbox=dict(boxstyle='round,pad=0.3', fc='#1a2a4a', ec='#E8A317'))
    if i < len(chain)-1:
        ax.annotate("", xy=(x+0.15,0.5), xytext=(x+0.12,0.5), arrowprops=dict(arrowstyle='->', color='#E8A317'))
    x += 0.16
ax.text(0.5, 0.85, "committed artifact 链 = 交接件 = 审计轨迹", fontsize=13, fontweight='bold', ha='center', fontproperties=FP)
plt.tight_layout()
plt.savefig(os.path.join(D,'04-artifact-chain.png'), dpi=150, bbox_inches='tight')
plt.close()
print("done extra")
