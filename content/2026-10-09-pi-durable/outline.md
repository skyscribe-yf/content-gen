# 大纲：Pi Durable——工具调用中途崩溃，重发还是放弃？

- 轨道：**文章轨 · AI Agent 工程系列第三篇**（开头零导航；全文不出现「第 N 篇 / 上一篇 / 拆给你看」）
- 合集：**[AI Agent 工程]**（第二篇为 10-08《多智能体路线之争》；链条 = 记得住 → 派得出去 → 崩了不丢）
- 排期：**2026-10-09 20:00**；目录 `content/2026-10-09-pi-durable/`
- grill 日志：`.grill/pi-durable.md`（不蹭热度、5000 字、可公开但不带项目细节、主论点已拍板）
- 篇幅：**实际 5783 汉字（含尾部）**；作者 2026-10-09 口径两次放宽（先「5000 字都可以、写细致一些」，后「长一点没有问题的」），覆盖恢复期 B.3 的 5k 上限
- 立场：**工程立场 + 明确批判**。批判落在"缺口"上（不是产品优劣），给出可验证的替代路径
- 新术语上限 **4**（首次出现给人话版）：`effect sandwich` / `replay` 声明 / `interrupted` 结果 / 幂等键
- **用词红线**：`mint` 一律译为「**另起一个新的**（工具调用 ID）」，全文不出现英文 `mint`；不用「铸造」
- 硬隔离：8-25《Pi 的新架构，答案早就在数据库论文里了》已写过「持久化事实→派生状态→派生上下文→派生 UI」与「先写意图→再做副作用→再写结果」——本篇当作"你已知"**一句带过**，不重讲

## 标题（已拍板）

> **Pi Durable：工具调用中途崩溃，重发还是放弃？**

- 自检：品牌词进前 22 字（`Pi Durable：工具调用中途崩溃，重发还是`）✓；二选一悬念 ✓；陌生人能懂 ✓；无续集感 ✓；无情绪词/热点词（符合"不蹭热度"）✓
- 摘要：**45 次强杀、0 重复工具步骤。它挡得住崩溃重放型重复，挡不住模型重新规划型重复。**
- 关键词：`Pi Durable`、`durable execution`、`Agent 崩溃恢复`、`幂等`

## 封面

- `00-cover.png` 21:9；金色发光标题横贯全幅、两行居中、每行字号约画面高 1/9–1/8、整块文字高 ≤ 画面高 1/4、文字 = 定稿标题**逐字一致**、背景压暗退后、画面无其他文字
- 意象（AI 概念图，无数字无文字）：一条被切断的轨道/管道，断口两侧各悬着一个半完成的方块，远处一端亮着已落盘的方块

## 交付句

- **转 1（机制）**：崩溃点上真正的难题不是"丢了多少"，而是"**我不知道副作用发生了没有**"。pi-durable 的答案是**把不确定本身写成状态**：先提交意图 → 再做副作用 → 再提交结果；停在意图阶段的调用，要么按 `replay` 声明重跑，要么给模型一个带部分输出的 `interrupted` 结果。
- **转 2（主张）**：它做到的是**任务级 exactly-once 记录 + at-least-once 执行**。挡住"崩溃重放型重复"，挡不住"模型重新规划型重复"——重新规划会 mint 新的 `toolCallId`，框架不去重，每层都幂等照样扣款三次。缺的是**编排层派生的幂等键**。
- **转 3（收尾）**：durable 不是"加个重试"，是在失败之后仍然让系统知道自己在哪。而"知道自己在哪"和"世界没有重复"是两件事——前者 pi-durable 已经做完了，后者还空着。

## 结构（7 节，~5000 字）

### 1. 开头钩子：它崩在 `git push` 的半路（~500 字，零导航）
- 场景：跑了一夜的 agent，最后一步在推代码，进程没了。重开之后要做的第一个决定不是"继续"，而是"**这一步到底成没成**"
- 三个坏选择摆上台面：重发 → 可能双写；当成功 → 可能丢工作；当失败去补偿 → 可能补一件没发生的事
- **作者原声（槽 1）**：那次真实事故——任务迟迟没完成，顺着执行轨迹查出来的
- 掉头：崩溃防不住。所以真正的问题不是"怎么不崩"，是"**崩了以后你到底知道什么**"
- 引出：2026-10-01 发布的 `@earendil-works/pi-durable`（experimental，规格名 Pico5，规范文本 4,747 行）；作者不打算夸它，打算把它拆开看它解决了哪一半
- ⚠️ 禁止「上一篇 / 我们知道 / 系列」开头

