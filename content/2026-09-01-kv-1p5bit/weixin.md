---
title: "KV缓存压到1bit：省92%显存，凭什么不掉点？"
author: "数解AI"
date: "2026-09-01"
type: "原理篇"
series: "开源大模型技术揭秘"
digest: "KV缓存是模型读文档时写的便签，1M上下文时就要吃掉26GB显存。压薄它有个反直觉发现：K的误差进softmax指数被放大，V的误差是线性平均——K要精、V能糙。平均1.25bit，省92%显存，代价是少数任务掉点。"
cover: "00-cover.png"
keywords: ["KV缓存", "量化", "softmax", "AsymKV", "DeepSeek-V4", "显存"]
---

同一个 100 万 token 的大文档，模型每看一个词，都要在便签上记一笔 K 和一笔 V。DeepSeek V4 Flash 上（antirez 实测），记满 100 万，这份便签就要吃掉 **26GB** 显存——还只是便签自己，不算模型权重。在 128GB 的 Mac 上配合 81GB 的 2bit 权重，这 26GB 就是压垮骆驼的最后一根稻草。

有办法把便签（K/V 值本身）从 16bit 记薄到平均 1.25bit——12.8 倍压缩。可这看起来像毁尸灭迹：每个数只剩两三个取值，模型怎么还认得字？

## 一、便签凭什么占满显存？

先说你天天骂的那件事。

> 训练模型和跑模型，最讨厌的就是OOM,毕竟物理的显存就那么多，而且高性能的HBM显存怎一个贵字了得！

OOM 的元凶常常不是模型权重，是这份便签。

模型每读完一个词，就会算出这个词的 K（要对比哪些词）和 V（提供什么内容），存进 KV 缓存。下一词直接取用，不用重算——这是拿显存换速度。记满 100 万 token，这份便签要吃掉 **26GB** 显存。这是 antirez 实测 DeepSeek V4 Flash 的数：1M 上下文的 KV 缓存约 26GB。其中压缩索引器就占 22GB。便签随 token 数**线性**疯长：token 翻一倍，便签翻一倍。所以长文档跑完之前，最先爆的总是它。这也是为什么 2bit 权重（81GB）加 1M 上下文（26GB）的组合，128GB 的机器都要精打细算。

压便签有两条路。一是**架构级**——少记点（DeepSeek 的 CSA/HCA 走这条，前面说的 26GB 就是这条路的产物）。二是**数值级**——每个数用更少 bit 存。本篇讲第二条。

![KV 便签随 token 线性膨胀](01-kv-notes.png)

## 二、把 6.5 万色压成 4 色，模型会失忆

数值级的路子叫**量化**：把每个 16bit 的小数，四舍五入成 2bit 的整数。比喻成照片：6.5 万色降到 4 色，照片还认得出轮廓，但细节全糊了。

> 居然可以压到1bit,是不是太离谱了？1bit只有0和1,还能保存什么信息呢？前面信息熵的文章才讨论过的。

