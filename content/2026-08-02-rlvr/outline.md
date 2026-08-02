# RLVR：可验证奖励怎么重塑后训练？

## 元信息

- 系列：大模型原理（收官篇）
- 发布目录：`2026-08-02-rlvr`
- 作者：数解AI
- 类型：后训练范式篇 / 系列收束篇
- 标题：RLVR：可验证奖励怎么重塑后训练？
- 核心关键词：RLVR、可验证奖励、Reward hacking、specification gaming、verifier、DeepSeek-R1、coding agent、Agent、PPO、GRPO、credit assignment、过程奖励
- 核心主张：RLVR 不是又一个策略优化算法，而是奖励设计的范式转折。当任务结果可以被可靠验证时，verifier 能提供比主观偏好更直接的反馈；但模型优化的是 verifier 能检测到的目标，Reward hacking 因此成为 RLVR 的内在边界。
- 主案例：DeepSeek-R1/R1-Zero（数学、代码与规则奖励）+ SWE-RL（真实软件工程）+ L0（多轮 code-as-action Agent + RLVR）
- 最新模型旁注：DeepSeek-V4-Flash-0731 的 `config.json` 只说明架构与上下文能力，不说明奖励配方；用它强调“模型结构”和“后训练反馈”是两层问题。必要时用 Qwen3-8B `config.json` 作为轻量 policy model 的架构锚点。
- 上一篇：[GRPO：为什么省显存，却撑不住长程任务？](https://mp.weixin.qq.com/s/t4sO-zC5v1_jq8hJT_YTGA)
- 前置回引：[RLHF 基础篇](https://mp.weixin.qq.com/s/NJDuCLAEfDpILf2J9D6qLQ)、[PPO 深入篇](https://mp.weixin.qq.com/s/OEZtUhm8MT_En7enJo_8dw?token=2031108942&lang=zh_CN)

## 文章设计

### 读者读完要得到的答案

1. RLVR、PPO、GRPO 分别解决什么问题，为什么不能把它们当成同义词。
2. 数学题的最终答案、代码测试和 Agent 环境状态，怎样变成可学习的奖励。
3. 为什么一个看似只有 0/1 的代码奖励，能够强化规划、工具调用、修改代码、运行测试和反复纠错等多步 Agent 行为。
4. Reward hacking 为什么不是偶然 bug，而是“优化可测指标”与“真实目标”之间的结构性风险。
5. RLVR 会重塑哪些后训练任务，又在哪些开放式任务上仍然需要 RLHF、奖励模型或人工反馈。

### 叙事主线

从前几篇的训练回路递进开始：

> RLHF 解决“人类喜欢什么”；PPO 解决“策略如何稳定更新”；GRPO 解决“没有 critic 时如何估计相对优势”；RLVR 进一步追问：如果任务结果可以自动验证，奖励能否不再依赖主观偏好？

随后抛出反直觉问题：

> 一个 coding agent 只在最终测试通过时得 1、失败得 0，中间没有人告诉它哪一步写得好。它为什么还能逐渐学会拆任务、调用工具、修改代码、运行测试并反复纠错？

答案分两层推进：

- 可执行环境把代码任务变成了一个能反复试错的世界；
- 策略优化把“成功轨迹”的概率整体推高，但并不保证每一步都真正有益。

第三层再转折到 Reward hacking：

> verifier 更客观，不等于 verifier 不会被钻空子。模型优化的始终是可观测的代理目标。

## 开头：只有 0/1 的奖励，为什么能教出 Agent？（约 450 字）

- 场景：Agent 读取仓库、修改文件、运行测试、看到失败、再次修改；训练器最后只收到“通过 / 不通过”。
- 直接提出反直觉问题：没有逐步老师，为什么会出现规划、工具使用、反思和纠错？
- 用一段话衔接系列：
  - 预训练让模型学会预测 token；
  - SFT 让模型听懂指令；
  - RLHF 让模型靠人类偏好选择更好的回答；
  - PPO 与 GRPO 解决策略怎样利用奖励更新；
  - RLVR 把问题推进到“结果是否可以自动验证”。
- 文章承诺：先定义 RLVR，再拆最小训练闭环；随后解释 coding → Agent 的迁移；最后用 Reward hacking 检查“可验证”到底有多可靠，并完成全系列回顾。
- 开头只保留一个数字事实，避免用未核验的模型宣传数字；所有实验数字放入正文对应案例段落并注明来源。

## 一、RLVR 不是 GRPO：先把两个维度拆开（约 650 字）

### 1. 奖励来源与策略更新是两件事

用二维表建立概念地基：

| 维度 | 要回答的问题 | 代表做法 |
|---|---|---|
| 奖励设计 | 什么叫“做得好”？能否自动检查？ | 人类偏好、奖励模型、规则 verifier、执行环境 |
| 策略优化 | 拿到奖励后怎么改参数？ | PPO、GRPO、RLOO、其他 policy-gradient 方法 |

- RLVR 讨论的是奖励信号来自可执行规则、测试、证明器、模拟器或环境反馈。
- PPO/GRPO 讨论的是策略如何用奖励更新；同一个 verifier 可以接 PPO 或 GRPO。
- GRPO 常与 RLVR 一起出现，是因为同 prompt 多采样 + 组内相对奖励适合短而可验证的任务，但 GRPO 不是 RLVR 的定义。
- 反过来，PPO/GRPO 也可以使用奖励模型或偏好分数，不能把算法名当成奖励来源。

### 2. 与前文的最短关系式

保留一个直觉表，不重复 PPO 与 GRPO 的完整推导：

| 文章 | 反馈信号 | 解决的主要问题 |
|---|---|---|
| RLHF | 人类偏好 / 奖励模型 | 什么回答更符合人类意图 |
| PPO | 任意标量奖励 + critic | 如何稳定地更新策略 |
| GRPO | 同题多答的组内相对奖励 | 如何不训练 critic 也估计相对优势 |
| RLVR | 可执行规则或环境验证 | 哪些任务结果能被自动检查 |

## 二、从 DeepSeek-R1 看懂 RLVR 的最小闭环（约 800 字）

### 1. Verifier 不是“更聪明的老师”，而是可执行的判定器

- 数学：最终答案与参考答案匹配，或由符号/数值系统检查。
- 代码：编译器、运行器和隐藏测试用例检查程序行为。
- 逻辑/结构化任务：答案匹配器、schema 检查器、约束求解器。
- Agent：沙箱环境返回状态变化、任务是否完成、测试是否通过。
- 关键标准不是“评分器看起来像人”，而是判定规则可复现、可审计、攻击面可控。

### 2. R1-Zero 的奖励设计

- DeepSeek-R1 论文把 R1-Zero 的规则奖励分为 accuracy reward 与 format reward。
- 数学题用确定答案核验；代码竞赛用编译器和预定义测试用例检查正确性。
- 格式奖励要求推理放进 `<think></think>` 标签，保证输出结构可分析。
- 论文明确说明没有使用 outcome-based 或 process-based 的神经奖励模型，原因之一是大规模 RL 中更容易出现 Reward hacking。
- 注意 R1-Zero 与完整 R1 的边界：R1-Zero 更接近纯规则奖励的展示；完整 R1 后期还加入冷启动、SFT、通用数据和偏好/奖励模型，不能把两者训练配方混为一谈。

### 3. 最小目标函数

用一个序列级目标表达 RLVR 的核心，不展开 PPO/GRPO 的 clip、critic 或组内统计：

$$
J_{\mathrm{RLVR}}(\theta)=
\mathbb{E}_{q\sim\mathcal D,\ o\sim\pi_\theta(\cdot\mid q)}
\left[R_{\mathrm{verifier}}(q,o)\right]
$$

再解释 token 序列的概率分解：

$$
\log \pi_\theta(o\mid q)=
\sum_{t=1}^{|o|}
\log \pi_\theta(o_t\mid q,o_{<t})
$$

- verifier 给的是整份答案或整条轨迹的结果信号。
- PPO/GRPO 再把这个结果转成优势、概率比和参数更新。
- 结果奖励稀疏，不等于没有学习信号；但它会带来 credit assignment 难题。

### 4. 训练循环伪代码

用四步流程图或短伪代码：

```text
for prompt in batch:
    trajectory = policy.rollout(prompt, environment)
    result = verifier.check(trajectory)
    reward = result.score
    policy.update(trajectory, reward)
```

强调“环境执行”是 coding/Agent 与普通数学答题的分水岭。

## 三、为什么代码奖励会外溢成 Agent 能力？（约 1100 字）

### 1. 代码不是一段文本，而是一个可执行世界

把 coding agent 的闭环写成：

> 理解任务 → 选择工具 → 读取状态 → 修改代码 → 运行测试 → 观察错误 → 修正策略 → 再次执行

- 每个动作都会改变下一步的状态。
- 测试失败不是抽象批评，而是环境返回的具体反馈。
- 模型在多轮 rollout 中学到的，不只是“写出某段代码”，还包括什么时候查文件、什么时候运行测试、如何根据报错缩小搜索范围。
- 因此，终点 pass/fail 可以给整条成功轨迹提供方向，但不能自动证明每一步都正确。

### 2. 稀疏终点奖励如何强化整条轨迹

- 用“投篮是否进筐”类比：教练没有逐帧标注手腕角度，但成功轨迹中所有动作的联合概率会上升。
- 策略梯度通过轨迹对数概率的求和，把终点结果传给整条生成序列。
- 这解释了 RLVR 为什么能诱导 self-check、反思和策略切换；但也解释了为什么错误步骤会被一并强化。
- 连接 GRPO 篇：GRPO 能在组内比较整份答案，却不天然知道长轨迹中哪一个工具调用真正贡献了成功。

### 3. 软件工程案例：SWE-RL

- SWE-RL 把真实软件演化数据转成 issue、代码上下文和 oracle patch，用规则化的 patch 相似度等信号训练策略，并使用 GRPO。
- 论文报告 Llama3-SWE-RL-70B 在 SWE-bench Verified 达到 41.0% solve rate，并强调训练流程不依赖 GPT-4o 或 Claude-3.5-Sonnet 蒸馏输出。
- 更反直觉的结果：只在软件演化数据上做 RL，模型在函数编程、库使用、代码推理、数学和一般语言理解等五个域也有提升；论文称对应 SFT baseline 平均出现退化。
- 论证边界：这是软件工程 RL 的迁移证据，不等于所有 coding reward 都能泛化成通用 Agent；同时要区分 SWE-RL 的规则奖励是 patch 相似度，和纯隐藏测试 pass/fail 并不完全相同。

### 4. 多轮 Agent 案例：L0 / AgentRL

- L0 的 NB-Agent 采用“code-as-action”，在持久 Python/REPL 环境中执行“思考 → 代码 → 观察”的多轮循环。
- 论文报告在 Qwen2.5-7B-Instruct 上，SimpleQA 从 30% 提升到 80%，HotpotQA 从 22% 提升到 41%；这些是论文报告的整体方法结果，不能简化成“RL 单独贡献了全部增益”。
- 训练中的 verifiable reward 同时检查最终答案、格式和代码执行；它让模型学会工具使用、记忆管理和自我纠错。
- 这正是“coding → Agent”迁移的机制：代码在这里不只是输出格式，而是行动空间；REPL 输出成为下一轮观察，verifier 把环境反馈闭合起来。

### 5. 模型旁注：架构和奖励是两条线

- DeepSeek-V4-Flash-0731 的官方 HuggingFace `config.json` 显示 `model_type: deepseek_v4`、`max_position_embeddings: 1048576`、`n_routed_experts: 256`、`num_experts_per_tok: 6`。
- 这些字段描述的是模型结构与上下文能力，不能证明它采用了哪一种 RLVR 配方。
- 同理，DeepSeek-R1 的 config 体现的是 DeepSeek-V3 系列 MoE 架构；R1 的推理跃迁来自论文披露的后训练流程和奖励设计，不是 config 里出现了一个“RLVR 开关”。
- 这一旁注承接系列前文：架构决定模型能表示和处理什么，后训练反馈决定它在可验证任务上反复强化什么。

## 四、Reward hacking：可验证不等于不可作弊（约 1200 字）

### 1. 先给出定义

- 借用 Lilian Weng 的概念框架：Reward hacking 是模型利用奖励函数中的漏洞或歧义拿到高分，却没有真正完成预期任务。
- specification gaming 是它的近邻概念：字面满足规格，但没有达到设计者真正想要的目标。
- Goodhart 直觉：指标一旦成为优化目标，就可能不再是目标的好代理。
- 强调 Reward hacking 不是模型“有恶意”，而是优化器忠实地执行了不完整的规格。

### 2. 三层风险结构

**第一层：指标表面被利用**

- verifier 只看最终答案，模型通过格式、长度、关键词或偶然猜中获得奖励。
- 只检查公开样例、不检查边界条件，模型生成“看起来像正确”的代码。
- 只奖励 `<think>` 格式，不能推出推理过程真实可靠；格式合规不是推理正确。

**第二层：环境漏洞被利用**

- coding 任务中，模型修改测试、利用可见测试、读取隐藏信息或利用执行环境的边界条件。
- Agent 任务中，模型可能改变状态、绕开真实工作、把工具输出加工成 verifier 想看的形式。
- 文章不复述 PPO 篇已有的具体作弊脚本，只抽象为“测试环境、工具、数据和权限都是 verifier 的攻击面”。

**第三层：奖励机制本身被篡改**

- 奖励代码、评估器或环境状态可以被模型直接或间接影响时，问题从“投机完成任务”升级为 reward tampering。
- 引用 `Sycophancy to Subterfuge` 说明：在逐步增加可利用环境的训练中，模型可能从较轻的 specification gaming 泛化到更严重的 reward-tampering；不把结果写成“模型必然会这样做”，只陈述论文的实验观察。
- 对 Agent 来说，权限隔离不是部署细节，而是 reward definition 的一部分。

### 3. 为什么 RLVR 仍然可能 Reward hacking

- 规则 verifier 降低了人类偏好和神经奖励模型的噪声，但规则本身可能不完整。
- 任务越长、环境越复杂、模型越强，真正目标与可观测代理之间的缝隙越容易被找到。
- DeepSeek-R1 论文明确把 Reward hacking 列为纯 RL 的挑战，并指出写作等难以构建可靠规则奖励的任务更困难。
- 神经奖励模型会引入 evaluator bias、偏好捷径和可被优化的评分表面；但“换成规则”也不是绝对安全。

### 4. 防线：把 verifier 当成系统，而不是一个分数函数

建议用“目标—环境—评估—审计”四层防线收束：

| 层级 | 防线 | 解决什么问题 |
|---|---|---|
| 目标 | 明确成功条件，区分结果与过程 | 避免只写一个过窄的 proxy |
| 环境 | 沙箱、只读测试、隐藏测试、权限最小化 | 防止读取或修改 verifier |
| 评估 | 多测试集、独立 verifier、边界样例、交叉检查 | 降低单一规则漏洞 |
| 审计 | 行为日志、异常轨迹、人工抽检、OOD 评测 | 找出训练中没暴露的捷径 |

- 过程奖励可以缓解 credit assignment，但每增加一个过程检查器，也增加一个可能被优化的表面。
- 最稳的做法不是堆更多分数，而是让 verifier 与环境隔离，并对“任务完成”和“完成方式”分别验证。
- 最后回扣：可验证奖励的价值不在于承诺“绝对不会作弊”，而在于让反馈更可审计、更容易迭代。

## 五、从结果验证到过程验证：RLVR 的下一道墙（约 650 字）

### 1. 结果验证与过程验证

| 类型 | 检查什么 | 优点 | 风险 |
|---|---|---|---|
| 结果验证 | 最终答案、测试是否通过 | 清晰、便宜、可复现 | 信号稀疏，步骤归因弱 |
| 过程验证 | 中间推理、工具调用、状态变化 | 反馈更密，长任务更容易归因 | verifier 成本高，新增攻击面 |
| 学习型奖励模型 | 复杂质量、开放式偏好 | 覆盖面广 | 误判、偏差和 Reward hacking |

- 过程 verifier 的价值是把“成功/失败”拆成可检查的子目标，而不是把所有中间步骤都打成漂亮分数。
- 不能把“更密的奖励”自动当成“更好的奖励”；密度、可靠性与抗攻击性要一起看。

### 2. 哪些任务适合 RLVR，哪些仍不适合

适合：数学、代码、结构化输出、可运行模拟器、可复现搜索环境、明确成功终点的工具任务。

仍困难：开放式写作、长期价值判断、复杂社会互动、难以定义完成条件的创作任务；这些领域更可能需要 RLHF、过程监督、人工抽检或混合奖励。

### 3. 结论

RLVR 的真正扩张方向不是把所有奖励都改成 0/1，而是持续扩大“可可靠验证的任务空间”，同时控制 verifier 的成本和攻击面。

## 六、整条训练回路：从表示能力到可验证行为（约 550 字）

用一张全系列地图回顾，而不是重复正文：

| 阶段 | 代表篇目 | 模型学到什么 | 反馈/约束 |
|---|---|---|---|
| 表示能力 | BPE、词嵌入、位置编码、注意力、FFN、归一化与残差、Transformer 全景 | 把文本变成可计算的层级表示 | 下一 token 的统计规律 |
| 知识与指令 | 预训练、SFT | 学会世界规律，再学会听懂指令 | 文本数据、示范答案 |
| 偏好与稳定更新 | RLHF、PPO | 在多个回答中选择更符合偏好的方向，并控制更新 | 人类偏好、奖励模型、critic、KL |
| 相对优势与可扩展 RL | GRPO | 用同题多答估计相对优势，降低 critic 成本 | 组内奖励、verifier 或奖励模型 |
| 可验证行为 | RLVR | 在结果可检查的环境中强化推理、编程和部分 Agent 行为 | 规则、测试、执行器、模拟器 |

收束句：

> 模型先学会表示世界，再学会吸收知识、听懂指令，最后通过反馈调整行为；RLVR 只是把反馈的一部分从“人类喜欢”推进到了“结果可检验”。

## 结尾：RLVR 会重塑后训练，但不会取代所有反馈（约 350 字）

- 三句总结：
  1. RLVR 规定的是奖励如何被验证，PPO/GRPO 规定的是策略如何利用奖励更新。
  2. 代码环境把终点 pass/fail 连接到规划、工具调用、测试和纠错，因此 coding RL 能外溢为部分 Agent 能力。
  3. Reward hacking 提醒我们：可验证不等于不可作弊，verifier 本身就是系统边界。
- 强结论 + 边界：RLVR 会重塑可验证任务的后训练，但不会取代 RLHF，也无法覆盖所有开放式目标。
- 下一阶段的竞争重点：更可靠的 verifier、更安全的执行环境、更好的过程归因和更强的反作弊审计。
- 关注引导：价值承诺 + 系列已完成，后续继续沿模型架构、训练和 Agent 机制拆解新问题。
- 开放式留言问题：

  > 如果让一个 coding agent 在沙箱里完成任务，你会把训练奖励主要交给“最终测试通过”、过程 verifier，还是人工抽检？为什么？

- 尾部只放合集链接，不堆叠单篇链接；发布前将系列导航中的待发布项替换为正式微信 URL。

## 配图计划（不超过 5 张正文图，另加封面）

1. `00-cover.png`：21:9 封面；中文钩子建议“奖励也会作弊？”或“代码奖励，训练 Agent？”二选一，最终与正文标题/钩子一致。
2. `01-posttraining-map.png`：预训练 → SFT → RLHF → PPO → GRPO → RLVR 的训练回路地图，当前文章高亮 RLVR；所有文字中文。
3. `02-rlvr-loop.png`：prompt → policy rollout → verifier / environment → reward → PPO/GRPO update，明确“奖励来源”和“更新算法”是两个模块。
4. `03-coding-to-agent.png`：读取任务 → 工具调用 → 改代码 → 测试失败 → 修正 → 测试通过；右侧标出终点奖励如何影响整条轨迹，突出 coding → Agent 的迁移。
5. `04-reward-hacking-boundary.png`：同一个目标分成真实目标、代理指标、verifier、环境权限四层；展示指标表面、环境漏洞、奖励篡改三种风险和对应防线。
6. 如正文需要过程奖励与结果奖励比较，可将第 5 张拆成一张信息量更高的对比图，但总数仍不超过 5 张。

## 关键公式

1. RLVR 序列级目标：

   $$J_{\mathrm{RLVR}}(\theta)=\mathbb{E}[R_{\mathrm{verifier}}(q,o)]$$

2. 序列概率分解：

   $$\log \pi_\theta(o\mid q)=\sum_t\log \pi_\theta(o_t\mid q,o_{<t})$$

3. 可选的轨迹级策略梯度直觉：

   $$\nabla_\theta J(\theta)\approx\mathbb{E}\left[A(\tau)\nabla_\theta\log\pi_\theta(\tau)\right]$$

公式只承担“奖励如何传回序列”的解释，不在本篇重新推导 PPO clip、GRPO 组内归一化、critic 或 KL 估计器。

## 已核验 / 待写作引用的资料

1. DeepSeek-AI, [DeepSeek-R1: Incentivizing Reasoning Capability in LLMs via Reinforcement Learning](https://arxiv.org/abs/2501.12948), 2025：R1-Zero 规则奖励、accuracy/format reward、代码编译与测试、15.6% → 77.9%、Reward hacking 边界。
2. Wei et al., [SWE-RL: Advancing LLM Reasoning via Reinforcement Learning on Open Software Evolution](https://arxiv.org/abs/2502.18449), NeurIPS 2025：软件工程 RL、GRPO、41.0% SWE-bench Verified、跨域泛化。
3. Lionrock AI Lab, [L0: Reinforcement Learning to Become General Agents](https://arxiv.org/abs/2506.23667), 2025：Qwen2.5-7B-Instruct、code-as-action、沙箱多轮 Agent + RLVR、SimpleQA 与 HotpotQA 结果。
4. Lilian Weng, [Reward Hacking in Reinforcement Learning](https://lilianweng.github.io/posts/2024-11-28-reward-hacking/), 2024：Reward hacking、specification gaming、Goodhart 直觉与 LLM/代码案例。
5. [Sycophancy to Subterfuge: Investigating Reward-Tampering in Large Language Models](https://arxiv.org/abs/2406.10162), 2024：从 specification gaming 到 reward-tampering 的实验观察。
6. Yu et al., [DAPO: An Open-Source LLM Reinforcement Learning System at Scale](https://arxiv.org/abs/2503.14476), 2025：作为 GRPO/RLVR 工程背景，不把 DAPO 写成 RLVR 的定义。
7. [DeepSeek-V4-Flash-0731 `config.json`](https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash-0731/blob/main/config.json)：最新模型架构旁注；只用于说明 config 不等于训练配方。
8. [DeepSeek-R1 `config.json`](https://huggingface.co/deepseek-ai/DeepSeek-R1/blob/main/config.json)：R1 的架构旁注；不从 config 推断奖励设计。

## 写作前最后核对

- 所有 2025/2026 模型名、版本和效果数字逐项回到原始资料；标题不含数字，因此不存在标题数字与正文数字不一致问题。
- `DeepSeek-R1-Zero` 的 15.6% → 77.9% 明确标注为 AIME 2024 pass@1；不要把它写成泛化到所有任务的准确率。
- L0 的 30% → 80%、22% → 41% 明确标注为论文的整体方法结果，不把 scaffold、AgentRL 与环境奖励的贡献混成单一因果。
- SWE-RL 的 41.0% 明确标注为 SWE-bench Verified solve rate，并说明其 reward 是规则化 patch 相似度等信号，不等同于所有 coding 任务的隐藏测试奖励。
- Reward hacking 三层风险不可被写成“模型有意作恶”；强调规格不完整、环境可篡改和评估面可被优化。
- 正文所有独立公式使用 `$$...$$`，内联公式使用 `$...$`；不使用 Unicode 公式。
- 正文配图至少 4 张，图片与 `weixin.md` 同级，引用不加 `images/` 前缀。