### 2. 真正的敌人是"不知道"（~600 字）
- **进程死了 ≠ 工具没跑**。这是两种完全不同的失败，而系统往往分不清
- 今天的 Pi 怎么处理悬空工具调用：`packages/ai/src/api/transform-messages.ts` 给没有结果的 tool call 补一条 `content: [{type:"text", text:"No result provided"}], isError: true` —— **撒谎式记账**：不记录副作用做没做，只让模型带着一个假错误继续往下走
- 四个根因（各 1–2 句）：上下文不是真相（有损/可压缩/可编辑，真相必须在日志里）；副作用不可撤销（纯函数随便重放，`git push --force` 不行）；进程不可靠但工作不该跟着死；观察者会晚到
- 落点：八条不变量里最有信息量的一条——规格第 67 行原文 **"All visible progress is durable. There is no volatile publication path."** 人话：**可见即已落盘**，不存在"先给 UI 看、稍后再存"
- 配图：`01-crash-point.png`（脚本画：崩溃点两分叉 —— 进程死了 / 效果发生了，四象限里只有两个确定）

### 3. 机关一：把意图先写下来（~800 字）
- **effect sandwich**（人话版一句话）：先提交"我打算做这件事" → 真正碰外界 → 提交结果或下一相位
- 支点：**重开时停在 intent 阶段 ⇒ 副作用可能已经发生**。此时只有三种诚实做法
  1. 安全重跑（`replay: "safe"`）
  2. 轮询外部句柄（deferred provider 就是一个"带 handle + 下次轮询时间"的持久相位）
  3. 记录中断（给模型一个 `interrupted` 结果，把不确定如实交出去）
- **`replay` 声明**：`readonly replay?: "safe" | "unsafe"`，**省略即 unsafe**——工具作者必须显式回答"重跑安全吗"，框架不替所有工具做同一个错误假设
- ⚠️ 必须写准的细节（已核源码/规格 §7）：重跑要**双向** safe——存储里记的意图策略 **AND** 当前代码的声明；当前 `unsafe` 可否决存储 `safe`，当前 `safe` 不能升级存储 `unsafe`；工具解析不到 = unsafe
- `interrupted` 结果带上**已持久化的部分输出** → 跑了 10 分钟的前半段不白干
- ⚠️ **落点必须是张力不是吹捧**：把不确定如实交给模型是“诚实”的，但诚实要付费——（**作者原声，槽 3**）不确定输入会让模型困惑、推高幻觉，结果要么任务失败，要么花更多轮次反复验证来找补。所以“诚实”只解决了“不撒谎”，没解决“模型拿它没办法”——后者的答案在第 6 节
- **memo（首写胜）**：补"效果已发生但 checkpoint 没写成"的窗口。规格自带的例子：打印 tick 2 之后立刻关掉 harness，重开后 tick 2 不会被打印第二次
- **`requestId`**：submit 幂等，客户端崩后重投拿到的是**同一个 submission**
- 配图：`02-effect-sandwich.png`（脚本画：三段 + 崩溃点落在中段的三种出口）
- **作者原声（槽 3）**

### 4. 机关二：任务状态机和所有权树（~1000 字）
- 一切皆 task：每次模型请求、每次工具调用、每次压缩都是 task，每个 task 每步都存 checkpoint
- **FSM**：`pending → running → waiting → completing → terminal`；abort 沿所有权自底向上
- **`waiting` 不跑代码**，只提交 `{status:"waiting", checkpoint, on, policy}` —— 因为**进程会死，promise 不会活过来**；`failFast` 在下一次 reconcile commit 里派生 abort
- **`completing` hold**：结果已定，但必须等它拥有的子工作收尾才算 terminal
- **"returning without durable progress faults the task"**：相位必须提交新 checkpoint 或终态，否则 faulted → 把"进程内挂死"从事故变成契约违规
- **owner 树**：`conversation` 或 `task`。abort mark 是**持久意图**，中间再崩也不丢（重新打开时重新派生）；补偿写在**做事的那一层**（规格原文 "Compensate at the level that did the effect"）
- **`close()` ≠ abort**：close 停止所有调用但**保留工作**，重开继续；只有 abort 是持久取消
- **主例：官方公告的 checkout + 多卡支付 + 退款**（转成中文叙述 + 流程图，不放长代码）：拆卡同时扣款 → 一张被拒 → 其余 abort 并各自退款；`payment-${task.id}` 当幂等键；父任务用 `{status:"waiting", on:[...], policy:"failFast"}`
- **回扣 §1**（**作者原声，槽 4**）：那次孤儿写者如果有 owner 树 + 持久 abort mark，父 run 结束那一刻就被级联撤掉，不用等人去查轨迹——但反过来，我现在实际用的还是土办法：**物理隔离 + 浪费磁盘 + 操作系统层面的文件锁**，因为机制没完全到位之前，物理边界比逻辑承诺更可靠；而真正的目标其实是那句“降低用户的心智负担”
- 配图：`03-task-fsm.png`（脚本画：五态状态机 + 自底向上 abort）、`04-ownership-tree.png`（脚本画：会话/任务/子代理三层归属树 + 级联方向）

