# math_audit — 上下文压缩的信息账（C1）

> 2026-10-24 建立。规则：正文每个数字必须回溯到本文件某一行；每个公式有假设、边界、反例。
> 状态标记：✅ 已核（有一手/可执行验证）｜🟡 笔记转述（有 arXiv ID，未开原文）｜🔴 待核（无源或口径未定）。

---

## 1. 公式清单

### M1 数据处理不等式（DPI）— 全文承重墙，记忆篇复用

**陈述**：若 $Z\to X\to Y$ 构成马尔可夫链（$Y$ 由 $X$ 决定），则

$$I(Z;Y)\le I(Z;X)$$

**假设**：$Y=f(X)$ 为确定性函数；$Z$ 为任务真正需要的变量（正确动作 / 必需凭证 / 状态）。

**证明梗概**（文中用两行版）：$I(Z;X,Y)=I(Z;X)+I(Z;Y\mid X)$，而 $Y$ 被 $X$ 决定 $\Rightarrow I(Z;Y\mid X)=0$；又 $I(Z;Y)\le I(Z;X,Y)$（数据处理）。故 $I(Z;Y)\le I(Z;X)$。

**边界**：说的是**信息量**，不是效用；等号成立当且仅当 $Y$ 保留了 $Z$ 的全部信息。

**出处**：Cover & Thomas《Elements of Information Theory》第 2 章（数据处理不等式）。✅ 已定位原文章节；**正文只引到章一级，不引定理编号**（编号未逐字复核，文章无引用必要）。

### M2 Fano 不等式（弱形式）

**陈述**：$Z$ 取有限字母表，估计量 $\hat Z=g(Y)$，错误率 $P_e=P(\hat Z\ne Z)$，则

$$P_e\ge\frac{H(Z\mid Y)-1}{\log_2|\mathcal Z|}$$

**假设**：$|\mathcal Z|$ 有限；$H$ 以 bit 计。

**出处**：Cover & Thomas 第 2 章（Fano 不等式）。✅ 章节已定位；正文不引定理编号。

### M3 Fano 工作例（457 动作）

**设定**：任务抽象成「从 457 个 API 动作里选对一个」；$Z$ 均匀；摘要对该选择零信息（$H(Z\mid Y)=H(Z)=\log_2 457$）。

$$P_e\ge 1-\frac{1}{\log_2 457}\approx 88.7\%$$

**算术核**：$\log_2 457=8.8355$；$1-1/8.8355=0.8868$。✅

**457 的出处**：AppWorld（ACON 的主基准）含 9 个 app、**457 个 API**（arXiv 2407.18901 / appworld.dev 海报原文 "457 APIs with detailed docs, 100+ DB tables"）。✅ 已核（2026-10-24 检索）。正文写法：「AppWorld 有 457 个 API，假设agent 要从里面选对下一步……」

**边界（文中必须声明）**：这是**简化 M 选一任务的下界**，不是真实 agent 失败率。真实任务有结构先验（并非均匀、并非零信息），实际 $P_e$ 可以远低于此。下界证明的是「信息不够时推理补不回来」，不是「agent 88.7% 会失败」。

### M4 率失真函数

**陈述**：$R(D)=\min_{p(y\mid x):\,\mathbb E[d(X,\hat X)]\le D} I(X;Y)$

**含义**：不声明允许的失真 $D$，「压缩率」没有意义。

**出处**：Shannon 1959 *Coding theorems for a discrete source with a fidelity criterion*；Cover & Thomas 第 10 章。🔴 复核表述。

> 注：vault 的 `AI数学/Shannon率失真理论.md` 是 0 字节占位锚点（链接靶子，勿删），率失真部分无笔记可依，以上按标准结果陈述，正文引到章一级。

### M5 二值信源 + 汉明失真闭式

**陈述**：$X\sim\text{Bernoulli}(p)$，汉明失真，$0\le D\le\min(p,1-p)$ 时

$$R(D)=H(p)-H(D)$$

$D=0$ 时 $R=H(p)$：**完全无损有不可压缩的底**；$D\ge\min(p,1-p)$ 时 $R=0$。

**出处**：Cover & Thomas 第 10 章标准结果。🔴 复核（示例编号待定，正文不引编号）。

**边界**：只在二值信源 + 汉明失真下成立；不能外推成「所有压缩任务的压缩率公式」。文中用法：给出「能压多小」的一个可复算具体例，配 $D=0$ 边界说明「压不动的那部分」。

---

## 2. 数字清单

