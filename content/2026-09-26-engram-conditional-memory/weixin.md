---
title: "DeepSeek 把 196B 参数做成字典，为什么反而更聪明？"
author: "数解AI"
date: "2026-09-26"
type: "原理"
series: "开源大模型技术揭秘"
digest: "DeepSeek 新旗舰挂着 196B 参数的 Engram 条件记忆：不进主干计算，只查哈希表。MoE 按需计算，Engram 按需记忆——字典怎么查、为什么放主机内存、关掉它分数掉多少，一篇算清楚。"
cover: "00-cover.png"
keywords: ["Engram", "DeepSeek", "条件记忆", "KV缓存", "稀疏化"]
scheduledPublish: "2026-09-26T20:00:00+08:00"
wechatUrl: "https://mp.weixin.qq.com/s/ZgHoN4v2SxiIC0_I7k40Lg"
---

把 196B 参数挂进一个模型，却不让它参与主干网络的计算。DeepSeek-V4.1-Flash 在 2026 年 9 月真的这么干了。

这 196B 参数组成的模块叫 Engram，官方名称是「条件记忆」。它不算数，只负责一件事：查表。

DeepSeek这篇论文在年初刚挂出来的时候，我当时第一反应就是，这莫非又是一个玩具项目？真的能得到大规模实验所验证吗？毕竟这个太拟人化的设定很多时候并不是工作的很好，比如大名鼎鼎的何恺明在MIT小组做的很多类似项目都是雷声大而雨点小。等到2026年4月底的DeepSeek大版本发布（当时叫预览版），翻阅了论文和技术报告，果然没有发现Engram的身影。不过我的内心里总是有一点隐隐约约的小期待，因为DeepSeek的风格向来是不会有意做那些无意义的噱头，既然是创始人亲自署名的文章，内部八成是做了不少实验觉得不会砸了招牌才会放出，创新这方面，我们从来都可以相信DeepSeek.

这句小期待没有落空。2026 年 1 月论文刚挂出时它还像个尝试，到了 9 月，Engram 以 196B 的规模进了 DeepSeek 的旗舰架构。记忆和网络从此分工：查表的管背，算数的管想。

