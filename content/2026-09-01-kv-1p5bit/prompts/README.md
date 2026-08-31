# KV 1.5bit 文章配图 Prompt 汇总

## 配图清单

| 编号 | 文件 | 类型 | 尺寸 | 位置 |
|------|------|------|------|------|
| 00 | 00-cover.md | AI 概念图 | 21:9（裁） | 封面 |
| 01 | 01-kv-notes.md | AI 概念图 | 1:1 | §一 |
| 02 | 02-quantization.md | AI 概念图 | 1:1 | §二 |
| 03 | 03-k-amplifier.md | AI 概念图 | 1:1 | §三 |
| 04 | 04-bit-width-ledger.png | 脚本图 | 1:1 | §四 |
| 05 | 05-task-compare.png | 脚本图 | 1:1 | §五 |
| 06 | 06-csa-hca.png | 脚本图 | 1:1 | §六 |

## 生成后端
- 默认：yairouter (gpt-image-2)，失败自动 fallback grok-imagine-image-quality
- 封面 21:9：生成后 PIL 裁剪（grok 输出 1024x1024 时也裁）

## 注意事项
- AI 概念图**禁止承载数字**（数字/结构全走脚本图）
- 图中若出现文字仅限符号性标注（K、V），与正文一致
- 色调：主蓝 #0F4C81（grace 主题）、白底、极简
- 生成后逐张核验
