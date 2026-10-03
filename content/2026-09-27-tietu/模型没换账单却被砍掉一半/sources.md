# 模型没换，账单却被砍掉一半 · 数字来源

核对日：2026-09-27。图上数字都来自下面论文原文或官方榜，不采用解说帖里的「能力没掉」「同一套 Harness 砍半」这类没写对照对象的说法。Harness 不译成「壳」。X 互动数是查看当时的公开计数，会变，不进图。

## 这周 X 上实际在传的几篇

查看时（2026-09-27）公开计数，只用来判断哪几篇在被讨论，不进图：

| 帖 | 时间 | 赞 | 收藏 | 浏览 |
| --- | --- | --- | --- | --- |
| @alex_verem 解说 SoL-Pi | 09-23 | 736 | 1,206 | 50,117 |
| @omarsar0 解说 WFM | 09-23 | 487 | 628 | 31,874 |
| @omarsar0 解说 Taste-Bench | 09-25 | 183 | 186 | 15,593 |
| @dair_ai 解说 JitMem | 09-26 | 141 | 140 | 11,744 |
| @arXivBangers 解说 JAZ | 09-26 | 68 | 50 | 3,342 |

收藏第二的 WFM（arXiv:2609.18182，09-16）是另一条路：给链接起来的 wiki 训检索模型，摘要写分布式训练加速 10.5 倍。它在改模型，不和下面三篇并成一句，不进图。

## 账单：SoL-Pi

- 2026-09-17，*SoL-Pi: Recursively Scaling Auto-Research Loops for Efficient Agent Harness*
- https://arxiv.org/abs/2609.20519
- HTML：https://arxiv.org/html/2609.20519
- 单位：NVIDIA、NTU、MIT

搜索规模（正文，不是摘要的约数）：

- 外层搜索从 152 个方向开始。引言写的是大约 150，图上用 152。
- 可执行环境 535 个：495 个仓库任务 + 40 个合成任务。引言写大约 500。
- 3,000 多次运行，6 万多次 agent–环境交互。论文写的是 more than，不是正好 3,000 / 60,000。
- 活下来的四个机制：Action Fusion、Online Context Compact、ObservationPack、Evidence-Preserving Reducer。

EdgeBench 口径：

- 公开 51 题，全榜 134 题。评测用的是公开集。
- 这 51 题里，11 题用来单向验收已经冻住的候选，40 题留作泛化。图上的分数是 51 题公开集，不是那 40 题单独的数。验收结果不回流进搜索。

对 Pi（它改的那套 Harness，不要和「砍一半」混成一句）：

- GPT-5.6 Sol，省钱档（四机制全开）：token 1.10B，比 Pi 少 49.0%；分数留 93.7%（论文写 42.0 对 44.8）。表 4 对应 42.003 对 44.833，费用 $894 对 $1,339，少 33.2%。
- Opus 5，同一套从 Sol 搬过去，不重新搜：token 少 44.7%，API 费用少 33.5%（$1,158 对 Pi 的 $1,741），分数留 94.3%（42.224 / 44.756）。

对原生 Harness（图上的「砍一半」只指这组）：

- 图 1 说明：相对 Codex + GPT-5.6 Sol，API 费用少 50.0%；相对 Claude Code + Opus 5，少 54.3%。
- 表 1：Codex + GPT-5.6 Sol，费用 $1,787，分数 34.738。$894 / $1,787 = 50.0%。分数是 42.0 对 34.7，SoL-Pi 更高，不是打平。
- 表 2：Claude Code + Opus 5，费用 $2,535，分数 43.689。$1,158 / $2,535 = 54.3%。分数 42.2 对 43.7，费用少一截，分数略低。
- 所有费用按 2026-08-17 的 API 价。

泼冷水，进图：

- Terminal-Bench 4，63 道只跑 CPU 的题。Codex 和 Pi 各解 18，SoL-Pi 解 15。
- 总模型费用 $211.12 对 Pi 的 $286.45，少 26.3%。每道解开的题 $14.07 对 $15.91，少 11.6%。11.6% 不进图。

不进图：

- IMO 2026，SoL-Pi 用 GPT-5.6 Sol 过 3/6，总费用 $62.69，每道通过题 $20.90，论文写低于 Codex 的 $22.89 和 Pi 的 $25.32。没给另外两套 Harness 各过了几题，不拿来比题数。
- 解说帖里的「大约 94%」「能力没掉」不进图。93.7% / 94.3% 是对 Pi 的分数保留，不是对 Codex、也不是对 Claude Code。

