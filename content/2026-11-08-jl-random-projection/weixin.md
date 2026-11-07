---
title: "向量检索为什么敢随机降维？1536 维砍到 128，精度几乎不掉"
author: "数解AI"
date: 2026-11-08
type: 原理篇
series: "数学直觉"
digest: "embedding 拿到手第一件事是砍维度：1536 维砍到 128，精度几乎不掉。凭什么？JL 引理、随机投影为什么打赢精心设计的 PCA，以及 DeepSeek MLA 的 512 维。"
cover: "00-cover.png"
keywords: "向量检索, 降维, JL 引理, 随机投影, embedding"
---

搭过 RAG 的人都大约知道一个潜规则：embedding 模型吐出来的向量，第一件事不是建索引，是砍维度。

1536 维全精度存着，没几篇文档就能到600MB 以上；如果砍到 128 维，50MB 搞定。

诡异的是：精度几乎不掉。

当我第一次搭建一个一百多人的团队使用的向量知识库的时候，一点点存量文档放进去，就发现几百MB的postgresql数据库存储空间没有了。

我仔细一估算，如果把全部文档放进去，按照默认的1536维设置，我的整个SSD剩余的几十个GB的空间可能都不够了。

![1536 维全精度与 128 维的存储账对比](01-storage-account.png)

凭什么敢这么砍？这个问题背后，站着一个 40 年前的定理。

## 一、随机拍扁，距离为什么还在

### 一把随机矩阵就够了

1984 年，Johnson 和 Lindenstrauss 证明了一件反直觉的事：

把高维空间里的点，用一把随机生成的矩阵拍扁到低维，任意两点之间的距离，几乎不变。

不用挑方向、不用看数据、不用训练，随机就行。

![随机投影直觉：高维点云被一把随机矩阵拍扁，两点距离还在](02-random-projection.png)

### 偏离概率是指数衰减的

单对点的偏离概率有精确的界。投影到 $k$ 维后：

$$\Pr\left[\left|\frac{\|Pu-Pv\|^2}{k} - \|u-v\|^2\right| \gt \varepsilon\|u-v\|^2\right] \leq 2\exp\left(-k\left(\frac{\varepsilon^2}{2}-\frac{\varepsilon^3}{3}\right)\right)$$

公式说的是：投影后距离的平方，相对原距离偏离超过 $\varepsilon$ 的概率，随维度 $k$ 指数衰减。$k$ 越大，偏得越多的可能性被按在地上。

为什么随机就够？因为投影后每个坐标，都是大量独立小随机量的平均，而平均会往一个值收敛——大数定律的老地盘。

![偏离概率随投影维度指数衰减（公式右端的指数尾巴）](03-jl-bound.png)

我会类比成是平均值的集中现象。