| 数字 | 值 | 出处 | 状态 |
|---|---|---|---|
| AppWorld API 数 | 457 | arXiv 2407.18901 / appworld.dev 海报 | ✅ |
| Fano 下界 | ≈88.7% | 由 457 推导（M3） | ✅ |
| 本机 compaction 总数 | 202（153 个会话文件，2026-06-09~10-17） | `~/.pi/agent/sessions/**/*.jsonl`，`type=="compaction"` 计数 | ✅ 口径见 §3 |
| 压缩后 25 步内重复调用 | 20/202（约 10%） | 同日志，同 name+args 精确匹配 | ✅ 口径见 §3 |
| 分月重复调用 | 6 月 13/94；**7 月 31/67（峰值）**；8 月 1/22；9 月 2/6；10 月 0/13 | 同日志按月聚合 | ✅ |
| tokensBefore 中位数 | 195,536（n=202） | 本日志 2026-10-24 扫描（compaction 事件自带字段） | ✅ |
| 压缩前后配对 | 压缩前 assistant totalTokens 中位 182,331（n=148）→ 压缩后第一条 62,610（n=194），约 −66% | 同扫描（最近一条带计费的 assistant 消息，pre/post 口径见 §3） | ✅ 与计划旧值（156,719→62,341）口径不同，以本次为准 |
| ACON 401 案例 | **原文（附录 C.2）**：未压缩轨迹中 gpt-4.1-mini 反复无认证调 file_system API，持续 401 Unauthorized；经压缩后历史只保留关键推理——需要 username+password、要把返回的 access_token 传入后续调用、supervisor app 无代理 API——agent 直接走对「登录→取 token→显式传入」序列，删除 ~/downloads 全部 .pdf 的任务从失败转成功 | arXiv 2510.00615v3 附录 C.2（2026-10-24 已开原文复核） | ✅ **⚠️ 框架修正：401 循环发生在未压缩轨迹，不是压缩丢失导致；案例的正确用法是「学习式压缩保住了任务关键变量」的工程证据。系列计划 §3.1 原转述把因果搞反了，已修正。禁止编造 401 次数。** |
| ACON optimizer 对比 | o3 51.2 > gpt-5 50.6 ≈ o3 无对比反馈 50.6 > gpt-4.1 47.6（Table 3, AppWorld） | arXiv 2510.00615v3 Table 3 原文（2026-10-24 已核） | ✅ 逐格与笔记一致 |
| ACON 主结果（摘要层） | peak token 用量降 26–54% 且任务成功率超基线；最多 +46% 来自缓解 context distraction | arXiv 2510.00615v3 摘要原文 | ✅ 跨基准不拼句（26–54% 与 46% 是不同设置） |
| ACON 双开消融 | history + observation 同时压缩：token 降最多但准确率显著低于单开其一 | arXiv 2510.00615v3 附录 Table 14 | ✅ |
| ACON 被引数 | 90+ | Semantic Scholar 2026-10-24 快照 | 🟡 引用时标日期，数字会变 |
| KEEP-Bench 规模 | 4,102 案例；QA 分高估忠实性 | arXiv 2610.26827（全景笔记转述） | 🟡 |
| TRACE 结论 | 压缩削弱近期交互影响力→动作阻塞、重复探索、跨运行不稳定；被引 11 | arXiv 2608.06503（后续笔记转述） | 🟡 |
| Counterfactual Continuations | 压缩先伤可靠性、再伤可解性 | arXiv 2609.36526 | 🟡 |
| Context Rot 白盒 | 干净上下文 Codex 8/10 → 塞 skill 上下文 3/10 | arXiv 2607.17937 | 🟡 |
| Prune the Summary, Not the History | 该修的是摘要不是原始历史 | arXiv 2610.20927 | 🟡 |

---

## 3. 本机统计口径（复现用）

1. 遍历 `~/.pi/agent/sessions/**/*.jsonl`（4,036 个文件），逐行 JSON 解析。
2. compaction 事件：`type=="compaction"`，字段 `timestamp / tokensBefore / summary / firstKeptEntryId / usage / fromHook / systemMessage`。
3. 消息条目：`type=="message"`，`message.content[]` 内 `toolCall`（`name`+`arguments`）/ `toolResult` / `text` / `thinking`。
4. 重复调用：compaction 后 25 条 entry 内，`name + JSON.stringify(arguments)` 精确匹配去重。
5. 致命丢失判定：压缩后窗口内未发现 401 循环 / 凭证丢失导致的失败模式（2026-06-12 会话的 401 为 CI/gh 命令自身报错，非压缩丢认证，已排除）。

**已知偏差（文中引用时必须带的口径）**：观察性统计、非受控实验；跨任务 / 跨模型 / 跨 provider / 跨 harness 版本混杂；「重复调用」是代理指标（也可能是任务本身需要重试）；摘要模板 6–10 月未变（Goal / Constraints & Preferences / Progress / Key Decisions / Critical Context 骨架稳定），9 月起日志 schema 变化（systemMessage 开始附带完整系统提示词）不影响计数口径。

---

## 4. 反例与自查（评审轮用）

1. **Fano 被误读成真实失败率** → 文中必须紧跟一句「这是简化模型的下界」。
2. **DPI 被误读成「压缩没用」** → 落点是「上限是数学的，皮实是工程的」；DPI 划界，不判死刑。
3. **「逐渐变好」被 7 月峰值打脸** → 只能写「7 月触顶后转干净」。
4. **把 88.7% 和 ACON 的任务分混搭** → 两者不同基准不同量纲，禁止拼一句。
5. **把率失真闭式当通用公式** → 声明二值+汉明前提。
6. **QA 分当压缩质量指标** → KEEP-Bench 的教训：拿错失真函数；文中作为「失真函数必须任务相关」的例证。

---

## 5. 待核清单（按优先级）

**P0（写大纲前）**
- [x] Cover & Thomas 第 2/10 章定位（正文引到章一级，不引定理编号）
- [x] ACON 附录 C 401 案例原文（2510.00615v3）——因果框架已修正

**P1（写正文前）**
- [ ] KEEP-Bench（2610.26827）4,102 案例的口径
- [ ] TRACE（2608.06503）「削弱近期交互影响力」的具体幅度
- [ ] ACON Table 3 数字（o3 51.2 等）若进正文，需对原文

**P2（可选）**
- [ ] ACON 被引数定稿日复核
- [ ] AppWorld 457 API 表述（海报 vs 论文正文，取论文版更稳）
