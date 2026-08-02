---
type: timeline
slug: ttft-vs-tps
backend: zairouter
model: gpt-image-2
size: 1:1
quality: high
language: zh
references: []
---

# FULL PROMPT

Create a square Chinese editorial infographic that separates two user-visible performance dimensions of a large-model API: time until the first response and speed after that response begins. Use two aligned horizontal timelines with identical starting points so the contrast is immediately understandable. Do not invent measured timings; communicate the difference through relative spacing only.

## ZONES

- Top: a clear title and a short divider separating two scenarios.
- Upper timeline: a long quiet interval after the request, then one first-response marker near the right; show the user waiting with no visible output during the long interval.
- Lower timeline: a short interval to the first-response marker, followed by widely spaced output markers that continue slowly.
- Right margin: a compact two-line takeaway contrasting the two bottlenecks.
- Keep both timelines aligned and use one visual language for start markers, first-response markers, and subsequent output markers.

## LABELS

- Title: "首字延迟，不等于生成速度"
- Upper scenario label: "首字延迟高"
- Upper timeline labels: "请求发出" and "第一个字到达"
- Lower scenario label: "首字快，首字后速度低"
- Lower timeline labels: "请求发出", "第一个字到达", and "连续输出"
- Right-side takeaway lines: "先等多久" and "之后说多快"
- Keep the technical acronyms exactly as small secondary labels: "TTFT" beside "首字延迟", and "TPS" beside "首字后速度". All other visible explanatory text must be Chinese.
- Do not add numbers, dates, vendor names, fake axes, or benchmark values.

## COLORS

- Background: pale ivory with graphite text.
- Upper timeline: amber waiting band and a single amber first-response marker.
- Lower timeline: cyan first-response marker followed by muted slate output markers.
- Use a small green check-like accent only for the concept that output has started; avoid making it a product badge.
- No purple gradient and no decorative blobs.

## STYLE

- Minimal, precise data-storytelling graphic; clean editorial typography, thin timeline rules, crisp dots, balanced margins, no realistic people.
- Make the blank waiting interval visually substantial without turning it into a literal clock or speedometer.
- Ensure the title and every label are sharp, correctly spelled Chinese, and readable at 1024x1024.

## ASPECT

- Exact square canvas, 1024x1024 pixels.
- Stable two-row timeline grid with no overlap or cropped text.

## NEGATIVE

- No claim that TTFT and TPS are the same metric, no fake numeric scales, no direct GPU imagery, no unreadable filler text, no logo, no watermark.
