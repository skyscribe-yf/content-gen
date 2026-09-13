---
title: "GRPO 省了一个 critic，长任务为什么反而崩了？"
author: "数解AI"
date: "2026-09-13"
type: "原理"
digest: "GRPO 用组内排名换掉 critic，省下显存，也埋下三堵墙：全对组零梯度、功劳平摊、越错越长。DAPO、Dr. GRPO、GSPO 各修一堵——练得越好，信号越少。"
cover: "00-cover.png"
keywords: ["GRPO", "强化学习", "DeepSeek", "DAPO", "PPO"]
scheduledPublish: "2026-09-13T20:00:00+08:00"
wechatUrl: ""
---

GRPO 砍掉的那个 critic 老师，省下的不只是显存，还有长程任务里的判断力——省下的和失去的，是同一个东西。

这不是一句抱怨。它是三段可以写在黑板上的数学：组内没有差异时，信号消失；功劳平摊时，信号有毒；按长度归一化时，信号被带偏。2025 年，DAPO、Dr. GRPO、GSPO 三篇论文修的，恰好就是这三堵墙。

## 一、先花一分钟：GRPO 只干一件事

同一道题，采样 16 份答卷（DeepSeek-R1 的真实训练配置），规则判分：对了是 1，错了是 0。然后组内减均值、除标准差：

$$\hat{A}_i = \frac{r_i - \mathrm{mean}(r_1,\dots,r_{16})}{\mathrm{std}(r_1,\dots,r_{16})}$$

每份答卷拿到一个相对成绩：比组内平均好就是正，差就是负。策略梯度推高正优势答卷里的每个 token，压低负优势的。

