# FFN after Attention — Article Design

## Purpose

Create the fifth article in the “大模型原理” series. It answers the question left by the attention article: if attention lets tokens exchange context, why does every Transformer block still need a feed-forward network (FFN)?

The article must give readers a durable mental model: **attention communicates across tokens; FFN transforms each token independently with shared nonlinear computation.**

## Audience and promise

Readers have completed the series articles on BPE, embeddings, positional encoding, and attention. They know Q/K/V at a conceptual level, but may assume attention performs all of a Transformer’s “thinking”.

Title: **Attention都够了，为什么还要FFN？**

The article promises a concrete explanation of FFN processing, not a claim that FFN alone makes the final prediction or literally stores one fact per neuron. Its intended cognitive reversal is more specific: **an FFN processes tokens independently at this step, yet it is not context-free, because attention has already written context into each token representation.**

The cover uses a question-style hook of no more than eight Chinese characters: **不交流，最费算力？**

## Narrative approach

Three approaches were considered:

1. Formula-first MLP explanation — precise, but risks reading like a textbook and does not resolve the misconception left by the attention article.
2. **Conflict-driven handoff from attention (selected)** — begin with “Attention Is All You Need”; continue the previous “roundtable” analogy into a shared private “thinking room”; then introduce the computation.
3. Model-scale-first explanation — practical, but parameters and implementation details would arrive before the reader knows what the sublayer is for.

The selected approach is used throughout: at the roundtable, attention lets every participant hear relevant remarks. Next, every participant visits the same thinking room alone. That room is the shared FFN: it does not mix tokens again, but transforms each token’s current representation.

## Article structure

1. **Opening conflict and rapid orientation.** Ask why a supposedly sufficient attention mechanism is followed by a large FFN. In two or three sentences, reconnect to the prior article: attention has already aggregated relevant context into each token; this article asks what happens next.
2. **Division of labor and misconception reversal.** Attention moves relevant contextual information between tokens; FFN applies the same nonlinear transformation separately to each resulting token vector. State explicitly that independent computation does not mean absent context.
3. **How FFN works.** Explain expansion, SwiGLU gating, and projection back to the model dimension. Use Unicode-only formulas. Frame each stage as processing the token's already contextualized representation: expansion creates options, gating selects them, and projection returns the result.
4. **Runnable miniature experiment.** Use fixed matrices, not random values. Retain the two-token perturbation test as the central evidence: changing one row cannot alter the other row inside the FFN. Compress repetitive explanation of the printed values.
5. **Dense FFN to MoE.** State that MoE organizes multiple FFN experts and routes each token to a few of them. Link the existing MoE article as the next step for seeing how real Chinese models organize FFN; do not re-explain routing or enumerate configuration fields.
6. **Next-step preview.** Briefly show where residual connection and normalization sit around the FFN, then reserve their mechanics for article six.

## Boundaries

- Include a short link back to the prior attention article for readers who need the context-aggregation refresher; do not repeat Q/K/V.
- Treat parameterized knowledge as distributed patterns, not a literal lookup database.
- Do not expand into FlashAttention, KV Cache, or a MoE routing tutorial.
- Do not explain residual or normalization mechanics beyond an accurate preview.

## Evidence and quality requirements

- Confirm every factual model configuration, version, parameter count, and date retained in the final text using current primary sources.
- Run the exact code example and retain its output before inserting it.
- Use Chinese-accessible products/models for practical examples.
- Include at least four planned illustrations, distributed across the article. Store prompts as source files; no image generation occurs during drafting.
- Include earlier-series links, a concrete open question for comments, and a follow invitation that states the series value.

## Planned visual sources

1. Roundtable exchange followed by individual thinking rooms.
2. FFN expand → SwiGLU gate → project pipeline.
3. Fixed-matrix experiment showing selected features.
4. Dense FFN alongside MoE’s selected experts.
5. Transformer-block preview locating FFN, residual, and normalization.

## Deliverables

- `.grill/ffn-after-attention.md`
- `2026-07-21-FFN/outline.md`
- `2026-07-21-FFN/draft.md`
- Runnable experiment source and captured output under the article directory.
- `2026-07-21-FFN/prompts/` source prompts for planned illustrations.
