---
title: "DeepSeek-V4为何不用MLA？"
author: "数解AI"
date: "2026-08-04"
digest: "MLA 把 KV cache 压小了，却没有让注意力少看一些位置。到了百万 token 上下文，瓶颈从存不下变成找不动。DeepSeek-V4 用 CSA 先压缩再稀疏选择，用 HCA 保留低成本的全局视野。"
type: "原理篇"
series: "DeepSeek 技术解密"
keywords: ["DeepSeek-V4", "CSA", "HCA", "DSA", "Lightning Indexer", "稀疏注意力", "长上下文"]
cover: 00-cover.png
wechatUrl: "https://mp.weixin.qq.com/s/MQEgbY16mLs-N7g2xKW1HQ"
---

上一篇我们讲了 [MLA 如何压缩 KV cache](https://mp.weixin.qq.com/s/HHMNEdCYThOjCLRozQorhg)。它把每个 token 留下的 KV cache 压缩成更短的表示，让长对话不至于先被显存卡住。

但这只解决了“每个位置存多少”的问题，没解决“需要看多少个位置”。

2026 年发布的 DeepSeek-V4，目标是让 **1M token 上下文**真正可以运行。它没有继续沿用 MLA，而是换成了 CSA + HCA 混合注意力。

问题来了：MLA 已经很省了，为什么还要换？

答案不是 MLA 做错了，而是上下文变长之后，瓶颈换了。我们在[长上下文那篇文章](https://mp.weixin.qq.com/s/PLVRS0TTHXHDve1Z3r6M7Q)里讨论过：长上下文同时会推高计算量和存储量。这篇继续追问其中“找信息”的一半。

![从 MLA 到 CSA 与 HCA：注意力开始改变工作方式](01-flowchart-attention-evolution.png)

## MLA 解决了“存多少”，没解决“看多少”

先回到注意力的基本动作。在[注意力机制那篇文章](https://mp.weixin.qq.com/s/KrilwX6VRjI9KfjvD7C6kw)里我们拆过 Q、K、V。

模型先用当前 token 的 query 和历史 token 的 key 比较相关性，再按照相关性给 value 加权。把这两步写在一起，就是：

$$
\operatorname{Attn}(q_t,K,V)=\operatorname{Softmax}\left(\frac{q_tK^\top}{\sqrt{d_h}}\right)V
$$

这里的 $q_t$ 是当前 token 的 query，$K$ 和 $V$ 是历史 token 留下的 key、value。点积先产生一组分数，[Softmax 那篇文章](https://mp.weixin.qq.com/s/5wMquh_v3oon2-NEDeQLEw)再把分数变成权重；最后用这些权重汇总 $V$。

$\sqrt{d_h}$ 是按 key 的维度做缩放，避免维度变大后点积数值过大。

为了看清成本，还要区分两个阶段。把整段输入一次送进模型，叫 **prefill**；模型逐 token 生成回答，叫 **decode**。

如果历史长度是 $L$，prefill 阶段要处理的 query-key 配对规模近似为 $L^2$。decode 虽然每次只新增一个 query，却仍要扫描越来越长的历史。这里的 $O(\cdot)$ 只表示增长趋势，不代表精确的 FLOPs。

MLA 的做法，是把每个位置的 KV 表示压进低维 latent：

$$
c_t^{KV}=h_tW^{DKV}
$$

其中 $h_t$ 是第 $t$ 个位置的隐藏状态，$W^{DKV}$ 是训练得到的下投影矩阵，$c_t^{KV}$ 是要存进缓存的短向量。于是，每个位置需要保存的向量变短了，但位置数量仍然是 $L$。

可以把历史信息想成一本会不断加页的会议记录：MLA 把每一页写得更精简，却没有减少页数。

当上下文从 128K 走到 1M，模型仍然要在更长的历史记录中寻找相关信息。所以，MLA 解决的是“每张卡片存多少”，不是“总共有多少张卡片”。

## DSA：第一次让注意力只看重点

DeepSeek-V3.2 给出了一个过渡答案。在 MLA 之上叠加 DSA，也就是 DeepSeek Sparse Attention。

需要先把分工说清楚：**V3.2 是 MLA + DSA，DSA 不是 MLA 的替代品。** MLA 负责压缩存储，DSA 负责减少核心注意力真正读取的位置。

### Lightning Indexer 做什么？

DSA 先用一个轻量的 Lightning Indexer 给候选位置打分。它不是第二个完整注意力模块，而是一个便宜的筛选器，只回答“哪些位置值得进入下一轮精读”：

$$
I_{t,s}=\sum_{h=1}^{n_h^I}w_{t,h}^I\,\operatorname{ReLU}\left((q_{t,h}^I)^\top K_s^I\right)
$$

$I_{t,s}$ 表示第 $t$ 个 query 对第 $s$ 个候选位置的兴趣分数。$q^I$ 和 $K^I$ 是索引器专用的 query、key，$w^I$ 是不同索引头的权重。

ReLU 可以先理解为“负数截断为 0”，这样索引器只保留非负的兴趣分数，不必承担完整注意力的表达能力。

拿到分数后，索引器只保留最高的 $k$ 个位置：

$$
\mathcal{S}_t=\operatorname{TopK}(I_{t,:})
$$

TopK 的意思就是从一排分数中挑出最大的 $k$ 个。核心注意力随后只读取 $\mathcal{S}_t$ 对应的位置。

这里不需要把全部分数归一化成总和为 1 的概率分布，因为索引器关心的是排序，不是概率。

### DSA 还留下了扫描成本

DSA 确实减少了核心注意力的工作量。如果每个 query 只精读 $k$ 个位置，核心路径就能从约 $O(L^2)$ 降到约 $O(Lk)$。当 $k$ 远小于 $L$ 时，这个差别很大。

但索引器要先知道谁重要。如果候选池仍然包含整段原始历史，它就仍然要为大量位置打分。

因此，DSA 的核心注意力变轻了，索引阶段却仍然接近 $O(L^2)$。这像是把“逐页精读”改成“先看目录再精读”，只是目录仍然要从整本书逐页扫描出来。

V4 的关键动作，就是先把候选池压短，再进行筛选。

![DSA 与 CSA 的差别：索引器面对原始 token 池还是压缩 KV 池](02-comparison-dsa-csa-indexer.png)

## CSA：先把整本书压成目录，再选重点章节

CSA 的全名是 Compressed Sparse Attention。它把两个动作明确排成先后顺序：先沿序列维度压缩 KV，再在压缩后的 KV 池里做 DSA 的稀疏选择。

这样，索引器面对的就不再是全部原始 token，而是一组更短的压缩条目。

### 双流重叠压缩

设输入 hidden states 为 $H$，每一行对应一个 token；$m$ 表示一个压缩块大致覆盖的 token 数。

CSA 先用两组学习到的投影生成两条 KV 流和两条权重流：

$$
C^a=HW_{KV}^a,\qquad C^b=HW_{KV}^b
$$

$$
Z^a=HW_Z^a,\qquad Z^b=HW_Z^b
$$

$Z^a$ 和 $Z^b$ 会经过带位置偏置的 Softmax，变成归一化权重 $S^a$ 和 $S^b$。

第 $i$ 个压缩条目把当前块的 $a$ 流和前一块的 $b$ 流合并：

$$
C_i^{\mathrm{Comp}}
=\sum_{j=mi}^{m(i+1)-1}S_j^a\odot C_j^a
+\sum_{j=m(i-1)}^{mi-1}S_j^b\odot C_j^b
$$

这里 $\odot$ 表示逐元素相乘，$i$ 是压缩条目的编号，$j$ 是原始 token 的编号。

这个公式最值得看的地方不是符号，而是“重叠”。第 $i$ 个摘要看到当前 $m$ 个 entry，也看到前一条流里的前 $m$ 个 entry。

相邻摘要之间因此共享一部分范围，有效序列压缩比仍然是 $m$，不是 $2m$。

这样做是为了减少块边界带来的信息断裂。如果每个块各自独立摘要，刚好跨过边界的依赖可能会被切开；双流重叠则为相邻摘要留下共同视野。

### 在压缩池里做 Lightning Indexer

这一步是 CSA 和 DSA 的真正分界线。DSA 直接面对长序列，CSA 则先得到压缩后的 $C^{\mathrm{Comp}}$，再为索引器构造压缩 key：

$$
K^{I\mathrm{Comp}}=\operatorname{Compress}(K^I)
$$

当前 query 的索引表示也走一条低秩路径：

$$
c_t^Q=h_tW^{DQ},\qquad q_t^I=c_t^QW^{IUQ}
$$

有了压缩 key 和索引 query，兴趣分数仍然用 Lightning Indexer 计算：

$$
I_{t,s}=\sum_h w_{t,h}^I\,\operatorname{ReLU}\left((q_{t,h}^I)^\top K_s^{I\mathrm{Comp}}\right)
$$

最后仍然是 TopK：

$$
C_t^{\mathrm{SprsComp}}
=\left\{C_s^{\mathrm{Comp}}\mid I_{t,s}\in\operatorname{TopK}(I_{t,:})\right\}
$$

区别在于，$s$ 现在遍历的是压缩块，候选数量从约 $L$ 变成约 $L/m$。索引器不需要先为每一个原始 token 建立兴趣分数，扫描成本也随候选池一起缩小。

### 选中的 entry 如何参与注意力？

CSA 对选中的压缩 entry 做 core attention。V4 使用 shared KV 的 MQA 方式，也就是多个 query 头共享同一份 key/value 表示：

$$
o_{t,i}=\operatorname{CoreAttn}\left(q_{t,i},C_t^{\mathrm{SprsComp}},C_t^{\mathrm{SprsComp}}\right)
$$

同一个压缩 entry 同时充当 key 和 value，所以公式中两个位置写的是同一个 $C_t^{\mathrm{SprsComp}}$。

这是一个很激进的存储选择：它进一步减少了 KV 表示的分工，但也把[位置编码](https://mp.weixin.qq.com/s/4nO2VqQLaYxGdDmtQeypCQ)问题推到了台前。带着位置旋转后的向量，怎样避免把绝对位置混进 value 汇总？这部分留到下一篇单独推导。

CSA 还会保留一条未压缩的滑动窗口：压缩路径负责远处的信息，滑动窗口负责最近 token 的精确关系。这样，块边界和局部语法不会全都交给摘要承担。

下面的公式是结构示意。严格的因果实现不会让块内 query 读取尚未完成的当前摘要。它只会把已经完成的前序压缩块交给 core attention，当前块的信息由未压缩窗口补齐。

![CSA 的双流重叠压缩与局部窗口](03-framework-csa-dual-stream.png)

## HCA：不挑章节，直接看极短摘要

HCA 的全名是 Heavily Compressed Attention，它和 CSA 的分工不同。CSA 压缩后还要选择 TopK，HCA 则压得更狠，但不做稀疏选择。

设压缩因子为 $m'$，且 $m'\gg m$，这里的含义是 HCA 每个摘要覆盖的 token 更多：

$$
C=HW_{KV},\qquad Z=HW_Z
$$

这里的 $Z$ 同样经过带位置偏置的 Softmax，得到归一化权重 $S$。

每 $m'$ 个 entry 直接汇成一个摘要：

$$
C_i^{\mathrm{Comp}}
=\sum_{j=m'i}^{m'(i+1)-1}S_j\odot C_j
$$

压缩后的序列已经足够短，所以 HCA 可以直接做 dense attention：

$$
o_{t,i}=\operatorname{CoreAttn}\left(q_{t,i},C^{\mathrm{Comp}},C^{\mathrm{Comp}}\right)
$$

这里没有 TopK，因为它要看的不是少数重点，而是一份便宜的全局概览。

可以这样记：CSA 从较短的目录里挑出最相关的几章精读。HCA 则快速浏览一份极短的全书摘要，避免模型完全失去全局信息。

两种机制交替堆叠，一个负责精准，一个负责覆盖，这就是 V4 的 hybrid attention。

![CSA 与 HCA 的分工：一个精读重点，一个浏览全局](04-comparison-csa-hca.png)

## 为什么不是继续修补 MLA？

把几种机制放在一起，差异可以概括成下面这张表：

| 机制 | 主要解决什么 | 还留下什么代价 |
|---|---|---|
| MLA | 每个位置的 KV 表示太大 | 位置数量没有减少 |
| MLA + DSA | 核心注意力只读 TopK | 索引器仍面对长序列 |
| CSA | 压缩序列后再稀疏选择 | 需要压缩、索引和窗口协同 |
| HCA | 用极短摘要保留全局 | 单个摘要更粗，需要 CSA 互补 |

所以，V4 的改变不是一句“MLA 不行了”。更准确的说法是：**MLA 适合解决“每个位置存得太贵”，而 1M context 还要求“位置本身也要变少”。**

从设计结果看，V4 把注意力拆成了两个角色：CSA 负责“去哪里找重点”，HCA 负责“用很低成本维持全局视野”。

这也是为什么 V4 不是简单地把 DSA 的 TopK 调大，而是先改变候选池的长度，再决定看哪些候选。

## 论文数字：1M context 到底省了多少？

[DeepSeek-V4 技术报告](https://arxiv.org/abs/2606.19348)在 Introduction 和注意力章节给出了对比。这里采用同一口径。

在 1M token 上下文里，DeepSeek-V4-Pro（2026）相对 DeepSeek-V3.2 的资源占用更低：

- 单 token 推理 FLOPs 约为 **27%**。
- KV cache 约为 **10%**。

DeepSeek-V4-Flash（2026）的数字更激进：

- 单 token 推理 FLOPs 约为 **10%**。
- KV cache 约为 **7%**。

这不是说所有任务都会固定快 3.7 倍，而是技术报告在 1M 场景下的估算比较。比较时还要注意模型规模和上下文长度不能混为一谈。

官方模型卡给出了两个模型的基本规格：

| 模型 | 总参数 | 激活参数 | 上下文长度 |
|---|---:|---:|---:|
| DeepSeek-V4-Pro（2026） | 1.6T | 49B | 1M |
| DeepSeek-V4-Flash（2026） | 284B | 13B | 1M |

公开的 config.json 也能看到 V4-Pro 的三项配置。num_attention_heads 是 128，num_key_value_heads 是 1。max_position_embeddings 是 1048576。

三项配置分别对应 query 头数、共享 KV 头数和最大位置数。它们和论文里的 shared KV MQA 相互呼应，但不能单独推出端到端速度。

## 一个 mini 机制实验

真实的 V4-Pro 太大，不能拿当前 CPU 环境直接跑完整模型。因此我做了一个透明的机制计数实验。

它不测模型质量，也不把 CPU 时间写成 GPU 性能，只统计因果 mask 下的 query-key pair 数量。

先解释四个演示参数。其中 $m$ 是 CSA 的压缩因子，$m'$ 是 HCA 的压缩因子。$k$ 是 DSA/CSA 每个 query 保留的候选数，$n_{\mathrm{win}}$ 是未压缩滑动窗口的长度。实验取：

$$
m=8,\qquad m'=32,\qquad k=8,\qquad n_{\mathrm{win}}=16
$$

结果如下。DSA 的两列分别是 indexer 和 core attention。CSA 的第二列包含 core attention 与 local window。HCA 的第二列包含 global compressed attention 与 local window。

| 序列长度 $L$ | Dense | DSA indexer / core | CSA indexer / core+window | HCA global+window | Dense / CSA / HCA 条目 |
|---:|---:|---:|---:|---:|---:|
| 512 | 131,328 | 131,328 / 4,068 | 16,128 / 11,880 | 3,840 / 11,912 | 512 / 64 / 16 |
| 1,024 | 524,800 | 524,800 / 8,164 | 65,024 / 24,168 | 15,872 / 32,136 | 1,024 / 128 / 32 |
| 2,048 | 2,098,176 | 2,098,176 / 16,356 | 261,120 / 48,744 | 64,512 / 97,160 | 2,048 / 256 / 64 |
| 4,096 | 8,390,656 | 8,390,656 / 32,740 | 1,046,528 / 97,896 | 260,096 / 325,512 | 4,096 / 512 / 128 |

![mini 机制实验中的压缩条目数](05-infographic-experiment-counts.png)

这个表有两个值得注意的地方。

第一，DSA 的 core 确实很小，但 indexer 仍然接近 dense 的候选扫描量。

第二，CSA 先把候选池压到 $1/m$ 左右，HCA 则把全局摘要进一步压到 $1/m'$ 左右。

这些数字是 pair count，不是 FLOPs。真实 indexer 还使用更小的维度和低精度路径，因此不能直接把表中的比值当成端到端速度。

为了验证社区实现本身的基本路径，我还运行了 deepseek-v4-mini-pytorch 的 CSA/HCA 测试。当前 CPU 环境的结果是：**261 passed in 1.84s**（本次质量核查时复现）。

这只能说明缩小实现的形状、因果性和梯度检查通过，不是官方 V4 的性能证明。

## 资料来源

- [DeepSeek-V4: Towards Highly Efficient Million-Token Context Intelligence](https://arxiv.org/abs/2606.19348)：CSA、HCA 和 1M context 效率数据，重点参见 Introduction 与注意力章节。
- [DeepSeek-V4-Pro 官方模型卡](https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro) 与 [config.json](https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/blob/main/config.json)：核验 2026 年 V4-Pro 的模型规格和注意力配置。
- [DeepSeek-V4-Flash 官方模型卡](https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash)：核验 V4-Flash 的模型规格和 1M context 信息。
- [DeepSeek-V3.2 Technical Report](https://arxiv.org/abs/2512.02556)：DSA 与 Lightning Indexer 的历史承接。
- [deepseek-v4-mini-pytorch](https://github.com/pablo-reyes8/deepseek-v4-mini-pytorch)：社区缩小实现；本文只引用其 CSA/HCA 测试结果，不把它当作官方性能基准。

## 结尾：注意力的下一步，是少找一点

回到开头的问题。MLA 把每个位置的记录压短了，DSA 开始只挑重点。CSA 先缩短候选池再做稀疏选择，HCA 则用极短摘要保留全局视野。

它们不是简单的“谁替代谁”。每一步都在处理上一阶段留下的瓶颈：**MLA 压缩存储，DSA 减少精读，CSA 缩短候选池，HCA 保留全局。**

下一篇继续拆 V4 注意力内部最激进的部分：为什么一个压缩 entry 可以同时当 key 和 value？Partial RoPE 为什么只旋转最后 64 维？输出为什么还要做 de-RoPE？

再下一篇，我们再看 mHC 如何让这套激进结构在深层网络里保持稳定。

📖 **[大模型原理合集](https://mp.weixin.qq.com/mp/appmsgalbum?__biz=MzkyMzQyODExNQ==&action=getalbum&album_id=4597831652025925632#wechat_redirect)**：BPE → 词嵌入 → 位置编码 → 注意力 → KDA 长上下文 → FFN → 归一化残差 → Transformer 全景 → 预训练 → Kimi K3 架构 → SFT → RLHF → PPO → GRPO → RLVR → 推理加速

🔥 **DeepSeek 技术解密**：AI 上下文为什么越长越慢 → MoE 混合专家 → MLA → **V4 注意力（本篇）** → FP8 训练

如果你在长文档、代码仓库或 Agent 任务里用过长上下文，欢迎**点赞、收藏**。关注「数解AI」，下一篇继续拆 K = V、Partial RoPE 和 de-RoPE。

你会优先选择“完整保留但检索更贵”的模型，还是“先压缩筛选、速度更快但可能漏掉细节”的模型？最担心哪类信息在压缩时被忽略？

#DeepSeek技术解密 #CSA #HCA #稀疏注意力 #数解AI
