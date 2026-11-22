# 成稿后：AI 味并行审查与自动改写循环（2026-11-15 起）

## 为什么有这一阶段

首版 `weixin.md`（无论哪支路）AI 味太重是当前最大痛点：讲师腔、塑料翻译腔、句长匀速、中英混杂，`article-reviewer` 的第 15/18 项只是终线复核、修一轮就进作者门禁，压不干净。本阶段是**去 AI 味第一线**：`weixin.md` 初版落盘后、派 `article-reviewer` 之前，跑一个**审查 → 改写 → 复检的循环**，直到 findings 收敛（或达到轮次上限交作者）。

## 边界：治什么，不治什么

| 治（本阶段） | 不治（归其他阶段） |
|---|---|
| 结构转折：总分总/每段小结/排比段/断点/功能标签过渡 | 事实/数字/版本号核实（阶段 2） |
| 词汇：塑料翻译腔、AI 讲师腔、公文黑话 | 封面/配图（阶段 3/6） |
| 节奏：句长匀速、模板段、长句链（对照作者 profile） | 原声句本身（**禁改**，只标） |
| 表达：中英混杂、术语裸奔、欧化长定语、错别字 | 发布不变量（`article-reviewer` / `quality_check.py`） |

**原声红线**：`【作者填入】` 占位符、`quality_check.json` 的 `slots`、`draft.md` 全文（手写稿分支）——审查 lane 只标不改，改写 lane 逐字保留，机械门禁兜底核。去 AI 味是去掉讲师腔，**不是把稿子改成另一个人**（`style-features.md` 红线）。

## 触发时机（三支路统一）

`weixin.md` 初版落盘 + `hot_articles.py` 替换 `<!-- HOT_ARTICLES -->` 占位行 + `quality_check.json` 写好之后，**派 `article-reviewer` 之前**。手写稿分支 = 阶段 1 完成处；自动成稿 = 大纲成稿回传落盘后；素材直出 = `structure.md` 获批出初版后。

## 循环状态机（orchestrator = main agent 视角）

```
R0（一次性）：python3 scripts/style_profile.py --include-published \
              --exclude content/<当前目录> > .grill/<slug>-style-profile.txt
current = content/<日期>-<slug>/weixin.md（初版）
round = 1
loop:
  findings_N = 并发派 4 个只读 lane 审 current（round≥2 时内联上一轮 findings 要求复核）
  合并落盘 .grill/<slug>-aiflavor-round{N}.md，提取 FAIL 清单
  if FAIL 为空 and 上轮 FAIL 全部「已解决」: break        # 收敛
  if round == MAX_ROUNDS（默认 3）: 记「未收敛」，break   # 剩余 FAIL 交作者拍板
  cp current .grill/<slug>-weixin-pre-aiflavor-r{N}.md   # 备份
  派 ai-flavor-rewriter（current 全文 + FAIL 全量 + WARN + 上轮改写报告 + profile + 原声边界）
  current = 回传代码块全文（覆盖写 weixin.md）
  gate = python3 scripts/ai_flavor_gate.py <pre 备份> current --dir content/<目录>
  if gate 有 FAIL: 把 GATE 项并入下一轮 findings（作为必改项）
  round += 1
写 .grill/<slug>-aiflavor.md 收敛总结（各轮 findings + 最终状态 + 未决项）
→ 才派 article-reviewer
```

**收敛定义**：一轮四 lane 全部报告「上轮 FAIL 已解决」且无新 FAIL。WARN 不阻塞收敛；但**同一 WARN 被同一 lane 连续两轮重复标出 → 升级为 FAIL** 进下一轮（防无限循环）。

**轮次上限**：默认 3（作者口头可调：「再改一轮」→ 放到 4）。到上限仍有 FAIL → 循环退出记「未收敛」，剩余清单进 `.grill/<slug>-aiflavor.md`，作者编辑门禁时交给作者看，由作者拍板。

