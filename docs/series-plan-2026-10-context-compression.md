# 上下文压缩与记忆 · 四篇系列写作计划

> 状态：**C1 已发布**（2026-10-25 20:00，[微信链接](https://mp.weixin.qq.com/s/XdAACdIWD2F6d8rq-ZszKg)，目录 `content/2026-10-25-context-compression-info-bound/`）；**C2 已发布**（2026-10-27 21:13，[微信链接](https://mp.weixin.qq.com/s/p-2YkAFT6sBwdU5_dw5O2g)，目录 `content/2026-10-27-compaction-break-even/`）；**C3 已入草稿箱**（2026-10-28 22:00 档，目录 `content/2026-10-28-compaction-constraint-survival/`，draft media_id …TSeoLt）。grill 日志：C1 `.grill/context-compression-info-bound.md` / C2 `.grill/compaction-break-even.md` / C3 `.grill/compaction-constraint-survival.md`。
> 下一步：**C4 记忆账（外传）**——C3 发布后按系列规矩隔一周再开题（10-21~23 三连发 + C1/C2/C3 已连发三篇，C4 需隔周）；开题前先查 C3 实际阅读数据。
> 本文件只记录计划与证据口径；正文素材仍以笔记原文和论文原文为准。

## 0. 一句话结论

素材能撑 **3 篇主线 + 1 篇外传**，但不能写成 4 篇论文综述。四篇各配一个**可推导、可证伪的数学硬约束**：

| # | 篇 | 数学核心 | 反常识结论 |
|---|---|---|---|
| 1 | 信息账 | 率失真 + Fano + 数据处理不等式 | 压缩率不是指标，失真是；丢了关键变量，失败有信息论下界 |
| 2 | 钱账 | 缓存成本模型 + 盈亏平衡 | 缓存越便宜，压缩越不划算；回本回合数 $\propto 1/\rho$ |
| 3 | 安全账 | 策略保持 + 拉格朗日 | 压缩器只为任务成功优化，没有保留安全约束的激励 |
| 4 | 记忆账（外传） | 数据处理不等式 + 贝叶斯陈旧记忆 | 记忆的信息量不可能超过原始历史，只赢在成本 |

**本地统计只作验证集，不作论点。** 202 次 Pi compaction 记录用来检验成本模型；信息论部分由 ACON / KEEP-Bench / TRACE / Raw-RAG 等论文验证。

---

## 1. 先分层，防张冠李戴

> 2026-10-24 作者纠正：DeepSeek V4.1 已经更换架构，且此前文章已写过。**V4.1 是模型层 KV 压缩，不是本系列的落点。**

| 层 | 机制 | 已有文章/素材 | 本系列 |
|---|---|---|---|
| **模型层 KV** | DeepSeek V4.1 Flash：CSA2 跨层复用、40 层只有 3 层记账、890 字节/token、FP4 主 KV、128 token 窗口 Bounded Replay、首层 Top-512 / 候选池 16,384 | `content/2026-09-11-v41-kv-csa2/`、`content/2026-09-24-four-arch-kv/` | **不碰**，最多当对照 |
| **会话层上下文** | Pi / OpenCode / DeepSeek Harness / Claude Code / Codex 的 compaction、prune、tool exposure、session log | 10-08 三家 harness 对比、10-11 MCP 三条路笔记、10-10 Context Rot 篇 | **主线三篇** |
| **跨会话记忆** | Mem0 / Kimi 记忆 / ZCode Memory / GLM 记忆文档 | 10-05 Agent 记忆篇、10-24 Mem0 笔记 | **外传一篇** |

**禁止**：把 V4.1 的 890 字节/token、3/40 层记账当成 agent 会话压缩的证据；那是 KV cache 账，不是 conversation compaction 账。

---

## 2. 四篇总表

| # | 篇 | 主落点（已有素材） | 国产/本机锚点 | 验证 | 状态 |
|---|---|---|---|---|---|
| 1 | 信息账 | ACON 401 案例、KEEP-Bench、TRACE、率失真综述 2607.08032 | Claude Code / Codex 的 compaction 行为 | 论文 + 数学推导 | 未写 |
| 2 | 钱账 | **Pi token logs：202 次 compaction** + Anthropic `clear_at_least` + Codex per-tool 限额 | 本机 107 MB 日志、4,032 个会话 | 成本模型 + 本机数据 | 未写 |
| 3 | 安全账 | Codex commit #41852（2026-10-27 一手）+ Governance Decay + relinking + 本机约束幸存率扫描 | DSH fail-closed / unknown outcome 不自动重试 | 论文摘要 + commit + 本机全量扫描 | ✅ 已入箱 2026-10-28（content/2026-10-28-compaction-constraint-survival/） |
| 4 | 记忆账 | DSH 事件溯源日志 vs Mem0 抽取/合并/检索；Raw-RAG 6/7 第一；62% 过期判定 | Kimi 50 条×500 字、GLM 200 行、ZCode 刻意不记 | Mem0/Raw-RAG/MemoryTax + DPI | 未写（外传） |

**篇目顺序建议**：信息账 → 钱账 → 安全账 → 记忆账。
- 逻辑：先立“压缩有信息上限”，再用成本模型证明“就算信息够也未必划算”，然后讲安全约束为何被目标函数丢掉，最后把同一套 DPI 用到跨会话记忆。
- 备选（数据先行）：钱账 → 信息账 → 安全账 → 记忆账。若想先用本机数据打出差异，用这个顺序。
- **不编号、不写“上篇”**。每篇独立钩子；系列连续性靠文末“四道极限”互链，不靠开头导航。

---

## 3. 每篇细案

### 3.1 信息账：压缩的硬上限

**核心问题**：上下文压缩到底能压到多小？丢了东西，后面能不能靠推理补回来？

**数学核心**

把原始上下文记作 $X$，摘要记作 $Y=f(X)$，下游任务真正需要的变量记作 $Z$（正确动作、必需凭证、状态变量）。因为 $Y$ 只由 $X$ 决定，构成马尔可夫链 $Z\to X\to Y$：

$$I(Z;Y)\le I(Z;X)$$

数据处理不等式：**压缩不可能凭空创造任务相关信息，只能保留或丢失。**

丢信息之后，失败有下界。Fano 不等式：

$$P_e\ge \frac{H(Z\mid Y)-1}{\log|\mathcal Z|}$$

简化成"从 457 个 API 动作里选一个"（457 = AppWorld 的 API 总数，arXiv 2407.18901，ACON 主基准，2026-10-24 已核）、$Z$ 均匀且摘要零信息：

$$P_e\ge 1-\frac{1}{\log_2 457}\approx 88.7\%$$

这是简化模型的下界，不是真实 agent 的失败率；它证明的是：**信息不够时，后面再怎么推理也补不回来，只能重新去取。**

率失真函数：

$$R(D)=\min_{p(y\mid x):\,\mathbb E[d(X,Y)]\le D} I(X;Y)$$

二值信源 + 汉明失真：$R(D)=H(p)-H(D)$。**不声明允许的失真 $D$，压缩率没有意义。**

**反常识**

- “压缩到 10%”不是指标；一个 access_token 只值 1 bit，但任务要求 $D=0$ 时，这 1 bit 不能丢。
- ACON 在小模型上的涨点只能解释为“去掉干扰项、让已有信息被用上”，不能解释为“压缩让模型知道了更多”。
- KEEP-Bench 的“QA 分高估忠实性”，本质是拿错了失真函数：用“答案对不对”代替“证据还在不在”。

**主落点**

- ACON 附录 C 的 401 案例：**未压缩轨迹中** gpt-4.1-mini 反复无认证调 file_system API 持续 401；经（优化后的）压缩，历史只保留关键推理——username+password、access_token 要传入后续调用、supervisor app 无代理 API——任务从失败转成功。⚠️ 2026-10-24 对原文（2510.00615v3 附录 C.2）复核修正：401 循环在未压缩轨迹里，案例是「学习式压缩保住关键变量」的工程证据，**不是**「压缩丢认证」的证据（原转述因果颠倒）。
- ACON 的对比式失败挖掘：在训练集上跑 with/without 压缩两遍，收集“不压缩成功、压缩失败”的轨迹，喂给 o3 改写压缩指南——这是任务相关失真的经验近似。
- TRACE：压缩削弱近期交互影响力，导致动作被阻塞、重复探索、跨运行不稳定。
- Prune the Summary, Not the History（2610.20927）：该修剪的是摘要，不是原始历史；原始历史是信息源，摘要是它的有损函数。

**标题候选（草稿，写前过 SEO 与数字核查）**

- 「上下文压缩的极限：删掉一个 token，任务为什么可能注定失败？」
- 「压缩率不是指标：上下文压缩的率失真下界」
- 「省了 90% token，为什么信息论说它一定会丢东西？」

**边界**

- Fano 是简化成 M 选一任务后的下界，不是真实失败率。
- 率失真的失真函数必须任务相关；用文本相似度/困惑度/QA 分代替，会优化错目标。
- ACON 只在 GPT 系验证；Gemini/Claude/DeepSeek/Qwen 未验证。

---

### 3.2 钱账：压缩的盈亏平衡

**核心问题**：压缩省了 token，为什么账单可能更贵？什么条件下压缩才划算？

**数学核心**

设压缩前上下文 $T$、压缩后 $T'$、缓存命中率 $h$、未缓存单价 $c_{in}$、缓存单价 $c_{cache}$，令 $\rho=c_{cache}/c_{in}$。压缩前缓存是热的；压缩后前缀变了，第一轮按全价重算。把压缩调用折算成压缩前上下文的成本 $\kappa T$：

$$N^*=\frac{\kappa T+T'(1-\rho)}{(T-T')\rho}$$

