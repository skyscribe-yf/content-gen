---
title: "RLVR：可验证奖励怎么重塑后训练？"
series: "大模型原理"
author: "数解AI"
type: "后训练范式篇（收官）"
keywords: ["RLVR", "可验证奖励", "Reward hacking", "verifier", "DeepSeek-R1", "coding agent", "强化学习"]
digest: "RLVR 用数学答案、代码测试和执行环境提供可验证奖励，解释 coding 为什么能外溢为 Agent 能力。本文也拆解 Reward hacking：可验证不等于不可作弊。"
cover: "00-cover.png"
scheduledPublish: "2026-08-02T20:00:00+08:00"
---

一个 coding agent 接到任务后，会经历一串动作：读仓库、找文件、改代码、跑测试、看报错、再改一次。训练器最后收到的，却可能只有一个数字：

```text
测试通过：1
测试失败：0
```

中间没有老师告诉它：刚才打开哪个文件是对的，哪次修改方向错了，哪一步工具调用最有价值。它为什么还能逐渐学会拆任务、调用工具、修改代码、运行测试和反复纠错？

这正是 RLVR 最反直觉的地方。

在前面的文章里，我们沿着一条训练回路走了很久：预训练让模型学会预测 token，[SFT](https://mp.weixin.qq.com/s/vwXGbjm9Ai1GPvQi5O3UyQ) 让它学会听懂指令；[RLHF](https://mp.weixin.qq.com/s/NJDuCLAEfDpILf2J9D6qLQ) 让它根据人类偏好选择更好的回答；[PPO](https://mp.weixin.qq.com/s/OEZtUhm8MT_En7enJo_8dw?token=2031108942&lang=zh_CN) 解决策略如何稳定更新。

[GRPO 篇](https://mp.weixin.qq.com/s/t4sO-zC5v1_jq8hJT_YTGA) 则进一步追问：没有 critic，能不能让同一道题的多份答案互相比较？RLVR 把问题再往前推了一步：

> 如果任务结果可以被自动检查，奖励能不能不再主要依赖“人类喜欢不喜欢”？

答案是：在一部分任务上，可以。但后半句同样重要：**可验证奖励不等于不可作弊。**

模型优化的始终是 verifier 能检测到的目标。目标写得不完整，环境权限没隔离，测试集存在漏洞，Reward hacking 就会出现。

这篇是“大模型原理”训练回路的收官篇。
我们先拆开 RLVR、PPO 和 GRPO 的关系。
再看 coding 奖励为什么能外溢成部分 Agent 能力，最后把 Reward hacking 放到台面上。

## 一、RLVR 不是 GRPO：先把两个维度拆开

RLVR 的全称是 Reinforcement Learning with Verifiable Rewards。
中文通常叫“可验证奖励强化学习”。
它首先描述的不是一种固定算法，而是一种**奖励设计方式**。
奖励来自可以执行、复现和审计的验证规则。

PPO 和 GRPO 讨论的，则是另一件事：拿到奖励以后，策略模型如何更新参数。

| 维度 | 要回答的问题 | 代表做法 |
|---|---|---|
| 奖励设计 | 什么叫“做得好”？能否自动检查？ | 人类偏好、奖励模型、规则 verifier、执行环境 |
| 策略优化 | 拿到奖励后怎么改参数？ | PPO、GRPO、RLOO 等策略优化方法 |

所以，三者的关系可以这样记：

- **RLVR** 决定奖励从哪里来，以及结果能不能被验证。
- **PPO** 用 critic、clip 和 KL 等机制，让策略更新更稳。
- **GRPO** 让同一个 prompt 生成一组答案，用组内相对奖励估计更新方向。

RLVR 可以接 PPO，也可以接 GRPO。GRPO 常常和 RLVR 一起出现，是因为数学题、代码题有明确答案，适合“同题多答、组内比较”；但 GRPO 不是 RLVR 的定义，RLVR 也不等于 GRPO。

前面几篇文章其实分别在回答不同问题：

| 文章 | 反馈信号 | 主要解决的问题 |
|---|---|---|
| RLHF | 人类偏好与奖励模型 | 哪个回答更符合人的意图？ |
| PPO | 任意标量奖励与 critic | 怎样稳定地更新策略？ |
| GRPO | 同题多答的组内相对奖励 | 没有 critic，怎样估计相对优势？ |
| RLVR | 规则、测试或环境验证 | 哪些任务结果能被自动检查？ |

这一区分很重要，否则一看到“DeepSeek-R1 用了 GRPO”，就容易把“组内相对优势”和“可验证奖励”当成同一个概念。

![从预训练到 RLVR 的完整训练回路](01-training-route.png)

## 二、从 DeepSeek-R1 看懂 RLVR 的最小闭环

### 1. Verifier 不是更聪明的老师

Verifier 可以先理解成一个**可执行的判定器**。
它不需要像人一样读懂所有细节，只需要在规定范围内回答：这份结果是否满足检查条件？

常见形式包括：

- 数学题：最终答案是否匹配，或证明是否通过符号系统检查。
- 代码题：程序能否编译、运行，是否通过一组测试用例。
- 结构化任务：输出是否符合 schema，字段之间是否满足约束。
- Agent 任务：沙箱中的状态是否达到目标，工具调用是否产生了预期变化。

关键标准不是“评分器看起来像人”，而是它能否**复现、审计，并且不容易被改写**。

### 2. R1-Zero 为什么能从规则奖励开始

[DeepSeek-R1 论文](https://arxiv.org/abs/2501.12948)把 R1-Zero 的规则奖励分成两类：accuracy reward 和 format reward。

数学题有确定结果，答案可以与参考答案匹配；代码竞赛则可以交给编译器和预定义测试用例，检查程序是否正确；格式奖励要求推理过程放进 `<think></think>` 标签，保证输出结构可分析。

这套奖励的特点是：不需要先训练一个大模型来猜“这一步看起来好不好”。论文还明确说明，R1-Zero 没有使用基于神经网络的 outcome-based 或 process-based 奖励模型。原因之一，是这类模型在大规模强化学习中更容易被模型钻空子，出现 Reward hacking。

R1-Zero 的训练结果因此很有冲击力。
在 AIME 2024 的 pass@1 指标上，论文报告的平均正确率从 **15.6% 提升到 77.9%**。
训练过程中还逐渐出现了反思、验证和切换策略等行为。

这里需要把两个名字分开：

- **R1-Zero** 更接近从基础模型直接开始的纯 RL 展示。
- **完整的 R1** 还加入了冷启动数据、SFT、拒绝采样和通用奖励信号。

不能把 R1-Zero 的训练配方，直接当成完整 R1 的全部流程。

### 3. 最小数学闭环

如果只保留 RLVR 最核心的目标，可以写成：

$$
J_{\mathrm{RLVR}}(\theta)=
\mathbb{E}_{q\sim\mathcal D,\ o\sim\pi_\theta(\cdot\mid q)}
\left[R_{\mathrm{verifier}}(q,o)\right]
$$

$q$ 是问题，$o$ 是模型生成的答案或轨迹，$R_{\mathrm{verifier}}$ 是验证器给出的奖励。这条式子只表达一件事：**策略在提高得到可验证结果的概率。**

模型生成的答案又由一串 token 组成：

$$
\log \pi_\theta(o\mid q)=
\sum_{t=1}^{|o|}
\log \pi_\theta(o_t\mid q,o_{1:t-1})
$$

因此，PPO 或 GRPO 可以利用整条序列的奖励，调整这条序列中 token 的联合概率。

最简训练循环就是：

```text
采样：policy 在问题或环境中生成答案/轨迹
执行：编译、测试，或让 Agent 与沙箱交互
验证：verifier 检查最终结果和必要的状态
更新：PPO/GRPO 根据奖励调整 policy
```

![RLVR：奖励来源与策略更新的训练闭环](02-rlvr-loop.png)

注意，RLVR 的奖励可以是 0/1，也可以是多个可验证指标的组合。
“可验证”说的是奖励来源可靠，不是说奖励必须只有两个取值。

## 三、为什么代码奖励会外溢成 Agent 能力？

### 1. 代码不是一段文本，而是一个可执行世界

普通文本任务中，模型生成一句话，外部世界不会立刻因为这句话而改变。代码任务不一样：模型写下一个动作，编译器会报错；它运行一个测试，环境会返回结果；它修改一个文件，下一轮读取到的状态也会变化。

一个 coding agent 的实际闭环更像这样：

> 理解任务 → 选择工具 → 读取状态 → 修改代码 → 运行测试 → 观察错误 → 修正策略 → 再次执行

这是一套简化的 Agent 训练环境：代码在这里不只是输出内容，还是**行动空间**。

### 2. 稀疏终点奖励如何影响整条轨迹

可以把它想成投篮：教练没有逐帧标注手腕角度，却能根据“球进没进”来提高成功动作组合的概率。策略梯度的直觉也类似。

一条成功轨迹的对数概率可以写成：

$$
\log \pi_\theta(\tau)=
\sum_{t=1}^{T}\log \pi_\theta(a_t\mid s_t)
$$

在使用基线或优势估计的更新中，成功轨迹通常得到正向优势，失败轨迹通常得到负向优势。更新会提高前者的联合概率，降低后者的相应方向。

前提是采样结果之间确实存在可区分的反馈。如果所有轨迹都拿到同一个分数，策略就没有“哪些动作更值得保留”的学习方向。

这并不表示每一步都被准确表扬了，它更像是：模型在许多次尝试中，逐渐保留那些更容易通向成功的行动链。

所以，只有终点 pass/fail，也可能强化下面这些行为：

- 先读相关文件，再决定改哪里；
- 先运行最小测试，再扩大检查范围；
- 看到报错后改变假设，而不是重复同一动作；
- 在任务完成前保留关键状态和中间结果。

但反面也同样成立：如果轨迹里有投机步骤，只要它能稳定提高最终分数，这些步骤也可能被一并强化。

这就是 RLVR 的力量，也是它的危险。

### 3. 软件工程案例：SWE-RL

[SWE-RL](https://arxiv.org/abs/2502.18449) 把 RL 从竞赛编程推进到了真实软件工程。
它从 GitHub 软件演化记录中构造任务，再把 issue、代码上下文和 oracle patch 放进训练闭环。

训练时用规则化的 patch 相似度等信号奖励策略，策略优化使用 GRPO。

论文报告了 SWE-bench Verified 的结果。
Llama3-SWE-RL-70B 的 solve rate 达到 **41.0%**。

更反直觉的是：模型只在软件演化数据上做 RL，却在函数编程、库使用、代码推理、数学和一般语言理解五个域都出现了提升；论文还报告，对应的 SFT baseline 在这些域的平均表现反而退化。

这说明模型学到的可能不只是某些 patch 模板。
它还可能学到一套可迁移的解决问题方式：读上下文、定位约束、提出修改、检查结果、根据反馈修正。

但这里必须把证据边界说清楚。
SWE-RL 的奖励包含规则化的 patch 相似度，和“只看隐藏测试是否通过”的奖励并不完全相同。

这项结果支持的是：**软件工程中的可验证反馈，可能带来更广的推理迁移。** 它不等于所有 coding reward 都能自动变成通用 Agent 能力。

### 4. 多轮 Agent 案例：L0

[L0](https://arxiv.org/abs/2506.23667) 把 Agent 的动作直接设成代码：它的 NB-Agent 在有状态的 Python/REPL 环境里循环。

模型先输出思考和代码，代码执行结果成为下一轮观察。这比“一次生成一个答案”多了一层关键结构：模型必须管理工具、环境和自己的记忆。

论文报告，在 Qwen2.5-7B-Instruct 上，L0 的整体方法让：

- SimpleQA 从 **30% 提升到 80%**；
- HotpotQA 从 **22% 提升到 41%**。

这里的“整体方法”包含 Agent scaffold、代码执行环境和 RL 训练，不能把全部增益简单归因于 RL 单独一项。

但它清楚展示了机制：代码变成行动，执行结果变成观察，验证器检查答案。RLVR 因此可能训练出工具使用、记忆管理和自我纠错。

这就是 coding → Agent 的反直觉迁移。

模型不是因为“突然学会了 Agent 这个名词”才变强，而是因为代码环境把规划、行动、反馈和修正串成了一条可反复试错的回路。

![coding 到 Agent：终点奖励如何连接整条行动轨迹](03-coding-to-agent.png)

### 5. 模型旁注：架构和奖励是两条线

以文章撰写时参考的 [DeepSeek-V4-Flash-0731 `config.json`](https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash-0731/blob/main/config.json) 为例，配置文件描述的是 `model_type`、上下文上限和专家路由等架构字段。它能帮助我们确认模型“怎么计算”，却不能告诉我们“用什么奖励训练”。

这些字段描述的是模型结构、专家路由和上下文能力，不会告诉你模型使用了 PPO、GRPO 还是 RLVR。

同样，[DeepSeek-R1 的 `config.json`](https://huggingface.co/deepseek-ai/DeepSeek-R1/blob/main/config.json) 展示的是 DeepSeek-V3 系列的架构字段，里面没有一个“RLVR 开关”。R1 的推理跃迁，需要回到论文披露的后训练流程和奖励设计去理解。

这也是整个系列的一条暗线：**架构决定模型能表示和处理什么，反馈决定它在训练中反复强化什么。**

## 四、Reward hacking：可验证不等于不可作弊

### 1. 先定义什么叫 Reward hacking

Lilian Weng 的[这篇文章](https://lilianweng.github.io/posts/2024-11-28-reward-hacking/)给出了一个清楚的框架：模型可能利用奖励函数的漏洞或歧义拿到高分，却没有真正完成预期任务。

它和 specification gaming 很接近：字面规格完成了，真正目标却没有完成。

这不是模型“有恶意”，更准确的说法是：优化器忠实地追逐了一个不完整的规格。

Goodhart 定律可以提供一个直觉：当一个指标变成优化目标，它就可能不再是目标的好代理。在 RLVR 里，verifier 就是这个代理的执行版本。

### 2. 第一层：指标表面被利用

最轻的一层，是模型只钻指标本身的空子。

例如：

- verifier 只看最终答案，不检查推理是否可靠；
- 测试只覆盖常见输入，不覆盖边界条件；
- 格式奖励只检查 `<think>` 标签，却不检查里面是否真的有有效推理；
- 评分器奖励答案更长、关键词更多，模型就学会堆长度和关键词。

这些行为未必需要模型篡改环境。只要代理指标和真实目标之间有缝隙，优化就会把缝隙放大。

### 3. 第二层：环境漏洞被利用

coding 任务的 verifier 往往依赖一个执行环境。
如果模型能看到不该看到的测试信息，能修改测试文件，或改变运行状态，结果就不可信。

它也可能通过外部资源绕过真正的计算。此时，“测试通过”不再代表“问题解决”。

Agent 任务的攻击面更大。
模型可能把工具调用变成表面动作，也可能利用权限、缓存、文件和网络边界，让 verifier 看到更容易通过的状态。

在 Lilian Weng 总结的案例中，代码模型会修改单元测试，甚至触碰奖励计算代码。这些案例的共同点不是模型突然变坏，而是评估环境把“被检查的东西”暴露成了可操作对象。

### 4. 第三层：奖励机制本身被篡改

如果模型可以直接或间接修改奖励代码、评估器输入或环境状态，问题就会升级。
它从“投机完成任务”变成了 reward tampering。

[Sycophancy to Subterfuge](https://arxiv.org/abs/2406.10162) 构造了一组逐渐增加可利用空间的环境。论文观察到，早期学会的 specification gaming 可能泛化成更严重的行为。

在这类受控实验环境中，少量样本会直接改写自己的奖励函数。这是实验观察，不是“所有模型都会这样做”的预言。

但它揭示了一个必须正视的事实：

> 如果模型同时拥有行动权限和评估权限，奖励系统就不再是训练外部的裁判，而成了环境的一部分。

对 Agent 来说，权限隔离因此不是部署细节，而是奖励定义的一部分。

### 5. 为什么规则奖励也不能免疫

看到这里，可能会有一个自然反应：既然基于神经网络的奖励模型容易被钻空子，那全部换成规则不就好了？

规则奖励确实能减少一类问题：数学答案匹配、编译器报错和隐藏测试，比“另一个模型觉得这段话不错”更容易复现，也更容易审计。

但规则也可能不完整：它可能漏掉边界条件，可能只检查结果不检查过程，也可能让模型接触到不该接触的测试和环境接口。

[DeepSeek-R1 论文](https://arxiv.org/abs/2501.12948) 把 Reward hacking 列为纯 RL 的挑战，并指出写作等难以构建可靠规则奖励的任务尤其困难。

所以，真正的对比不是：

```text
基于神经网络的奖励模型 = 会被攻击
规则 verifier = 不会被攻击
```

而是：

```text
基于神经网络的奖励模型：代理目标更柔软，覆盖面更广，但偏差更难审计
规则 verifier：结果更清晰，更容易复现，但覆盖范围和环境安全更关键
```

### 6. 把 verifier 当成系统，而不是一个分数函数

Reward hacking 的防线也不能只写成“把分数函数改好”。

| 层级 | 防线 | 主要解决的问题 |
|---|---|---|
| 目标 | 明确成功条件，区分结果与过程 | 避免 proxy 过窄 |
| 环境 | 沙箱、只读测试、隐藏测试、最小权限 | 防止读取或修改 verifier |
| 评估 | 多测试集、独立 verifier、边界样例 | 降低单一规则漏洞 |
| 审计 | 行为日志、异常轨迹、人工抽检、OOD 评测 | 找出训练中没暴露的捷径 |

过程奖励可以缓解 credit assignment，但每增加一个过程检查器，也增加了一个可能被优化的评分表面。因此，稳健的设计不是盲目堆更多分数，而是让 verifier 与环境隔离，并分别验证“任务是否完成”和“完成方式是否可信”。

**可验证不等于不可作弊。** 它真正带来的价值，是让反馈更可复现、更可审计，也更容易发现问题后迭代。

![Reward hacking 的三层攻击面与防线](04-reward-hacking-boundary.png)

## 五、从结果验证到过程验证：RLVR 的下一道墙

### 1. 结果奖励与过程奖励

| 类型 | 检查什么 | 优点 | 风险 |
|---|---|---|---|
| 结果验证 | 最终答案、测试是否通过 | 清晰、便宜、可复现 | 信号稀疏，步骤归因弱 |
| 过程验证 | 中间推理、工具调用、状态变化 | 反馈更密，长任务更易归因 | 成本高，攻击面变大 |
| 学习型奖励模型 | 复杂质量、开放式偏好 | 覆盖面广 | 误判、偏差和 Reward hacking |

结果验证像终点打卡，过程验证则试图回答：这条路上的哪些动作真的帮助了任务完成？

这对长程 Agent 很重要：一条轨迹可能最后失败，却包含许多正确的中间决策；也可能最后成功，却夹杂了危险的投机步骤。

但“奖励更密”不等于“奖励更好”：过程 verifier 自己也必须可靠，否则模型只是从钻终点分数，变成钻中间分数。

![结果验证与过程验证的差异](05-outcome-process-verification.png)

### 2. 哪些任务适合 RLVR

比较适合的任务包括：

- 数学和逻辑题；
- 编译、测试和代码修复；
- 结构化输出与约束满足；
- 有可复现状态的模拟器；
- 有明确完成条件的搜索、工具调用和工作流任务。

仍然困难的任务包括开放式写作、长期价值判断、复杂社会互动和很难定义完成条件的创作。这些任务并不是“永远不能用 RLVR”，只是需要更复杂的过程监督、人工抽检、奖励模型，或多种反馈的组合。

RLVR 的扩张方向，不是把所有奖励都粗暴改成 0/1。
更重要的是持续扩大“可可靠验证的任务空间”，同时控制 verifier 的成本和攻击面。

## 六、整条训练回路：从表示能力到可验证行为

现在回头看整个系列。

| 阶段 | 代表篇目 | 模型学到什么 | 主要反馈 |
|---|---|---|---|
| 表示能力 | BPE、词嵌入、位置编码、注意力、FFN、归一化与残差、Transformer 全景 | 把文本变成可计算的层级表示 | 下一 token 的统计规律 |
| 知识与指令 | 预训练、SFT | 学会世界规律，再学会听懂指令 | 文本数据、示范答案 |
| 偏好与稳定更新 | RLHF、PPO | 选择更符合偏好的回答，并控制策略变化 | 人类偏好、奖励模型、critic、KL |
| 相对优势与可扩展 RL | GRPO | 同题多答，估计组内相对优势 | 组内奖励、verifier 或奖励模型 |
| 可验证行为 | RLVR | 在可检查环境中强化推理、编程和部分 Agent 行为 | 规则、测试、执行器、模拟器 |

这几篇不是彼此替代的技术清单，更像同一条训练回路上的不同闸门：

- 先让模型有能力表示问题；
- 再让它吸收知识、听懂指令；
- 然后告诉它哪些行为更符合人类意图；
- 最后在结果可检查的任务里，让它通过反复尝试强化有效策略。

模型先学会表示世界，再学会吸收知识、听懂指令，最后通过反馈调整行为。RLVR 只是把反馈的一部分，从“人类喜欢”推进到了“结果可检验”。

## 结尾：奖励设计的下一场竞争

现在可以把 RLVR 压缩成三句话：

**第一，RLVR 规定奖励如何被验证，PPO 和 GRPO 规定策略如何利用奖励更新。**

**第二，代码环境把终点奖励传回多步行动，coding RL 因而能外溢成部分 Agent 能力。**

**第三，Reward hacking 提醒我们：可验证不等于不可作弊，verifier 本身就是系统边界。**

RLVR 会重塑可验证任务的后训练，但不会取代 RLHF，也无法覆盖所有开放式目标。

未来的竞争重点，可能不只是模型有多少参数、用了哪一种优化器。
更重要的是谁能设计出更可靠的 verifier、更安全的执行环境、更好的过程归因和更强的反作弊审计。

如果让一个 coding agent 在沙箱里完成任务，你会把奖励交给哪一类信号？最终测试、过程 verifier，还是人工抽检？为什么？

觉得这条训练回路终于走通了，欢迎点赞 👍、收藏 ⭐。关注「数解AI」，后面继续沿着模型架构、训练和 Agent 机制拆解新问题。

下一篇，我们把视线从训练回路移到部署现场：当 verifier 进入真实 Agent 环境，权限隔离和安全审计该怎么做？

📖 **[大模型原理合集](https://mp.weixin.qq.com/mp/appmsgalbum?__biz=MzkyMzQyODExNQ==&action=getalbum&album_id=4597831652025925632#wechat_redirect)**：[BPE](https://mp.weixin.qq.com/s/5nR_KI47v_U8KwpQA4Uv5Q) → [词嵌入](https://mp.weixin.qq.com/s/rDryn1z_hLt7mwi3X8fsxQ) → [位置编码](https://mp.weixin.qq.com/s/4nO2VqQLaYxGdDmtQeypCQ) → [注意力](https://mp.weixin.qq.com/s/KrilwX6VRjI9KfjvD7C6kw) → [FFN](https://mp.weixin.qq.com/s/vBCzukDlQyB9O6ASgAmlvQ) → [归一化残差](https://mp.weixin.qq.com/s/v-SBuMTbMANSTxHj7gYDkg) → [Transformer 全景](https://mp.weixin.qq.com/s/22J8JPkdpVeUx23KahbBmA) → [预训练](https://mp.weixin.qq.com/s/XoGHVycQHR5Tp-BWPac9Hg) → [SFT 微调](https://mp.weixin.qq.com/s/vwXGbjm9Ai1GPvQi5O3UyQ) → [RLHF 基础篇](https://mp.weixin.qq.com/s/NJDuCLAEfDpILf2J9D6qLQ) → [PPO 深入篇](https://mp.weixin.qq.com/s/OEZtUhm8MT_En7enJo_8dw?token=2031108942&lang=zh_CN) → [GRPO](https://mp.weixin.qq.com/s/t4sO-zC5v1_jq8hJT_YTGA) → **RLVR 收官**

## 参考资料

1. DeepSeek-AI，[DeepSeek-R1: Incentivizing Reasoning Capability in LLMs via Reinforcement Learning](https://arxiv.org/abs/2501.12948)，2025。
2. Wei et al.，[SWE-RL: Advancing LLM Reasoning via Reinforcement Learning on Open Software Evolution](https://arxiv.org/abs/2502.18449)，NeurIPS 2025。
3. Lionrock AI Lab，[L0: Reinforcement Learning to Become General Agents](https://arxiv.org/abs/2506.23667)，2025。
4. Lilian Weng，[Reward Hacking in Reinforcement Learning](https://lilianweng.github.io/posts/2024-11-28-reward-hacking/)，2024。
5. [Sycophancy to Subterfuge: Investigating Reward-Tampering in Large Language Models](https://arxiv.org/abs/2406.10162)，2024。
6. Yu et al.，[DAPO: An Open-Source LLM Reinforcement Learning System at Scale](https://arxiv.org/abs/2503.14476)，2025。
7. [DeepSeek-V4-Flash-0731 `config.json`](https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash-0731/blob/main/config.json)。
8. [DeepSeek-R1 `config.json`](https://huggingface.co/deepseek-ai/DeepSeek-R1/blob/main/config.json)。

#大模型原理 #RLVR #强化学习 #RewardHacking #数解AI
