# 文章写作流程（硬性门禁）

## 规则

每次开始起草文章大纲之前，**必须先调用 grill-me skill 与作者进行深入讨论**，讨论收敛后才能起笔撰写。禁止跳过 grill-me 直接起草大纲或正文。

Skill 位置：[`.agents/skills/grill-me/SKILL.md`](.agents/skills/grill-me/SKILL.md)

自动成稿在写出 `outline.md` 之后、动笔 `weixin.md` 之前，**大纲末尾必须列作者原声槽（全部占位符）**；AI 不等作者填直接动笔，`weixin.md` 每个槽位留 `【作者填入】`，由作者在 VS Code 自行填入；原声门禁在**发布前终检**把关（≥5 逐字在场 + 占位符清零），第一轮质检不管原声。规则见下文「作者原声槽」。

## 篇幅

正文可视字数一般 **2000 字左右**（含尾部热门区/参考资料/标签总计不超过约 2500），紧凑优先、不拉长。为凑篇幅扩写结构、重复铺垫按返工处理（2026-09-13 作者口径；此前 3.5-5k 恢复期口径废止）。

**数学篇的「深」= 推导密度，不是篇幅**（2026-09-14 作者口径，奖励函数 hack 篇确立）：字数口径不变，把「会写浅」的地方整段换成推导——只给结论不给式子的补式子，只给现象不给条件的补成立条件，只给直觉不给反例的补边界。禁止以「数学篇可以放宽到 3-4k」为由扩写。

**段落 300–600 字 + 多级标题**（2026-11-15 作者纠正，**取代 2026-10-10「≤80 字」旧规，项目级**）：**小于 300 字一般不分段**，段落长于 300 字可以、**不超过 600 字**，超过才在逻辑转折处拆；醒目句（驱动句 / 反转句 / 金句）**独立成段**；`##` 节 ≥5 个，超约 400 字的节**必补 `###` 小标题**（每节 1 个、放在真逻辑转折处，不随意增拆）。原声句不改写，但可在原句自带句读处加句号、分段（不增删字）。

**开头禁标题开场（2026-11-01 作者追加，项目级）**：正文第一段必须是钩子文本——**禁止以 `##` 标题起首，也禁止把文章标题抄成开头第一行**。第一个节标题只能出现在开头段之后。细则与自检见 [`article-quality-check.md`](article-quality-check.md) **第 17 项**；脚本参考实现 `content/2026-10-10-context-rot-isolation/quality_check.py`。

## 适用范围

- **自动成稿**（本文件后半段）：选题经 grill-me，产物是 `outline.md`，再由 `weixin-writer` 生成 `weixin.md`。套原声槽门禁。
- **素材直出**：走 [`.agents/skills/raw-material-to-wechat-draft/SKILL.md`](../.agents/skills/raw-material-to-wechat-draft/SKILL.md)，用 `raw.md` + 原声句清单。**不套**本文件的原声槽门禁。
- **手写稿直出**：走 [`.agents/skills/handwritten-draft-to-wechat/SKILL.md`](../.agents/skills/handwritten-draft-to-wechat/SKILL.md)，作者手写全文 `draft.md`——**所有要 AI 补的地方统一标「待补充」**（公式/配图/表格/前文索引/事实数据五种，冒号后说明类型；`【图样：描述】`是配图等价写法）。AI 建稿 + 开 VS Code 后静默等作者说「好了」，**收到「好了」先校验稿件非空**（正文去头和注释块 <500 字 → 驳回继续等），再跑 润色（含内链：前文索引只取已发布文章微信 URL；**最小干预：AI 新增正文段落默认禁止，作者行文自足时禁写桥接/过渡/总结段**）→ 素材扫描（作者提示时扫 Obsidian `_INDEX.md`）+ 查事实 → 补公式 → 配图 → 事实查验（作者裁决）→ 质量审查 → 封面 → 存草稿箱。**不套**原声槽门禁——全文手写即全篇原声，AI 把作者原稿段落登记进本篇 `quality_check.json` 的 `slots` 让机器核验润色未动原声；事实疑点必须交作者裁决；作者编辑门禁与发布硬门禁和自动成稿相同；**篇幅可被作者口头豁免**（「不要管文章长度」→ `quality_check.json` 的 `exempt` 加「篇幅」并放大 `body_max`/`all_max`，禁按默认 2000 字口径砍稿）。

