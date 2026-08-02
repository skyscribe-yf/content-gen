---
type: infographic
slug: xunfei-ttft-buckets
backend: zairouter
model: gpt-image-2
size: 1:1
quality: high
language: zh
references: []
---

# FULL PROMPT

Create a square, publication-quality Chinese data infographic using the author's real Pi request logs for the xunfei / xopglm51 route. Show the relationship between input-length buckets and user-side first-response latency. This is an observational chart, not a vendor ranking and not a causal proof. Use a clean grouped bar chart with exact data labels, a faithful non-monotonic P90 series, and no invented values.

## ZONES

- Top: title and source note.
- Center: grouped bars for five input-length buckets. Each bucket has two bars: TTFT P50 in cyan and TTFT P90 in amber. Label every bar with the exact seconds value.
- Bottom: x-axis bucket labels and sample counts. Keep the five groups equally spaced and make the fourth group visibly high for P90; do not force the fifth P90 bar to keep rising.
- Add a small side callout explaining the main reading: the P50 rises from 4.7 seconds to 14.0 seconds as input moves from 0–16K to 96–128K, while P90 shows a long tail and does not form a perfectly monotonic line.
- Use an inset legend and a restrained note that the values are user-side observations from Pi logs.

## LABELS

- Title: "讯飞线路：输入越长，首字越晚"
- Source note: "Pi 实际请求日志｜主窗口：2026-07-20 至 2026-08-02"
- Y-axis: "首字延迟（秒）"
- X-axis: "输入长度（token）"
- Legend labels: "TTFT P50（中位数）" and "TTFT P90（长尾）"
- Exact x-axis labels, in order: "0–16K", "16–32K", "32–64K", "64–96K", "96–128K"
- Exact P50 values, in order: "4.7", "6.6", "7.9", "11.8", "14.0"
- Exact P90 values, in order: "19.3", "19.6", "22.5", "26.1", "24.1"
- Exact sample counts, in order: "样本 191", "样本 449", "样本 2,430", "样本 1,868", "样本 851"
- Callout text: "P50：4.7 秒 → 14.0 秒" and "P90 受路由、重试与负载影响"
- All visible explanatory text must be Chinese. Do not add other dates, providers, models, prices, ranks, cache claims, or fake data points.

## COLORS

- Background: warm white or very light gray.
- P50 bars: deep cyan with clear white numeric labels.
- P90 bars: amber-orange with dark numeric labels for contrast.
- Axes and body text: graphite.
- Use a thin red-orange warning rule only around the long-tail callout, not as a performance judgment.
- No purple gradient, no 3D bars, no photographic background.

## STYLE

- Rigorous editorial data visualization, crisp chart grid, generous margins, consistent numeral formatting, high legibility on a mobile screen.
- Keep the chart flat and two-dimensional. No perspective distortion, no decorative icons that compete with the data.
- Preserve the exact relative ordering: P50 is 4.7, 6.6, 7.9, 11.8, 14.0; P90 is 19.3, 19.6, 22.5, 26.1, 24.1.

## ASPECT

- Exact square canvas, 1024x1024 pixels.
- Make all axis labels, legend text, values, sample counts, and callouts fit without overlap or cropping.

## NEGATIVE

- No smooth trend line that implies P90 is monotonic, no supplier speed ranking, no cache-hit conclusion, no extra data, no unreadable pseudo-text, no logo, no watermark.
