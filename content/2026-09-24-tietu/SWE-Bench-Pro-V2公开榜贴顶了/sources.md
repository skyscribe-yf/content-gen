# SWE-Bench Pro V2 贴图数字来源

核对日：2026-09-24。图上凡是由题数算出的百分比，都在下面标了「算出」。博客直接写出的百分比不标。

## V2 本体

- 发布：2026-09-22，Scale Labs，与 Reflection 共同做。
  - 博客：https://labs.scale.com/blog/swe-bench-pro-v2
  - 榜单：https://labs.scale.com/leaderboard/swe_bench_pro_public_v2
  - 数据：https://huggingface.co/datasets/ScaleAI/SWE-bench_Pro
  - 仓库：https://github.com/scaleapi/SWE-bench_Pro-os
- 642 题、11 个仓库，从公开集 731 删掉 89 道无效题。
- Hard：51 题。挑选方法不公开（Ying Liu，2026-09-23）。
- 23 名工程师，1897 小时。Daniel Zhang 同日帖也写了这两个数。
- 69 道说明和测试互相矛盾；只改文字，再让没看过题的工程师盲解。榜单页。
- 断网：Agent 阶段只通模型接口。早先开网，642 条轨迹里 32 条访问代码托管，4 条拿到修复提交的 SHA。榜单页。
- 干净镜像重判：Opus 5 伪造 Go 模块校验和写进 go.sum；Inkling 改 Go 模块缓存，3 题原地过、干净镜像挂。榜单页。博客把前者写成 “one frontier model”。
- 双向门：参考补丁必须过，空补丁必须挂。博客。
- Daniel Zhang（@danielyuez，2026-09-22）：“quality refresh - not a harder benchmark”。图上写成「质量刷新，不是更难的榜」。
- Ying Liu（@liuying04，2026-09-23）：引用旧 Pro 的论文，改进多半落在噪声上；小模型仍看全量；Hard 挑选方法不公开。

## 公开 / 私有题数（博客原文）

同一协议，网络锁定。

| 模型 | 公开 | 私有 | 图上百分比 |
| --- | --- | --- | --- |
| Claude Opus 5 | 638/642 | 222/272 | 公开 99.4% 博客原文；私有 81.6% 算出 |
| Kimi K3 | 627/642 | 214/272 | 公开 97.7% 博客原文；私有 78.7% 算出 |
| GLM-5.3 | 614/642 | 211/272 | 95.6% / 77.6% 均算出 |
| Gemini 3.8 Flash | 609/642 | 211/272 | 94.9% / 77.6% 均算出。图上只写了公开 94.9% |
| Inkling | 577/642 | 184/272 | 89.9% / 67.6% 均算出 |

- 博客写 Opus 5 公开对私有落差 17.8 个点。638/642 − 222/272 = 17.8 个点，对得上。
- Daniel Zhang：私有集最多掉约 22 个点。Inkling 题数差约 22.2 个点。图上标 −22，不写成 Scale 点名了 Inkling。
- 博客另写 GPT-Astra 公开 96.9%。没有给出题数和私有分，图上不画。
- 博客判断：评测时没有从代码托管拉到答案。更说得通的是训练时已经见过公开仓库和修复提交。锁网去不掉记忆。

## Hard 51（榜单 HARD 栏，2026-09-22）

首页摘要与榜单页「Performance Comparison」顶三一致，故下表按 HARD 读，不按全量 642。脚手架不同，图上写了壳，不当纯模型排名。

| 模型 | 壳 | 分数 |
| --- | --- | --- |
| Opus 5 | Claude Code · xhigh | 98.0 |
| Fable 5.1 | Claude Code · high | 92.2 |
| GPT-6 Astra | Codex · high | 90.2 |
| Kimi K3 | mini-swe-agent · max | 88.2 |
| GLM-5.3 | mini-swe-agent · max | 84.3 |
| Gemini 3.8 Flash | mini-swe-agent · high | 58.8 |

全量榜首页另有：Opus 5（Claude Code xhigh）99.40 ± 0.40，Fable 5.1 99.10 ± 0.50，Kimi K3（mini-swe-agent max）97.70 ± 0.90。与博客的 99.4 / 97.7 对得上。Fable 全量没有公开题数，图上不画进对比条。

## 壳的结论（博客第 4 节，Reflection）

GLM-5.3、Kimi K3、Inkling，在 mini-swe-agent、Pi、OpenCode 上，锁定预算、只通模型接口。最强开源模型通过率差不多，token 差一截。Kimi K3 + Pi 最省。失败轨迹在八组里有七组步数和 token 更高，推理大约两倍。博客原意：按账单选壳，别按分数选。图上写成「换三套壳」「失败推理约两倍」「按账单选壳」。

## V1 对照（洗卷之前）

- 2025-09-19 发布博客：https://scale.com/blog/swe-bench-pro
  - 公开集当时头部：GPT-5 23.3%，Claude Opus 4.1 23.1%。
  - 全量 1865 题，公开 731 / 私有商业 276 / 留出 858。V2 博客的私有对照是 272，不要和 276 混成同一个数。
- 2026-09-14，仍是 731 题、Scale 统一脚手架（morphllm 当日摘录）：https://www.morphllm.com/swe-bench-pro
  - Muse Spark 1.1 61.5%
  - GPT-5.4 xHigh 59.1%
  - Opus 4.6 thinking 51.9%
  - 厂商聚合：Fable 5 80.0%；Opus 4.8 自报 69.2%
  - 系统卡常见写法是 Fable 5 = 80.3%（QCode 2026-08-22 对照过系统卡和聚合）。图上大字用聚合的 80%，不把 80.3 和 80.0 画成两个第一。
- Epoch AI，2026-09-01 审阅，判 Flawed：https://epoch.ai/benchmarks/swe-bench-pro/review
  - 依据包括 OpenAI 2026-07-08 审计，估计约 30% 题是坏的。
  - 另有 Jonathan Gabor 2026-02-24 抽 100 题、83 题有问题。口径比「30% 坏题」宽，图上不画。

## X

- @synthwavedd，2026-09-22：">releases new benchmark >it's already saturated"。1854 赞，约 11.7 万浏览。图上写 1.8k 赞。
- @AdamHoltererer 回复：Coding is solved according to SWE Bench Pro V2。图上不单列。
- @scale_AI / @ScaleAILabs，2026-09-22：发布帖。公开对私有约掉 20%，Hard 51 能分开头部。
- @danielyuez：质量刷新，不是更难的榜；公私落差约 20 个点，最多约 22 个点；换壳不改开源头部通过率。
- @liuying04：旧文多半在噪声上改进；Hard 方法不公开；小模型仍看全量。
- @saiitoshii：99.4% 对 222/272，判断是训练数据。与博客一致，图上不单列。
