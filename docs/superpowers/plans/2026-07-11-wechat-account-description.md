# WeChat Account Description Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce a short WeChat Official Account description for 数解AI that gives self-directed AI learners a sense of control.

**Architecture:** Use three scan-friendly lines: mathematics as the brand anchor, the shared obstacle of noise and formulas, and the outcome of better judgment and action. Provide distinct copy directions so the author can choose the degree of warmth and directness.

**Tech Stack:** Chinese brand copy for the WeChat Official Account profile.

---

## File Structure

- Read: `branding/公众号品牌方案.md` — current positioning and the description to replace after selection.
- Read: `docs/superpowers/specs/2026-07-11-wechat-account-description-design.md` — approved audience, voice, and constraints.
- Modify only after author selection: `branding/公众号品牌方案.md` — record the chosen canonical account description.

### Task 1: Present short, compliant copy variants

**Files:**
- Read: `branding/公众号品牌方案.md`
- Read: `docs/superpowers/specs/2026-07-11-wechat-account-description-design.md`

- [x] **Step 1: Present the recommended “降噪掌控型” version**

```text
用数学，看懂 AI。
穿过噪音和复杂公式，
把理解变成判断与行动。
```

- [x] **Step 2: Present the warmer “同行陪伴型” version**

```text
数学不是门槛，
是穿过 AI 噪音和公式的路。
学明白，也用得上。
```

- [x] **Step 3: Present the firmer “反跟风型” version**

```text
用数学拆开 AI 的复杂。
少一点跟风，多一点理解。
敢判断，也能上手。
```

- [x] **Step 4: Explain the selection rule**

```text
首选版本 1：数学标签最直接，且“判断与行动”最准确传达掌控感。
版本 2：连接感最强，适合强调陪伴。
版本 3：态度最鲜明，适合强化与喧嚣自媒体的区隔。
```

### Task 2: Persist the selected canonical description

**Files:**
- Modify: `branding/公众号品牌方案.md` — replace the three lines under “公众号简介”.

- [x] **Step 1: Wait for the author to select a version or request a hybrid**

Do not alter the canonical brand document before the author makes a selection.

- [x] **Step 2: Replace the existing description block exactly with the selected text**

Use the selected three-line version without adding a title, call to action, emoji, or explanatory prose. The author selected version 1 and refined the middle line to emphasize that understanding matters in the AI era.

- [x] **Step 3: Verify the updated block**

Run:

```bash
sed -n '18,30p' branding/公众号品牌方案.md
```

Expected: the “公众号简介” block contains exactly the author-selected three lines and preserves the surrounding Markdown structure.
