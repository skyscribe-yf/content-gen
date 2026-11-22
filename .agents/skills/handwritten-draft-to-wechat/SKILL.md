---
name: handwritten-draft-to-wechat
description: Use when 作者要手写全文直出公众号——建 draft.md、VS Code 静默手写、作者说「好了」后 AI 依次跑润色/查事实/补公式/配图/事实查验（作者裁决）/质量审查/封面/存草稿箱；或用户提到「手写稿」「draft.md 直出」「我写好了」这类写文章方式。本 skill 是 AGENTS.md 写作流程的「手写稿直出」分支，与 grill-me（大纲成稿）和 raw-material-to-wechat-draft（素材直出）并列：素材即全文原稿，作者手写完成才触发 AI。
---

# 手写稿直出公众号草稿

## Overview

作者在手写稿 `draft.md` 里写完全文；AI 只负责建稿、开 VS Code、静默等待。作者说「好了」后按固定管线执行：空稿校验 → 润色（含内链）→ 素材扫描（Obsidian vault）+ 查事实 → 补公式 → 配图 → 事实查验（作者裁决）→ 质量审查 → 封面 → 作者编辑门禁 → 存草稿箱。**全文是作者原声**：润色只做最小干预，原话逐字保留。作者随时可用「不要管文章长度」豁免篇幅门禁、用「继续」授权剩余阶段连跑。

## 硬性门禁（无例外）

1. **建稿后才开写**：必须由 AI 运行 `scripts/new-handwritten-topic.sh <slug>` 建好 `draft.md` 并打开 VS Code，作者才开写。
2. **静默等待 + 空稿校验**：作者说「好了」（或「写完了」等同义确认）之前，AI 禁催稿、禁代写、禁主动插话、禁中途插话问结构。等待是这一阶段的全部工作。**收到「好了」后先校验稿件非空**：正文（去 YAML 头和约定注释块）不足 500 字 → 判定未开写或未保存，告知作者「稿子还是空的」并继续静默等，禁启动管线、禁代写救场。
3. **原声句逐字保留 + 最小干预**：draft.md 全文即原声。润色默认只做：修明显错别字、补「待补充」项、把「【图样：描述】」落成图片、按项目规矩补标题/frontmatter/话题标签/尾部热门文章。**AI 新增正文段落默认禁止**——作者行文自足时，任何桥接段/过渡段/总结段/专家式解读都属过度添加（2026-11-14 篇作者原话：「本来写得挺顺利的，加上的反而画蛇添足」）。仅三种例外：① 项目硬规矩要求而作者没写（开头钩子——只补一句，禁加段）；② 公式/图片前后门禁要求的一句凡人话解释；③ 作者原文有硬断点（话题硬跳、关键连接缺失）时补一句、禁加段。禁把口语改书面语，禁加「总的来说」式总结，禁专家口吻，禁删作者任何论点。
4. **「待补充」统一标记，全量处理**：draft.md 里凡是让 AI 补的地方都标「待补充」，冒号后说明类型——**公式 / 配图 / 表格 / 前文索引 / 事实数据**五种；标记形态随意（`待补充`、`待补充：`、`待补充，`、行内或包在 HTML 注释里都认），`【图样：描述】`是配图的等价写法。每一处都要在 weixin.md 落成对应产物，或列入交作者清单，**禁静默丢弃**；补不了的（标记不清）列出来交作者。
5. **公式必须补全**：公式类「待补充」都要在 weixin.md 落成 LaTeX，规则读 `docs/math-latex.md`（禁裸 `<`/`>`、禁 `\text{}` 包中文、禁 Unicode 公式）；公式前后补一句人话解释。补不了的（作者标记不清）→ 列出来交作者，禁静默丢弃。
6. **事实查验闭环**：承重数字/版本号/价格/论文结论一律联网核实（AGENTS.md §4）。与原文不符 → 列 findings 停下来交作者裁决，作者拍板后才改；禁自行「顺手修正」作者的事实性论断。**核查范围含 AI 润色期补写的新数字/论断**，不只作者原话（2026-11-14 篇 reviewer 抓到 2 处润色期数字漂移）。
7. **素材双源**：作者提示 vault 有素材（或主题明显相关）时，先扫 `~/vaults/papers/AI-Chats/_INDEX.md` 一屏扫题定位笔记，只读摘线索（纪律见 AGENTS.md §5：vault 原文禁搬进 content/、禁提交；vault 里的「AI 归纳」只当线索，一手事实仍要开原文复核）；vault 未挂载或无命中 → 明说并走纯联网。
8. **内链必须微信 URL**：前文索引/文内导航只取已发布文章的 frontmatter `wechatUrl`（查 `branding/style-corpus/wechat-published-index.json` / `docs/wechat-data-audit-log.json`），禁相对路径；未发布标「（待发布）」，发布后补 URL。
9. **配图三轨**：概念图 AI 生（默认 `scripts/yairouter_img.py`，prompt 写明无文字无数字），数字/对比/结构/公式图脚本画，**原报告表格类「待补充」脚本重画**（禁截图外文表格）。**AI 概念图禁承载具体数字**；每张图的文字/数字/年份必须与正文一致。
10. **质量审查必派**：weixin.md 第一版完成后派命名 agent **`article-reviewer`**（`async: true` + 完成通知），findings 落盘 `.grill/<slug>-review.md`，主 agent 按 findings 修完才进封面。
11. **作者编辑门禁（存草稿箱前）**：`scripts/precheck_and_open.sh` 两轮（打开 VS Code 等作者 → `--no-open` 复检），通过或作者明确豁免才存草稿。详见 AGENTS.md「发布硬门禁」。
12. **只存草稿，禁止直接发布**：走 `baoyu-post-to-wechat` 的 `--submit`（浏览器保存草稿）或 API `draft/add`，不触发群发；存草稿前复校验 draft.md 与阶段 0 记录的 md5 一致（作者原稿未被管线改动）；发布后第一时间回填 frontmatter `wechatUrl`。
13. **成稿必派 subagent**：`weixin.md` **初版**由命名 agent **`weixin-writer`**（`.agents/agents/weixin-writer.md`；`gemini-web/gemini-auto` + thinking `medium`，**零工具纯文本 lane**）生成——**材料全内联**：main 派发前把 `draft.md` 全文、md5 基线、待补充清单、作者豁免全部贴进 task；main agent 只收稿落盘、替换热门文章占位行、复核、补 `quality_check.json` 与跑后续门禁，禁自己从零写正文。