### 5. 机关三：把"能丢什么"写进契契约（~700 字）
- 提交节拍：`settings.progress.outputIntervalMs` **默认 100 ms**（远端存储建议 500 ms）→ 崩溃最多丢这一窗可见进度
- 存储分级（已核代码 `storage/sqlite/node.ts:190-191`）：SQLite `PRAGMA journal_mode = WAL` + `PRAGMA synchronous = NORMAL` → **进程崩溃可活，断电可能丢最新一次提交**；JSONL 的 `{ fsync: true }` 才在每个 commit marker 前 flush sidecar，默认 false
- **失败二分**（本篇最"工程正确"的一处）：`StorageRejected`（确定没提交，可回滚继续）vs **不确定的存储失败 = 致命**（什么也不发布，必须 close + reopen）—— 宁可停，不可半真半假
- torn-tail 修复：JSONL 打开时截断未确认的尾部，缺必需数据 = 损坏
- 单写者：**一个进程独占一份 storage，没有跨进程锁**（非目标：无 CRDT、无离线多写合并、无自动 checkpoint 启发式）
- 落点：它承认“分布式系统里最难的是不知道对方做没做”，并把它从**静默腐坏**升级为**显式故障**
- **但取舍没有银弹**（**作者原声，槽 5**）：传统数据库设计也没在这个点上取得共识，可靠性/可用性在分布式面前就是要权衡；**模型调用便宜、时间成本不高，事后探测重试未尝不可；反之就要上更安全的方案**。这一句把 §5 从“参数罗列”变成“按场景选档”
- 配图：`05-loss-budget.png`（脚本画：能丢什么对照表 —— 100ms / NORMAL / fsync）
- **作者原声（槽 5）**

