---
type: framework
slug: inference-acceleration-map
backend: zairouter
model: gpt-image-2
size: 1:1
quality: high
language: zh
references: []
---

# FULL PROMPT

Create a square Chinese technical framework infographic mapping four inference-optimization techniques to the part of the serving path they actually improve. The central message is that each technique fixes a different bottleneck; none of them magically removes every source of first-response latency. Use one horizontal serving path as the spine and four clearly separated intervention cards connected to the relevant stage.

## ZONES

- Top: title and a compact serving-path spine with three stage labels: service scheduling, prefill, and decode.
- Middle: four equal cards arranged in a balanced two-by-two grid, each with one technique, one mechanism, and one scope statement.
- Draw a thin connector from each card to its primary stage. The first technique points to prefill, the second spans history reuse during decode, the third points to decode, and the fourth points to memory and data movement around inference.
- Bottom: a calm warning strip separating sampling behavior from latency optimization.

## LABELS

- Title: "四种加速手段，各自只解决一段"
- Spine labels: "服务调度" → "预填充" → "逐字生成"
- Card 1 technique: "减少输入"; mechanism: "少读一部分上下文"; scope: "主要降低首字延迟"
- Card 2 technique: "键值缓存"; mechanism: "避免重复重算历史"; scope: "减少重复计算，但仍占显存"
- Card 3 technique: "推测解码"; mechanism: "小模型先猜，大模型校验"; scope: "主要提高首字后的速度"
- Card 4 technique: "量化"; mechanism: "减少存储与搬运字节"; scope: "依赖硬件与算子实现"
- Bottom warning: "采样参数不是首字延迟的万能药"
- All visible explanatory text must be Chinese. Do not add model names, prices, fixed speedup multiples, dates, or unsupported performance claims.

## COLORS

- Background: off-white with graphite ink.
- Card 1: cyan accent; Card 2: teal accent; Card 3: amber accent; Card 4: brick-red accent used sparingly.
- Spine: dark graphite with cyan arrows.
- Warning strip: pale amber, dark text, no alarmist styling.
- Keep the palette multicolor but restrained; no purple gradient, no bokeh, no decorative blobs.

## STYLE

- High-end editorial framework graphic, flat vector with subtle paper grain, consistent cards, thin connector lines, precise alignment, compact but readable Chinese typography.
- Use simple abstract symbols for context, cache, draft-and-check, and reduced data width. Do not draw literal server racks or crowded code.
- Preserve clear hierarchy: stage first, technique second, scope limitation third.

## ASPECT

- Exact square canvas, 1024x1024 pixels.
- Stable two-by-two card grid with all text safely inside its card and no connector crossing through labels.

## NEGATIVE

- No claim that any method always halves latency, no one-size-fits-all arrow, no fake benchmark numbers, no unreadable filler text, no logo, no watermark.
