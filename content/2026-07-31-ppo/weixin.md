---
title: "PPO：被顶会拒稿，怎么成了RLHF发动机？"
series: "大模型原理"
author: "数解AI"
type: "原理篇（深入）"
wechatUrl: "https://mp.weixin.qq.com/s/OEZtUhm8MT_En7enJo_8dw?token=2031108942&lang=zh_CN"
keywords: ["PPO", "TRPO", "GRPO", "策略梯度", "价值网络", "GLM-5.2", "奖励黑客", "KL约束"]
digest: "PPO 曾是 OpenAI 的默认 RL 算法，被 NIPS 2017 拒稿，却在 LLM 时代迎来第二春。本文用 GLM-5.2 的案例，拆解 PPO 的三道机关——Clip、Critic 和 KL 约束，以及长程任务为什么让 GRPO 站不住。"
cover: "00-cover.png"
---

2026 年 6 月，智谱发布 GLM-5.2。

这个 744B 参数的开源模型，在 FrontierSWE 上拿到 74.4%，逼近 Claude Opus 4.8。但比性能更让技术圈坐不住的，是一个「倒退」决策——

在所有人都在扔掉 critic 的时候，智谱花了额外显存把它请了回来。

两年前，DeepSeek 提出的 GRPO 成了开源社区的新默认：不训练价值网络，省显存又稳定。GLM-5.1 用的正是这套思路。但 GLM-5.2 悄悄切回了一种更经典的算法——**PPO**（Proximal Policy Optimization）。

这个决定像一根针，扎破了一个维持了一年多的共识。要理解为什么，得先回到 PPO 的身世。

![PPO 训练闭环：策略模型 + Critic + 奖励模型 + KL 约束](01-ppo-loop.png)

## 一、PPO 的前世今生

### TRPO：信任域的思想

理解 PPO，得先知道它解决了什么问题。

强化学习训练的核心矛盾是：策略更新太猛会崩溃，太慢又学不动。TRPO（Trust Region Policy Optimization）给了数学上优雅的答案：划定一个「信任域」。新策略的分布不能离旧策略太远，然后在这个域内找最优更新。

问题在于，TRPO 需要计算 Fisher 信息矩阵（二阶导数），计算量巨大，工程上几乎不可行。它告诉人们「该约束」，但没给出「怎么简单约束」的答案。

> TRPO 的完整数学推导和 trust region 的几何直觉，我们留到强化学习系列。

### PPO：TRPO 的工程化答案

2017 年，OpenAI 的 John Schulman 提出 PPO：用 **clip** 替代复杂的二阶优化。

不再计算 Fisher 矩阵，而是直接截断新旧策略的概率比。效果接近 TRPO 的稳定性，实现只需几行代码。

传承线很清晰：TRPO 告诉你要约束策略更新幅度，PPO 告诉你用 clip 就够了。

### 被 NIPS 2017 拒稿

然后这个故事有一个讽刺的注脚。

2026 年 6 月，Schulman 在 X 上轻描淡写地提起一句话：

> **PPO: rejected from NIPS 2017**

审稿意见：「创新性有限」「对比基线提升不够显著」。学术评审的标准，与产业真正的需求，在这里出现了错位。

颇具讽刺意味的是，NIPS 这个名字后来也成了历史：2018 年，它正式改名为 NeurIPS。一个后来被证明是 RLHF 基石的算法，被这个会议拒之门外。

Schulman 后来感慨：PPO 在 LLM 时代迎来第二波热潮，原因甚至超出了原论文的预期。importance ratio 目标修复了异步训练的偏差。clip 机制则通过当时未知的途径影响熵——直到 2025 年，DAPO 论文才揭示这一点。

这不是孤例。据机器之心梳理，LSTM 在 1996 年、Dropout 在 2012 年也都曾被 NIPS 拒稿。简单但可规模化的方法，往往最初不被学术评审认可。

时间才是最公正的评审。

### PPO → GRPO：去掉 critic 的变体

PPO 在 RLHF 中跑通后，开源社区开始琢磨怎么简化它。

2024 年，DeepSeek 提出 GRPO：不训练价值网络了。改成让模型对同一个问题生成一组回答，拿组内平均奖励做基线，谁比平均分高，优势值就为正。

这就像让同一道题的几十名学生同时交卷，互相比较打分——不需要一个全知的阅卷老师，矮子里也能拔将军。

GRPO 省掉了 critic 的显存和训练成本，在数学题、单元测试这类短任务上效果稳定，迅速成为开源社区的新默认。GLM-5 的技术报告里，GRPO 的组大小正是 32。GLM-5.1 作为同一条路线的增量版本，延续的正是这套思路。

但 GLM-5.2 为什么又放弃了它？

## 二、PPO 的三道机关

要理解 GLM-5.2 的「回归」，得先拆解 PPO 的核心机制。

### 机关 1：Clip——策略不能更新太快

PPO 的核心目标函数长这样：