### 6. 最后一公里：它只做了一半（~1300 字，主论点）
- 先给它的成绩：任务级 **exactly-once 记录** + **at-least-once 执行**；第三方实测（issue #10386 原文）**45 次强制 SIGKILL 恢复（15 次 × 3 角色）、0 个重复完成的工具步骤、每步 1.8–2.9 ms SQLite 开销**
- **它挡住的**：崩溃重放型重复——进程死了重跑，靠 `replay` + memo + 确定性 ID + `requestId` 去重
- **它挡不住的**：模型重新规划型重复——`interrupted` 只是把不确定告诉模型；模型下一轮完全可能**重新发起同一个动作**（另起一个新的 generation、一个新的 `toolCallId`），框架不去重
- **还有一类它同样不管**（**作者原声，槽 6**）：两个子 agent 都认为自己需要做同一件事，改了同一份文件，直到合并才发现冲突——两个独立任务各自都在做“正确”的事，合起来不尽然。论文把这一类叫 **A7（并发）**，并给出一个很重的判据：**可交换性必须声明在资源上**（不能由给单个 agent 的规则表达），而 pi-durable 只有环境 `id` + 路径级的文件改动串行化，没有资源级的可交换性声明
- **坐标一：论文**。arXiv 2609.15397（Trofimov & Novikov，2026-09-14）——8 类异常（A1 重发 / A2 提交 / A3 补偿 / A4 存活 / A5 时机 / A6 依赖 / A7 并发 / A8 观察者）+ 三契约族 + **四条黑盒极限**（挑两条讲透：①没有"权威结果"原语，就不可能既解决歧义调用又保证 unknown-safe/compensation-safe；②跨多个不同工具的不可逆效果，**无法在工具层之上原子释放**）。论文自己的结论：*更好的 replay 与恢复本身并不闭合这个缺口，缺的是工具边界的契约层*
- **坐标二：普查数据**。官方 MCP registry 快照 **98,291 个工具 / 4,838 个 server**，只做 `tools/list`：`destructiveHint` 设在 65.8% 的工具上，但只有 **12.9%** 是有意义分类，真正断言破坏性操作的只有 **3.1%**；**幂等只有 hint，没有 key**
- **坐标三：MCP 官方自己说的**。官方博客（2026-03-16）："Hints inform decisions; contracts enforce them. **If a proposal's value depends on the annotation being true, it's asking for a contract，而 contract 该在授权层、传输层或运行时**，不在 ToolAnnotations"；并且"不可信的 server 可以撒谎"
- **坐标四：支付协议的镜子**。AP2 的 mandate 是**签名意图**，而签名不解决"这份意图有没有被行使过"——"Consumption is runtime state"。类比一句话：**`replay: "safe"` 的问题是"声明 ≠ 幂等"**
- **真正的缺口**：pi-durable 有 task id / entry id / `requestId`，但**外部效果的键实质是模型 mint 的 `toolCallId`**；正确做法是编排层派生 `(agent_run_id, step_id, tool_name, business_scope)`，其中 `step_id` 是**逻辑步骤**（同一件事的两次重规划折叠成同一个 step），**不能**用模型给的工具参数做哈希
- **补法按性价比**（四条，各一句代价）：① 框架注入编排派生键（需"逻辑步骤"概念）② `replay` 二分类扩成效果类 `read-only / bufferable / reversible-costly / irreversible-gated / idempotent-known-outcome`（需要工具被切成"执行"与"释放"两段，很多工具没有这道缝）③ 补偿契约化，结果标 `clean / leaked / unresolved`（abort handler 复杂度上升）④ 回执与对账 `reconcile()`（要服务侧配合）
- **为什么这一格空着（本节收口，作者原声槽 7）**：不是没人想到，是**没人站在能定义它的位置上**——模型自己没有一个一致性很高的心智（本质上就是个无状态的大金鱼）；工具作者不可能知道，除非你用的不是通用工具而是领域特化的 app；用户和业务方确实知道，但他们可能根本没直接和 agent 打过交道
- 配图：`06-two-duplicates.png`（脚本画：崩溃重放型重复 vs 模型重新规划型重复 —— 前者被挡住，后者漏出去）
- **作者原声（槽 6、槽 7）**

### 7. 它故意不解决的，以及这篇的落点（~600 字）
- 非目标清单（规格 §13）：外部效果不能回滚 / 非协作扩展无法强杀 / 单写者 / 无 CRDT / **进程内计时器**（退避 sleep 与 deferred poll 的等待仍是内存计时器 → serverless 上等待直接变账单）/ 嵌套工具调用崩溃语义未定义
- 现状（**2026-10-09 核过：六个 issue 全部仍 OPEN**）：等待环会死锁而不是被拒绝（#10411 / #10533）/ 重试退避没作为任务状态提交（#10535）/ 宿主无法知道 harness"只是在睡"（#10325）/ 嵌套工具执行无受支持路径（#10455）/ **扩展 API 未对齐（#10386）**→ 所以真身 Pi 至今还跑在老 JSONL 会话上
- 反差坐标：Temporal Agent Harness（2026-08-20）、Restate、Cloudflare Workflows 那一派走的是**工作流引擎**路线（把 agent 塞进既有 durable execution 引擎）；pi-durable 走的是 **harness 原生**路线。两条路的差别是"谁决定什么是可重放的"
- 收尾三句：durable 不是加个重试，是失败之后仍然让系统知道自己在哪 / 它把"我不知道"变成了可提交状态，这一步已经做完 / "知道自己在哪"和"世界没有重复"是两件事，后者还空着
- **作者原声（槽 8 类比 + 槽 9 互动问）**
- 关注引导（价值承诺 + 本号定位）+ 合集导航 + 热门文章 + 参考资料 + 话题标签

## 配图（7 张；数字/结构图脚本画，AI 图禁承载数字）

