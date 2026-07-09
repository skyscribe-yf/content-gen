---
type: infographic
style: notion
palette: warm
aspect: "1:1"
refs: []
---

ZONES:
- Top: Title "高斯椭球困境" and formula f(x,y) = x²/100 + y²
- Center: A 2D contour plot showing highly elongated elliptical contours (ellipsoid shape, 100:1 aspect ratio)
- Overlay on contours: A zigzag optimization path (SGD trajectory) that oscillates violently in the y direction (steep axis) while barely progressing in the x direction (shallow axis)
- Left annotation: "x 方向：极平缓（该走的路，走不动）" pointing to shallow axis
- Right annotation: "y 方向：极陡峭（不该走的路，反复横跳）" pointing to steep axis
- Starting point marked with a dot labeled "起点", target minimum at center labeled "最小值"

LABELS:
- Title: 高斯椭球困境
- Formula: f(x, y) = x²/100 + y²
- Left annotation: x 方向 极平缓
- Right annotation: y 方向 极陡峭
- Path label: SGD 之字形震荡
- Points: 起点 → 之字形路径 → 最小值

COLORS:
- Background: warm cream
- Contours: muted gradient from light gray to warm brown
- SGD path: red/orange zigzag with arrows
- Steep axis: red highlight
- Shallow axis: blue highlight
- Start/min points: distinct circle markers

STYLE: notion clean scientific visualization, contour plot in warm tones, clear before/after contrast
ASPECT: 1:1 square
