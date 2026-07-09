---
illustration_id: 05
type: flowchart
style: notion
palette: warm
---

语言模型输出层 - 每生成一个词的全流程

Minimalist hand-drawn line art style on warm cream (#FFFAF0) background. Intentional wobble on all lines. Generous white space. Chinese text labels, large and prominent with handwritten-style fonts.

LAYOUT: Left-to-right flowchart with 5 stages connected by hand-drawn arrows.

STAGE 1 - "输入序列":
- Icon: stack of word cards (你好, 今天, 天气)
- Label: "token 序列"

STAGE 2 - "Transformer 层":
- Icon: stacked rectangles with attention arrows
- Label: "多层自注意力"

STAGE 3 - "Logits 向量":
- Icon: tall vertical bar chart (129,280 bars, most tiny)
- Big label: "129,280维" with annotation "DeepSeek-V4 词表"
- Label: "原始分数"

STAGE 4 - "Softmax":
- Icon: probability distribution curve
- Label: "分数→概率"

STAGE 5 - "采样输出":
- Icon: pointing hand selecting one bar
- Two sub-annotations: "top-k: 只看前k个" and "top-p: 只看累计p%"
- Label: "下一个词"

BOTTOM TAGLINE: Hand-lettered: "每一步都对12万+个候选词做softmax"

COLORS: Cream background (#FFFAF0), Warm Orange (#ED8936) for the Softmax stage highlight, Golden Yellow (#F6AD55) for logits bars, Terracotta (#C05621) for the output, Near Black (#1A1A1A) for all lines and text. Color accents under 15%.

STYLE: Clean composition with generous white space. Simple or no background. Hand-drawn wobble on all lines. Chinese labels only. No computer fonts, no gradients, no shadows. Flow arrows with slight curve.

ASPECT: 16:9, medium complexity
