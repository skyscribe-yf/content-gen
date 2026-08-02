---
illustration_id: 02
type: infographic
style: notion
palette: warm
aspect: "1:1"
---

## ZONES

### Zone 1 — Top: Traditional Attention (O(T²))
A grid of 5×5 dots representing token-to-token attention pairs. Each dot connected to every other dot with thin lines, creating a dense mesh. A red "×" overlay indicating this is the expensive approach. Label: "Traditional: O(T²)"

### Zone 2 — Bottom: KDA State Update (O(T))
A horizontal pipeline showing:
- Left: token k₁, k₂, ..., kₜ arriving one by one
- Center: A fixed-size state box S with the formula "Sₜ = α·Sₜ₋₁ + kₜ⊗vₜ"
- Right: Output qₜ · Sₜ
A green checkmark overlay. Label: "KDA: O(T)"

### Zone 3 — Central Arrow
A large downward arrow from top zone to bottom zone, with text "Fixed-size state replaces KV Cache"

## LABELS
- Top label: "Traditional Attention: O(T²)"
- Bottom label: "KDA Delta Update: O(T)"
- Formula in center: "Sₜ = α·Sₜ₋₁ + kₜ⊗vₜ"
- Annotation: "State S is fixed-size, does not grow with sequence length"

## COLORS
- Primary: #E8756D (warm coral for traditional/problem)
- Secondary: #7ECFC0 (warm teal for KDA/solution)
- Background: #FFF8F5 (warm white)
- Arrow: #B8A4D4 (warm purple)

## STYLE
Clean composition with generous white space. Simple flat illustration. Split-screen comparison layout (problem on top, solution on bottom). Notion-style with rounded rectangles and subtle shadows. Color values (#hex) and color names are rendering guidance only — do NOT display color names, hex codes, or palette labels as visible text in the image.

## ASPECT
1:1 square
