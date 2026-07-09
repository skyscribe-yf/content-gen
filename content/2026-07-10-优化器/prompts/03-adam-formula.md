---
type: framework
style: notion
palette: warm
aspect: "1:1"
refs: []
---

ZONES:
- Top: Title "Adam 公式拆解" with subtitle "四个方程，四个动机"
- Four vertical panels, each containing one equation and its annotation:
  Panel 1: mₜ = β₁·mₜ₋₁ + (1−β₁)·gₜ  →  annotation: ① 给梯度加记忆（动量）
  Panel 2: vₜ = β₂·vₜ₋₁ + (1−β₂)·gₜ²  →  annotation: ② 追踪梯度尺度
  Panel 3: m̂ₜ = mₜ/(1−β₁ᵗ), v̂ₜ = vₜ/(1−β₂ᵗ)  →  annotation: ③ 偏差修正（前几步放大）
  Panel 4: θₜ₊₁ = θₜ − η · m̂ₜ / (√v̂ₜ + ε)  →  annotation: ④ 方向 ÷ 尺度 = 步长
- Bottom: Summary line "分子决定方向 · 分母决定步长 · 一一对应，没有多余"

LABELS:
- Title: Adam 公式拆解
- Each panel has equation + annotation
- Bottom summary: 分子 = 方向 · 分母 = 步长
- m̂ₜ highlighted in blue, √v̂ₜ in green

COLORS:
- Background: warm cream
- Panel backgrounds: slightly lighter cream with thin borders
- Equations: dark charcoal
- m̂ₜ terms: blue (#3B82F6)
- v̂ₜ terms: green (#10B981)
- Final formula: bold with orange accent
- Summary stripe: warm orange background

STYLE: notion clean framework diagram, equation cards, structured flow from top to bottom, Chinese labels
ASPECT: 1:1 square