**关键不是分母，是 $1/\rho$：缓存越便宜，压缩越难回本。**

**本机数据（2026-10-24 粗扫，待受控统计）**

- 202 次 compaction，分布在 153 个会话文件，时间 2026-06-09 ~ 2026-10-17。
- `tokensBefore` 中位数 195,475；最小 789，最大 864,544。
- 196 次有前后配对：压缩前总 token 中位 156,719 → 压缩后 62,341（约 -59%）。
- 但压缩后未缓存输入中位 2,389 → 55,988（约 23 倍）；107/196 次压缩后的未缓存输入反而更高。
- 55 次有 compaction `usage`：压缩调用本身中位 124,202 token；有费用的 39 次，中位约 $0.1（样本偏少，不能当全量结论）。
- 最极端一例：总 token 310,197 → 88,104，但 `input` 52 → 87,946，`cacheRead` 310,016 → 0。
- 54 次有完整 pre/post/compaction 计费记录，其中 37 次 $T>T'$ 可用于回本检验。

**provider 缓存折扣（粗扫线性拟合估计，非官方价目表）**

> ⚠️ **2026-10-26 作者排除令：ollama-cloud 计费不准，其数据一律不入钱账**——下表两条 ollama-cloud 行作废、下方 37 样本回本表作废；以 4.4 节受控统计（剔除 ollama-cloud / commandcode）为准。

