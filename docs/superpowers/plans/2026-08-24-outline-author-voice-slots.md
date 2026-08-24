# 自动成稿原声槽 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 自动成稿在写出 `outline.md` 之后、动笔 `weixin.md` 之前，必须向作者采集不少于 5 处原声，并把它写成可执行的硬门禁。

**Architecture:** `docs/writing-flow.md` 是唯一事实源（流程、槽格式、成稿前/代拟挡板）。`AGENTS.md` 只加指针。`docs/article-quality-check.md` 第 14 项只写如何对照大纲核对接稿，细节回指 writing-flow。不新建 skill、脚本或 `voice.md`。

**Tech Stack:** Markdown 流程文档。验收用 `rg` 对照 spec，不写测试代码。

**Spec:** [`docs/superpowers/specs/2026-08-24-outline-author-voice-slots-design.md`](../specs/2026-08-24-outline-author-voice-slots-design.md)

---

## File map

| File | Responsibility |
|---|---|
| `docs/writing-flow.md` | 自动成稿全流程 + 原声槽规则（事实源） |
| `docs/article-quality-check.md` | 第 14 项：成稿后对照大纲数原句 |
| `AGENTS.md` | 写作流程节加一句指针；「13 项」改为「14 项」 |
| `docs/wechat-ops.md` | 仅把「13 项核查」改成「14 项核查」，不写原声规则 |

不改：`.agents/skills/raw-material-to-wechat-draft/SKILL.md`、`.agents/skills/grill-me/SKILL.md`、`branding/style-corpus/style-features.md`。

---

### Task 1: 把原声槽写进 writing-flow

**Files:**
- Modify: `docs/writing-flow.md`

- [ ] **Step 1: 确认现状只有 grill 四步**

Run:

```bash
rg -n "作者原声槽|weixin.md|下限 5" docs/writing-flow.md
```

Expected: 无匹配（文件目前只写到确认 grill 日志、禁止跳过 grill）。

- [ ] **Step 2: 用下面全文覆写 `docs/writing-flow.md`**

保留原有 grill-me 门禁，在其后接上自动成稿步骤和原声槽。五类原声的定义不在这里重写，只指向 `branding/style-corpus/style-features.md`。

```markdown
# 文章写作流程（硬性门禁）

## 规则

每次开始起草文章大纲之前，**必须先调用 grill-me skill 与作者进行深入讨论**，讨论收敛后才能起笔撰写。禁止跳过 grill-me 直接起草大纲或正文。

Skill 位置：[`.agents/skills/grill-me/SKILL.md`](.agents/skills/grill-me/SKILL.md)

自动成稿在写出 `outline.md` 之后、动笔 `weixin.md` 之前，**必须先做作者原声槽对话**，进稿原声不少于 5 处。规则见下文「作者原声槽」。

## 适用范围

- **自动成稿**（本文件后半段）：选题经 grill-me，产物是 `outline.md` 再写 `weixin.md`。套原声槽门禁。
- **素材直出**：走 [`.agents/skills/raw-material-to-wechat-draft/SKILL.md`](../.agents/skills/raw-material-to-wechat-draft/SKILL.md)，用 `raw.md` + 原声句清单。**不套**本文件的原声槽门禁。

判断：目录里有作为素材入口的 `raw.md`、且作者按素材直出 skill 走 → 不套。作者明确说走 grill / 大纲成稿 → 套。

## 执行流程（自动成稿）

1. 作者提出选题方向 → AI 加载 grill-me skill
2. grill-me 逐轮追问：意图、约束、核心冲突、类比选择、受众假设等
3. 讨论收敛后，AI 将结论写入 `.grill/<slug>.md` 日志
4. 确认 grill 日志无误 → 方可进入大纲起草
5. 读 [`docs/viral-article-playbook.md`](viral-article-playbook.md)，写 `outline.md`（定位、结论、结构、配图、既有检查清单）
6. **停住，禁止写 `weixin.md`。** 在对话里一次列出候选原声槽（默认 7–10 个；节很少、挖不满 7 个时可以少列，但候选不得少于 5 个）。进稿下限仍是 5 处。
7. 作者按编号回复原文或「跳过」。AI 把结果追加到 `outline.md` 的 `## 作者原声槽`，更新计数。
8. 「已填」+「沿用」≥ 5：才写 `weixin.md`，按槽位逐字插入原句（只修错别字）。
9. 少于 5：停在大纲。作者说「先写着」「帮我凑两句」也不写正文、不代填。

已有沿用原声仍要展示空槽（标明已占用）。沿用已经 ≥ 5 时，作者可以回复「就这些」过门；空槽未展示之前，不能以「grill 里已经有了」跳过第 6 步。

正在写的自动成稿篇，从「尚未写 `weixin.md`」的那一步开始执行。不回溯已发布文章。

## 作者原声槽

### 什么算一处

