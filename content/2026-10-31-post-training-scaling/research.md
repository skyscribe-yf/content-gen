# 后训练为什么能在一个月内改写同一个基座？——资料挖掘笔记

> 状态：**选题研究阶段**（未定大纲）。目录名 2026-10-31 为建库日，发布日期确定后按规则重命名。
> 用途：给作者挑主线用。所有数字均标注一手出处，写稿前仍需逐项回原文复核。

---

## 0. 一句话结论

后训练不是「给模型灌新知识」，而是三件事的叠加：
**① 把基座里已有但采样不到的能力（pass@k）压成一次答对（pass@1）；
② 用可执行、可验证的环境把「练什么」从人工出题换成自动造环境；
③ 用蒸馏把强老师的解题轨迹低成本搬进小模型。**
三件事里，2026 年真正在扩的是第 ②，而 ①②③ 都有一个共同天花板：基座本身。

---

## 1. 一手事实：三个模型自己怎么说的

### 1.1 GLM-5.3（智谱，2026-08-14）

- 原文：「**Scaling post-training is all we did for GLM-5.3.** It uses the same base model as GLM-5.2 — every gain comes from post-training.」（z.ai/blog/glm-5.3）
- 「Over the past month we kept scaling on this stack: more environments, more diverse tasks, and more compute spent training on them.」→ **一个月、基座不动**
- 数字（GLM-5.2 → 5.3）：
  - Z.ai Code Bench（内部体感）**+50%**
  - Terminal-Bench 3.0：**4.6 → 28.3**
  - DeepSWE v1.1：**46.2 → 66.9**
  - Agents' Last Exam (CLI)：**23.8 → 28.5**
  - CyberGym：**77.2 → 84.5**；ExploitBench：**24.4 → 54.4**；ExploitGym 2h/6h：**29/39 → 105/130**
  - 官方口径：「涌现的网络安全能力……随后训练规模持续扩大，以超出预期的速度提升」
- 环境做法（这篇最值钱的部分）：
  - 任务不再是编程题，而是「**资深工程师也要做几天**」的完整工作单元（给集群、存储、内部文档、代码库、实验结果，让它自己找瓶颈、改、跑实验、交可量化加速）
  - **端到端合成任务环境**：研究 agent 从真实工作里抽任务模式 → 变成可运行、多步依赖、带隐藏状态的长程环境；判分 agent 先试做，确认可解
  - **验证器不看参考解**生成；用求解轨迹找并堵「奖励捷径」；只有同时通过 **oracle / 空操作 / 未解决态** 三项检查的验证器，产出的二值奖励才准予训练
  - 沿用 GLM-5.2 的 **SAO + 上下文压缩**，让增益留在长程任务上；训练框架 **slime**（github.com/THUDM/slime）

### 1.2 GLM-5.3-Flash（2026-08-26）

- **320B 总参 / 18B 激活**；首个「稀疏注意力 + 线性注意力」混合架构开源前沿模型
- 对比 GLM-5.3：注意力计算量 **降 3.01×**、KV cache **降 4.44×**；定价 **1/10**（限时 1/20，Opus 4.8 的 1/40）
- Artificial Analysis 智能指数 **57**，与 Claude Opus 4.8 持平（GLM-5.2 为 53）
- ⚠️ 注意：Flash **不是**同一个基座——「starts from a newly trained base model」，30T token 多模态预训练
  → 正好构成对照组：**旗舰靠后训练改写同一基座；Flash 靠「新小基座 + 高效架构 + 后训练」越级**

### 1.3 DeepSeek-V4.1-Flash（2026-09-10）

- 原文（最狠的一句）：「**we refrain from introducing novel post-training algorithms** … our efforts are concentrated almost entirely on **what the model is trained on rather than how it is optimized**」
- 「under a fixed and unremarkable optimization procedure, systematic improvements in the **scale, diversity, and verifiability** of synthesized data and environments account for essentially **all** of the observed gains」
- 「the marginal return of engineering the data and environment pipeline **substantially exceeds** that of algorithmic novelty in post-training」
- 规格：预训练 **45T tokens**（多模态）；**552B 总参 / 8B 或 16B 激活**；Base 用 **1/3 总参、1/4 激活** 达到 V4-Pro-Base 水平
- 后训练配方：**SFT → RL → OPD**（与 V4 一致；V4 是「混合 RL 阶段整体被 OPD 取代」，10+ 领域专家、全词表 reverse-KL）
- 结果（小模型越级）：
  - DeepSWE v1.1 **74.2%**（V4-Flash 54.4；Opus-5 74.0；GPT-5.6 Sol 73.0）
  - Terminal-Bench 2.1 **90.6%**（Opus-5 89.1；GLM-5.3 88.2）
  - Codeforces rating **3471**（V4-Pro 3348）；MathArena Apex 65.6%（=Kimi-K3）
