# FFN 去 AI 味语言修订 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让 FFN 文章减少教程腔与工整排比，同时不改变技术内容、链接、图片或文章结构。

**Architecture:** 只修改文章 Markdown 的句级措辞与过渡。先识别模板化句子，再以具体主语、因果关系和自然过渡替换，最后用文本检查确认没有损坏公式、图片路径或运行过的实验。

**Tech Stack:** Markdown、Unicode 数学公式、Python 实验脚本、ripgrep。

---

### Task 1: 逐段修订语言

**Files:**

- Modify: `content/2026-07-21-FFN/draft.md`

- [ ] **Step 1: 标记模板化表达**

运行：

```bash
rg -n '这意味着|需要注意|一句话记忆|回头看|第一步|第二步|最后' content/2026-07-21-FFN/draft.md
```

预期：列出候选句，作为逐段人工判断的清单；不按关键词机械删除。

- [ ] **Step 2: 以具体判断改写候选句**

在 `draft.md` 中执行以下边界：

```text
保留：公式、代码、实验输出、图片、外链、标题和摘要。
改写：替读者总结的句子、对称排比、泛化段首。
禁止：为了缩短 API 内容而删除实验或技术因果。
```

- [ ] **Step 3: 检查数学、图片与链接完整性**

运行：

```bash
rg -n '\$' content/2026-07-21-FFN/draft.md
rg -c '!\[\]\(images/' content/2026-07-21-FFN/draft.md
rg -n 'https://mp.weixin.qq.com/s/' content/2026-07-21-FFN/draft.md
```

预期：第一条没有输出；第二条为 `5`；第三条保留 MoE、残差与基础系列的微信链接。

### Task 2: 验证技术示例并提交

**Files:**

- Modify: `content/2026-07-21-FFN/draft.md`
- Test: `content/2026-07-21-FFN/experiment.py`

- [ ] **Step 1: 运行文章中的实验**

运行：

```bash
python3 content/2026-07-21-FFN/experiment.py
```

预期：输出 `x`、`gate`、`up`、`hidden`、`y` 五组矩阵，且断言全部通过。

- [ ] **Step 2: 审阅变更范围**

运行：

```bash
git diff -- content/2026-07-21-FFN/draft.md
```

预期：差异只涉及自然语言措辞与已修正的 `images/` 图片相对路径。

- [ ] **Step 3: 提交文章修订**

运行：

```bash
git add content/2026-07-21-FFN/draft.md
git commit -m "docs(ffn): soften instructional tone"
```

预期：产生仅包含 FFN 正文的提交。

## Self-review

- 规格中的四条保留/修订规则均由 Task 1 覆盖。
- 不含 TBD、TODO 或未定义的实现步骤。
- Task 2 验证的是同一篇文章和其中引用的实验脚本。
