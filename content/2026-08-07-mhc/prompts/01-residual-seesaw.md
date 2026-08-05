---
type: comparison
slug: residual-seesaw
backend: zairouter
model: gpt-image-2
size: "1:1"
quality: high
language: zh
output: "../01-residual-seesaw.png"
references: []
---

# FULL PROMPT

生成一张正方形中文对比信息图，解释残差连接的跷跷板困境：Pre-Norm 梯度稳但表征坍缩，Post-Norm 表征多样但梯度消失。使用左右两栏结构，风格克制、信息清晰。

## ZONES

- 中央：一个跷跷板，两端各坐着一个方块。
- 左端下沉：方块上标“Pre-Norm”，旁边标注“梯度稳定”，跷跷板下方一行小字“表征坍缩——深层 hidden state 趋同”。
- 右端上翘：方块上标“Post-Norm”，旁边标注“表征多样”，跷跷板下方一行小字“梯度消失——深层训不动”。
- 跷跷板支点处：一个齿轮，标注“1:1 硬编码混合”，暗示问题出在固定的混合比例。
- 顶部标题：“残差的跷跷板”。

## LABELS

- 只允许出现：“残差的跷跷板”、“Pre-Norm”、“Post-Norm”、“梯度稳定”、“表征多样”、“表征坍缩——深层 hidden state 趋同”、“梯度消失——深层训不动”、“1:1 硬编码混合”。
- 不添加任何数字、英文说明、品牌 Logo、公式、网址或额外标语。

## COLORS

- 背景：温暖象牙白。
- Pre-Norm 端：琥珀色系。
- Post-Norm 端：深青色系。
- 支点齿轮：石墨黑。
- 文字：深石墨黑。

## STYLE

- 精确的扁平编辑插画，细线、几何块面。
- 中文排版干净，无多余装饰，信息层次清楚。