| provider / model | 估计 $\rho$ | 状态 |
|---|---:|---|
| opencode-go deepseek-v4-pro | 0.003 | ✅ 受控复现一致（0.0030） |
| ~~ollama-cloud deepseek-v4.1-flash~~ | ~~0.02~~ | ❌ 2026-10-26 排除 |
| ~~ollama-cloud deepseek-v4-flash:0731~~ | ~~0.127~~ | ❌ 2026-10-26 排除 |
| xiaomi-mimo-tp mimo-v2.5-pro | 0.20 | 未进受控窗口（无 compaction 样本） |

**回本敏感性（37 次可用样本；含 ollama-cloud，口径已作废，仅存档）**

| $\rho$ | 回本回合中位数 $N^*$ | 实际回本比例 |
|---:|---:|---:|
| 0.003 | 387.1 轮 | 10.8% |
| 0.02 | 57.3 轮 | 64.9% |
| 0.10 | 11.0 轮 | 86.5% |
| 0.127 | 8.6 轮 | 86.5% |
| 0.20 | 5.3 轮 | 91.9% |

**反常识**

- 同一个压缩动作，在缓存几乎免费的 provider 上是净亏，在缓存贵的 provider 上几轮就赚回来。
- “压缩省 token”只看了 $T-T'$，没看 $\rho$ 和 $\kappa$；缓存越便宜，省下的 token 越不值钱。
- 短会话（未来回合数 < $N^*$）压缩是净亏；长会话才可能回本。

**主落点**

- **本机 Pi token logs**：`~/.pi/token-logs/usage.jsonl`（107 MB，358k+ 行；字段含 `inputTokens / outputTokens / cacheReadTokens / cacheWriteTokens / totalTokens / cost / ttftMs / tps`）。
- **会话 JSONL**：`~/.pi/agent/sessions/**/*.jsonl`（4,032 个会话；`type:"compaction"` 事件含 `tokensBefore`、`summary`、`usage`、`firstKeptEntryId`）。
- Anthropic context editing：清旧工具结果会击穿 prompt cache 前缀，所以要设 `clear_at_least`，保证“清得够多才值得”。
- Codex：per-tool `output_token_limit` + 全局兜底；`model_auto_compact_token_limit` + scope。
- OpenCode：曾每轮 `session.compaction.prune` 剪 tool results 导致 prompt cache 全失效（作者后来改过，**不能写成现状**）。

