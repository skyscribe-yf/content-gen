---
title: "加入100个dummy token，算术能力飞涨10.7分：AI思维链正在悄然发生着变化"
author: "数解AI"
date: "2026-11-22"
type: "原理篇"
series: "Latent 思维链"
digest: "给13个前沿模型的提示词里面塞一些 dummy token，模型的智力就可以提升甚至多达10%？聊聊这个现象背后关于思维链消失术背后的整整八档光谱。"
cover: "00-cover.png"
keywords: "latent reasoning, 隐藏思维链, 思维链, filler token, 推理"
wechatUrl: "https://mp.weixin.qq.com/s/kwnvH_nhchJjZdESQPlP9g"
---

最近看到这篇2026年7月的一篇论文（arXiv:2607.22925）做了一个奇怪的实验：给当时的13个前沿模型的 prompt 里塞了一串「1、2、3……」这样的计数 token。面对同一道多步算术测试题，Gemini 3 Flash 的准确率竟然能从51.0涨到了61.7。

没有新指令，没有新例子，塞进去的看起来是对模型输出无关的 token，这样真的也能行吗？

联想到最近甚嚣尘上的隐藏思维链抗蒸馏新闻。其实不经意间，**思维链正在从「一串人类可读的step by step 的推理链条」变成了「人类看不懂的别的东西」**。翻阅相关论文才发现，这个领域已经延伸出来了8种不同的做法。

不过还是先看这篇论文本身是如何做的。

## 思考其实可以不依赖于有意义的 token 就可以

论文的设定并不复杂：需要完成的是3个合成任务——4位乘法、多步算术和代码变量计数。实验给的是10-shots的示例，用的方法叫作 filler，就是采用计数 token「1–100」填充，衡量的是相对无 filler 的额外叠加收益是怎样的。

论文实验里使用了13个模型，其中接近一半是我们的国产大模型。Kimi K2.5、DeepSeek V3.2、GLM-4.7 和 GLM-5 都赫然在列，大多是 2024–2025 年的模型，有点老，不过论文实验一般都有一定的滞后。

这里面也包含了 Qwen3-235B 与 Qwen3.5-397B，剩下的就是 Claude 家的模型、Gemini 3 Flash、Llama 4 Maverick 和 GPT-5.2/5.5，相对于论文发表时间，还算当时比较新和有代表性的模型了。

实验结果却分化得相当严重。

Gemini 3 Flash 的多步算术测试准确率，从51.0涨到61.7（+10.7pp）。乘法却只有1.0分的增加，看起来完全不明显。而 Opus 4.5 的两项得分都涨了不少：算术+11.2、乘法+10.0。

论文里还有一个看起来更加夸张的数字，对 Opus 4.6 模型而言，算术得分居然增加了30个点。但它的 API 其实是不支持assistant prefilling——也就是把prefix设定之后让模型接着做输出推理，所以这个得分似乎不能作数。

你可能觉得这个实验有什么意思？其实这个有点小儿科的实验，似乎和我们日常使用 AI 的背景并不太匹配。然而它背后折射出来的一件非常有意思的事情是：**「思考」这件事，本来就是否可以不依赖于有具体意义的 token 上？**

翻阅了一些相关领域的论文，我才发现针对大模型如何做推理，在思维链 CoT 技术被发明出来的2年之后，业界已经悄然衍生出来了8种不尽相同的做法，有些已经进入了实际的生产环境影响着我们使用 AI 的方式，有些却依然在实验室里被研究和讨论。

## 推理思维链 CoT 的八种处理手法

要理清这种现象，得先把市面上形形色色的「推理」处理手法放在一起看。理清之后，我发现得到的是一条类似太阳光通过三棱镜之后得到的光谱一样的东西，只不过和物理学中的光谱不同，**这个谱是高度不连续的**。

这条光谱，学术研究领域有人取名叫 latent reasoning，**潜思维链推理**。其判断标准简单来说，可以看作是对三个问题的不同答案：给不给人看？有没有实在的 token？谁付钱？

### 隐藏思维链技术

第一个谱系上的其实类似于“障眼法”，从完全可见的思维链，到完全隐藏，用户不可见，但是模型推理还完全依赖于隐藏在 API 背后服务器上的 token，可以分为三种：

- ① 显式可见 CoT：如 DeepSeek V4 的 thinking 模式，思维链全量流式可见。
- ② 摘要式 CoT：如 GPT-6.1 Sol 的默认形态，只给用户展示提炼后的轨迹。
- ③ 完全隐藏 CoT：token 照常生成，用户不可见，厂商在后端可读。

