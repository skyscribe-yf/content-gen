---
type: framework
slug: v4-layout
backend: zairouter
model: gpt-image-2
size: "1:1"
quality: high
language: zh
output: "../05-v4-layout.png"
references: []
---

# FULL PROMPT

生成一张正方形中文架构信息图，展示 DeepSeek-V4 的 61 层里 mHC 模块的布局与优化器分组：每层两个 mHC，mHC 静态偏置归 AdamW，主模型参数归 Muon。风格克制、信息清晰。

## ZONES

- 顶部：一条水平带，由 61 个小块组成，标注“61 层”，其中前三个小块用虚线标出，表示前几层的差异。
- 中部：放大展示一个层的结构：“mHC₁ → 注意力 → mHC₂ → FFN”，两个 mHC 方块用深青色标出，标注“每层 2 个 mHC = 122 个”。
- 下方：两行分组说明：
  - 第一行小方块标注“mHC 静态偏置 + gating → AdamW”。
  - 第二行大方块标注“主模型参数 → Muon”。
- 底部一行小字：“新组件从恒等出发，不破坏已有训练动态”。
- 顶部标题：“V4 里的 mHC：61 层 × 2 = 122 个模块”。

## LABELS

- 只允许出现：“V4 里的 mHC：61 层 × 2 = 122 个模块”、“61 层”、“mHC₁ → 注意力 → mHC₂ → FFN”、“每层 2 个 mHC = 122 个”、“mHC 静态偏置 + gating → AdamW”、“主模型参数 → Muon”、“新组件从恒等出发，不破坏已有训练动态”。
- 不添加任何数字、英文说明、品牌 Logo、公式、网址或额外标语。

## COLORS

- 背景：温暖象牙白。
- mHC 方块：深青色。
- 注意力 / FFN 方块：浅灰。
- AdamW 行：琥珀色标签。
- Muon 行：石墨黑标签。
- 文字：深石墨黑。

## STYLE

- 精确的扁平编辑插画，细线、几何块面、清晰箭头。
- 中文排版干净，无多余装饰，信息层次清楚。
