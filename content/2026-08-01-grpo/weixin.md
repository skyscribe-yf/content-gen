---
title: "GRPO为什么省显存，却撑不住长程任务？"
series: "大模型原理"
author: "数解AI"
type: "算法对比深拆"
keywords: ["GRPO", "PPO", "策略梯度", "组内相对优势", "U-Statistic", "方差-偏差权衡", "DeepSeekMath", "DeepSeek-R1-Zero", "RLVR", "组大小"]
digest: "GRPO 用组内奖励替代 critic，显著降低显存压力，却依赖同 prompt 的可比较样本。本文从 DeepSeekMath、DeepSeek-R1-Zero 到 DAPO，拆解组内相对优势、组大小 G，以及它在长程任务上的边界。"
cover: "00-cover.png"
wechatUrl: "https://mp.weixin.qq.com/s/t4sO-zC5v1_jq8hJT_YTGA"
---

在 [PPO 篇](https://mp.weixin.qq.com/s/OEZtUhm8MT_En7enJo_8dw?token=2031108942&lang=zh_CN) 结尾，智谱 GLM-5.2 做了一个「倒退」决策——在 GRPO 省掉“老师模型”的潮流里，它花了额外显存把 critic（老师模型）请了回来。

但 GLM-5.1 用的正是这篇要拆的算法：**GRPO**（Group Relative Policy Optimization）。

2024 年，DeepSeek 发布了论文 [DeepSeekMath](https://arxiv.org/abs/2402.03300)。这不是后文随手挑的一个模型案例，而是 **GRPO 的起点**：论文首次提出并系统介绍了 GRPO（Group Relative Policy Optimization），把它作为 PPO 的一个变体用于数学推理后训练，因此通常被视为 GRPO 的开山论文。

这篇论文的关键观察是：数学题有标准答案，可以用规则直接判分；如果奖励能够验证，就不必再训练一套大模型去猜每一步的价值。于是，GRPO 不训练专门给每一步估分的价值网络，而是让同一道题生成多份答案，再用组内平均分作参照。它省掉了一套训练网络，也让实现更简单，后来成为开源社区常用的后训练基线。DeepSeek-R1-Zero 再把这条路线推向聚光灯下，用它训练出了会「反思」的推理模型，AIME 2024 的一次作答正确率从 15.6% 提升到 77.9%。

但 GLM-5.2 为什么又放弃了它？

要回答这个问题，得先搞清楚 GRPO 到底怎么工作的，以及它和 PPO 的本质差异。

## 先不用背名词：把强化学习翻成人话

这篇会遇到不少强化学习术语。先把它们翻成一场考试：

- **策略模型**：正在学习“怎么答题”的模型；每次训练都是改一点答题习惯。
- **强化学习（RL）**：模型先试答，再根据分数调整下一次的答法。
- **SFT**：用“指令—示范答案”教模型先学会听懂指令。
- **RLHF**：让人类偏好变成分数，再用强化学习调整模型。
- **奖励（reward）**：这份答案拿到的分数；数学题看最终答案，代码题看测试是否通过。
- **奖励模型**：专门学习“什么回答更好”的评分器；它给的是偏好分，不一定是真实答案。
- **critic**：像老师一样，估计“走到这一步还有没有希望”的模型。
- **基线（baseline）和优势（advantage）**：班级平均分，以及这份答卷比平均分高还是低。
- **参考模型和 KL**：一把“别走太远”的尺子，约束新模型不要突然偏离原来的说话方式。
- **clip**：更新时的刹车，不让模型一次改得过猛。
- **rollout**：让模型完整答一遍题，得到一份答卷和一条过程记录。

所以，PPO 和 GRPO 的区别可以先记成一句话：**PPO 请老师逐步估分，GRPO 让同一道题的多份答卷互相比较。**

上一篇 [PPO](https://mp.weixin.qq.com/s/OEZtUhm8MT_En7enJo_8dw?token=2031108942&lang=zh_CN) 已经细拆了 clip、critic 和 KL。本文先讲直觉，再给出 GRPO 的核心公式；更细的估计器推导和强化学习术语，暂不在这里展开。

## 一、GRPO 的诞生

### DeepSeekMath：GRPO 为什么从数学题开始

回到这篇开山论文，DeepSeekMath 首先面对的是 PPO 的一个工程痛点：critic 网络和策略模型一样大。

一个 70B 的模型做典型 RLHF，往往要同时处理策略模型、critic 模型、奖励模型、参考模型——约 4 份模型权重。真正的显存还要加上优化器、激活值和 rollout 缓存，critic 往往是最重的一项额外开销。

DeepSeekMath 的核心观察是：**对于有确定性答案的任务，不需要神经网络当裁判**。

数学题有标准答案，代码测试有编译器判分。规则就能给出 0/1 奖励，为什么要额外训练一个 critic 来「猜」每步的好坏？

GRPO 的改动很直接：**去掉 critic，用同 prompt 多样本的组内平均奖励做基线**。

### DeepSeek-R1-Zero：“等等，我再检查一遍”

2025 年，DeepSeek-R1-Zero 把 GRPO 推向了聚光灯下。

R1-Zero 的训练流程更激进——**不先做 SFT，直接在 DeepSeek-V3 Base 上做 GRPO**。模型从基础模型出发，通过纯强化学习自发学会了推理。

这里要把两个名字分开：**R1-Zero 是纯 RL 路线，R1 不是**。完整的 R1 加入了冷启动数据、拒绝采样、SFT 和后续 RL。

结果让人坐不住：

- AIME 2024 数学竞赛的一次作答正确率（pass@1）从 15.6% → 77.9%。
- 让模型回答 16 次再投票，自一致性得分（cons@16）达到 86.7%。
- 模型自发出现了**反思**行为：「等等，我算错了，让我重新检查一遍」。
- 推理链自然变长，从几百 token 到几千 token。

这些行为不是人工写进规则的，而是在 GRPO 训练中涌现出来的。

DeepSeek-R1-Zero 的奖励系统很简单：

- **正确性分数**：答案正确得 1，错误得 0。
- **格式分数**：推理过程放在 `<think></think>` 标签内得 1，否则 0；两类分数同权。

没有奖励神经网络模型，也不依赖人工偏好标签，核心信号来自可验证规则。

### 为什么 GRPO 成了新默认

三个原因：

1. **少一套大模型训练**。不需要训练 critic；是否能从 4 份降到 2 份，还取决于是否使用奖励模型和参考模型。
2. **少一组估值超参**。省掉老师模型的训练和逐步估分设置，但新增了组大小 $G$、采样预算等选择。
3. **实现简单**。TRL 等工具提供现成的训练器，实验原型可以快速跑起来。

从 DeepSeekMath、R1-Zero 到 DAPO 等公开系统，围绕 GRPO 的复现和变体越来越多。

但 GRPO 真的是万能的吗？

![PPO vs GRPO 架构对比：critic 网络 vs 组内归一化](01-ppo-vs-grpo.png)

## 二、GRPO 的核心机制

### 先用一场考试看懂 GRPO

把同一个 prompt 想成同一道题，把模型生成的 $G$ 个答案想成 $G$ 份答卷。

数学题的标准答案、代码题的测试程序，就是自动裁判。这个裁判就是 verifier（验证器）。

GRPO 不请老师逐步批改，而是先看全班平均分：

- 高于平均分的答卷，得到正向信号，之后更容易被模型保留。
- 低于平均分的答卷，得到负向信号，之后出现的概率会下降。
- 全班都对或全班都错时，大家分数一样，没有“谁更好”的方向。

这就是“组内相对优势”。整份答卷共用一个总评，叫 output-level；每个答题步骤分别评分，才是 token-level。GRPO 的基础版本采用前者，所以省掉了老师，却牺牲了逐步判断的细致程度。

### 算法流程：4 步

下面只是把刚才的考试类比换成符号。

**Step 1：采样**

对每个 prompt $q$，从旧策略 $\pi_{\theta_{old}}$ 采样 $G$ 个输出：

$$\{o_1, o_2, \cdots, o_G\} \sim \pi_{\theta_{old}}(\cdot \mid q)$$

$G$ 是组大小。DeepSeekMath 论文使用 64；工程上它是可以按任务难度和采样预算调节的超参数，不是固定标准。

**Step 2：计算奖励**

用奖励函数（或规则）计算每个输出的奖励：

$$r_i = R(q, o_i)$$

**Step 3：组内归一化**

这是 GRPO 的核心。把组内奖励做标准化（z-score）：先减去平均分，再除以这组分数的波动幅度，得到相对优势：

$$\hat{A}_{i,t} = \frac{r_i - \text{mean}(\{r_1, r_2, \cdots, r_G\})}{\text{std}(\{r_1, r_2, \cdots, r_G\})}$$

注意一个关键细节：在“最终答案打分”的基础实现里，**优势在整个序列上是常数**（output-level），不是 token-level。同一个输出里的每个 token 共享同一个优势值。工程实现通常还会给标准差加数值稳定项。

**Step 4：策略更新**

这一步先不用怕公式。$q$ 是题目，$o_i$ 是第 $i$ 份答卷，$\hat A_{i,t}$ 是“这份答卷比平均分高还是低”。

$\rho_{i,t}(\theta)$ 是新模型和旧模型给同一个 token 的概率比；`clip` 就是刹车，防止一次改得太猛；$\beta$ 和 KL 则控制模型不要离参考模型太远。

把这几个词对上号，再看目标函数：

$$
\begin{aligned}
J_{GRPO}(\theta)=\mathbb{E}\Bigg[&\frac{1}{G}\sum_{i=1}^{G}\frac{1}{|o_i|}
\sum_{t=1}^{|o_i|}\min\Big(\rho_{i,t}(\theta)\hat A_{i,t},\\
&\quad \operatorname{clip}(\rho_{i,t}(\theta),1-\epsilon,1+\epsilon)\hat A_{i,t}\Big)
 -\beta D_{\mathrm{KL}}(\pi_\theta\|\pi_{\mathrm{ref}})\Bigg]
\end{aligned}
$$

其中

$$\rho_{i,t}(\theta)=\frac{\pi_\theta(o_{i,t}\mid q,o_{i,1:t-1})}{\pi_{\theta_{old}}(o_{i,t}\mid q,o_{i,1:t-1})}$$

这里的 $o_{i,1:t-1}$ 表示第 $i$ 份答卷在第 $t$ 个 token 之前的前缀。

上式是原始 GRPO 常见的“先按响应平均，再按组平均”写法。后续变体会改变“答案长度如何计入训练”，这里先不展开。

### KL：先把它当成“别走太远”的尺子

公式里的 KL，可以先理解成“新模型和旧模型差了多远”。它让模型追求更高分时，不要突然改掉原本的语言习惯。

有些 GRPO 配置会关掉 KL，有些会保留一个很小的约束。工程库通常都允许这样配置。KL 的单样本估计器和稳定性推导，留给后面的强化学习专题细说。

## 三、PPO vs GRPO 全维度对比

### 1. 显存开销

| 组件 | PPO（典型 RLHF） | GRPO（规则奖励） |
|------|------------------|------------------|
| 策略模型 | ✅ | ✅ |
| Critic 模型 | ✅（通常与策略等大） | ❌ |
| 奖励模型 | ✅ | ❌（由 verifier 判分） |
| 参考模型 | ✅ | 可选；$\beta=0$ 时通常不加载 |
| **模型权重粗算** | **约 4 份** | **约 1～2 份** |

对 70B 模型而言，一份 bf16（半精度）权重约 140GB：PPO 的 4 份约 560GB，GRPO 通常约 140～280GB。实际总显存还要加优化器、激活值和生成缓存，所以“减半”只是模型组件的粗算，不是端到端训练显存。

### 2. 优势估计：独立估值 vs 组内比较

这是两种算法最本质的差异。

**PPO 的 critic** 给每个 token 独立估计价值——「这个位置的 token 比平均水平好多少？」粒度精细，但需要额外训练。

**GRPO 的组归一化** 给整个输出打一个分——「这个输出比同组同伴好多少？」粒度粗（output-level），但零 critic 训练成本。如果每一步都有单独分数，优势也可以改成 token-level；这里先不展开。

一个关键后果：长序列中某个关键转折点（比如推理链中的 aha moment）的信号会被整个序列的平均奖励稀释。

### 3. 方差-偏差权衡

这是理解 PPO/GRPO 选择的核心框架。

![方差-偏差权衡示意：PPO 通常低方差，GRPO 的组均值基线在有限 G 下方差更高](03-variance-bias.png)

图中的“零偏差”是理想化标注：它假设只使用组均值基线，不加入标准化、长度归一化等工程修正。真实训练的偏差要看具体实现。

这里的“方差”可以理解成同一道题多答几次，结果会不会忽上忽下；“偏差”则是估分方法是否长期偏向某类答案。

**PPO（critic）**：通常低方差，但会继承 critic 的近似误差。Critic 估计不完美，但每次估计往往更稳定。

**GRPO（组均值）**：在不做额外标准化的理想化推导里，不引入 critic 的估值偏差，但有限组大小下方差较高。实际标准化、长度归一化和截断处理，可能重新带来偏差。

方差随 $G$ 增大而降低（$O(1/G)$），但采样成本线性增长。

![组大小 G 与梯度估计误差（MSE）的关系：GSM8K 与 Qwen2.5-1.5B-Instruct 的实验设置](02-group-size-mse.png)

Zhou et al. (2026) 从理论上证明了**最优组大小**的存在：

$$G^* = \sqrt{\frac{c_3}{c_1}}$$

其中 $c_1$、$c_3$ 是误差分解中的系数，分别反映 prompt 层面和组内估计的波动。**在论文的简化成本模型和主导项假设下，$G^*$ 只依赖数据与模型，不随训练预算线性变化**；它不是所有任务都通用的固定常数。

实验验证：

- GSM8K 数据集 + Qwen2.5-1.5B-Instruct：多数设置在 $G^* \approx 32$ 附近
- MATH 数据集 + Qwen2.5-Math-7B：多数设置在 $G^* \approx 64$ 附近；预算增大时有设置升到 128

这些是论文实验范围内的结果，不是“模型越大，G 就一定越大”的经验公式。

### 4. 理论旁注：为什么 $G$ 不是越大越好

Zhou et al. (2026) 把 GRPO 的组内比较写成了二阶 U-Statistic。

这个名字先不用背。通俗说，它研究的是“同一道题生成多份答卷，再用答卷之间的比较估计更新方向”这件事，能不能比单独请老师估分更划算。

结论只有两句：$G$ 变大，平均分更稳定；但每道题都要多生成答案，采样成本也会变高。因此，真实训练里通常存在一个折中点。

完整的数学分解、理想基线和误差证明，放到后面的强化学习专题再细说。这里先记住：理论结论依赖简化假设，不能把某个实验里的 $G^*$ 当成通用常数。

### 5. 全维度对比表

| 对比维度 | PPO | GRPO |
|---------|-----|------|
| 显存 | 约 4 份模型权重 | 约 1～2 份，取决于 verifier/KL |
| 额外训练 | critic 网络 | 无 critic |
| 优势粒度 | token-level | output-level（最终答案打分时） |
| 方差-偏差 | 通常低方差，但有 critic 近似误差 | 有限 $G$ 方差高；标准化可能引入偏差 |
| 长程任务 | 有独立价值估计，但不自动解决“哪一步该记功” | 组内比较条件更苛刻 |
| 短任务 | 可用但贵 | 便宜且稳定 |
| 超参敏感性 | 老师模型的训练设置、更新步长 | 组大小、KL 强度、更新幅度 |
| 奖励黑客 | 取决于 reward model/verifier | 同样取决于 reward；相对排名不保证绝对质量 |
| 理论结论 | 依赖 critic 估计质量 | 特定假设下有组内统计分析 |

## 四、GRPO 的边界：什么时候站不住

### 1. 零方差问题

当一组样本的奖励全部相同——全对（$r_i = 1$）或全错（$r_i = 0$），标准差 $\text{std}(\mathbf{r}) = 0$，归一化公式分母为零。

实现会给分母加一个很小的数，避免程序报错。但这只是补丁，核心问题仍然存在：**大家分数一样，模型就不知道该往哪个方向改**。后面的 DAPO 会用筛选和重采样，尽量减少这种组。

### 2. 长程任务的墙

[PPO 篇](https://mp.weixin.qq.com/s/OEZtUhm8MT_En7enJo_8dw?token=2031108942&lang=zh_CN)详细讲过这个问题。

Coding agent 执行几十步工具调用，轨迹远超上下文窗口。Compaction（轨迹压缩）会把前面的多步操作总结成短记忆，也会让每次完整执行的边界和长度变得不整齐。

GRPO 仍然可以为同一个 prompt 采样多个输出。
但压缩后，组内比较会更脆弱：

- 不同 rollout 可能在不同阶段结束。
- 子轨迹**长度参差不齐**，最终奖励更难定位到具体步骤。
- 同一个分数不一定代表完成了同样多的工作。

所以问题不是“算法绝对无法成组”，而是一个整段回答的相对分数，越来越难回答“到底哪一步做对了”。这就是长程任务的步骤归因问题。

Critic 可以为每个状态独立估计价值，减少对同组样本的依赖；但它也不能自动解决工具调用中的步骤归因。

### 3. 奖励黑客的温床

GRPO 用组内相对排名，模型可能学会的不是「做对」，而是「比同伴差得少」。

R1-Zero 使用规则奖励，降低了奖励神经网络模型被钻空子的空间；但格式奖励和验证器本身仍然需要防护，不能把规则奖励等同于绝对不会被钻空子。

如果使用奖励神经网络模型（reward model），模型可能不是真正变好，而只是学会让自己的分数高于同组同伴；PPO 和 GRPO 都会遇到这个问题，比较基线并不能替代好的 verifier。

### 4. 任务长度的限制

GRPO 的优势在 output-level——整个输出共享一个优势值。

长序列中，可能只有少数几个 token 是关键的推理转折点（比如「等等，我算错了」），其余都是常规推理。但 GRPO 无法区分这些 token 的贡献差异。

DAPO（2025）等后续工作改成按 token 汇总训练信号，并调整长度处理，部分缓解了这个问题，但不会自动恢复每个 token 的真实功劳。

## 五、GRPO 的进化

GRPO 不是终点，而是一个起点。2025 年涌现了大量变体：

### Dr.GRPO（2025）

原始 GRPO 会按答卷长度做归一化，长答案和短答案可能因此被赋予不同权重。Dr.GRPO 用固定长度常数替代这个分母，先解决“答案写得长就改变分数权重”的问题。

### DAPO（2025）

字节跳动开源的大规模 RL 系统，对 GRPO 做了四个直观改动：

1. **动态采样**。过滤全对、全错的题目，避免没有区分度的组。
2. **Clip-higher**。给“明显更好”的答案多留一点更新空间。
3. **按 token 汇总**。减少回答长度对训练权重的影响，但不等于知道每个 token 的真实功劳。
4. **处理超长输出**。过滤或轻微惩罚被截断的答案，减少噪声。

### GPG（2025）

GPG 继续做减法：不使用 critic、参考模型和 KL，直接根据答卷分数调整策略。这里先把它理解成“更轻的 GRPO 训练路线”，具体推导留给后面的强化学习专题。

### 为什么 GRPO 在 2026 年依然是默认

不是因为它是最好的算法，而是因为它在**性价比**上无人能及。

- 短任务（数学题、代码测试、单元测试）上效果稳定。
- 模型权重和训练组件通常少于典型 PPO，但具体节省取决于 verifier 与 KL 配置。
- 开源工具链成熟（如 TRL 等）。
- 理论分析逐渐完善（组内统计和最优组大小）。

GLM-5.2 的选择提醒人们：**算法选择正在变得任务相关**。短任务用 GRPO 往往又便宜又稳；长程任务可能需要 critic，或需要更强的过程奖励、状态建模和轨迹切分方案。

---

现在可以把这篇文章压缩成三句话：

**GRPO 用组内奖励替代 critic，显著降低额外模型的显存压力。**

**组大小** $G$ **是核心超参，特定实验设定下存在最优值** $G^*$。

**短任务更适合 GRPO，长程任务要重新检查组比较和步骤归因。**

这也是为什么后面还要继续拆。

下一篇我们进入 RLVR（可验证奖励强化学习）：如果“人类喜欢”太主观，数学题的最终答案、代码测试的 pass/fail，能否提供更可验证的奖励？GRPO 的可验证奖励变体正在重塑后训练的奖励设计范式。

这几篇不是新系列，而是「**大模型原理**」主线的连续几步。

![后训练路线：预训练、SFT、RLHF、PPO、GRPO、RLVR，当前文章高亮 GRPO](04-posttraining-map.png)

觉得有用就点个赞 👍、收藏 ⭐ 备用；关注「数解AI」，后面继续沿着这条训练回路往下拆。

最后留一道题：如果一个 prompt 生成了 16 个输出，其中 15 个全错、1 个全对——你会扩大 $G$ 来增加可比较样本，还是先改 verifier 或采样策略？为什么？

📖 **[大模型原理合集](https://mp.weixin.qq.com/mp/appmsgalbum?__biz=MzkyMzQyODExNQ==&action=getalbum&album_id=4597831652025925632#wechat_redirect)**： [BPE](https://mp.weixin.qq.com/s/5nR_KI47v_U8KwpQA4Uv5Q) → [词嵌入](https://mp.weixin.qq.com/s/rDryn1z_hLt7mwi3X8fsxQ) → [位置编码](https://mp.weixin.qq.com/s/4nO2VqQLaYxGdDmtQeypCQ) → [注意力](https://mp.weixin.qq.com/s/KrilwX6VRjI9KfjvD7C6kw) → [KDA 长上下文](https://mp.weixin.qq.com/s/_RR5LLWgjGNm-qXdSdnAGA) → [FFN](https://mp.weixin.qq.com/s/vBCzukDlQyB9O6ASgAmlvQ) → [归一化残差](https://mp.weixin.qq.com/s/v-SBuMTbMANSTxHj7gYDkg) → [Transformer 全景](https://mp.weixin.qq.com/s/22J8JPkdpVeUx23KahbBmA) → [预训练](https://mp.weixin.qq.com/s/XoGHVycQHR5Tp-BWPac9Hg) → [Kimi K3 架构](https://mp.weixin.qq.com/s/6GJ2781jJh-dqYswJ07dfA?token=1097302935&lang=zh_CN) → [SFT 微调](https://mp.weixin.qq.com/s/vwXGbjm9Ai1GPvQi5O3UyQ) → [RLHF 基础篇](https://mp.weixin.qq.com/s/NJDuCLAEfDpILf2J9D6qLQ) → [PPO 深入篇](https://mp.weixin.qq.com/s/OEZtUhm8MT_En7enJo_8dw?token=2031108942&lang=zh_CN) → **GRPO 深拆** → RLVR

---

## 参考资料

1. Shao et al., [DeepSeekMath: Pushing the Limits of Mathematical Reasoning in Open Language Models](https://arxiv.org/abs/2402.03300), 2024.
2. Guo et al., [DeepSeek-R1: Incentivizing Reasoning Capability in LLMs via Reinforcement Learning](https://www.nature.com/articles/s41586-025-09422-z), Nature, 2025.
3. Mroueh, [Reinforcement Learning with Verifiable Rewards: GRPO's Effective Loss, Dynamics, and Success Amplification](https://arxiv.org/abs/2503.06639), 2025.
4. Zhou et al., [Demystifying Group Relative Policy Optimization: Its Policy Gradient is a U-Statistic](https://arxiv.org/abs/2603.01162), 2026.
5. Liu et al., [Understanding R1-Zero-Like Training: A Critical Perspective](https://arxiv.org/abs/2503.20783), 2025.
6. Yu et al., [DAPO: An Open-Source LLM Reinforcement Learning System at Scale](https://arxiv.org/abs/2503.14476), 2025.
7. Chu et al., [GPG: A Simple and Strong Reinforcement Learning Baseline for Model Reasoning](https://arxiv.org/abs/2504.02546), 2025.
8. TRL Documentation, [GRPO Trainer](https://huggingface.co/docs/trl/v0.25.1/en/grpo_trainer).

#GRPO #强化学习 #大模型原理 #DeepSeek #数解AI
