---
type: comparison
style: notion
palette: warm
aspect: "1:1"
refs: []
---

ZONES:
- Top: Title "SGD vs Adam：同一个椭球，不同命运"
- Split into left/right halves comparing SGD and Adam on the same Gaussian ellipsoid
- LEFT (SGD): Ellipsoid contour with dramatic zigzag path (red), many steps, barely reaches center. Label: "SGD：同一个 η，震荡着往下蹭"
- RIGHT (Adam): Same ellipsoid contour with smooth curved path (blue), fewer steps, directly reaches center. Label: "Adam：方向 ÷ 尺度，一步到位"
- Bottom center: Summary comparison box:
  SGD: 步数多 · 方向乱 · 走不动
  Adam: 步数少 · 方向准 · 直切谷底

LABELS:
- Title: SGD vs Adam
- Left: SGD（之字形震荡）
- Right: Adam（弧线直切）
- Path labels: 起点 → 终点
- Comparison box: SGD vs Adam metrics

COLORS:
- Background: warm cream
- Left ellipsoid: slightly red-tinted
- Right ellipsoid: slightly blue-tinted
- SGD path: red/orange (#DC2626)
- Adam path: blue (#3B82F6)
- Comparison box: warm orange accent border
- Step counts: small number annotations

STYLE: notion clean side-by-side comparison, scientific contour plots, dramatic path contrast, Chinese labels
ASPECT: 1:1 square