- 数据/环境工程：
  - 任务 = **(problem, environment, verification system)** 三元组，按「难度 + 正确性」两维打分，再用这两个信号训模型自己造任务
  - 通用 agent：员工/伙伴回传真实交互 → 造 **mock 工具**（复刻接口/行为/约束）→ 把真实失败案例做成单轮/多轮环境重放
  - coding agent：内部高难 session + 高星 GitHub 仓库 → 多 agent 协作建容器、设计 fail-to-pass/pass-to-pass 评测点、自测、去解法痕迹、独立质检 agent 查「环境问题 / 事实错误 / 评测点与描述不符 / 可 hack 风险」，不过则返修重验
  - RL 两个扩展维度：**训练算力 × scaffold（harness）数量**；跨 scaffold 训完用 **model merging 重新初始化下一轮 RL**，把有效算力推出单次训练的上限
  - 沙箱平台 **DSec**：单集群管理**数十万并发 sandbox**，分片 + 弱一致性调度，不用 K8s

### 1.4 成本参照（回答「为什么这么快」的量级感）

- DeepSeek-R1 的 RL：**64×8 = 512 张 H800，198 小时** ≈ 10 万 GPU 小时（R1 技术报告 B.4.4）
- DeepSeek-V3 预训练：**2.788M H800 GPU 小时**
- → RL 阶段约等于预训练的 **3.6%**。GLM 口径更直白：同样的 stack，再堆一个月后训练。

---

## 2. 论文怎么说：机制层证据

### 2.1 「放大器」主证据：RL 提高的是采样效率，不是凭空长出新能力

- **Yue et al., arXiv:2504.13837**（NeurIPS 2025 oral）
  - 结论：RLVR「enhances **sampling efficiency** without expanding the reasoning capacity already present in base models」；**大 k 时基座反超 RL 版**
  - 即：基座里其实存在正确解法，只是概率低；RL 把这条路径的概率抬起来 → pass@1 涨，pass@k 上界没变
- **反方，arXiv:2506.14245（MSRA）**：用 **CoT-Pass@K**（同时看答案和中间推理步骤）重做实验，认为 RLVR **确实扩展推理边界**；并给出「只给答案奖励也能激励正确推理」的理论解释
- 写作口径：**这是活跃争议，不能写成定论**。安全说法：RL 至少大幅提高了采样效率；是否扩边界取决于怎么定义「会」

### 2.2 但放大器要有东西可放大：预训练决定 RL 的斜率

- **arXiv:2607.16097**（NYU 等，国际象棋受控实验，5M–1B 参数）
  - 「post-RL performance at a given RL compute level is well-predicted from the **pretraining loss**」；「slope of the RL reward curves improves approximately **linearly with the pretraining tokens**」
  - 且 RL **不只是把 SFT 策略变尖**：简单题上放大 SFT 已偏好的走法，**难题上能找到 SFT 下几乎不存在的正确走法**
  - 用途：一句话解释「为什么后训练能提分，但换不来跨代能力」——**地板是预训练铺的，后训练是斜率**

### 2.3 真正的扩展轴换了：环境 > 任务 > 轨迹

- **arXiv:2610.23946**（MBZUAI 等）
  - 把 agentic 数据拆成三条基数轴（**task / environment / trajectory**）+ 奖励密度控制变量，在多模型、多域（数学+代码 / SWE / web / UI 工具）、PPO 与 GRPO 上拟合
  - 「the scaling exponents order as **environment > task > trajectory**」；环境多样性里主要起作用的是 **world diversity**（而非环境结构多样性）；合成/真实比例超过临界点会崩，**各轴临界比例差一个数量级**
  - 与厂商口径完全对上：GLM 说「难点从模型转移到任务环境」，DeepSeek 说「环境 > 算法新颖性」
- **ScaleRL, ICLR 2026（The Art of Scaling RL Compute, arXiv 预印本同名）**
  - 40 万 GPU 小时系统研究，sigmoid 拟合；单次 **10 万 GPU 小时** 的 8B 训练可外推预测
  - 关键：**loss 聚合、归一化、课程、off-policy 程度等细节主要改「算力效率」，不改渐近线**；而**模型越大，渐近线越高**
  - 用途：既支持「算法不是瓶颈」，也支持「小模型有上界」
- **arXiv:2607.13389**（固定预算下算力怎么分）
  - 同等 FLOPs 下，更大策略每次 token 更贵 → 买到的更新/rollout 更少；最优分配随模型规模、奖励系统、评测目标漂移
  - 用途：解释「为什么 Flash 档位是工程最优解，而不是单纯省钱」

### 2.4 小模型的特殊通道：蒸馏能搬「会解」，搬不动「知道何时停」

- **arXiv:2609.37326（On-Policy Distillation at Small Scale）**：Qwen3-8B → 4B / 1.7B / 0.6B
  - 「Long reasoning needs two abilities, **solving** a problem and **knowing when it is solved**」→ 蒸馏**只转移前者**
  - 天花板：「a student's **single attempt never exceeds what it could already reach in many attempts before training**」；学生越小，离老师越远
  - 停不下来：「in thinking mode students **stop ending their reasoning early** in training, and the smaller the student, the less of this ability survives」；「distillation teaches **no new stops**」——老师几乎只在学生本来就会停的地方给停止信号
  - 最小档常见症状：算到了正确值，但**不落笔**（很少标记）或**写过头**（标记了还继续写）
  - 用途：这是全篇最好的反常识钩子——**小模型后训练后变强了，也变啰嗦了，而且这不是 bug，是机制**
