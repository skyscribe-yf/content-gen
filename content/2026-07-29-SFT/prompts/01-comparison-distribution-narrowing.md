---
type: comparison
style: notion
palette: warm
aspect: "16:9"
lang: zh
---

Create a side-by-side comparison of two BAR CHARTS (NOT bell curves, NOT smooth curves) showing token probability distributions. This is a CATEGORICAL distribution — bars must be arranged from TALLEST on the LEFT to SHORTEST on the RIGHT, descending order. There is NO symmetry. The first bar is always the tallest.

CRITICAL RULE: Do NOT draw bell curves, normal distributions, or any symmetric shape. These are DESCENDING BAR CHARTS where height strictly decreases from left to right.

LEFT CHART - "Base 模型":
- A bar chart with 10 vertical bars arranged in DESCENDING order (tallest bar on the far LEFT)
- Bar heights from left to right: 0.57, 0.21, 0.06, 0.06, 0.013, 0.010, 0.010, 0.008, 0.008, 0.008
- The first bar (0.57) is clearly the tallest but NOT dominant — the second bar (0.21) is still substantial
- Labels below bars: 算法, 法, ，, ，并, 。↵, ？, ？↵, 方法, 。↵↵, 。
- The distribution is SPREAD OUT — multiple bars have meaningful height
- Color: muted warm tones (soft orange bars)

RIGHT CHART - "Instruct 模型":
- A bar chart with 9 vertical bars arranged in DESCENDING order (tallest bar on the far LEFT)
- Bar heights from left to right: 0.81, 0.08, 0.08, 0.03, 0.003, 0.001, 0.001, 0.001, 0.001
- The first bar (0.81) DOMINATES — it towers above all others. The remaining bars are tiny in comparison
- Labels below bars: 梯, 当然, **, 好的, ", 好, ###, 很好, 「
- The distribution is HIGHLY CONCENTRATED — one bar dominates, rest are negligible
- Color: vibrant warm tones (bright coral for the dominant bar, lighter for others)

CENTER: A large arrow pointing left→right labeled "SFT"
BOTTOM: Key metric "熵: 0.90 bits → 0.33 bits (−63%)"

VISUAL EMPHASIS: The KEY difference is that the left chart has TWO substantial bars (0.57 and 0.21) while the right chart has ONE dominant bar (0.81) with everything else tiny. This contrast must be immediately visible.

Style: Clean infographic, warm palette, white/light background, no photos, no realistic humans. The bar charts must look like actual data visualizations with a y-axis showing probability from 0 to 1.
