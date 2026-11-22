---
title: "AI 写字还要逐字来？扩散模型已经整段抠了"
author: "数解AI"
date: "2026-11-26"
type: "原理篇"
series: "扩散语言模型"
digest: "自回归逐字写，扩散语言模型逐块抠；2026 年已跑出千级 tok/s 与百亿级开源，但 SDAR 摘要明言 AR 仍更省——它是工程解，不是智能解。"
cover: "00-cover.png"
keywords: "扩散语言模型,diffusion language model,扩散模型,LLaDA,Mercury,非自回归"
wechatUrl: ""
---

让模型补一段两三百字的代码或实现，它一个字一个字往外吐，没有完事儿之前，你只有干等着的份儿。
2026 年，Inception Labs 的 Mercury Coder 跑出了 1,109 tok/s，这是 Artificial Analysis 的独立实测成绩（H100，Coder Mini；Coder Small 为 737 tok/s）。

同样一段内容，这边还没打完字，那边已经写完停在那儿了。这不是厂商通稿，而是第三方独立评测。

看到这个超过1000的tps数据，我其实有点不敢相信自己的眼睛。DeepSeek V4.1 Flash刚刚上线的时候，官方API的确达到接近400tps，这是我自己测试看到过的；GPT astra甚至一度被嘲笑只有60tps。

逐字输出是语言模型的默认做法。而到了 2026 年，选择不按这个写法来的，已经出现了三股不同的力量。这篇文章把这条线捋一遍：看看它们到底是什么、谁在推、账怎么算。

## 一、你等模型逐字吐的时间，够别人抠完两轮了

平时写代码或等长回答，自回归模型大多停留在每秒几十个 token 的量级；到了多轮 agent 循环，单步等待会一层层叠上去。Mercury Coder 的独立实测数字是 1,109 与 737 tok/s（arXiv:2506.17298），把「等出字」拉到了肉眼可见的落差上。

算快几倍之前，得先看清数字是谁说的：厂商自宣、第三方独立实测、论文摘要、论文自报无复现，四种口径的分量并不一样。先搞清楚它换掉的到底是什么，再聊快了几倍。

## 二、AI 写字，凭什么可以不用逐字？

传统自回归像写字时一个字一个字往前挪，前面写错的字很难收回来；masked 扩散语言模型换了条路，先整段糊住，再一遍遍抠清楚。准确说是逐块抠：块内并行，块间仍可顺序。标题里的「整段抠」图个上口，落到机制上，其实就是一块一块来。

