---
title: "几万块挑几百块：Lightning Indexer 凭什么敢这么挑"
author: "数解AI"
date: "2026-08-11"
type: "解密篇"
series: "DeepSeek 技术解密"
digest: "注意力想跳过不重要的内容，但只有看完才知道哪些不重要——这是长上下文的第一道死结。DeepSeek-V4 的答案是一个 FP4 精度的小模型：Lightning Indexer。它从 128K token 压缩成的 3.2 万块里挑出 512 块，交给核心注意力去算，稀疏注意力让计算量直接砍到 1/64。为什么一个用残缺数字训练的小网络敢替大模型做决定？因为筛选是弱判断，漏几块只是多算一点；计算才是强成本。V4 用两阶段训练教会它只看重点，并以 99.7% 的召回率验收。"
cover: "00-cover.png"
wechatUrl: null
keywords: ["Lightning Indexer", "稀疏注意力", "CSA", "DeepSeek-V4", "长上下文", "top-k"]
---

# 几万块挑几百块：Lightning Indexer 凭什么敢这么挑

上次讲完 KV 落盘，有读者追问了一句：档案按块存进硬盘了，但**翻档案**本身要不要时间？

要，而且如果翻得笨，落盘省下的 prefill 会全还回去。DeepSeek-V4 的答案是训练了一个小模型——Lightning Indexer，专门负责从几万个块里挑出该看哪几个。这篇文章拆三件事：为什么非筛不可、它凭什么敢筛、以及它是怎么被教出来的。

（先交代一句背景：V4 已在 2026 年 4 月开源，MIT 协议。下面所有参数都能在官方 config.json 里查到，不信可以自己去翻。）