类型与 [`branding/style-corpus/style-features.md`](../branding/style-corpus/style-features.md) 的五类原声句相同（个人经验、类比、情绪吐槽、数字实测、结尾互动问），全部计入。

- 一句或连续几句、表达同一个亲历 / 判断 / 类比 / 实测 / 提问，算 **1 处**。
- 只有作者写出来的句子才算。AI 写的开头钩子、过渡、小结、开放式问题都不算。
- grill 对话或作者笔记里的 **逐字原话**，且确定进稿，可标「沿用」并计入；AI 写进 `.grill/<slug>.md` 的综述、Intent、决策摘要不算。
- 作者标明用来填槽的句子，即使很短，也算；AI 不得以「不够感人」拒收。
- 「跳过」的槽不计。
- 下限 5 是进稿处数，不是展示槽数。能多则多。

### 对话里怎么问

每个槽固定四行，**禁止出现可进稿的完整原声句**（沿用槽引用作者已有原话除外）：

- **位置**：第几节，接在哪句论点后面
- **为什么这里**：读者这里容易出戏，或需要一个「我」
- **问你一句**：具体、可回答（「你第一次在哪看到这个数字愣住的？」），禁止「有什么感想？」这类空问
- **方向**：只点类型（亲历 / 类比 / 吐槽 / 实测 / 互动问），不给成句

已占用的沿用槽同样列出，多一行：`已占用，算 1 处：「……原话……」`。

作者一次回复多个编号时，按编号原样归档，不改写、不合并、不润色。某一槽作者说「帮我起一句 / 你写」：只换一个更具体的问题或方向，仍不给成句。

### `outline.md` 怎么记

在大纲末尾追加。计数写在节标题下第一行。状态只有三种：`已填`、`沿用`、`跳过`。既有检查清单增加一项：`[ ] 作者原声槽已填且进稿 ≥5`。

```markdown
## 作者原声槽

原声进稿：6 / 下限 5

### 槽 1 · 开头场景之后
- 状态：沿用
- 类型：亲历
- 原句：恨不得给当年的自己一拳

### 槽 3 · 第三节「折扣回报」之后
- 状态：已填
- 类型：吐槽
- 原句：（作者原文）

### 槽 4 · 第四节结尾
- 状态：跳过
- 类型：类比
```

写 `weixin.md` 时：按槽的「位置」插入对应「原句」；不改写、不补总结句、不把口语改成书面语。只修明显错别字。

### 挡板

1. **成稿前**：`outline.md` 中状态为「已填」或「沿用」的条目 < 5，禁止创建或覆写 `weixin.md`。
2. **代拟**：AI 不得写出可进稿的原声句。唯一允许的改动是错别字。
3. **成稿后**：见 [`docs/article-quality-check.md`](article-quality-check.md) 第 14 项。

## 禁止行为

- 禁止在 grill-me 讨论完成前输出大纲或草稿
- 禁止 AI 单方面生成 grill 日志（必须经过逐轮追问）
- 禁止以"我已经了解了"跳过 grill-me 流程
- 禁止在原声槽未展示、或「已填」+「沿用」< 5 时写 `weixin.md`
- 禁止代拟可进稿的原声句（包括作者要求「帮我起一句」时）
```

- [ ] **Step 3: 核对事实源齐备**

Run:

```bash
rg -n "停住，禁止写|作者原声槽|已填|沿用|跳过|下限 5|帮我起一句|素材直出" docs/writing-flow.md
```

Expected: 每条关键词至少命中一次。流程含第 6 步停住、第 8 步满 5 才写正文、三种状态、代拟拒绝、素材直出不套。

- [ ] **Step 4: Commit**

```bash
git add docs/writing-flow.md
git commit -m "docs: add post-outline author voice slots to writing-flow"
```

---

### Task 2: 质量核查第 14 项

**Files:**
- Modify: `docs/article-quality-check.md`

- [ ] **Step 1: 确认第 13 项是最后一项**

Run:

```bash
rg -n "^## 1[34]\." docs/article-quality-check.md
```

Expected: 只有 `## 13. 爆款检查器`，没有第 14 项。

- [ ] **Step 2: 在文件末尾追加第 14 项**

只写怎么核对接稿，规则细节回指 writing-flow，不把五类定义或对话格式再抄一遍。紧接在第 13 项「原因」段落后追加：

```markdown

## 14. 自动成稿原声槽

**规则**：自动成稿（grill-me → `outline.md` → `weixin.md`）必须对照大纲 `## 作者原声槽`，确认 `weixin.md` 里至少 5 处「已填」或「沿用」原句逐字在场。缺一条就按槽补插，禁止改写成书面语后再过关。

执行：
1. 确认本文走自动成稿。目录里有作为素材入口的 `raw.md`、且按素材直出 skill 成稿的，**本项豁免**（仍核它自己的原声句清单）。
2. 打开 `outline.md` 的 `## 作者原声槽`，数状态为「已填」或「沿用」的条目，必须 ≥ 5。
3. 对每一条「原句」在 `weixin.md` 里逐字检索，必须在场。
4. 缺句则按槽的「位置」原句插入后再查；不得把口语改成书面语充数。

