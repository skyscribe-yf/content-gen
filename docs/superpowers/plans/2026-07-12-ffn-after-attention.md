# FFN after Attention Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce a fact-checked first draft for the scheduled 2026-07-21 article “前馈网络怎么工作？注意力之后还要想一遍”.

**Architecture:** Keep all new content in `2026-07-21-FFN/`. Build evidence before prose: first collect model configuration data from a primary source, then write and run the deterministic FFN experiment, then draft around the approved narrative. Keep illustrations as versioned prompt source files; do not submit image-generation tasks.

**Tech Stack:** Markdown with YAML frontmatter, Python 3 with NumPy, Hugging Face model repository `config.json` primary sources, Unicode mathematics.

---

## File structure

- Create: `2026-07-21-FFN/experiment.py` — deterministic two-token SwiGLU FFN experiment.
- Create: `2026-07-21-FFN/experiment-output.txt` — captured output used by the article.
- Create: `2026-07-21-FFN/outline.md` — section-level writing map and evidence placement.
- Create: `2026-07-21-FFN/draft.md` — first article draft.
- Create: `2026-07-21-FFN/prompts/00-cover-ffn.md` through `04-transformer-preview.md` — image-generation source prompts only.
- Modify: `findings.md`, `progress.md`, `task_plan.md` — evidence and progress records.

### Task 1: Establish primary-source model evidence

**Files:**
- Modify: `findings.md`
- Modify: `progress.md`

- [ ] **Step 1: Locate a preferred Chinese model’s official Hugging Face repository and open its `config.json`.**

Run a web search restricted to Hugging Face for the preferred current model, starting with DeepSeek-V4; if its public config is unavailable, try GLM-5.2, Kimi K2.6, then Qwen3.

- [ ] **Step 2: Record only values present in the selected config.**

Capture the model identifier, revision/date if supplied, `hidden_size`, `intermediate_size`, `hidden_act`, and architecture field names that show its FFN projection layout. Include the direct source URL in `findings.md`.

- [ ] **Step 3: Check the article claim against the evidence.**

Confirm that the wording says “this model’s configuration uses …” rather than generalizing an implementation-specific field to every Transformer.

- [ ] **Step 4: Update the evidence log.**

Add the source, exact values, the intended prose claim, and any unavailable fields to `findings.md`; log completion in `progress.md`.

### Task 2: Build and run the deterministic FFN experiment

**Files:**
- Create: `2026-07-21-FFN/experiment.py`
- Create: `2026-07-21-FFN/experiment-output.txt`
- Modify: `findings.md`
- Modify: `progress.md`

- [ ] **Step 1: Write the experiment with two 2-dimensional token rows and fixed matrices.**

Use this exact computation structure:

```python
import numpy as np

x = np.array([[1.0, -0.5], [0.2, 1.0]])
w_gate = np.array([[1.0, -1.0, 0.5], [0.5, 1.0, -1.0]])
w_up = np.array([[0.8, 0.4, 1.2], [-0.3, 0.9, 0.2]])
w_down = np.array([[0.6, -0.2], [0.1, 0.7], [0.5, 0.3]])

def silu(z):
    return z / (1.0 + np.exp(-z))

gate = silu(x @ w_gate)
up = x @ w_up
hidden = gate * up
y = hidden @ w_down
```

- [ ] **Step 2: Add explicit invariance assertions.**

```python
assert np.allclose(y[0], (silu(x[0] @ w_gate) * (x[0] @ w_up)) @ w_down)
assert np.allclose(y[1], (silu(x[1] @ w_gate) * (x[1] @ w_up)) @ w_down)
```

These assertions demonstrate that each FFN output row depends only on its own input row.

- [ ] **Step 3: Print rounded intermediate arrays and run the script.**

Run: `python3 2026-07-21-FFN/experiment.py | tee 2026-07-21-FFN/experiment-output.txt`

Expected: exit status 0; printed arrays for `x`, `gate`, `up`, `hidden`, and `y`; two invariant assertions pass silently.

- [ ] **Step 4: Validate the output is reproducible.**

Run: `python3 2026-07-21-FFN/experiment.py > /tmp/ffn-output.txt && diff -u 2026-07-21-FFN/experiment-output.txt /tmp/ffn-output.txt`

Expected: exit status 0 and no diff.

- [ ] **Step 5: Record the experiment result.**

Summarize the observable gate behavior and passed assertions in `findings.md` and `progress.md`.

### Task 3: Create the article structure and visual prompt sources

**Files:**
- Create: `2026-07-21-FFN/outline.md`
- Create: `2026-07-21-FFN/prompts/00-cover-ffn.md`
- Create: `2026-07-21-FFN/prompts/01-roundtable-thinking-room.md`
- Create: `2026-07-21-FFN/prompts/02-swiglu-pipeline.md`
- Create: `2026-07-21-FFN/prompts/03-fixed-matrix-experiment.md`
- Create: `2026-07-21-FFN/prompts/04-transformer-preview.md`