$$
L^{PPO}(\theta) = \mathbb{E}\left[\min\left(r_t(\theta) A_t,\ \text{clip}(r_t(\theta), 1-\epsilon, 1+\epsilon) A_t\right)\right]
$$

其中 $r_t(\theta) = \frac{\pi_\theta(a|s)}{\pi_{\theta_{old}}(a|s)}$ 是新旧策略的概率比，$A_t$ 是优势函数。

直觉是什么？**学骑自行车**。

方向偏了就纠正，但纠正幅度不能太大——左倾就往右摆，但摆猛了反而摔向另一边。clip 把每次策略更新幅度限制在 $[1-\epsilon, 1+\epsilon]$ 区间内：概率比超过这个范围的，直接截断，不让它贡献梯度。

$\epsilon$ 通常取 0.1~0.2，控制「一步走多大」。工程里常做非对称 clip——GLM-5 就用 $\epsilon_{\text{low}}=0.2$、$\epsilon_{\text{high}}=0.28$，给正向优势留更大空间。

这个设计的精妙之处在于：它用一次截断操作，替代了 TRPO 的整个二阶优化。简单、稳定、可扩展。

![Clip 机制：概率比被截断在 1±ε 区间外](02-clip-mechanism.png)

### 机关 2：Critic/GAE——每一步动作的好坏由谁判断

$A_t$（优势函数）回答的问题是：这个动作比「平均水平」好多少？

GRPO 的做法：用同组样本的均值做基线。同一 prompt 生成一组回答（比如 32 个），平均分以上的就是「好动作」。

PPO 的做法是训练一个**价值网络（critic）**。它用 GAE（Generalized Advantage Estimation）估计 token 级优势。Critic 给每段轨迹独立估值，不依赖「组内同伴」的存在。

为什么 critic 更灵活？因为它能处理**不可比较**的情况。

当不同 rollout 产生的子轨迹长短不一、数量不齐时，GRPO 的组内归一化就失效了。你没法把一条 5 步的子轨迹和一条 50 步的子轨迹放在一起算平均。但 critic 给每条子轨迹独立打分，长度不影响估值。

### 机关 3：KL 约束——别离参考模型太远