1. `00-cover.png` — 21:9 封面（AI 概念图无字底 + 叠金字标题，逐字 = 定稿标题）
2. `01-crash-point.png` — 脚本画：崩溃点四象限（进程死了 × 效果发生了）
3. `02-effect-sandwich.png` — 脚本画：intent → effect → outcome + 停在 intent 的三种出口
4. `03-task-fsm.png` — 脚本画：五态状态机 + 自底向上 abort
5. `04-ownership-tree.png` — 脚本画：会话/任务/子代理所有权树 + 级联方向 + `completing` hold
6. `05-loss-budget.png` — 脚本画：能丢什么对照表（100ms / WAL+NORMAL / fsync）
7. `06-two-duplicates.png` — 脚本画：两类重复对照（崩溃重放型被挡 / 重新规划型漏出）
- ⚠️ AI 图禁止承载数字与文字；数字一律走脚本画图；封面文字必须与定稿标题逐字一致

## 事实与数字红线（成稿自查，均 2026-10-09 核过）

1. **`replay` 取值是 `"safe" | "unsafe"`，省略即 unsafe** —— ⚠️ 素材写的是 `"never"`，**错的**，不得沿用；重跑需"存储策略 AND 当前声明"双向 safe（规格 §7）
2. **`@earendil-works/pi-durable` 1.1.0 / 2026-10-07 发布；1.0.0 首发 2026-10-01；experimental**（npm 实时核；README 首行原文 "Experimental. The API changes without notice between releases."）
3. **规格名 Pico5，`docs/spec.md` 4,747 行**（实时核；不写"规范书"以外的定性）
4. **pi-agent-core 1.0.0（2026-10-01）Breaking Changes 原文**（CHANGELOG 实时核）：删掉 `AgentHarness`、sessions/session storage、durable runtime、pico3 等，并写明 "Use `@earendil-works/pi-durable` for durable sessions." —— 引用时必须给日期
5. **不变量原文**：`All visible progress is durable. There is no volatile publication path.`（spec.md 第 67 行，逐字引用）
6. **100 ms 默认**：`settings.progress.outputIntervalMs`（spec.md §"progress"，原文 default 100 ms；远端存储建议 500 ms）
7. **SQLite 参数**：`PRAGMA journal_mode = WAL` + `PRAGMA synchronous = NORMAL`（`packages/durable/src/storage/sqlite/node.ts:190-191` 实时核）；JSONL `fsync` 选项**默认 false**（`storage/jsonl/storage.ts:77-78`）。⚠️ 不得写成"SQLite 保证断电不丢"
8. **悬空工具调用的现状**：`packages/ai/src/api/transform-messages.ts:175` 合成 `No result provided` + `isError: true`（实时核）；描述时用"启发式修补/撒谎式记账"，不得写成"pi 会重试"
9. **第三方实测数字**（issue #10386 原文，署名口径写"有团队在 issue 里报告"）：45 次强制 SIGKILL 恢复（15 × 3 角色）、0 个重复完成的工具步骤、1.8–2.9 ms/step
10. **论文**：arXiv 2609.15397，Artem Trofimov & Boris Novikov，2026-09-14，标题《When Tool Calls Succeed but Workflows Fail: Anomalies at the Agent–Tool Boundary》
11. **普查数字**（论文 §5，arXiv HTML 实时命中）：98,291 tools / 4,838 servers / 65.8% / 12.9% / 3.1%。⚠️ 口径必须写"只做 `tools/list`、不调用任何工具"，不得扩写成"98,291 个工具都不安全"
12. **MCP 官方博客**：2026-03-16《Tool Annotations as Risk Vocabulary》；引文 "Hints inform decisions; contracts enforce them." 为原文口径
13. **AP2**：Mandate + Receipt、`vct` 版本后缀为规范口径；"签名证明意图有效、不证明意图只被行使一次"属 runcycles 分析观点，须标"有分析指出"
14. **六个 issue 状态**：2026-10-09 实测**全部仍 OPEN**（#10411 / #10533 / #10535 / #10325 / #10455 / #10386）；⚠️ **不得写成"已修复"或"即将修复"**
15. **源码规模**：官方公告原文"the entire source code, without tests, is about 15,000 lines"（约等于 150k token @GPT / 250k @Claude）——引用注明来自官方公告，不当成本号实测
16. **年份一律写全 2026**；所有版本号/日期不得凭记忆
17. **不编造**：不虚构延迟、成本、提升百分比的任何数字；官方未给的一律不写
18. **批判红线**：只批评"缺口/未对齐"，不写"pi durable 是骗局/没用"这类结论；`replay` 的问题措辞保持"声明 ≠ 幂等"
19. **不带项目细节**：作者亲历只保留"任务迟迟没完成 → 顺着执行轨迹查出来"，不得出现项目名/仓库名/内部代号

