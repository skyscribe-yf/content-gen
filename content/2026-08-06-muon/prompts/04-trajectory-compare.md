---
type: comparison
slug: trajectory-compare
backend: zairouter
model: gpt-image-2
size: "1:1"
quality: high
language: zh
output: "../04-trajectory-compare.png"
references: []
---

# FULL PROMPT

生成一张正方形中文对比示意图，对比 AdamW 与 Muon 在窄谷地形上的优化轨迹：AdamW 之字震荡，Muon 近直线下降。使用左右两栏的椭圆等高线图，风格克制、信息清晰。

## ZONES

- 顶部标题区：一句简短标题。
- 左栏：一张椭圆等高线图（长而窄的椭圆谷），一条来回震荡的之字形路径从边缘走到中心，标注“AdamW：对角缩放，之字前进”。
- 右栏：同一形状的椭圆等高线图，一条近乎直线的路径直达中心，标注“Muon：正交化，直线下降”。
- 两栏共用底部一行小字：“椭圆越扁，条件数越大，之字越明显”。

## LABELS

- 标题：“窄谷里谁走得更直？”
- 只允许出现：“AdamW：对角缩放，之字前进”、“Muon：正交化，直线下降”、“椭圆越扁，条件数越大，之字越明显”。
- 不添加任何数字、英文说明、品牌 Logo、公式、网址或额外标语。

## COLORS

- 背景：温暖象牙白。
- 椭圆等高线：浅灰，中心最低点用深青色点。
- AdamW 轨迹：琥珀色，之字折线。
- Muon 轨迹：深青色，直线。
- 文字：深石墨黑。

## STYLE

- 精确的扁平编辑插画，细线、几何块面。
- 轨迹线清晰可辨，中文排版干净，无多余装饰。

## NEGATIVE

- 不要人物、Logo、网址、英文句子、公式、复杂电路板、3D 透视和主导性渐变。
