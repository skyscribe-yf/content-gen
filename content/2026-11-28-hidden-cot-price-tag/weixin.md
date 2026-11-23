---
title: "AI 把思维链藏起来，为什么反而收你 5 倍的钱？"
author: "数解AI"
date: "2026-11-28"
type: "article"
series: "Latent 思维链"
digest: "隐藏思维链不是帮你省钱，而是按输出计费的加价项；盘点四家现役厂商的思维链可见性与五道坎。"
cover: "00-cover.png"
keywords: ["隐藏思维链", "推理计费", "思维链监控", "Latent思维链", "API定价"]
wechatUrl: ""
---

为了弄清自己的 agent 到底烧多少 token，我把 202 次会话 compaction 翻了个底朝天。那笔账算的是「压缩省了多少」。但同一本账里漏了一半：模型思考用的 token，我看不见，它却在计费。

Google 定价页每张模型卡都标着「Output price (including thinking tokens)」。

翻完那 202 次 compaction 记录时，我盯着压缩前后省下来的 token 数字算得挺顺，看到「思考 token 也计费」这句才反应过来，我只盯了上下文窗口的账，没把思考过程算进同一本账里。一笔漏算的账，和一张四家厂商的对比表——撞的是同一个东西：「不给你看」从来不省钱，它只是个加价项。

## 1. 我审计了 202 次压缩的账，才发现漏算了一半

隐藏思维链的 token 照常逐个生成、照常按输出单价计费，只是 API 响应里不再把原始推理过程吐给你。