判断：目录里有作为素材入口的 `raw.md`、且作者按素材直出 skill 走 → 不套。目录里有 `draft.md`、且作者按手写稿直出 skill 走 → 不套（slots 门禁见上）。作者明确说走 grill / 大纲成稿 → 套。

## 执行流程（自动成稿）

1. 作者提出选题方向 → AI 派生 `<slug>`，派发命名 agent **`article-researcher`**（`subagent({ agent: "article-researcher", task: "选题方向：…；slug：…" })`），**等 brief 回传**（原生完成通知唤醒；async 派发则 `bg_wait` 阻塞等），main agent 将 brief 落盘 `.grill/<slug>-research.md`
2. **brief 在手后**才加载 grill-me skill 逐轮追问：意图、约束、核心冲突、类比选择、受众假设等
3. 讨论收敛后，AI 将结论写入 `.grill/<slug>.md` 日志
4. 确认 grill 日志无误**且 `.grill/<slug>-research.md` 调研 brief 已在手**（brief 未回则等完成通知，禁开写）→ 方可进入大纲起草
5. 读 [`docs/viral-article-playbook.md`](viral-article-playbook.md)，写 `outline.md`（定位、结论、结构、配图、既有检查清单）；**一手证据 / vault 素材 / 内链以 brief 为单一事实源**，brief 缺项才定点补查并回写 brief 对应节
6. **大纲末尾列作者原声槽，全部占位符**：默认 7–10 个候选槽（节少时可少列，不得少于 5 个），每槽给「位置 + 为什么这里 + 问你一句 + 方向」四行提示，原句一律占位符 `【作者填入】`。
7. **成稿派发（2026-11-15 起）**：大纲与调研 brief 定稿后派命名 agent **`weixin-writer`**（**零工具纯文本 lane，材料全部内联进 task**，细则见下文「成稿 subagent」），**不等作者填、直接动笔**，每个槽位「位置」留 `【作者填入】` 占位符；**main agent 禁自己从零写正文**。回传后 main 把 output 代码块里的全文落盘成 `weixin.md`、替换热门文章占位行，再复核 frontmatter / 篇幅 / 占位符 / 图片名，补 `quality_check.json`，然后跑「AI 味并行审查与自动改写循环」（见下文专节），收敛后才派 `article-reviewer`。
8. 作者在 VS Code 自行填入（`outline.md` 或 `weixin.md` 填哪处均可，以 `weixin.md` 为准；可粘 grill 逐字原话，算 1 处；也可整槽标「跳过」）。**AI 禁代拟、禁代填、禁追问催稿**——作者问「这槽写什么好」也只给更具体的提示或方向，不给成句。
9. 原声门禁后移到**发布前终检**：已填 <5 或 `weixin.md` 残留 `【作者填入】` → 禁止存草稿箱（见下文「成稿后：作者编辑门禁」两轮质检）。作者说「先写着」「帮我凑两句」也不代填。

正在写的自动成稿篇，从「尚未写 `weixin.md`」的那一步开始执行。不回溯已发布文章。

## 调研 subagent（选题阶段，2026-11-07 起）

选题阶段的重活（矩阵定位、vault 扫描、选题搜索、arXiv 全文抓取）历史上在主上下文烧掉 **113k tokens**（2026-11-07 会话实测：动笔前 25 分钟，占单篇成稿上下文 43%），改为派命名 agent **`article-researcher`** 承担（定义 `.agents/agents/article-researcher.md`，只读工具由 harness 锁定），main agent 只收 ≤6KB 的结构化 brief：

- **派发时机**：作者提出选题方向即派；**brief 回传后 main agent 才进 grill-me**（2026-11-07 作者改口径：先调研后讨论——grill 的意图/约束/类比讨论要踩在已核实的一手证据上，避免讨论收敛后发现素材不成立而返工；「派完不等、直接 grill-me」旧口径废止）
- **brief 落盘**：子 agent 以 output 回传 brief，main agent 写入 `.grill/<slug>-research.md`
- **硬门禁**：brief 未回不写 `outline.md`；brief 标「未核实」的承重数字禁进大纲结论层
- **main agent 不再全文通读** `docs/content-matrix.md` 与 `docs/note-material-source.md`（归 subagent）；按 brief 指向定点取，禁止重复覆盖
- **brief 缺项补核**：`subagent({ action: "resume", id, message })` 回到同一 run 补，不自己抓全文