## 每轮派发：4 个并行只读 lane

一条 `subagent({ workflow: "parallel", args: { tasks: [...] } })` 并发派 4 个命名 agent；等全部完成通知，禁轮询。Paseo 会话按 AGENTS.md 路由表派（只读审查走「只读调查」行：免费档并发 4 OK，CMD 档先跑 `~/.local/bin/cmd-window-check`；改写 lane 走 coding 档），任务书照用本规。

| lane | agent 定义 | 维度 | 关键判据 | id 前缀 |
|---|---|---|---|---|
| 结构转折 | `.agents/agents/ai-flavor-structure.md` | 遮标题通读、AI 骨架、过渡质量、钩子连贯 | 断点/总分总/每段小结/排比段/首先其次最后骨架 | `S-` |
| 塑料翻译腔词汇 | `.agents/agents/ai-flavor-lexicon.md` | 讲师腔/动词名词化/被动泛滥/介宾套娃/公文黑话 | 逐处口语替换建议；口头禅禁删 | `L-` |
| 句式长短套路 | `.agents/agents/ai-flavor-rhythm.md` | 对照作者 profile 量句长序列 | 匀速句/模板段/长句链/一句一段新闻腔 | `R-` |
| 中英混杂与表达 | `.agents/agents/ai-flavor-language.md` | 英文使用审计、欧化中文、标点格式、错别字 | 术语裸奔/不必要混杂/叠字 typo/项目禁词 | `G-` |

每个 lane 的 task 必给：`审查 content/<日期>-<slug>；第 N 轮`、分支与原声边界、**style profile 全文**（R0 产物，四 lane 用同一把尺）、上一轮 findings 汇总（N≥2）。round≥2 时 lane 必须逐条复核上轮 findings 并标「已解决 / 未解决 / 部分解决」+ 当前文本证据。

派发示例（照抄改路径即可）：

```js
subagent({ workflow: "parallel", args: { tasks: [
  { agent: "ai-flavor-structure", task: "审查 content/2026-11-20-memory-curse；第 1 轮。分支 auto；原声边界：quality_check.json 的 slots + 【作者填入】占位符（共 7 处）。作者风格 profile：<R0 产物全文>。首轮无上一轮 findings。" },
  { agent: "ai-flavor-lexicon",  task: "同上（lane 任务书一致，维度=塑料翻译腔词汇）" },
  { agent: "ai-flavor-rhythm",   task: "同上（lane 任务书一致，维度=句式长短套路，对照 profile）" },
  { agent: "ai-flavor-language", task: "同上（lane 任务书一致，维度=中英混杂与表达卫生）" },
]}})
```

改写 lane 串行单派（`async: true` + 完成通知）：

```js
subagent({ agent: "ai-flavor-rewriter", task: "改写 content/2026-11-20-memory-curse；第 1 轮。分支 auto。当前版 weixin.md 全文：<全文>。本轮 findings（FAIL 必改，WARN 可改）：<四 lane 汇总>。上轮改写报告：无（首轮）。作者风格 profile：<全文>。原声边界：slots 清单 + 【作者填入】×7。" })
```

**lane 失败处理**：空回传/超时 → `subagent({ action: "resume", id, message })` 重派一次；仍失败 → 记「本项第 N 轮未审」进汇总，不阻塞循环，终局由 `article-reviewer` 兜底。

## 改写：ai-flavor-rewriter（零工具纯文本 lane）

`.agents/agents/ai-flavor-rewriter.md`（`gemini-web/gemini-auto` + thinking `medium`，与 `weixin-writer` 同模式）。task 全内联：当前 `weixin.md` 全文、本轮 FAIL 全量 + WARN、上轮改写报告（防翻烧饼）、style profile、原声边界。回传一个 markdown 代码块（改写后全文）+ 改动报告（每条对应 finding id；未改项 + 原因）。