- [ ] **Step 1: Write an outline that maps each of the seven approved sections to its reader question, evidence, and visual insertion point.**

- [ ] **Step 2: Write the cover prompt source.**

Specify a 21:9 cinematic cover with the technical idea of “many tokens finish a roundtable, then enter identical individual processing rooms.” Do not include title text, dates, or numeric claims in the image.

- [ ] **Step 3: Write four inline prompt sources.**

Use the approved visuals: roundtable-to-thinking-room, expand/SwiGLU/project pipeline, fixed-matrix feature gating, and Transformer-block preview. Use text only when necessary and ensure every technical term matches the outline.

- [ ] **Step 4: Check source-prompt consistency.**

Run: `rg -n 'FFN|SwiGLU|残差|归一化|MoE|注意力' 2026-07-21-FFN/outline.md 2026-07-21-FFN/prompts/*.md`

Expected: all labels agree with the planned article terminology.

### Task 4: Draft the article

**Files:**
- Create: `2026-07-21-FFN/draft.md`

- [ ] **Step 1: Add YAML frontmatter.**

Set `title: "前馈网络怎么工作？注意力之后还要想一遍"`, `author: "数解AI"`, `type: "原理篇"`, `series: "大模型原理"`, `scheduledPublish: "2026-07-21T08:00:00+08:00"`, a 2–3 keyword digest, and keyword list containing `"前馈网络"`, `"FFN"`, and `"SwiGLU"`.

- [ ] **Step 2: Draft the opening and division-of-labor sections.**

Use the “Attention Is All You Need” conflict and the roundtable-to-thinking-room metaphor. State explicitly that attention mixes information across positions, while FFN applies the same transformation independently to every position.

- [ ] **Step 3: Draft the calculation and experiment sections.**

Use Unicode-only formulas for the two-projection SwiGLU path. Insert the tested code and exact selected output from `experiment-output.txt`. Explain that rows do not interact inside the FFN and that the fixed values are illustrative, not learned language semantics.

- [ ] **Step 4: Draft the real-model, MoE, and preview sections.**

Use only Task 1’s verified configuration data. Link the existing activation article, MoE article, and attention article using their known WeChat URLs where available; mark unpublished FFN-series URLs as `（待发布）`. Close by previewing residual connection and normalization without explaining their mechanics.

- [ ] **Step 5: Add all visual placeholders, series navigation, follow invitation, and open discussion question.**

Include five image filenames that match the prompt files. The discussion question must be answerable and tied to the article, for example: “如果注意力负责从上下文取信息、FFN负责加工信息，你觉得长上下文模型先遇到的瓶颈会是哪一层？”

### Task 5: Run the article quality review

**Files:**
- Modify: `findings.md`
- Modify: `progress.md`
- Modify: `task_plan.md`

- [ ] **Step 1: Check forbidden math delimiters and title length.**

Run: `rg -n '\$\$?|\\\(|\\\[' 2026-07-21-FFN/draft.md; printf '%s' '前馈网络怎么工作？注意力之后还要想一遍' | wc -m`

Expected: no regex matches; title length 22 or less.

- [ ] **Step 2: Check required editorial elements.**

Run: `rg -n 'SwiGLU|MoE|残差|归一化|https://mp.weixin.qq.com/s/|（待发布）|关注|评论|讨论' 2026-07-21-FFN/draft.md`

Expected: matches for model behavior, MoE bridge, next-article preview, valid links/placeholders, follow invitation, and an open question.

- [ ] **Step 3: Check visual-source coverage.**

Run: `find 2026-07-21-FFN/prompts -type f -name '*.md' | wc -l && rg -n '!\[\]\(' 2026-07-21-FFN/draft.md`

Expected: five prompt source files; at least four inline image placeholders in the draft.

- [ ] **Step 4: Re-run the experiment and compare captured output.**

Run: `python3 2026-07-21-FFN/experiment.py > /tmp/ffn-output.txt && diff -u 2026-07-21-FFN/experiment-output.txt /tmp/ffn-output.txt`

Expected: exit status 0 and no diff.

- [ ] **Step 5: Record final verification.**

Update the planning records with command results, remaining non-draft assets (generated images and WeChat publication), and Phase 4 status.

### Task 6: Hand off the draft

**Files:**
- Modify: `task_plan.md`
- Modify: `progress.md`

- [ ] **Step 1: Review only the new FFN directory and planning records in `git diff --`.**

Run: `git diff -- 2026-07-21-FFN .grill/ffn-after-attention.md task_plan.md findings.md progress.md ../docs/superpowers/specs/2026-07-12-ffn-after-attention-design.md ../docs/superpowers/plans/2026-07-12-ffn-after-attention.md`

Expected: review is confined to the article task; no unrelated files are modified.

- [ ] **Step 2: Provide the draft path, verified evidence summary, and publishing follow-ups.**

State that image generation and WeChat publication are not included in this drafting task; images require prompt review and the configured image workflow.
