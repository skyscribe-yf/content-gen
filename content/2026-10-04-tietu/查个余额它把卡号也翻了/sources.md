# 事实源

> 2026-10-04 贴图。主论文一手核对自 arXiv HTML（表格从原始 `<th>` 抽出，不采用转写丢列后的数字）。

## 主论文

- 标题：OverAct: Measuring and Mitigating Proactive Over-Authorization in LLM Tool-Calling Agents
- arXiv: https://arxiv.org/abs/2610.01508 （v1，2026-10-01，cs.CR）
- HTML：https://arxiv.org/html/2610.01508v1
- 作者：Zhang Taolin、Wan Jiuheng（合肥工业大学）；Wang Hanyu、Hu Tingyuan（华东师范大学）；Wang Chengyu（阿里云计算，通讯）
- 银行原例（Introduction）：用户说 “check my balance”，字面最少是一次 `get_checking_balance`；实际可能再调交易流水、储蓄、卡信息。医疗对比例子是 “When is my next appointment?” 可能再调用药、化验、诊断史。

## 可写数字（均来自论文正文或表）

| 项 | 数字 | 出处 |
|---|---|---|
| 题量 / 域 | 720 episodes，8 个隐私域，每域 6 个工具，共 48 个工具 | §3.4 |
| 模型 | 7 个，4 家：Qwen3.6-Flash / Plus、Qwen3.7-Max、DeepSeek-v3、DeepSeek-v4-Pro、GLM-5.2、Kimi-K2.7-Code | §4.1，Table 1 |
| 核心实验量 | 90,720 runs（7×6×720×3）；另有约 3.9 万补充跑 | §4.1 |
| Baseline SIR | Flash 1.50；Plus 1.65；Qwen3.7-Max 1.74；DeepSeek-v3 1.18；DeepSeek-v4-Pro **2.39**；GLM-5.2 1.96；Kimi-K2.7-Code 1.65。七个都显著 >1（p<0.001） | Table 1 |
| 平均超额 | 约 0.7 个多余工具 / 题 | §4.2 |
| v3 / GLM 定性 | v3 超额最低，任务完成也最低，是少调不是会节制；GLM-5.2 完成率最高，超额也在最强一档 | §4.2 |
| 说法模糊 | 精确请求接近完全合规；模糊请求的 scope excess 是 2.7×（d=1.19） | §4.3 |
| 工具池 | 4→24 次线性上升后平台；pool 24 SIR 1.97，pool 36 SIR 2.00，36/48 相对 24 没有实质更高 | §4.4 |
| 温度 | 0.0 / 0.7 / 1.0，SIR 统计上分不开（p=0.367） | §4.4 |
| 权限清单 | SIR 0.96，TCR 0.95，要 oracle（事先知道最少该调哪些） | Table 2 |
| SelfAudit 消融 | 仅中等+模糊题、四模型。Baseline SIR 2.28 / TCR 0.94 / PVS 2.26。只解释：SIR 2.42，PVS 2.46（论文写 +9% PVS）。只过滤：PVS 1.43（−36%）。解释+过滤：SIR 1.68，TCR 0.89，PVS 1.29。摘要写隐私向超额降 43%（(2.26−1.29)/2.26） | Table 3，§4.6，摘要 |
| 人工判断 | 100 题、340 次超额调用。不想要 71.2%，中性 17.0%，想要 11.8%。精确请求不想要 93.3%（n=30）；模糊请求不想要 63.9% | Table 5，§4.7 |
| 超额类型 | Exploratory 50%，Anticipatory 21%，Completionist 20%，Confirmatory 9% | §4.7 |

SIR = 实际调用个数 / 最少该调的个数。SIR=1 也不等于集合刚好对上（可能漏一个、多一个）。TCR 是最少工具集合的召回，不检查参数和执行是否真成功。PVS 把超额调用碰到的 PII 类别加总，43% 降的是 PVS，不是 SIR。

## 口径边界（正文必须带）

- 认的是字面最少工具集，作者自己称为保守口径。不声称每一次超额都是用户讨厌的，也不等于生产事故。
- 不是文件系统 coding agent 的越权（论文指向同期 OverEager-Gen 为互补设置）。
- 模型名以论文为准：Kimi-K2.7-Code、Qwen3.7-Max、DeepSeek-v4-Pro。不改写成别的版本。

## X 上的讨论（2026-10-02 ~ 10-04）

今天在传、但还没爆：

- @cv_usk 2026-10-04：https://x.com/cv_usk/status/2106625848250110457 （转述 1.18–2.39、2.7×、43%、71.2%；数字与论文一致）
- @ai_database 2026-10-04：https://x.com/ai_database/status/2106581232238879231

同窗口更热、但本篇不写：

- Wavestone 七件套拆解帖，2026-10-03，约 469 赞 / 822 收藏：https://x.com/undefinedKi/status/2106479644354474463 。论文是 2026 年 7 月的旧文回锅，和本号已发的 Harness 稿重叠。
- ActiveSaddler，arXiv:2610.00906，2026-10-01，微软/POSTECH/KAIST。同优化器、只改训练课表：GAIA2 Pass@1 55.4%→59.8%（+4.4），Terminal-Bench 2.0 72.5%→80.0%（+7.5）；摸到 58.5% 开发集精度，$1,360 → $298。讨论量小。项目页：https://autosaddler-projectpage.github.io/activesaddler/
- Karpathy 2026-10-02 关于「理解模型输出」的帖子是全网最热讨论，不是 agent 论文，不拿来当这篇的事实。
