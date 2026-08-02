---
type: comparison
slug: dsa-csa-indexer
backend: zairouter
model: gpt-image-2
size: "1:1"
quality: high
language: zh
output: "../02-comparison-dsa-csa-indexer.png"
references: []
---

# FULL PROMPT

生成一张正方形中文技术对比图，解释 DSA 与 CSA 的关键差别：两者都使用 Lightning Indexer 做重点选择，但 DSA 在原始 token 池上打分，CSA 先把候选压成 KV 池再打分。使用左右两栏对比，箭头和候选池长度必须一眼可见。

## ZONES

- 顶部标题区。
- 左栏：长长的原始 token 池，许多小方块排成一行；Lightning Indexer 扫描整个池子，输出少量 Top-k，再进入核心注意力。
- 右栏：原始 token 先经过压缩，形成明显更短的 KV 池；Lightning Indexer 只扫描短池，输出少量 Top-k，再进入核心注意力。
- 两栏底部各有一句结论，右栏突出“先压缩，再选择”。

## LABELS

- 标题："DSA 与 CSA：索引器先面对什么？"
- 左栏标题："DSA"
- 左栏标签："原始 token 池"、"Lightning Indexer"、"Top-k"、"核心注意力"
- 左栏结论："核心变稀疏，候选仍很长"
- 右栏标题："CSA"
- 右栏标签："压缩 KV 池"、"Lightning Indexer"、"Top-k"、"核心注意力"
- 右栏结论："先压缩，再选择"
- 只使用以上文字和技术缩写。

## COLORS

- 背景：暖白。
- DSA：石墨灰与琥珀色。
- CSA：青绿色与深青色。
- 原始 token 池用密集灰色小块，压缩 KV 池用少量青绿色块。

## STYLE

- 清晰的扁平技术对比信息图，左右栏等宽，箭头方向明确。
- 轻微纸张纹理，细线和几何块面，适合移动端扫描。
- 中文必须准确清晰，不要把技术缩写改写，不要添加公式或未经给出的数字。

## ASPECT

- 正方形 1024x1024，所有标签在安全区域内，不重叠、不裁切。

## NEGATIVE

- 不要人物、Logo、网址、英文说明段落、额外数字、复杂背景、伪代码和主导性渐变。