## 岔路口：Taste-Bench

- 2026-09-22 提交，09-23 修订 v2，*The Tasteful Agent: Measuring and Improving Taste in Long-Horizon Tasks*
- https://arxiv.org/abs/2609.25804
- HTML：https://arxiv.org/html/2609.25804v2
- 作者：港城大、独立研究者、微软。第一作者在微软实习期间做的。不要写成「微软一篇论文」。

- 502 题。工程 390，研究 112。候选分叉 4,657 个，10.8% 过全部过滤。
- 14 个模型。最好的是 GPT-5.6 Sol，59.7%。GPT-5.5 是 59.5%。
- 证据越靠后越难。14 个模型平均，从 in-prefix 的 62.3% 掉到 more-work 的 21.0%。论文写 21.0% 靠近随机猜的 25%。图上写「论文把随机底标在 25%」，不另编「为什么是 25%」的协议说明。
- 思考预算只重跑了两个模型、三档。从最低档到最高档，GPT-5.6 Sol −0.2 个点，GPT-5.6 Luna +2.2 个点。不是 14 个模型都测了。
- 留出 41 道 SWE-bench Pro。无建议 14.6%，学生建议 33.7%（+19.1 个点），正确建议上限 39.0%（+24.4 个点）。执行器是 SWE-agent 1.1.0 + Qwen3.6-27B，思考关掉。学生也是 Qwen3.6-27B 加 LoRA。
- 去掉解析失败超过 9% 的 3 个模型后，剩 11 个能和 SWE-bench Verified 对。DeepSeek V4 Flash 做题排第 5，Taste-Bench 排第 10。相关区间很宽，图上不写相关系数。

官方榜（仓库 README，核对日页面；59.7 与论文表一致）：

- https://github.com/wbopan/tastebench
- Claude Opus 5：55.5。Grok 4.5：54.6，未解析 10。GLM-5.2：53.9，未解析 17。
- 这三行进图 2 的小表。未解析条数写在脚注，不把 GLM 写成干净第一档。

不进图：作者 Hugging Face 页上的 Qwen3.6-27B 从 30.0% 到 47.9%，本轮没在论文 HTML 里核对到，不用。

## 记忆时机：JitMem

- 2026-09-23，*Just-in-Time Memory: Learning to Curate Task-Adaptive Memory for LLM Agents*
- https://arxiv.org/abs/2609.27334
- HTML：https://arxiv.org/html/2609.27334
- Salesforce AI Research

- 摘要：ALFWorld、WebShop、τ²-bench，比最强基线高 16.2、16.3、3.9 个成功率点。
- 表里 +16.2 / +16.3 对得上 Qwen3-8B 当执行器：ALFWorld 77.4 对 SkillOS 61.2；WebShop 成功率 32.8 对 16.5。图上标明执行器，不写成所有模型都是这个抬幅。
- τ²-bench 的 3.9 用摘要，图上不另标执行器。
- 没训练的例子：WebShop，JitMem-gemini 成功率 61.0，SkillOS-gemini 41.0，两边都是 Gemini-2.5-Pro 既当抽取器又当执行器。这是引言里的例子，不是上面那组 +16.3。
- 引言另有：相对写时记忆，输入 token 少 50.3%–56.3%，执行步数少 28.4%–31.4%。不进图，避免和 SoL-Pi 的账单砍半搅在一张图上。

## 一句对照：JAZ

- 2026-09-22，*Harness as a Language: A Minimalist Agent Framework With Maximal Expressivity*
- https://arxiv.org/abs/2609.26891
- 摘要原话：StuLife 里要回忆、超出上下文的那一段，invoke 比 Letta（MemGPT）高 8%，成本一半。AppWorld 上比 ACE 高 4%，成本更低。
- 8% 和 4% 是论文自己的相对说法，不是我换算的绝对点数。图上照抄这个口径，并写明不是整份 StuLife。
- 设定：只有提示，没有手写工具、外接记忆或文件系统。作者里有 Omar Khattab、Armando Solar-Lezama。

## 不进图

- 解说帖里的「150 个方向、500 个环境、正好 3000 次运行、6 万次交互、能力大约 94%」。论文精确数见上。
- 「SoL-Pi 比 Codex 和 Claude Code 都能力不掉、费用砍半」。对 Codex 分数更高；对 Claude Code 分数略低。
- WFM 的分项准确率。只在文案里点一句「另一条路」，数字不进图。
