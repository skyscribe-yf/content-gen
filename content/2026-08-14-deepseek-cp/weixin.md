---
title: "上下文并行：1M序列为什么切了会坏？"
author: "数解AI"
date: "2026-08-14"
type: "解密篇"
series: "DeepSeek 技术解密"
digest: "上下文并行（CP）是为 1M 长上下文而生的：序列太长，切成 8 段分给 8 张 GPU——听起来像切蛋糕。但 DeepSeek-V4 的答案是：一切就坏。压缩注意力把 KV 按块压缩，压缩块可能横跨两张卡的边界，切完再压，每张卡产出的压缩 KV 还长短不一。V4 用两阶段通信解决：先交换边界原料补齐跨边界块，再 all-gather 压缩 KV、用 select-and-pad 重组。本篇用一个小模拟器，把『为什么切了会坏』和『两阶段怎么修好』跑给你看。"
cover: "00-cover.png"
wechatUrl: "https://mp.weixin.qq.com/s/UB_ILj-62K3VBUY4_AopSw"
keywords: ["上下文并行", "CP", "长上下文", "压缩注意力", "CSA", "HCA", "DeepSeek-V4", "大模型训练"]
---

上篇拆解五维并行时，CP（上下文并行）只给了个开头：把 1M token 的序列切成 8 段，每张卡管一段，各算各的注意力。听起来像切蛋糕——蛋糕切 8 块，每人一块，有什么难的？

V4 技术报告的回答是：**一切就坏**。今天把「为什么坏」和「怎么修」拆解，再用一个小模拟器跑给你看。

## 一、为什么必须切：1.3TB 的显存账

先回到动机。1M token 的序列，注意力这一步要存多少东西？