先立一个框架。DeepSeek 自家的 MoE 把「算」做成了按需，每个 token 只激活一小部分专家（[384 个专家怎么选，那篇拆过](https://mp.weixin.qq.com/s/z6dUKGtDjcPQOK9GnxBnFA)）。Engram 把「背」也做成了按需：每个 token 只查字典里被命中的那几行。

MoE 是条件计算，Engram 是条件记忆。这是大模型稀疏化的第二条轴。

## 二、字典怎么查：8 把哈希钥匙

这本字典的编法毫不神秘。把相邻 2、3、4 个 token 的组合（n-gram），用 8 个不同的哈希函数各查一遍，每个头索引约 1,600 万条目，表长取不同质数来减少碰撞。整张表用 FP8 存储（[残缺数字怎么练出顶级模型](https://mp.weixin.qq.com/s/yxrkmxPSZ8CnsFhWZ1bCPA) 讲过 FP8 为什么够用）。

V4.1-Flash 把这 196B 拆成两个模块，挂在网络的第 1 层和第 14 层——连挂哪儿都是按训练时的内存平衡挑的。

查到的向量怎么用？乘一个「门控」权重融回主干，门控由上下文决定。也就是说，翻不翻字典、翻完信几分，是网络自己学的。

![Engram 的结构：检索静态 n-gram 记忆，经上下文感知门控与主干状态融合（图源：arXiv:2601.07372 Figure 1）](01-engram-arch.png)

这套设计还有个副产品：查询只依赖输入 token 序列，和计算状态无关。查哪几行提前就知道，表可以预取。

所谓大道至简，说的就是这样吧。几十年前数据库设计那些进入教科书的标准操作，换一个领域继续发光发热，不正说明了一些长期主义的东西，其实变化并不是那么频繁吗？这才是我辈普通人应该学习和追求的本质的东西，因为说不定哪天它就改头换面出现了，只追逐表层东西的人只会徒然呼唤变化太快，但是你看根子上的东西基本没太多变化。

## 三、字典挂在最便宜的内存上

推理时，这张大表不驻留 GPU，而是整张放在主机内存里。GPU 通过 RDMA 在后台预取要查的行，与计算重叠——因为查哪行提前已知，预取永远跑在需求前面。

![Engram 的系统实现：训练时表在 GPU 间分片（All-to-All 取活跃行），推理时卸载到主机内存异步预取（图源：arXiv:2601.07372 Figure 2）](02-engram-system.png)

这笔账的参照物是 KV 缓存：同样 1M 上下文，各家旗舰的 KV 要 0.93 到 13.7 GB（[四家架构那本账](https://mp.weixin.qq.com/s/7BdQlueJrRJ5f-x3v_2VqA) 刚算过）。Engram 一字节 KV 都不占——表待在便宜的内存里，显存一分不掏。

有人会问：一本「查出来」的字典，参数是死的吗？恰恰相反，Engram 全程参与训练，端到端更新梯度。它省的是优化器：动量更新加 Sinkhorn 平衡替代 Adam，砍掉优化器状态的内存开销。

其实这种做法反映了计算机科学里面最重要的一个原则之一：tradeoff,中文翻译叫做权衡或者交换。既然GPU上面的高速显存很贵，那么就把内容给交换到稍微便宜一些的内存上来，迂回解决问题就好了。这是工程设计方面的取舍，并没有什么特别高深的大道理。可惜的是现在内存也随着大涨价了，不过这些都是后话。

## 四、关掉字典，事实题崩到三成

查表真能查来聪明？原始论文把 Engram 做到 27B，对标参数相同、算力相同的 MoE 模型：MMLU 高 3.4 分，BBH 高 5.0 分，多查询大海捞针从 84.2 拉到 97.0。

更有说服力的是反向实验。推理时把字典的输出关掉，事实知识类基准只剩 29–44%，阅读理解却保留 81–93%——背事实靠字典，讲道理靠主干，分工是实测出来的。

![推理时抑制 Engram 输出：事实知识类基准大幅掉分，阅读理解类基本保留（图源：arXiv:2601.07372 Figure 6）](03-engram-ablation.png)

落地这一步已经发生：DeepSeek 把 196B 挂进了 V4.1-Flash（[四十层那条线](https://mp.weixin.qq.com/s/DBI990JLYtbxQGF3LIWbhQ) 之前拆过），编程评测反超自家 Pro。阿里也跟进了同一条路线，Qwen3.8-Next 在加速器之外挂了 51B 的 n-gram 表，同样从主机内存预取。

![V4.1-Flash 总架构：Engram 作为条件记忆组件，与 CED 主干、稀疏索引器并列（图源：arXiv:2609.19969 Figure 3）](04-v41-flash-arch.png)

当我第一眼看到这些数字，还是被它那良好的效果震撼到了，原来真的可以落地实验得到和预期差别不大的良好效果。当然证明好用了，大家就要跟进来为我所用，创新和共同进步，本来就是开源社区所期望的。当然闭源模型悄悄跟进吸收了也不好说，毕竟上次deepseek刚刚发布了DSpark加速技术，OpenAI就宣称他们找到了能把推理成本降低很多的新方法，到底是怎么情况，人家捂着不说，社区的猜测就很有倾向性了，我这里就不搬运了，感兴趣的可以自己查查相关的吐槽报道看，挺有趣的。

## 五、泼冷水：字典不是越大越好

Qwen 的数据里藏着一条边界：n-gram 词表加大，loss 单调下降，下游精度却饱和了。字典再厚，分数不再涨。

原始论文的缩放实验给出同样的形状：固定算力，在「计算」和「记忆」之间分配参数，验证损失随配比呈 U 形。字典太小背不动，太大挤占算力，中间存在一个最优配比。

![稀疏度分配实验：验证损失对「计算↔记忆」配比呈 U 形；无限内存下损失随嵌入数量对数线性下降（图源：arXiv:2601.07372 Figure 3）](05-engram-scaling.png)

这样的结果很多时候，我觉得从本质上非常贴合中国人的中庸之道，过犹不及。当然从治学角度看，追求中庸之道容易导致不求甚解，我的看法纯粹是从事物最本质的表现上看这样，不代表我建议对事情差不多就可以。反而这些结论是在努力穷尽本质+实验验证之后，得到的暂时的阶段性结论。尤其是目前的唉，AI领域还是充斥了大量这种工程方面的妥协之道。

## 六、所以，为什么反而更聪明

回到标题的问题。铁律说「参数都要算」，错在把「背」也当成了计算：背题搬进字典，主干省下的容量全部花在推理上。

聪明从来不是背出来的，是把背的东西挪走之后剩下来的那部分。

MoE 之后，「多大算力配多大记忆」正在成为架构设计的第二个旋钮。

一句话收尾：**196B 参数不算数，事实题反而对得更多——省下的算力，全花在了刀刃上**。

---

📖 本文收进「开源大模型技术揭秘」合集。前几篇见：[同样 1M 上下文，KV 缓存差 15 倍：四家架构差在哪一层](https://mp.weixin.qq.com/s/7BdQlueJrRJ5f-x3v_2VqA) · [DeepSeek-V4为何不用MLA？](https://mp.weixin.qq.com/s/MQEgbY16mLs-N7g2xKW1HQ) · [KV缓存存进SSD：慢50倍的硬盘，为什么反而更快？](https://mp.weixin.qq.com/s/40BQ06eDTv4-2r8FmQ_rMA)

**参考资料**

1. Cheng, X. et al. (2026-01). [Conditional Memory via Scalable Lookup: A New Axis of Sparsity for Large Language Models](https://arxiv.org/abs/2601.07372). 27B Engram、等参等 FLOPs 对比 MoE，[官方开源](https://github.com/deepseek-ai/Engram)。
2. DeepSeek-AI (2026-09). [DeepSeek-V4.1-Flash: Pushing the Limits of KV Cache Compression](https://arxiv.org/abs/2609.19969) 与 [HF 模型卡](https://huggingface.co/deepseek-ai/DeepSeek-V4.1-Flash). 763B 总参、552B 主干、Engram 196B 挂第 1/14 层。
3. Qwen Team (2026-08). [On the Design of Qwen3.8-Next Architecture](https://arxiv.org/abs/2608.30320). 125B-A6B，+51B n-gram 表放加速器之外。

🔥 **热门文章**：

[KV缓存存进SSD：慢50倍的硬盘，为什么反而更快？](https://mp.weixin.qq.com/s/40BQ06eDTv4-2r8FmQ_rMA)  
[高维空间为什么全是壳？内积才是那把尺子](https://mp.weixin.qq.com/s/Nrfr-90Fpu3mFDML9s0d1Q)  
[高斯为什么二阶就够？非线性去哪了](https://mp.weixin.qq.com/s/gs_3y7JXuBLlzR5w6jW6fQ)  
[学习率怎么自动调？Adam 优化器拆给你看](https://mp.weixin.qq.com/s/aSLVO-otvr2rxIU1kr2eAA)  
[DeepSeek-V4为何不用MLA？](https://mp.weixin.qq.com/s/MQEgbY16mLs-N7g2xKW1HQ)  
[随机变量为什么不是变量？它其实是个函数](https://mp.weixin.qq.com/s/5BxjOUblW64DXNffHc2sxQ)  
[DeepSeek 有 384 个专家，为什么不敢强迫它们平均干活？](https://mp.weixin.qq.com/s/z6dUKGtDjcPQOK9GnxBnFA)  
[FP8训练：残缺数字怎么练出顶级模型](https://mp.weixin.qq.com/s/yxrkmxPSZ8CnsFhWZ1bCPA)  
[同样 1M 上下文，KV 缓存差 15 倍：四家架构差在哪一层](https://mp.weixin.qq.com/s/7BdQlueJrRJ5f-x3v_2VqA)  
[DeepSeek V4.1 四十层网络，为什么不给每层都记账？](https://mp.weixin.qq.com/s/DBI990JLYtbxQGF3LIWbhQ)  

💬 **留言互动**

你觉得这张「字典」还有多大的扩展空间？除了背事实，还有哪类现在靠算力的能力，也值得改成查表？

觉得有用就 **点个赞 👍、收藏 ⭐**；关注「数解AI」，大模型架构的最新拆解第一时间推给你。

---

#开源大模型 #DeepSeek #Engram #KV缓存 #数解AI