## 成稿 subagent（成稿阶段，2026-11-15 起）

正式 `weixin.md` 的**初版**由命名 agent **`weixin-writer`** 生成（定义 `.agents/agents/weixin-writer.md`：模型 `gemini-web/gemini-auto`，thinking `medium`，**`tools: []` 零工具**——该 provider 无原生 function calling，lane 退化为纯文本生成器：不读文件、不写文件、不跑命令）。三支路（自动成稿 / 手写稿直出 / 素材直出）共用：

- **派发时机**：自动成稿 = `outline.md` 与 `.grill/<slug>-research.md` 定稿后；手写稿 = 作者说「好了」且空稿校验通过后；素材直出 = `structure.md` 获作者批准后
- **材料全内联**（main agent 派发前读好文件、全文贴进 task，不给路径）：目录、`slug`、分支、标题；分支入口文件全文（auto = `outline.md` + `.grill/<slug>.md` + `.grill/<slug>-research.md`；handwritten = `draft.md` + 待补充清单 + 作者豁免；raw = `raw.md` + `structure.md`）；内链候选清单（从 `branding/style-corpus/wechat-published-index.json` 或往篇 `weixin.md` frontmatter 取好）；auto 另给原声槽数量
- **lane 产出**：output = 一个 markdown 代码块（`weixin.md` 全文：frontmatter + 正文 + 原声占位符 + 公式 + 配图占位 + 内链 + 尾部；「🔥 热门文章」区为占位行 `<!-- HOT_ARTICLES -->`）+ 一份简短报告（字数 / 结构 / 原声计数 / 待补充处理 / 配图计划 / 内链 / 存疑点）。子 agent 不派 subagent、不出图、不裁决事实、不碰封面与草稿箱
- **回传后 main agent 负责**：① 从代码块取全文写入 `content/<目录>/weixin.md`；② 跑 `python3 scripts/hot_articles.py --md --cited <目录>/weixin.md`，用输出**整块替换** `<!-- HOT_ARTICLES -->` 占位行（禁手写榜单）；③ 复核 frontmatter / 篇幅 / 段落与标题层级 / 原声占位符残留 / 图片文件名；④ 写本篇 `quality_check.json`（slots 逐字取自 `draft.md` 或作者填入内容，numbers/links 按成稿）；⑤ 派 `article-reviewer`，按 findings 修补——**修补不经过 `weixin-writer`**
- **缺项补稿**：回传缺失或成稿明显不达标 → `subagent({ action: "resume", id, message })` 回同一 run 补，不新建 run；连续 2 次不达标才由 main agent 按 outline 补写，并在 `.grill/<slug>-review.md` 留痕
- **禁**：main agent 自己从零写正文；让 `weixin-writer` 自审替代 `article-reviewer`；派发时只给文件路径不内联材料（该 lane 无工具，给了也读不到）

## 成稿后：AI 味并行审查与自动改写循环（2026-11-15 起，派 article-reviewer 前必走）

`weixin.md` 初版落盘（含热门文章占位行替换 + `quality_check.json`）后**禁止直接派 `article-reviewer`**。完整规见 [`docs/ai-flavor-review.md`](ai-flavor-review.md)，要点：

1. 跑 `python3 scripts/style_profile.py --include-published --exclude content/<当前目录>` 生成作者行文 profile（落盘 `.grill/<slug>-style-profile.txt`；句长中位数/短长句占比/功能词基线/AI 味词基线，四 lane 共用同一把尺）
2. 一条 parallel 调用并发派 4 个只读 lane：`ai-flavor-structure`（结构转折）/ `ai-flavor-lexicon`（塑料翻译腔词汇）/ `ai-flavor-rhythm`（句式长短套路，对照 profile）/ `ai-flavor-language`（中英混杂与表达卫生）；round≥2 时内联上一轮 findings 要求逐条复核
3. findings 汇总落盘 `.grill/<slug>-aiflavor-roundN.md`；有 FAIL 则备份 pre 版后派 `ai-flavor-rewriter`（零工具 lane，材料全内联）出改写版
4. 跑 `python3 scripts/ai_flavor_gate.py <pre> <post> --dir <目录>` 机械门禁（11 项不变量）；FAIL 项原样并入下一轮 findings
5. 循环至收敛（一轮无新 FAIL 且上轮 FAIL 全部「已解决」）或 3 轮上限；未收敛的剩余清单交作者拍板
6. **orchestrator 纪律**：main agent 只协调（派发/汇总/备份/跑脚本/落盘），禁自己写改正文、禁自己评审——本阶段所有文字修改只经 `ai-flavor-rewriter`

