# 文章写作流程（硬性门禁）

## 规则

每次开始起草文章大纲之前，**必须先调用 grill-me skill 与作者进行深入讨论**，讨论收敛后才能起笔撰写。禁止跳过 grill-me 直接起草大纲或正文。

Skill 位置：[`.agents/skills/grill-me/SKILL.md`](.agents/skills/grill-me/SKILL.md)

## 执行流程

1. 作者提出选题方向 → AI 加载 grill-me skill
2. grill-me 逐轮追问：意图、约束、核心冲突、类比选择、受众假设等
3. 讨论收敛后，AI 将结论写入 `.grill/<slug>.md` 日志
4. 确认 grill 日志无误 → 方可进入大纲起草

## 禁止行为

- 禁止在 grill-me 讨论完成前输出大纲或草稿
- 禁止 AI 单方面生成 grill 日志（必须经过逐轮追问）
- 禁止以"我已经了解了"跳过 grill-me 流程