这个谱系的做法目前已经进入了生产阶段，尤其是海外前沿模型，都慢慢在开始采用第二和第三种做法，而国产开源模型，几乎全部在第一个阵营。

对于研究者而言，隐藏思维链的做法显然不是一个好消息，因为想深度探究模型在完成任务输出的过程中做了哪些事儿，已经变得极度困难甚至不可能。

甚至有人提出思维链正在失去意义的说法，大多是基于这个谱系的后两种做法发出的警告。模型侧的出发点其实主要是为了反蒸馏，但是对于用户和研究者来说则变成了分析权利的丧失。

### token 隐身家族

另外一个大类谱系就开始对模型推理过程中（自回归语言模型）的 token 做不同程度的微操手术了：

- ④ 哑 token 推理：pause / filler tokens，token 并无特定的语义，计算不可见。
- ⑤ 抽象 token 语言：离散端的压缩形态，两端之间的过渡带。
- ⑥ 连续 latent thought：如 Coconut / CODI，没有 token，思考直接藏在连续向量里。
- ⑦ 循环/隐藏计算：如 Ouro、Astra 的 recurrent depth、Hidden Decoding。同一组权重反复用，计算发生在深度维，中间并不产生输出 token。
- ⑧ neuralese：模型完全在私有稠密表示里思考与交流。这是安全学界想象出来的概念，目前还不存在这样的模型。

至于谁在付钱——第八档其实还不存在，而第一个谱系里面的第三档，海外前沿模型的 API，慢慢都演进到这条路径上了。
日常配工作流或选模型，我习惯把可见性排在第一位，其次看成本和速度，像 DeepSeek V4 这种全量可见的通常是首选。

![八档可见性光谱图](01-visible-spectrum.png)

## 「不给你看」仅仅是展示策略，并不会省钱

这个光谱里，误解最多的是第三档。很多人以为厂商把思维链藏起来是为了省算力——事实恰恰相反。

隐藏思维链的 token 照常是按照逐 token 生成的方式在解码。模型每一次前向推理的成本，前向推理的过程其实都不变，GPU 资源消耗的方式其实也和前面两种没有区别。

只是在 API 层面，返回给用户的时候，被拦截或者改写了。这方面不妨看 OpenAI 在 o1 发布时留过一段官方说明。原话是：「我们决定不向用户展示原始思维链」。官方给出的理由里，明写了「保留 chain-of-thought 监控的选项」。

![隐藏思维链机制图](03-hidden-cot-tokens.png)

账单上看更直接：OpenAI 和 Anthropic 的输出单价是输入的5倍，DeepSeek 峰时是 3–4倍（2026-11-17数据）。Gemini 定价表里也清晰地写道：「Output price (including thinking tokens)」。

思考 token 按输出计费，完全没有什么变化，资源消耗还是那么多，费用也照样收取，只是作为用户你看不到而已了。

### 思维链投毒