## 工作流

### 阶段 0 · 建稿与静默等待

1. 作者给出话题 → AI 派生 `<slug>`（kebab-case，与目录名一致）→ `bash scripts/new-handwritten-topic.sh "<slug>"`。
   产物：`content/<日期>-<slug>/draft.md`（YAML 头 + 手写约定注释块），脚本自动打开 VS Code 并弹出 MPE 预览。
   **台账登记由脚手架自动完成**（`new-handwritten-topic.sh` 建稿即跑 `schedule.py add`）；AI 建稿后用 `python3 scripts/schedule.py get <目录名>` 核对有条目，缺了立即手动 `add`——2026-11-14 GB300 篇漏了这步，发布时才补录，禁止再犯。（台账 slug = `content/` 下完整目录名）
2. **AI 静默**：作者在 VS Code 写完全文之前不做任何事。作者问「这里写什么」也只给提示不给成句。
3. 作者说「好了」→ **先空稿校验**：读 draft.md 全文，正文（去 YAML 头和约定注释块）不足 500 字 → 只含模板占位句，判定未开写，告知作者「稿子还是空的，写完再跟我说」并回到静默等待；禁启动后续任何阶段、禁代写救场。
4. 稿件非空 → 记录 draft.md 的 md5（冻结基线，存草稿前复校验）→ 通读全文，列「待补充」清单（五种类型各几处），进入阶段 1。

### 阶段 1 · 润色（draft.md → weixin.md；派 `weixin-writer` 执行）

draft.md 冻结不动；成稿写 `weixin.md`（唯一发布基准）。

