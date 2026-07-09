---
type: infographic
style: notion
palette: warm
aspect: "1:1"
refs: []
---

ZONES:
- Top: Title "SGD 的困境：一刀切的学习率" in bold
- Left side: A neural network node diagram showing weight W and bias b connected
- Center-left: A large gauge/scale showing the same η applied to both parameters
- Right side: Two visual indicators — W oscillating up and down (震荡, with zigzag annotation), b barely moving (不动, with flat line annotation)
- Bottom: Annotation "同一个 η，管百万个参数，尺度差的参数要么震荡要么不动"

LABELS:
- Title: SGD 的困境
- Left label: 权重 W（梯度大 100 倍）
- Right label: 偏置 b（梯度很小）
- Center gauge: η（固定学习率）
- W behavior: 震荡！
- b behavior: 不动！
- Bottom annotation: 一刀切

COLORS:
- Background: warm cream
- Title: deep orange
- W node and zigzag: red/orange
- b node and flat line: cool blue/gray
- η gauge: neutral gray
- Warning annotations: red accents

STYLE: notion clean educational infographic, simple icon-style neural diagram, clear before/after contrast
ASPECT: 1:1 square
