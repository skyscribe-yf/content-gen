---
title: "RL 越训越准，为什么反而越训越笨？"
author: "数解AI"
date: 2026-10-01
type: "原理"
digest: "词频、财富榜、城市人口全是幂律长尾，幂律是世界的默认形状。但 RL 后训练涨分的秘密恰恰是剪掉长尾：熵坍缩三篇论文证明，涨分的剪刀也是能力的天花板。RL Scaling Law、DeepSeek V4.1 的取舍一次讲清。"
cover: "00-cover.png"
keywords: ["幂律分布", "RL后训练", "熵坍缩"]
series: "数学直觉"
scheduledPublish: "2026-10-01T20:00:00+08:00"
---

英语语料里最常见的词是 the，它出现的次数约是第十名的 10 倍、第一百名的 100 倍。这不是语言学的怪癖——财富榜、城市人口、论文引用，全都是这条拖得极长的尾巴。因为在学校和各种教科书、科普材料里面见到太多高斯分布的内容，我一直以为被叫做自然分布的高斯分布是这个物理世界里面最普遍的规律，但是显示这个世界并不是这样的。大量的财经新闻和其他专业的描述都让我隐隐约约意识到，其实这个世界充满了长尾，高斯分布那个随指数衰减极快的良好分布，还是太过于理想化了，不能描述更普遍而又复杂的现象。

这种拖着长尾的分布有个名字：幂律分布。而今天要讲的反常识是——大模型的强化学习后训练（RL），干的恰恰是把这条尾巴剪掉的事。剪掉尾巴，分数就涨；但模型也在变「笨」。

## 幂律：一条拖得吓人的尾巴

幂律的公式短得吓人：$p(x)\propto x^{-\alpha}$——出现次数随规模的 $\alpha$ 次方衰减。就这一个式子，长出四个反直觉的特征。

一是**长尾**，80-20 只是起步价：少数头部占掉大头，尾巴拖得看不见尽头。二是在**双对数坐标上是直线**：把词频图画成 log-log，幂律就是那条笔直的斜线，这是它的身份证。三是**无标度**：没有「典型值」，平均数会被尾巴拽跑。四是**富者越富**：越常用的词越容易被用，越有钱的人越容易赚钱。

最典型的例子就是世界上的收入差距，大量的普通人处于低收入的长尾上，以至于如果你拿财富500排行榜去算平均，就会得到一个一段离谱的结果，相信所有人都被这种身边统计学蒙蔽过自己的直觉。

![幂律长尾：双对数坐标上的一条直线](01-powerlaw-loglog.png)

## RL 里也有幂律：连收敛都能提前算出来

幂律不只住在词频里。ACL 2026 一篇研究（中科大&上海AILab）在 Qwen2.5 全系 0.5B–72B 上跑 RL 后训练。他们发现测试损失随算力、数据量都按幂律下降，拟合优度 **R²>0.99**；换成 Llama 3 全系重做一遍，还是同一条直线。这就是 RL 后训练自己的 Scaling Law。

它带来一个很爽的工程能力：只用训练早期 **20%–30% 的数据点**，就能外推模型收敛到哪。用 0.5B–32B 的数据，甚至能预测 72B 的完整训练轨迹。还有一个反直觉的「性能交叉」：等算力预算下，**32B 训练初期反而跑在 72B 前面**。原因不复杂——大模型单步效率高但每步贵，小模型靠步数多扳回来。

这个规模之小，的确令人感到诧异。然而这真的能成立吗？我想最后还要看事实的检验。

