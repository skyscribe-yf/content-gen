---
illustration_id: 04
type: infographic
style: notion
palette: warm
aspect: "1:1"
---

## ZONES

### Zone 1 — Left: Routing & Selection
A central "Router" box (rounded rectangle, warm purple) with arrows pointing to 12 small expert boxes arranged in a grid. Only 3 of the 12 experts are highlighted/glowing (representing top-16 selection from 896). The other 9 are grayed out. Label above: "896 Experts → Top 16 Active"

### Zone 2 — Center: Latent Projection
A flow diagram:
- Input: "x (7168-dim)" → down arrow labeled "W_down" → "x_latent (3584-dim)" → experts → "W_up" → output
A callout: "Communication halved via latent projection"

### Zone 3 — Right: Quantile Balancing
A small histogram/bar chart showing:
- Left side (before): uneven bars (some very tall, some short) — labeled "Unbalanced"
- Right side (after): bars of equal height — labeled "Quantile Balancing"
A formula annotation: "bᵢ ← Q_target - Qᵢ"

### Zone 4 — Bottom Summary
Three stat boxes in a row:
- "1.8% sparsity (16/896)"
- "104B active params"
- "2 shared experts"

## LABELS
- Router label: "Router g(x) = softmax(W_g·x)"
- Expert selection: "Top-16 from 896"
- Projection: "7168 → 3584 → 7168"
- Balancing: "Quantile Balancing: automatic load equalization"

## COLORS
- Primary: #E8756D (warm coral for active experts)
- Secondary: #7ECFC0 (warm teal for balanced state)
- Accent: #B8A4D4 (warm purple for router)
- Background: #FFF8F5 (warm white)
- Inactive experts: #D4D4D4 (light gray)

## STYLE
Clean composition with generous white space. Notion-style flat illustration. Three-panel layout (routing → projection → balancing). Rounded rectangles for components. Color values (#hex) and color names are rendering guidance only — do NOT display color names, hex codes, or palette labels as visible text in the image.

## ASPECT
1:1 square