从「几乎全遮」起步，每一步把最有把握的几个词点亮，直到整段话浮出来——每一步敢同时点亮几个词（并行度），就是核心旋钮。「遮词—猜词」最早是 BERT 时代的预任务，如今成了生成方式本身。想看图像扩散去噪的底子，可以对照[《AI 出图要跑 50 步，为什么砍到 10 步还清晰，砍到 1 步就糊了？》](https://mp.weixin.qq.com/s/WOrO8gJ0wH6XnhtJ28FRtQ)里「同一数学、不同模态」的逻辑。

这个范式的出现其实有一两年时间了，之所以没有取代自回归这种主流范式，我想很大程度上还有赖于模型智力是否真的有所超越，以及既有的中训练和后训练机制是否有可替代方案。

![逐字写与逐块抠对比示意图](01-paradigm.png)

逐块抠图的方式其实像我们准备长篇演讲时候打的腹稿，先是在脑袋里有一个大框框的勾勒，然后再逐一细化接下来要讲的每一句话。

## 三、BERT 玩剩的遮词，凭什么变成生成方式？

把「遮住词让模型猜」变成语言模型的生成方式，它其实不是一天内就发生的。

离散扩散从 D3PM（2021 年把扩散搬进离散空间）起步，经由 SEDD 与 MDLM（2022–2023 年连续时间去噪的离散路线）搭起数学地基。

2025 年，LLaDA（arXiv:2502.09992）用 8B 从头训练，reversal poem 任务超过 GPT-4o；Dream 7B（arXiv:2508.15487）基于自回归初始化，引入上下文自适应噪声重调度，两篇一起把路线推到实用化的程度。

2026 年这条技术路线开始走向规模化：LLaDA2.0（arXiv:2512.15745）是首个 100B 级扩散语言模型，含 flash 100B 与 mini 16B MoE，走 AR 到 dLLM 的知识继承转换加三阶段块级 WSD。

SDAR（arXiv:2510.06303，ACL'26 Findings）把块内扩散与块间自回归合到一处，30B MoE 在 GPQA 与 ChemBench 上超过同源 AR 版本。

### 为什么偏偏是现在：数据效率与并行执念

这条路线在 2026 年抬头，背后有两笔账。

一是数据账：Super Data Learners（arXiv:2510.04071）发现，0.6B 扩散语言模型只用 3B 唯一 token 训练，就超过了 36T token 的对照模型。作者把主因归于输入 token 的随机掩码——在所谓 token crisis 之下，遮词不只是技巧，也是数据效率的来源。

训练目标与噪声级别，可参看[《猜噪声怎么就学会了画猫？扩散模型的训练目标不是拍脑袋定的》](https://mp.weixin.qq.com/s/IuoNCCYdsabOnkeGerOKEA)与[《扩散模型为什么要几百个噪声级别？一个够吗》](https://mp.weixin.qq.com/s/ieHJjnSvSEseQkR4sFQh_w)。

二是算力账：训练早就并行化了，推理侧却到今天仍卡在串行生成上，我们放到最后一节来详细说说。另外，后来的玩家大多从自回归改造而来，为什么这样，后面第五节会仔细讲一下原因。

![扩散语言模型家族演进时间线](02-family.png)

## 四、2026 年，谁在不逐字写字？

到了 2026 年，不逐字写字的玩家分成三股势力：商用巨头「三极」、开源双雄、国产一条线。

商用与巨头三极各有打法。Inception 的 Mercury 3 于 2026 年 10 月 19 日发布，宣称 1,000+ tok/s 与 4–8x 加速下，能力仍超 GPT-6 Luna 与 Claude Haiku 5.5，规模比 Mercury 1 大 40x 以上，支持 1M 上下文与最大 131,072 输出。

定价上，input 每百万 token $0.20、cached $0.02、output $0.70，发布期折扣价分别为 $0.10、$0.01、$0.35。

另有 Mercury Decide（$0.04 折扣价 $0.02，output $0），做分类、打分与抽取。

Google 的 DiffusionGemma 于 2026 年 6 月 10 日发布，Apache 2.0，26B MoE 推理激活 3.8B、上下文 256K，架构是 encoder 因果预填充 + decoder 对画布双向去噪的 block-autoregressive multi-canvas，官方口径为单卡 H100 1,000+ tok/s（RTX 5090 为 700+ tok/s），最高 4x token 输出加速。

NVIDIA 的 Nemotron-Diffusion（arXiv:2607.05722，3B/8B/14B 家族）走 tri-mode 路线，相对 Qwen3-8B 在精度相当下可达每前向 6x tokens，GB200 搭配 SGLang 的 SPEED-Bench 吞吐达 4x，linear self-speculation 在 GB200 上最高 3.3x，优化 kernel 达 3.97x / 1,015 tok/s，batch=1 则为 277 tok/s。

论文里面明明老老实实写了自回归仍然比扩散模型更加经济实惠，新闻宣传上却没有人老老实实地把真想说完整。况且这个比较对象，还多少有点田忌赛马的味道。

### 开源双雄与国产一条线

开源侧有首个 100B 级扩散语言模型 LLaDA2.0（flash 100B / mini 16B MoE），另一支是 30B MoE 的 SDAR（上海AI实验室、浙大、UMD、上交与清华合写）。

国产模型这一条线里，人大高瓴人工智能学院与蚂蚁在推 LLaDA 路线；字节 Seed Diffusion（arXiv:2508.02193）在 H20 GPU 上跑出 2,146 token/s，摘要自称在代码模型的速度—质量帕累托前沿上是新 SOTA。

DiffuSpace 的 Clover（arXiv:2611.24636，35B-A3B MoE）在 2026 年 11 月 18 日发布，SWE-bench Verified 拿到 73.6（表 1 第一），Terminal-Bench 2.1 为 51.7、SWE-Pro 为 46.5，速度上单卡 GB300（BF16，batch=1，block size 16）跑出 680 tok/s，H200 同设置为 515 tok/s。

关于稀疏与架构取舍的另一侧争论，也可对照[《1M 上下文只算 2048 个 token，MiniMax 的稀疏为什么这次成了？》](https://mp.weixin.qq.com/s/9m_vkJpWr__Ce7JJQYOyIQ)。

国产模型里面风声很大的微信大模型团队，其实感觉一直躲在混元主产品模型的背后，雷声大而雨点小。

![2026年扩散语言模型玩家格局图](03-players.png)

## 五、这么快，论文摘要里为什么藏着冷水？

掌声之外，好几盆冷水其实就摆在论文和评测表里。

第一盆算力账：SDAR 摘要明言「AR 仍比 masked 扩散算得更省」，块间带着顺序依赖，并不是所有场景都天然省。

第二盆口径账：「快」不是一个数，tok/s、端到端延迟、每前向 token 数（如 Nemotron 的 6x）各测各的维度，不能直接混为一谈。

第三盆是可监控性。DiffusionGemma 透明度研究（arXiv:2606.20560）指出，朴素实现的 opaque serial depth 是 AR 版 Gemma 4 的 28.6 倍，加入 token bottleneck 后才降到 1.1 倍且不掉性能，可监控性与 Gemma 4 相当。

第四盆是改造与编码账：都从自回归改造而来，是因为纯从头训的数据账还没算漂亮；Clover 表 1 的复现也显示，受测扩散语言模型在 Terminal-Bench 2.1 与 SWE-bench Verified 上仍落后 Qwen 基线，agentic 编码场景还没翻盘。

如果仅仅是用更快的输出速度，付出可观测性下降的成本，智力上限又没有本质的提升，窃以为这还不能算一个合算的权衡。

## 六、所以，是下一个范式，还是又一个补丁？

把整条线串起来看：逐字写的等待太久，才有人把「遮词—猜词」改成逐块抠；三极与开源、国产交出了千级 tok/s 和百亿级参数，但论文摘要与评测基准又把算力账、口径差和编码短板摆上台面。

### 扩散语言模型押的注

Kuleshov Group《How to Build a Diffusion Language Model》（2026）点出了一个押注点：后训练与推理都被串行生成卡着脖子，推理若能像训练一样并行，加速或许会像当年 Transformer 撬动扩展律一样戏剧化。

早年串行算法吃不满 GPU，直到并行化才释放规模效应。眼下它解决的还是延迟和成本的工程账，能力上限那本账尚未兑现，但从 8B 到 100B 的速度，谁也不敢给下一年下定论。

这更像是[《DeepSeek 只换了权重：分数涨 11 分，思考少了三成》](https://mp.weixin.qq.com/s/HG2yIC1XVNRGLz909UzifA)里那种「换挡而非单点修补」的路线博弈。

扩散模型是否真的能吃掉自回归模型，还是继续充当边角料，默默等待下一个算法或者理论层面的逆袭，每个人可能都会有自己的判断。

至少目前这个时间节点，谁能最终胜出还并不明朗。下次你再干等模型逐字吐那两秒，至少知道有人已经不等了。

觉得这篇有用，点赞、收藏，转发给还在干等模型逐字吐字的朋友。

---

🔥 **热门文章**：

[KV缓存存进SSD：慢50倍的硬盘，为什么反而更快？](https://mp.weixin.qq.com/s/40BQ06eDTv4-2r8FmQ_rMA)  
[高维空间为什么全是壳？内积才是那把尺子](https://mp.weixin.qq.com/s/Nrfr-90Fpu3mFDML9s0d1Q)  
[高斯为什么二阶就够？非线性去哪了](https://mp.weixin.qq.com/s/gs_3y7JXuBLlzR5w6jW6fQ)  
[微软用 Go 重写 TypeScript，他一个人用 C++ 又写了一遍](https://mp.weixin.qq.com/s/GmPJAh8ERPkm64KzYirV2g)  
[学习率怎么自动调？Adam 优化器拆给你看](https://mp.weixin.qq.com/s/aSLVO-otvr2rxIU1kr2eAA)  
[DeepSeek-V4为何不用MLA？](https://mp.weixin.qq.com/s/MQEgbY16mLs-N7g2xKW1HQ)  
[AI 出图要跑 50 步，为什么砍到 10 步还清晰，砍到 1 步就糊了？](https://mp.weixin.qq.com/s/WOrO8gJ0wH6XnhtJ28FRtQ)  
[猜噪声怎么就学会了画猫？扩散模型的训练目标不是拍脑袋定的](https://mp.weixin.qq.com/s/IuoNCCYdsabOnkeGerOKEA)  
[扩散模型为什么要几百个噪声级别？一个够吗](https://mp.weixin.qq.com/s/ieHJjnSvSEseQkR4sFQh_w)  
[1M 上下文只算 2048 个 token，MiniMax 的稀疏为什么这次成了？》](https://mp.weixin.qq.com/s/9m_vkJpWr__Ce7JJQYOyIQ)  
[DeepSeek 只换了权重：分数涨 11 分，思考少了三成](https://mp.weixin.qq.com/s/HG2yIC1XVNRGLz909UzifA)  

**参考资料与数字溯源**（以下来源均于 2026-11-22 检索核对）

- LLaDA：arXiv:2502.09992（https://arxiv.org/abs/2502.09992）
- LLaDA2.0：arXiv:2512.15745（https://arxiv.org/abs/2512.15745）
- Dream 7B：arXiv:2508.15487（https://arxiv.org/abs/2508.15487）
- SDAR：arXiv:2510.06303（https://arxiv.org/abs/2510.06303）
- Mercury：arXiv:2506.17298（https://arxiv.org/abs/2506.17298）；Mercury 3 官方发布（2026-10-19）与定价说明（https://docs.inceptionlabs.ai）
- DiffusionGemma：官方发布（2026-06-10）及透明度研究 arXiv:2606.20560（https://arxiv.org/abs/2606.20560）
- Nemotron-Diffusion：arXiv:2607.05722（https://arxiv.org/abs/2607.05722）
- Super Data Learners：arXiv:2510.04071（https://arxiv.org/abs/2510.04071）
- Seed Diffusion：arXiv:2508.02193（https://arxiv.org/abs/2508.02193）
- Clover（DiffuSpace）：arXiv:2611.24636（https://arxiv.org/abs/2611.24636）；https://diffuspace.ai
- Kuleshov Group, *How to Build a Diffusion Language Model*（2026）

#扩散语言模型 #非自回归 #大模型推理 #原理篇 #数解AI