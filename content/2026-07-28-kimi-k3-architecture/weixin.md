---
title: "Kimi K3 架构怎么撑住 2.8T 参数？三轴拆给你看"
author: "数解AI"
digest: "Kimi K3 的 2.8T 参数不是暴力堆料。从数学直觉拆解三条扩展路线：KDA 省序列、AttnRes 换深度、Latent MoE 控通道。"
type: "架构全貌篇"
series: "DeepSeek 技术解密"
keywords: ["Kimi K3", "KDA", "Attention Residuals", "Latent MoE", "架构拆解"]
cover: 00-cover.png
wechatUrl: "https://mp.weixin.qq.com/s/6GJ2781jJh-dqYswJ07dfA"
scheduledPublish: "2026-07-28T20:00:00+08:00"
---

## 🎯 驱动问题：2.8T 参数怎么跑得动

一个 Agent 在 50 万 token 的代码仓库里连续改了 3 小时代码。第 37 轮时工程师加了一条约束：「支付接口绝对不能改」。3 小时后，工程师问：

> 「你还记得第 37 轮那条不能动支付接口的约束吗？」

模型要找到它，不能每次都把 50 万 token 从头翻到尾；但也不能为了快，把这条罕见却致命的约束忘掉。

如果你跟到这儿，我们已经一个一个拆过[注意力](https://mp.weixin.qq.com/s/KrilwX6VRjI9KfjvD7C6kw)、[MLA](https://mp.weixin.qq.com/s/HHMNEdCYThOjCLRozQorhg)、[MoE](https://mp.weixin.qq.com/s/QdkD0CR2fD-HfY77-gX3Ug)、[残差连接](https://mp.weixin.qq.com/s/v-SBuMTbMANSTxHj7gYDkg)。今天换个视角：不再拆单个零件，而是把它们拼回一个真实的 2.8T 模型，看 Kimi K3 怎么把「跑得动」这件事扛住。

**K3 要答对上面那个问题，靠的不是更大的注意力窗口，而是三个各自解决不同问题的架构选择。**

它的总参数 2.8T，但每次生成只激活 104B。这背后是三组各管一个方向、互不干扰的设计。序列方向用 KDA 省「翻历史」的账。深度方向用 AttnRes 救「层太深信号走样」。通道方向用 Latent MoE 控「唤醒多少参数」。三组设计拼起来，才让 2.8T 从一个吓人的数字，变成一个真能跑的模型。

---

## 一、KDA 轴：序列方向，别每次都翻全部历史

先看序列方向——也就是「历史有多长」。

普通注意力每生成一个新 token，都要拿自己的 Query 去和前面所有历史位置的 Key、Value 配对：

$$\text{Attention}(Q, K, V) = \text{softmax}\left(\frac{QK^T}{\sqrt{d_k}}\right)V$$

历史有 T 个位置，就要配对 T 次。T 涨到一百万，每一步生成都得扫一百万个位置。这就是[KDA 那篇](https://mp.weixin.qq.com/s/_RR5LLWgjGNm-qXdSdnAGA)里讲的「会议录音」困境：会议越长，可翻的录音越多，翻起来越贵。

KDA 的换法不在这里重复推导，只留一句直觉。它不再每次回放全部录音，而是维护一份持续更新的「会议速记」。状态 $S$ 大小固定，不随序列长度增长：

$$S_t = \alpha_t \cdot S_{t-1} + k_t \otimes v_t$$

$$\text{Output}_t = q_t \cdot S_t$$

新信息以「变化量」$k_t \otimes v_t$ 写入，旧的按门控 $\alpha_t$ 衰减。整段序列的处理量从 $O(T^2)$ 降到 $O(T)$。想知道这套状态更新为什么能撑住 1M 上下文、速记又为什么会漏掉关键原话，回看那篇有完整推演。

K3 的配比是 **69 层 KDA + 24 层 Gated MLA = 93 层**。多数层当速记员，把长历史高效整理。少数层（Gated MLA，门控版的多头潜在注意力）留作关键时刻的全局精读。所谓「门控」，就是一个可学习的开关，决定何时让这次精读真正写进模型状态。这正是 KDA 那篇讲的「速记 + 全局回看」分工，在 K3 里落成了具体数字。

![](01-kda-state-update.png)

到这里，序列方向「翻历史太贵」的问题压住了。但 K3 有 93 层——一旦层数深到这个地步，第二个方向的麻烦就冒出来：信号从底层往上传，传着传着就走样。

---

## 二、AttnRes 轴：深度方向，别让早期信号被传话传没了

### 传统残差：链式传话的代价

先说清「残差」在做什么。[归一化残差那篇](https://mp.weixin.qq.com/s/v-SBuMTbMANSTxHj7gYDkg)讲过：残差连接让每一层学一个「修正量」叠加到上一层的结果上，而不是从头重算。所以网络可以堆很深而不崩。

它的数学是：

$$h_l = h_{l-1} + f_l(h_{l-1})$$

看起来人畜无害，却藏着一个代价：第 $l$ 层只能看到第 $l-1$ 层的输出。信息要从第 1 层传到第 93 层，得经过 92 次这样的叠加与变换。

打个比方：像一群人玩传话游戏。第 100 个人听到的，不是第 1 个人原话，而是前 99 个人各转述过一遍的版本。传得越远，原话被压得越扁、混得越糊。在 93 层的网络里，早期那些「原始而关键」的特征，就容易被这么层层稀释掉。

### AttnRes：从「只能问上一层」到「能翻任意层」

Attention Residuals（注意力残差，下称 AttnRes）改的就是这一点。它把「只能问上一层」改成「可以翻前面任意一层」：

$$h_l = \sum_{i=0}^{l-1} \alpha_{l,i} \cdot \text{AttnRes}(h_i) + f_l(h_{l-1})$$

这里的 $\alpha_{l,i}$ 是第 $l$ 层对第 $i$ 层表示的注意力权重。第 93 层觉得第 3 层的原始表示有用，可以直接把权重投过去，不必再经过中间 90 层的转述。

一句话直觉：传统残差是「链式传递」，AttnRes 是「全连接检索」。

### Block AttnRes：检索成本也得压住

但有一个现实问题。如果第 $l$ 层要能翻看前面每一层的表示，就得把每层输出都存着供检索，内存是 $O(Ld)$——93 层 × 隐藏维度，扛不住。

K3 的解法叫 Block AttnRes（分块注意力残差）：把层按 12 个一组分块。块内还是传统残差累加，块与块之间才用注意力检索：

$$\text{Block}_j = \sum_{i \in \text{block}_j} h_i$$

$$h_l = \sum_{j} \beta_{l,j} \cdot \text{Block}_j + f_l(h_{l-1})$$

$\beta_{l,j}$ 是块级注意力权重。活跃状态从「每层一份」$O(Ld)$，压到「每块一份」$O(Nd)$，块数 $N = L/12$ 远小于层数。

还是会议的比方，但升一级：不是一个人先猜哪些录音重要，而是把录音分小组管理；要用的时候跨组调阅，而不是逐盘回放。AttnRes 让 93 层深度下的信息流动，从「链式衰减」变成「按需检索」——深度方向的问题，到这里也压住了。

![](02-attnres-block-retrieval.png)

---

## 三、Latent MoE 轴：通道方向，别每次都唤醒所有参数

序列和深度都搞定了，还剩第三个方向：通道——也就是[前馈网络](https://mp.weixin.qq.com/s/vBCzukDlQyB9O6ASgAmlvQ)那一步要唤醒多少参数。

K3 总参数 2.8T，如果每次前馈都全员参与，算力和显存都顶不住。MoE（混合专家）的思路在[DeepSeek MoE 那篇](https://mp.weixin.qq.com/s/QdkD0CR2fD-HfY77-gX3Ug)讲过：不让所有参数都参与每次计算，而是为每个 token 挑少数「专家」干活。这里只接上 K3 的具体做法。

### 稀疏路由：896 个专家里挑 16 个

K3 有 896 个 Routed Experts（路由专家），每个 token 只激活 16 个（约 1.8%）。另外 2 个 Shared Experts（共享专家）常驻兜底——不管路由挑到谁，每个 token 都会再过一遍这两个专家，保证基础能力不被稀疏路由削掉。最终激活参数 104B。

路由器给每个专家打分，挑分最高的 16 个：

$$g_i(x) = \text{softmax}(W_g \cdot x)_i, \quad \mathcal{E} = \text{topk}(g(x), 16)$$

被选中的专家各自处理后，按分数加权求和：

$$y = \sum_{i \in \mathcal{E}} g_i(x) \cdot E_i(x)$$

### Latent 投影：先缩成草图再批改

直接对 7168 维的隐状态做 16 个专家计算，搬运量很大。LatentMoE 多了一步：先把隐状态压到低维，在低维空间做专家计算，再升回去：

$$x_{\text{latent}} = W_{\text{down}} \cdot x \quad (7168 \rightarrow 3584)$$

$$y = W_{\text{up}} \cdot \sum_{i \in \mathcal{E}} g_i(x) \cdot E_i(x_{\text{latent}})$$

直觉：像把一份高分辨率图纸先缩成草图，在草图上批改，再放回原图——改的是同一处，但来回搬运的代价小了一半。这就是「Latent（潜在）」在 LatentMoE 里的含义：在低维潜空间里完成专家计算。

### Quantile Balancing：让 896 个专家别忙的忙死、闲的闲死

还有一道麻烦。896 个专家，如果路由不均衡，就会出现有的过载、有的闲置——闲置的等于白占显存，过载的成为瓶颈。

老办法是手工调一个「负载均衡」的超参，敲打专家被选中的频率。问题是这个超参很敏感，调小了不均衡，调大了又把路由带偏，本质上是个启发式补丁。

Quantile Balancing（分位数均衡）换了个思路。它名字里的「分位数」指什么？把一组数按大小排好，排在某个百分比位置的值就叫那个分位数——中位数就是排在正中间的那个。一句话：分位数就是「你在这堆数里排第几」的精确刻度。

它给每个专家 $i$ 维护一个可学习的偏置 $b_i$。关键设计在于：$b_i$ 只参与「选不选这个专家」的 top-k 决策，不参与选中后的混合权重：

$$g_i^{\text{route}}(x) = \text{softmax}(W_g \cdot x + b)_i$$

$$y = \sum_{i \in \mathcal{E}} \underbrace{\text{softmax}(W_g \cdot x)_{\text{无 } b}}_{\text{混合权重}} \cdot E_i(x)$$

这样偏置只调「谁被选中」，不污染「选中后贡献多少」。$b_i$ 的更新按分位数直接算：

$$b_i \leftarrow Q_{\text{target}} - Q_i$$

$Q_i$ 是专家 $i$ 当前被选中分数的分位数，$Q_{\text{target}}$ 是目标分位数。直觉很直白：被选太多的专家，把偏置往下压；被选太少的，往上抬。负载自动往均匀拉平，不再需要手工调超参。

![](03-latent-moe-routing.png)

---

## 四、Benchmark 速览

三个方向各自把效率推到极限，落到跑分上是什么样？

| Benchmark | K3 | Fable 5 | GPT-5.6 Sol |
|-----------|-----|---------|-------------|
| DeepSWE | 67.5 | 70.0 | 73.0 |
| SWE Marathon | **42.0** | 35.0 | 39.0 |
| BrowseComp | **91.2** | 88.0 | 90.4 |
| Program Bench | **77.8** | 76.8 | 77.6 |
| GPQA Diamond | 93.5 | 92.6 | 94.1 |
| GDPval-AA v2 | 1686 | 1747 | 1736 |

整体数字上，K3 还落后 Fable 5 和 GPT-5.6 Sol；但在长程编程（SWE Marathon）和 Agent 浏览（BrowseComp）这两类最吃「长上下文 + 深层推理」的任务上反超。这正对上了三轴设计的初衷——它优化的不是单步峰值，而是「在很长的历史里连续工作还不掉链子」。

---

## 回到开头：三轴合力，才撑得住那条约束

Agent 在第 37 轮找到那条「不能动支付接口」的约束，靠的是三轴合力。KDA 让它在百万 token 里高效检索，不必每次翻全程。AttnRes 让 93 层深度下的早期信号不被传话传没。Latent MoE 让 104B 激活参数足够强大，又不必每次全员上阵。

K3 的 2.8T 也不是凭空堆上去的。上一个开源天花板是 DeepSeek-V4-Pro 的 1.6T，K3 一步把它抬到 2.8T——参数量多出七成多。这么大的模型，要塞进 1M token 还跑得动，靠的是前面三轴。KDA 压序列成本，AttnRes 救回深层信号，Latent MoE 控住每次激活的参数。而且它不只是「跑得动」——实测里，K3 在长程编程和 Agent 浏览上反超了闭源旗舰。**K3 站上开源参数量的新顶点，靠的不只是大，是让「大」既能跑、又跑得赢的三轴效率。**

不过，架构撑住的只是「能力上限」。一个能跑 1M 上下文的模型，不等于天生就会听「帮我改这段代码」这样的指令——它还只是个会预测下一个词的语言底座。下一篇 SFT 监督微调，就讲怎么把这堆能力调教成听话的助手。

---

### 资料来源

- [Kimi K3 官方技术博客](https://www.kimi.com/blog/kimi-k3)
- [moonshotai/Kimi-K3 HuggingFace 模型卡](https://huggingface.co/moonshotai/Kimi-K3)
- [Kimi K3 技术报告](https://github.com/MoonshotAI/Kimi-K3)

---

📖 **[大模型原理合集](https://mp.weixin.qq.com/mp/appmsgalbum?__biz=MzkyMzQyODExNQ==&action=getalbum&album_id=4597831652025925632#wechat_redirect)**：BPE → 词嵌入 → 位置编码 → 注意力 → KDA 长上下文 → MLA → FFN → 归一化残差 → Transformer 全景 → **Kimi K3 架构全貌** → 预训练 → SFT → RLHF → 推理加速

日更节奏，把大模型从输入到生成的链路讲到不用回头查。关注「数解AI」，下一篇第一时间推给你。

*觉得有用就点个赞 👍、收藏 ⭐ 备用；点个「在看」让更多朋友看到。*

假如你在设计一个 2.8T 模型：你会把更多层分给 KDA（速记）还是 Gated MLA（全局回看）？为什么？评论区聊聊。

#大模型原理 #KimiK3 #AttentionResiduals #LatentMoE #数解AI