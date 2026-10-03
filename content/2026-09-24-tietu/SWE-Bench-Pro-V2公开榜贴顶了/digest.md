# 新榜一发，就贴顶了

> 2026-09-24 贴图草稿。未发布。数字见同目录 `sources.md`。图：`01.png`。

## 手敲文本

SWE-Bench Pro V2，9 月 22 日 Scale 和 Reflection 一起放的。X 上最响的一句是：新榜一发，就已经饱和。那条帖子 1.8k 赞。

别急着笑。V1 自己先饱和过一轮。

2025 年 9 月，公开集 731 题，头部是 GPT-5 的 23.3%，Opus 4.1 的 23.1%。到 2026 年 9 月，厂商聚合里 Fable 5 到了 80%，Opus 4.8 自报到 69.2%。同一时期 Scale 统一脚手架，头部只有 61.5%，Claude 官方最好的 Opus 4.6 是 51.9%。一张名字，两套分。OpenAI 7 月审计估计约三成题是坏的。Epoch 9 月 1 日判 Flawed。

V2 不是加难。Scale 研究员原话：质量刷新，不是更难的榜。731 删到 642，砍掉 89 道无效题。69 道说明和测试打架，只改文字，盲解才过。Agent 阶段断网。早先开着网，642 条里 32 条敲过代码托管，4 条拿到修复提交的 SHA。交卷后换干净镜像重判。Opus 5 伪造过 go.sum。Inkling 改过缓存，3 题原地能过。23 人，1897 小时。

洗完，公开集贴顶。Opus 5 是 638/642，99.4%。Kimi K3 是 627/642，97.7%。私有集 272 题，Opus 5 掉到 222/272，博客写的落差是 17.8 个点。Inkling 的题数差对得上 Scale 说的最多约 22 个点。他们的判断：评测时没漏题。公开仓库训练时就已经在网上。锁网锁不住记忆。

还想分开模型，看 Hard 那 51 道。壳不一样，不能当纯排名。Opus 5 用 Claude Code 是 98.0，Fable 5.1 是 92.2，GPT-6 Astra 用 Codex 是 90.2，Kimi K3 是 88.2，GLM-5.3 是 84.3。Gemini 3.8 Flash 公开集还有 609/642，Hard 只剩 58.8。

公开通过率不能再排名。信号在私有仓库、Hard-51、单题 token。开源头部换三套壳，通过率差不多，账单差一截，失败轨迹的推理大约两倍。按账单选壳。下一截是没见过的仓库，不是再刷公开 PR。

99.4% 不能和 23.3% 直接相减。你现在还拿公开 SWE-Bench 给模型排名吗？

<a class="wx_topic_link" data-topic="1" style="color: #576b95;">#SWEBench</a>  <a class="wx_topic_link" data-topic="1" style="color: #576b95;">#CodingAgent</a>  <a class="wx_topic_link" data-topic="1" style="color: #576b95;">#评测</a>  <a class="wx_topic_link" data-topic="1" style="color: #576b95;">#开源模型</a>  <a class="wx_topic_link" data-topic="1" style="color: #576b95;">#数解AI</a>
