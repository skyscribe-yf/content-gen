# 大纲：GRPO 深拆——为什么省显存，却撑不住长程任务？

## 元信息
- 系列：大模型原理
- 作者：数解AI
- 类型：算法对比深拆
- 关键词：GRPO, PPO, 策略梯度, 组内相对优势, U-Statistic, 方差-偏差权衡, DeepSeekMath, DeepSeek-R1-Zero, RLVR, 组大小
- 案例模型：DeepSeekMath（GRPO 首发论文/开山论文）+ DeepSeek-R1-Zero（纯 RL）+ Qwen2.5 复现实验
- 上一篇：PPO 深入篇
- 下一篇预告：RLVR——可验证奖励的新范式

---

## 开头（~300 字）

**钩子**：PPO 篇结尾，智谱 GLM-5.2 做了一个「倒退」决策——在 GRPO 省掉 critic 的潮流里，它花了额外显存把 critic 请了回来。但 GLM-5.1 用的正是这篇要拆的算法：GRPO（Group Relative Policy Optimization）。

**核心问题**：GRPO 到底是什么？它怎么做到不用 critic 也能训练？为什么在数学题、代码测试上又便宜又稳，到了长程任务上组内比较却更脆弱？

**PPO 篇回响**：PPO 有三道机关——clip、critic、KL 约束。GRPO 去掉 critic，用组内奖励估计基线；KL 是否保留则由配置决定，TRL 默认可以关闭。它不是“只剩 clip”的唯一固定配方。

## 阅读地图：先把名词翻成人话

- 策略模型：正在学习“怎么答题”的模型
- 奖励：答案拿到的分数
- critic：像老师一样，估计每一步还有没有希望
- 基线/优势：班级平均分，以及某份答卷比平均分高还是低
- 参考模型/KL：约束新模型不要突然偏离原来的答题习惯
- 先用“同一道题的多份答卷互相比较”建立直觉，后面只保留 GRPO 的核心公式；KL 估计器、U-Statistic 完整推导放到后续强化学习专题

---

## 一、GRPO 的诞生：从 DeepSeekMath 到 DeepSeek-R1-Zero（~500 字）

- 先说明 DeepSeekMath 不是普通案例：2024 年论文首次提出并系统介绍 GRPO，通常被视为 GRPO 的开山论文
- 这篇论文把 GRPO 作为 PPO 的变体用于数学推理后训练，后来的 R1-Zero、DAPO 等沿着这条路线继续发展
- 数学题有标准答案，可以用规则直接判分；如果奖励能够验证，就不必再训练一套大模型去猜每一步价值
- PPO 的 critic 网络和策略模型一样大，显存翻倍、训练成本翻倍
- 核心改动：不训练价值网络，用同 prompt 多样本的组内平均奖励做基线

### DeepSeek-R1-Zero：纯 RL 的「aha moment」
- 直接在 DeepSeek-V3 Base 上用 GRPO 做 RL，**R1-Zero 不先做 SFT**；完整 R1 则加入冷启动、SFT 和后续 RL
- AIME 2024 从 15.6% → 77.9%（pass@1），自一致性达到 86.7%（cons@16）
- 模型自发学会了反思、验证、延长推理链
- 关键规则：rule-based reward（accuracy + format），不用奖励神经网络模型

### 为什么 GRPO 能成为开源社区新默认
- 少一套 critic 模型和训练成本，是否减半取决于 verifier/KL 配置
- 短任务（数学题、单元测试）上效果稳定
- 实现简单，TRL 提供现成的 `GRPOTrainer`
- 从 DeepSeekMath、R1-Zero 到 DAPO 等公开系统，复现和变体越来越多

---

## 二、GRPO 的核心机制：组内相对优势（~800 字）

### 先用一场考试看懂 GRPO
- 同一个 prompt = 同一道题
- $G$ 个输出 = $G$ 份答卷
- verifier = 数学标准答案或代码测试程序
- 高于平均分的答卷增加概率，低于平均分的答卷降低概率
- 整份答卷一个总评是 output-level；每个步骤分别评分是 token-level

### 算法流程（4 步）
1. **采样**：对每个 prompt $q$，从旧策略 $\pi_{\theta_{old}}$ 采样 $G$ 个输出 $\{o_1, o_2, ..., o_G\}$
2. **计算奖励**：用奖励函数/规则计算每个输出的奖励 $r_i = R(q, o_i)$
3. **组内归一化**：计算相对优势
   $$\hat{A}_{i,t} = \frac{r_i - \text{mean}(\mathbf{r})}{\text{std}(\mathbf{r})}$$
   - 最终答案打分时，优势在整个序列上是常数（output-level），不是 token-level；工程实现会处理零标准差