## 尾部

- 系列导航：**[AI Agent 工程] 合集链接**（`https://mp.weixin.qq.com/mp/appmsgalbum?__biz=MzkyMzQyODExNQ==&action=getalbum&album_id=4680422529625325570#wechat_redirect`）+ 箭头链：给 Agent 装了记忆 → 多智能体路线之争 → **本篇**
- 🔥 热门文章块由 `scripts/hot_articles.py --md --cited content/2026-10-09-pi-durable/weixin.md` 生成（行尾两空格、行间不留空行），发布前 `--self-check`
- 话题标签 5 个（暂定）：#Pi #DurableExecution #Agent工程 #崩溃恢复 #数解AI
- 参考资料（带日期）：earendil 官方公告 2026-10-01 / 规格 `docs/spec.md` / issue #10386（第三方实测）与 #10411、#10325、#10535、#10455 / arXiv 2609.15397（2026-09-14）/ MCP 官方博客 2026-03-16 / AP2 规范
- 末尾开放式问题（作者原声）+ 点赞/收藏/关注引导

## 作者原声槽

原声进稿：9 / 下限 5（9 个候选槽全部走完：1 沿用 + 8 已填）

### 槽 1 · 第 1 节「掉头」之后
- 状态：沿用
- 类型：亲历
- 原句：后面发现任务迟迟没有完成，仔细查看agent执行轨迹才发现这个问题。
- 备注：来自 2026-10-09 grill 对话（作者原话，逐字进稿）

### 槽 2 · 第 2 节「撒谎式记账」之后
- 状态：已填
- 类型：吐槽 / 判断
- 原句：很多时候，我不得不提醒自己这个有点反常的事实：对于没有实际产生任何结果的工具调用，agent不得不自己给模型创造一条实际上不存在的错误，阅读和排查agent运行轨迹的时候，不需要对这种行为大惊小怪。

### 槽 3 · 第 3 节 `interrupted` 结果之后
- 状态：已填
- 类型：判断
- 原句：其实不确定性的东西交给模型作为输入，更容易让模型对不确定的输入产生困惑，进而推高幻觉，导致要么任务执行失败，要么后续需要花费更多轮次的反复验证来找补。
- 备注：⚠️ 作者这句是对 §3 落点的**反向压力**——成稿时 §3 不得把“把不确定交给模型”写成免费好处，必须写成“诚实但付费”的张力（代价：推高幻觉 / 多轮找补），并把重量交给 §6 的编排派生键

### 槽 4 · 第 4 节「回扣开头」处
- 状态：已填
- 类型：亲历 / 判断
- 原句：其实在agent没有进化出来更好的机制之前，我还是更信赖物理层面的隔离那种看起来很土鳖的方案，浪费一点磁盘空间，施加一些操作系统层面的文件锁来避免并发踩踏，但是主观上我还是希望agent的设计可以更好地处理这种情况，降低用户的心智负担。
- 备注：⚠️ 这句是全文一个真实立场的来源——成稿时 §4 回扣段用它收口（机制能救什么 vs 我现在实际怎么防），§7 再用一句话回扣“物理隔离仍是兜底”，但**不重复引用**

### 槽 5 · 第 5 节「能丢什么」之后
- 状态：已填
- 类型：判断
- 原句：其实我觉得这种取舍并没有一种放之四海皆准的套路，还是要看具体任务的场景，毕竟这是传统数据库设计也没有取得共识的地方，可靠性、可用性在分布式设计面前本身就必须要权衡。如果模型调用非常便宜，时间成本也不高，那么事后探测重试，也未尝不可。反之，就需要更安全的方案了。

### 槽 6 · 第 6 节「挡不住的重复」之后
- 状态：已填
- 类型：亲历 / 判断
- 原句：有时候两个子agent都觉得自己需要做同一件事，进而改动了同一份文件，最后到了需要合并的时候，才发现产生了冲突，此时虽然两个独立任务都认为自己在做正确的事，合在一起就不尽然了。

### 槽 7 · 第 6 节「编排派生键」之后
- 状态：已填
- 类型：判断
- 原句：这个边界的界定很多时候就比较麻烦了，模型自己很多时候并没有一个一致性很高的心智 - 本质上它完全是无状态的大金鱼，agent工具的作者自然是不可能知道除非你使用的agent不是一个通用的工具而是一个领域特化的app, 用户和业务方显然是知道的，但是他们可能根本就没有直接和agent打交道。

