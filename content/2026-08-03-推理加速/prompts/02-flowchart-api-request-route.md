---
type: flowchart
slug: api-request-route
backend: zairouter
model: gpt-image-2
size: 1:1
quality: high
language: zh
references: []
---

# FULL PROMPT

Create a square Chinese technical infographic explaining the real path of a large-model API request before the user sees the first response. The image must show that the request is not a direct conversation with a GPU. Use a clean editorial flowchart with a left-to-right main route, clear arrows, evenly sized nodes, and enough whitespace for accurate Chinese labels. This is an information visualization, not a decorative illustration.

## ZONES

- Top band: a concise title area with the concept of a service chain between the user and model computation.
- Main canvas: seven connected stages from left to right, grouped into two softly outlined regions. The first four stages are the service layer; the last three are model inference and delivery.
- Add a small side queue beside the scheduling stage, with multiple request dots waiting in line. This should communicate batch scheduling and tail latency without adding any unrequested metrics.
- End at a small client screen on the right where the first response signal appears. The GPU or compute block must be shown inside the model-inference region, never as the first destination.

## LABELS

- Title: "调用接口，不是直达 GPU"
- Service-layer group label: "服务层"
- Model-and-delivery group label: "模型推理与返回"
- Seven stage labels, in this exact order: "客户端" → "网关与鉴权" → "模型路由" → "排队与批处理" → "预填充" → "逐字生成" → "流式返回"
- Queue callout: "等待调度"
- Final callout: "第一个字到达"
- All visible explanatory text must be Chinese. Do not add vendor names, fake timings, extra numbers, dates, or unsupported performance claims.

## COLORS

- Background: warm ivory, light gray, and graphite ink.
- Service-layer nodes: muted slate with amber highlights around queue and routing.
- Model-inference nodes: cyan and deep teal with a single restrained amber signal for the first response.
- Arrows: dark graphite, with the final response arrow in cyan.
- Use color to distinguish stages, never to imply a speed ranking.

## STYLE

- Precise flat-vector editorial infographic, subtle paper texture, thin technical lines, rounded rectangles no larger than necessary, consistent spacing and line weight.
- The diagram must be legible at mobile article width. Avoid tiny labels, dense pseudo-code, circuit-board ornament, and 3D clutter.
- Make the queue and stage boundaries visually obvious while preserving a calm, rigorous publication style.

## ASPECT

- Exact square canvas, 1024x1024 pixels.
- Use a stable seven-stage layout that does not crop or overlap labels.

## NEGATIVE

- No direct user-to-GPU arrow, no English labels except the technical acronym in the title, no unreadable placeholder text, no logos, no watermark, no gradients dominating the page.
