---
title: "DeepSeek 注意力只算 8.6%，为什么 V4 反而不用？"
author: "数解AI"
date: "2026-09-02"
type: "原理篇"
series: "开源大模型技术揭秘"
digest: "注意力每步要扫全部历史，64k 上下文时模型真正加载的只有 8.6%。NSA 论文用「扫目录、精读重点、余光保底」三层做到算得少还更准。可这亲儿子 DeepSeek V4 没用，别人还在用。"
cover: "00-cover.png"
keywords: ["NSA", "稀疏注意力", "DeepSeek", "DSA", "注意力"]
---

第一次打开模型的 attention map，我愣了半天：满屏热力图，但真正亮的地方只有一小撮。大部分格子都是浅浅的颜色。

第一眼看到这个热力图，感觉大部分都是浅浅的颜色，似乎没有什么信息量，是否计算都白费了？

这个问题，论文里还真有人认真地算过。答案是：确实有九成多注意力是在算空气——但「算空气」不是模型的错，而是它还没学会偷懒。

你要说这跟 DeepSeek 有什么关系？2025 年，DeepSeek-AI 团队做出一篇论文，第一次让模型从「全算」变成「只算 8.6%」，还更准。可到了自家 V4，这个亲儿子反而没被用上。为什么？

## 一、注意力为什么非要全算？

