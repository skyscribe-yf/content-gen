---
title: "DeepSeek-V4为何不用MLA？"
author: "数解AI"
date: "2026-08-04"
type: "原理篇"
series: "DeepSeek 技术解密"
keywords: ["DeepSeek-V4", "CSA", "HCA", "DSA", "Lightning Indexer", "稀疏注意力", "长上下文"]
illustration_type: "infographic / flowchart / comparison"
illustration_density: "per-section"
illustration_style: "notion editorial"
illustration_palette: "warm graphite with cyan accents"
illustration_backend: "zairouter / gpt-image-2"
illustration_count: 5
---

# DeepSeek-V4为何不用MLA？

## 文章定位

- 本篇是 DeepSeek 技术解密 D4，承接已发布的 [MLA 文章](https://mp.weixin.qq.com/s/HHMNEdCYThOjCLRozQorhg)。
- 文章只回答一个问题：MLA 已经把 KV cache 压小，为什么 V4 仍然要换成 CSA + HCA？
- DSA 作为 V3.2 的桥接机制出现，重点解释“主注意力变稀疏了，但索引器仍要面对长序列”的剩余瓶颈。
- 第二篇再深入双流压缩、`K = V`、Partial RoPE/de-RoPE、Attention Sink 和 FP4 indexer；第二篇结尾再预告 mHC。
- 推荐篇幅：正文约 2,800-3,500 字，公式 6-8 组，配图 5 张。

## 核心结论

1. MLA 解决的是 KV cache 的**每个 token 存多少**，没有改变**要面对多少个 token**。
2. V3.2 的 DSA 让核心注意力只看 top-k，但 Lightning Indexer 仍要给长序列打分；稀疏了核心计算，序列长度还在。
3. V4 的 CSA 把流程改成“先压缩 KV 序列，再用 Lightning Indexer 选 top-k 压缩块”，同时保留滑动窗口补局部信息。
4. HCA 不做稀疏选择，而是把 KV 压得更狠，让 dense attention 只在很短的摘要序列上运行。
5. CSA 负责精准找重点，HCA 负责便宜看全局，二者交替才是 V4 面向 1M context 的答案。

## 标题与摘要

### 标题

**DeepSeek-V4为何不用MLA？**

### 摘要

MLA 把 KV cache 压小了，却没有让注意力少看一些位置。到了百万 token 上下文，真正的墙从“存不下”变成“找不动”。DeepSeek-V4 用 CSA 先压缩再稀疏选择，用 HCA 保留极低成本的全局视野，重新分配了注意力的工作。

## 正文结构

### 0. 开头：MLA 才发布多久，为什么已经换了？（约 250 字）

开场画面：上一期刚讲完 MLA 如何压缩 KV cache，读者自然会问：既然 KV 已经变小，为什么 V4 不继续沿用？

给出悬念：在短上下文里，缓存体积是主要矛盾；在 1M context 里，模型即使把每个位置存得很小，仍然要反复面对很长的序列。V4 换的不是一个小零件，而是注意力的工作方式。

承接链接：MLA 只做 1 段回顾，链接已发布文章，不重复推导低秩 KV 压缩和矩阵吸收。

### 1. MLA 解决了“存多少”，没解决“看多少”（约 450 字）

从标准注意力开始：

$$
\operatorname{Attn}(q_t,K,V)=\operatorname{Softmax}\left(\frac{q_tK^\top}{\sqrt{d_h}}\right)V
$$

说明在长度为 $L$ 的序列里，query 仍要面对前面的大量 key；MLA 把每个位置的 KV 表示压到 latent，不等于把位置数量压掉。

用类比承接：书变成了更薄的卡片，但卡片数量没有减少；读者仍要从头翻到尾。

### 2. DSA：第一次让注意力学会“只看重点”（约 550 字）

#### 2.1 DSA 在路线中的位置

明确区分：V3.2 是 **MLA + DSA**，DSA 不是 MLA 的替代品。MLA 负责存储压缩，DSA 负责稀疏选择。

#### 2.2 Lightning Indexer 和 top-k

给出简化但与论文一致的打分形式：

$$
I_{t,s}=\sum_{h=1}^{n_h^I}w_{t,h}^I\,\operatorname{ReLU}\left((q_{t,h}^I)^\top K_s^I\right)
$$

再写选择：

$$
\mathcal{S}_t=\operatorname{TopK}(I_{t,:})
$$

解释 ReLU 的作用：这里不需要把整行分数归一化成概率，只需要排序找重点。

#### 2.3 DSA 的剩余瓶颈

核心注意力的可见 pair 从约 $O(L^2)$ 降为 $O(Lk)$；但 indexer 仍需扫描候选位置，若候选仍是原始序列，索引阶段仍随 $L$ 二次增长。这个矛盾是 V4 重构的入口。

### 3. CSA：先把书压成目录，再选重点章节（约 700 字）

#### 3.1 双流重叠压缩

按技术报告的记号介绍：

$$
C^a=H W_{KV}^a,\qquad C^b=H W_{KV}^b
$$

$$
Z^a=H W_Z^a,\qquad Z^b=H W_Z^b
$$

对每个压缩块，使用带位置偏置的 softmax 得到两条流的权重 $S^a,S^b$，再合并：

$$
C_i^{\mathrm{Comp}}
=\sum_{j=mi}^{m(i+1)-1}S_j^a\odot C_j^a
+\sum_{j=m(i-1)}^{mi-1}S_j^b\odot C_j^b
$$

解释：当前块走 $a$ 流，前一个块走 $b$ 流；每个摘要看到了 $2m$ 个 entry，但相邻摘要重叠，所以有效压缩比仍为 $m$，不是 $2m$。

#### 3.2 在压缩后的池子里做 Lightning Indexer

V4 不再直接对全量 token 做索引，而是先得到 $K^{I\mathrm{Comp}}$，再生成低秩 indexer query：

$$
c_t^Q=h_tW^{DQ},\qquad q_t^I=c_t^QW^{IUQ}
$$

$$
I_{t,s}=\sum_h w_{t,h}^I\,\operatorname{ReLU}\left((q_{t,h}^I)^\top K_s^{I\mathrm{Comp}}\right)
$$

此时候选数大约从 $L$ 变成 $L/m$，top-k 仍然保留，但索引池已经变短。

#### 3.3 core attention 与滑动窗口

选出的压缩 entry 同时作为 key 和 value：

$$
o_{t,i}=\operatorname{CoreAttn}(q_{t,i},C_t^{\mathrm{SprsComp}},C_t^{\mathrm{SprsComp}})
$$

再补一条未压缩的滑动窗口，弥补压缩块的边界和局部词法关系。

### 4. HCA：不挑章节，直接看极短摘要（约 450 字）

HCA 使用更大的压缩因子 $m'\gg m$，但不做 top-k：

$$
C=H W_{KV},\qquad Z=H W_Z
$$

$$
C_i^{\mathrm{Comp}}=\sum_{j=m'i}^{m'(i+1)-1}S_j\odot C_j
$$

对极短的摘要序列做 dense attention：

$$
o_{t,i}=\operatorname{CoreAttn}(q_{t,i},C^{\mathrm{Comp}},C^{\mathrm{Comp}})
$$

用“CSA 是精读，HCA 是目录总览”解释分工：CSA 保留远处重点，HCA 让每层都能低价接触全局。

### 5. 为什么不是继续修补 MLA？（约 500 字）

用对照表收束：

| 机制 | 解决的主要问题 | 仍然付出的代价 |
|---|---|---|
| MLA | 每个位置的 KV 表示太大 | 位置数量没有减少 |
| MLA + DSA | 核心注意力只看 top-k | Indexer 仍面对长序列 |
| CSA | 压缩序列后再稀疏选择 | 需要压缩、索引、局部窗口协同 |
| HCA | 极低成本保留全局摘要 | 单个摘要更粗糙，需要与 CSA 互补 |

明确措辞：论文直接给出的是 CSA/HCA 结构与效率结果；“V4 为什么抛弃 MLA”是基于瓶颈对照做出的工程解释，不把推测写成官方原话。

用一句话引入下一篇细节：V4 还做了一个更激进的决定——压缩后的 entry 同时当 key 和 value；这会把位置编码问题推到台前。

### 6. 论文数据与 mini 机制实验（约 350 字）

#### 6.1 论文数据

- V4-Pro 与 V4-Flash 都支持 1M context。
- 1M 场景下，相对 V3.2：V4-Pro 单 token inference FLOPs 为 27%，KV cache 为 10%；V4-Flash 分别为 10% 和 7%。
- 明确说明这是论文估算/报告的比较口径，不等同于所有任务的端到端加速倍数。

#### 6.2 社区 mini 机制实验

使用 `experiment.py`，参数默认 `m=8`、`m'=32`、`k=8`、`window=16`，输出不同 $L$ 下的：

- dense causal score pair 数；
- DSA indexer 与 core pair 数；
- CSA 压缩后 indexer、core 和 local window pair 数；
- HCA 压缩后的 dense global pair 数；
- 压缩条目数量。

上游社区实现 `pablo-reyes8/deepseek-v4-mini-pytorch` 的 CSA/HCA 单元测试在当前 CPU 环境为 `149 passed`；这只能证明缩小实现的形状、因果性和梯度检查通过，不能证明官方 V4 性能。

### 7. 结尾：注意力的下一步不是“记更多”，而是“少找一点”（约 200 字）

回扣开头：MLA 把卡片变薄，CSA/HCA 进一步减少要翻的卡片数量，并给“精准找重点”和“低价看全局”分工。

下一篇预告：`K = V` 为什么能继续省缓存？Partial RoPE 为什么只旋转最后 64 维？为什么还需要 de-RoPE 和 Attention Sink？更后面再讲 mHC 如何让这套激进结构训练不崩。

开放式问题：如果只能二选一，你更愿意让模型保留完整原文，还是让模型先压缩成摘要再找重点？

## 配图计划

1. `00-cover.png`：封面标题“DeepSeek-V4为何不用MLA？”；画面为变薄的卡片堆与压缩目录，不出现未经核验的数字。
2. `01-flowchart-attention-evolution.png`：MHA → MLA → MLA+DSA → CSA+HCA；每一步标注“压缩什么、跳过什么”。
3. `02-comparison-dsa-csa-indexer.png`：左侧原始 token 池上的 DSA indexer，右侧压缩 KV 池上的 CSA indexer。
4. `03-framework-csa-dual-stream.png`：$a/b$ 双流重叠压缩、Top-k、滑动窗口和 core attention 数据流。
5. `04-comparison-csa-hca.png`：CSA 精读重点块，HCA 浏览全局摘要，突出两种注意力交替分工。
6. `05-infographic-experiment-counts.png`：机制实验中的原始条目、CSA 条目和 HCA 条目，图注标明“机制计数，不是官方性能基准”。

## 来源与核验口径

- [DeepSeek-V4 Technical Report, arXiv:2606.19348](https://arxiv.org/abs/2606.19348)，重点为 §2.3 和 Introduction 效率数据。
- [DeepSeek-V4-Pro 官方模型卡](https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro)，核验模型规模、1M context 和效率摘要。
- [DeepSeek-V4-Pro config.json](https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/raw/main/config.json)，核验 `model_type`、`num_hidden_layers`、`num_attention_heads`、`num_key_value_heads`、`max_position_embeddings` 等字段。
- [DeepSeek-V3.2 论文](https://arxiv.org/abs/2512.02556)，用于 DSA/Lightning Indexer 的历史承接。
- [社区 mini V4 PyTorch 实现](https://github.com/pablo-reyes8/deepseek-v4-mini-pytorch)，用于 CPU 机制测试，不作为官方性能来源。

## 自检清单

- [ ] 标题不超过 22 字，关键词前置。
- [ ] MLA 有正文回顾和已发布微信链接。
- [ ] DSA 明确写成 V3.2 的桥接机制，不冒充 V4。
- [ ] CSA/HCA 的压缩、选择、滑窗和 dense/sparse 分工讲清楚。
- [ ] 所有公式使用 LaTeX，独立公式使用 `$$...$$`。
- [ ] 论文数据与 toy experiment 分开标注。
- [ ] `mHC` 只作第二篇之后的预告，本篇不展开。
- [ ] 文末有 3-5 个话题标签、合集导航、下一篇预告、开放式问题。