**标题候选**

- 「压缩省了 60% token，为什么账单可能更贵？一个盈亏平衡公式」
- 「缓存越便宜，上下文压缩越不划算？」
- 「什么时候该压缩？先算这个回本回合数」

**边界**

- 成本模型是一阶近似；缓存行为、阶梯计价、任务阶段、输出 token 都会让 $N^*$ 偏移。
- 54 次有完整计费的记录是有偏子集；provider 的 $\rho$ 是回归估计，写稿前必须对官方价目表复核。
- `tokensBefore` 是压缩前上下文大小；`usage.totalTokens` 是压缩调用本身，两者不能混为“压缩省下的 token”。

---

### 3.3 安全账：压缩器的激励错位

**核心问题**：压缩后的上下文，为什么能骗过安全检查？

**数学核心**

安全策略记作谓词 $P(X)\in\{0,1\}$，压缩器 $f$。策略保持的定义：

$$\forall X:\;P(X)=1\;\Rightarrow\;P(f(X))=1$$

压缩器的目标函数里只有任务成功 $S(f(X))$，没有 $P$。拉格朗日形式：

$$\max\;\mathbb E[S(f(X))]-\lambda\,\mathbb P(P(f(X))=0)$$

默认 $\lambda=0$，所以“丢掉一条安全约束”在优化里是免费的。Governance Decay 不是 bug，是**目标函数里没这一项**。

relinking 攻击：每份原始文档都满足 $P(X_i)=1$，但摘要把分散的良性片段组合成一条完整恶意指令，$P(f(X))=0$。这是构造性反例，证明 $P$ 在摘要下不保持。

修法：压缩后加验证器，或把 $P$ 硬写进压缩目标。代价是“安全税”：约束下的率失真 $R_P(D)\ge R(D)$，压缩率必须让步。

**反常识**

- 安全检查看的是压缩前的 $X$，执行用的是压缩后的 $Y=f(X)$；检查与使用不是同一个对象。
- 压缩器不是攻击者，但它会把良性片段组合成恶意指令——confused deputy。
- “摘要忠实于原文”不等于“策略保持”；忠实是语义相似，策略保持是谓词不变。

**主落点**

- Codex v0.152：压缩后会丢用户指令与未结授权；修法是让压缩 prompt 显式枚举本次会话的用户指令与 Guardian 授权，摘要必须保留。**目前是第三方整理（codex.danielvaughan.com），未独立验证；写稿前必须核 Codex changelog/PR 原文。**
- Governance Decay（2606.22528）：压缩会静默抹除安全约束。
- Safe to Check, Unsafe to Use（2606.21732）：relinking 攻击；过滤器检查压缩前 prompt，后端执行压缩后新生成的上下文。
- DSH 的对照：`session-checkpoint-policy` 三道屏障 + fail-closed + `unknown outcome` 不自动重试——用“不确定就不执行”代替“摘要里应该还在”。

**标题候选**

- 「安全检查看压缩前，执行为什么用压缩后？」
- 「压缩器为什么会成为安全检查的替罪羊？」
- 「一条被摘要掉的安全规则，是怎么让 agent 越权的？」

**边界**

- 策略保持是形式化模型；relinking 是构造性攻击，不是所有压缩器都必然中招。
- Codex 案例是历史 bug，不能写成现网行为；必须核原文。
- 不要把它写成“压缩很危险，别压缩”；结论应是“压缩目标里必须显式加约束”。

---

### 3.4 记忆账（外传）：记忆只是历史的有损函数

**核心问题**：Mem0 有 67,635 star，为什么输给原始历史 + 检索，甚至输给几个 Markdown 文件？

**数学核心**

记忆 $M=g(H)$ 是完整历史 $H$ 的函数，当前状态 $S$ 构成 $S\to H\to M$：

$$I(M;S)\le I(H;S)$$

数据处理不等式：**记忆层对当前状态的信息量，永远不可能超过原始历史。** 它唯一能赢的是检索成本、延迟、格式。模型自己能搜原始历史时，这个优势就被打掉了。

陈旧记忆的贝叶斯模型。状态以风险率 $q$ 变化，记忆写于 $k$ 步之前：

$$P(M\mid S_t)=(1-q)P(M\mid S_{t-k})+q\,P(M\mid \text{noise})$$

$q$ 大时，似然被噪声主导，后验可能比先验还糟。记忆的价值：

$$V(M)=\mathbb E[\Delta L]-c(M)$$

