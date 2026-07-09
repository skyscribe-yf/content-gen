---
type: infographic
style: notion
palette: warm
aspect: "1:1"
refs: []
---

ZONES:
- Top: Title "每个参数自己的学习率" and formula vₜ = β₂·vₜ₋₁ + (1−β₂)·gₜ²
- Center: A split visual — left side shows a "大梯度参数" (tall bar) with a small arrow (减速), right side shows a "小梯度参数" (short bar) with a large arrow (加速)
- Middle: The vₜ mechanism illustrated as a scale/divider: large v → η/√v small; small v → η/√v large
- Bottom left: 大梯度 → v大 → 步长自动变小 (red to green gradient)
- Bottom right: 小梯度 → v小 → 步长自动变大 (green to blue gradient)
- Arrow connecting: "不需要手动调！vₜ 替你算好了"

LABELS:
- Title: 每个参数自己的学习率
- Left bar: 大梯度参数 → v 大 → 减速
- Right bar: 小梯度参数 → v 小 → 加速
- Middle: η / √vₜ
- Bottom: 自动调速，无需手动！

COLORS:
- Background: warm cream
- Large gradient bar: red/orange
- Small gradient bar: blue
- v divider: neutral gray
- Step arrows: green (correctly sized steps)
- Annotation text: dark charcoal

STYLE: notion clean infographic, bar/arrow visual metaphor, clear size contrast, Chinese labels
ASPECT: 1:1 square
