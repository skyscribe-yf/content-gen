---
type: infographic
slug: outlier-scale
backend: zairouter
model: gpt-image-2
size: "1:1"
quality: high
language: zh
output: "../02-outlier-scale.png"
references: []
---

# FULL PROMPT

生成一张正方形中文对比信息图，解释一个 outlier 如何毁掉 per-tensor 量化：全局一个 scale 被 outlier 拉高，正常值全部挤进低精度区间。风格克制、信息清晰。

## ZONES

- 上方：一条水平数轴被一个巨大的柱子占据（柱子标注“outlier”），其余正常值挤在最左端一小块区域，标注“正常值被压扁”。
- 中部：一个放大镜对准被压扁的区域，里面显示粗大的台阶（只有 4-5 级），标注“台阶太粗，精度全毁”。
- 下方：对比小图——按行分组后，outlier 所在行单独被拉高，其余行台阶正常，标注“分组量化：只毁自己那组”。
- 顶部标题：“一个 outlier 毁掉整张图”。

## LABELS

- 只允许出现：“一个 outlier 毁掉整张图”、“outlier”、“正常值被压扁”、“台阶太粗，精度全毁”、“分组量化：只毁自己那组”。
- 不添加任何数字、英文说明、品牌 Logo、公式、网址或额外标语。

## COLORS

- 背景：温暖象牙白。
- outlier 柱子：赭红色。
- 正常值区域：浅灰。
- 分组对比图：深青色，正常台阶清晰。
- 文字：深石墨黑。

## STYLE

- 精确的扁平编辑插画，细线、几何块面、清晰的数轴与台阶。
- 中文排版干净，无多余装饰，信息层次清楚。
