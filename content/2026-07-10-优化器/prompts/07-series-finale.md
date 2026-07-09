---
type: framework
style: notion
palette: warm
aspect: "1:1"
refs: []
---

ZONES:
- Top: Title "深度学习基础系列 · 完结" with "六篇一条线" subtitle
- Six connected nodes in a circular/hexagonal arrangement, each with icon + title:
  Node 1: ① 梯度下降 — 方向（蒙眼下山）
  Node 2: ② 损失函数 — 打分（交叉熵 vs MSE）
  Node 3: ③ 反向传播 — 追责（链式法则回传）
  Node 4: ④ Softmax — 概率化（可导的 argmax）
  Node 5: ⑤ 残差连接 — 通路（∂y/∂x = 1 + ∂F/∂x）
  Node 6: ⑥ 优化器 — 步伐（方向 ÷ 尺度）
- Arrows connecting all six nodes showing the flow: 方向 → 打分 → 追责 → 概率化 → 通路 → 步伐
- Center: A gear/brain icon with text "训练闭环"
- Bottom: "每个环节缺一不可 · 下一篇：大模型原理系列"

LABELS:
- Title: 深度学习基础系列 — 六篇一条线
- Each node has its number, concept name, and one-line description
- Center: 训练闭环
- Bottom subtitle: 下一篇 → 大模型原理系列

COLORS:
- Background: warm cream
- Nodes: each in a distinct warm-tone color (progression from light orange to deep orange through the six)
- Connecting arrows: warm gray
- Center icon: warm orange with glow
- Bottom: muted text with arrow

STYLE: notion clean framework diagram, circular/hexagonal layout, connected nodes, elegant summary, Chinese labels
ASPECT: 1:1 square
