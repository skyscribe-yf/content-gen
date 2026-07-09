---
illustration_id: 02
type: flowchart
style: notion
palette: warm
---

MoE 门控路由三步流程

Left-to-right flowchart with three step boxes connected by wavy hand-drawn arrows.

STEP 1 — "打分":
- 输入 token x 进入方框
- 乘 W_g 矩阵 → softmax
- 输出得分向量示例: [0.02, 0.15, 0.41, 0.03, 0.22, 0.01, ...]
- 第 3 和第 5 个值用 Coral Red 高亮

STEP 2 — "选人 (Top-k)":
- 从得分向量取前 k=2 个最大的
- 显示选中 Expert₃ (0.41) 和 Expert₅ (0.22)
- 其余专家灰色

STEP 3 — "加权":
- Expert₃ 和 Expert₅ 各自计算输出
- 输出 = 0.41 × Expert₃(x) + 0.22 × Expert₅(x)
- 箭头汇聚到最终输出 y

BOTTOM TAGLINE: "256 个专家，每次只激活 8 个 → FLOPs 减少 32×"

COLORS: Warm Cream background (#F5F0E8), black hand-drawn lines with slight wobble.
Step boxes filled in Golden Yellow (#F6AD55), arrows in Terracotta (#C05621).
Highlight values in Coral Red (#E8655A). Gray (#D4C5B9) for unselected experts.

Clean composition with generous white space. Simple background.
Hand-lettered Chinese labels and values. Text large and prominent.
Color values (#hex) are rendering guidance only — do NOT display hex codes as visible text.
ASPECT: 16:9