4. **策略更新**：最大化 GRPO 目标函数

### 完整目标函数
$$
J_{GRPO}(\theta)=\mathbb{E}\left[\frac{1}{G}\sum_{i=1}^{G}\frac{1}{|o_i|}
\sum_{t=1}^{|o_i|}\min\left(\rho_{i,t}\hat A_{i,t},
\operatorname{clip}(\rho_{i,t},1-\epsilon,1+\epsilon)\hat A_{i,t}\right)
-\beta D_{\mathrm{KL}}(\pi_\theta\|\pi_{\mathrm{ref}})\right]
$$

其中 $\rho_{i,t}=\pi_\theta(o_{i,t})/\pi_{\theta_{old}}(o_{i,t})$。原始 GRPO 按响应平均、再按组平均；后续变体会改变答案长度如何计入训练。

### KL：先理解成“别走太远”的尺子
- KL 先理解成新模型和旧模型差了多远
- 有些 GRPO 配置会关掉 KL，有些保留小约束
- 单样本估计器和稳定性推导留到后续强化学习专题

---

## 三、PPO vs GRPO 全维度对比（~1200 字）

### 1. 显存开销
- PPO：策略模型 + critic 模型 + 奖励模型 + 参考模型 ≈ 4 份模型权重
- GRPO：策略模型 + 可选参考模型；规则奖励时通常不需要奖励模型 ≈ 1～2 份权重
- 70B bf16 一份约 140GB；这是模型权重粗算，实际还要计入优化器、激活值和 rollout 缓存

### 2. 优势估计：独立估值 vs 组内比较

| 维度 | PPO (critic) | GRPO (组内归一化) |
|------|-------------|------------------|
| 估值粒度 | token-level | output-level（序列内常数） |
| 独立性 | 每条轨迹独立估值 | 依赖同组其他样本 |
| 训练成本 | 需训练 critic | 零额外训练 |
| 长程适应性 | 不受轨迹压缩影响 | 组内比较失效 |

### 3. 方差-偏差权衡
- **PPO 的 critic**：通常低方差，但会继承 critic 的近似误差
- **GRPO 的组均值**：理想化设定下不含 critic 近似误差，但有限 $G$ 时方差高；标准化和长度处理可能引入偏差
- $G$ 越大，方差越低（$O(1/G)$），但采样成本线性增长
- **最优组大小**：Zhou et al. (2026) 在简化成本模型下给出 $G^* = \sqrt{c_3/c_1}$
  - GSM8K + Qwen2.5-1.5B-Instruct：多数设置在 $G^* \approx 32$ 附近
  - MATH + Qwen2.5-Math-7B：多数设置在 $G^* \approx 64$ 附近，预算增大时有设置升到 128

### 4. 理论旁注：为什么 $G$ 不是越大越好
- Zhou et al. (2026) 把 GRPO 的组内比较写成二阶 U-Statistic
- 通俗理解：研究同一道题的多份答卷互相比较，能否比单独请老师估分更划算
- 结论：$G$ 变大，平均分更稳定；但每道题要多生成答案，采样成本也会增加
- 完整数学分解和误差证明放到后续强化学习专题

### 5. 对比总结表

| 对比维度 | PPO | GRPO |
|---------|-----|------|
| 显存 | 约 4 份模型权重 | 约 1～2 份，取决于 verifier/KL |
| 额外训练 | critic 网络 | 无 critic |
| 优势粒度 | token-level | output-level |
| 方差-偏差 | 通常低方差，但有 critic 近似误差 | 有限 $G$ 方差高；标准化可能引入偏差 |
| 长程任务 | 有独立价值估计，但不自动解决“哪一步该记功” | 组内比较条件更苛刻 |
| 短任务 | 可用但贵 | 便宜且稳定 |
| 超参敏感性 | 老师模型的训练设置、更新步长 | 组大小、KL 强度、更新幅度 |
| 奖励黑客 | 取决于 reward model/verifier | 同样取决于 reward；相对排名不保证绝对质量 |

---

## 四、GRPO 的边界：什么时候站不住（~600 字）