- 旧证据（可作历史线）：
  - **DeepSeek-R1 蒸馏**：800k 样本直接 SFT，R1-Distill-Qwen-1.5B 在 AIME 2024 上 28.9%，超过同规模 instruct 基线（报告 Table 6 附近）
  - **Qwen3 tech report (arXiv:2505.09388)**：0.6B–14B + 30B-A3B 走 **strong-to-weak 蒸馏**，先 off-policy 再 on-policy；顺带一个底子证据：Qwen3-1.7B/4B/8B/14B/32B-**Base** ≈ Qwen2.5-3B/7B/14B/32B/**72B**-Base（小模型的地板本身也在抬）

---

## 3. 可写的反常识钩子（按锋利度排序）

1. **「基座没换，一个月，编程 +50%」**——GLM-5.3 官方原话，最能一句话立住「后训练是什么」
2. **「DeepSeek 明说：这次没有任何算法创新」**——增益全部来自数据与环境；反直觉在于行业叙事一直围着算法转
3. **「后训练不教新知识，它把『第 256 次才答对』变成『第 1 次就答对』」**——pass@k → pass@1，一个比喻讲清 sampling efficiency
4. **「小模型学得会解题，学不会停」**——OPD 小规模研究，越小越明显；顺带解释日常体感：小模型爱绕圈
5. **「新的 scaling law 不在算法里，在环境数量里」**——environment > task > trajectory，指数排序是硬结论
6. **成本对照**：「10 万 GPU 小时改写了 278 万 GPU 小时训出来的模型」——量级差 27 倍，却决定了产品能不能用

---

## 4. 三条边界（防止写成「后训练万能」）

1. **上界由基座定**：ScaleRL 显示渐近线随模型规模上升；DeepSeek 自认「science-oriented agentic（TB 4.0）仍与巨模型有差距」；OPD 论文显示单次尝试不超过基座多次尝试的上界
2. **小模型付出的是「元认知」**：会解不会停、爱写过头；thinking 模式下这种退化随规模缩小而加剧
3. **环境与验证器成了新的瓶颈和攻击面**：奖励捷径要靠 oracle / 空操作 / 未解决态三查来堵（GLM），质检 agent 要查「可 hack 风险」（DeepSeek）；「环境工程」的钱从 GPU 转到人力和沙箱（DSec 数十万并发、MiMo 账本已写过）

---

## 5. 与本号既有文章的差异化（避免撞题）

| 已发/已规划 | 内容 | 本篇如何错开 |
| --- | --- | --- |
| 2026-09-04 R1-Zero | 无 SFT 纯 RL 入门机制 | 不提 GRPO 推导，只取「RL 提采样效率」一句 |
| 2026-10-02 RL 幂律/熵坍缩 | 幂律、剪长尾、V4.1 取舍 | 不重复熵坍缩论证 |
| 2026-10-06 合成数据 60 万题 | 合成数据规模 | 本篇讲「环境」而非「题目」，且只引环境指数排序 |
| 2026-09-28 MiMo 账本 | RL 成本结构 | 成本只用一句对照（3.6%），不展开账单 |
| 2026-08-26 知识蒸馏 | off-policy 软标签 | 不展开 KD 数学 |
| content-matrix L1/L2（未写，作者指定） | OPD 多教师整合范式 | 本篇只把 OPD 当「小模型通道」用一段，机制细节留给 L 组 |

---

## 6. 三条候选主线（供作者定夺）

- **A.「放大器」主线**：同一基座、一个月、+50% —— 后训练到底改了什么。机制（pass@k→pass@1）+ 三个模型证据 + 小模型的得与失。**最贴合用户原始问题**，也最容易写得反直觉。
- **B.「环境即新预训练」主线**：scaling 轴从参数/数据换成环境；讲 DSec / slime / 验证器三件套的工程账。**最硬核、最独家**，但读者盘偏窄（与 L 组有部分重叠风险）。
- **C.「小模型的越级」主线**：Flash 档位如何用「小基座 + 后训练」打到 Opus 级，代价是什么。**最贴近读者利益**（便宜好用），但需要更多价格/延迟数据支撑。

---

## 7. 写稿前必须回原文核实（未定稿项）

- [ ] GLM-5.3 与 GLM-5.2 的发布时间差（确认「一个月」口径；release notes 写 8-19 上线，blog 写 8-14）
- [ ] R1-Distill-Qwen-1.5B 的 AIME / MATH-500 具体数（本地 PDF 表格需重排后核对）
- [ ] Qwen3 strong-to-weak 蒸馏的「4B ≈ 72B-Instruct」说法是否出自报告原文（当前只核到 Base 对比）
- [ ] V4.1「模型合并重初始化 RL」的具体收益数字（正文图 7/8 附近，需读图）
- [ ] 环境指数排序论文的拟合区间与模型清单（避免过度一般化）
- [ ] 若引用「27 倍」成本对照，需注明 R1 RL 时长与 V3 预训练口径均不含失败重跑/研究试错