它可以为负。

**反常识**

- 记忆层不是“记忆”，是历史的一个有损摘要；按 DPI，它对当前状态的信息不可能超过原始历史。
- 记忆只在“当前状态变化慢 + 检索成本高”时划算；状态变化快时，它会把旧判断带进新任务。
- 结构化抽取（Mem0 的 ADD/UPDATE/DELETE）不等于理解；审计潮里 Raw-RAG 在 6/7 个设置第一。

**主落点**

- Mem0（2504.19413）：extraction / consolidation / retrieval；ADD/UPDATE/DELETE/NOOP；GitHub 67,635 star（2026-10-24 快照，写前复核）；claude-mem 101,934 star 反超。
- Raw-RAG（2610.30755）：原始历史 + 稠密检索 + 重排在 LoCoMo / LongMemEval / MEME / MemoryAgentBench 七个设置中六个第一。
- MemoryTax（2610.29823）：mem0/Zep 在问题到来前决定保留什么；coding agent 保留原始历史让模型自己搜。
- Memories That Outlive Their Reasons（2610.25123）：模拟长对话中 agent 62% 的任务发布了已失效判定。
- The Value of Memory（2609.31303）：决策论框架，记忆价值 = 避免的任务损失；rate-cost 前沿。
- DSH 对照：事件溯源日志、append-only `SessionEvent`、“Model-visible means logged”、`deriveMessages()` 投影、committed generation 永不改写——保留原始历史，而不是只留摘要。

**标题候选**

- 「Mem0 有 67,635 star，为什么信息量比不过原始历史？」
- 「记忆层的信息上限：数据处理不等式早就说了」
- 「记得越准，为什么反而越容易错？」

**边界**

- DPI 说的是“信息量”，不是“效用”；记忆仍可能因低延迟、低成本、格式化而有用。
- Mem0 的 star 数是快照；Raw-RAG 的“6/7 第一”要核具体设置与基线。
- 62% 是特定模拟长对话的设置，不能外推成所有 agent。

---

## 4. 本机数据与复现口径

### 4.1 数据位置

| 资产 | 路径 | 规模/字段 |
|---|---|---|
| Pi token logs | `~/.pi/token-logs/usage.jsonl` | 107 MB，358k+ 行；`date, time, apiKeyPrefix, provider, model, source, inputTokens, outputTokens, cacheReadTokens, cacheWriteTokens, totalTokens, cost, ttftMs, tps` |
| Pi sessions | `~/.pi/agent/sessions/**/*.jsonl` | 4,032 个会话；`type:"compaction"` 事件含 `timestamp, summary, firstKeptEntryId, tokensBefore, details, usage, fromHook, systemMessage` |

### 4.2 统计口径

1. 遍历 session JSONL，找 `type=="compaction"` 事件。
2. 向前找最近一条 `role=="assistant"` 且带 `usage` 的消息，记 pre。
3. 向后找最近一条 `role=="assistant"` 且带 `usage` 的消息，记 post。
4. 统计 pre/post 的 `input`、`cacheRead`、`totalTokens`；compaction 的 `usage.totalTokens`。
5. 未来回合数 = compaction 之后 `role=="assistant"` 的消息数（代理指标，不等于任务剩余步数）。
6. 回本公式：$N^*=\dfrac{\kappa T+T'(1-\rho)}{(T-T')\rho}$，其中 $\kappa=C_{comp}/T$，$\rho=c_{cache}/c_{in}$。
7. $\rho$ 的估计：对同一 provider/model 的付费记录做线性拟合 `cost ~ inputTokens + cacheReadTokens + outputTokens + const`，取 `cacheRead` 系数 / `input` 系数。

### 4.3 已知偏差

- 跨模型、跨 provider、跨任务阶段；不是受控实验。
- 很多免费/本地模型 `cost=0`，会拉低费用中位数；有费用样本只有 39 次。
- `commandcode` 的拟合 $\rho>1$（约 10.25），疑似计价结构异常/缓存写入单独计价，**不纳入结论**。
- **`ollama-cloud` 计费不准（作者 2026-10-26 拍板），ρ 拟合 / N\* / 回本 / 费用统计一律不用其数据**。
- **`xunfei` / `xunfei-ex` 数字一律不算（作者 2026-10-26 拍板「讯飞的数字也不要算」）——全量排除，token 量级也不用**（它们不报 cacheRead、cost=0，此前还把聚合中位数拉低、把缓存命中率压平）。
- 未来回合数是会话内 assistant 消息数，不是“任务还需要多少步”；只作一阶代理。
- 压缩后的第一条 assistant 消息可能包含压缩摘要调用本身，需在受控统计里排除。