**派发（2026-11-15 起）**：本阶段整体交命名 agent **`weixin-writer`**（`.agents/agents/weixin-writer.md`；`gemini-web/gemini-auto` + thinking `medium`，零工具 lane），task 给：目录、`slug`、分支 `handwritten`、标题、`draft.md` 全文、`draft.md` 的 md5 基线、待补充清单（五类各几处）、作者豁免（如「篇幅」）、内链候选清单。**材料不内联 = 白派**（该 lane 无工具，读不了文件）。main agent 禁自己从零写正文；回传后从 output 的 markdown 代码块取全文落盘 `weixin.md`、跑 `scripts/hot_articles.py --md --cited` 替换 `<!-- HOT_ARTICLES -->` 占位行，再按下列清单逐项复核，并补第 9 项 `quality_check.json`。

1. **读语料**：`branding/style-corpus/style-features.md` 认原声句类型（本篇全文手写，全部算原声）。
2. **标题**：作者 frontmatter 有 `title` 就用；空着按 `docs/article-title-seo.md` 起（≤22 字、关键词前置、痛点驱动），写进 weixin.md frontmatter。
3. **正文搬运**：作者原话逐字进稿，只修明显错别字。段落 300–600 字（<300 一般不分段，醒目句独立成段）、`##` 节 ≥5、超约 400 字的节补 `###`（`docs/writing-flow.md` 2026-11-15 规，≤80 字旧规已废止；**原声段落按门禁豁免**，不得为凑规则改写原句）。
4. **开头钩子**：正文第一段禁标题开场（禁 `##` 起首、禁把标题抄成第一行）；作者自己写好了钩子就不动；没写则 AI **只补一句**，禁加段。
5. **补公式**：公式类「待补充」→ LaTeX（`docs/math-latex.md`），公式前后补一句人话解释（门禁 3 例外②，除此以外 AI 禁写任何结构过渡/桥接段）；结尾禁加引导段——项目规矩要的尾部（热门文章 + 话题标签）除外。
6. **图片/表格占位**：每一处配图类「待补充」或「【图样：描述】」→ `![说明](NN-名称.png)`，同时登记出图计划（描述 + 轨道：AI 概念图 / 脚本数据图 / 脚本表格）。图片与 weixin.md 同级、无 `images/` 前缀。
7. **内链（前文索引）**：作者标了「待补充：插入《篇名》前文链接」→ 按篇名取已发布文章微信 URL 插到指定位置；没标 → AI 按本篇主题从 `branding/style-corpus/wechat-published-index.json` / `docs/wechat-data-audit-log.json` 配 2–4 篇相关旧文，插在相关论述处（禁堆文末）。链接登记进 `quality_check.json` 的 `links`。
8. **frontmatter 补全**：`digest`/`keywords`/`type`/`series` 作者没填则 AI 补。
9. **写 quality_check.json（main agent 在 `weixin-writer` 回传后做）**：`slots` = 作者原稿段落逐字（挑 8–12 段有代表性的：亲历/判断/类比/实测/提问），让机器核验润色没动原声；其余定制项按 `scripts/quality_check.py` 要求，`numbers` 与正文格式严格一致（LaTeX 千分位写 `745{,}472` 这种转义形态）。
10. **篇幅豁免**：作者说过「不要管文章长度」等口径 → `exempt` 加「篇幅」并同步调大 `body_max`/`all_max`（参考 2026-11-14 篇的 99999）；**禁再按默认 ~2000 字口径砍作者稿**。作者没提 → 按默认口径。
11. **尾部热门文章**：`python3 scripts/hot_articles.py --md --cited <weixin.md>` 生成「🔥 热门文章」区（禁手写），发布前跑 `--self-check`；正例模板见 `docs/pre-publish-final-check.md` 6c 节。

### 阶段 2 · 素材扫描 + 事实核查（先记不改）

1. **素材扫描（作者提示 vault 有素材时必做）**：读 `~/vaults/papers/AI-Chats/_INDEX.md` 一屏扫题，按本篇主题词定位相关笔记，只读摘线索（AGENTS.md §5：vault 原文禁搬进 content/、禁提交；vault 里的「AI 归纳」只当线索，一手事实仍要开原文复核）。vault 未挂载或无命中 → 明说「vault 无相关素材」，纯联网继续。
2. **联网核实**：从 weixin.md 抽取承重数字/版本号/价格/论文结论/模型发布时间，逐条核实（`deepseek_search` / `ollama_web_search` / 只读调研 lane；AGENTS.md §4：价格/版本号/参数规模必须实时搜索验证，禁沿用「大概」）。**核查范围含 AI 润色期补写的新数字/论断**——本次 2026-11-14 篇 reviewer 抓到 2 处润色期漂移，只查作者原话会漏。
   - 派只读调研 lane 按 AGENTS.md Paseo 路由表（免费档 / CMD 允许时段；派 CMD 前必跑 `~/.local/bin/cmd-window-check`）。付费档 402/余额不足/挂错 → **换免费档重试一次**再谈升级，禁一失败就上付费档。
   - 产出**疑点清单**（先不停机）：

