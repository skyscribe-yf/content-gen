# FFN 点击钩子与上下文主线改稿计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 FFN 文章改为由反直觉问题驱动，同时让读者准确理解“逐 token 独立计算不等于没有上下文”。

**Architecture:** 保留经过运行验证的 SwiGLU 实验与现有配图占位符，只重排读者进入文章后的信息顺序。标题和首屏负责兑现点击承诺；中段以注意力写入上下文、FFN 分别加工为主线；现实模型段保留一条经核验的国产模型配置旁注；MoE 段压缩为已发布文章的因果回引。

**Tech Stack:** Markdown/YAML frontmatter、Unicode 数学公式、Python 3 + NumPy（既有实验复验）、微信公众号 Markdown 链接。

---

## File structure

- Modify: `content/2026-07-21-FFN/draft.md` — 调整标题、摘要、导语、核心论证、MoE 回引和结尾。
- Modify: `content/2026-07-21-FFN/outline.md` — 令文章结构、读者问题和图片职责与新主线一致。
- Modify: `content/2026-07-21-FFN/prompts/00-cover-ffn.md` — 使 21:9 封面源 prompt 支持“不交流，最费算力？”的文字钩子，且不增加正文外的数字或事实。
- Create: `content/.grill/ffn-click-and-context.md` — 已完成的讨论结论，不在执行中改写。

### Task 1: 核对改稿基线与保留证据

**Files:**
- Read: `content/2026-07-21-FFN/draft.md`
- Read: `content/2026-07-21-FFN/outline.md`
- Read: `content/2026-07-21-FFN/experiment.py`
- Read: `content/2026-07-21-FFN/experiment-output.txt`

- [ ] **Step 1: 复跑确定性实验。**

Run: `python3 2026-07-21-FFN/experiment.py > /tmp/ffn-refinement-output.txt && diff -u 2026-07-21-FFN/experiment-output.txt /tmp/ffn-refinement-output.txt`

Expected: exit status 0 and no diff. The tested assertion remains the basis for “改变一个 token 不会在 FFN 内改变另一个 token 的输出”.

- [ ] **Step 2: 记录本次不触碰的技术边界。**

Keep the existing Unicode equations, fixed matrices, four inline-image placeholders, residual/normalization preview, and valid published WeChat links. Do not introduce new model version, pricing, parameter, or configuration claims.

### Task 2: 重写首屏以兑现反直觉点击承诺

**Files:**
- Modify: `content/2026-07-21-FFN/draft.md`

- [ ] **Step 1: 更新 frontmatter 标题与摘要。**

Replace the title with:

```yaml
title: "Attention都够了，为什么还要FFN？"
```

Replace `digest` with a two-sentence promise containing all three terms “前馈网络”, “FFN”, and “注意力”: attention first writes context into each token; FFN then independently expands, gates, and projects that contextualized representation.

- [ ] **Step 2: 替换“驱动问题”开头的前三段。**

Open with the title’s contradiction instead of a paper-title explanation. Within the first three paragraphs, state both of these sentences in equivalent natural Chinese:

```text
注意力已经把别的 token 的线索汇进当前 token；FFN 不再开圆桌，却负责把这份带上下文的表示继续加工。
逐 token 独立计算，描述的是这一步不互相读取，不是说它没有上下文。
```

- [ ] **Step 3: 保留快速前情引导而不重讲 Q/K/V。**

Add one sentence linking the existing attention article if its WeChat URL is available in the project; otherwise mark it `（待发布）`. The sentence must make clear that readers with Attention 基础 can continue directly and that the link is only a refresher.

- [ ] **Step 4: 进行首屏可读性检查。**

Run: `sed -n '1,75p' 2026-07-21-FFN/draft.md`

Expected: title, cover placeholder, contradiction, rapid orientation, and the two-part division of labor all appear before the first formula section.

### Task 3: 让计算与实验服务“独立但有上下文”

**Files:**
- Modify: `content/2026-07-21-FFN/draft.md`
- Modify: `content/2026-07-21-FFN/outline.md`

- [ ] **Step 1: 调整“注意力负责互相看，FFN 负责各自想”段。**

Place the boundary before the formula:

```text
进入 FFN 的 xᵢ 不是孤立的原始词向量；它已经是注意力读取上下文后的表示。FFN 的独立性只限制它此刻不再读取 xⱼ。
```

Keep `yᵢ ＝ f(xᵢ)` directly after this boundary, then retain the distinction between parameter sharing and cross-token interaction.

- [ ] **Step 2: 给 SwiGLU 三个动作增加同一条因果线。**

Keep the existing four Unicode equations. Revise the explanatory paragraph so that “扩张” is a set of candidate transformations for the contextualized representation, “门控” selects them based on this input, and “投影” returns the selected result to `d_model`. Do not claim that individual dimensions map to named semantics.

- [ ] **Step 3: 压缩实验解读，突出扰动结果。**

Keep the complete runnable code and captured output unchanged. Replace repetitive prose with two claims: each row computed alone exactly equals its batch result; perturbing one row leaves the other output exactly unchanged. Immediately state the boundary that earlier/later attention can still propagate context across tokens.

