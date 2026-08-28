---
wechatUrl: "https://mp.weixin.qq.com/s/5w1mEVLW5igvJ28Dn6pe9A"
title: "智谱阿里为什么拆注意力？KV缓存砍4.4倍"
author: "数解AI"
date: "2026-08-27"
type: "原理篇"
series: "开源大模型技术揭秘"
digest: "GLM-5.3-Flash 和 Qwen3.8-Flash-Next 同一天发布，都拆掉了全注意力：一个用 KDA 压缩记忆 + MLA 省 KV，一个用 Gated DeltaNet 记笔记 + QSA 稀疏查档案。KV 缓存砍 4.4 倍凭什么不掉点？稀疏化成了行业共识，但稠密模型还没死。"
cover: "00-cover.png"
keywords: ["GLM-5.3-Flash", "Qwen4", "稀疏注意力", "KDA", "Gated DeltaNet", "KV缓存", "混合注意力"]
---

你让 AI 读一份 100 万字的文档，它每生成一个字，都要回头把全部历史翻一遍——这就是注意力。智谱和阿里，同一天宣布：不翻了。

8 月 26 日，智谱揭晓了匿名刷屏一周的「牛来」真身——GLM-5.3-Flash。当晚 23 点，阿里开源了 Qwen3.8-Flash-Next，官方明说是下一代 Qwen4 架构的预览版。两家不约而同干了一件事：**把全注意力拆了**。

## ① 为什么拆：注意力是长上下文的最大成本

