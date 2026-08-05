---
type: infographic
slug: muon-v4-strategy
backend: zairouter
model: gpt-image-2
size: "1:1"
quality: high
language: zh
output: "../05-muon-v4-strategy.png"
references: []
---

# FULL PROMPT

生成一张正方形中文技术信息图，总结 DeepSeek-V4 的 Muon 使用策略：绝大多数参数交给 Muon，少数参数留 AdamW；更新矩阵 RMS 缩放到 0.18；正交化让热冷专家的更新幅度拉平。使用分区结构，风格克制、信息清晰。

## ZONES

- 顶部标题区：一句简短标题。
- 左区（占画布大部分）：一个大色块标注“绝大多数参数 → Muon”，色块内画两个等长的小条，分别标“热门专家”和“冷门专家”，旁边标注“更新幅度拉平，防 expert collapse”。
- 右上区：三个小块依次标注“embedding”、“输出层”、“RMSNorm”，用箭头指向“AdamW”，标注“保留精调”。
- 底部一行小字：“更新矩阵 RMS 缩放到 0.18，复用 AdamW 学习率”。

## LABELS

- 标题：“V4 的分组策略”
- 只允许出现：“绝大多数参数 → Muon”、“热门专家”、“冷门专家”、“更新幅度拉平，防 expert collapse”、“embedding”、“输出层”、“RMSNorm”、“AdamW”、“保留精调”、“更新矩阵 RMS 缩放到 0.18，复用 AdamW 学习率”。
- 不添加任何数字（0.18 除外）、英文说明、品牌 Logo、公式、网址或额外标语。

## COLORS

- 背景：温暖象牙白。
- Muon 大色块：青绿色系。
- AdamW 小块：琥珀色系。
- 两个专家小条：石墨灰，等长。
- 文字：深石墨黑。

## STYLE

- 精确的扁平编辑插画，细线、几何块面。
- 中文排版干净，无多余装饰，信息层次清楚。

## NEGATIVE

- 不要人物、Logo、网址、英文句子、公式、复杂电路板、3D 透视和主导性渐变。
