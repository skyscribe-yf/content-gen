---
illustration_id: 03
type: infographic
style: notion
palette: warm
aspect: "1:1"
---

## ZONES

### Zone 1 — Top: Traditional Residual (problem)
A vertical stack of 8 layer rectangles (representing layers 1-8), each connected to the next by a single upward arrow. The bottom layers are bright, the top layers are faded/desaturated, showing signal dilution. A red "×" overlay. Label: "Traditional Residual: signal dilutes with depth"

### Zone 2 — Bottom: Block AttnRes (solution)
Same 8 layers, but grouped into 2 blocks of 4. Within each block, layers are summed (thick arrow). Between blocks, a retrieval mechanism: the upper block has dotted attention arrows pointing back to representations in the lower block. A green checkmark overlay. Label: "Block AttnRes: retrieve from any earlier block"

### Zone 3 — Central Arrow
A large downward arrow with text "From chain to retrieval"

### Zone 4 — Side annotation
A small comparison box:
- "Traditional: O(Ld) active state"
- "Block AttnRes: O(Nd), N = L/12"

## LABELS
- Top: "Traditional Residual: hₗ = hₗ₋₁ + f(hₗ₋₁)"
- Bottom: "Block AttnRes: hₗ = Σ βⱼ·Blockⱼ + f(hₗ₋₁)"
- Annotation: "Each layer can retrieve from any earlier block, not just the previous layer"

## COLORS
- Primary: #E8756D (warm coral for traditional/problem)
- Secondary: #7ECFC0 (warm teal for AttnRes/solution)
- Accent: #B8A4D4 (warm purple for retrieval arrows)
- Background: #FFF8F5 (warm white)

## STYLE
Clean composition with generous white space. Split-screen comparison. Notion-style flat illustration with rounded rectangles. Dotted lines for attention retrieval, solid lines for residual. Color values (#hex) and color names are rendering guidance only — do NOT display color names, hex codes, or palette labels as visible text in the image.

## ASPECT
1:1 square