只看 Q：1M 个 token，每个 token 的 Q 是 7168 维，FP8 每个数占 1 字节（V4 已不用 BF16，见 [FP8训练那篇](https://mp.weixin.qq.com/s/yxrkmxPSZ8CnsFhWZ1bCPA)）：

$$Q = 10^6 \times 7168 \times 1 \approx 7.2 \text{ GB}$$

单层注意力要把 Q、KV、输出都留在显存里。注意 V4 的 K/V 已经合并成一份（shared KV MQA，见 [K=V那篇](https://mp.weixin.qq.com/s/88kscO8p0kMxHmeGm2llLA)），所以是 3 份张量而不是 4 份，加起来约 **21.5GB**。V4 有 61 层，激活总量：

$$21.5 \times 61 \approx 1.3 \text{ TB}$$

一块 H800 只有 80GB。**1.3TB 对 80GB，差了约 16 倍。**

你可能会问：Flash Attention 不是解决了注意力矩阵占显存的问题吗？对，它把 T×T 的分数矩阵压成了 O(T)——但 Q、KV、输出这些张量本身就是 O(T)，1.3TB 一分没少。

CP 就是为这个而生的：切成 8 段后，每张卡只持有 125K token。所有线性于序列长度的张量都同比缩小 8 倍，Q 从 7.2GB 降到 0.9GB。

所以 CP 不是优化，是**必须**。1M 上下文训练，没有 CP 根本跑不起来。

![显存账：1M 序列的激活为什么装不下](01-memory-ledger.png)

## 二、普通 CP 怎么切：两个隐含假设

传统的 CP 思路非常朴素：序列沿长度切段，每张卡持有一段连续 token，各算各的注意力，需要全局信息时再通信。

它成立，依赖两个隐含假设：

1. **本地 token 数和本地 KV 数大致一一对应**。我有 125K 个 token，就大约产生 125K 份 KV，形状整齐，all-gather 也好对齐；
2. **边界好处理**——某个操作只依赖段内数据，跨段的边界补一补就行。

对普通注意力，这两个假设都成立。所以长上下文社区早期有个方案叫 Ring-Attention：把 K/V 块像击鼓传花一样轮流传着算。来一块算一块，用流水线把通信藏在计算后面。

但 V4 的压缩注意力（CSA/HCA，见 [DeepSeek-V4为何不用MLA？](https://mp.weixin.qq.com/s/MQEgbY16mLs-N7g2xKW1HQ)）把这两个假设**同时打破**了。

## 三、为什么 V4 一切就坏：两个坏因

压缩注意力把 KV 按块压缩：每 m 个连续 KV entry 压成 1 个。V4-Pro 的配置（config.json 的 compress_ratios 字段）是：CSA 层 m=4、HCA 层 m'=128。两种层在 61 层里交错排列。

一切，就出两个问题。

**坏因 1：压缩后 KV 长度不齐。**

训练样本是多个序列打包（packed）在一起的，每个序列**按自己的边界独立压缩**，尾部不足 m 个的 token 直接丢弃。

想象两条序列打包：第一条 1000 个 token，第二条 7 个 token。第二条压缩时，7 个凑不出 2 个完整块（m=4），尾部 3 个被丢弃，只产生 1 个压缩 KV。

问题在于：**每个 rank 分到的序列边界位置不一样**。有的 rank 运气好，段内全是完整块；有的 rank 段尾正好是残块。结果每张卡实际产出的压缩 KV 数，都小于理论值 s/m，而且彼此不等。

普通 CP 最爱「每个 rank 产出同样形状的张量，再整齐地 all-gather」——现在形状不齐了，第一步就卡住。

**坏因 2：压缩窗口跨 rank 边界。**

压缩要 m 个**连续**的 KV entry。如果恰好有 m 个 token 组成的块，横跨两个相邻 rank 的分界线呢？

左边 rank 只有前半块，右边 rank 只有后半块——**任何一边单独都无法完成压缩**。半块没有合法输出，因为压缩函数的定义域是完整的一组。

打个比方：照片 4 张一组放进相册。你把相册切给两个人，边界正好切在两张照片中间。谁都没拿到完整的一组，这组照片就丢了。

![两个坏因：压缩后长度不齐 + 压缩窗口跨边界](02-two-breakages.png)

所以 V4 的 CP 不能照搬普通 CP。它必须重新设计——这就是报告 §3.5.3 的两阶段通信。

## 四、阶段 1：先交换边界原料

第一个要解决的问题：跨边界的压缩块怎么办？

V4 的做法很直接：**每个 rank 把自己末尾最后 m 个未压缩 KV 发给右邻居**（rank r → rank r+1）。右邻居拿这些原料，和自己本地开头的 KV 拼起来，在本地把原本跨边界的块压缩出来。

注意传的是**原料**，不是压缩结果。为什么？

因为跨边界块在左边 rank 手里根本不是一个完整块——它没有足够信息生成正确的压缩输出。如果硬要左边先压个「半成品」传过去，就引入了一种不存在的中间表示：后面还得拼接、校正、再压一次，纯属自找麻烦。最干净的办法是一句话：

$$\text{发原料} \rightarrow \text{右邻居拼成完整块} \rightarrow \text{压一次}$$

这里有个 ownership 约定：横跨 rank r 和 rank r+1 的压缩块，**由右侧 rank 负责产出**。

这一步的关键性质是：**通信量与序列长度 T 无关**。不管序列是 100K 还是 1M，每个 rank 都只发最后 m 个 KV。m 是压缩比（CSA 层 4、HCA 层 128），不是序列长度。算下来：

| 层类型 | 阶段 1 通信量（每 rank 每层） |
|---|---|
| CSA 层（m=4） | 4 × 576B ≈ 2.3 KB |
| HCA 层（m'=128） | 128 × 576B ≈ 74 KB |

（KV entry 576 字节 = 64 维 RoPE BF16 + 448 维 FP8，同 parallel 篇口径。）

KB 级，几乎可以忽略。反向传播时梯度原路返回（右 rank 把边界块的梯度传回左 rank），对称，不展开。

![阶段 1：边界原料交换，右邻居补齐跨边界块](03-stage1-boundary.png)

## 五、阶段 2：all-gather + select-and-pad

边界块补齐了，第二个问题还在：**每张卡产出的压缩 KV 长度依然不齐**。

原因有两层：packed 序列的边界位置各卡不同；承接了跨边界块的右 rank 还多一两个 entry。

all-gather 要求形状整齐。V4 的办法是：**每张卡先把产出 pad 到统一上界，再 all-gather**。gather 之后每个 rank 拿到的是一块形状整齐的 blob：

$$\text{shape} = \text{cp_size} \times \text{padded_len} \times d_{KV}$$

但这块 blob 里**有洞**——padding 不对应任何真实压缩块。如果直接喂给注意力，padding 行会污染注意力分数。

all-gather 解决的是**通信接口的形状对齐**，不是**语义正确**。所以还需要最后一步：**select-and-pad**。

这个算子做三件事，合并成一个 kernel：

1. **去 padding**：按每卡的 valid_count 过滤，跳过 padding entry；
2. **尾对齐**：把所有 padding 集中移到尾端，后续 kernel 可以按定长切前缀；
3. **稀疏重排**（仅 CSA sparse 路径）。按 top-k 选出的全局索引，把选中的 entry 重排成稀疏 kernel 期望的紧凑布局。

为什么要 fused 成一个 kernel？因为分三步做，gathered blob 要被反复读写三次。1M 上下文下这块 blob 体积很大，合并后数据只过一次内存总线。

举个最小的例子（cp_size=2，m=4）：

```text
Rank 0 sends: [C0, PAD, PAD, PAD]   valid_count = 1
Rank 1 sends: [C1, C2, C3, PAD]   valid_count = 3

select-and-pad 后: [C0, C1, C2, C3]
```

HCA 和 CSA 的 indexer 拿到去 padding 的全量 entry。CSA 的稀疏路径拿到按 top-k 重排的紧凑视图。

![阶段 2：all-gather 对齐形状，select-and-pad 修好语义](04-select-pad.png)

顺便解释一个设计取舍：为什么三条路径的「可见范围」要在这里统一处理？为什么两条路径的视图不一样？

因为 HCA 和 indexer 的可见范围，可以按规则静态预计算。但 CSA sparse 的 top-k，要等 indexer 跑完才知道。所以必须先 gather 全量，才能做选择。

这也是为什么 V4 不能像 Ring-Attention 那样「来一块算一块」。压缩边界要等邻居数据就绪，top-k 要全局视野，流水线的 overlap 基础直接消失。

一句话：Ring 用流水线藏通信，V4 用压缩省通信，代价是必须先 gather 再算。

## 六、通信量账：9MB vs 72MB

两阶段各花多少通信？把账算开（1M 序列、CP=8、每 rank 125K token）：

**阶段 1**：KB 级，见上表，与 T 无关。忽略。

**阶段 2**：每 rank 产出约 s/m 个压缩 KV entry，all-gather 发给其他 7 个 rank：

- CSA 层：125000 ÷ 4 × 576B ≈ **18 MB** / rank / 层
- HCA 层：125000 ÷ 128 × 576B ≈ **0.56 MB** / rank / 层
- 平均（CSA/HCA 交错各半）：**约 9 MB / 层**

假想一下，如果压缩不存在，直接 all-gather 未压缩 KV：

$$125000 \times 576 \approx 72 \text{ MB / rank / 层}$$

**压缩后平均省约 8 倍；单看 HCA 层，省 128 倍——压缩比直接兑换成通信节省倍数。** 这正是压缩注意力的复利：压缩 m 倍，KV 显存省 m 倍，CP 通信也省 m 倍。

![通信量账：压缩比直接兑换成节省倍数](05-comm-ledger.png)

9MB 在 NVLink（节点内 400GB/s 级）上只要约 0.02ms，可以被计算 overlap 掉。72MB 就藏不住了。

这也呼应上篇的账：EP 单层通信 16GB，CP 全模型（61 层）才约 549MB。CP 走 NVLink、EP 走 IB，就是因为 CP 的通信量被压缩按住了。

## 七、实验：切了会坏模拟器

纸上谈兵不够，我写了个小模拟器（experiment.py，纯 Python 无依赖）把「切了会坏」跑出来。

**实验设计**：随机生成多个 packed 序列（长度 37~210 不等，故意制造尾部残块）。拼成一条 token 流后，切成 8 个 rank。三种做法对比：

1. **单卡基准**：整条流在一张卡上按序列边界压缩——这是正确结果；
2. **朴素 CP**：每张卡只压自己段内的完整块，不管跨边界；
3. **两阶段 CP**：阶段 1 边界原料交换 + 阶段 2 all-gather + select-and-pad。

运行结果（CSA 场景，m=4，8 ranks × 140 tokens，10 个 packed 序列）：

| 做法 | 压缩 KV 数 | 与单卡基准一致？ |
|---|---:|---|
| 单卡基准 | 277 | — |
| 朴素 CP | 276（缺 1 个跨边界块） | ❌ 不一致 |
| 两阶段 CP | 277 | ✅ 逐一比对一致 |

朴素 CP 缺的那个 entry，正是跨在 rank 边界上的压缩块——两边各自都不够 m 个，谁都没压出来。两阶段 CP 用阶段 1 把原料补过去，结果与单卡完全一致。

HCA 场景（m=128）更夸张：朴素 CP 从 4 个 entry 直接丢到 2 个，缺一半。两阶段依然与基准一致。换个随机种子重跑 10 次，断言全部通过。

![实验：朴素 CP 缺块，两阶段与基准一致](06-experiment.png)

**模拟器跑出来的结论**：CP 的难点从来不是「切」，是「切完还要压缩」。压缩边界跨 rank、压缩后长度不齐——这两个坑，普通 CP 看不见，V4 用两阶段通信填平了。

## 结尾

回到开头的问题：1M 序列为什么切了会坏？因为 V4 的注意力是压缩的，压缩块会跨边界、压缩后长度会不齐。两阶段通信的实质，是把「补齐边界原料」和「对齐形状、修好语义」拆开处理。阶段 1 传原料给右邻居补块；阶段 2 用 all-gather 对齐形状，用 select-and-pad 修好语义。

这也是一个常被忽略的事实：**注意力公式变了，训练并行策略不能原封不动。** CSA/HCA 不只是「推理更快、KV 更小」。它连 rank 间怎么通信、张量怎么对齐、kernel 要什么布局，全都改了。

下一个问题顺理成章：GPU 之间通信这么多，训练时卡在等谁？PP 流水线的气泡怎么填？EP 的 all-to-all 怎么藏进计算？这是 08-15 的主角——DualPipe 与 DeepEP。

一个问题留给你：如果让你设计一个「压缩注意力 + 长序列」的训练系统，你会选「先 gather 再算」的 V4 方案吗？还是想办法保留「来一块算一块」的流水线？压缩省通信和流水线藏通信，你更看好哪条路？

🔥 **近期热门**：
[1.6T参数怎么塞进GPU？V4五维并行策略](https://mp.weixin.qq.com/s/ae1iwvau14gFCnyfg4hVIw)

[多Token预测：一次猜两个词，快1.8倍](https://mp.weixin.qq.com/s/EmjgFu5C6bkpltYidQhLRQ)

[KV缓存存进SSD：慢50倍的硬盘，为什么反而更快？](https://mp.weixin.qq.com/s/40BQ06eDTv4-2r8FmQ_rMA)

[FP8训练：残缺数字怎么练出顶级模型](https://mp.weixin.qq.com/s/yxrkmxPSZ8CnsFhWZ1bCPA)

[mHC 怎么让 DeepSeek-V4 稳定训练 61 层？](https://mp.weixin.qq.com/s/VKD1Epopeuj_od-ITbg_dQ)

[K=V：一份KV缓存怎么干两份活？](https://mp.weixin.qq.com/s/88kscO8p0kMxHmeGm2llLA)

📖 **DeepSeek 技术解密**
- [1.6T参数怎么塞进GPU？V4五维并行策略（上篇）](https://mp.weixin.qq.com/s/ae1iwvau14gFCnyfg4hVIw)
- **上下文并行：1M序列为什么切了会坏？（本篇）**
- DualPipe 与 DeepEP：训练时 GPU 在等什么（下一篇）

📖 **[大模型原理合集](https://mp.weixin.qq.com/mp/appmsgalbum?__biz=MzkyMzQyODExNQ==&action=getalbum&album_id=4597831652025925632#wechat_redirect)**：① [BPE分词](https://mp.weixin.qq.com/s/5nR_KI47v_U8KwpQA4Uv5Q) → ② [词嵌入](https://mp.weixin.qq.com/s/rDryn1z_hLt7mwi3X8fsxQ) → ③ [位置编码](https://mp.weixin.qq.com/s/4nO2VqQLaYxGdDmtQeypCQ) → ④ [注意力机制](https://mp.weixin.qq.com/s/KrilwX6VRjI9KfjvD7C6kw) → ⑤ [前馈网络 FFN](https://mp.weixin.qq.com/s/vBCzukDlQyB9O6ASgAmlvQ) → ⑥ [归一化残差](https://mp.weixin.qq.com/s/v-SBuMTbMANSTxHj7gYDkg) → ⑦ [Transformer 全景](https://mp.weixin.qq.com/s/22J8JPkdpVeUx23KahbBmA) → ⑧ [预训练](https://mp.weixin.qq.com/s/XoGHVycQHR5Tp-BWPac9Hg) → ⑨ [SFT](https://mp.weixin.qq.com/s/vwXGbjm9Ai1GPvQi5O3UyQ) → ⑩ [RLHF](https://mp.weixin.qq.com/s/NJDuCLAEfDpILf2J9D6qLQ) → ⑪ [PPO](https://mp.weixin.qq.com/s/OEZtUhm8MT_En7enJo_8dw) → ⑫ [GRPO](https://mp.weixin.qq.com/s/t4sO-zC5v1_jq8hJT_YTGA) → ⑬ [RLVR](https://mp.weixin.qq.com/s/NvemnDdtkinRKEbmtcckzA) → ⑭ [推理加速](https://mp.weixin.qq.com/s/LvxasW-4t0YuXy8nWpyzVw)

觉得有用就点个赞 👍、收藏 ⭐ 备用；关注「数解AI」。下一篇拆解 DualPipe 与 DeepEP：训练时 GPU 到底在等什么。

#DeepSeek技术解密 #上下文并行 #长上下文 #大模型训练 #数解AI

## 资料来源

- [DeepSeek-V4 Technical Report](https://arxiv.org/abs/2606.19348)（2026）：§3.5.3 Contextual Parallelism for Long-Context Attention 原文（两阶段通信、s/m+1、cp_size·s/m、select-and-pad、三路径可见范围）——逐项核对原文。
- HuggingFace `deepseek-ai/DeepSeek-V4-Pro/config.json`（已抓取核验）：`compress_ratios` 交替 [4, 128]（CSA m=4 / HCA m'=128）、61 层、`sliding_window: 128`。
- [Ring Attention with Blockwise Transformers for Near-Infinite Context](https://arxiv.org/abs/2310.01889)（Liu et al., 2023）：Ring-Attention 原理（击鼓传花 + 在线 softmax），对比 V4 为什么不能流水线式。
- [FP8训练：残缺数字怎么练出顶级模型](https://mp.weixin.qq.com/s/yxrkmxPSZ8CnsFhWZ1bCPA)：V4 训练用 FP8（E4M3，1 字节）而非 BF16，显存账按 1 字节/数计。
- [K=V：一份KV缓存怎么干两份活？](https://mp.weixin.qq.com/s/88kscO8p0kMxHmeGm2llLA)：V4 的 K/V 合并为一份（shared KV MQA，head_dim 512），显存账按 3 份张量（Q/KV/输出）计。
- 实验：`experiment.py` 自包含纯 Python 模拟器（packed sequences 切 8 rank，朴素 CP vs 两阶段 CP vs 单卡基准），仅机制演示，不代表官方性能。