### 4.4 受控统计（2026-10-26，C2 开题前置，作者拍板 #3 的口径）

脚本 `scripts/compaction_stats.py`（`--window 5`），逐样本明细 `content/2026-10-27-compaction-break-even/compaction_controlled.json`。

- **样本漏斗**：202 次 compaction → 168 个「同 provider+model、压缩前后各 5 轮」窗口 → **剔除讯飞（全量，78 个）与 ollama-cloud / commandcode（钱账）后 51 个干净窗口**，其中 $T>T'$ 可回本检验 **49 个**。
- **降幅（标题口径）**：tokensBefore 中位 **267,916** → 压缩后首轮 **60,889**（聚合 **77%**；逐样本降幅中位 **75%**，n=51）。含讯飞的 68% 是被稀释的旧口径，弃用。
- **缓存击穿与恢复（第二节证据）**：前 5 轮每轮 input 中位 **1,006**、cacheRead **242,893**、命中率 **99.6%**；压缩后第 1 轮 input **34,543**、命中率 **48.5%**；第 5 轮恢复 98.3%。每轮成本中位 $0.0865 → $0.0532。
- **ρ 拟合（usage.jsonl 全量计费行，剔除排除名单）**：opencode-go/deepseek-v4-pro **0.0030**（n=26,191，R²=0.850）；ainaiba/gpt-5.4/5.5/5.6 与 fenno/gpt-5.5/5.6-terra 全部 **0.1000**（n 合计 1.6 万+，R²=1.000）；opencode-go/glm-5.2 **0.1857**（n=1,244，R²=1.000）；opencode-go/muse-spark 0.02；opencode-go/v4-flash-vision-exp 0.033。xunfei 系不报 cacheRead（0%），已全量排除。
- **回本翻转（同一压缩动作，N\* 差 85 倍）**：V4-Pro（ρ=0.003）N\* 中位 **169.8 轮**、未来轮中位 92 → **实际回本 20%**（5 样本 1 中）；ainaiba/gpt-5.5（ρ=0.10）N\* 中位 **2.4 轮** → **100% 回本**；opencode-go/glm-5.2（ρ=0.186）N\* **2.0 轮** → 100%。fenno/gpt-5.6-terra 一例 N\*=6 但未来仅 27 轮 → 67%（短会话是另一个亏损维度）。
- 拟合 ρ 复现了粗扫的 opencode-go/V4-Pro 0.003，两条线互证。**⚠️ 2026-10-27 作者指令：opencode-go 网关例子不进正文（V4-Pro 0.003、glm-5.2 0.186 一并移除），论证走官方价**——DeepSeek V4.1-Flash 官方 ρ=0.02（峰谷两时段同）、V4-Pro 官方 0.033、**GLM-5.3-Flash 官方 0.20（Z.ai 定价页 $0.15/$0.50/$0.03；10-27 修正——此前误采第三方转售价 0.8/0.23 元算出 0.29）**、OpenAI 10%（= GPT-5.x 账单拟合互证）。49 样本官方价 what-if：ρ=0.20 → N\* 1.6 轮 / 100% 回本；0.10 → 3.5 轮 / 96%；0.02 → 19.3 轮 / 84%（C>0 子集 n=12 → 53.6 轮 / 92%）。网关拟合数据仅存档于此，作交叉验证线索。
- **官方价目对照（2026-10-26 搜核，写稿引用前逐条开官方页复核）**：OpenAI 官方 cached input ≈ 输入价 10%（如 GPT-5.4 自动缓存 10%）→ ainaiba/fenno 拟合 ρ=0.1000 与官方口径一致，账单拟合升级为「与官方一致的锚点」；DeepSeek 官方 2026-04 价 V4-Pro 缓存命中 0.1 元/M vs 未命中 3 元/M（ρ≈0.033），**2026-08-17 起改峰谷定价**（缓存命中空闲 $0.02~0.04 / 高峰 $0.15~0.30，未命中 $0.15~1.32）→ 官方 ρ 本身随时段漂移；opencode-go/V4-Pro 网关价 ρ=0.003 比官方再低一个量级。Anthropic 官方 cache read = 0.1× 输入价（写稿时连同 `clear_at_least` 一起核文档）。

---

## 5. 阅读与核实清单

### 5.1 数学底子（P0）

