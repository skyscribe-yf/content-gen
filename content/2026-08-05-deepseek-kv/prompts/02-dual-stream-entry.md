---
type: flowchart
slug: dual-stream-entry
backend: zairouter
model: gpt-image-2
size: "1:1"
quality: high
language: zh
output: "../02-dual-stream-entry.png"
references: []
---

# FULL PROMPT

生成一张正方形中文数据流信息图，解释 DeepSeek-V4 的 CSA 双流重叠压缩：两条 KV 流合并成一个压缩 entry，这个 entry 同时当 key 和 value。

## ZONES

- 上方：两排等宽的小方块，分别标“a 流”和“b 流”，表示两条 KV 流。
- 中部：两组小方块各自收缩，汇入一个较大的圆角方块，标注“压缩 entry”。
- 下方：从“压缩 entry”引出两条路径，一条标“当 key”，一条标“当 value”，指向同一个注意力输出节点，标注“K=V”。
- 相邻两组方块之间用浅色连线表示“重叠”，标注“相邻摘要共享范围”。

## LABELS

- 只允许出现：“a 流”、“b 流”、“压缩 entry”、“当 key”、“当 value”、“K=V”、“相邻摘要共享范围”。
- 不添加任何数字、英文说明、品牌 Logo、公式、网址或额外标语。

## COLORS

- 背景：温暖象牙白。
- a 流：琥珀色系。
- b 流：深青色系。
- 压缩 entry 与 K=V 路径：石墨黑描边 + 金色高亮。
- 文字：深石墨黑。

## STYLE

- 精确的扁平编辑插画，细线、几何块面、清晰箭头。
- 中文排版干净，无多余装饰。