细节（什么算一处、对话怎么问、不满 5 不准写正文）见 [`docs/writing-flow.md`](writing-flow.md)。
```

- [ ] **Step 3: 核对第 14 项只做下游核查**

Run:

```bash
rg -n "^## 14\.|素材直出|writing-flow.md|逐字" docs/article-quality-check.md
```

Expected: 存在第 14 项；含素材直出豁免；含回指 `writing-flow.md`；含逐字在场。文件中不应出现完整的「每个槽固定四行」对话模板（那只属于 writing-flow）。

- [ ] **Step 4: Commit**

```bash
git add docs/article-quality-check.md
git commit -m "docs: add quality-check item 14 for author voice slots"
```

---

### Task 3: 索引指针和项数

**Files:**
- Modify: `AGENTS.md`（约第 5–7 行、第 164 行）
- Modify: `docs/wechat-ops.md`（约第 46 行）

- [ ] **Step 1: 在 `AGENTS.md` 写作流程节加指针**

把

```markdown
起草大纲前**必须先调用 grill-me skill** 与作者深入讨论（`.agents/skills/grill-me/SKILL.md`）。禁止 AI 单方面生成 `.grill/<slug>.md` 日志。详见 [`docs/writing-flow.md`](docs/writing-flow.md)。
```

改成：

```markdown
起草大纲前**必须先调用 grill-me skill** 与作者深入讨论（`.agents/skills/grill-me/SKILL.md`）。禁止 AI 单方面生成 `.grill/<slug>.md` 日志。自动成稿在大纲之后还必须采集作者原声槽（进稿 ≥5 处）才写 `weixin.md`。详见 [`docs/writing-flow.md`](docs/writing-flow.md)。
```

不要把对话格式、三种状态或五类定义写进 `AGENTS.md`。不要改「素材直出公众号草稿 Skill」那一节。

- [ ] **Step 2: 更新清单项数 13 → 14**

`AGENTS.md` 文章质量核查节（约第 164 行）把「含 13 项核查清单，第 13 项为爆款检查器」改成「含 14 项核查清单，第 13 项为爆款检查器，第 14 项为自动成稿原声槽」。

`docs/wechat-ops.md` 约第 46 行把「在既有 `docs/article-quality-check.md` 13 项核查之上」改成「在既有 `docs/article-quality-check.md` 14 项核查之上」。不要在 `wechat-ops.md` 里展开原声槽规则。

- [ ] **Step 3: 核对指针在、素材直出节未膨胀**

Run:

```bash
rg -n "原声槽|14 项" AGENTS.md docs/wechat-ops.md
rg -n "作者原声槽|每个槽固定四行|原声进稿：" AGENTS.md .agents/skills/raw-material-to-wechat-draft/SKILL.md
```

Expected: `AGENTS.md` 写作流程节和质检节、以及 `wechat-ops.md` 命中「原声槽」或「14 项」。第二条命令在 `AGENTS.md` 和素材直出 skill 里都**不应**命中槽模板或 `原声进稿：`（那些只属于 writing-flow / 单篇 outline）。

- [ ] **Step 4: Commit**

```bash
git add AGENTS.md docs/wechat-ops.md
git commit -m "docs: point AGENTS writing-flow at author voice slots"
```

---

### Task 4: 对照 spec 做总验收

**Files:**
- Read: `docs/superpowers/specs/2026-08-24-outline-author-voice-slots-design.md`
- Verify only（本任务不改规则正文）

- [ ] **Step 1: 三条验收命令**

Run:

```bash
rg -n "停住，禁止写|候选不得少于 5|已填|沿用|跳过|帮我起一句" docs/writing-flow.md
rg -n "^## 14\. 自动成稿原声槽|本项豁免" docs/article-quality-check.md
rg -l "作者原声槽" .agents/skills/grill-me/SKILL.md .agents/skills/raw-material-to-wechat-draft/SKILL.md branding/style-corpus/style-features.md || true
```

Expected:

1. writing-flow 命中停笔、候选下限、三种状态、拒绝代拟。
2. 质检存在第 14 项且写明素材直出豁免。
3. 第三条对 grill-me / 素材直出 / style-features **无文件命中**（`|| true` 避免无匹配时非零退出）。

- [ ] **Step 2: 确认没有新建禁止产物**

Run:

```bash
rg --files -g '**/voice.md' -g '**/*voice-slot*' || true
ls .agents/skills | rg -i "voice|yuansheng|grill" || true
```

Expected: 没有新的 `voice.md` 或 voice-slot skill。`ls` 里仍只有既有的 `grill-me`，没有新 skill 目录。

- [ ] **Step 3: 若 Step 1 或 Step 2 失败，停下来修对应文件后重跑；不要在本任务新开规则。全部通过则无需再 commit。**
