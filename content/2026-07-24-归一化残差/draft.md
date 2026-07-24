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

前一篇 [残差连接](https://mp.weixin.qq.com/s/xefNN9Gjaw3TKl60KeHzAg) 解决的是一件很重要的事：深度神经网络里，原始信号不必每次都穿过一个复杂变换，可以沿捷径直接往下走。

可这还不够。把 61 个 Transformer Block 叠起来，真正麻烦的不是"有没有路"，而是每走一层，路上的信号会不会越滚越大、越滚越小。残差给了信号一条直通车，归一化做的则像稳压器：它不替你决定信息该怎么变，只确保 Attention 和 FFN 每次接手时，面对的是一个尺度可控的输入。

这正是现代大模型普遍把归一化放在子层前面的原因：**残差保住信息和梯度的通路，归一化管住每次加工的数值尺度。**

![](01-residual-and-norm.png)

## 恒等捷径保真，不等于相加之后的尺度不变

把残差块写成 $y = x + F(x)$。先看捷径这条分路：恒等映射 $\|\text{id}(x)\|_2 = \|x\|_2$，不放大不旋转——原始向量沿捷径下去，长度不变。

这里用 $\|\cdot\|_2$（L2 范数，即欧氏长度）衡量向量大小，不是偶然。后续归一化操作全程围绕"数值尺度"展开，而 L2 范数是最直观的尺度指标：它越大，向量里越可能出现大数字；大数字在低精度浮点（BF16）计算中会吞掉小数字，直接导致数值误差。

不过别把"捷径保长度"偷换成"残差连接会自动稳定数值"。真正送到下一层的是 $x + F(x)$。三角不等式给出上下界：

$$\bigl|\|x\|_2 - \|F(x)\|_2\bigr| \leq \|x + F(x)\|_2 \leq \|x\|_2 + \|F(x)\|_2$$

相加后长度最大是两份长度之和（同向），最小是两份长度之差（反向）。捷径保住了原件，**$F(x)$ 的方向和大小决定了整体尺度往哪走**。

这就像你每次都把原始文档存一份，确实不会丢稿；但你还在不断把修改意见并进主文档，几十轮之后，文档的长度和重点仍可能失控。残差解决“原件会不会丢”，归一化解决“下一位编辑拿到的稿子会不会大到没法处理”。

## 归一化管尺度，不擦信息

残差管不了尺度，需要另一个机制专门管——这就是归一化。它常被误解成"把不同 token 强行拉成同一表示"。实际正好相反：归一化只约束数值范围，不碰语义差异。

### LayerNorm 到底在算什么

每个 token 的隐藏向量 x 是一个 d 维实数向量（d 通常是 7168 或 10240）。LayerNorm 在这 d 个特征维度上、对**这一个 token** 独立地计算均值和方差：

$$\mu = \frac{1}{d}\sum_i x_i,\quad \sigma^2 = \frac{1}{d}\sum_i (x_i - \mu)^2$$

也就是说，它看的是"这个 token 的 7168 个数字整体偏到哪儿、散得多开"。然后做两步变换：先减去均值、除以标准差，把分布拉到零附近、单位方差；再用两个可学参数 $\gamma$（缩放）和 $\beta$（平移）让模型自己决定最终留在哪儿：

$$\text{LN}(x) = \gamma \odot \frac{x - \mu}{\sqrt{\sigma^2 + \varepsilon}} + \beta$$

$\varepsilon$ 是一个极小的常数（通常 $10^{-5}$），防止方差为零时除以零。

### 为什么必须每个 token 自己算

不同 token 的隐藏向量数值尺度差异可以非常夸张。一句话里，"银行"的某些维度可能普遍在 ±50 的范围，而"贷款"可能只有 ±2。如果跨 token 共享统计量，大值 token 会把均值和方差都拉偏，小值 token 的细节差异就会被淹没——模型等于在拿着一堆不同亮度的照片硬拼。

每个 token 独立计算 μ 和 σ，等于给每张照片单独调曝光：**"银行"不会因为"贷款"数值小就被洗掉自己的特征，"贷款"也不会被"银行"的数值压得看不见**。归一化之后，它们都站在同一个起跑线上，但各自的语义差异完整保留。

![](02-layernorm-rmsnorm.png)

### RMSNorm：省掉一步也够用

LayerNorm 两步操作里，减均值这一步在很多场景并非刚需——子层真正怕的不是"输入偏正偏负"，而是"数值范围过大导致梯度爆炸"。尺度控制的核心在缩放。

于是大模型逐渐改用 RMSNorm。它直接跳过减均值，只按均方根缩放：

$$\text{RMSNorm}(x) = \gamma \odot \frac{x}{\sqrt{\frac{1}{d}\sum_i x_i^2 + \varepsilon}}$$

少了一步"把均值移回零"，计算更轻；但对子层而言，最关键的尺度控制还在。原始论文提出的正是这个取舍：保留重新缩放，省掉在许多场景中并不必要的重新居中。

所以别把"归一化"理解成"信息变少"。更准确的说法是：**让子层少关心输入到底有多大，把精力放在输入里有什么结构。**

## 不只是训练技巧：数值计算的刚性需求

归一化不只让训练更平滑——在低精度几乎成为标配的今天，它直接决定了计算会不会崩。

现代大模型的隐藏层动辄激活数十亿参数,训练和推理普遍用 BF16(8 位尾数)甚至 FP8(7 位尾数)。以 BF16 为例,它能表示的最小精度在 1e-8 量级;当某个 token 的激活值整体落在 1e-7 附近时,相邻两个可表示的 BF16 数之间的间隔已经和数值本身量级相当。如果不在输入子层之前做一次归一化、把数值拉到 $O(1)$ 量级，RMSNorm 分母里的 $\sqrt{\text{mean}(x^2) + \varepsilon}$ 就会因为浮点舍入产生巨大偏差--NVIDIA 和 HuggingFace 的开发者社区都记录过,同样一份代码在 BF16 下跑出的 logits 有超过 80% 的元素误差超过 0.01,根源就在归一化附近的一次低精度乘加。

DeepSeek-V4-Pro 的 `rms_norm_eps: 1e−6` 这个值在 FP32 下几乎可以忽略，但在 BF16 下它是刚性安全网：确保分母永远不会因为舍入而接近零。归一化在这里不只是"让训练更稳"，而是保证每一步乘法和除法在有限精度下仍然有效。

## 放在前面，残差的直通路才真的好走

### 两种写法的结构差异

原始 Transformer 常见的 Post-Norm 写法是：

$$x_{l+1} = \text{Norm}(x_l + F_l(x_l))$$

先做子层变换、和残差相加，再归一化。它当然能把这一轮的输出拉回尺度，但归一化也站在残差主路的后面：每一层的主路都得经过一次 Norm。

Pre-Norm 把位置换过来：

$$x_{l+1} = x_l + F_l(\text{Norm}(x_l))$$

现在 Norm 只服务于分支 $F_l$：Attention 或 FFN 先吃到稳定尺度的输入，再把自己学到的"增量"加回原来的 $x_l$。残差主路仍是直接相加的链条。注意，Pre-Norm 不是让 $x_l$ 的模长永远不变；它保证的是每一层准备加工时，**$F_l$ 的输入尺度可控**。

### 为什么 Pre-Norm 更容易把深模型训起来

关键在梯度的反向传播路径。

Post-Norm 中，梯度要回传必须**逐层穿过 Norm**。Norm 的雅可比矩阵（反向传播求导时，输入每维对输出每维的影响系数）与输入尺度相关——当某一层输出的范数偏大或偏小时，梯度缩放因子也跟着变化。多层连乘下来，靠近输入端的梯度可能指数级放大或衰减，初始化时尤其不稳定，因此更依赖学习率 warm-up 来"躲开"早期的梯度爆炸区。

Pre-Norm 中，残差主路 $x_{l+1} = x_l + \dots$ 为梯度提供了一条**不经过 Norm 的直达通路**。反向传播时,这条支路的梯度接近恒等映射,数值几乎不衰减;而穿过 Norm 的分支通路的梯度虽然仍有缩放,但只影响"增量"部分。两层叠加后,整体梯度在初始化阶段就能保持相对平稳,深 Transformer 更容易训起来。

"更容易训练"不等于 Post-Norm 一定错误。它是结构与训练配方的取舍；但当模型很深、训练预算又昂贵时，先把分支输入稳住，通常是更省心的默认选择。

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

## DeepSeek-V4-Pro：同样的原则，更大的胆

前面讲的 61 层模型不是假设——它来自 DeepSeek-V4-Pro 的开源推理代码。

这份代码的 `Block` 实现在 Attention 和 FFN 前分别调用了 `attn_norm` 和 `ffn_norm`——每个子层输入都先经过 RMSNorm 稳住尺度。其 `config.json` 写有 `num_hidden_layers: 61`、`hidden_size: 7168` 与 `rms_norm_eps: 1e−6`，和伪代码描述的"先稳住、再做增量"完全一致。

值得一提的是，DeepSeek-V4-Pro 的残差连接没有停在最朴素的 $x + F(x)$。同一份配置里的 `hc_mult: 4` 和代码中的 Hyper-Connections（超连接：维护并混合 4 份隐藏状态，替代单一捷径），把残差的"直通车"升级成了可学习的"多车道"。归一化依然守在每条车道的入口——Attn 和 FFN 前面那两次 RMSNorm——稳住了子层输入尺度。残差本身怎么连线、怎么进化，是另一条独立的工程方向。

这正好提醒我们：文章里的伪代码是读懂 Transformer 分工的骨架，不是把所有新架构压扁成同一种实现。**归一化和残差是两种职责；具体怎么连线，模型还会继续进化。**

![](05-deepseek-v4-norm-hc.png)

## 回到开头：模型不崩，靠的不是其中一个“神招”

61 层网络能工作，不是因为残差把一切数值问题都解决了，也不是因为归一化替模型保存了信息。恒等捷径让原始状态有不被变换的通路；RMSNorm 让 Attention 和 FFN 不必反复适应忽大忽小的输入；Pre-Norm 则把两件事排成了对的顺序。

所以,归一化放在前面,不是装饰性的惯例。它是在告诉每个子层："你可以大胆学增量，但先在稳定的尺度上工作。"

## 一句话总结

残差连接保住 $x$ 的直通路，却不保证 $x + F(x)$ 的整体范数不变；Pre-Norm 用 LayerNorm 或 RMSNorm 先稳定子层输入，再把增量加回去，才让深 Transformer 同时拥有可控尺度和可走通的梯度路径。

你会更愿意把一条残差主路保持为完全不动的"原件通道"，还是让它也学会混合多份状态？哪一种更让你安心？评论区聊聊。

前一篇 [残差连接](https://mp.weixin.qq.com/s/xefNN9Gjaw3TKl60KeHzAg) 讲了深度神经网络为什么需要捷径来保住原始信号；这篇讲的是光有捷径还不够，还需要归一化来稳住每一层的加工尺度。下一篇进入 FFN：信号经过 Attention 之后，前馈网络负责提炼和扩展表示，到那里你会看到归一化的分工怎样贯穿整个 Block。

关注「数解AI」，把 Transformer 拆成一条能自己推演的链。

📖 **[大模型原理合集](https://mp.weixin.qq.com/mp/appmsgalbum?__biz=MzkyMzQyODExNQ==&action=getalbum&album_id=4597831652025925632#wechat_redirect)**：① [BPE分词：AI为什么把文字切成碎片？](https://mp.weixin.qq.com/s/5nR_KI47v_U8KwpQA4Uv5Q) → ② [词嵌入为什么让AI懂"苹果"？5万个0变坐标](https://mp.weixin.qq.com/s/rDryn1z_hLt7mwi3X8fsxQ) → ③ [位置编码怎么工作？词序一错意思全变](https://mp.weixin.qq.com/s/4nO2VqQLaYxGdDmtQeypCQ) → ④ [注意力机制是什么？别再当数据库查询](预告) → ⑤ [Attention都够了，为什么还要FFN？](预告) → ⑥ 归一化为什么总在前面？61层模型靠它不崩（本篇） → ⑦ [注意力找人，FFN存知识：跟一句话走完Transformer](预告)

📖 **[训练回路合集](https://mp.weixin.qq.com/mp/appmsgalbum?__biz=MzkyMzQyODExNQ==&action=getalbum&album_id=4594958081087864833#wechat_redirect)**：① [梯度下降：蒙着眼下山](https://mp.weixin.qq.com/s/V6mGvCVFpTvmC51pNtxiTw) → ② [损失函数：打分标准决定学习方向](https://mp.weixin.qq.com/s/zIWqYqYVzEaF1e8P6fcTfw) → ③ [反向传播是什么？AI怎么知道自己错在哪](https://mp.weixin.qq.com/s/oYj_qpwF4tZG84ImOn977g) → ④ [Softmax为什么不直接取最大值？](https://mp.weixin.qq.com/s/5wMquh_v3oon2-NEDeQLEw) → ⑤ [残差连接：为什么56层比20层还差](https://mp.weixin.qq.com/s/xefNN9Gjaw3TKl60KeHzAg) → ⑥ [学习率怎么自动调？Adam 优化器拆给你看](https://mp.weixin.qq.com/s/aSLVO-otvr2rxIU1kr2eAA)

---

**参考资料**

- [Root Mean Square Layer Normalization](https://arxiv.org/abs/1910.07467)（RMSNorm 原论文，Zhang & Sennrich, 2019）
- [On Layer Normalization in the Transformer Architecture](https://arxiv.org/abs/2002.04745)（Pre-Norm 分析论文，Xiong et al., 2020）
- [DeepSeek-V4-Pro config.json](https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/blob/b5968e9190ef611bbf34a7229255be88a0e937c1/config.json)
- [DeepSeek-V4-Pro Block 实现](https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/blob/b5968e9190ef611bbf34a7229255be88a0e937c1/inference/model.py)

#归一化 #RMSNorm #Pre-Norm #残差连接 #大模型原理 #数解AI
