---
title: "1M 上下文只算 2048 个 token，MiniMax 的稀疏为什么这次成了？"
wechatUrl: "https://mp.weixin.qq.com/s/9m_vkJpWr__Ce7JJQYOyIQ"
author: "数解AI"
date: "2026-10-29"
type: "原理"
series: "开源大模型技术揭秘"
digest: "MiniMax 先押 7:1 混合线性注意力，又退回全注意力，七个多月后全押 MSA 块稀疏。1M 上下文里每个 query 每层只看 2048 个 token。关键词：MiniMax、稀疏注意力、长上下文。"
cover: "00-cover.png"
keywords: ["MiniMax", "稀疏注意力", "长上下文"]
scheduledPublish: "2026-10-29T22:00:00+08:00"
---

2025 年 10 月 30 日，MiniMax 在 M2 的复盘长文里写下一句：在真实的工业级系统里，高效注意力要能确定性地击败全注意力，还差得远。

全量注意力还是稀疏注意力，在过去一段时间一直是一个争议的焦点。最初我看到 MiniMax 并不看好稀疏注意力、而想押注全量注意力的时候，其实对它技术方向充满了期待，希望它能走出一条不同于 DeepSeek 的路来。

七个多月后，2026 年 6 月 1 日，M3 发布。注意力的核心换成 MSA 块稀疏，1M 上下文回来了。

10 月 19 日，M3.1 Flash 把 M3 仅剩的前 3 层全注意力也换成了稀疏。连保险都撤了。

中间这七个多月，到底补了什么？

## 一、先押线性，再退回全量，最后只算 2048 个

Text-01 是 2025 年 1 月的事：80 层里每 7 层 lightning attention 配 1 层 softmax，456B 总参、45.9B 激活，1M 训练、4M 外推。

线性注意力几乎不存 KV，代价是检索弱。论文自己承认这一点，才插进 softmax 层来补。

M2 在同年 10 月全部退回 GQA 全注意力：62 层，229.9B / 9.8B，上下文 192K。

官方复盘给了三条理由：小规模榜单打平，大规模多跳推理掉；SWA 各种混合做遍全负；CPT 改不动预训练早期成形的 retrieval 和 induction head。

| | 注意力设计 | 总参 / 激活 | 上下文 |
|---|---|---|---|
| Text-01 | 7:1 线性 + softmax | 456B / 45.9B | 1M |
| M2 | GQA 全注意力 | 229.9B / 9.8B | 192K |
| M3 | MSA 块稀疏 | 428B / 23B | 1M |

还是很希望这家当时位列前几的大模型厂商给出一条不同的解法，毕竟某国外前沿模型据说一直押注于全注意力机制。我猜测他们内部一定是经历了什么路线或者方向上的摇摆。

M3 在 2026 年 6 月回来，428B / 23B，1M。它既不是回到线性，也不是固定滑窗，而是保留 softmax，只挑块。

