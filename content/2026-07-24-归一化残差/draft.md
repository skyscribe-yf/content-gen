---
title: "归一化为什么总在前面？61层模型靠它不崩"
author: "数解AI"
digest: "归一化为什么放在残差连接前？从 LayerNorm 到 RMSNorm，看 Pre-Norm 如何稳定 Transformer 的激活尺度，并读懂 61 层 DeepSeek-V4-Pro 的真实结构。"
type: "原理篇"
series: "大模型原理"
keywords: ["归一化", "RMSNorm", "Pre-Norm"]
cover: 00-cover.png
scheduledPublish: "2026-07-24T19:30:00+08:00"
---

## 残差都开了直通车，61 层为什么还要归一化？

![](00-cover.png)

前一篇 [残差连接](https://mp.weixin.qq.com/s/xefNN9Gjaw3TKl60KeHzAg) 解决的是一件很重要的事：深网络里，原始信号不必每次都穿过一个复杂变换，可以沿捷径直接往下走。

可这还不够。把 61 个 Transformer Block 叠起来，真正麻烦的不是“有没有路”，而是每走一层，路上的信号会不会越滚越大、越滚越小。残差给了信号一条直通车，归一化做的则像稳压器：它不替你决定信息该怎么变，只确保 Attention 和 FFN 每次接手时，面对的是一个尺度可控的输入。

这正是现代大模型普遍把归一化放在子层前面的原因：**残差保住信息和梯度的通路，归一化管住每次加工的数值尺度。**

![](01-residual-and-norm.png)

## 恒等捷径保真，不等于相加之后的尺度不变

把残差块写成 **y = x + F(x)**。捷径上的恒等映射确实很“老实”：**‖Ix‖₂ = ‖x‖₂**。它既不把 x 放大，也不旋转 x；原始向量沿这条分支过去，范数不会因为捷径本身改变。

但别把这句话偷换成“残差连接会自动稳定数值”。真正送到下一层的是 **x + F(x)**。F(x) 可能和 x 同方向，把模长推大；也可能反方向，抵消一部分。也就是说，恒等分支保住了原件，**两份东西相加后的尺度仍然会变**。

这就像你每次都把原始文档存一份，确实不会丢稿；但你还在不断把修改意见并进主文档，几十轮之后，文档的长度和重点仍可能失控。残差解决“原件会不会丢”，归一化解决“下一位编辑拿到的稿子会不会大到没法处理”。

## 归一化不是把信息洗成一样

对一个 token 的隐藏向量 x，LayerNorm 在它自己的特征维度上计算均值和方差：

> **μ = (1/d)Σᵢxᵢ，σ² = (1/d)Σᵢ(xᵢ−μ)²**

然后把它拉回一个可控尺度：

> **LN(x) = γ ⊙ (x−μ)/√(σ²+ε) + β**

这里 γ 和 β 是模型自己学的缩放与平移，ε 是防止除以零的小常数。它不是把每一维改成相同数字，而是先消掉“这一整行数整体偏大、偏小、偏正或偏负”的问题，再把细节差异交还给模型学习。

对 Transformer 来说，关键在“每个 token 自己算”。一句话里，“银行”“河岸”“贷款”会各自按自己的隐藏向量调整尺度；不会把不同 token 强行拉成同一种表示。

![](02-layernorm-rmsnorm.png)

后来许多大模型改用 RMSNorm。它不再减均值，只按均方根缩放：

> **RMSNorm(x) = γ ⊙ x/√((1/d)Σᵢxᵢ²+ε)**

少了一步“把均值移回零”，计算更轻；但对子层而言，最关键的尺度控制还在。RMSNorm 的原始论文提出的正是这个取舍：保留重新缩放，省掉在许多场景中并不必要的重新居中。[RMSNorm 原论文](https://arxiv.org/abs/1910.07467)

所以别把“归一化”理解成“信息变少”。更准确的说法是：**让子层少关心输入到底有多大，把精力放在输入里有什么结构。**

## 放在前面，残差的直通路才真的好走

原始 Transformer 常见的 Post-Norm 写法是：

> **xₗ₊₁ = Norm(xₗ + Fₗ(xₗ))**

先做子层变换、和残差相加，再归一化。它当然能把这一轮的输出拉回尺度，但归一化也站在残差主路的后面：每一层的主路都得经过一次 Norm。

Pre-Norm 把位置换过来：

> **xₗ₊₁ = xₗ + Fₗ(Norm(xₗ))**

现在 Norm 只服务于分支 Fₗ：Attention 或 FFN 先吃到稳定尺度的输入，再把自己学到的“增量”加回原来的 xₗ。残差主路仍是直接相加的链条。注意，Pre-Norm 不是让 xₗ 的模长永远不变；它保证的是每一层准备加工时，**Fₗ 的输入尺度可控**。

这点对训练尤其重要。研究者比较两种位置后发现，Post-Norm 在初始化时靠近输出端的参数梯度可能偏大，往往更依赖学习率 warm-up；Pre-Norm 的初始化梯度更平稳，因此通常更容易把深 Transformer 训起来。[Pre-Norm 分析论文](https://arxiv.org/abs/2002.04745)

“更容易训练”不等于 Post-Norm 一定错误。它是结构与训练配方的取舍；但当模型很深、训练预算又昂贵时，先把分支输入稳住，通常是更省心的默认选择。

![](03-pre-norm-vs-post-norm.png)

## 一层 Pre-Norm Transformer，代码其实只多了两次“先稳住”

把 Attention 和 FFN 的内部细节暂时折起来，简化版 Block 只有这几步：

```python
def transformer_block(x):
    a = rms_norm(x)          # 先稳住 Attention 的输入
    x = x + attention(a)     # 残差加回原始状态
    f = rms_norm(x)          # 再稳住 FFN 的输入
    x = x + ffn(f)           # 继续保留直通主路
    return x
```

代码里没有“把残差归一化”的一行，因为分工本来就不是这样：RMSNorm 把每次送进子层的输入拉到合适尺度；两次加法让状态和梯度有直达通路。你可以把它读成一句节奏：**先稳住，做增量，再加回；再稳住，再加回。**

![](04-prenorm-block.png)

## DeepSeek-V4-Pro 不是普通残差的复读机

2026 年 4 月的 DeepSeek-V4-Pro 把这条原则用在了 61 层模型上。其固定版本 [config.json](https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/blob/b5968e9190ef611bbf34a7229255be88a0e937c1/config.json) 写有 `num_hidden_layers: 61`、`hidden_size: 7168` 与 `rms_norm_eps: 1e−6`；官方推理代码也在 Attention 和 FFN 前分别建立了 `attn_norm`、`ffn_norm`。[Block 实现](https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/blob/b5968e9190ef611bbf34a7229255be88a0e937c1/inference/model.py)

但它没有把残差停在最朴素的 **x + F(x)**。同一份配置里的 `hc_mult: 4`，以及代码中的 Hyper-Connections，维护并混合多份隐藏状态；官方注释直接说明，这是对“简单残差”的替代。它仍然保留了“先用 RMSNorm 稳定子层输入”的思路，却把那条单一捷径扩展成可学习的多通路。

这正好提醒我们：文章里的 8 行伪代码是读懂 Transformer 分工的骨架，不是把所有新架构压扁成同一种实现。**归一化和残差是两种职责；具体怎么连线，模型还会继续进化。**

![](05-deepseek-v4-norm-hc.png)

## 回到开头：模型不崩，靠的不是其中一个“神招”

61 层网络能工作，不是因为残差把一切数值问题都解决了，也不是因为归一化替模型保存了信息。恒等捷径让原始状态有不被变换的通路；RMSNorm 让 Attention 和 FFN 不必反复适应忽大忽小的输入；Pre-Norm 则把两件事排成了对的顺序。

所以，归一化放在前面，不是装饰性的惯例。它是在告诉每个子层：“你可以大胆学增量，但先在稳定的尺度上工作。”

## 一句话总结

残差连接保住 **x** 的直通路，却不保证 **x + F(x)** 的整体范数不变；Pre-Norm 用 LayerNorm 或 RMSNorm 先稳定子层输入，再把增量加回去，才让深 Transformer 同时拥有可控尺度和可走通的梯度路径。

你会更愿意把一条残差主路保持为完全不动的“原件通道”，还是让它也学会混合多份状态？哪一种更让你安心？评论区聊聊。

关注「数解AI」，我们会继续把 Transformer 拆成一条能自己推演的链：前面讲 token 怎样进入模型，这篇讲各层怎样稳住自己，下一篇把这些零件重新装成完整 Transformer。

📖 **[大模型原理合集](https://mp.weixin.qq.com/mp/appmsgalbum?__biz=MzkyMzQyODExNQ==&action=getalbum&album_id=4597831652025925632#wechat_redirect)**：BPE → 词嵌入 → 位置编码 → 注意力 → FFN → **归一化与残差（本篇）** → Transformer 全景（待发布）

📖 **[训练回路合集](https://mp.weixin.qq.com/mp/appmsgalbum?__biz=MzkyMzQyODExNQ==&action=getalbum&album_id=4594958081087864833#wechat_redirect)**：梯度下降 → 损失函数 → 反向传播 → Softmax → 残差连接 → Adam