critic 干的本来是另一件事：一格一格估「走到这一步还有多少希望」，而它是一个和策略一样大的网络。GRPO 把这整套估值换成了一句「看你在组里排第几」——诞生背景和它与 PPO 的逐项对比，[之前专门拆过](https://mp.weixin.qq.com/s/t4sO-zC5v1_jq8hJT_YTGA)，这里不重复。

账面上这是纯赚。但有三堵墙，都砌在「排名」这两个字上。

## 二、第一堵墙：全对的组，一步都没学到

16 份答卷全对，奖励全是 1：均值是 1，标准差是 0，优势变成 0/0——工程上置 0。整组梯度为零，这批样本白跑。全错同理。

这不是偶发故障。一组全同分的概率是 $p^{16} + (1-p)^{16}$，p 是题目的正确率：

![一道题答 16 遍全对或全错的概率](01-all-same-group.png)

正确率 50% 的题，全同分几乎不可能（0.003%）；正确率 90%，概率 18.5%；95%，44.0%；99%——85.1%。模型越练越强，简单题成批退化成全对组。练得越好，信号越少。

反转还在后面。「差一点全同分」的组——16 份对了 15 份——除以那个极小的标准差，微弱差异被放大成大梯度。简单题和难题的权重被系统性扭曲，Dr. GRPO 管这叫难度偏差。

修法是 DAPO 的动态采样：过采样一批组，把全对全错的扔掉，补满有效样本再更新。论文报告训练时间基本不变，收敛步数反而更少。

## 三、第二堵墙：一个总分，泼给几万个 token

基础 GRPO 是 output-level：整条序列共享同一个优势值。第 3 个 token 和第 3000 个 token，梯度里乘的是同一个数。

好答卷里的废棋被一同推高，烂答卷里的妙手被一同压低。连坐。

作为对比，有的方案给每一步单独配一个估值，把 100 步的功劳按视野打折、逐格分摊；GRPO 反过来，终点一个总分，平摊给全部几万个 token。序列越长，每个 token 分到的信号越稀。长 CoT、长程 agent 任务动辄几万 token——这就是「长程任务撑不住」的数学本体。

![一份总分平摊给整条长卷](02-credit-pool.png)

这堵墙至今没有修法。DAPO 的 token-level loss 只是把 loss 的加权方式改了，分摊本身一动没动。critic 的位置，没人补上。

## 四、第三堵墙：错了，还更啰嗦

GRPO 的损失里，每份答卷还要按长度归一（除以回答长度）。负面答卷越长，每个 token 摊到的惩罚越薄。模型从这套规则里学到的是：把错答案写长。

Dr. GRPO 论文统计过 DeepSeek-R1-Zero 的回答：错误回答平均 8206 字符，正确回答 4965 字符。错了，还长 65%。

![R1-Zero 错误与正确回答的平均长度](03-wrong-longer.png)

修法来自 Sea AI Lab 的 Dr. GRPO：把除以长度、除以标准差全部删掉，优势改成简单的 $r_i - \mathrm{mean}$，归一分母换成固定常数。绕了一圈回到 PPO 式的目标函数，AIME 2024 上 7B 模型拿到 43.3%，8 卡 A100 跑 27 小时。

同年 Qwen 团队从另一个方向撞上长度的墙：逐 token 的修正系数噪声沿长序列累积，训练能崩到撤销检查点都救不回来。他们的 GSPO 把修正挪到整条序列一级——Qwen3 的 RL 训练用的就是它。

## 五、省下的和失去的，是同一个东西

三堵墙，同一个根源：GRPO 把「每步值多少」外包给了「组内排名」。

组内有差异、序列不太长、回答不太啰嗦时，它便宜好用。长程任务把三个条件同时打破：没有差异、序列极长、惩罚被摊薄——于是没有信号、平摊黑锅、奖励啰嗦。

DAPO 补信号，Dr. GRPO 纠偏差，GSPO 稳噪声，但没有一家把 critic 请回来。那个「这一步值不值」的判断，仍然悬空。这个题目在我这里拖了快一个月，真正值得写的，果然不是它怎么省，而是它崩在哪。

下一篇是系列收尾：奖励函数——AI 钻空子的源头，为什么奖励设计总在造出新的流氓。

你的工程里见过「平均分大锅饭」式考核吗？评论区聊聊。

觉得这步走明白了，点个赞 👍、收藏 ⭐ 备用。关注「数解AI」，热点当天拆，数学慢慢讲。

🔥 **热门文章**：

[KV缓存存进SSD：慢50倍的硬盘，为什么反而更快？](https://mp.weixin.qq.com/s/40BQ06eDTv4-2r8FmQ_rMA)  
[高维空间为什么全是壳？内积才是那把尺子](https://mp.weixin.qq.com/s/Nrfr-90Fpu3mFDML9s0d1Q)  
[高斯为什么二阶就够？非线性去哪了](https://mp.weixin.qq.com/s/gs_3y7JXuBLlzR5w6jW6fQ)  
[学习率怎么自动调？Adam 优化器拆给你看](https://mp.weixin.qq.com/s/aSLVO-otvr2rxIU1kr2eAA)  
[DeepSeek-V4为何不用MLA？](https://mp.weixin.qq.com/s/MQEgbY16mLs-N7g2xKW1HQ)  
[SFT微调：1万条数据就能让模型听话？](https://mp.weixin.qq.com/s/vwXGbjm9Ai1GPvQi5O3UyQ)  
[GRPO为什么省显存，却撑不住长程任务？](https://mp.weixin.qq.com/s/t4sO-zC5v1_jq8hJT_YTGA)  

**参考资料**

1. DeepSeek-AI (2024). [DeepSeekMath: Pushing the Limits of Mathematical Reasoning](https://arxiv.org/abs/2402.03300). GRPO 原始论文。
2. ByteDance Seed & Tsinghua AIR (2025). [DAPO: An Open-Source LLM Reinforcement Learning System at Scale](https://arxiv.org/abs/2503.14476).
3. Liu et al., Sea AI Lab (2025). [Understanding R1-Zero-Like Training: A Critical Perspective](https://arxiv.org/abs/2503.20783). Dr. GRPO。
4. Qwen Team (2025). [Group Sequence Policy Optimization](https://arxiv.org/abs/2507.18071). GSPO。
5. DeepSeek-AI (2025). [DeepSeek-R1: Incentivizing Reasoning Capability in LLMs via Reinforcement Learning](https://arxiv.org/abs/2501.12948). G=16 训练配置。

#强化学习原理 #GRPO #DeepSeek #大模型 #数解AI
