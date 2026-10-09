# 事实来源

核对时间：2026-10-08。贴图只用下面能对上原文的句子。单价都是标准档、每百万 token、美元。

## 选题档位

圈内大事件里的钱包题材，接近 09-07 ollama 峰谷价、08-07 opencode 那档：品牌词在前，90% 能单独转发，还能跟 Luna 站队。窗口是昨天发布、今天次日。普通人 3 秒能说出：Haiku 5.5 标价砍了 90%，账单没这么爽。

同日扫到、本篇不用：

- ChatGPT 免费档和 Go 从 10 月 8 日起换 GPT-6 Luna，付费档 10 月 7 日已是 GPT-6 Sol，并上线 Intelligent UI。出圈，但是另一篇。今天不跟价格刀绑在一起。
- 今天已有长文稿《Anthropic 实测多智能体强 90%》和《微软用 Go 重写 TypeScript》。题材不同，可以同发。
- Meta / 微软削减内部 Claude，是 10 月 5 日的报道，窗口过了，公司没确认。

## 官方：Haiku 5.5

- Anthropic，2026-10-07，*Introducing Claude Haiku 5.5*  
  https://www.anthropic.com/claude-haiku-5-5  
  - 「On average, it now costs around 75% less to run.」  
  - 10 万 token 以内的任务，约占上一代 Haiku 请求的 90%。  
  - 脚注 2：「priced 90% lower than Claude Haiku 4.5 for requests up to 100,000 tokens, and 50% lower for requests over 100,000 tokens. On Haiku 4.5, 90% of requests fell into the former category.」计算里计入了新分词器：同样的活会多用一些 token。  
  - 价目表（每百万 token，10 万以内 / 超过 10 万）：  
    缓存读取 $0.01 / $0.05；5 分钟缓存写入 $0.125 / $0.625；输入 $0.10 / $0.50；输出 $0.50 / $2.50。  
  - Haiku 4.5：缓存读取 $0.10，5 分钟缓存写入 $1.25，输入 $1.00，输出 $5.00。  
  - 同一天：「lowering the price of cache reads on Claude Sonnet 5.5. Cache reads now cost 50% less: $0.10 per million tokens rather than $0.20.」因此「reduces the cost of Sonnet 5.5 on most agentic tasks by around 20%.」  
  - 发布页自己的对照表（Anthropic 跑的，不是第三方）：OSWorld 2.1 离线子集 Haiku 5.5 72.4%，GPT-6 Luna 48.9%，Haiku 4.5 15.7%。Terminal-Bench 4.0：39.2% / 16.4% / 0.0%。正文不把这些分数当封面，只在文末当站队弹药，并标明是他们自己的表。

- 平台文档，2026-10-08 抓取  
  https://platform.claude.com/docs/en/about-claude/pricing  
  - 两行价目：「Claude Haiku 5.5 (for prompts up to 100,000 tokens)」与「for prompts over 100,000 tokens」。  
  - 「Claude Haiku 5.5 is priced by prompt length: a prompt of over 100,000 tokens pays higher prices.」  
  - 分词器：「This tokenizer produces approximately 30% more tokens for the same text. The exact increase depends on the content and workload shape.」Claude 4.7 及之后用这套；Haiku 4.5 用旧的。  
  - 模型页同句：同样一段字，大约比 Haiku 4.5 多计 30% token。  
    https://platform.claude.com/docs/en/models/haiku-5-5/overview

官方把超过 10 万 token 的提示单列一张价目表，没有写「只对超出的那一段加价」。图里按这两张价目表画单价，不自算一笔整单美元，避免把计费细节说死。

## 官方：GPT-6 Luna

- OpenAI 模型页，2026-10-08 抓取  
  https://developers.openai.com/api/docs/models/gpt-6-luna  
  - 短档：输入 $0.10，缓存读取 $0.01，缓存写入 $0.125，输出 $0.50。  
  - 「Prompts with more than 272K input tokens are priced at 2x input and cache rates and 1.5x output for the full request.」  
  - 所以超过 27.2 万输入 token，整单变成输入 $0.20、输出 $0.75。这句是 OpenAI 写明的整单重算，跟 Haiku 的两档价目不是同一种表述。

- 价目总表同一天抓取  
  https://developers.openai.com/api/docs/pricing  
  - gpt-6-luna 短档 / 长档：输入 $0.10 / $0.20，缓存读取 $0.01 / $0.02，缓存写入 $0.125 / $0.25，输出 $0.50 / $0.75。

短档四项里，Haiku 5.5（≤10 万）和 Luna（≤27.2 万）的输入、输出、缓存读取、5 分钟缓存写入，数字相同。

## 不写进正文的说法

- 不说「账单差 12 倍」。那是转帖，不是这两张家的价目。  
- 不把 90% 写成所有请求都便宜 90%。官方平均是大约 75%，90% 只覆盖 10 万 token 以内的标价。  
- 不把 30% 写成每段字都正好多 30%。官方写的是大约，而且看内容。  
- 不自算「15 万 token 整单贵 5 倍」。单价是 5 倍，整单算法官方没写成 Luna 那种 full request。  
- 不写「我跑了一下」。这轮没有作者实测。  
- 不把 Anthropic 自己的榜写成第三方已复核。  
- 不画真人脸，不画两家商标。