### 槽 8 · 第 7 节收尾
- 状态：已填
- 类型：类比
- 原句：durable的名字看起来很抽象，其实它就是一个账本，里面可靠地记录着所有的任务情况，具有良好的结构信息，可以让agent随时来翻阅决定如何调度各种工具以及如何与底层的LLM模型通信将目标持续往前推进。
- 备注：成稿收尾用它接最后一刀——账本记的是“我知道什么”，不是“世界发生了什么”

### 槽 9 · 文末开放式问题
- 状态：已填
- 类型：结尾互动问
- 原句：你觉得这个Durable机制的设计能解决你平时遇到的痛点吗

## 检查清单

- [x] 作者原声槽已填且进稿 ≥5（9/5，槽 1–9 全部归档）
- [x] 机器可查项全过（`quality_check.py` PASS：原声 9/9 逐字、禁词零、AI 腔零、无超 60 字 AI 句、字数、开头白盒、尾部互动杠杆、图片同级）
- [x] 事实与数字红线逐条核过（`replay` = safe/unsafe 已纠错；spec 4,747 行；issue 六个全 OPEN）
- [x] 8-25 老文强隔离核过（intent/effect/outcome 一笔带过，未重讲）
- [x] 翻译腔专项三连改（翻译腔扫描零命中；「拆」字三处逐处判过）
- [x] 封面生成（**无字纯图**，作者 2026-10-09 口径：不再嵌标题；实际输出 1916×821 = 2.33:1，落在 21:9 无需裁剪）
- [x] 正文 9 张图（6–9 号概念图 + 01–05 号结构图，全部插入）：`01-crash-point` / `02-effect-sandwich` / `03-task-fsm` / `04-ownership-tree` / `05-two-duplicates`（脚本画，深色终端底）+ `06-sent-letter` / `07-two-keys` / `08-stamp` / `09-ledger`（AI 概念图，深色电影感 + 金色主光）
- [x] **手机可读性修正**（`scripts/wechat_readability.py`，七条规则全命中）：字号 16→17px；容器行高 1.75→1.85；段落间距 1.5em→1.7em；**列表左缩进 1.5em→0（修掉参考文献左侧空白）**；列表项间距 0.5→0.65em；代码块 `overflow-x:auto`→`pre-wrap + break-all`（手机不横滚）；代码块底色 `#fff`→`#f6f8fa`
- [x] 话题标签 5 个（#Pi #DurableExecution #Agent工程 #崩溃恢复 #数解AI）
- [x] **手机可读性修正（改在 mdnice 管线内，2026-10-09）**：在 `.agents/skills/baoyu-post-to-wechat/scripts/md-to-wechat.ts` 新增 `relaxWechatReadability()`（接在 `compactWechatLayout` 之后）：正文 15→16px、行高 1.75→1.85、段间距 10→14px、**`ol/ul` 左缩进 25px→0（修掉参考文献左侧空白）**、`li` 补 4px、代码块 `overflow-x:auto`→`pre-wrap + break-all`（手机不横滚，同时保住缩进）、代码 12→13px。八条正则全命中、旧值零残留。
- [x] ⚠️ **流程纠错**：首次存稿误把 md 预渲染成 HTML（`baoyu-markdown-to-html` 的 grace 主题）再发布，**绕过了 mdnice**；已改为交 `weixin.md` 重发。已写入 `docs/pre-publish-final-check.md` 第 11 项。
- [x] 存公众号草稿箱（**mdnice 版**，`draft/add`）：media_id `kOcXH4SytIYVIpYksTGfHq5xsqSfxgP5PpQYvgnlfS2zuq-EQamZxvRkxVnPGC9v`；封面 thumb `kOcXH4SytIYVIpYksTGfHjukOM1eWZUtPW6Yy2gu4Ot_acqpiCXFQ3JVHtFt5_lT`
- [ ] ⚠️ **待作者手动删除错主题旧稿**：media_id `kOcXH4SytIYVIpYksTGfHrvZeWBdS8gguQdBi0SBQfSa_EKK52F39ITbD_ywewWI`（后台草稿箱删除；skill 无 draft/delete 封装）
- [ ] 发布回填 `wechatUrl` + 数据台账
