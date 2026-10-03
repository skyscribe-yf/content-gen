# 五分之一，只对得上牌价 · 数字来源

核对日：2026-09-30。图上数字只来自 OpenAI 发布页正文、OpenAI 价目文档，以及 Artificial Analysis 文章里写明的句子。发布页的分数图没有读出绝对分，二级博客转述的 75.2%、$0.65 这类不进图。X / HN 互动数会变，不进图。

## 热帖

- HN 首页，2026-09-30 直接打开 `https://news.ycombinator.com/`：*GPT 6.1 Sol: Near-Astra intelligence for a fifth of the price*，`https://news.ycombinator.com/item?id=49896586`，链到 `https://openai.com/index/introducing-gpt-6-1-sol/`。查看时约 800 分、700 多条评论。只用来判断这句在被讨论。
- 同页另一条 AI 热帖是 *Livenerf: Has Opus 5.5 been nerfed yet?*（约 329 分）。仓库写明系列才跑到第 6/30 天，最早约 2026-10-24 才能下结论。这条不进本图。
- 同页 *Dots: Always-on agents* 约 479 分。同日发布，不是这句价格主张，不进本图。
- `openai.com` 直接抓取返回 403。发布页正文经 `https://r.jina.ai/https://openai.com/index/introducing-gpt-6-1-sol/` 于 2026-09-30 读取。价目不是从这篇转述来的。

## 发布页原句

标题句：Near-Astra intelligence for a fifth of the price。

正文原句：nearly matches GPT-6 Astra’s intelligence on agentic coding, computer use, and professional work at one-fifth of Astra’s standard input and output token prices。缓存读取 $0.10 / 百万 token，95% less than standard input pricing，50% less than GPT-6 Sol’s cached input pricing。

分榜原句，不把两句并成同一个思考档，除非原句自己写了：

- DeepSWE v1.1：matches Astra at roughly one-fifth of the cost，同时 eclipsing GPT-6 Sol’s best score by 6.4 percentage points at a lower reasoning effort and cost。6.4 个点这句挂在「更低思考档」上，不另写成某一个档的绝对分。
- GDP.pdf：比 Opus 5.5 with fallbacks 分更高，less than half the cost per task，across the tested reasoning settings。另句：approaches Astra at roughly one-fifth the cost per task。
- AutomationBench：medium 档比 Opus 5.5 高 2.2 个点，roughly a third of the cost。同一档比 GPT-6 Sol 高 4.8 个点。这节没写接近 Astra，也没写五分之一。脚注：Fable 5.1 的成本少算了 fallback，大约 40% 的任务发生过。这个 40% 不进图，避免和 6.1 的账单混。
- OSWorld 2.0 离线集，v2026.08.08，报的是 partial reward。max 档比 GPT-6 Sol 高 7 个点，less than half the cost。同一档离 Astra 2.1 个点，roughly one-seventh the cost per task。
- Terminal-Bench Science 0.1：max 档比 GPT-6 Sol 的分 more than doubles，成本不到一半。同一档单任务 $5.47，Opus 5.5 $23.21，Astra $23.80，over 75% lower cost than either。Astra 仍是测过的模型里最高，68.1%。6.1 Sol 和上一档 Sol 的绝对分，正文没给。
- 事实错误，内部评测，难例，不是日常：low 档从 11.4% 降到 7.7%，approximately 32%。各档离 Astra 不超过 1.9 个点，任务成本 less than one-fifth。美元数没给。
- 坏搜索不披露，max 档，故意挑的难题：6.1 Sol 2.1%，GPT-6 Sol 4.9%，Astra 1.5%，Luna 28.7%。

供应原句：即日起 Plus、Pro、Business、Enterprise、Edu 可在 ChatGPT Work 和 Codex 用。Chat 里还没有。API 名 `gpt-6.1-sol`。标准价 $2 / $0.10 缓存 / $10 输出，单位都是每百万 token。Ultrafast 随后几天到，Codex 里最高约 8 倍生成速度。Ultrafast 的价目正文没给，不进图。

## 价目

直接读取，2026-09-30：

- `https://developers.openai.com/api/docs/models/gpt-6.1-sol.md`
- `https://developers.openai.com/api/docs/pricing.md`

标准、短上下文（≤272K），每百万 token：

| 项 | gpt-6.1-sol | gpt-6-astra | gpt-6-sol |
| --- | ---: | ---: | ---: |
| 输入 | $2.00 | $10.00 | $2.00 |
| 缓存读取 | $0.10 | $1.00 | $0.20 |
| 缓存写入 | $2.50 | $12.50 | $2.50 |
| 输出 | $10.00 | $50.00 | $10.00 |

长上下文（输入超过 272K，**整单**按长上下文价，不是只给超出部分加价）：

| 项 | gpt-6.1-sol | gpt-6-astra | gpt-6-sol |
| --- | ---: | ---: | ---: |
| 输入 | $4.00 | $20.00 | $4.00 |
| 缓存读取 | $0.20 | $2.00 | $0.40 |
| 缓存写入 | $5.00 | $25.00 | $5.00 |
| 输出 | $15.00 | $75.00 | $15.00 |

