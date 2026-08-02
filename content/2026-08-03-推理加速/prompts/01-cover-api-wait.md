---
type: cover
slug: api-wait
backend: zairouter
model: gpt-image-2
size: 21:9
quality: high
language: zh
references: []
---

# FULL PROMPT

Create a cinematic editorial cover illustration for a Chinese technical article about why a large-model API feels slow before the first visible response. The core visual idea is that an API request does not travel directly to a GPU: it passes through a long service chain before the first token appears. Use a sophisticated technical magazine aesthetic, precise geometry, restrained visual density, and strong negative space for the title. Do not use a literal server-room stock photo.

## ZONES

- Left third: a small laptop or terminal sends one bright request signal into the system, suggesting a user pressing send.
- Center: a transparent layered service pipeline with gateway, routing, waiting queue, and model computation represented as distinct stages. Several request particles are visibly waiting in a queue; the pipeline should feel like a sequence of gates, not a direct cable.
- Right third: a clean client screen receives one bright first response signal, with the visual tension resolving only at the far right. A subtle GPU compute block is behind the pipeline, showing that the GPU is only one stage.
- Keep the lower half calm and uncluttered. Reserve the upper-left to center-left area for readable title typography.

## LABELS

- The only visible title text must be exactly: "大模型 API 为什么这么慢？首字延迟揭秘"
- Render the title in large, crisp Chinese sans-serif typography, with correct punctuation and no line-breaking that changes the wording.
- Do not add any other visible words, captions, logos, dates, numbers, watermarks, or invented labels.

## COLORS

- Background: deep graphite and ink black, with a subtle ivory light field around the title.
- Pipeline signals: electric cyan and cool white.
- Waiting queue and warning accents: restrained amber, used sparingly.
- Text: warm white with one amber emphasis on "首字延迟" only if it remains perfectly legible.
- No purple gradient, no bokeh, no decorative blobs.

## STYLE

- High-end digital editorial illustration, cinematic wide composition, clean vector-like geometry blended with realistic light and shallow depth.
- Technical but human-centered: the user is waiting for the first response, while the hidden service chain is visibly doing work.
- Strong hierarchy, generous whitespace, sharp edges, coherent line weights, polished publication-ready finish.
- All explanatory visual marks must be abstract symbols only; avoid unreadable pseudo-text.

## ASPECT

- Exact wide canvas ratio 21:9, target size 1248x528 pixels.
- Keep all title glyphs safely inside the canvas and away from the crop edges.

## NEGATIVE

- No direct arrow from user to GPU, no single straight cable, no generic speedometer, no human portrait, no stock-photo collage.
- No English explanatory text besides the exact title's technical term "API".
- No extra numbers or years; do not introduce benchmark claims.