| # | 位置（节/行） | 原文断言 | 核实结果（来源） | 结论 |
|---|---|---|---|---|

3. **外链规则**：核实通过的来源写进文末「**参考资料与数字溯源**」区，逐条列**纯文本** URL——公众号里外部链接禁用 markdown 语法（质量门禁会打 ✗，2026-11-14 篇踩过）；文章间导航才用 markdown 链接且限微信 URL。
4. 疑点 → 带入阶段 4 交作者裁决。

### 阶段 3 · 补公式与配图

1. 公式在阶段 1 已落稿；此处复核渲染（改完公式必回查：`scripts/mdnice-render.py` 渲染后 `merror` 计数为 0、SVG 数与公式数一致，`docs/math-latex.md`）。
2. 按出图计划逐张出图（`docs/image-generation.md`）：
   - 概念图 → `scripts/yairouter_img.py`，prompt 禁文字禁数字；逐张检查与正文一致。
   - 数字/对比/结构图 → 脚本画（参考往篇 `gen_charts.py`）；**只有核实通过的数字才画**，疑点数字对应的图标记「待裁决」先不画。
   - 表格类「待补充」（如原报告 Table 1）→ 脚本重画或 HTML table，**禁截图外文表格**。
3. 文件命名 `NN-名称.png`，与 weixin.md 同级。

### 阶段 4 · 事实查验闭环（作者裁决）

- 疑点清单逐条交作者，每条四要素：**编号 + 位置 + 原文断言 + 核实来源 + 建议改法**；末尾附一句「回复『改 / 不改 / 你的措辞』即可，可极简回复（如『1）改 2）保留』）」。
- 有疑点 → **STOP**，等作者拍板；作者回复后 **AI 先逐条复述裁决结论**（哪条改、怎么改）再应用，**同步更新受影响的图片**（数字变了就重画），再进阶段 5。
- 作者说「**继续**」= 授权剩余阶段连续执行，不再逐阶段停机汇报（作者编辑门禁与存草稿前两处仍必停）。
- 无疑点 → 明说「事实查验通过」继续。
- 禁跳过裁决自行改数；禁把疑点带进终稿。

### 阶段 5 · 质量审查

1. 派 `article-reviewer`（`async: true`，等完成通知）：机器质检三轨 + 封面/配图核验 + 19 项人工清单 + 与疑点清单对账 + **AI 新增段落必要性对账**（diff weixin.md 与 draft.md：成稿有而原稿无的正文段落逐个审，命中不了门禁 3 三种例外的标 FAIL 建议删）。findings 落盘 `.grill/<slug>-review.md`，按 findings 修完。
2. 复跑机器质检：`bash scripts/precheck_and_open.sh <目录> --no-open`（全量，含原声门禁：slots ≥5 逐字在场 + 无 `【作者填入】` 残留）。

### 阶段 6 · 封面

1. AI 出无字深色底图（prompt 写明 no text，`docs/image-generation.md`）→ `cover_spec.json`（两行 `lines`，总字数 ≤12）→ `python3 scripts/make_cover.py <目录>`（裁 21:9 + PIL 叠金色发光字）。
2. 验收必跑 `python3 scripts/check_cover.py <目录>`（21:9 + 文字块高 ≤25% + 每行字高 ≥8%），并放大文字区逐字看底部笔画。

### 阶段 7 · 作者编辑门禁 + 存草稿箱

