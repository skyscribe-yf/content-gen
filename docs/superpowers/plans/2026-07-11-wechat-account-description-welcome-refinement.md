# WeChat Account Description Welcome Refinement Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace 数解AI's account description with a concise welcome that reassures readers about mathematics and promises better AI judgment.

**Architecture:** Preserve a three-line profile format. Line one gives the AI-era context and a direct invitation; line two reframes mathematics as a usable tool; line three converts understanding into a practical outcome.

**Tech Stack:** Chinese brand copy in Markdown.

---

## File Structure

- Read: `docs/superpowers/specs/2026-07-11-wechat-account-description-welcome-refinement-design.md` — approved voice and acceptance criteria.
- Modify: `branding/公众号品牌方案.md` — canonical WeChat account description.

### Task 1: Replace the canonical description

**Files:**
- Modify: `branding/公众号品牌方案.md:28-30`

- [x] **Step 1: Replace the three lines in the “公众号简介” code block**

```text
AI 时代，和你一起用数学看懂 AI。
数学没那么可怕，它只是理解 AI 的工具。
少一点跟风，多一点判断与行动。
```

- [x] **Step 2: Verify the description block exactly**

Run:

```bash
sed -n '26,35p' branding/公众号品牌方案.md
```

Expected: the code block contains the three planned lines, with no extra call to action, emoji, or explanatory text.

- [x] **Step 3: Check Markdown whitespace**

Run:

```bash
git diff --check -- branding/公众号品牌方案.md
```

Expected: no output and exit code 0.
