---
type: comparison
slug: csa-hca-division
backend: zairouter
model: gpt-image-2
size: "1:1"
quality: high
language: zh
output: "../04-comparison-csa-hca.png"
references: []
---

# FULL PROMPT

生成一张正方形中文技术对比信息图，解释 DeepSeek-V4 中 CSA 和 HCA 的互补分工。使用左右两栏和底部交替堆叠的简洁结构：CSA 精确选择重点，HCA 用极短摘要维持全局。

## ZONES

- 左栏：标题“CSA”，画出较短的压缩块池，Lightning Indexer 从中挑出少量高亮块，进入“精读重点”。
- 右栏：标题“HCA”，画出更短的摘要池，所有摘要块都进入 dense attention，进入“浏览全局”。
- 底部：两种模块交替排列成一条稳定的深层网络路径，标记“交替堆叠”。
- 视觉中心突出“精准”与“覆盖”的互补，而不是速度竞赛。

## LABELS

- 标题："CSA + HCA：一个精读，一个浏览"
- 左栏标签："CSA"、"压缩块"、"Lightning Indexer"、"Top-k"、"精读重点"
- 右栏标签："HCA"、"极短摘要"、"dense attention"、"浏览全局"
- 底部标签："交替堆叠"、"精准"、"覆盖"
- 只使用以上文字和技术缩写。

## COLORS

- 背景：暖白。
- CSA：琥珀色高亮重点块。
- HCA：深青色摘要块。
- 共同路径：石墨灰；“精准”用琥珀色，“覆盖”用青绿色。

## STYLE

- 扁平编辑信息图，左右对称、线条清楚、留白充足。
- 轻微纸张纹理，不要装饰性卡片堆叠、3D 透视或复杂渐变。
- 标签必须准确清晰，避免额外解释文字。

## ASPECT

- 正方形 1024x1024，移动端可读，所有元素位于安全区内。

## NEGATIVE

- 不要人物、Logo、网址、额外数字、英文段落、伪代码、乱码和主导性渐变。
