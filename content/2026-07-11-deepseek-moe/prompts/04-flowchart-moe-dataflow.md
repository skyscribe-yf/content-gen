---
illustration_id: 04
type: flowchart
style: notion
palette: warm
---

MoE 前向传播数据流图

Top-to-bottom data flow diagram.

TOP: 输入块 — "x: [N, D]" token 批次进入

MIDDLE SPLIT (two parallel paths):
- 左路径 "门控路由": x → Linear(W_g) → softmax → +bias → top-k → 输出 topk_idx 和 weights
  - 标注 "gated scores 选人 / raw scores 加权"
- 右路径 "专家计算": for each expert_id in 0..255:
  - 找到分配给这个专家的 token → expert(x[tok]) → 输出
  - 标注 "256 个 Expert，各自处理分配的 token"

BOTTOM MERGE: 两个路径汇合 → output[tok] += weights × expert_out → "y: [N, D]"

RIGHT SIDE LEGEND:
- "偏置 b_i 只影响 top-k 选择（左路径），不参与加权"

COLORS: Warm Cream background (#F5F0E8), black hand-drawn lines with slight wobble.
Left path fills in Golden Yellow (#F6AD55), right path fills in Terracotta (#C05621).
Merge zone in Warm Orange (#ED8936). Arrows in Deep Brown (#744210).

Clean composition with generous white space. Simple background.
Hand-lettered Chinese labels. Text large and prominent.
Color values (#hex) are rendering guidance only — do NOT display hex codes as visible text.
ASPECT: 16:9