- [ ] Cover & Thomas《Elements of Information Theory》第 2 章：数据处理不等式、Fano 不等式
- [ ] Cover & Thomas 第 10 章：率失真函数；二值信源 + 汉明失真的 $R(D)=H(p)-H(D)$
- [ ] Shannon 1959, "Coding theorems for a discrete source with a fidelity criterion"
- [ ] vault `Shannon率失真理论.md`；`Rate-Distortion View of Memory Compaction`（2607.08032）

### 5.2 信息账（P0）

- [ ] ACON `2510.00615v3`：Table 1/2 逐格数字、Table 4 延迟账、附录 C 的 401 案例、附录 D 的指南原文
- [ ] KEEP-Bench `2610.26827`：4102 案例、QA 分与证据忠实性的差距
- [ ] TRACE `2608.06503`：配对闭环续跑方法、“近期交互影响力下降”的具体幅度
- [ ] Counterfactual Continuations `2609.36526`：压缩先伤可靠性、再伤可解性

### 5.3 钱账（P0/P1）

- [ ] 本机 token logs / sessions 的受控统计（同模型、相邻时间窗、压缩前后各 5 轮）
- [ ] provider 官方价目表：缓存读/写单价，核对回归估计的 $\rho$
- [ ] Anthropic `context-editing` 文档：`clear_tool_uses`、`clear_at_least`、prompt cache 权衡
- [ ] Codex `config-reference`：`model_auto_compact_token_limit`、`model_auto_compact_token_limit_scope`、per-tool `output_token_limit`
- [ ] OpenCode 历史 prune 行为：作者演讲原文，确认后来是否已修

### 5.4 安全账（P1）

- [ ] Codex v0.152 changelog/PR 原文：压缩后丢用户指令/Guardian 授权（**目前第三方，必须核**）
- [ ] Governance Decay `2606.22528`：哪些约束被抹除、任务设置、幅度
- [ ] Safe to Check, Unsafe to Use `2606.21732`：relinking 攻击条件、过滤器位置、成功率
- [ ] AI Guardrail Survival `2608.11392`

### 5.5 记忆账（P1）

- [ ] Mem0 `2504.19413`：机制与 LOCOMO 数字；GitHub star 复核
- [ ] Raw-RAG `2610.30755`：七个设置、基线定义、六个第一的具体口径
- [ ] MemoryTax `2610.29823`：419 轮 LoCoMo + Pi/Codex/Claude Code × 三档模型
- [ ] Memories That Outlive Their Reasons `2610.25123`：62% 的任务设置
- [ ] The Value of Memory `2609.31303`：决策论框架、rate-cost 前沿
- [ ] Memory as Infrastructure `2609.05510`：63.3 万行 Claude Code 会话、压缩 + 持久记忆双基础设施
- [ ] DSH 官方文档：`docs/architecture.md`、`packages/session/*`、`Model-visible means logged`

---

## 6. 写作顺序与门禁

### 6.1 顺序

1. **信息账**：定理地基，先立“压缩有硬上限”。
2. **钱账**：用本机数据做第一次证伪；成本模型 + 敏感性。
3. **安全账**：目标函数缺项，安全约束被静默丢掉。
4. **记忆账（外传）**：DPI 用到跨会话记忆；与 10-05 篇明确分工。

### 6.2 每篇流程

1. **grill-me**：先与作者逐题讨论，收敛后写 `.grill/<slug>.md`；**禁止 AI 单方面生成 grill 日志**。
2. **math_audit**：在文章目录写 `math_audit.md`，逐条列公式、假设、反例、每个数字的出处；正文数字必须能回溯。
3. **outline.md**：定位、结论、结构、配图、既有检查清单。
4. **原声槽**：AI 一次只提 1 个槽位（位置 + 为什么这里 + 问你一句 + 方向），作者逐条手动输入；**≥5 处才写正文**，禁止批量“过”式代填。
5. **weixin.md**：正文约 2000 字（含尾部总计 ≤2500）；段落 ≤80 字；多级标题；术语 ≤2 个。
6. **quality_check.py**：过 `docs/article-quality-check.md` 的 20 项；发布前过 `docs/pre-publish-final-check.md` 的 9 项。

### 6.3 原声槽方向（不代写句子）

四篇笔记里**没有一处第一人称“我的判断/我踩过”**（已核对），原声是真正瓶颈。可采集的方向：

