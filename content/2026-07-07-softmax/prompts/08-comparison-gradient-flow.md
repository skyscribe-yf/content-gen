---
illustration_id: 08
type: comparison
style: notion
palette: warm
---

三种温度的梯度流向对比 - 同一组 logits, 真实类别=第3个

Minimalist hand-drawn line art style on warm cream (#FFFAF0) background. Intentional wobble on all lines. Generous white space. Chinese text labels, large and prominent with handwritten-style fonts.

LAYOUT: Three horizontal bar charts stacked vertically.

HEADER: "logits = [2.1, -0.3, 5.7], 真实类 = 第1个 (预测错了)"

CHART 1 - "T=0.1 (argmax幽灵)":
- Three horizontal bars:
  - 类别1(真实类): large negative bar (−10.0) labeled "−10.0"
  - 类别2: nearly zero bar labeled "≈0"
  - 类别3(预测最大): large positive bar (+10.0) labeled "+10.0"
- Annotation: "梯度巨大，只看2个类"

CHART 2 - "T=1.0 (标准平衡)":
- Three horizontal bars:
  - 类别1(真实类): large negative bar (−0.973) labeled "−0.973"
  - 类别2: tiny positive bar (0.002) labeled "0.002"
  - 类别3(预测最大): large positive bar (0.971) labeled "0.971"
- Annotation: "所有类都有信号"

CHART 3 - "T=5.0 (均匀稀释)":
- Three horizontal bars:
  - 类别1(真实类): moderate negative bar (−0.146) labeled "−0.146"
  - 类别2: small positive bar (0.034) labeled "0.034"
  - 类别3(预测最大): moderate positive bar (0.112) labeled "0.112"
- Annotation: "信号均匀但推力弱"

BOTTOM TAGLINE: Hand-lettered: "低温梯度集中，高温梯度均匀——T=1 兼顾两者"

COLORS: Cream background (#FFFAF0), Warm Orange (#ED8936) for positive gradient bars, Terracotta (#C05621) for negative gradient bars, Near Black (#1A1A1A) for all lines and text. Color accents under 15%.

STYLE: Clean composition with generous white space. Simple or no background. Hand-drawn wobble on bar chart outlines. Chinese labels only. No computer fonts, no gradients, no shadows. Bar lengths proportional to actual gradient values.

ASPECT: 16:9, medium complexity
