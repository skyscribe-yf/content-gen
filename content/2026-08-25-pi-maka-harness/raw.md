# 原始素材（话题：Pi 与 Maka 的 harness 撞车）

> 素材源：`/home/skyscribe/图片/贴图/0825`（2026-08-25 06:32–06:43）
> 类型：贴图（图片消息）｜合集：Agent 前线
> 素材为推特截图 + 对比表，以下为 AI 转述要点，正文照录时以截图原话为准。

## 素材

### 图 1（截图 06-32-01 → kabikabi 推特 @jakevin7）

标题：**Pi 的新架构和 Maka 告诉我们 harness 的答案早就在数据库论文里了！**

- Maka 的核心作者很多都是 database 背景出身的
- 当 Pi 的 harness v2 文档出来后，Maka 内部群大家直接愣住了，因为它和我们在 Maka 里做的架构几乎一致
- 一致的主链路：持久化事实 → 派生运行状态 → 派生模型上下文 → 派生 UI → 崩溃后重新归约
- 连 tool 的边界都一样：先写执行意图，再做副作用，再写结果：
  - Pi: tool_started_intent → execute → tool-result entry
  - Maka: T1 toolDispatch → execute → T2 function_response
- Pi V2 和 Maka 从各自的路径出发，最后设计出几乎一样的架构，说明了问题
- 感觉 Agent harness 这一层正在形成一些共识
- 这个共识其实就是 OS 和 db 那一套——预写日志、事件溯源、可恢复的持久化操作
- 所以工程没有银弹，当我们最后做了很多工作之后，发现核心原理还是软件工程的那些内容

### 图 2（截图 06-43-14 → 小墨同学 @xiaomovps 推特）

标题：很多人用 Pi，但未必知道背后这个人

- Pi Agent 作者 Mario Zechner，X 上 @badlogicgames，奥地利人，以前不是做 AI 的，是做游戏框架的。libGDX 就是他搞出来的，Ingress、杀戮尖塔这些都用过
- 后来做过 RoboVM，公司卖了又被微软关掉，社区反噬那一套他经历过，所以现在特别不愿意自己去融一堆钱当 CEO
- 2025 年底他自己折腾了一个极简 coding agent，两晚写出来，本来只给自己用。默认就四个工具：read、write、edit、bash，系统提示词压得很短，其他全靠你自己加。口号也写得很直：There are many agent harnesses, but this one is yours.
- 后来 Flask 作者 Armin Ronacher 的公司 Earendil 把 Pi 收了，Mario 入股并加入团队。他自己发文标题就叫 I've sold out，写得很坦率：不想再走一遍创业那套高压，家里有小孩，但又希望 Pi 能有人养着别停更。技术方向还是他拍板，核心继续开源
- 这人说话冲，bio 写的是 Old man yelling at Clauses。讨厌 Agent 越做越重、提示词越写越长。他自己还专门测过 MCP 和 CLI，结论和很多人实际感受一样：CLI 往往更省、更稳
- 所以 Pi 长成现在这样，不是产品经理推出来的功能清单，是一个老开源作者按自己脾气做的壳。你喜欢它干净、可改、不绑死模型，基本都能从他这个人身上对上号
- 感兴趣可以看他博客 mariozechner.at，产品号是 @pidotdev

### 图 3（pi-versiondiff.png → Pi v3 vs Harness v2 核心维度对比表）

| 维度 | 上一代（v3 / Legacy Loop） | 全新一代（Harness v2） |
|---|---|---|
| 核心定位 | 线性流式执行器（Linear Chat/Tool Loop） | 确定性状态机与多泳道 Agent 虚拟机 |
| 会话数据结构 | 扁平/弱结构 JSONL 文件（消息流水账） | 四大解耦模型（被动共享树 Tree + 泳道 Lanes + 操作日志 Op Log + 全局事实 Facts） |
| 并发能力 | 单会话单线程（Busy 期间锁死或生硬排队） | 多泳道并发（Lanes）（同一 Session 树上可开辟多个并发工作分支） |
| 崩溃与断电恢复 | 尽力而为（Best-effort），断电易产生半成品脏数据、孤儿 Tool Call | 绝对韧性（Durable Runs，Intent-First 预分配 ID，数学级零半成品（No Partial Outcomes）） |
| 打断与排队 | 粗暴中止（可能导致上下文残缺或死锁） | 三队列分流（steer / followUp / nextRun）+ Checkpoint 检查点机制 + 合成结果对齐 |
| Token 成本记账 | 成本附着在最终成功消息上（失败/重试丢 Token 统计） | 独立成本账本（UsageRecord），物理请求一发生即记账，与结果是否丢弃完全解耦 |
| KV Cache 保护 | 随时向上下文插入系统状态，频繁破坏缓存前缀 | Append-Only 上下文铁律，中途变更全部进入 Deferred Writes，仅在 Tail 追加 |
| 测试与调试 | 异步黑盒集成测试，难以精准复现断电态 | 确定性单步模式（Manual Drive），每个副作用边界前可精准挂起（Park）单步执行 |

## 事实核查（2026-08-25）

- Mario Zechner 身份 / libGDX / RoboVM 经历：推特截图口径，业界可检索
- Earendil 收购 Pi、Armin Ronacher 为 Flask 作者：截图口径，待作者确认（联网检索未执行成功）
- Pi Harness v2 各维度描述：来自对比表照录，正文不另估
- 截图内容与正文一致，数字/术语（tool_started_intent、Durable Runs、Append-Only 等）照录