1. `bash scripts/precheck_and_open.sh <目录>`——机器质检 + 打开 VS Code 定位 weixin.md，MPE 预览随文件弹出。**AI 停在这里等作者改**，不催、不代改。
2. 作者改完 → `bash scripts/precheck_and_open.sh <目录> --no-open`——终检（FAIL 项由作者改稿产生的由作者拍板）。
3. 终检通过（或作者明确豁免）→ 复校验 draft.md md5 与阶段 0 记录一致（作者原稿未被管线改动）→ `baoyu-post-to-wechat` 存草稿箱（grace + blue）→ **台账条目翻 `draft_saved` + 记 media_id**：`python3 scripts/schedule.py set <slug> --status draft_saved --draft-media-id <media_id>`。**只存草稿，不发布。**
4. 作者确认已发布（供链接）→ 三处回填 + 一次核验：
   - `weixin.md` frontmatter `wechatUrl` = 真实 URL；**title 同步为后台 msg_title**（发布时作者可能改过标题，如 GB300 篇多了个「吗」）
   - 台账：`python3 scripts/schedule.py set <slug> --status published --published-date <日期> --wechat-url <url>`（条目自动迁入 published.json，meta 计数自动重算）
   - `branding/style-corpus/wechat-published-index.json` 首行追加 `{title: 后台 msg_title, url}`（内链检索源）
   - 跑 `python3 scripts/verify_published_urls.py --slug <slug>` 核验 URL 有效且页面 msg_title 与台账一致

## 输出约定

- `content/<日期>-<slug>/draft.md`：作者手写原稿，冻结不改（阶段 0 记 md5，存草稿前复验）
- `content/<日期>-<slug>/weixin.md`：成稿，唯一发布基准
- `content/<日期>-<slug>/quality_check.json`：本篇质检配置（slots = 作者原声段落；exempt = 作者给过的豁免，如「篇幅」）
- `content/<日期>-<slug>/cover_spec.json` + `00-cover.png` + `NN-*.png`：封面与配图，与 weixin.md 同级
- `content/<日期>-<slug>/gen_charts.py`：脚本图/表格绘制脚本（留档复算用）
- 台账 `schedule/*.json`（`scripts/schedule.py`）：建稿 `add`（drafting）→ 存箱 `set --status draft_saved --draft-media-id` → 发布回填 `set --status published --published-date --wechat-url`
- `branding/style-corpus/wechat-published-index.json`：发布后首行追加 `{title, url}`（后台 msg_title）
- `.grill/<slug>-review.md`：article-reviewer findings
- 文末「参考资料与数字溯源」：核实通过的数字来源（纯文本 URL）

## 常见错误（禁止）

- 作者说「好了」之前催稿、代写、主动插话
- 收到「好了」不校验空稿直接跑管线（稿子还是模板占位句也硬跑）
- 把原声句改成书面语、补总结句、加「总的来说」
- 「待补充」漏处理或静默丢弃（尤其是包在 HTML 注释里的形态），补不了不向作者报告
- 疑点数字未经作者裁决就出数据图/进终稿
- 只核查作者原话，不核查 AI 润色期补写的新数字/论断
- 跳过 article-reviewer 或作者编辑门禁直接存草稿箱
- main agent 自己从零写 weixin.md 初版（应派 `weixin-writer`）；或让 `weixin-writer` 替 `article-reviewer` 自审；或派发时不内联材料只给路径（零工具 lane 读不到）
- AI 概念图承载具体数字；图片带 `images/` 前缀；外文表格用截图
- 用 draft.md 当发布基准（唯一基准是 weixin.md）
- 内链用相对路径、或把未发布文章当已发布引用
- 作者豁免篇幅后仍按默认 ~2000 字口径砍稿
- 作者行文自足时加桥接段/过渡段/总结段/专家式解读（画蛇添足）
- 裁决后不逐条复述确认就应用修正

## 相关资源

- 风格语料：`branding/style-corpus/style-features.md`
- 标题：`docs/article-title-seo.md`；数学公式：`docs/math-latex.md`
- 配图：`docs/image-generation.md` + `scripts/yairouter_img.py`
- 质检：`scripts/precheck_and_open.sh` + `scripts/quality_check.py` + `docs/article-quality-check.md` + `docs/pre-publish-final-check.md`
- 封面：`scripts/make_cover.py` + `scripts/check_cover.py`
- 尾部热门文章：`scripts/hot_articles.py --md --cited <本文weixin.md>`（禁手写，发布前跑 `--self-check`）
- 存草稿：`baoyu-post-to-wechat` skill（`--submit` / `draft/add`）
- 脚手架：`scripts/new-handwritten-topic.sh`