线性那条路，Kimi K3 的 KDA 走得更远（[KDA 篇](https://mp.weixin.qq.com/s/_RR5LLWgjGNm-qXdSdnAGA)），智谱和阿里则把两种注意力拼进同一层（[拆注意力](https://mp.weixin.qq.com/s/5w1mEVLW5igvJ28Dn6pe9A)）。1M 上下文的 KV 账本到底差多少，我们在[四家对比](https://mp.weixin.qq.com/s/7BdQlueJrRJ5f-x3v_2VqA)里逐本算过。

![三代路线：线性混合、全注意力、块稀疏](01-three-turns.png)

## 二、128 个 token 一盒，每个 group 自己列单

MSA 分两个分支。Index Branch 决定看哪儿，Main Branch 只对选中的地方做精确 softmax。

索引分支极轻：每个 GQA group 一个 index query 头，全局共用一个 index key 头。

它先给每个 token 打分，再按 128 个 token 一块做 max-pool，取 top-16。本地块无条件常驻。

1M token 像一屋子卷宗，128 页装一盒，每层只调 16 盒。每个 group 自己列调阅单，不是全公司共用一张。

选择结果按 group 共享：一个 group 里 16 个 query 头共用一张单子。

主分支只算 16 × 128 = 2048 个 token。候选少了，注意力的形式一点没缩水。

$$F_{\text{GQA}} = 2H_q d_h N^2$$

$$F_{\text{MSA}} = H_{kv} d_{idx} N^2 + 4H_q d_h N k B_k$$

两式一比，1M 处差 28.4 倍。

按块级选择，相当于说我做了一系列事情之后，才会反思是不是要换一个走法。而按 token 级选择，那就更谨慎，也更灵活了，每走一步都得考虑考虑。

和 NSA 的三分支、token 级、全头共享相比，MSA 是两分支、块级、每个 group 独立选（[NSA 篇](https://mp.weixin.qq.com/s/HIBJliEXWtVyJqvH_Ocbog)）。和 V4.1 的 lightning indexer 一样，它想让索引成本和上下文长度脱钩（[四十层那篇](https://mp.weixin.qq.com/s/DBI990JLYtbxQGF3LIWbhQ)）。

![索引分支选块，主分支精确 softmax](02-msa-branches.png)

## 三、索引器先当 40B token 的学徒

难点在 top-k 不可微。语言建模的梯度，传不到 index 投影上。

解法是 KL 对齐：让 index 分支的分布，去对齐主分支在该 group、在选中 token 上的平均注意力分布。

这里有两个 stop-gradient。teacher 分布 detach，index 分支的输入也 detach。

于是辅助损失只更新两个 index 投影，一点不碰主干。

然后是 40B token 的 warmup：两个分支都跑全注意力，只训索引器。热完再切稀疏，让它接管路由。

其实这种想法在工程上屡见不鲜了。对于一些关键的模块，如果从一个随机数开始训练，它可能就四处乱撞，根本没有办法优化到一个好的状态。这个时候更需要的是一个类似于 warm up 的过程。

档案管理员在这里回收一次：先跟着老馆员学归类，再自己列单。

对照 SWA-CPT 就清楚了。滑窗是固定规则，没有可训的部件。

MSA 从 2.6T 的全注意力 checkpoint 接 400B，前 40B 热身，能成。SWA 败在全局模式早期定型，事后改不动。

## 四、三个条件同时成立，才叫能上生产

条件一，选择器是可训练的部件，不是训练完再硬换上去的。

条件二，主分支保留精确 softmax，只缩小支撑集，不改注意力形式。

条件三，kernel 把省下的 FLOPs 兑现成墙钟。

这三个条件，精确的 softmax 之前文章已经讲了不少，反而是 kernel 协同容易被忽略。

第三条最不像论文，却最难。三处细节：

- exp-free top-k：softmax 保序，直接排原始分，跳过 max / exp / sum；每线程用寄存器维护一个 k 元小顶堆。
- KV-outer：以 KV 块为外循环，聚合命中它的 query，每块只读一次；两段式 LSE combine 处理 split-K。
- 预调度分块：热门块（sink 行）拆给多个 CTA，别让单块拖垮整个 kernel。

账本：H800 上 prefill 14.2×、decode 7.6×。M3 对 M2 在 1M 处，prefill 9×、decode 15×，单 token 算力 1/20。

![28.4 倍理论算力，14.2 倍与 7.6 倍墙钟](03-budget.png)

## 五、账单的另一面：三条边界

检索有残差。HELMET-128K 总体 46.53 掉到 45.93，−0.60，Rerank / RAG 那一项 −2.10。

RULER-128K 总体 +0.12，但 CWE / FWE 是 −1.35。多数打平，检索略亏。

![MSA 与全注意力的差距：多数打平，检索略亏](04-caveats.png)

FLOPs 不等于墙钟。28.4× 是理论值，建索引、top-k、反向索引、query gather 全要花钱。

落到 H800 上，只剩 14.2× 和 7.6×。

还有规模。消融做在 109B / 3T，生产 M3 是 428B。同一个 428B 上差多少，论文没给。

有时候理论上的数字，转化到实际工程落地，就是会有很大的损耗。这个损耗比其实也算非常优秀了，很多时候想有一倍提升都是超级困难的。这也是为什么架构优化和演进这么有趣的原因，以小博大的效果往往需要靠模型架构上的大大小小的创新。

更根本的一层：稀疏注意力是矩阵逼近，不是挑 mass。扔掉的列里可能藏着高分数（[MASA 篇](https://mp.weixin.qq.com/s/imKzKYitjtrvAcIB3fIr6A)）。

## 六、M3.1 把最后三层保险也撤了

M3 还留前 3 层全注意力当保险。M3.1 Flash 把这三层换成 MSA，整个模型全稀疏。

顺带做了 QAT：路由专家压到 W4A4，注意力 KV 压到 4 位，细节在 [FP4 那篇](https://mp.weixin.qq.com/s/Bra0y-wCSeYEW5ABxa3slw)。

账本：线上推理快将近 3×，agent 综合成本 −70%，200+ TPS，$0.15 / $0.60 / $0.015 每百万 token。

这无疑是一个非常冒险的决定，毕竟其他几家如 Kimi 和 Qwen 系列，都还遵循着相对保守一点的混合架构设定。具体效果如何，还是要看实际场景大量用户的校验了。

关键在这里：稀疏不是推理时的一个开关。模型就是按稀疏训练的，当 dense 跑，是分布外近似。

所以回到开头的问题。这七个多月补的不是一个更快的 kernel，是把选择器从「事后替换」挪回了「训练对象」。

你觉得几家大厂的稀疏注意力探索努力，MiniMax 在略微落后的情况下，还有机会完成逆袭吗？

觉得这笔账算得清楚，点个赞 👍、收藏 ⭐ 备用，转发给还在被长上下文账单折磨的朋友。关注「数解AI」，AI 原理和工程，慢慢拆。

下一篇拆 DSpark：1M 上下文里，投机解码的草稿头怎么不拖后腿。

📖 **[大模型原理合集](https://mp.weixin.qq.com/mp/appmsgalbum?__biz=MzkyMzQyODExNQ==&action=getalbum&album_id=4597831652025925632#wechat_redirect)**：注意力机制 → KDA 长上下文 → KV 账本 → NSA 稀疏 → **MiniMax MSA**

🔥 **热门文章**：

[KV缓存存进SSD：慢50倍的硬盘，为什么反而更快？](https://mp.weixin.qq.com/s/40BQ06eDTv4-2r8FmQ_rMA)  
[高维空间为什么全是壳？内积才是那把尺子](https://mp.weixin.qq.com/s/Nrfr-90Fpu3mFDML9s0d1Q)  
[高斯为什么二阶就够？非线性去哪了](https://mp.weixin.qq.com/s/gs_3y7JXuBLlzR5w6jW6fQ)  
[微软用 Go 重写 TypeScript，他一个人用 C++ 又写了一遍](https://mp.weixin.qq.com/s/GmPJAh8ERPkm64KzYirV2g)  
[学习率怎么自动调？Adam 优化器拆给你看](https://mp.weixin.qq.com/s/aSLVO-otvr2rxIU1kr2eAA)  
[DeepSeek-V4为何不用MLA？](https://mp.weixin.qq.com/s/MQEgbY16mLs-N7g2xKW1HQ)  
[Kimi K3：KDA怎么撑住1M上下文？](https://mp.weixin.qq.com/s/_RR5LLWgjGNm-qXdSdnAGA)  
[智谱阿里为什么要改注意力？KV缓存竟砍4.4倍](https://mp.weixin.qq.com/s/5w1mEVLW5igvJ28Dn6pe9A)  
[同样 1M 上下文，KV 缓存差 15 倍：四家架构差在哪一层](https://mp.weixin.qq.com/s/7BdQlueJrRJ5f-x3v_2VqA)  
[DeepSeek 注意力只算 8.6%，为什么 V4 反而不用？](https://mp.weixin.qq.com/s/HIBJliEXWtVyJqvH_Ocbog)  
[DeepSeek V4.1 四十层网络，为什么不给每层都记账？](https://mp.weixin.qq.com/s/DBI990JLYtbxQGF3LIWbhQ)  
[注意力分数高 66 倍的那列，为什么反而带来 98% 的误差？](https://mp.weixin.qq.com/s/imKzKYitjtrvAcIB3fIr6A)  
[FP4量化：4位数字怎么做到无损](https://mp.weixin.qq.com/s/Bra0y-wCSeYEW5ABxa3slw)

**参考资料与数字溯源**

1. MiniMax (2025-01). Scaling MiniMax-01（arXiv:2501.08313）：Text-01、80 层、7:1、456B / 45.9B、1M 训练 4M 外推。
2. MiniMax (2025-10-30). Why Did MiniMax M2 End Up as a Full Attention Model?（minimax.io 官方长文）：全注意力回调、SWA 全负、CPT 改不动 retrieval / induction head。
3. MiniMax (2026-05). MiniMax-M2 Technical Report（arXiv:2605.26494）：62 层、229.9B / 9.8B、48Q / 8KV、192K。
4. MiniMax (2026-06). MiniMax Sparse Attention（arXiv:2606.13392）：109B / 6B 消融、Bk=128、k=16、28.4×、14.2× / 7.6×、HELMET / RULER 表 3。
5. MiniMax (2026-06-01). M3 官方发布：428B / 23B、1M、对 M2 的 9× / 15×。
6. MiniMax (2026-10-19 / 10-25). M3.1 Flash 官方博客与 HF 模型卡（huggingface.co/MiniMaxAI/MiniMax-M3.1-Flash）：全模型稀疏、QAT、3× / −70% / 200+ TPS。

#MiniMax #稀疏注意力 #长上下文 #开源大模型 #数解AI