这反应太对了。[信息熵那篇](https://mp.weixin.qq.com/s/BkGWzKxiJE2mlPMlZgb7ag)说过：量的不是内容，是意外。1bit 确实离了谱——把 KV 缓存直接压到 1bit，模型立刻「失忆」。Rice 大学的 CQ 论文里摆着这个对照实验。普通方法把 KV 压到 1bit，LLaMA-7b 的困惑度从 FP16 的 **5.68** 崩到 **321~620**。越低越好，这一差就是 60~110 倍。这种状态下，模型连下一词该是什么都猜不出来了。

![量化等于把 6.5 万色降到 4 色](02-quantization.png)

但信息熵还有个后续：**信息少，不代表不能压缩**——前提是去掉的是冗余，不是信息。接下来这个发现，就是「谁压得狠、谁碰不得」的数学依据。

## 三、K 是放大器，V 是平均器

> 其实乍一看还挺反直觉的，所以还是需要看看数学上它为什么可以成立？

先看注意力在算什么：

$$A = \text{softmax}\left(\frac{QK^T}{\sqrt{d}}\right)V$$

一句话分工：**K 负责「找什么」，V 负责「取什么」**。这个分工，决定了 K 和 V 对量化误差的敏感度完全不同。

**K 的误差进指数。** K 出现在 softmax 的指数里。假设 K 的量化误差是 $\delta$，那么指数里多了一个 $\delta$：

$$e^{x+\delta} = e^x \cdot e^\delta$$

$e^\delta$ 就是误差的放大倍数——指数函数是超线性增长，误差进指数，出来就放大了。阿里通义团队在 AsymKV 论文里把这条路径证得明明白白：K 量化后的注意力输出误差项长得像

$$(A_w \odot (1 - s_r \cdot e^{E_q/\sqrt{h}})) \cdot V$$

误差 $E_q$ 待在**指数**里，被指数函数放大了。

**V 的误差是线性的。** V 在 softmax 的右边，只是被注意力权重加权求和。V 的误差传播是线性的：

$$A_w \cdot E_v$$

这是加权平均——误差有正有负，在求和里互相抵消。V 的量化误差进不了指数，也凑不成倍数。

一句话人话版：**K 是放大器（误差进去放大出来），V 是平均器（误差进去被抹平）。**

![K 进指数放大、V 线性平均](03-k-amplifier.png)

那结论就出来了：**K 要用精一点，V 可以糙一点**。AsymKV 就是这么干的——前十几层（约一半）的 K 保 2bit。其余所有层的 K 和**全部层的 V** 压到 1bit。数一数：Llama-2-7B 共 32 层，每层一对 K/V 矩阵。64 个矩阵里 48 个是 1bit——**75% 的 KV 缓存压到 1bit**。K 平均 1.5bit、V 平均 1bit，合计平均每个数约 **1.25bit**。

而且不止 K/V 之间，**层之间**也要区别对待：误差随层数累积，越深的层越糙。所以前十几层的 K 花 2bit，后面全压 1bit。

## 四、账本：省多少？值不值？

先算账：16bit → 平均 1.25bit，是 **12.8 倍**压缩，**省 92.2%** 的 KV 显存。此时 75% 的矩阵已是 1bit。长上下文时配置不同（全部 K 保 2bit、V 全 1bit）。平均 1.5bit，**10.7 倍**、**省 90.6%**。下表两种都标清楚。实测数字（Llama-2 系列，AsymKV 论文）：

![位宽账本](04-bit-width-ledger.png)

- Llama-7b：相比 KIVI-2bit 再省 **9.0GB**（常规长度）/ 6.0GB（长上下文）
- Llama-13b：省 10.4GB / 7.0GB（实测条件：批次 48/36，生成长度 4096）
- **75% 的 KV 矩阵**可以压到 1bit，多数任务保持浮点模型的 90% 以上

值不值？看任务。AsymKV 在 Llama-7b 上的对照：

| 任务 | 配置 | 浮点 FP16 | AsymKV 量化 |
|---|---|---|---|
| TruthfulQA | 常规长度（平均≈1.25bit） | 30.76 | **38.77**（反而更高） |
| CoQA | 常规长度（平均≈1.25bit） | 63.88 | 58.12 |
| TriviaQA | 长上下文（平均 1.5bit） | 87.72 | 85.27 |
| TREC | 长上下文（平均 1.5bit） | 66.0 | 65.50 |
| RepoBench-P（代码） | 长上下文（平均 1.5bit） | 59.82 | **43.35（掉 16 分）** |

![任务性能对照](05-task-compare.png)

有意思的是 TruthfulQA 不降反升——量化误差有时反而抹掉了一点噪声，起了「去噪」作用。但 RepoBench-P 这种精确代码任务，16 分说掉就掉。所以「不掉点」这句话要打个引号：**大多数任务 9 成以上保住了，少数精确任务会打折**。

另外提醒一句：这些是学术论文的实验，模型是 Llama-2 系，还没人在 DeepSeek V4 上做过同样实验。平均 1.25bit 的可行性已被验证，但「对 V4 也成立」目前只是合理推断。

## 五、跷跷板：没有既要又要

> 工程问题上，往往充满了不得已的取舍，这就是最真实的物理世界，没有那么多既要又要的奢侈，总得在跷跷板的某一头坐下来，不是吗？

这句就是全文的答案。量化不是白嫖：省下 92.2% 的 KV 显存，换的是「多数场景无损、少数场景打折」。想两头都占？没有这种好事。想要更省，就全员压到 1bit。CQ 实验证明 1bit 也能做，但代价更大：LLaMA-7b 困惑度从 5.68 到 8.09，长上下文任务明显掉。想要无损，就回到 16bit 的贵价。

而且注意取舍的方向感：**位数要花在敏感的地方**。K 敏感就保 K，V 糙就压 V；层浅敏感就保前层，层深糙就压后层。这个「把精度预算花在刀刃上」的思路，比「一律 4bit」更省。这套方法论，等下你会看到 antirez 在真实世界里也用同样的逻辑。

## 六、DeepSeek 怎么答这道题？

> 其实架构压缩，和精度压缩并不矛盾。社区还有人把deepseek压缩到2bit甚至1bit呢

对，不矛盾，而且 DeepSeek 两条腿都迈了。

**架构级**：DeepSeek V4 用 CSA（压缩稀疏注意力）+ HCA（重度压缩注意力，128:1 压缩）。1M 上下文下，KV 缓存占用降至 V3.2 的 **10%**，单 token 计算量降至 27%。这是「少记点」：大部分块只记压缩摘要。[为什么不用 MLA 那篇](https://mp.weixin.qq.com/s/MQEgbY16mLs-N7g2xKW1HQ)和[K=V 那篇](https://mp.weixin.qq.com/s/88kscO8p0kMxHmeGm2llLA)拆解过这条线。

![DeepSeek V4 CSA+HCA 架构压缩](06-csa-hca.png)

**精度级**：V4 的权重本身就是 mxFP4（4bit 浮点），配合昇腾 950 的原生 FP4 支持。

**而社区真的把 DeepSeek 压到了 2bit。** 今年 5 月，Redis 之父 antirez 开源了 ds4 推理引擎。他把 284B 参数的 DeepSeek V4 Flash 做成 81GB 的 2bit 量化版。路由专家用 IQ2_XXS 压到约 2.06bit/权重。128GB 内存的 M3 Max 上跑出 26.7 token/s，96GB 的机器也有人跑通 250k 上下文。他的量化逻辑和 AsymKV 同一个思路。「决策组件（router、注意力投影、共享专家）全保精度不量化；路由专家占参数 95%，压狠换体积」。GitHub 21.9k star，HuggingFace 累计下载 208 万次。他原话：「2 bit 量化不是开玩笑：在 coding agent 里表现良好，工具调用可靠。」

顺带一提，antirez 还干了件更狠的事：**把 KV 缓存做成磁盘一等公民**。DeepSeek 的压缩 KV + Mac 的高速 SSD，让 1M 上下文在笔记本上不再是奢望。这条「SSD 换内存」的路子，我们的老文[KV缓存存进SSD](https://mp.weixin.qq.com/s/40BQ06eDTv4-2r8FmQ_rMA)里已经讲过。

三者合起来看：**架构压缩（少记）× 精度压缩（省 bit）× 存储迁移（上 SSD）**。三条路都在回答同一个问题：怎么让显存/内存装下更多上下文。

## 七、回扣：12.8 倍压缩，凭什么不掉点

回到开头。26GB 的便签不是靠 K 精 V 糙压到 1/10——那是架构压缩（CSA/HCA 少记点）的账。本篇这步棋是**数值压缩**：每笔 K/V 从 16bit 记到平均 1.25bit，省 92.2%。靠的是「K 精 V 糙」：放大器要准，平均器可以糊；敏感的地方保精度，不敏感的地方压狠。以及更重要的一句——显存就那么多，HBM 贵得要命，**取舍不是妥协，是工程常识**。

下一步：64k 上下文，为什么只算 8.6% 的注意力？——DeepSeek 的稀疏注意力（NSA），下篇拆。

要是这篇把「平均 1.25bit 为什么行」讲透了，点个赞 👍、收藏 ⭐ 备用。关注「数解AI」，回复「开源」，我把「开源大模型技术揭秘」合集链接发你。也欢迎留言聊聊：你跑模型遇到 OOM 的时候，是哪一块内存先爆的？

📖 本文收进「开源大模型技术揭秘」合集。前几篇见：[DeepSeek-V4为何不用MLA？](https://mp.weixin.qq.com/s/MQEgbY16mLs-N7g2xKW1HQ) · [Kimi K3：KDA怎么撑住1M上下文？](https://mp.weixin.qq.com/s/_RR5LLWgjGNm-qXdSdnAGA) · [显存被谁吃掉了？DeepSeek如何省下90%](https://mp.weixin.qq.com/s/HHMNEdCYThOjCLRozQorhg) · [KV缓存存进SSD：慢50倍的硬盘，为什么反而更快？](https://mp.weixin.qq.com/s/40BQ06eDTv4-2r8FmQ_rMA)

🔥 **热门文章**：

[KV缓存存进SSD：慢50倍的硬盘，为什么反而更快？](https://mp.weixin.qq.com/s/40BQ06eDTv4-2r8FmQ_rMA)  
[高维空间为什么全是壳？内积才是那把尺子](https://mp.weixin.qq.com/s/Nrfr-90Fpu3mFDML9s0d1Q)  
[高斯为什么二阶就够？非线性去哪了](https://mp.weixin.qq.com/s/gs_3y7JXuBLlzR5w6jW6fQ)  
[学习率怎么自动调？Adam 优化器拆给你看](https://mp.weixin.qq.com/s/aSLVO-otvr2rxIU1kr2eAA)  
[DeepSeek-V4为何不用MLA？](https://mp.weixin.qq.com/s/MQEgbY16mLs-N7g2xKW1HQ)  
[SFT微调：1万条数据就能让模型听话？](https://mp.weixin.qq.com/s/vwXGbjm9Ai1GPvQi5O3UyQ)  
[信息熵：压缩1000倍，为什么信息反而少？](https://mp.weixin.qq.com/s/BkGWzKxiJE2mlPMlZgb7ag)  
[K=V：一份KV缓存怎么干两份活？](https://mp.weixin.qq.com/s/88kscO8p0kMxHmeGm2llLA)  
[Kimi K3：KDA怎么撑住1M上下文？](https://mp.weixin.qq.com/s/_RR5LLWgjGNm-qXdSdnAGA)  
[显存被谁吃掉了？DeepSeek如何省下90%](https://mp.weixin.qq.com/s/HHMNEdCYThOjCLRozQorhg)  

**参考文献**

1. Tao, Q., Yu, W., & Zhou, J. (2025). AsymKV: Enabling 1-Bit Quantization of KV Cache with Layer-Wise Asymmetric Quantization Configurations. *COLING 2025*.
2. Zhang, T., Yi, J., Xu, Z., & Shrivastava, A. (2024). KV Cache is 1 Bit Per Channel: Efficient Large Language Model Inference with Coupled Quantization. *NeurIPS 2024*.
3. DeepSeek-AI (2026). DeepSeek-V4: Towards Highly Efficient Million-Token Context Intelligence.
4. Sanfilippo, S. (2026). DwarfStar 4 (ds4) & DeepSeek-V4-Flash GGUF. GitHub / HuggingFace.
5. Hooper, C., et al. (2024). KVQuant: Towards 10 Million Context Length LLM Inference with KV Cache Quantization.

#KV缓存 #量化 #softmax #DeepSeek #数解AI
