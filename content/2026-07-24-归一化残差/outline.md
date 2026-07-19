---
title: "归一化为什么总在前面？61层模型靠它不崩"
scheduledPublish: "2026-07-24T19:30:00+08:00"
type: "原理篇"
series: "大模型原理"
image_type: "infographic / framework / comparison"
image_density: "5 张文内图 + 1 张封面"
image_style: "notion"
image_palette: "warm"
---

## 驱动问题

残差连接已经给深层网络留下不被变换的信号通路；为什么 Transformer 还要在 Attention 与 FFN 前加归一化？

## 逻辑链

1. 回链残差旧文：恒等捷径保留 x，但 x + F(x) 的整体范数仍会变化。
2. 归一化只约束每个 token 特征维度的尺度，不是把信息“洗成一样”。
3. 用 LayerNorm 与 RMSNorm 的最小公式区分“去中心 + 缩放”与“只看 RMS 缩放”。
4. 对比 Post-Norm 和 Pre-Norm：前者在相加后归一化，后者先稳定子层输入，再让残差流直通。
5. 用 8 行伪代码翻译一个简化的 Pre-Norm Transformer Block。
6. 以 2026 年 4 月 DeepSeek-V4-Pro 为真实案例：61 层、RMSNorm；说明其 Hyper-Connections 是残差的扩展，不能误写成普通 x + F(x)。

## 文章边界

- 残差回顾不重讲 ResNet、梯度公式和历史实验。
- 不给 LayerNorm/RMSNorm 的完整推导，不给可运行训练代码或横向模型评测。
- 文内用 Unicode 公式；正式配图生成后与 `weixin.md` 同级。

## 配图规划

### Illustration 1

**Position**: 开头说明残差与归一化分工之后。  
**Purpose**: 区分恒等捷径保真与相加结果尺度变化。  
**Filename**: `01-residual-and-norm.png`

### Illustration 2

**Position**: LayerNorm 与 RMSNorm 解释之后。  
**Purpose**: 对比“减均值 + 缩放”和“只按均方根缩放”。  
**Filename**: `02-layernorm-rmsnorm.png`

### Illustration 3

**Position**: Pre-Norm 与 Post-Norm 对比之后。  
**Purpose**: 看清归一化在相加前后的位置差异。  
**Filename**: `03-pre-norm-vs-post-norm.png`

### Illustration 4

**Position**: 8 行伪代码之后。  
**Purpose**: 用一张完整 Block 流程图连接两次“先稳住、再加回”。  
**Filename**: `04-prenorm-block.png`

### Illustration 5

**Position**: DeepSeek-V4-Pro 实践旁注之后。  
**Purpose**: 呈现 61 层、均方根归一化与四路隐藏状态的真实扩展。  
**Filename**: `05-deepseek-v4-norm-hc.png`