- [ ] **Step 4: 同步更新 outline 的读者问题。**

Set the opening reader question to “Attention 已经汇入上下文，为什么还需要一个不再让 token 交流的 FFN？” Set the experiment reader question to “怎样验证独立计算不等于脱离上下文？” Preserve existing image filenames and their section placements.

### Task 4: 保留极短的真实模型旁注，再将 MoE 改为有因果的旧文回引

**Files:**
- Modify: `content/2026-07-21-FFN/draft.md`

- [ ] **Step 1: 将当前国产模型配置字段清单压缩为经核验的一条旁注。**

Before editing, open the current official Hugging Face `config.json` for the priority model available at execution time. Retain only the exact `hidden_size` and `hidden_act` values present in that source, plus the direct source link. State that these fields show the model's token-representation width and activation selection; do not infer layer-by-layer MoE deployment, knowledge locations, or capability causality.

- [ ] **Step 2: 以两段文字重写 Dense FFN → MoE。**

Use this factual relationship:

```text
Dense FFN 让每个 token 都经过同一套扩张、门控、投影；MoE 则让路由器为当前 token 选择少数专家 FFN，再汇总它们的输出。
```

Then explain that the FFN article supplies the prerequisite for understanding how real models organize FFN, and link the existing published DeepSeek MoE WeChat article. Do not re-explain router scores, load balancing, or model configuration.

- [ ] **Step 3: 检查回引位置的承接。**

Run: `rg -n -C 3 'MoE|专家|DeepSeek' 2026-07-21-FFN/draft.md`

Expected: MoE follows the FFN explanation and contains one valid `https://mp.weixin.qq.com/s/` link; the concise model aside contains only source-supported `hidden_size` and `hidden_act` claims.

### Task 5: 统一封面、目录与结尾表述

**Files:**
- Modify: `content/2026-07-21-FFN/prompts/00-cover-ffn.md`
- Modify: `content/2026-07-21-FFN/draft.md`
- Modify: `content/2026-07-21-FFN/outline.md`

- [ ] **Step 1: 更新封面 prompt 源。**

Keep the required 21:9 cinematic composition and insert the exact text request `不交流，最费算力？`. Verify that the prompt includes no date, year, parameter count, or claim absent from the article. Do not submit image generation.

- [ ] **Step 2: 统一结尾回扣。**

Revise the final recap to state: attention writes relevant context into each token; FFN independently transforms that contextualized token; residual and normalization connect it safely to the rest of the block. Keep the existing open comment question but ensure it asks about normalization or MoE only if its wording follows directly from this recap.

- [ ] **Step 3: 同步 outline 标题、主问题、MoE 职责与封面文案。**

Make `outline.md` use exactly the same title and hook as `draft.md` and `00-cover-ffn.md`. Describe MoE as an old-article bridge, not as a model-configuration evidence section.

### Task 6: 执行改稿核查并完成交接

**Files:**
- Verify: `content/2026-07-21-FFN/draft.md`
- Verify: `content/2026-07-21-FFN/outline.md`
- Verify: `content/2026-07-21-FFN/prompts/00-cover-ffn.md`

- [ ] **Step 1: 检查标题长度、关键词与数学格式。**

Run:

```bash
printf '%s' 'Attention 都够了，为什么还要 FFN？' | wc -m
rg -n '\$\$?|\\\\\(|\\\\\[' 2026-07-21-FFN/draft.md
rg -n '前馈网络|FFN|SwiGLU' 2026-07-21-FFN/draft.md
```

Expected: title length no more than 22 characters; no LaTex delimiter matches; each required keyword appears.

- [ ] **Step 2: 检查文章承诺与回引边界。**

Run:

```bash
rg -n '独立|上下文|扰动|MoE|https://mp.weixin.qq.com/s/' 2026-07-21-FFN/draft.md
rg -n 'hidden_size|hidden_act|moe_intermediate_size|n_routed_experts|num_experts_per_tok' 2026-07-21-FFN/draft.md
```

Expected: first command shows the misconception reversal, perturbation evidence, and published links; second command contains only `hidden_size` and `hidden_act` from the verified model aside, with none of the MoE-routing field names.

- [ ] **Step 3: 复验代码、配图来源和 prompt 一致性。**

Run:

```bash
python3 2026-07-21-FFN/experiment.py > /tmp/ffn-refinement-output.txt
diff -u 2026-07-21-FFN/experiment-output.txt /tmp/ffn-refinement-output.txt
find 2026-07-21-FFN/prompts -maxdepth 1 -type f -name '*.md' | wc -l
rg -n '不交流，最费算力？|Attention都够了，为什么还要FFN？' 2026-07-21-FFN/{draft.md,outline.md,prompts/00-cover-ffn.md}
```

Expected: experiment diff is empty; five prompt sources exist; title/hook references agree where applicable.

- [ ] **Step 4: Review the scoped diff.**

Run: `git diff -- 2026-07-21-FFN .grill/ffn-click-and-context.md`

Expected: changes are confined to the FFN article, its cover source prompt, and the discussion log; no image-generation task is submitted.