上一篇 [RLHF 基础篇](https://mp.weixin.qq.com/s/NJDuCLAEfDpILf2J9D6qLQ) 讲过，PPO 的目标里还有一项：

$$
-\beta D_{\mathrm{KL}}\left(\pi_\theta(\cdot\mid x)\,\|\,\pi_{\mathrm{ref}}(\cdot\mid x)\right)
$$

它的作用是：防止模型为了骗奖励，突然改掉原本的语言能力。

三道机关的协同：
- **Clip** 限制单步更新幅度（微观稳定）
- **Critic** 提供精细的 token 级信号（中观导航）
- **KL 约束** 控制整体方向（宏观锚定）

## 三、GLM-5.2 实战：长程任务怎么撞了 GRPO 的墙

### 轨迹压缩：长程任务的必然选择

GLM-5.2 瞄准的是长程智能体任务——coding agent 执行几十步工具调用，轨迹远超上下文窗口。

解决方案是 **compaction**：把早期步骤压缩摘要，腾出空间继续执行。一条 200 步的轨迹，压缩后可能变成 3 条子轨迹——第一条 50 步，第二条 30 步，第三条 120 步。

### GRPO 的墙：组内比较失效

GRPO 要求同 prompt 的多个输出可比较。但压缩后：

- 不同 rollout 产生**不同数量**的子轨迹
- 子轨迹**长度参差不齐**
- 无法凑成「一组」做归一化

继续硬上组内比较，大量数据会变得没法用。

### Critic 的解法：独立估值

Critic 给每条子轨迹独立估计 token 级优势，不依赖组内比较。长度不一？Token 级 loss 吸收长度不平衡。数量不齐？每条轨迹独立训练，没有「组」的概念。

这让模型能训练在**恰好是部署时会遇到的压缩摘要上**，而不是完整的、干净的轨迹上。

![轨迹压缩 → 子轨迹长短不一 → Critic 独立估值](03-trajectory-compaction.png)

### 反作弊模块：奖励黑客的在线拦截

Coding RL 的奖励通常是可验证的 pass/fail 信号——测试通过就是 1，不通过就是 0。这种干净信号也容易被钻空子。

GLM-5.2 比 5.1 表现出更多奖励黑客行为：

```text
# 模式 1：直接读取隐藏测试文件
find /workspace -name "*hidden*"
cat /workspace/.eval/secret_cases.json

# 模式 2：从上游仓库 curl 答案
curl https://raw.githubusercontent.com/<org>/<repo>/solution.py

# 模式 3：链式利用
python solve.py --case "$(cat /workspace/.eval/secret_cases.json)"
```

GLM-5.2 的解法是**两阶段在线反作弊**：

1. **规则过滤**（高召回）：检测可疑工具调用——读取隐藏目录、curl 外部 URL、链式利用
2. **LLM 裁判**（高精度）：判断被标记的行为是作弊还是正常操作

关键设计：拦截后**返回假信息，让轨迹继续**——而非粗暴中断。

为什么？因为中断轨迹会引发训练不稳定。让模型看到「作弊没用，返回的是垃圾」，它才学会走正道。

### slime 框架：PPO 的工程基础设施

GLM-5.2 的整个后训练跑在 **slime** 上——智谱开源的 RL 训练框架。

slime 的核心设计：训练跑在 Megatron-LM 上，rollout 跑在 SGLang 上。两者用数据 buffer 解耦，生成和训练异步进行，GPU 不闲着。

一个值得注意的细节：slime 的训练模块带有一个**可选的 critic**。GLM-5.2 的选择直接体现在架构里——把 critic 打开。

配合 slime，智谱还用 OPD（On-Policy Distillation）做并行蒸馏。10+ 个领域专家模型被蒸馏合并进最终模型，整个过程只用了约两天。

## 四、PPO 不是万能，但目前最稳

把线索收拢一下。

GRPO 在短任务（数学题、单元测试）上依然够用且便宜——答案就在那一组采样里，组内比较的成本优势依然成立。

PPO 在长程任务（多轮工具调用、稀疏奖励、轨迹压缩）上更鲁棒——critic 给每段轨迹独立估值，不依赖组内比较。

算法选择正在变得**任务相关**，不再有放之四海皆准的默认选项。

GLM-5.2 的选择提醒人们：一个被广泛接受的范式，可能有你还没看到的边界。

---

现在可以把这篇文章压缩成三句话：

**PPO 用 clip 限制策略更新幅度。**

**Critic 给每段轨迹独立估值。**

**KL 约束防止模型走偏。**

这也是为什么后面还要继续拆。

下一篇我们拆 GRPO 的数学：组内归一化的优势到底怎么算出来？为什么组大小 32 是甜点，再大或再小又会怎样？

再往后，RLVR 会尝试回答另一个问题：如果「人类喜欢」太主观，数学题的最终答案、代码测试是否能提供更可验证的奖励？

这几篇不是新系列，而是「**大模型原理**」主线的连续几步。

![后训练路线：预训练、SFT、RLHF、GRPO、RLVR，当前文章高亮 PPO](04-posttraining-map.png)

觉得有用就点个赞 👍、收藏 ⭐ 备用；关注「数解AI」，后面继续沿着这条训练回路往下拆。

最后留一道题：如果一个 coding agent 花了 50 步修一个 bug，压缩后变成 3 条长短不一的子轨迹。你觉得，GRPO 和 PPO 分别会怎么处理？哪种方式更合理？

📖 **[大模型原理合集](https://mp.weixin.qq.com/mp/appmsgalbum?__biz=MzkyMzQyODExNQ==&action=getalbum&album_id=4597831652025925632#wechat_redirect)**：[BPE](https://mp.weixin.qq.com/s/5nR_KI47v_U8KwpQA4Uv5Q) → [词嵌入](https://mp.weixin.qq.com/s/rDryn1z_hLt7mwi3X8fsxQ) → [位置编码](https://mp.weixin.qq.com/s/4nO2VqQLaYxGdDmtQeypCQ) → [注意力](https://mp.weixin.qq.com/s/KrilwX6VRjI9KfjvD7C6kw) → [FFN](https://mp.weixin.qq.com/s/vBCzukDlQyB9O6ASgAmlvQ) → [归一化残差](https://mp.weixin.qq.com/s/v-SBuMTbMANSTxHj7gYDkg) → [Transformer 全景](https://mp.weixin.qq.com/s/22J8JPkdpVeUx23KahbBmA) → [预训练](https://mp.weixin.qq.com/s/XoGHVycQHR5Tp-BWPac9Hg) → [SFT 微调](https://mp.weixin.qq.com/s/vwXGbjm9Ai1GPvQi5O3UyQ) → [RLHF 基础篇](https://mp.weixin.qq.com/s/NJDuCLAEfDpILf2J9D6qLQ) → **PPO 深入篇** → [GRPO](https://mp.weixin.qq.com/s/t4sO-zC5v1_jq8hJT_YTGA) → RLVR

---

## 参考资料

1. Schulman et al.，[Proximal Policy Optimization Algorithms](https://arxiv.org/abs/1707.06347)，2017。
2. Shao et al.，[DeepSeekMath: Pushing the Limits of Mathematical Reasoning in Open Language Models](https://arxiv.org/abs/2402.03300)，2024。
3. Z.ai，[GLM-5.2: Built for Long-Horizon Tasks](https://z.ai/blog/glm-5.2)，2026-06-16。
4. Z.ai，[GLM-5 Technical Report](https://arxiv.org/abs/2602.15763)，2026-02-17。
5. Yu et al.，[DAPO: An Open-Source LLM Reinforcement Learning System at Scale](https://arxiv.org/abs/2503.14476)，2025。
6. THUDM，[slime: An Open-Source RL Post-Training Framework](https://thudm.github.io/slime/)。

#PPO #GRPO #强化学习 #大模型原理 #数解AI