模型页还写：缓存读取是未缓存输入的 5%；缓存写入是未缓存输入的 1.25 倍；超过 272K 的请求，输入和缓存 ×2、输出 ×1.5，且按整单。Fast 模式是标准价的 2 倍。Batch 和 Flex 是标准价的 50%。区域处理加 10%（2026-03-05 及之后发布、且适用的模型）。同档比较时，这些倍数不改变和 Astra 的比例。图上的牌价是标准、短上下文。

上一档 Sol 的输入输出降价，写在 `https://openai.com/index/introducing-gpt-6-sol-and-luna/`：相对 GPT-5.6 的促销价，输入 $4→$2，输出 $20→$10，50% cheaper。那是上一档的事。6.1 相对这一档，输入输出牌价没再动。

## 算出的差

- 2 / 10 = 0.2，10 / 50 = 0.2。标准输入、标准输出相对 Astra 正好五分之一。
- 0.10 / 1.00 = 0.1。缓存读取相对 Astra 是十分之一，不是五分之一。
- 0.10 / 0.20 = 0.5。相对上一档 Sol，缓存读取少 50%。和发布页那句一致。
- 0.10 / 2.00 = 0.05，1 − 0.05 = 0.95。相对自己的标准输入少 95%。和发布页那句一致。
- 2.50 / 12.50 = 0.2。缓存写入相对 Astra 仍是五分之一，相对上一档 Sol 没动。
- 长上下文：4 / 20 = 0.2，15 / 75 = 0.2，0.20 / 2.00 = 0.1，5 / 25 = 0.2。比例没破。0.20 / 0.40 = 0.5，长缓存读取相对上一档 Sol 也是砍半。
- 5.47 / 23.80 = 0.2298319328 = 23.0%。1 − 该数 = 77.0%。官方写 over 75% lower，对得上。五分之一应是 23.80 × 0.2 = 4.76，实际贵 $0.71。
- 5.47 / 23.21 = 0.2356742783 = 23.6%。1 − 该数 = 76.4%。同样 over 75%，同样不是五分之一。
- (11.4 − 7.7) / 11.4 = 0.3245614035 = 32.5%。官方写 approximately 32%。两套都在图上，不混成一个数。

## Artificial Analysis

`https://artificialanalysis.ai/articles/gpt-6-1-sol-replaces-gpt-6-sol-after-just-7-days-with-near-astra-intelligence`，经 jina 于 2026-09-30 读取。这是他们的测量，不是 OpenAI 的表。

正文写明、图上采用的：

- 价目和 GPT-6 Sol 一样是 $2 / $10，缓存读取折扣从 90% 升到 95%。90% 对得上 0.20 / 2.00，95% 对得上 0.10 / 2.00。
- Intelligence Index：比 Astra 低 1 分；比 GPT-6 Sol 高 4 分；比 GPT-5.6 Sol 高 5 分。绝对分正文没给，不进图。标题里的「7 天」这篇不另核 Sol 的发布日，不进图。
- max 档，指数单任务：$0.72 对 Astra $3.26，他们写成不到四分之一。对 GPT-6 Sol $1.05，少 31%。对 GPT-5.6 Sol $1.99，少 64%。
- 输出 token 比 GPT-6 Sol 多大约 10% 到 30%。这句和「任务成本少 31%」不要捏成一个原因。输出牌价没降。
- Coding Agent Index：max 档比 GPT-6 Sol 高 3 分，比 Astra 低 2 分。xhigh 比 Astra 高 1 分，任务成本不到 Astra 的 15%；比 max 高 3 分。美元数正文没给，图上只保留这个比例和他写的分差。

算出的、他们没写成这个小数的：

- 0.72 / 3.26 = 0.2208588957 = 22.1%。四分之一是 0.815，五分之一是 0.652。0.72 低于 0.815，高于 0.652。所以「不到四分之一」对，「五分之一」不对。
- 1 − 0.72 / 3.26 = 77.9%。这是另一张账单上的降幅，不和科学榜的 77.0% 写成同一个数。
- 0.72 / 1.05 = 0.6857142857，少 31.4%。他们写 31%。
- 1 − 0.72 / 1.99 = 0.6381909548 = 63.8%。他们写 64%。

## 不进图

- HN / X 的点赞、转发、浏览
- 发布页图表上没被正文写出来的绝对分和单任务美元，包括二级博客读图得到的 DeepSWE 75.2%、$0.65、OSWorld $1.27 / $9.44
- Ultrafast 的价格；Pro 500；订阅倍数从 20x 改到 10x。发布页正文和价目文档都没写
- Dots、Livenerf
- AA 标题里的「7 天」，以及 AA 正文没给绝对分的指数
- Fable fallback 的大约 40%。那是成本脚注，不是 6.1 的测量