## 成稿后：作者编辑门禁（存草稿箱前必走，2026-11-08 起）

`weixin.md` 写完后**禁止直接存草稿箱**。先后台派发命名 agent **`article-reviewer`**（定义 `.agents/agents/article-reviewer.md`，只读工具由 harness 锁定：机器质检三轨 + 封面/配图核验 + 19 项人工清单 + 与调研 brief 对账），findings 以 output 回传、main agent 落盘 `.grill/<slug>-review.md` 并按 findings 修完，再走固定四步：

1. `bash scripts/precheck_and_open.sh content/<日期>-<slug> --skip-voice`——**第一轮机器质检**（本篇 `quality_check.py` + `check_cover.py` + 微信链接溯源）；`--skip-voice` = 不管原声（作者此时正在 VS Code 填原声占位符）
2. 脚本自动打开 content-gen 文件夹工作区并定位到 `weixin.md`，MPE 预览随文件自动弹出（`.vscode/settings.json` 自动预览开关）——**AI 停在这里等作者改**（内容修改 + 填原声占位符），不催、不代改
3. 作者改完后 `bash scripts/precheck_and_open.sh content/<日期>-<slug> --no-open`——**终检**（全量含原声门禁：≥5 逐字在场 + 无 `【作者填入】` 残留；终检前 AI 把已填原句（outline / weixin.md 哪处有填取哪处，**以 `weixin.md` 为准**）同步进本篇 `quality_check.json` 的 `slots`，逐字）；FAIL 项由作者改稿产生的（如原声被作者自己改写），由作者拍板，AI 不擅自改回
4. 终检通过（或作者明确豁免）才走 `baoyu-post-to-wechat` 存草稿箱（grace + blue）

完整规则见 `AGENTS.md`「作者编辑门禁」节。

## 作者原声槽

### 什么算一处

类型与 [`branding/style-corpus/style-features.md`](../branding/style-corpus/style-features.md) 的五类原声句相同（个人经验、类比、情绪吐槽、数字实测、结尾互动问），全部计入。

- 一句或连续几句、表达同一个亲历 / 判断 / 类比 / 实测 / 提问，算 **1 处**。
- 只有作者写出来的句子才算。AI 写的开头钩子、过渡、小结、开放式问题都不算。
- grill 对话或作者笔记里的 **逐字原话**，作者粘进占位符即算 1 处；AI 写进 `.grill/<slug>.md` 的综述、Intent、决策摘要不算。
- 作者标明用来填槽的句子，即使很短，也算；AI 不得以「不够感人」拒收。
- 「跳过」的槽不计。
- 下限 5 是进稿处数，不是展示槽数。能多则多。

### 占位符怎么列（2026-11-07 作者改口径：VS Code 自填，取代逐槽交互）

每个槽固定四行，**原句一律占位符，禁止出现可进稿的完整原声句**：

- **位置**：第几节，接在哪句论点后面
- **为什么这里**：读者这里容易出戏，或需要一个「我」
- **问你一句**：具体、可回答的提示（「你第一次在哪看到这个数字愣住的？」），禁止「有什么感想？」这类空问
- **方向**：只点类型（亲历 / 类比 / 吐槽 / 实测 / 互动问），不给成句
- **原句**：`【作者填入】`（作者在 VS Code 填入；粘 grill 逐字原话亦可，算 1 处）

作者不填也不催：AI 只在大纲里留好槽位与提示，填多少、什么时候填由作者在 VS Code 决定。作者问「这槽写什么好」：只换更具体的提示或方向，仍不给成句。

`weixin-writer` 写 `weixin.md` 时在同一槽位留同样占位符；作者在 `outline.md` 或 `weixin.md` 填均可，**以 `weixin.md` 为准**（终检查的是 `weixin.md`）。

### `outline.md` 怎么记

在大纲末尾追加。计数写在节标题下第一行。状态只有三种：`待填`（占位符，等作者 VS Code 填入）、`已填`（作者已填入）、`跳过`（作者明确不用）。既有检查清单增加一项：`[ ] 作者原声槽已填且进稿 ≥5`。

