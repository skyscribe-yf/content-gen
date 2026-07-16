---
illustration_id: 04-probability-distribution
type: comparison
style: vector-illustration
palette: warm
---

Three-Stage Probability Distribution Comparison

Side-by-side comparison of three probability distributions at different training stages. Demonstrates how the model's output distribution evolves from uniform precision.

LAYOUT: Three vertical panels, left to right.

LEFT PANEL: "初始状态 ppl≈109"
- Visual: Nearly uniform bar chart — 10 bars of almost equal short height
- Label: "近似均匀分布 — 每个字概率 ~1%"
- Color: Pale gray bars on peach background

MIDDLE PANEL: "中期 ppl≈5"
- Visual: Several bars are now taller (peaking around common characters), others shorter
- Label: "尖峰初现 — 高频字概率升高"
- Color: Warm Orange (#ED8936) for peaks, terracotta for short bars

RIGHT PANEL: "收敛 ppl≈2"
- Visual: One very tall sharp peak (correct token), others minimal
- Label: "尖峰精准 — 模型确定了"
- Color: Coral Red (#E07A5F) for the peak, minimal others

Each panel has a small perplexity gauge icon below showing the ppl value.

CONNECTING ELEMENTS: Upward arrow between panels showing sharpening distribution. Label: "Perplexity 持续下降".

COLORS: Soft Peach background (#FFECD2), black outlines, warm palette fills

STYLE: Clean scientific visualization, bold labels, clear contrast between stages

ASPECT: 1:1
COMPOSITION: balanced three-panel comparison
