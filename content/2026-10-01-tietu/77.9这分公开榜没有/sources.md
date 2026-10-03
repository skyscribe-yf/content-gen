# 77.9% 这分，公开榜没有 · 数字来源

核对日：2026-10-01。图上数字只来自 Google 博客、Gemini 4 Argon 评测 PDF、Gemini 3.8 Flash 模型卡、Artificial Analysis 文章和模型页、DeepSWE 公开榜、FrontierSWE 公开榜。X 互动数会变，不进图。X 原话进正文时标明是评论，不当成测量。

## 热帖（只用来判断在被讨论）

- Google DeepMind 官宣，2026-09-30：https://x.com/GoogleDeepMind/status/2105388084154056939
- Sundar 官宣，同日：https://x.com/sundarpichai/status/2105387952478277979
- Artificial Analysis 评测帖，同日，指数 53、折扣期单任务 $1.99、输出 62k 对 27k：https://x.com/ArtificialAnlys/status/2105392625788637299
- Tanvir，2026-10-01：把 77.9% / Opus 74.2% / Astra 74.1% 三行贴出来，接着写 “Sounds impressive. But there’s one problem… You can’t use it yet.” https://x.com/mrtanviir/status/2105599940936204320
- SemiAnalysis 线程，2026-09-08，把 3.8 Flash 和 Muse Spark 1.3 称为 “two of the most clearly benchmaxxed models we've seen yet”。2.1 的题公开，提到 4.0 对不上。第 4 帖写 “Gemini 3.8 Flash on DeepSWE is another good example. Clearly, Datacurve made a ton of money selling Google DeepSWE-shaped tasks.” 买卖这句是他们的说法，正文标明没核到合同，不进图。https://x.com/SemiAnalysis_/status/2097112791471522292
- Davey Alba / 彭博，2026-09-30：榜和真用有落差，包括某些写代码的活；内部对有没有追上 OpenAI、Anthropic 意见不一。匿名信源。回复里有 Google 工程师说相反。两句都不进图。https://x.com/daveyalba/status/2105398718178443512
- 也有人替 Google 说话：3.8 Flash 冲上 DeepSWE 时喊榜饱和，别人冲上去喊 SOTA，Argon 一上来又喊饱和。立场，不是测量，不进图。https://x.com/HarshithLucky3/status/2105424982071541888

## Argon · DeepSWE

博客，2026-09-30，https://blog.google/innovation-and-ai/models-and-research/gemini-models/gemini-4-argon/

- 写 DeepSWE v1.1 新 SOTA，77.9%。博客这句没写「自己跑的」。
- 还没公开。先给 Fairwind 里的可信测试者。开发者、企业和消费者随后，从付费 API 和 Google AI Ultra 开始。
- 首发价 $2 / $10 每百万 token，缓存输入 95% off。脚注：introductory period 结束后 $4 / $20。结束日没写。
- 输出上限从 64K 提到 1M。

评测 PDF，2026-10-01 读取：https://storage.googleapis.com/deepmind-media/gemini/gemini_4_argon_model_evaluation.pdf

- 第 2 页：DeepSWE v1.1 的 Argon 分是 self computed，用 mini-swe-agent。Astra 来自 Datacurve 公开榜。Fable 5.1 和 Opus 5.5 来自各自系统卡。各家取公开榜上最高思考档。
- 第 2 页：Terminal-bench 4.0 的 Argon 分是 self computed，其他模型来自公开榜。
- 第 2 页：FrontierSWE 来自 Proximal 公开榜。这句没写 Argon 自评。
- 第 5 页表，2026 年 10 月：

| 榜 | Argon | Astra | Fable 5.1 | Opus 5.5 |
| --- | ---: | ---: | ---: | ---: |
| DeepSWE v1.1 | 77.9% | 74.1% | 67.4% | 74.2% |
| FrontierSWE v2 | 55.0% | 65.5% | 56.3% | 62.3% |
| Terminal-bench 4.0 | 57.4% | 58.2% | 57.9% | 66.4% |

算出的差：

- 77.9 − 74.1 = 3.8 个点。
- 65.5 − 55.0 = 10.5 个点。
- 66.4 − 57.4 = 9.0 个点。
- 58.2 − 57.4 = 0.8 个点。

DeepSWE 公开榜，2026-10-01 打开 https://deepswe.datacurve.ai/ ，页头写 updated September 22, 2026。Best 视图没有 Argon。

- gpt-6-astra [xhigh] 74%±3%
- gemini-3.8-flash [high] 74%±1%
- 全员 mini-swe-agent

公开榜页面是 74%，不是 74.1%。他们表上的 74.1% 是公开榜最高档的未四舍五入写法，差 0.1，不另作一张榜。±3 的上沿按页面写法大约 77%。77.9 − 77 = 0.9，图上写「不到 1 个点」。Argon 没给区间。若中心其实是 74.1，上沿大约 77.1，差 0.8，仍是不到 1 个点。不写成统计显著。