### 1. 零方差问题
- 当一组样本的奖励全部相同（全 0 或全 1），$\text{std}(\mathbf{r}) = 0$，归一化失效
- 实践中：用数值稳定项保护分母，但“大家分数一样，模型没有更新方向”这个问题仍在
- DAPO 通过动态采样过滤或重采样全对、全错的 prompt

### 2. 长程任务的墙
- PPO 篇已讲：轨迹压缩后完整执行的状态边界和完成长度更不整齐
- GRPO 仍可采样同 prompt 的多个输出，但最终分数更难定位到具体步骤
- 问题不是绝对无法成组，而是组内比较和长程步骤归因更脆弱
- Critic 可提供独立价值估计，但也不自动解决工具调用中的步骤归因

### 3. 奖励黑客的温床
- GRPO 用组内相对排名，模型可能学会「比同伴差得少」而非「做对」
- R1-Zero 使用规则奖励（正确性 + 格式），降低奖励神经网络模型被钻空子的空间
- 但 verifier 和格式奖励仍需防护；使用奖励神经网络模型时，两种算法都可能被钻空子

### 4. 任务长度的限制
- GRPO 的优势在 output-level（序列级），无法区分序列内哪些 token 贡献更大
- 长序列中关键转折点（如 aha moment）的信号被稀释
- DAPO（2025）等后续工作改成按 token 汇总训练信号，并调整长度处理，部分缓解这个问题

---

## 五、GRPO 的进化：从 DeepSeekMath 到 DAPO（~400 字）

### 关键变体
- **Dr.GRPO**（2025）：用固定长度常数替代原始 GRPO 的逐响应长度分母，修正响应长度偏差
- **DAPO**（2025）：
  - 动态采样：过滤全对/全错的 prompt
  - Clip-higher：给“明显更好”的答案多留一点更新空间
  - 按 token 汇总：减少回答长度对训练权重的影响
  - Overlong 处理：过滤或软惩罚截断输出，减少噪声
- **GPG**（2025）：不使用 critic、参考模型和 KL，直接根据答卷分数调整策略

### 为什么 GRPO 在 2026 年依然是默认
- 开源工具链成熟（如 TRL）
- 短任务（数学、代码）上性价比无人能及
- 理论分析逐渐完善（组内统计和最优组大小）

---

## 结尾（~200 字）

- 三句话总结：
  - GRPO 用组内奖励替代 critic，显著降低额外模型的显存压力。
  - 组大小 $G$ 是核心超参，特定实验设定下存在最优值 $G^*$。
  - 短任务更适合 GRPO，长程任务要重新检查组比较和步骤归因。

- 系列预告：
  - 下一篇——RLVR：如果人类偏好太主观，数学题的最终答案、代码测试的 pass/fail，能否提供更可验证的奖励？
  - GRPO 的可验证奖励变体正在重塑后训练的奖励设计范式。

- 关注引导 + 合集链接

---

## 预计字数
~3500 字（不含公式、图表说明）

## 预计配图
1. PPO vs GRPO 架构对比图（critic vs 组内归一化）
2. 组大小 $G$ 与梯度估计 MSE 的关系曲线（示意最优 $G^*$）
3. 方差-偏差权衡示意图（理想化设定下的有限 $G$ 对比）
4. 后训练路线图（预训练 → SFT → RLHF → PPO → GRPO → RLVR，当前文章高亮 GRPO）

## 关键公式清单
- 组内归一化优势：$\hat{A}_{i,t} = \frac{r_i - \text{mean}(\mathbf{r})}{\text{std}(\mathbf{r})}$
- GRPO 目标函数（clip + KL）
- KL 的直觉解释（单样本估计器留到后续专题）
- 最优组大小：$G^* = \sqrt{c_3/c_1}$
- 二阶 U-Statistic 表示

## 参考资料
1. Shao et al., "DeepSeekMath: Pushing the Limits of Mathematical Reasoning in Open Language Models", 2024.
2. Guo et al., "DeepSeek-R1: Incentivizing Reasoning Capability in LLMs via Reinforcement Learning", 2025.
3. Mroueh, "Reinforcement Learning with Verifiable Rewards: GRPO's Effective Loss, Dynamics, and Success Amplification", 2025.
4. Zhou et al., "Demystifying Group Relative Policy Optimization: Its Policy Gradient is a U-Statistic", 2026.
5. Liu et al., "Understanding R1-Zero-Like Training: A Critical Perspective", 2025.
6. Yu et al., "DAPO: An Open-Source LLM Reinforcement Learning System at Scale", 2025.
7. TRL Documentation, "GRPO Trainer".