高维空间还有一层加持：向量能量本来就集中在薄壳上（[高维空间为什么全是壳？内积才是那把尺子](https://mp.weixin.qq.com/s/Nrfr-90Fpu3mFDML9s0d1Q)），随机拍扁丢的本来就不多。

## 二、公式里没有 D

### 先把全部点对管起来

上一节的概率界只约束一对点的概率，而更大的问题，是对整体的所有数据点，看如何约束任意两点的距离都还能同时保得住。

记第 $i$、$j$ 两点的距离被破坏的事件为 $A_{ij}$。那么全部点对同时成立的概率，可以用并集计算上界，利用概率测度的次可加性不等式展开：

$$\Pr\left[\bigcup_{i\lt j}A_{ij}\right] \le \sum_{i\lt j}\Pr[A_{ij}]$$

并集界就是说：合并事件发生的概率，不超过各自概率的直接相加。它不需要处理事件之间是否独立，就是永远成立。

$N$个点两两配对，点对的个数是组合数，上限很好算：

$$\binom{N}{2}=\frac{N(N-1)}{2}\le\frac{N^2}{2}$$

### 把逐项代进去

每对点单独坏的概率，不超过第一节那个指数界 $2e^{-kc}$。其中 $c=\tfrac{\varepsilon^2}{2}-\tfrac{\varepsilon^3}{3}$，只跟 $\varepsilon$ 有关。

想让总体搞砸概率压在 $\delta$ 以内：

$$\frac{N^2}{2}\cdot 2e^{-kc}\le\delta$$

解出 $k$：

$$k\ge\frac{2\ln N-\ln\delta}{\frac{\varepsilon^2}{2}-\frac{\varepsilon^3}{3}}$$

分子里那个 2，来自点对数是 $N^2$：$\ln N^2=2\ln N$。管完全部点对，$k$ 只翻一倍。

这就是并集界的全部代价：坏事件按 $N^2$ 多项式增加，失败概率按 $e^{-kc}$ 指数衰减——指数吃多项式，所以随机够用。

小 $\varepsilon$ 时分母约等于 $\varepsilon^2/2$，按照算法量级记作：

$$k = O(\varepsilon^{-2} \ln N)$$

注意这个公式里已经没有 $D$。

所以，原始向量是1万维还是100亿维，投影目标维度一个样。压缩比的上限，被点的个数锁死，不被维度锁死。

![目标维度只随点的个数对数增长，与原始维度无关](04-k-vs-n.png)

接下来计算一个诚实的账。假设有10 万个点，容忍 10% 的距离误差，对应的：

$k \approx 2\ln(10^5)/(0.005-0.0003) \approx 4900$，约 5000 维。

这是最松的 $\delta=1$ 口径。要求总体失败概率不超过 1%，分子再加 $\ln100\approx4.6$，约 5900 维——同一量级。

容忍度放松到30%，就只要约 640 维。

其实仔细一思考，的确这个东西更多和点的个数关系更大，而维度只是一个表示层面的事情。

## 三、随机 ≥ 精心设计

说到降维，教科书第一反应都是给你看PCA：保留方差最大的若干个方向（按照奇异值排序），求解线性最优。

但 PCA 有个前提：数据真的存在低秩结构，而且你得先看数据、算协方差、分解矩阵。
JL 不挑数据。任意点集、最坏情况也成立，一把随机矩阵投影下去就完事了。

人类的朴素直觉，对随机性的理解其实是一直以来都错的离谱。高维数据的结构和随机性，其实比朴素直觉的想象要规整的多。这就是所谓的维度的祝福了。

规整到「随机投影变换」都不会有什么刚性结构上的大损失，这才是随机投影敢叫板一切精心设计的底气。

## 四、学出来的投影，又赢过随机

但是先别把随机投影给捧上天去了。随机是下限，却不代表最优。

DeepSeek 的 MLA 走了另一条路：投影矩阵不随机，端到端学出来。
每个 token 的 K/V 压成一个 512 维隐向量，再加 64 维位置旁路，缓存里只存 576 个数。
同样位置全量要存 $2\times128\times128=32768$ 个数，约 1/57（[显存被谁吃掉了？DeepSeek如何省下90%](https://mp.weixin.qq.com/s/HHMNEdCYThOjCLRozQorhg)）。

对照一下：随机 JL 在 10% 误差下要约 5000 维，学习投影 512 维就够，还顺带做了任务相关的特征选择。随机加上量化，看起来很笨的方法，其实在工程上有巨大的应用空间。学习出来的东西会吃掉很多随机的东西。

![三条路线对照：随机 JL 约 5000 维、PCA 看数据、MLA 学习投影 576 个标量](05-three-way.png)

## 五、向量库里干活的「随机」

工程界早就把 JL 用成了日常耐用品，甚至于是在你没有留意到的角落里，散落的到处都是。

RaBitQ（SIGMOD 2024）的做法甚至将这个思维推导了一个极致。先把向量归一化到单位球，乘一个 Haar 随机正交矩阵，再取符号压成 1 bit。每个向量只剩一个 D 位串。

论文原话，这个随机旋转是一种 JLT（Johnson-Lindenstrauss Transformation）。距离估计无偏、带误差界，单条查询比 PQ 快约 3 倍——而 PQ 完全没有理论保证。

今年 3 月出圈的那个 TurboQuant（Google 2025）。一篇论文直接把全球存储股市值砸掉 900 多亿美元。它用的是同一个套路。随机旋转打散能量，Lloyd-Max 标量量化，再用 1 bit QJL 修正残差偏差。

同一招还跨到了模型侧。QuIP#、QuaRot 用随机 Hadamard 旋转削平 LLM 权重的离群值，4 bit 量化才得以成立。

![RaBitQ 流水线：归一化、随机旋转、取符号、popcount 估距离](06-rabitq-pipeline.png)

很多工程上的奇思妙想，其实都有一个深刻的数学底层逻辑在那里支撑。数学之美，往往隐藏在那些看似复杂的工程应用公式的背后。

从[词嵌入](https://mp.weixin.qq.com/s/rDryn1z_hLt7mwi3X8fsxQ)到向量库再到权重量化，同一条数学原理被到处应用，四处开花。

## 六、128 维不是万能截断

泼一盆冷水：1536 砍到 128 不掉点，不是单独靠 JL 就可以的。严谨的来说，要向上达到更高的天花板，需要不少工程上的努力，具体来说就是靠 Matryoshka 训练。

text-embedding-3 有 dimensions 参数。Qwen3-Embedding 原生 1024 维，支持截到 32。这都是学出来的截断友好的结构。

Azure 官方文档明确警告：配二进制量化时，低于 1000 维其实搜索的质量还是会下降的。OpenAI 也要求截断后在自己的数据上实测。

![Matryoshka 截断：1024 维原生向量截到更短仍可用，但精度随截断递减](07-matryoshka-layers.png)

其实理论和实践之间，往往还是隔着一道深沟。实际应用上，还是要看测试，根据自己的实际数据和场景来判定多少维度会是一个更好的平衡。

所以「高维随机好用」的完整答案从工程上来看，需要分三层：随机给下界，旋转给工程可行性依据，学习训练给现实优化求解路径。

## 那笔账，现在每一层都可以计算了

回到开头的存储账。600MB 砍到 50MB，现在每一层都敢这么算：

JL 保证随机变换不会损失距离。RaBitQ 把随机旋转变成 1 bit 的字节账，Matryoshka 让 128 维真的能用。

下次你的 embedding 模型再吐出 1536 维，别急着全量入库。先问自己一句：这个数，是非要不可，还是默认值无脑拿来用的？也许你还在用推荐的512维度？先测试一下你的查询质量看是否你的选择是最适合你的场景的。

做RAG的时候，你是否被选择多少维度困惑过？最后是怎样平衡准确度和存储占用之间的矛盾？

如果读到这里，欢迎点赞 👍、收藏 ⭐ 备用，转发给还在被向量库存储账单折磨的朋友。关注「数解AI」，AI 原理和工程，和你一起慢慢深入拆解。

🔥 **热门文章**：

[KV缓存存进SSD：慢50倍的硬盘，为什么反而更快？](https://mp.weixin.qq.com/s/40BQ06eDTv4-2r8FmQ_rMA)  
[高维空间为什么全是壳？内积才是那把尺子](https://mp.weixin.qq.com/s/Nrfr-90Fpu3mFDML9s0d1Q)  
[高斯为什么二阶就够？非线性去哪了](https://mp.weixin.qq.com/s/gs_3y7JXuBLlzR5w6jW6fQ)  
[微软用 Go 重写 TypeScript，他一个人用 C++ 又写了一遍](https://mp.weixin.qq.com/s/GmPJAh8ERPkm64KzYirV2g)  
[学习率怎么自动调？Adam 优化器拆给你看](https://mp.weixin.qq.com/s/aSLVO-otvr2rxIU1kr2eAA)  
[DeepSeek-V4为何不用MLA？](https://mp.weixin.qq.com/s/MQEgbY16mLs-N7g2xKW1HQ)  
[显存被谁吃掉了？DeepSeek如何省下90%](https://mp.weixin.qq.com/s/HHMNEdCYThOjCLRozQorhg)  
[词嵌入为什么让AI懂](https://mp.weixin.qq.com/s/rDryn1z_hLt7mwi3X8fsxQ)  
[曾困扰人类358年的费马大定理终被AI证明](https://mp.weixin.qq.com/s/SJWle4e-JtCw5qO_A6eQ-g)  

**参考资料与数字溯源**

1. W. Johnson & J. Lindenstrauss（1984）. Extensions of Lipschitz mappings into a Hilbert space. Contemporary Mathematics：JL 引理原始论文
2. D. Achlioptas（2003）. Database-friendly random projections: Johnson-Lindenstrauss with binary coins. JCSS：±1 随机矩阵与 $2\exp(-k(\varepsilon^2/2-\varepsilon^3/3))$ 形式
3. Gao & Long（2024）. RaBitQ: Quantizing High-Dimensional Vectors with a Theoretical Error Bound for Approximate Nearest Neighbor Search. SIGMOD 2024（arXiv:2405.12497）：随机旋转即 JLT（论文原话）、1-bit、无偏估计、比 PQ 快约 3×；RaBitQ+（VLDB 2025，arXiv:2409.12353）
4. Zandieh 等（2025）. TurboQuant（arXiv:2504.19874）：随机旋转 + Lloyd-Max + 1-bit QJL 残差偏差修正；2026-03-24 Google Research 发布，存储芯片股单日全球市值蒸发超 900 亿美元（每日经济新闻/钛媒体/新浪财经，2026-03-25/26）
5. Tseng 等（2024）. QuIP#: Even Better LLM Quantization with Hadamard Incoherence and Lattice Codebooks（arXiv:2402.04396）；Ashkboos 等（2024）. QuaRot: Outlier-Free 4-Bit Inference in Rotated LLMs（arXiv:2404.00456）
6. OpenAI embeddings 指南（2024 起，2026-11 核对）：text-embedding-3-small 1536 维、dimensions 参数截断需实测
7. Azure AI Search 文档（2026-11 核对）：MRL 截断 + 二进制量化低于 1000 维掉质量的官方警告
8. Qwen3-Embedding（2025）：0.6B 原生 1024 维、MRL 支持 32–1024 截断
9. DeepSeek-V2 论文（arXiv:2405.04434）与 V3 公开配置：kv_lora_rank=512、qk_rope_head_dim=64，576 vs 32768 标量

#向量检索 #降维 #JL引理 #embedding #数解AI