```markdown
## 作者原声槽

原声进稿：2 / 下限 5（其余待作者填入）

### 槽 1 · 开头场景之后
- 状态：待填
- 类型：亲历
- 原句：【作者填入】

### 槽 3 · 第三节「折扣回报」之后
- 状态：已填
- 类型：吐槽
- 原句：（作者在 VS Code 填入的原文）

### 槽 4 · 第四节结尾
- 状态：跳过
- 类型：类比
```

写 `weixin.md` 时（`weixin-writer` 执行）：按槽的「位置」插入对应「原句」；不改写、不补总结句、不把口语改成书面语。只修明显错别字。

**原声排版硬规则（2026-11-01 作者追加）**：原声句进稿**禁止加 ★ 前缀、禁止套 blockquote 或任何 AI 加的装饰框**，按正文段落直接排。作者自己在后台改稿时加的 ★ 是后台习惯，AI 成稿一律不得预先添加。

### 挡板

1. **终检前**：`outline.md` 中「已填」< 5，或 `weixin.md` 残留 `【作者填入】` 占位符，禁止存草稿箱（2026-11-07 作者改口径：门禁只在最后一关，不再卡动笔）。
2. **代拟**：AI 不得写出可进稿的原声句。唯一允许的改动是错别字。
3. **成稿后**：见 [`docs/article-quality-check.md`](article-quality-check.md) 第 14 项（原声逐字在场）和第 15 项（说人话 / 去 AI 味）。

## 作者后台改写模式与回拉同步

### 后台改写模式（2026-10-25 信息账篇首次复盘；成稿时预写可减少后台改动）

作者在草稿箱后台的改写有稳定偏好，逐条对照预写：

1. **开头叙事化**：干数据陈述改成「为了分析 X，我把 Y 翻了个底朝天」场景句；预期落空单独成段（「没有想到的是，居然……」）。
2. **公式后补人肉解释**：每个展示公式后补「其中的 I/H 是……，公式说的是……」。AI 原稿常缺这半句，大纲阶段排进结构。
3. **过渡句口语化**：书面过渡（「数学划完边界，说工程」）一律被改口语；断言收尾（「先别急着转发」）被改「我感觉这个结论似乎还下早了」。
4. **结论加保险**：引用数字后加「辩证地看」「毕竟是 X 年的研究了」式条件提醒；绝对判断改双句式（「上限是数学锁死的，皮实是工程技巧可以获得的」）。
5. **原声加 ★ 前缀**：blockquote 原声句前加 ★，回拉同步时保留。⚠️ 这是**作者本人在后台**的编辑习惯；AI 成稿不得预先添加 ★ 或 blockquote 装饰（2026-11-01 作者明确）。
6. **去系列导航化**：删「本篇是系列开篇，XX（待发布）」，改为「下次得空详细说说……」。
7. **结尾合并**：提问+引导合并一段；关注引导加「转发给需要的朋友」。
8. **叠字 typo 高发**：后台快速编辑易留叠字（出来出来 / 案例案例 / 需要要），回拉时必查。

### 回拉同步流程（发布后，每篇必做）

1. `scripts/fetch_draft.sh <media_id>` → `draft-content.html`（vps-us SOCKS5 隧道；40164 即隧道/白名单问题）
2. ⚠️ **公式在 HTML 里是 SVG 矢量块**（信息账篇 28 块）：纯文本 diff 会把公式滤没，别误判公式丢失——按 SVG 块数核对
3. 逐段 diff（web 文本 vs `weixin.md`）：作者改过的段落逐字采用；公式 / 图片 / 链接按原位恢复；叠字 typo 修掉
4. 同步后跑 `quality_check.py --published`（后台改稿跳过成稿期门禁；正文超 2300 属作者扩写，以 ≤2500 总上限守）
5. 发布后第一时间回填 frontmatter `wechatUrl`

## 禁止行为

- 禁止在 grill-me 讨论完成前输出大纲或草稿
- 禁止 AI 单方面生成 grill 日志（必须经过逐轮追问）
- 禁止以"我已经了解了"跳过 grill-me 流程
- 禁止代填占位符；终检「已填」< 5 或占位符未清零禁存草稿箱
- 禁止代拟可进稿的原声句（包括作者要求「帮我起一句」时）
- 禁止 brief 未回就写 `outline.md`；禁止 brief 标「未核实」的承重数字进大纲结论层
- 禁止 main agent 重复调研 subagent 已覆盖的重活（content-matrix 全文通读、vault 通读、arXiv 全文抓取）
