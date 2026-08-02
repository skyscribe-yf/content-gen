---
title: "DeepSeek-V4为何不用MLA？"
author: "数解AI"
date: "2026-08-04"
digest: "MLA 把 KV cache 压小了，却没有让注意力少看一些位置。到了百万 token 上下文，真正的墙从存不下变成找不动。DeepSeek-V4 用 CSA 先压缩再稀疏选择，用 HCA 保留低成本的全局视野。"
type: "原理篇"
series: "DeepSeek 技术解密"
keywords: ["DeepSeek-V4", "CSA", "HCA", "DSA", "Lightning Indexer", "稀疏注意力", "长上下文"]
cover: 00-cover.png
---

上一篇我们讲了 [MLA 如何压缩 KV cache](https://mp.weixin.qq.com/s/HHMNEdCYThOjCLRozQorhg)。

它解决的是一个很现实的问题：上下文越长，模型留下的“阅读笔记”越厚，显存越容易先撑不住。

但 MLA 只解决了一半。

它把每个位置的 KV 表示写得更薄，却没有减少位置的数量。模型仍然要面对整段历史。

2026 年发布的 DeepSeek-V4，目标是让 **1M token 上下文**真正可以运行。它没有继续沿用 MLA，而是换成了 CSA + HCA 混合注意力。

![从 MLA 到 CSA 与 HCA：注意力开始改变工作方式](01-flowchart-attention-evolution.png)

问题来了：MLA 已经很省了，为什么还要换？

答案不是 MLA 做错了，而是上下文变长之后，瓶颈换了。

## MLA 解决了“存多少”，没解决“看多少”

先回到注意力的基本公式：

$$
\operatorname{Attn}(q_t,K,V)=\operatorname{Softmax}\left(\frac{q_tK^\top}{\sqrt{d_h}}\right)V
$$

这里的 $q_t$ 是当前 token 的 query，$K$ 和 $V$ 是历史 token 留下的 key、value。

如果历史长度是 $L$，一个 query 至少要面对前面的大量 key。

在 prefill 阶段，所有 query 一起计算，注意力矩阵的规模近似是 $L^2$。

在 decode 阶段，虽然每次只生成一个 query，但它仍要扫描越来越长的历史。

MLA 的做法，是把每个位置的 KV 表示压进低维 latent：

$$
c_t^{KV}=h_tW^{DKV}
$$

于是，每个位置需要保存的向量变短了。

但位置数量仍然是 $L$。

可以把它想成一面贴满便利贴的墙。

MLA 把每张便利贴写得更小，却没有撕掉便利贴。

当上下文从 128K 走到 1M，模型仍然要从这面更大的墙上寻找信息。

所以，MLA 解决的是“每张卡片存多少”，不是“总共有多少张卡片”。

## DSA：第一次让注意力只看重点

DeepSeek-V3.2 给出了一个过渡答案。

它在 MLA 之上叠加 DSA，也就是 DeepSeek Sparse Attention。

这一点必须先说清楚：

**V3.2 是 MLA + DSA，DSA 不是 MLA 的替代品。**

MLA 负责压缩存储。

DSA 负责减少核心注意力真正读取的位置。

### Lightning Indexer 做什么？

DSA 先用一个轻量的 Lightning Indexer 给候选位置打分。

它的简化形式可以写成：

$$
I_{t,s}=\sum_{h=1}^{n_h^I}w_{t,h}^I\,\operatorname{ReLU}\left((q_{t,h}^I)^\top K_s^I\right)
$$

$I_{t,s}$ 表示第 $t$ 个 query 对第 $s$ 个候选位置的兴趣分数。

$q^I$ 和 $K^I$ 是专门给索引器使用的 query、key。

它们不必承担完整注意力的全部表达能力。

索引器只需要回答一个问题：

**哪些位置值得进入下一轮精读？**

因此，下一步是：

$$
\mathcal{S}_t=\operatorname{TopK}(I_{t,:})
$$

核心注意力只读取 $\mathcal{S}_t$ 对应的少量位置。

这里使用 ReLU 也有一个直觉。

索引器需要的是排序，不是概率。

它不必把所有分数归一化成总和为 1 的 softmax 分布。

负的相似度直接变成 0，再从非负分数里选 top-k 即可。

### DSA 还留下了一面墙

DSA 确实减少了核心注意力的工作量。

如果每个 query 只精读 $k$ 个位置，核心路径从约 $O(L^2)$ 降到约 $O(Lk)$。

但索引器要先知道谁重要。

如果候选池仍然包含整段原始历史，它就仍然要为大量位置打分。

所以，在整段序列上看，DSA 的索引阶段仍然接近 $O(L^2)$。

这像是把“逐页精读”改成了“先看目录再精读”。

但目录本身还是一页一页扫描出来的。

![DSA 与 CSA 的差别：索引器面对原始 token 池还是压缩 KV 池](02-comparison-dsa-csa-indexer.png)

V4 的关键动作，就是先把目录也压短。

## CSA：先把整本书压成目录，再选重点章节

CSA 的全名是 Compressed Sparse Attention。

它把两个动作明确排成先后顺序：

1. 沿序列维度压缩 KV。
2. 在压缩后的 KV 池里做 DSA 的稀疏选择。

### 双流重叠压缩

设输入 hidden states 为 $H$。

CSA 先生成两条 KV 流：

$$
C^a=HW_{KV}^a,\qquad C^b=HW_{KV}^b
$$

同时生成两条压缩权重：

$$
Z^a=HW_Z^a,\qquad Z^b=HW_Z^b
$$

每个压缩块都会用带位置偏置的 softmax 产生权重。

然后把当前块的 $a$ 流和前一块的 $b$ 流合并：

$$
C_i^{\mathrm{Comp}}
=\sum_{j=mi}^{m(i+1)-1}S_j^a\odot C_j^a
+\sum_{j=m(i-1)}^{mi-1}S_j^b\odot C_j^b
$$

$\odot$ 是逐元素相乘。

这个公式最值得看的地方，不是符号，而是“重叠”。

第 $i$ 个摘要看到当前 $m$ 个 entry。

它还看到前一条流里的前 $m$ 个 entry。

所以感受野大约覆盖 $2m$ 个 entry。

但相邻摘要之间共享一部分范围。

最终的有效序列压缩比仍然是 $m$，不是 $2m$。

这样做是为了减少块边界带来的信息断裂。

如果每块各自独立摘要，刚好跨过边界的依赖可能会被切断。

双流重叠让相邻摘要之间留出一段共同视野。

### 在压缩池里做 Lightning Indexer

这一步是 CSA 和 DSA 的真正分界线。

DSA 直接面对长序列。

CSA 先得到压缩后的 $C^{\mathrm{Comp}}$，再为索引器构造压缩 key：

$$
K^{I\mathrm{Comp}}=\operatorname{Compress}(K^I)
$$

当前 query 的索引表示也通过低秩路径生成：

$$
c_t^Q=h_tW^{DQ},\qquad q_t^I=c_t^QW^{IUQ}
$$

于是，索引分数变成：

$$
I_{t,s}=\sum_h w_{t,h}^I\,\operatorname{ReLU}\left((q_{t,h}^I)^\top K_s^{I\mathrm{Comp}}\right)
$$

最后仍然是 top-k：

$$
C_t^{\mathrm{SprsComp}}
=\left\{C_s^{\mathrm{Comp}}\mid I_{t,s}\in\operatorname{TopK}(I_{t,:})\right\}
$$

区别在于，$s$ 现在遍历的是压缩块。

候选数量从约 $L$ 变成约 $L/m$。

索引器这道墙，也跟着变矮了。

### 选中的 entry 如何参与注意力？

CSA 对选中的压缩 entry 做 core attention。

V4 使用 shared KV 的 MQA 方式：

$$
o_{t,i}=\operatorname{CoreAttn}\left(q_{t,i},C_t^{\mathrm{SprsComp}},C_t^{\mathrm{SprsComp}}\right)
$$

同一个压缩 entry 同时充当 key 和 value。

这是一个非常激进的决定。

它进一步减少了 KV 表示的分工与存储开销。

但它也把位置编码问题推到了台前。

为什么 key 和 value 可以共用一个 entry？

同一个向量带着位置旋转后，怎样避免把绝对位置混进 value 汇总？

这部分留到下一篇单独推导。

CSA 还会保留一条未压缩的滑动窗口。

压缩路径负责远处的信息。

滑动窗口负责最近 token 的精确关系。

这样，块边界和局部语法不会全都交给摘要承担。

这里的公式是结构示意。

严格的因果实现不会让块内 query 读取尚未完成的当前摘要。

它只把已经完成的前序压缩块交给 core attention。

当前块的信息由未压缩的滑动窗口补齐。

![CSA 的双流重叠压缩与局部窗口](03-framework-csa-dual-stream.png)

## HCA：不挑章节，直接看极短摘要

HCA 的全名是 Heavily Compressed Attention。

它和 CSA 的分工不同。

CSA 压缩后还要选择 top-k。

HCA 压得更狠，但不做稀疏选择。

设压缩因子为 $m'$，且 $m'\gg m$：

$$
C=HW_{KV},\qquad Z=HW_Z
$$

每 $m'$ 个 entry 直接汇成一个摘要：

$$
C_i^{\mathrm{Comp}}
=\sum_{j=m'i}^{m'(i+1)-1}S_j\odot C_j
$$

压缩后的序列已经足够短。

所以 HCA 可以直接做 dense attention：

$$
o_{t,i}=\operatorname{CoreAttn}\left(q_{t,i},C^{\mathrm{Comp}},C^{\mathrm{Comp}}\right)
$$

这里没有 top-k。

因为它要看的不是少数重点，而是一份便宜的全局概览。

可以这样记：

- CSA：翻目录，挑出最相关的几章精读。
- HCA：看一本极短的全书摘要，避免完全失去全局。

两种机制交替堆叠。

一个负责精准，一个负责覆盖。

这就是 V4 的 hybrid attention。

![CSA 与 HCA 的分工：一个精读重点，一个浏览全局](04-comparison-csa-hca.png)

## 为什么不是继续修补 MLA？

把几种机制放在一起，差异就清楚了：

| 机制 | 主要解决什么 | 还留下什么代价 |
|---|---|---|
| MLA | 每个位置的 KV 表示太大 | 位置数量没有减少 |
| MLA + DSA | 核心注意力只读 top-k | 索引器仍面对长序列 |
| CSA | 压缩序列后再稀疏选择 | 需要压缩、索引和窗口协同 |
| HCA | 用极短摘要保留全局 | 单个摘要更粗，需要 CSA 互补 |

所以，V4 的改变不是一句“MLA 不行了”。

更准确的说法是：

**MLA 适合解决“每个位置存得太贵”，而 1M context 还要求“位置本身也要变少”。**

从设计结果看，V4 把注意力拆成了两个角色。

CSA 负责“去哪里找重点”。

HCA 负责“用很低成本维持全局视野”。

这也是为什么 V4 不是简单地把 DSA 的 top-k 调大。

它先改变了候选池的长度，再决定看哪些候选。

## 论文数字：1M context 到底省了多少？

DeepSeek-V4 Technical Report 在 Introduction 和注意力章节给出了对比。

这里采用同一口径。

在 1M token 上下文里，DeepSeek-V4-Pro 相对 DeepSeek-V3.2：

- 单 token 推理 FLOPs 约为 **27%**。
- KV cache 约为 **10%**。

DeepSeek-V4-Flash 的数字更激进：

- 单 token 推理 FLOPs 约为 **10%**。
- KV cache 约为 **7%**。

这不是说所有任务都会固定快 3.7 倍。

它是技术报告在 1M 场景下的估算比较。

比较口径很重要。

官方模型卡还给出了两个模型的基本规格：

| 模型 | 总参数 | 激活参数 | 上下文长度 |
|---|---:|---:|---:|
| DeepSeek-V4-Pro（2026） | 1.6T | 49B | 1M |
| DeepSeek-V4-Flash（2026） | 284B | 13B | 1M |

公开 `config.json` 也能看到 V4-Pro 的 `num_attention_heads: 128`、`num_key_value_heads: 1` 和 `max_position_embeddings: 1048576`。

这组配置和论文里的 shared KV MQA 是相互呼应的。

## 一个 mini 机制实验

真实的 V4-Pro 太大，不能拿当前 CPU 环境直接跑完整模型。

所以我先做一个透明的机制计数实验。

它不测模型质量，也不把 CPU 时间写成 GPU 性能。

实验只统计因果 mask 下的 query-key pair 数量。

参数取一个小型演示值：

$$
m=8,\qquad m'=32,\qquad k=8,\qquad n_{\mathrm{win}}=16
$$

结果如下。DSA 的两列分别是 indexer 和 core attention。

CSA 的第二列包含 core attention 与 local window。

HCA 的第二列包含 global compressed attention 与 local window。

| 序列长度 $L$ | Dense | DSA indexer / core | CSA indexer / core+window | HCA global+window | Dense / CSA / HCA 条目 |
|---:|---:|---:|---:|---:|---:|
| 512 | 131,328 | 131,328 / 4,068 | 16,128 / 11,880 | 3,840 / 11,912 | 512 / 64 / 16 |
| 1,024 | 524,800 | 524,800 / 8,164 | 65,024 / 24,168 | 15,872 / 32,136 | 1,024 / 128 / 32 |
| 2,048 | 2,098,176 | 2,098,176 / 16,356 | 261,120 / 48,744 | 64,512 / 97,160 | 2,048 / 256 / 64 |
| 4,096 | 8,390,656 | 8,390,656 / 32,740 | 1,046,528 / 97,896 | 260,096 / 325,512 | 4,096 / 512 / 128 |

![mini 机制实验中的压缩条目数](05-infographic-experiment-counts.png)

这个表有两个值得注意的地方。

第一，DSA 的 core 确实很小。

但 indexer 仍然接近 dense 的候选扫描量。

第二，CSA 先把候选池压到 $1/m$ 左右。

HCA 则把全局摘要进一步压到 $1/m'$ 左右。

这些数字是 pair count，不是 FLOPs。

真实 indexer 还使用更小的维度和低精度路径。

因此，不能直接把表中的比值当成端到端速度。

为了验证社区实现本身的基本路径，我还运行了 `pablo-reyes8/deepseek-v4-mini-pytorch` 的 CSA/HCA 测试。

当前 CPU 环境的结果是：**149 passed in 2.54s**。

这只能说明缩小实现的形状、因果性和梯度检查通过。

它不是官方 V4 的性能证明。

## 资料来源

- [DeepSeek-V4: Towards Highly Efficient Million-Token Context Intelligence](https://arxiv.org/abs/2606.19348)：CSA、HCA 和 1M context 效率数据，重点参见 Introduction 与注意力章节。
- [DeepSeek-V4-Pro 官方模型卡](https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro) 与 [`config.json`](https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/blob/main/config.json)：核验 2026 年 V4-Pro 的模型规格和注意力配置。
- [DeepSeek-V4-Flash 官方模型卡](https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash)：核验 V4-Flash 的模型规格和 1M context 信息。
- [DeepSeek-V3.2 Technical Report](https://arxiv.org/abs/2512.02556)：DSA 与 Lightning Indexer 的历史承接。
- [deepseek-v4-mini-pytorch](https://github.com/pablo-reyes8/deepseek-v4-mini-pytorch)：社区缩小实现；本文只引用其 CSA/HCA 测试结果，不把它当作官方性能基准。

## 结尾：注意力的下一步，是少找一点

MLA 把每张便利贴写薄了。

DSA 开始只挑重点。

CSA 先把便利贴压成目录，再从目录里选重点。

HCA 则保留一份极短的全局摘要。

这条路线不是“谁替代谁”这么简单。

每一步都在处理上一阶段留下的瓶颈：

**MLA 压缩存储，DSA 减少精读，CSA 缩短候选池，HCA 保留全局。**

下一篇继续拆 V4 注意力内部最激进的部分：

为什么一个压缩 entry 可以同时当 key 和 value？

Partial RoPE 为什么只旋转最后 64 维？

输出为什么还要做 de-RoPE？

再下一篇，我们再看 mHC 如何让这套激进结构在深层网络里保持稳定。

📖 **[大模型原理合集](https://mp.weixin.qq.com/mp/appmsgalbum?__biz=MzkyMzQyODExNQ==&action=getalbum&album_id=4597831652025925632#wechat_redirect)**：BPE → 词嵌入 → 位置编码 → 注意力 → KDA 长上下文 → **MLA 压缩 KV cache** → FFN → 归一化残差 → Transformer 全景 → 预训练 → RLHF → 推理加速

🔥 **DeepSeek 技术解密**：上下文硬墙 → MoE 混合专家 → MLA → **V4 注意力（本篇）**

觉得这篇帮你看懂了 V4 的注意力路线，欢迎**点赞、收藏**，关注「数解AI」，下一篇继续拆 `K = V`、Partial RoPE 和 de-RoPE。

你更愿意让模型保存完整原文，还是先压缩成摘要再去找重点？

#DeepSeek技术解密 #CSA #HCA #稀疏注意力 #数解AI