**隐藏思维链在商业上反而可能是加价项：它的中心是「不给你看」，不是「更便宜」。** 关于 API 账单的另一半，可以参考我们此前的分析：[上下文压缩省了 77% token，为什么账单反而更贵？](https://mp.weixin.qq.com/s/p-2YkAFT6sBwdU5_dw5O2g)。

之前就有人怀疑厂商是否在 API 上多给你计算一点 token 费用，你也无从争辩，因为从 API 交互层面，你完全没有办法去辩驳。

最近 Anthropic 甚至玩弄了更恶心的花招：给**你看的思维链，甚至不是模型内部推理使用的那个轨迹数据**——它的 API 根本不返回原始思维链，只回一个叫 thinking signature 的引用。而 2026 年 3 月 Claude Code 源码泄露曝光的 ANTI_DISTILLATION_CC 更狠：服务器会往系统提示里注入假工具定义，专门污染那些被抓去训练竞品模型的流量数据。

这个行为就很恶劣了，直接对模型的输出进行投毒了。如果真的只是针对蒸馏，道义上自然也可以站住脚，问题是普通人会不会无意躺枪？根本没法验证。

## 计算机制变化的几条路

前三档至少还有 token 可以在推理服务器上看到（权且假设你是厂商内部人士或者被授权的研究人员，可以看到原始输出），第四到第七档连 token 输出的形式都发生了变化，计算机制本身被改变了：

- **A. Pause / Filler tokens**（2310.02226 / 2404.15758）
  零成本试水，但是天花板很低。2404.15758 那篇靠 filler '......' 就可以解出两道算法任务题，但过程要依赖密集监督。
- **B. Coconut / CODI**（2412.06769 / 2502.21074）
  最纯的 latent 路线，直接用**连续向量当作思考过程的输入输出**，而不是现在这样需要映射回离散的文本空间来。CODI 在小学应用题基准 GSM8k 上，在 GPT-2 规模大小的实验模型上，甚至可以追平显式 CoT，大概采用了3.1倍的压缩。代价是训练极重、推理过程基本是串行的。
- **C. WeLM**（2607.08186，48 位作者）来自微信团队的探索。工程实现上最为干净，且唯一验证到了前沿模型的规模。大小是80B/617B，n=4——4 条并行流——在九个测试基准上宣称全部涨分。这也是国产阵营里，唯一走到这个规模的。只是官方博客定位在研究和探索，很可能并没有上微信的产品线。论文还做了探针实验——直接读隐状态。各流隐状态的余弦相似度从 0.987 降到 0.637——这也证明了几条流确实在分工推进。
- **D. Ouro looped**（2502.05171 / 2510.25741）参数效率最高的一种。项目使用了7.7T token 做预训练，同一组权重反复用 T 次。项目页的原话翻译过来是：增益来自 better knowledge manipulation。而不是 more knowledge storage——操纵知识，不是存储知识。

我个人比较倾向工程干净、能落地的 WeLM 这类路线，改动小且并行流清晰。

![四条路线在光谱上的就位图](02-four-routes-on-spectrum.png)

## 后训练和 agentic 任务的影响？

回到开头那篇论文上来——这条光谱最该被记住的，其实是一个负面的结果。

同一篇论文里，RL 确实能让 Qwen3-235B 形成使用 filler 的偏好。但论文的结论同样明确：RL 和 SFT 捏出的 filler 收益，无法继续在后续的长推理任务中继续受益。

13 模型横评中，Qwen3-235B 的计数 filler 涨点直接为零。如果你认为是模型参数空间中本来就藏有那些能被刺激涨点的东西，仅仅靠常规训练就能放大模型的能力的做法，其实被证实了并不是成立的。

这对天天调 prompt 的人不是好消息——**仅仅靠塞一些废话到输入里面这招，模型根本无法自己学会**，每次都得你手动去塞。而那种做法，对现在的 agentic 任务而言，无疑是一场灾难。

论文里还有个更深入的发现：Claude Opus 4.5 能在不牺牲主任务目标的情况下，暗暗地满足一个模运算约束。它做到了，但并不体现在任何一个 token 里。

测试时计算在训练侧的映照，可查看前文：[1,250 篇论文之后：AI 自己练自己，为什么只有两条线敢上生产](https://mp.weixin.qq.com/s/8O45vlW6bCqOlObyf2lF7Q).

## 隐思维链推理的最新进展
GPT-6 Astra 同时用了更短更省的 CoT——OpenAI 9 月的系统卡显示，同等 reasoning effort 下它的思维链明显短于 GPT-5.6 Sol；The Information 还在发布前报道它加了有限程度的循环深度。OpenAI 的 Pachocki 本人的说法是「限制了使用程度」。

这有点像是在这道光谱的中间，挑选了一个折中的做法，既有内部的循环，同时又继续使用当前的隐藏思维链技术。需要说明的是，目前只有媒体报道，加上本人帖子的部分承认，并不是官方渠道的确认。

所以，如果未来的计算不再完全落在显式的 token 上，你定位跑偏时，尝试去翻看的那个「思考过程」的做法，还有意义吗？你该依据什么，继续优化自己的 agent 行为？

如果你已经读到这里，欢迎点赞 👍、收藏 ⭐ 备用，转发给关心 AI 推理的朋友。关注「数解AI」，AI 原理和工程，慢慢深入拆解。


🔥 **热门文章**：

[KV缓存存进SSD：慢50倍的硬盘，为什么反而更快？](https://mp.weixin.qq.com/s/40BQ06eDTv4-2r8FmQ_rMA)  
[高维空间为什么全是壳？内积才是那把尺子](https://mp.weixin.qq.com/s/Nrfr-90Fpu3mFDML9s0d1Q)  
[高斯为什么二阶就够？非线性去哪了](https://mp.weixin.qq.com/s/gs_3y7JXuBLlzR5w6jW6fQ)  
[微软用 Go 重写 TypeScript，他一个人用 C++ 又写了一遍](https://mp.weixin.qq.com/s/GmPJAh8ERPkm64KzYirV2g)  
[学习率怎么自动调？Adam 优化器拆给你看](https://mp.weixin.qq.com/s/aSLVO-otvr2rxIU1kr2eAA)  
[DeepSeek-V4为何不用MLA？](https://mp.weixin.qq.com/s/MQEgbY16mLs-N7g2xKW1HQ)  

**参考资料与数字溯源**（以下来源均于 2026-11-17 检索核对）

1. *Not All LLM Reasoning is Visible in the Chain-of-Thought*（arXiv:2607.22925，https://arxiv.org/abs/2607.22925，v1 2026-07-24 / v2 2026-09-03，NYU+UMD+TogetherAI）：13 模型 × 3 合成任务；10-shot；filler = 计数 token「1–100」；Gemini 3 Flash 算术 51.0→61.7（+10.7pp）、乘法 +1.0；Opus 4.5 算术 +11.2 / 乘法 +10.0；Opus 4.6* 算术 +30.0（选择效应，非主数字）；负面结果原话「neither RL nor SFT produces a filler token benefit that persists at test time」；Claude Opus 4.5 隐藏约束实验
2. WeLM Hidden Decoding（论文 https://arxiv.org/abs/2607.08186；官方博客 https://welm.weixin.qq.com/posts/hidden_decoding_at_scale/，2026-07-14）：九基准全部为自测结果；n=4 单 batch 5.1×（80B）/ 4.4×（617B）；各流隐状态余弦 0.987→0.637→0.783；未确认上线微信产品线
3. Ouro 项目页（https://ouro-llm.github.io；论文 https://arxiv.org/abs/2510.25741 / https://arxiv.org/abs/2502.05171）：7.7T token 预训练；原话「gains come from better knowledge manipulation, not more knowledge storage」
4. 厂商现役定价表（https://platform.openai.com/docs/pricing / https://www.anthropic.com/pricing / https://ai.google.dev/gemini-api/docs/pricing / https://api-docs.deepseek.com/quick_start/pricing，2026-11-17 检索日刊例）：OpenAI / Anthropic 输出单价 = 输入 5×；DeepSeek 峰时 3–4×（峰谷价并存）；Gemini 3.5 Flash 输入 $1.50 / 输出 $9.00（6×，不计入 5× 口径）；Gemini 定价表「Output price (including thinking tokens)」
5. OpenAI《Learning to reason with LLMs》（https://openai.com/index/learning-to-reason-with-llms，2024-09）：「after weighing multiple factors including user experience, competitive advantage, and the option to pursue the chain of thought monitoring, we have decided not to show the raw chains of thought to users」
6. The Information 对 GPT-6 Astra「recurrent depth / looped transformers」的报道（2026-09，Astra 发布前两日）；Pachocki X 帖（2026-09-02，「limited the extent to which the looped Transformer architecture is used」/「限制了使用程度」）；Raschka 专文《GPT-6 Astra, Looped Transformers, and Hidden Reasoning》（https://magazine.sebastianraschka.com/p/gpt-6-astra-looped-transformers-and）转述核实；GPT-6 Astra 系统卡（2026-09）：同等 reasoning effort 下 CoT 明显短于 GPT-5.6 Sol
7. 前传与内链：《上下文压缩省了 77% token，为什么账单反而更贵？》（https://mp.weixin.qq.com/s/p-2YkAFT6sBwdU5_dw5O2g）、《1,250 篇论文之后：AI 自己练自己，为什么只有两条线敢上生产？》（https://mp.weixin.qq.com/s/8O45vlW6bCqOlObyf2lF7Q）
8. Anthropic 反蒸馏机制：2026-09 威胁情报报告（https://www.anthropic.com/threat-intelligence-report-september-2026，API 以 thinking signature 代替原始思维链返回）；Detecting and preventing distillation attacks（https://www.anthropic.com/news/detecting-and-preventing-distillation-attacks，分类器+行为指纹+访问控制）；2026-03-31 Claude Code 源码泄露曝光的 ANTI_DISTILLATION_CC（GrowthBook 开关 tengu_anti_distill_fake_tool_injection，服务器向系统提示注入假工具定义，污染被抓流量训练的数据）

#Latent思维链 #大模型原理 #AI推理 #数解AI
