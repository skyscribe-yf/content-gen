---
name: raw-material-to-wechat-draft
description: Use when 作者要新建话题并把想表达的内容以原始文本扔进来，让 AI 归纳整理、突出要点、生成配图后存公众号草稿箱；或用户提到「素材直出」「把我的素材整理成文章」「先建话题」这类写文章方式。本 skill 是 AGENTS.md 写作流程的「素材直出」分支，与 grill-me 不同：素材由作者提供，AI 不代拟观点。
---

# 素材直出公众号草稿

## Overview

作者先建话题、把想表达的内容以原始文本（口语、随手记、数据、链接都行）扔进 `raw.md`；AI 负责归纳整理、突出要点，但**保留作者原声句**；作者在检查点确认后，生成配图、渲染排版、存公众号草稿箱（不直接发布）。

## 硬性门禁（无例外）

1. **动笔前必读风格语料**：`branding/style-corpus/style-features.md`（先认语料分层）。长文再读一篇金标准 `raw.md`（矩阵秩 / 期望与导数换序 / 多维高斯注解 / KL 散度等）；贴图读 `tietu-raw/` 手敲原文。**不要**拿 2026-08-23 及之后的贴图轨道当文风样本。识别作者原声后再整理。
2. **原声句逐字保留**：`style-features.md` 列出的类型一律不改写（含学习过程句、划边界句）；允许的唯一改动是修正明显错别字。禁止把口语改成书面语，禁止加总结句和「专家口吻」。
3. **必须停在检查点**：归纳整理后输出 `structure.md`（结构大纲 + 原声句清单 + 配图清单 + 素材缺口），**等待作者确认**。作者未批准前禁止写正文、禁止生成任何图片。
4. **双轨配图**：概念图用 AI 生成（默认 `scripts/yairouter_img.py`），数字/对比/结构/公式用脚本画图。**AI 生图禁止承载具体数字**（AI 会编数字）。封面 AI 画，21:9，正文概念图 4-6 张，每节至少一张、重点段最多两张，概念密度低时 3 张可接受但须在配图清单标注原因。
5. **事实必须联网核实**：价格、版本号、模型发布时间等素材中的数字，一律实时搜索验证后再进稿，禁止沿用作者口头「大概」。
6. **只存草稿，禁止直接发布**：走 `baoyu-post-to-wechat` 的 `--submit`（浏览器保存草稿）或 API `draft/add`，不触发群发。

## 工作流

1. **建话题**：运行 `scripts/new-raw-topic.sh <slug>` 创建 `content/<日期>-<slug>/raw.md`；作者把想表达的一切贴进去，不要求结构。
2. **读素材与语料**：读 `raw.md`、`style-features.md`；长文对照一篇金标准 raw，贴图对照 `tietu-raw/`。跳过 2026-08-23 及之后贴图混稿。
3. **归纳整理**：标注原声句 → 排结构 → 写 `structure.md`，包含：
   - 结构大纲（章节 + 一句话要点）
   - 原声句清单（逐条引用原文，注明将原样进稿）
   - 配图清单（每张图一句话说明用途，标注 AI 概念图 / 脚本数据图）
   - 素材缺口（哪些点缺论据/数据，建议作者补充）
4. **STOP —— 请作者确认 `structure.md`**。作者改完或批准后才继续；不得以「先出图看看」绕开。
5. **写 `weixin.md`**：原声句原文进稿；AI 只补结构过渡、标题（≤22 字、关键词前置、痛点驱动）、开头钩子、结尾引导与话题标签（3-5 个，含 `#数解AI`）。`weixin.md` 是唯一发布基准。结尾若有「🔥 热门文章」，必须运行 `scripts/hot_articles.py --md --cited <本文weixin.md>` 现查现填（读最近审计 `docs/wechat-data-audit-log.json`，自动过滤贴图、追加本文引用的相关文章），禁止凭记忆挑最近文章；每个链接一行、行间不留空行（空行会被渲染成「段间距空行」）。
6. **出图**：按批准的配图清单生成；AI 概念图逐张检查文字/数字/年份与正文一致。
7. **渲染**：markdown → 微信兼容 HTML（`baoyu-markdown-to-html` 或 `baoyu-post-to-wechat` 内部渲染），图片与 `weixin.md` 同级、无 `images/` 前缀。
8. **存草稿**：调用 `baoyu-post-to-wechat` 以 `--submit` 保存草稿；回填草稿 URL 到 frontmatter，不发布。

## 输出约定

- `content/<日期>-<slug>/raw.md`：原始素材，AI 不改动
- `content/<日期>-<slug>/structure.md`：检查点产物，作者确认后视为契约
- `content/<日期>-<slug>/weixin.md`：成稿，唯一发布基准
- 图片与 `weixin.md` 同级存放

## 质量门禁（与常规流程相同，不可豁免）

- 标题：关键词前置 + 痛点驱动 + ≤22 字（`docs/article-title-seo.md`）
- 文末话题标签 3-5 个（`docs/wechat-topic-tags.md`）
- 数据时效实时搜索（`docs/data-freshness.md`）
- 定稿前过 `docs/article-quality-check.md` 全项（含第 15 项说人话/去 AI 味）；发布前过 `docs/pre-publish-final-check.md`
- `weixin.md` 未定稿时，禁止生成任何衍生内容（小红书/知乎/视频等）

## 常见错误（禁止）

- 跳过检查点直接写正文或出图
- 把原声句翻译成书面语、补总结、加「总的来说」
- AI 概念图里出现具体数字、年份与正文不一致
- 用 `draft.md`、模板或 AI 通用文风当基准
- 存草稿时误触发发布/群发

## 相关资源

- 风格语料：`branding/style-corpus/style-features.md`（金标准列表在该文件；含长文 raw.md + `tietu-raw/`）
- 话题脚手架：`scripts/new-raw-topic.sh`
- 配图：`scripts/yairouter_img.py`（AI 概念图）、`docs/image-generation.md`
- 发布/草稿：`baoyu-post-to-wechat` skill（`--submit` / `draft/add`）
- 渲染：`baoyu-markdown-to-html` skill