- **信息账**：你第一次看到“压缩后任务重跑/认证失败”的具体场景；丢过哪个 token/path/凭证；你对“压缩率不是指标”的第一反应。
- **钱账**：你看到 token 降了但账单/延迟升了的经历；你选 provider 时是否看过缓存折扣；你实际用 Pi 压缩的频率与体感。
- **安全账**：你见过哪次约束/授权被摘要掉；你对“压缩后加验证器”的工程判断；你所在项目的权限边界故事。
- **记忆账**：10-05 记忆插件翻车经历；Kimi/ZCode/GLM 记忆的实际使用；你对“Markdown 比记忆层可靠”的判断。

---

## 7. 禁止事项 / 常见错误

1. **不要把 V4.1 当落点**：V4.1 是模型层 KV 压缩（CSA2、3/40 层、890 字节/token），不是 agent 会话压缩；已有 09-11、09-24 两篇。
2. **不要跨基准拼数字**：54.5% 是 8-objective QA 的 peak token；73→102 秒是 AppWorld 的 observation compression；不能写成“省 54% 却慢 29 秒”。
3. **不要编 401 次数**：ACON 案例只写“持续 401”，没写次数；标题不能写“40 次”。
4. **不要把 Codex v0.152 当一手**：目前是第三方整理，写前核 changelog/PR。
5. **不要把 Fano 当真实失败率**：它是简化 M 选一任务的下界。
6. **不要把成本模型当账单预测**：它是一阶近似；$\rho$ 必须用官方价目表复核。
7. **不要写“记忆没用”**：DPI 只说信息量上限；记忆仍可能赢在成本、延迟、格式。
8. **不要编号/不要“上篇”**：系列连续性靠文末互链，不靠开头导航；每篇独立钩子。
9. **不要同日双发同题材**；3 篇主线可连发（10-21~23 已验证 116/119/79），但每篇换主角；第 4 篇隔一周。

---

## 8. 作者拍板（2026-10-24 已定）

1. **主轴**：C1 信息账首篇，**只锁这一篇**，C2/C3/C4 后议。
2. **系列规模**：只定下一篇；C4 记忆账（外传）与 C1 的关系在 grill 中确认为「C1 是记忆篇的数学前传，DPI 地基由 C1 铺垫」。
3. **钱账的统计深度**：C2 开题前先做受控统计（同模型、相邻时间窗、压缩前后各 5 轮）。
4. **安全账的边界**：主线用 Governance Decay + relinking；Codex v0.152 核不到一手就降为佐证或砍。

拍板后已开 `grill-me` 并收敛（C1）；grill 日志待作者确认，确认后才写大纲。

---

## 9. 更新记录

- 2026-10-26：C1 已发布（2026-10-25 20:00，[微信链接](https://mp.weixin.qq.com/s/XdAACdIWD2F6d8rq-ZszKg)），下一步 C2 钱账。完成作者拍板 #3 的**受控统计**（§4.4：168 同模型 5/5 窗口、121 可回本检验；脚本 `scripts/compaction_stats.py`）。**作者排除令：ollama-cloud 计费不准，钱账数据一律不用**（粗扫 ρ 表两条 ollama 行与 37 样本回本表作废存档）。
- 2026-10-24：建立。来源为作者 Obsidian 四篇上下文压缩/记忆笔记（`Agent上下文压缩-2026研究全景与HN讨论`、`ACON论文精读`、`ACON后续研究`、`Mem0喧嚣与后果`）+ `Pi-vs-OpenCode-vs-DeepSeekHarness` + `MCP处置三条路` 笔记 + 本机 Pi token logs / sessions 粗扫。已按作者纠正，把落点从 V4.1 模型层改为 harness 会话层。
- 2026-10-28：**C3 安全账入草稿箱**（content/2026-10-28-compaction-constraint-survival/，排期 10-28 22:00）。全流程：grill 五问收敛（.grill/compaction-constraint-survival.md）→ 本机新实验（scripts/constraint_survival_scan.py：4,041 会话 / 202 次 compaction / 2,556 条约束实例；规则形态丢失 0.3% vs 叮嘱形态 24.4%；87.6% summary 自带 Constraints 节）→ 一手核验三件套（Governance Decay 2606.22528 / relinking 2606.21732 / **Codex commit #41852**——系列计划原记「v0.152 第三方待核」升级为 first-party）→ 原声 8/8 逐槽交互 → 正文 1,746 字 → quality_check PASS → 6 图（封面 + 3 脚本图 + 2 AI 概念图）→ remote-api 入箱。**作者两条新硬约束**：① 原声不进引用块（覆盖 C1/C2 ★ 惯例）；② 原声语气词（嗯/呃）删除。下一步 C4 记忆账隔周开题。