我当时审 compaction 算的是上下文怎么省，可一旦切到推理模型，输出侧的思考用量才是另一本账，这本账的前一半我在[《上下文压缩省了 77% token，为什么账单反而更贵？》](https://mp.weixin.qq.com/s/p-2YkAFT6sBwdU5_dw5O2g)里算过。

![一本账的三段计费结构](03-billing-structure.png)

拿现役主流刊例来看，输出单价普遍是输入的 5 倍左右。OpenAI 现役 GPT-6.2 家族多数为 5 倍输出。Anthropic 的 Fable 5.2/Opus 5.5/Sonnet 5.5/Haiku 5.5 也都是 5 倍。

Google 的 Gemini 4 家族与 Gemini 3.8 Flash 同样是 5 倍。Google 定价页明确带上了 2026-12-01 和 2027-01-01 两个调价时点。DeepSeek 两款峰时倍率：`deepseek-v4-pro` 3 倍，`deepseek-flash` 4 倍。谷时全项半价。峰时为周一至周五 UTC 01:00–04:00 与 06:00–10:00，法定节假日除外，周末整日谷时。

据我整理的研究笔记，单次难 query 可能烧掉 1 万以上的隐藏思考 token。总成本很容易被推到 3–6 倍。平时跑普通任务时，隐藏思考 token 偶尔拉高一截，账单波动还不算太刺眼，但真碰上重推理场景时，输出侧的用量感就会明显上来。

## 2. 四家里，只有一家把思考过程返回给你

计费讲完了，再看接口这边，四家现役厂商的文档态度非常分明。不是「只有 DeepSeek 敢给你看」。另外三家的官方文档都写了不返回原始推理，这是厂商在产品与安全上主动做的选择，不是技术做不到。

![四家思维链可见性对比](01-vendor-visibility.png)

- **DeepSeek**：思维链通过 `reasoning_content` 字段与 `content` 同级返回。默认开启 `thinking mode`，`effort = high`。`deepseek-v4-pro` 与 `deepseek-flash` 均适用。官方未声明该字段与内部推理 token 逐字对应。
- **OpenAI**：官方文档说得很直接，不暴露模型发出的原始推理 token。摘要需显式通过 `summary` 参数开启。多轮对话则仅回传加密后的推理 token 供后续调用。
- **Anthropic**：5.x 系列默认采用 `omitted`（`thinking` 字段为空）。4.6 及更早版本默认 `summarized`。
- **Google**：官方文档写明默认只返回最终输出，可通过 `thinking_summaries` 开启思考摘要。`thought signature` 则是内部推理的加密表征。

### 为什么三家都不给看原始思维链

OpenAI 的推理模型 o1 发布时，官方文章就写明了权衡过程。用户体验、竞争优势、保留思维链监控的选项都算过，最后决定不向用户展示原始思维链。

日常调接口时我用 DeepSeek 的次数不少，看不到完整思维链的时候，我主要靠看最终输出的完整度、响应耗时和重试次数来猜它有没有跑偏。Anthropic 说得更直白。原话：「No display setting returns the raw chain of thought」。

## 3. 另外三家不是不上，是五道坎

为什么主流厂商普遍收紧原始思维链的可见性，同时在潜在推理（latent reasoning）上保持克制？把「收紧」拆开，卡着的是五道坎。

![五道坎的两拨分布](02-five-obstacles.png)

### 五道坎分两拨：拦可见性的和拦 latent 的

第一道坎是 **CoT 监控的安全刚需**。OpenAI 的 Pachocki 在 2026-09-02 发了条 X（原 Twitter）帖。TNW 四天后逐字转述了它。核心句是防止一场「race into unmonitorability」。更早的 2025-07 四十机构立场论文（`arXiv:2507.11473`）称思维链可监控性是「新的且脆弱的机会」。

一旦思维链藏起来或变成隐式向量，安全审计和对齐检查就没处下手了。这跟[《机械臂蹭一下桶盖，成功率高10%：奖励函数才是AI钻空子的源头》](https://mp.weixin.qq.com/s/boIPBlmyX2ahoFYnEVLjxw)里那个钻空子的风险，在监控这边正好对上。

latent 这边已经有实证威胁——ICLR 2026 有研究触及输出对齐与 latent 携带不对齐的风险。隐式表征里藏着没法一下读出来的偏差。

第三、四道坎都是落地侧的——循环（looped）结构与流水线并行不兼容，KV 缓存的语义也得重新想一遍。收益也不确定。独立研究者 Sebastian Raschka 拆解过 OpenAI 的 Astra（GPT-6.2 家族）。媒体报道称它带了有限循环深度，他的结论是提升主要来自训练，不是循环结构。结构本身并不是灵丹妙药。

隐藏思考 token 照常按输出计费，本身就是一块可观的收入来源。五道坎里最实的那道不是技术，是第五条——「不给你看」本身就是门生意。

在我看来，五条里「计费结构」和「监控刚需」最现实，有些看似高深的架构争论在真实账单面前反而是次要的。如果哪天有厂商把「完整可见」单列成高价卖点，我大概率只会为确实需要深度排障的特定任务买单，不会无条件加价。

## 4. 国产阵营其实还没上桌

再说国产模型这边，现实情况比不少人想象的更克制。`DeepSeek-V4-Pro-0813` 就是 API 侧的 `deepseek-v4-pro`。直接读它的 Hugging Face 配置：61 层架构。配置里没有 `looped`、`latent`、`recurrent`、`depth`、`recursion` 类参数。

唯一邻接项是用于训练期与投机解码的 MTP（`num_nextn_predict_layers=1`）。这并非测试时 latent reasoning。`GLM-5.2` 与 `Kimi K2.6` 的配置里同样没有这类参数。`Qwen3.5` 仓库为 gated（受限访问）状态，没读到相关参数。

所以别以为国产已经在搞 latent reasoning 了。目前只有 DeepSeek 一家在「可见性」上做了不同的选择，而它选的是「给你看」。国内前沿规模的 latent reasoning 探索，代表是微信 AI 的 WeLM。论文 `2607.08186`，规模 80B/617B。官方博客将其定位为研究与探索，尚未确认上线产品线。

面对 WeLM 这种「研究博客、先看论文」的国产进展，我通常会先翻一遍论文看方法是否扎实，真要落到日常工作流里，还是得等稳定可用的接口或工程方案出来再说。

## 5. 你依赖的那条监控通道，只剩一家还给

回头看我审计那 202 次 compaction 的初衷，无非是想搞清楚 agent 到底花了多少成本。但对工程落地来说，比少算几个 token 更关键的是监控通道。想靠读思维链弄清 agent 为什么跑偏的时候，四家里只剩一家还给你看。

### 监控通道收窄后的工程落点

「不给你看」和「根本没有显式思维链」是两回事，这在《加入100个dummy token，算术能力飞涨10.7分：AI思维链正在悄然发生着变化》里已有系统梳理，而「思维链写得头头是道、最终答案却对不上」也是实际排障中会碰到的现象。如果「可见」只剩一家还给，我不会为了「能看」就盲目换掉整套主力模型，更多还是靠结构化校验、工具调用日志和回归测试去兜底。

如果你的工作流靠读思维链判断 agent 有没有跑偏，这件事从哪一档开始失效？

如果你已经读到这里，欢迎点赞 👍、收藏 ⭐ 备用，转发给关心 AI 推理的朋友。关注「数解AI」，AI 原理和工程，慢慢深入拆解。

🔥 **热门文章**：

[KV缓存存进SSD：慢50倍的硬盘，为什么反而更快？](https://mp.weixin.qq.com/s/40BQ06eDTv4-2r8FmQ_rMA)  
[高维空间为什么全是壳？内积才是那把尺子](https://mp.weixin.qq.com/s/Nrfr-90Fpu3mFDML9s0d1Q)  
[高斯为什么二阶就够？非线性去哪了](https://mp.weixin.qq.com/s/gs_3y7JXuBLlzR5w6jW6fQ)  
[微软用 Go 重写 TypeScript，他一个人用 C++ 又写了一遍](https://mp.weixin.qq.com/s/GmPJAh8ERPkm64KzYirV2g)  
[学习率怎么自动调？Adam 优化器拆给你看](https://mp.weixin.qq.com/s/aSLVO-otvr2rxIU1kr2eAA)  
[DeepSeek-V4为何不用MLA？](https://mp.weixin.qq.com/s/MQEgbY16mLs-N7g2xKW1HQ)  

**参考资料与数字溯源**（以下来源均于 2026-11-22 检索核对）

1. **DeepSeek Thinking Mode 官方文档**（`https://api-docs.deepseek.com/guides/thinking_mode`，检索日期：2026-11-22）：明确 `reasoning_content` 与 `content` 同级返回思维链内容，默认开启 thinking mode 且默认 `effort = high`，适用于 `deepseek-v4-pro` 与 `deepseek-flash`。
2. **DeepSeek API 定价说明**（`https://api-docs.deepseek.com/quick_start/pricing`，检索日期：2026-11-22）：记录 `deepseek-v4-pro` 峰时缓存命中/未命中/输出单价（$0.044 / $1.32 / $3.96）与 `deepseek-flash` 峰时单价（$0.006 / $0.3 / $1.2），谷时全项半价。
3. **OpenAI Reasoning 官方指南**（`https://platform.openai.com/docs/guides/reasoning`，检索日期：2026-11-22）：明确不暴露原始推理 token，摘要需通过 `summary` 参数开启，多轮回传加密推理 token。
4. **OpenAI API 定价页**（`https://platform.openai.com/docs/pricing`，检索日期：2026-11-22）：收录现役 GPT-6.2 家族等模型刊例（如 `gpt-6.2-astra` $8 / $40、`gpt-6.2-sol` $2 / $10），多数主力型号输出单价为输入的 5 倍。
5. **OpenAI o1 发布说明（Learning to Reason with LLMs）**（`https://openai.com/index/learning-to-reason-with-llms`，检索日期：2026-11-22）：载明权衡用户体验、竞争优势与思维链监控选项后决定不向用户展示原始思维链。
6. **Anthropic Thinking 官方文档与定价页**（`https://platform.claude.com/docs/en/build-with-claude/thinking`、`https://www.anthropic.com/pricing`，检索日期：2026-11-22）：载明「No display setting returns the raw chain of thought」及 5.x 默认 `omitted`、4.6 及更早默认 `summarized`；Fable 5.2 / Opus 5.5 / Sonnet 5.5 / Haiku 5.5 均为 5 倍输出。
7. **Google Gemini API Thinking 官方文档与定价页**（`https://ai.google.dev/gemini-api/docs/thinking`、`https://ai.google.dev/gemini-api/docs/pricing`，检索日期：2026-11-22）：载明默认只返回最终输出，`Output price (including thinking tokens)` 及处理计费规则，并含 2026-12-01 与 2027-01-01 调价时间点。
8. **arXiv:2507.11473 立场论文**（`https://arxiv.org/abs/2507.11473`，检索日期：2026-11-22）：2025-07 四十机构立场论文称思维链可监控性为「a new and fragile opportunity」。
9. **TNW 对 Pachocki X 帖的报道**（2026-09-04，URL 未存档）：逐字转述「I want to prevent a race into unmonitorability kicked off by confused reporting.」。
10. **Sebastian Raschka《GPT-6 Astra, Looped Transformers, and Hidden Reasoning》**（`https://magazine.sebastianraschka.com/p/gpt-6-astra-looped-transformers-and`，2026-09；转录自 2026-11-22 篇已核参考资料）：分析 Astra 提升主要来自训练而非循环结构。
11. **ICLR 2026 latent 对齐相关研究**（据作者 latent reasoning 研究笔记归纳，二手，未核到具体论文条目，检索日期：2026-11-22）：输出对齐与 latent 携带不对齐风险的出处。
12. **作者 latent reasoning 研究笔记**（2026-11 整理，二手归纳，非官方来源）：难 query 隐藏思考 token 用量与总成本 3–6 倍口径的来源。
13. **WeLM Hidden Decoding 论文与官方博客**（论文 `https://arxiv.org/abs/2607.08186`；官方博客 `https://welm.weixin.qq.com/posts/hidden_decoding_at_scale/`，2026-07-14；转录自 2026-11-22 篇已核参考资料）：微信 AI 的 WeLM 80B/617B 研究探索材料，官方博客定位研究与探索、未确认上线产品线。同条记录 `DeepSeek-V4-Pro-0813`、`GLM-5.2`、`Kimi K2.6`、`Qwen3.5` 的 Hugging Face 公开配置核查（2026-11-22 直读）。

#Latent思维链 #大模型原理 #AI推理 #数解AI