先回忆一下注意力在干什么。模型生成每个字时，都要回头「看」一遍上下文里所有位置，决定哪些信息重要。[注意力机制是什么？别再当数据库查询](https://mp.weixin.qq.com/s/KrilwX6VRjI9KfjvD7C6kw) 里讲过，它本质是拿当前问题去数据库里查。

问题在于这个「查」有两笔账：

**第一笔，算力账。** 注意力要算「当前字 × 每个历史位置」的相关性，上下文翻一倍，计算量翻四倍。1M 上下文意味着每个字要跟 100 万个历史位置各算一次相关性。100 万 × 100 万，十亿亿次量级的计算，每生成一个字都要来一遍。

**第二笔，存储账。** 每个历史位置都要留一份 K 和 V（key 和 value，相当于档案的索引和内容），上下文多长，KV 缓存就多长。[为什么AI上下文越长越慢？两道数学硬墙一次讲透](https://mp.weixin.qq.com/s/PLVRS0TTHXHDve1Z3r6M7Q) 里拆解过这两道墙——算力墙和显存墙，长上下文时代两堵墙一起塌。

所以各家都在想：能不能不翻全部历史？

![注意力成本曲线：全注意力 O(n²) vs 混合注意力近似线性](01-attention-cost.png)

## ② 智谱怎么拆：34 层压缩记忆 + 11 层省 KV

GLM-5.3-Flash，320B 总参数，每个 token 只激活 18B，45 层，1M 上下文，MIT 开源。

匿名刷屏一周的「牛来」，昨天揭晓真身了——GLM-5.3-Flash，智谱家的。

它的注意力是 3:1 混合：**34 层 KDA + 11 层 MLA/DSA**。

KDA 是线性注意力——不翻全部历史，而是把历史持续压缩成一份「浓缩笔记」，每次只读笔记。[Kimi K3：KDA怎么撑住1M上下文？](https://mp.weixin.qq.com/s/_RR5LLWgjGNm-qXdSdnAGA) 拆解过同款机制：笔记越写越厚，但永远比原文小得多。

MLA 则是把每个位置留下的 KV 记录压短——[显存被谁吃掉了？DeepSeek如何省下90%](https://mp.weixin.qq.com/s/HHMNEdCYThOjCLRozQorhg) 讲过，一份 KV 记录可以压缩成更短的表示，省显存。

两个机制叠加，官方数字：**注意力计算降到 1/3.01，KV 缓存降到 1/4.44**。这就是标题里「砍 4.4 倍」的出处。

除了注意力，GLM-5.3-Flash 还改了层与层之间的连接方式：mHC 残差路径，把信息通道从一条拓宽成四条并行流。每条流负责不同距离的信息传递，再用一个「总量必须等于 100%」的约束保证不打架。这个细节不展开。你只需要知道：拆注意力不是孤立的改动，整条信息通路都在为长上下文重新设计。

SemiAnalysis 的料最震撼：预览周每天 100T tokens 的处理量，全是中国芯片扛下来的。

![拆注意力：全注意力被拆成压缩记忆 + 稀疏检索](03-attention-split.png)

## ③ 阿里怎么拆：GDN 记笔记 + QSA 查档案

Qwen3.8-Flash-Next，125B 总参数，每个 token 只激活 6B。外加 51B 的 n-gram 嵌入，放在显存外，用的时候异步取。训练成本只有 Qwen3.7-Plus 的 1/9。

它的注意力也是 3:1 混合，48 层排成 12 组，每组「3 层 Gated DeltaNet + 1 层 QSA」。

Gated DeltaNet（GDN）——把历史持续压缩成「浓缩笔记」。注意，这和智谱的 KDA 是同一个思路：**线性注意力，压缩记忆**。

QSA（Qwen Sparse Attention）——不逐字检索，而是按「微块」为单位，先筛出值得看的小块。再精准查档案。相当于笔记记了大概，关键细节回原文翻。

还有一笔账值得说：那 51B 的 n-gram 嵌入，本质是一张「局部模式查表」。根据上下文里相邻的几个字直接查表拿特征，几乎不增加每个 token 的计算量。而且放在显存外，用的时候异步取。等于用硬盘空间换模型容量，不占推理时的显存。

一句话：**GDN 负责记住，QSA 负责找到。**

## ④ 殊途同归：稀疏化成了行业共识

两家方案对照：

| | 智谱 GLM-5.3-Flash | 阿里 Qwen3.8-Flash-Next |
|---|---|---|
| 总参数 / 激活 | 320B / 18B | 125B / 6B |
| 混合结构 | 34 层 KDA + 11 层 MLA/DSA | 12 组 ×（3 层 GDN + 1 层 QSA） |
| 压缩记忆 | KDA（线性注意力） | Gated DeltaNet |
| 稀疏检索 | MLA/DSA | QSA（微块级） |
| KV 缓存 | 砍 4.44 倍 | 未公布（GDN 无 KV） |
| 上下文 | 1M | 262K 原生，可扩 1M |

注意看：两家用的技术名词完全不同，但骨架一模一样。**一部分层把历史压成笔记（便宜），一部分层保留精准检索（不掉点）**。。

而且不止这两家。DeepSeek 的 V4 用 CSA/HCA 混合注意力（[DeepSeek-V4为何不用MLA？](https://mp.weixin.qq.com/s/MQEgbY16mLs-N7g2xKW1HQ)），Kimi K3 用 KDA 撑 1M 上下文（[Kimi K3 架构怎么撑住 2.8T 参数？三轴拆给你看](https://mp.weixin.qq.com/s/6GJ2781jJh-dqYswJ07dfA)），连 KV 复用都有专门的玩法（[K=V：一份KV缓存怎么干两份活？](https://mp.weixin.qq.com/s/88kscO8p0kMxHmeGm2llLA)）。

四家国产头部模型，全部转向混合注意力。这不是巧合。

![同一天，两家把全注意力拆成「压缩记忆 + 稀疏检索」](02-architecture-compare.png)

## ⑤ 但是：稠密模型还没死

稀疏注意力模型，从Google论文发表起，到现在已经接近10年，行业基本所有的研究者都收敛到了一个共同的共识上来了，几乎所有的开源模型都采用了花色多样的稀疏注意力机制来降低存储和计算的开销，这方面前面的公众号文章也讨论了好多了。

但就在智谱和阿里发布新架构的同一天，社区里最火的模型，恰恰是一个「什么都没拆」的。

Qwen3.8-27B，27B 稠密模型——不搞 MoE，不搞稀疏注意力，所有参数每个 token 全量激活。Artificial Analysis 独立跑分：Intelligence Index 52。追平 DeepSeek V4 Flash（50）。Agentic Index 51，反超 V4 Pro（50）。编程榜单更夸张：LiveCodeBench 90.3，超过 Claude Opus 4.6 Max 的 88.8。SWE-bench Pro 61.7，同样压过 Opus 4.6 Max 的 53.4。开源两天下载破百万，海外开发者叫它「本地 Opus 4.6」。

值得注意的是，qwen3.8-27B采用了传统的稠密机制，依然取得了接近deepseek v4 flash的智能，是最近社区里面的当红炸子鸡，也许目前给稠密模型判死刑，还为时尚早？

更有意思的是，这俩是同一家公司发的：阿里一边发 Qwen4 稀疏化架构预览，一边发稠密 27B 追平 MoE。自己跟自己打擂台。

![稀疏化是共识，但稠密模型还在发光](04-sparse-consensus.png)

这似乎又回到了计算机科学的一个基本假设上来，作为一门偏重时间验证的科学，追求的从来不是唯一标准答案，而是各种各样的tradeoff。

## ⑥ 回扣：凭什么不掉点？

回到标题的问题：KV 缓存砍 4.4 倍，凭什么不掉点？

因为「压缩记忆 + 精准检索」是互补的：日常生成靠浓缩笔记，便宜；关键细节靠稀疏检索回原文，精准。笔记负责快，原文负责准——两套机制各管一段，所以砍掉的是冗余，不是能力。

我的 token-stats 实测：DeepSeek 14 天 3.9 万次调用，缓存命中率 98.9%，缓存读取量是非缓存输入的 91 倍——代码场景几乎全是缓存。

这也是为什么 KV 缓存的大小，比算力更早成为长上下文的天花板——[KV缓存存进SSD：慢50倍的硬盘，为什么反而更快？](https://mp.weixin.qq.com/s/40BQ06eDTv4-2r8FmQ_rMA) 里算过这笔账：上下文一长，KV 缓存比模型本身还占地方。

所以智谱砍 4.4 倍 KV 缓存，砍的是真金白银的推理成本。写代码的老实人，千万别听自媒体瞎吹——架构怎么变，最终都要落到「同样的智能，更少的钱」。

至于稠密还是稀疏？时间会给出答案。毕竟，写代码的老实人，看的是账单，不是架构图。

一个问题留给你：你最近用的模型，是稠密还是稀疏的？你猜它每生成一个字，要翻多少历史？评论区聊聊。

> 本文收进「开源大模型技术揭秘」合集。前几篇见：[DeepSeek-V4为何不用MLA？](https://mp.weixin.qq.com/s/MQEgbY16mLs-N7g2xKW1HQ) · [Kimi K3：KDA怎么撑住1M上下文？](https://mp.weixin.qq.com/s/_RR5LLWgjGNm-qXdSdnAGA) · [显存被谁吃掉了？DeepSeek如何省下90%](https://mp.weixin.qq.com/s/HHMNEdCYThOjCLRozQorhg) · [KV缓存存进SSD：慢50倍的硬盘，为什么反而更快？](https://mp.weixin.qq.com/s/40BQ06eDTv4-2r8FmQ_rMA)

🔥 **热门文章**：

[KV缓存存进SSD：慢50倍的硬盘，为什么反而更快？](https://mp.weixin.qq.com/s/40BQ06eDTv4-2r8FmQ_rMA)  
[高维空间为什么全是壳？内积才是那把尺子](https://mp.weixin.qq.com/s/Nrfr-90Fpu3mFDML9s0d1Q)  
[学习率怎么自动调？Adam 优化器拆给你看](https://mp.weixin.qq.com/s/aSLVO-otvr2rxIU1kr2eAA)  
[DeepSeek-V4为何不用MLA？](https://mp.weixin.qq.com/s/MQEgbY16mLs-N7g2xKW1HQ)  
[高斯为什么二阶就够？非线性去哪了](https://mp.weixin.qq.com/s/gs_3y7JXuBLlzR5w6jW6fQ)  
[SFT微调：1万条数据就能让模型听话？](https://mp.weixin.qq.com/s/vwXGbjm9Ai1GPvQi5O3UyQ)  
[注意力机制是什么？别再当数据库查询](https://mp.weixin.qq.com/s/KrilwX6VRjI9KfjvD7C6kw)  
[为什么AI上下文越长越慢？两道数学硬墙一次讲透](https://mp.weixin.qq.com/s/PLVRS0TTHXHDve1Z3r6M7Q)  
[Kimi K3：KDA怎么撑住1M上下文？](https://mp.weixin.qq.com/s/_RR5LLWgjGNm-qXdSdnAGA)  
[显存被谁吃掉了？DeepSeek如何省下90%](https://mp.weixin.qq.com/s/HHMNEdCYThOjCLRozQorhg)  
[Kimi K3 架构怎么撑住 2.8T 参数？三轴拆给你看](https://mp.weixin.qq.com/s/6GJ2781jJh-dqYswJ07dfA)  
[K=V：一份KV缓存怎么干两份活？](https://mp.weixin.qq.com/s/88kscO8p0kMxHmeGm2llLA)  

如果这篇把「注意力为什么被拆」讲明白了，点个赞 👍、收藏 ⭐ 备用。关注「数解AI」，回复「开源」我把「开源大模型技术揭秘」合集链接发你。

#开源大模型技术揭秘 #GLM #Qwen #稀疏注意力 #数解AI
