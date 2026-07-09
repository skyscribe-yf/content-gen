---
illustration_id: 02
type: comparison
style: notion
palette: warm
---

直接归一化 vs 指数归一化 - 负数问题与差距放大

Minimalist hand-drawn line art style on warm cream (#FFFAF0) background. Intentional wobble on all lines. Generous white space. Chinese text labels, large and prominent with handwritten-style fonts.

LAYOUT: Top | Bottom vertical comparison.

TOP ZONE - "直接归一化 ❌":
- Three boxes showing z=[2.1, -0.3, 5.7]
- Arrow down to "÷ sum(7.5)"
- Result: [0.28, -0.04, 0.76] with the -0.04 highlighted in red
- Red cross and label: "负概率！不可能"
- Small sketch of a confused stick figure

BOTTOM ZONE - "指数归一化 (Softmax) ✅":
- Three boxes showing z=[2.1, -0.3, 5.7]
- Arrow down to "e^z → ÷ sum"
- Result: [2.7%, 0.2%, 97.1%] all positive
- Annotation arrow showing "e^5.7 / e^2.1 ≈ 36倍" — gap amplified
- Small sketch of a happy stick figure

BOTTOM TAGLINE: Hand-lettered: "指数让负数变正，让差距放大"

COLORS: Cream background (#FFFAF0), Warm Orange (#ED8936) for positive/softmax accents, Soft Red (#E53E3E) for negative values, Near Black (#1A1A1A) for all lines and text. Color accents minimal.

STYLE: Clean composition with generous white space. Simple or no background. Main elements centered. Hand-drawn wobble on all lines. Chinese labels only. No computer fonts, no gradients, no shadows.

ASPECT: 16:9, medium complexity
