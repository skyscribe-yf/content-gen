---
type: framework
slug: hc-multistream
backend: zairouter
model: gpt-image-2
size: "1:1"
quality: high
language: zh
output: "../02-hc-multistream.png"
references: []
---

# FULL PROMPT

生成一张正方形中文架构信息图，解释 Hyper-Connections（HC）的多流结构：四条并行流，每层通过 pre 混合、post 分发、res 跨流路由三个映射与 Transformer 层连接。风格克制、信息清晰。

## ZONES

- 左侧：四条水平并行流（四条细长条带，上下排列），标注“4 条流”。
- 中部：四条流汇聚成一个方块，标注“pre 混合”，文字“匝道入口”，再进入一个大方块标注“Transformer 层”。
- 右侧：层输出经过一个方块标注“post 分发”，文字“匝道出口”，再回到四条流。
- 四条流之间：一个方形网格标注“res 跨流路由”，文字“高速公路——连续 60 段”，表示流与流之间的路由混合。
- 顶部标题：“HC：把一条路扩成四条”。

## LABELS

- 只允许出现：“HC：把一条路扩成四条”、“4 条流”、“pre 混合”、“匝道入口”、“Transformer 层”、“post 分发”、“匝道出口”、“res 跨流路由”、“高速公路——连续 60 段”。
- 不添加任何数字、英文说明、品牌 Logo、公式、网址或额外标语。

## COLORS

- 背景：温暖象牙白。
- 四条流：石墨灰渐变色。
- pre / post 方块：琥珀色系。
- res 网格：深青色系。
- Transformer 层：浅灰。
- 文字：深石墨黑。

## STYLE

- 精确的扁平编辑插画，细线、几何块面、清晰箭头。
- 中文排版干净，无多余装饰，信息层次清楚。