上一站是 KV 落盘（[V4 注意力篇](https://mp.weixin.qq.com/s/MQEgbY16mLs-N7g2xKW1HQ)同系列），讲了档案怎么按块存进硬盘。这一站讲档案怎么被翻出来。

## 一、死结：选择依赖计算，计算依赖选择

先回到注意力本身。每个新 token（query）都要跟历史上所有 KV 做点积，才知道该重点关注谁——这是注意力机制的基本盘，上篇讲过，不重复。

问题在于：**想跳过不重要的块，前提是知道哪些块不重要；想知道哪些块不重要，得先读一遍所有块。** 读一遍所有块的代价，跟全量注意力是同级的。

这就是「先筛后算」的死结：

- 选择依赖计算：判断「哪块重要」需要计算
- 计算依赖选择：想少算，得先知道该算哪块

全注意力怎么处理这个死结？它不处理——它选择「全都算」，用 O(L²) 的代价换正确性。上下文短的时候没问题，可 1M token 的上下文里，每个 query 要面对 100 万个历史位置。全都算，算不动。

直觉类比：图书馆查资料，目录卡只有「读了正文才知道哪本有用」。你只有两个选择：全读（O(L²)，正确但贵），或者赌（可能漏掉关键的那本）。

## 二、压缩块：把问题从 128K 缩到 32K

V4 的第一步是压缩——把每 m=4 个 token 压成一个「块」（压缩机制在 [V4 注意力篇](https://mp.weixin.qq.com/s/MQEgbY16mLs-N7g2xKW1HQ) 讲过，落盘细节见 KV 落盘篇（待发布），此处只回链不重推）。128K 的上下文，压完之后是 32K 个块——这就是标题里说的「几万块」。

压缩解决了「存得下」，没解决「算得完」：核心注意力还是要对全部 32K 个块做点积。1M 上下文更夸张，每个 query 要面对 **25 万个块**。

所以下一步必然是稀疏：**只挑出少数几个块给核心注意力算。** 谁来挑？就是本文主角。

## 三、主角：一个 FP4 精度的小网络

Lightning Indexer 的参数（V4-Flash 真实 config）：

| 参数 | 值 | 含义 |
|------|-----|------|
| index_n_heads | 64 | 打分用的 head 数 |
| index_head_dim | 128 | 每个 head 的维度 |
| index_topk | 512 | 每个 query 只留 512 个块 |
| 精度 | FP4 | 比 FP8 还狠的低精度 |

它做三件事：对每个 query，给全部压缩块算一个「相关分」→ 用 ReLU 把负分淘汰 → 只把分数最高的 512 块交给核心注意力。

主模型负责精读，Indexer 负责速览。速览便宜到每个 token 都能跑，精读贵到只留给选中的块。

## 四、为什么敢：三个支柱

### 支柱一：ReLU 淘汰制，是 FP4 下的唯一活路

打分公式（[CSA 篇](https://mp.weixin.qq.com/s/MQEgbY16mLs-N7g2xKW1HQ)给过，这里只做回味）：

$$
I_{t,s} = \sum_{h=1}^{64} w_{t,h} \cdot \mathrm{ReLU}\big((q_{t,h}^I)^\top K_s^{IComp}\big)
$$

$q_{t,h}^I$ 是第 $h$ 个 indexer head 的 query，$K_s^{IComp}$ 是第 $s$ 个块的检索键，$w_{t,h}$ 是 query 动态生成的 head 权重。

为什么是 ReLU 而不是 Softmax？两个原因：

1. **Softmax 需要全序列归一化**——每个分数依赖所有分数，必须等全部算完才能继续。ReLU 每个分数独立计算，可以**边算边筛**，负分直接就地淘汰。
2. **更致命的是精度**：Indexer 跑在 FP4 上（4-bit，只有 16 个可表示的值）。`exp(x)` 在这么小的动态范围下直接溢出，除法精度崩坏。而 `max(0, x)` 只有比较运算——**零精度损失**。这不是设计偏好，是软硬件协同的必然。

还有个免费的赠品：高维空间里随机向量的点积接近 0，ReLU 天然截掉一半负分——粗筛的第一刀是白送的。

### 支柱二：多头加权，比单路打分聪明

64 个 head 各学一套「重要性标准」——有的看语义相关，有的看位置模式，有的盯特殊 token。每个 head 的权重 $w_{t,h}$ 由 query 动态生成、可正可负：**「某个 head 的高分反而是负面信号」这种逻辑也能表达。**

对比最早的粗筛方案 NSA（2025 年的论文），它用压缩路径的副产品当分数，相当于「门卫兼面试官」。Indexer 则是「雇了专职面试官团队」——每人看不同维度，最后加权决策。

### 支柱三：选错代价有上限——这是「敢」的底气

最关键的还是这笔账：

- **选错了 = 漏掉一个关键块 = 核心注意力没看到它。漏看 ≠ 看错**，只是信息少了一点，输出会模糊但不会胡说。
- **全都算 = 刚性成本**，1M 上下文下每个 query 25 万次点积，躲不掉。

k=512 vs 32K 块，稀疏 **64 倍**。只要召回率守住（V4 QAT 后披露的验收数字是 **99.7%**），质量损失可忽略。

赌注结构一目了然：输的代价小（漏块），赢的收益大（省 64 倍计算）。这买卖值得做。

## 五、怎么做到的：15 行代码 + 一个数字例子

真实实现（HF transformers 开源版，`modeling_deepseek_v4.py`）的链路，简化成 15 行：

```python
# 压缩块已就绪：C[0..T-1]，T = 序列长度 / 4（如 128K → 32K 块）
def lightning_indexer(query, blocks, W_q, W_w, k=512):
    scores = []
    for h in range(64):                       # 64 个 indexer head
        q_h = query @ W_q[h]                  # query 的低秩投影（每 head 一份）
        s_h = relu(q_h @ blocks.T)            # 与全部块点积 → ReLU 淘汰负分
        scores.append(s_h)
    w = query @ W_w                           # query 动态生成 head 权重（可正可负）
    score = sum(w[h] * scores[h] for h in range(64))   # 多头加权求和
    return topk(score, k)                     # 只留分数最高的 k 个块
```

数字走一遍（128K 上下文）：query 向量 → 64 个 head 各对 32K 块做点积（FP4，极便宜）→ ReLU 截掉负分 → 加权求和 → 取 top-512。核心注意力只算这 512 块，全算则要算 32K 块，稀疏 **64 倍**。

有个因果细节值得一提：query 只能看「已闭块」——窗口还没凑满的块对 query 不可见，真实实现里用 -1 哨兵处理。这种细节藏在开源代码里，恰恰说明它不是 PPT 架构。

## 六、怎么学会的：两阶段 warmup

这一节是本文主场，因为「注意力怎么学会只看重点」的答案在这里。

**问题**：Indexer 是随机初始化的。直接上稀疏训练 = 随机丢块 = 训练直接崩。必须先教会它「哪些块重要」。

**阶段一（前 1T tokens）**：模型用密集注意力正常预训练。论文原文（§4.2.2）：「we first warmup the model with dense attention for the first 1T tokens」。此时没有稀疏、没有 Indexer，主模型先把语言能力学好。

**阶段二（序列长度到 64K 时）**：引入稀疏注意力。但在此之前，论文设了一个短阶段，专门 warmup Lightning Indexer（原文 "a short stage to warm up the lightning indexer in CSA"）。论文只交代了有这么一步，没写老师是谁——下面是我的推理。

**老师是谁？（合理推断，论文未披露细节）**：warmup 阶段模型仍按密集方式跑，把**密集注意力的真实注意力权重**当老师。学生（Indexer）的任务，是预测「密集注意力会把权重放在哪些块上」。学的是「真正重要的块长什么样」，不是自己瞎猜。

我为什么这么推断？因为这是两阶段训练唯一自洽的监督来源：indexer 学的若是自己的分数，就退回随机丢块了。只有模仿密集注意力，它才能学会「哪些块值得看」。论文没写这一步的细节，但推理链条是唯一合理的。

我在自己的 `experiment.py` 里完整复现了这个流程：先训练一个小 Transformer（密集注意力），再用它的真实注意力权重当老师，训练 indexer。效果见下文。

**top-k 不可微怎么绕**：`topk` 的索引选择不可导，梯度没法穿过「选了哪几个块」。绕法：训练时用打分网络的**连续输出**（每块的分数）接交叉熵/排序类损失，推理时才离散化成 top-k。梯度走分数，不走索引。

**验收标准**：召回率——indexer 挑出的块覆盖了「密集注意力真正看重」的 KV 的比例。V4 在 QAT 阶段披露：index scores 从 FP32 压到 BF16 后，**top-k 选择器提速 2 倍，召回率保持 99.7%**。

为什么必须两阶段而不是端到端？因为稀疏结构一旦固定就很难改——块选错的信息再也进不来。**先学全量、再学偷懒，偷懒才不至于变成瞎。**

## 七、他山之石：GLM 和 Kimi 的两条路

Indexer 不是「先筛后算」的唯一方案，甚至不是 DeepSeek 独家。中国开源前沿模型至少有三条路线：

**路线一：DeepSeek 系（本文主角）**——独立打分网络，ReLU + 低精度，从 token 到压缩块。

**路线二：GLM-5 系——同一套 DSA，但把 Indexer 共享化。**

GLM-5（智谱，744B，2026-02 开源）直接采用了 DeepSeek 的 DSA + Lightning Indexer（config 里 index_topk=2048、index_n_heads=32）。这是「Indexer 不是 V4 独家」最直接的证据。

GLM-5.2（2026-06）更进一步提出 **IndexShare**。清华的 IndexCache 论文（arXiv 2603.12201）实测：**相邻 DSA 层的 top-k 选择有 70%-100% 重叠**，相邻层对「哪些 token 重要」的判断几乎一致。既然如此，每 4 层共享一个 indexer（一个 full 层算，三个 shared 层复用），1M 上下文下 per-token FLOPs 降 **2.9 倍**。

这里藏着本文最重要的一条引申：**粗筛自己也会变成瓶颈**。IndexCache 实测 200K 上下文时，indexer 点积消耗了 **81% 的 prefill 时间**。「先筛后算」的「筛」也是 O(L²) 量级，只是常数更小。GLM 的答案是让「筛」的次数除以 4；V4 的答案是让「筛」的对象从 token 变成压缩块（除以 m）。**两家其实在解同一个新问题：筛选成本本身。**

**路线三：Kimi K3——压根不筛。**

K3（2.8T，2026-07 开源）走线性注意力：KDA 把历史压成固定大小的递推状态（93 层里 69 层是 KDA），1M 上下文不需要为每个 token 存 KV。没有 top-k，也没有 indexer，**选择问题被结构消解**。代价是压缩状态丢失精确历史，靠 24 层 Gated MLA 定期做全局检索兜底。

| 方案 | 选择机制 | 筛选成本 |
|------|---------|---------|
| V4 CSA Indexer | 独立打分网络，ReLU+FP4，选压缩块 | O(L/m)，FP4 廉价 |
| GLM-5.2 IndexShare | 同款 indexer，4 层共享 1 个 | 打分次数 ÷4，FLOPs 降 2.9× |
| Kimi K3 KDA | 无选择，固定状态递推 | 无 top-k，O(1) 状态 |

DeepSeek 发明了「筛」，GLM 把「筛」变便宜，Kimi 把「筛」整个省掉。三者都在回答同一个问题：1M 上下文下，注意力凭什么敢不全算。

## 八、回扣：同事的追问，现在有答案了

回到开头。同事问「它怎么知道该翻哪几卷档案？」

答案：不是大模型自己翻的。是一个 FP4 精度、参数占比不到 1% 的小网络替它速览——先花 200 万次廉价点积给几万块打分，挑出 512 卷，大模型才动手精读。它敢这么挑，因为漏看只是少看一点，全算才是真的贵；它能学会这么挑，因为两阶段训练里，密集注意力当了它的老师。

我越来越觉得，这行的聪明人不是把一件事做到极致，而是想清楚「什么事该用多大的力气做」。翻档案用 FP4 的小模型，精读才用得上 V4-Pro 那样 1.6T 参数的庞然大物。

我的 `experiment.py` 复现了这条链路：训练一个小 Transformer 学会联想检索（序列开头埋 key-value 对，末尾问 key 要 value），再用它的真实注意力当老师，教 indexer。结果：**只保留 1/8 的块（k=8 vs 64 块），query 位置的召回率 88.5%，输出与全量注意力的余弦相似度约 0.95**（实测 0.9464）。少算 8 倍，输出几乎不变，「漏块只是信息少一点」在这张表上看得清清楚楚。（机制演示，不是官方性能基准；indexer 打分自身的成本未计入，V4 里它是 FP4 廉价路径。）

如果「先筛后算」这么好用，你觉得模型里还有哪些「全部算一遍」的地方，可以换成先筛后算？评论区聊聊。

下一篇算另一笔时间账：Indexer 省的是推理时翻档案的时间，MTP 省的是训练时猜词的时间。一次猜两个词，训练为什么快 1.8 倍？

📖 **[大模型原理合集](https://mp.weixin.qq.com/mp/appmsgalbum?__biz=MzkyMzQyODExNQ==&action=getalbum&album_id=4597831652025925632#wechat_redirect)**：BPE → 词嵌入 → 位置编码 → 注意力 → KDA 长上下文 → FFN → 归一化残差 → Transformer 全景 → 预训练 → Kimi K3 架构 → SFT → RLHF → PPO → GRPO → RLVR → 推理加速

📖 **[DeepSeek 技术解密系列]**：… → [AI 上下文为什么越长越慢](https://mp.weixin.qq.com/s/PLVRS0TTHXHDve1Z3r6M7Q) → [MoE 混合专家](https://mp.weixin.qq.com/s/QdkD0CR2fD-HfY77-gX3Ug) → [KDA 长上下文](https://mp.weixin.qq.com/s/_RR5LLWgjGNm-qXdSdnAGA) → [MLA](https://mp.weixin.qq.com/s/HHMNEdCYThOjCLRozQorhg) → [Kimi K3 架构](https://mp.weixin.qq.com/s/6GJ2781jJh-dqYswJ07dfA) → [V4 注意力](https://mp.weixin.qq.com/s/MQEgbY16mLs-N7g2xKW1HQ) → [K=V](https://mp.weixin.qq.com/s/88kscO8p0kMxHmeGm2llLA) → [Muon](https://mp.weixin.qq.com/s/7bpfjLYn9E-CiBS4TY8A6w) → mHC → FP8 训练 → FP4 量化 → KV 落盘 → **Indexer（本篇）** → MTP

如果这篇帮你算清了「速览 vs 精读」这笔账，点个赞让更多人看到。关注后回复「Indexer」，我把稀疏注意力系列（V4 注意力、CSA、本篇）的合集链接发你。

#LightningIndexer #稀疏注意力 #DeepSeek-V4 #长上下文 #数解AI
