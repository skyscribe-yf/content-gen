# 原始素材（话题：Pi 锐评 DSH 剪枝）

> 素材源：`/home/skyscribe/图片/贴图/0824`（2026-08-24 06:39–06:43）
> 类型：贴图（图片消息）｜合集：Agent 前线

## 素材

### 图 1（06-42-17 → 01-pi-roast-dsh.png）

Max For AI @MaxForAI · Aug 22：Pi 新开发笔记锐评其他家 Agent。
- 问题从「谁多几个 Tool」变成：Agent 连续跑 50 小时还知道自己干过什么吗
- 先点 DSH：tool result pruner 留头留尾、中间裁掉 = permanently-lossy
- 3 万字符日志、报错在第 12000 字符，压缩后消失
- Pi：prune + spill，完整结果落盘，Context 留路径和 offset
- GLM-5.3 + DeepSeek V4 Flash，19 个真实 Session：Context 降 26%～35%，uncached prefill 降 72%～88%
- PR 原文：strictly better than dsh's permanently-lossy pruner

### 图 2（06-42-47 → 02-claude-bind.png）

- 新一代 Claude 在第三方 Harness 上更容易把 Tool 调错
- 生成 requireUnique、matchCase、oldText2 等 Pi 没有的参数
- 猜测：后训练越来越适配 Claude Code 自己的 Tool Schema
- Claude + Claude Code、DeepSeek + DSH、GPT + Codex 逐渐变成整体
- Pi 把一次 Agent Run 当接近数据库事务：先写 intent，执行完再写结果；崩溃后要知道 Tool 有没有执行过
- Session Tree / 运行状态 / Lane / Operation Log 分开保存；进程死在 Tool 半路有 recovery

### 图 3（06-43-10 → 03-harness-os.png）

- 以前：while loop + 模型 + 几个 Tool，Context 满了就总结，祈祷别挂
- 跑几小时、几天后变成操作系统和数据库问题
- DSH Cordis「一切皆插件」走得很远；Pi 开始强调 Conversation / Runtime / UI / Extension 边界
- OpenCode、Claude Code、DSH、Pi 看着都是 Coding Agent，底层开始走不同路线
- 收束：Harness 开始越来越像 AI 时代的操作系统

### 图 4（06-39-52 → 04-cordis-effect.png）

子茄 @ant_sz：读 DSH Cordis
- Effect：对环境的操作，要带 undo，unload 可 revert（像 sagas）
- Coeffect：运行依赖的环境，提前声明，依赖图动态管理激活
- 不能完全消除外部调用的副作用
- PL 和 DB 都在解决副作用和状态一致性；现阶段大多 agent 不需要 0 downtime，88 页论文有点 overkill

## 事实核对（2026-08-24）

- GLM-5.3：2026-08 已发布（截图口径，OpenRouter / 行业报道可检索）
- DeepSeek V4 Flash：已发布，截图与正文统一写 V4 Flash
- 26%～35%、72%～88%、19 Session、12000 / 3 万字符：来自截图转述的 Pi 笔记，正文照录，不另估