硬约束（详见 agent 定义）：只改 findings 指向的位置；原声逐字；禁新增事实/数字；禁动 frontmatter、公式、图片占位、内链 URL、`<!-- HOT_ARTICLES -->` 占位行；结构规矩不变（`##` ≥5、段落 300–600、开头禁标题开场）。

## 机械门禁：scripts/ai_flavor_gate.py

orchestrator 每轮改写落盘后跑（这是 orchestrator 唯一被允许做的「检查」——跑脚本，不做文字判断）：

```
python3 scripts/ai_flavor_gate.py .grill/<slug>-weixin-pre-aiflavor-rN.md content/<目录>/weixin.md --dir content/<目录>
```

11 项：frontmatter 未变 / 占位符数量 / 图片集合 / 公式数量 / URL 集合 / HOT_ARTICLES 占位行 / 原声未被破坏（slots ≥0.9 绝对；draft 段不降 >5% 相对）/ CJK 字数变化 ≤15% / 硬 AI 味词零新增 / `##` ≥5 / 首段非标题。**FAIL 项原样作为下一轮 findings 交回改写 lane**（输出里已生成 `| GATE-n | FAIL | … |` 行，直抄）。

## orchestrator 纪律（硬约束）

- **禁自己写/改正文任何句子；禁自己评审；禁「顺手修」**。本阶段所有文字修改只经由 `ai-flavor-rewriter`。这是 2026-11-15 作者明确要求：orchestrator 只做协调（派发、汇总、备份、跑脚本、落盘回传、决定继续/停止）。
- 只允许的动作：读文件、派发/收集 subagent、跑脚本（`style_profile.py` / `hot_articles.py` / `ai_flavor_gate.py`）、备份、把回传代码块落盘、写 `.grill/` 汇总。
- 门禁 FAIL 不当场修；lane 失败不代审。
- rewriter 连续 2 回传不达标（同 run resume 带更紧指令重试 1 次后仍不行）→ 循环退出记「未收敛」，剩余 findings 交作者，禁无限循环烧 token。

## 产物与留痕

| 文件 | 内容 |
|---|---|
| `.grill/<slug>-style-profile.txt` | 作者行文 profile（R0 一次生成，四 lane 共用） |
| `.grill/<slug>-aiflavor-roundN.md` | 第 N 轮四 lane findings 汇总（含上轮复核结论） |
| `.grill/<slug>-weixin-pre-aiflavor-rN.md` | 第 N 轮改写前备份（门禁 pre 版 + 回滚用） |
| `.grill/<slug>-aiflavor.md` | 收敛总结：各轮 FAIL 数、最终状态（收敛/未收敛+剩余清单）、门禁历史 |

## 与其他阶段的关系

- 本阶段过后才派 `article-reviewer`：其第 15 项（说人话/去 AI 味）、第 18 项（段落衔接）此时应已干净，退化为复核残留。
- 阶段 2/3（事实核查、补公式配图）若之后大改文本 → 大改后由 main agent 复跑一轮**只派 `ai-flavor-rhythm` + `ai-flavor-lexicon` 两 lane** 的快检（新表述最容易带进翻译腔和匀速感），有 FAIL 再走一轮迷你循环。
- 作者编辑门禁两轮质检、原声门禁、存草稿箱流程不变。

## 常见错误（禁止）

- orchestrator 自己动手改句子「顺手修」——所有修改必须经过 `ai-flavor-rewriter`
- 四 lane 串行派发或轮询等结果（应一条 parallel 调用并发 + 完成通知）
- 门禁 FAIL 后 orchestrator 自己补修而不并入下一轮 findings
- 改写 lane 拿到 findings 却全局洗稿（禁改 finding 没提的段落）
- 拿 profile 当硬性 KPI 把作者长句推演全拆短（profile 是基准尺，不是枷锁；原声禁拆）
- 循环超过 3 轮还不停（token 无限燃烧；未收敛就交作者）