[注意力机制那篇](https://mp.weixin.qq.com/s/KrilwX6VRjI9KfjvD7C6kw)里我们拆解过 Q、K、V。当前 token 的 query 和历史每个 token 的 key 打分，再按分数加权汇总 value：

$$
\operatorname{Attn}(q_t,K,V)=\operatorname{Softmax}\left(\frac{q_tK^\top}{\sqrt{d_h}}\right)V
$$

这个动作的问题在于：**每个 query 都要和全部历史 K 打一遍分**。

如果历史长度是 $L$，prefill 阶段要处理的 query-key 配对近似 $L^2$ 规模。decode 阶段每次只新增一个 query，但新 query 仍然要回头扫描越来越长的历史。历史翻倍，工作量跟着翻倍，这是 O(N²) 的硬墙。

论文里给过一个理论估计：64k 上下文解码时，注意力占了总延迟的 70~80%。这不是实测，但单看公式你也能感受到——序列一长，大头就是它。

人话版账本：1M 上下文，第 100 万个 token 进来，要和前 999,999 个逐一比对。这还只是**一层**——模型有几十层，每层都这么干。

我在自己租赁的4090卡上跑一个8B的模型，上下文稍微开大一点，就直接OOM没内存了，这个上下文的开销都快被人们说烂了，然而只有当你自己碰到问题，才会有更真切的感受。

所以「能不能少算点？」就成了所有人的目标。你猜怎么着——前面的一批聪明人，全失败了。

## 二、前人为什么都失败？

[长上下文那篇](https://mp.weixin.qq.com/s/PLVRS0TTHXHDve1Z3r6M7Q)里提过，长上下文同时推高计算量和存储量。NSA 论文把前人的失败总结成了三类，翻译成人话：

**第一类，阶段不对。** H2O 只加速 decode，prefill 阶段照样满负荷。MInference 只加速 prefill，生成时又回到全算。省一半，另一半白搭。

**第二类，和 GQA 打架。** GQA 让多个 query 头共享 KV，这本来就是省显存的关键。可 Quest 这种方案让每个头**各自**选重点，KV 访问变成所有头选择的并集——计算省了，搬运没省，等于白省。

**第三类，学不会。** 聚类、哈希这类方法（ClusterKV、MagicPIG）在数学上不可微，梯度传不过去。模型只能「被安排」该看哪，不能「自己学会」该看哪。

这些失败其实都不足为奇，科学技术上的很多进步，都是从失败中找到那条少有人能提前发现的真相。毕竟连早期AlexNet里面的很多看似最佳实践的东西，最后也证明了完全没有任何道理而言。Transformer论文里面的这种玄学其实也不少。

所以 NSA 要同时回答三个问题：能训练吗？能和 GQA 共处吗？prefill 和 decode 能一起省吗？

答案藏在一个人人都熟悉的动作里。

![attention scores 呈块状：相邻 token 的重要度相近](01-attention-map.png)

## 三、读书法三层：扫目录、精读、余光保底

NSA 全称 Native Sparse Attention。论文就是那篇拿下 ACL 2025 最佳论文的《Native Sparse Attention: Hardware-Aligned and Natively Trainable Sparse Attention》。名字先放一边，看它怎么干。

想象你读一份 100 万字的技术文档：

1. **先扫目录**，知道全书大概讲哪些部分；
2. **挑最相关的章节精读**，不要逐页读；
3. **余光保底**，手边这几十页随时能翻，免得错过上下文里的细节。

就这三招。NSA 把注意力分成了三条分支，跟这三招一一对应。

### 层 1：压缩分支——扫目录

把 $l=32$ 个连续 token 压成**一个**「摘要」token。用可学习的 MLP 加块内位置编码，把 32 个 key 的精华汇进一个表示。

注意步长 $d=16$，不是 32——相邻压缩块之间重叠一半。为什么？防止某个刚好横跨块边界的依赖被一刀切开。像目录的条目之间会相互引用一样，重叠让摘要之间留了共有的视野。

### 层 2：选择分支——精读重点

压缩完，怎么知道哪块最重要？NSA 的妙招是：**目录层已经把 attention score 算出来了，直接拿来当重要性分数**。

压缩分支对每个块都会产生一个分数——这个分数就是「这个块跟当前 query 有多相关」。于是选择分支**零额外开销**：直接挑分数最高的 $l'=64$ 长、Top-16 个块，进精读。

这个想法也太妙了，既符合直觉，又能被工程上验证是可以大规模扩展应用，用Kimi创始人杨植麟的话说，叫simple yet effective

### 层 3：滑动窗口——余光保底

最近 $w=512$ 个 token 单独维护一份 KV，不让它参与上面任何筛选。

为什么？论文说得直白：防止模型学会「只看筛选结果」的 shortcut learning。最近的 token 往往是语法、指代、局部语义的重灾区，得保证它们永远能被精确看到。

### 门控：三路不是三选一

三条分支各自输出，最后用一个 MLP + sigmoid 的门控按当前 query 动态加权融合。三条分支还有各自独立的 KV 投影，防止相互之间梯度干扰。

![读书法三层：扫目录 → 精读重点 → 余光保底](04-reading-method.png)

你看这个结构有没有想起什么——开头那张 attention map，亮的格子从来不是随机分布的，而是**成块**的。论文的 Figure 8 直接把这一点画了出来：attention scores 天然 cluster 成块状。相邻 token 的重要度高度相近。这就是读书法的生物学基础：**重要度不是逐 token 跳变的，是逐段跳变的。** 块的边缘在哪儿，模型自己早就「看」见了。

就像你拿到一片长达几百页的技术书，也会先看下目录大纲分成几个部分，然后再决定怎么去读。

## 四、8.6% 账本：算得少凭什么还更强？

先交代账本。64k 解码时，模型每步真正要加载的 token 数：

- 压缩分支：约 4096 个摘要 token
- 选择分支：1024 个 token（16 块 × 64）
- 滑动窗口：512 个 token

合计 **5632** 个，除以 65536，等于 **8.6%**。

也就是说，64k 上下文的每一步解码，91.4% 的 KV 历史根本不用搬进计算核心。这一步是实打实的**内存访问量**省下来，不是虚账。表里还有更长的口径：8192→2048、16384→2560、32768→3584。比例随序列增长一路走低——序列越长，省得越多。

![8.6% 怎么来的：5632 / 65536](02-863-accounting.png)

速度账（相对 FlashAttention-2，同一套 Triton 后端，64k）：

- decode：**11.6×**
- prefill（前向）：**9.0×**
- 反向：**6.0×**

省了 91% 访问量，速度却只快 11.6 倍——因为压缩和门控本身也要算。这正常，省的是搬运，不是全部。

![解码 11.6× 前向 9.0× 反向 6.0×](03-speedup.png)

最反直觉的在这里：**算得少，质量反而更高。**

| 基准 | Full Attention | NSA |
|---|---:|---:|
| LongBench（长上下文综合） | 0.437 | **0.469** |
| NIAH（大海捞针，64k） | 有漏 | **满分** |
| GSM8K | 0.486 | **0.520** |
| AIME 8k | 0.046 | **0.121** |
| MMLU | **0.567** | 0.565 |

LongBench 反超、大海捞针满分、数学类任务涨一倍多。为什么？论文给的解释是：稀疏过滤本身是一种**去噪**——把不相关的历史按权重归零，减少噪声掺进注意力分布。同时，多尺度的归纳偏置（压缩块+精读块+窗口）让模型不必自己学「在哪层看什么」。

这种比例的节约，是在是叫人叹为观止，原来最初scaling law的设想，竟然都不是放之四海而皆准的真理，那不过是朴素经验的预测而已！

诚实说两句边界：这是 27B 规模模型的实验（总参 27B、激活 3B、72 路由专家 + 2 共享），不是千亿级验证。kernel 只针对 A100 调过（Triton）。MMLU 这类知识型基准微降 0.002，别当成「全面碾压」。而且注意——**上文预训练 + YaRN 32k 长上下文适配，损失全程低于 Full Attention**。这是「可训练」的直接证据：它不是死规则，是学出来的。

## 五、后来 DeepSeek 自己怎么用？

一句话，不展开：V3.2 落地了简化版（MLA + DSA，索引器扫全文）。V4 换成了 CSA + HCA——先压缩、再选择。[V4 为何不用 MLA 那篇](https://mp.weixin.qq.com/s/MQEgbY16mLs-N7g2xKW1HQ)和[索引器那篇](https://mp.weixin.qq.com/s/QcZUcxYZUw27_J2ykESUHA)拆解过这两条线。

注意这个措辞：DSA 吸收了 NSA 的一部分思想（稀疏选择），但 **NSA 原版三分支没有直接进产品线**。论文是 DeepSeek-AI 实习期的作品，V3.2 落地成简化版 DSA，V4 的路子又变了。

于是问题来了：亲爹为什么不用亲儿子？

## 六、收尾反差：谁在用，为什么？

先把事实摆开：

- **NSA 论文（2025.02）**：DeepSeek-AI 出品，三分支，8.6%，反超全注意力。
- **V3.2**：MLA + DSA（简化版，索引器扫全文选出 TopK）。
- **V4**：CSA + HCA，把「先压后选」变成主结构。
- **GLM-5.3-Flash**：45 层 3:1 混合——34 层 KDA + **11 层还在 MLA/DSA 路线**。数字见[拆注意力那篇](https://mp.weixin.qq.com/s/5w1mEVLW5igvJ28Dn6pe9A)。
- **Kimi**：K3 起用 KDA 撑 1M 上下文（[KDA 那篇](https://mp.weixin.qq.com/s/_RR5LLWgjGNm-qXdSdnAGA)），也是块级稀疏的路数。

亲爹换成 CSA+HCA，不是 NSA 错了——是 V4 的目标变量变了。它要的是 **1M 上下文计算量可控**，不是「64k 省到 8.6%」。DSA 的索引器仍然要扫全序列，候选池根本没缩小。V4 要的是把「索引器扫全文」这个尾巴也砍掉。至于 NSA 原版，滑窗、压缩块长、Top-K 都要针对自家硬件重新调。这些参数在 27B 验证过，换到 V4 的规模未必还能用。这是路线取舍，不是打脸。

换个角度：其他家为什么不跟着 V4 换路？GLM 是 3:1 混合——11 层 DSA 配上 34 层 KDA，本身稀释了注意力成本。Kimi 的 KDA 是自家打磨多年的路数。每家手里牌不一样。

有时候成功的道路其实不止一条，你把它开源出来，别人经过探索，发现一条全新的路，可能是你没有想到，或者是你自己探索的路更好，都需要交给实践去检验，或许还会殊途同归，或者用更好的消融实验和理论推到把事情的本源搞清楚，都是很好的。

诚实边界三句：GLM 是 3:1 混合，不是落后。KDA 是 Kimi 自家的路数。NSA 至今没有开源生产级实现（社区 fla-org 在复现）。「DeepSeek 全线在用 NSA」这句话是错的。

![路线分叉：NSA 8.6% → DSA → CSA+HCA，GLM 还在 DSA 路线](05-road-fork.png)

## 七、回扣：白的不是噪声

回到开头那张 attention map。大片浅浅的颜色不是噪声，也不是「计算白费了」——它是一份**读书法说明书**。模型早就在告诉你：最近的内容要用余光盯着，远的内容翻目录挑重点看。稀疏不是偷懒，是把力气花在刀刃上。

8.6% 是 NSA 论文的答案。「谁在用、为什么用、不用换成了什么」才是 2026 年的问题——而答案是：**有不止一条路，每条路都有它要省的那笔账。**

下一步：有人忙着少算，也有人故意多算——让模型多想 3 秒，数学分为什么能从 40 涨到 90？推理时计算，下篇拆。

要是这篇把「8.6% 为什么行」讲透了，点个赞 👍、收藏 ⭐ 备用。关注「数解AI」，回复「开源」，我把「开源大模型技术揭秘」合集链接发你。

你会因为技术上的优越，而对模型的实际效果网开一面嘛，还是只看效果，不关心技术创新本身？

📖 本文收进「开源大模型技术揭秘」合集。前几篇见：[DeepSeek-V4为何不用MLA？](https://mp.weixin.qq.com/s/MQEgbY16mLs-N7g2xKW1HQ) · [Kimi K3：KDA怎么撑住1M上下文？](https://mp.weixin.qq.com/s/_RR5LLWgjGNm-qXdSdnAGA) · [显存被谁吃掉了？DeepSeek如何省下90%](https://mp.weixin.qq.com/s/HHMNEdCYThOjCLRozQorhg) · [KV缓存存进SSD：慢50倍的硬盘，为什么反而更快？](https://mp.weixin.qq.com/s/40BQ06eDTv4-2r8FmQ_rMA)

🔥 **热门文章**：

[KV缓存存进SSD：慢50倍的硬盘，为什么反而更快？](https://mp.weixin.qq.com/s/40BQ06eDTv4-2r8FmQ_rMA)  
[高维空间为什么全是壳？内积才是那把尺子](https://mp.weixin.qq.com/s/Nrfr-90Fpu3mFDML9s0d1Q)  
[高斯为什么二阶就够？非线性去哪了](https://mp.weixin.qq.com/s/gs_3y7JXuBLlzR5w6jW6fQ)  
[学习率怎么自动调？Adam 优化器拆给你看](https://mp.weixin.qq.com/s/aSLVO-otvr2rxIU1kr2eAA)  
[DeepSeek-V4为何不用MLA？](https://mp.weixin.qq.com/s/MQEgbY16mLs-N7g2xKW1HQ)  
[SFT微调：1万条数据就能让模型听话？](https://mp.weixin.qq.com/s/vwXGbjm9Ai1GPvQi5O3UyQ)  
[注意力机制是什么？别再当数据库查询](https://mp.weixin.qq.com/s/KrilwX6VRjI9KfjvD7C6kw)  
[为什么AI上下文越长越慢？两道数学硬墙一次讲透](https://mp.weixin.qq.com/s/PLVRS0TTHXHDve1Z3r6M7Q)  
[稀疏注意力怎么挑重点？DeepSeek-V4 只算 1/64](https://mp.weixin.qq.com/s/QcZUcxYZUw27_J2ykESUHA)  
[智谱阿里为什么拆注意力？KV缓存砍4.4倍](https://mp.weixin.qq.com/s/5w1mEVLW5igvJ28Dn6pe9A)  
[Kimi K3：KDA怎么撑住1M上下文？](https://mp.weixin.qq.com/s/_RR5LLWgjGNm-qXdSdnAGA)  
[显存被谁吃掉了？DeepSeek如何省下90%](https://mp.weixin.qq.com/s/HHMNEdCYThOjCLRozQorhg)  

**参考文献**

1. Yuan, G., Gao, B., Dai, Z., et al. (2025). Native Sparse Attention: Hardware-Aligned and Natively Trainable Sparse Attention. *arXiv:2502.11089*, ACL 2025.
2. DeepSeek-AI (2025). DeepSeek-V3.2: The Era of Sparse Attention.
3. DeepSeek-AI (2026). DeepSeek-V4: Towards Highly Efficient Million-Token Context Intelligence.
4. DeepSeek-AI (2025). DeepSeek-V3 Technical Report.

#稀疏注意力 #NSA #DeepSeek #开源大模型技术揭秘 #数解AI
