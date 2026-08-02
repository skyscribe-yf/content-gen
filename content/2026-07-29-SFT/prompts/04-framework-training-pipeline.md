---
type: framework
style: notion
palette: warm
aspect: "16:9"
lang: zh
---

Create a pipeline/framework diagram showing the three stages of LLM training.

THREE STAGES IN A LEFT-TO-RIGHT PIPELINE:

STAGE 1 - "预训练" (Pre-training):
- Icon: A large open book or globe with text flowing out
- Label: "学语言" (Learn Language)
- Key characteristic: "分布宽：什么都可能说" (Wide distribution: anything possible)
- Data: "互联网文本" (Internet text)
- Loss: "下一个 token 预测" (Next token prediction)
- Color: Soft warm beige

STAGE 2 - "SFT" (Supervised Fine-Tuning):
- Icon: A clipboard or instruction manual
- Label: "学听话" (Learn to Follow Instructions)
- Key characteristic: "分布窄：该说什么就说什么" (Narrow distribution: say what should be said)
- Data: "指令-回答对" (Instruction-response pairs)
- Loss: "交叉熵 (one-hot)" (Cross-entropy with one-hot)
- Highlighted with a border or glow as the current article's focus
- Color: Warm coral/amber

STAGE 3 - "RLHF/DPO":
- Icon: A thumbs-up or heart symbol
- Label: "学说好话" (Learn to Speak Well)
- Key characteristic: "偏好对齐：选更好的回答" (Preference alignment: choose better responses)
- Data: "人类偏好数据" (Human preference data)
- Loss: "奖励模型 / DPO loss"
- Color: Warm gold, slightly muted (future topic)

ARROWS between stages showing progression
BOTTOM: A small note "每一步都不增加知识，只改变分布形状" (Each step adds no knowledge, only changes distribution shape)

Style: Clean Notion-style framework diagram, warm palette, modern and minimal. No photos, no realistic humans. White/light background.
