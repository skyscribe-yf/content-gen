---
illustration_id: 03
type: infographic
style: notion
palette: warm
---

链式法则的魔法 - softmax+交叉熵梯度简化为 p-y

Minimalist hand-drawn line art style on warm cream (#FFFAF0) background. Intentional wobble on all lines. Generous white space. Chinese text labels, large and prominent with handwritten-style fonts.

LAYOUT: Central transformation diagram, top-to-bottom flow.

TOP: Complex formula block (hand-drawn box with scribbled math inside):
"∂L/∂zᵢ = Σₖ (−yₖ/pₖ) · pₖ·(δₖᵢ − pᵢ)"
- Show crossing-out lines through pₖ and −yₖ/pₖ canceling out

MIDDLE: Large downward arrow with label "约掉了！" and sparkles/doodle decorations around it

BOTTOM: Clean result in a highlighted box:
"∂L/∂zᵢ = pᵢ − yᵢ"
- Two side annotations:
  Left: "sigmoid + 交叉熵 → ŷ − y"
  Right: "softmax + 交叉熵 → p − y"
- Both connected by "=" sign with label "同一套魔法"

BOTTOM TAGLINE: Hand-lettered: "复杂的导数约掉后，只剩预测减真实"

COLORS: Cream background (#FFFAF0), Golden Yellow (#F6AD55) for the highlighted result box, Warm Orange (#ED8936) for sparkles/emphasis, Near Black (#1A1A1A) for all lines and text. Color accents under 10%.

STYLE: Clean composition with generous white space. Simple or no background. Main elements centered. Hand-drawn wobble on all lines. Chinese labels only. No computer fonts, no gradients, no shadows.

ASPECT: 16:9, medium complexity