可预测性不是魔法：正因为数据住在低维结构上（[流形假设：15 万像素的图片，AI 凭什么只用 43 个数就认得？](https://mp.weixin.qq.com/s/z5OT4caCjpMsMKxLd7Zp7A)），规律才有被学出来的可能。

![RL 后训练的幂律：小模型外推大模型的训练轨迹](02-rl-scaling-law.png)

## 转折：分数在涨，多样性在跌

就在同一批论文里，另一个方向的发现让人笑不出来：RL 训练越久，模型的输出分布越窄。

三个角度盯的是同一件事。东京大学 2026 年 1 月的分析（arXiv 2601.04670）发现，RL 更新会系统性地推高模型置信度，输出分布整体概率集中。更有意思的是 Best-of-N 实验：SFT 和 GRPO 的差距随采样数增大而收窄。**分布变窄本身就部分解释了 RL 的涨分**。

其实这个研究本身也还不能算是盖棺定论，如果据此就说是RL毫无用处，可能也太过武断了一些，因为不经过RL手法中做复杂的后训练，谁也不知道怎么样让分布变窄，以及变到何种程度。

The Invisible Leash（arXiv 2507.14843）补了第二刀。pass@1 一直在涨，但经验支撑「收缩大于扩张」——base model 原本答对的题，RL 之后采再多也捞不回来。第三篇 When Sharpening Becomes Collapse（arXiv 2601.15609）更狠。有限批次的更新天然偏向被采到的模式，锐化过头就是坍缩，把同样正确的其他解法压死了。

这其实有点像人类专家所经历的狭窄领域的反复实践和训练，你在一个细分的领域上面把一系列看起来极其复杂的技能都快速内化了之后，那些通用领域的技能，反而变得生疏了起来。

![剪尾前后：分布收窄，长尾消失](03-sharpening-collapse.png)

## 剪刀说：涨分的秘密，就是天花板

把两条线索并起来看：幂律长尾是罕见解的栖身地——低概率、高价值的解法都住在尾巴上。RL 的剪刀剪掉长尾，正是熵坍缩的另一种说法。

![长尾被剪断：罕见解法随尾段一起消失](04-tail-cut-concept.png)

听起来似乎有点离谱，但是没办法，涨分和天花板，就是同一把剪刀的两个不同的侧面。

也有反方。MRPO（arXiv 2602.02545，2026-01）认为问题不在剪，而在「只在预训练的低秩偏置流形内剪」。他们用几何干预把探索踢出流形，4B 模型在数学任务上打赢了 Qwen3-32B。所以剪不一定是坏事，怎么剪才是。

## 给剪刀踩刹车

工程上已经有几招。DAPO / clip-higher 放开裁剪上限，让「稀有但正确」的低概率 token 也能参与更新——保住尾巴上的好解法。ACL 2026 杰出论文 STEER 的思路是给剧烈的熵变化踩限速器，而不是盲目把熵推高——熵涨过头同样会发散。还有 CF-RL 两阶段：先塑分类器再全量 RL，置信度涨得慢一点，多样性就多留一点。

现实里最新的取舍样本是 DeepSeek V4.1 Flash（2026-09-10 发布，552B MoE）。官方称做了更大规模的强化学习后训练，Coding/Agent 全线大涨——DeepSWE v1.1 从 62.7 提到 74.2。但 GPQA Diamond 从 92.4 微降到 90.9。工作场景涨分、纯推理微退，剪刀的两面在同一版模型上同时出现。

## 尾巴才是常态

词频的长尾是语言的丰富度，解法的长尾是智能的丰富度。幂律告诉我们长尾才是常态，RL 的故事提醒我们：剪掉常态换来的准，是有代价的。真正的天花板不是分数，是「只会一招」。

如果只转一句话给同事：**RL 涨分的秘密是剪掉幂律长尾——涨分的剪刀，也是能力的天花板。**

其实社区里，也有大量对近期的前沿coding模型其他方面能力退化的抱怨和不满。你是否认可这种取舍和权衡：用少得几分的写代码能力，换取模型写文章写的更好？评论区聊聊。

下一篇我们把「熵」拆开：分布变窄的这个「窄」，到底是用什么尺子量出来的？

觉得这篇把「剪刀」这笔账算清了，点个赞 👍、收藏 ⭐ 备用。关注「数解AI」，AI 的原理慢慢拆解。

📖 **数学直觉**：[高维空间为什么全是壳？内积才是那把尺子](https://mp.weixin.qq.com/s/Nrfr-90Fpu3mFDML9s0d1Q) → [KL散度：为什么整个AI共用一把尺子？](https://mp.weixin.qq.com/s/G1PUOuwxURoo1Dp1pDfQMg) → [损失面上全是坑，为什么梯度下降还能走到谷底？](https://mp.weixin.qq.com/s/AYlFPXsMJJ0esCa_7_amrw) → [流形假设：15 万像素的图片，AI 凭什么只用 43 个数就认得？](https://mp.weixin.qq.com/s/z5OT4caCjpMsMKxLd7Zp7A) → **RL 越训越准，为什么反而越训越笨？（本篇）**

🔥 **热门文章**：

[KV缓存存进SSD：慢50倍的硬盘，为什么反而更快？](https://mp.weixin.qq.com/s/40BQ06eDTv4-2r8FmQ_rMA)  
[高维空间为什么全是壳？内积才是那把尺子](https://mp.weixin.qq.com/s/Nrfr-90Fpu3mFDML9s0d1Q)  
[高斯为什么二阶就够？非线性去哪了](https://mp.weixin.qq.com/s/gs_3y7JXuBLlzR5w6jW6fQ)  
[学习率怎么自动调？Adam 优化器拆给你看](https://mp.weixin.qq.com/s/aSLVO-otvr2rxIU1kr2eAA)  
[DeepSeek-V4为何不用MLA？](https://mp.weixin.qq.com/s/MQEgbY16mLs-N7g2xKW1HQ)  
[随机变量为什么不是变量？它其实是个函数](https://mp.weixin.qq.com/s/5BxjOUblW64DXNffHc2sxQ)  
[流形假设：15 万像素的图片，AI 凭什么只用 43 个数就认得？](https://mp.weixin.qq.com/s/z5OT4caCjpMsMKxLd7Zp7A)  
[KL散度：为什么整个AI共用一把尺子？](https://mp.weixin.qq.com/s/G1PUOuwxURoo1Dp1pDfQMg)  
[损失面上全是坑，为什么梯度下降还能走到谷底？](https://mp.weixin.qq.com/s/AYlFPXsMJJ0esCa_7_amrw)  

**参考资料与数字溯源**

1. Tomihari, A. (2026). [Learning Dynamics in RL Post-Training for Language Models](https://arxiv.org/abs/2601.04670). arXiv 2601.04670（2026-01，一手）：特征表征变异有限 → RL 更新系统性推高置信度 → 输出多样性收窄；SFT 与 GRPO 的 Best-of-N 差距随 N 收窄，概率集中部分解释涨分。
2. Tan, Z. et al. (2025). [Scaling Behaviors of LLM RL Post-Training](https://arxiv.org/abs/2509.25300). arXiv 2509.25300 / ACL 2026（一手）：Qwen2.5 0.5B–72B + Llama 3 1B–70B，幂律拟合 R²>0.99；20%–30% 数据点外推收敛；学习效率 k(N) 饱和，等算力下 32B 初期反超 72B。
3. Wu, F. et al. (2025). [The Invisible Leash: Why RLVR May or May Not Escape Its Origin](https://arxiv.org/abs/2507.14843). arXiv 2507.14843（2026-02 v4）：更大采样预算下经验支撑收缩大于扩张；token 熵可升但答案级熵降。
4. Fan, M. et al. (2026). [When Sharpening Becomes Collapse](https://arxiv.org/abs/2601.15609). arXiv 2601.15609：有限批次更新偏向被采样模式，坍缩经语义耦合扩散。
5. 郝哲正等 (2025). [Rethinking Entropy Interventions in RLVR](https://arxiv.org/abs/2510.10150). arXiv 2510.10150 / ACL 2026 Outstanding Paper：token 级熵变四因素，STEER 给剧烈熵变限速；DAPO/clip-higher 保留低概率正确分支。
6. Wang, D. et al. (2026). [Beyond Alignment: Manifold-Reshaping Policy Optimization](https://arxiv.org/abs/2602.02545). arXiv 2602.02545：探索受限于低秩偏置流形，MRPO 几何重塑后 4B 在数学任务超 Qwen3-32B（论文实验口径）。
7. 机器之心 (2026-09-10). [DeepSeek V4.1 Flash 正式上线](https://m.163.com/dy/article/L6FLIARS0511AQHO.html) + DeepSeek 官方基准：552B MoE / CED（输入激活 8B、输出 16B）；「更大规模的强化学习后训练」为官方口径；DeepSWE v1.1 62.7→74.2、Terminal-Bench 2.1 87.9→90.6、GPQA Diamond 92.4→90.9（V4 Pro→V4.1 Flash）。
8. Zipf 定律（1949）：词频与排名成反比——第一名约为第十名的 10 倍、第一百名的 100 倍，经典经验规律。

#幂律分布 #RL后训练 #熵坍缩 #强化学习 #数解AI
