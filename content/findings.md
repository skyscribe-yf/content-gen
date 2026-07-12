# Findings & Decisions

## Requirements
- Deliver a first draft for the 2026-07-21 FFN article in the 大模型原理 series.
- Explain the division of labor: attention communicates across tokens; FFN transforms each token nonlinearly.
- Use title “前馈网络怎么工作？注意力之后还要想一遍”.
- Include a fixed-matrix runnable example and a current Chinese-model configuration reference.
- Bridge to the prior attention, activation-function, and MoE articles; preview normalization and residual connection.

## Research Findings
- The scheduled attention article already covers Q/K/V, causal masking, multi-head attention, and GQA; it explicitly positions FFN as series item five.
- The published MoE article describes MoE as replacing the FFN with routed experts, so the new article should teach dense FFN as the baseline.
- The activation-function article has already introduced SwiGLU and cites `hidden_act: "silu"`; the FFN article should link back rather than repeat gradient derivations.
- Primary source: [DeepSeek-V4-Pro fixed-revision config.json](https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/raw/b5968e9190ef611bbf34a7229255be88a0e937c1/config.json). The fixed revision contains `hidden_size: 7168`, `hidden_act: "silu"`, `moe_intermediate_size: 3072`, `n_routed_experts: 384`, `n_shared_experts: 1`, and `num_experts_per_tok: 6`; the model API reports this revision last modified at 2026-06-22T12:12:50Z.
- The config does not expose a generic `intermediate_size` or gate/up/down projection details; the article explicitly limits claims to configuration declarations.

## Technical Decisions
| Decision | Rationale |
|---|---|
| Explain “knowledge” as distributed reusable patterns | Avoids the inaccurate claim that individual neurons store individual facts. |
| Show residual and normalization only in a preview | Keeps the sixth series article distinct. |
| Use Chinese-model config.json data | Required by project rules and grounds the theory in real architecture. |
| Use conflict-driven handoff from attention | The approved design best resolves the reader’s “attention is everything” misconception. |

## Issues Encountered
| Issue | Resolution |
|---|---|
| Initial relative path for title guidance was wrong | Used `../docs/article-title-seo.md`; no content was changed. |

## Specification Review
- The design contains no TODO/TBD placeholders.
- The selected title is 19 characters, within the 22-character limit.
- Scope remains one article: evidence, one runnable experiment, planned visual sources, and no image generation.

## Verification
- `python3 2026-07-21-FFN/experiment.py` reproduced the captured output exactly.
- The draft has no LaTeX delimiters, contains five image placeholders, and passed checks for the approved title, publication date, verified DeepSeek fields, MoE placeholder link, and residual-article link.