## FrontierSWE 公开榜

2026-10-01 打开 https://frontierswe.com/ ，Best 视图：

- GPT-6 Astra 65.5%
- Claude Opus 5.5 62.3%
- Gemini 4 Argon 55.0%
- 星号：Cache hit rate is much lower due to a non-production setting.

和 PDF 表上的 55.0% / 65.5% 一致。不是全榜垫底（同页 GLM-5.3 是 30.2%）。图上只写比 Astra 低 10.5，以及自家四家表里垫底。

## 3.8 Flash 前科

模型卡，https://deepmind.google/models/model-cards/gemini-3-8-flash/ ，2026-10-01 读取表：

| 榜 | 3.8 Flash | Opus 5 | GPT-5.6 Sol |
| --- | ---: | ---: | ---: |
| DeepSWE v1.1 | 73.7% | 74.0% | 72.7% |
| Terminal-bench 2.1 | 89.4% | 89.1% | 88.8% |
| Terminal-bench 4.0 | 19.1% | 51.8% | 37.3% |

3.8 Flash 评测 PDF，https://storage.googleapis.com/deepmind-media/gemini/gemini_3-8_flash_model_evaluation.pdf ：

- DeepSWE v1.1：3.8 Flash 是 self computed，mini-swe-agent，high。
- Terminal-bench 2.1：Gemini 自家分 self computed，其他模型来自公开榜和 Artificial Analysis。
- Terminal-bench 4.0：来自官方公开榜。

所以 89.4% 是自己跑的，19.1% 是公开榜。51.8 − 19.1 = 32.7 个点。89.4 和 19.1 不是同一套题，图上不写成「掉了 70.3 个点」。

公开 DeepSWE 后来给 3.8 Flash 的是 74%±1%，和发布时自评 73.7% 差 0.3，算对得上。Argon 的 77.9% 还没走完这一步。

## Artificial Analysis

3.8 Flash 发布稿，2026-09-02：https://artificialanalysis.ai/articles/gemini-3-8-flash

- high 档智力指数 59，比 3.7 Flash 高 3 分。
- 单任务 $0.58。

指数 v4.3 说明，2026-09-07：https://artificialanalysis.ai/articles/artificial-analysis-intelligence-index-v4-3

- Terminal-Bench 从 2.1 换成 4.0。
- 用留出题的 AutomationBench-AA 换掉 τ³-Banking。私有题权重 40% → 45%。
- 这篇没单列 3.8 Flash 的新指数。

3.8 Flash 模型页，2026-10-01：https://artificialanalysis.ai/models/gemini-3-8-flash

- 指数 v4.3.2，high，41。
- 单任务 $1.24。
- 对比页 Terminal-Bench 4.0：19.7%。https://artificialanalysis.ai/zh/models/releases/comparisons/gemini-3-8-flash-vs-kimi-k3

59 和 41 不是同一套题。图上写「尺子换了」，不写「同一张卷掉了 18 分」当唯一读法。$0.58 和 $1.24 同样跨了这次换尺，不读成牌价涨了。1.24 / 0.58 = 2.14，不进图。

Argon 文章，2026-09-30：https://artificialanalysis.ai/articles/gemini-4-argon-google-top-three-labs

- high 指数 53，打平 Astra max 53，高于 Sol max 52。
- 上一代非 Flash，3.1 Pro Preview，指数 30。53 − 30 = 23。文中写 over 7 months 来第一款 Flash 以上的闭源模型。
- 折扣期单任务 $1.99，Astra $3.26。他们写 60%。1.99 / 3.26 = 0.6104 = 61.0%。
- 折扣结束 $3.98。3.98 / 3.26 = 1.2209，他们写大约 1.2 倍。图上写 1.22 倍。
- 输出 token 平均 62k 对 Astra 27k。62 / 27 = 2.296，图上写 2.30 倍。
- 还没公开。50% 折扣是首发促销。
- 同一篇两处口径：一处写结束日未确认，另一处写 $2 / $10 at least one month。Google 脚注也没写死日期。图上不锁「一个月」。
- AA-Omniscience：幻觉率 15%，Astra 51%，Sol 54%。准确率 50%，比 3.1 Pro Preview 低 5 个点，比 Astra 63% 低 13 个点。综合分 42，Astra 43，Sol 42。
- Terminal Bench 4：Argon 57%，排在 Sonnet 5.5 64%、Opus 5.5 60%、Astra 59% 后面。和 Google 表的 57.4% / 58.2% / 66.4% 不是同一处测量。图上只用 Google 表，这组不并进去。
- AutomationBench-AA 正文页写 78%，推文曾写 77.5%。Google 博客的 Zapier AutomationBench 是 51.3%。同名两张榜，本图不采用，避免和 DeepSWE 抢主数字。
