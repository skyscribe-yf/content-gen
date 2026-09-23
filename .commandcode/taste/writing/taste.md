# Article Writing Style

- Merge overly fragmented one-sentence paragraphs, especially at article openings; text should be cohesive blocks, not tiny staccato paragraphs. Confidence: 0.9
- Prefers a relaxed, chat-like, natural tone; avoid AI-flavored "不是…而是…" sentence patterns and stiff wording. Confidence: 0.8
- Do not use the "墙" (wall) metaphor in articles. Confidence: 0.8
- Introduce complex math/technical concepts with simple intuition, analogy, and minimal formulas before going deeper; keep math simple enough for the lay reader and ensure every formula renders correctly (no garbled/mis-rendered math). Confidence: 0.9
- Always add links back to previous series articles (钩子) where relevant, and end with a brief preview/teaser of the next article; openings should invite the reader in and connect with them. Confidence: 0.9
- End-of-article series lists must include every article in the series (and only that series — don't mix in articles from other series); a final article should recap the whole series. Confidence: 0.8
- Prefer the author's real data (e.g., records in ~/srcs/token-stats/) over fabricated examples; be honest with readers about data provenance. Confidence: 0.9
- Prefer concrete, real examples (e.g., DeepSeek v4's actual implementation) and small real experiments over abstract illustrations. Confidence: 0.8
- Err on the side of MORE illustrations in dry/technical articles — add a concept image to each derivation-heavy section rather than leaving long stretches of pure text ("配图可以多一点，因为文章比较枯燥"). Confidence: 0.7
- Include engaging real-world anecdotes/stories (e.g., the strawberry story, Westworld) to boost interest; only lightly foreshadow future topics — tease, don't dive in. Confidence: 0.8
- Verify specific facts — years, numbers, and historical claims (e.g., InstructGPT vs ChatGPT) — with search before including them. Confidence: 0.9
- Audience includes students, programmers, and hobbyists interested in LLM fundamentals, not just practitioners; avoid assuming advanced background, but keep some simple math in. Confidence: 0.8
- Titles must satisfy SEO requirements; adjust titles accordingly. Confidence: 0.7
- Topics with several distinct "why" answers are split into a multi-part series of independently readable articles (each with its own hook and title, no "上/下篇" framing) rather than one long piece. Confidence: 0.7
- Placeholder links are acceptable in drafts, to be replaced with real URLs later. Confidence: 0.6
Confidence: 0.7
- For math/technical deep dives, expects the full derivation chain (derive rather than state results); treats "深入/depth" as derivation density, not article length. Confidence: 0.7
- Clever metaphors/analogies alone are not satisfying: articles must show *why* something works, down to the underlying math (he cites fancy course analogies that left him "稀里糊涂" as the failure mode to avoid). Ground intuition in the actual derivation. Confidence: 0.7
- Anchors specific numbers on open-source/open-weight models with publicly verifiable configs (e.g., HuggingFace weights, official repos); closed-source products are used only as experiential anchors, with numbers from official statements. Confidence: 0.6
- Views intimidating technical naming (e.g., "ELBO/变分下界") as the real barrier to non-experts, not the underlying math; favors content that demystifies the jargon and reassures readers they don't need advanced prerequisites (variational calculus, higher statistics) to follow diffusion/generation — while noting studying them "doesn't hurt". Confidence: 0.6
- Favors "祛魅" framing that reduces advanced-looking derivation steps to elementary techniques the reader already learned (e.g., the posterior derivation is "just middle-school completing the square in a different form"), explicitly flagging such payload steps so readers don't stall on them. Confidence: 0.6
- Grounds "why does this work?" explanations in already-established properties rather than new machinery (e.g., completing the square works because a Gaussian is fully determined by its first two moments) — connect the trick back to the property it relies on. Confidence: 0.55
- When a derivation reuses a concept covered in an earlier article (e.g., the beautiful properties of the Gaussian), reference/link that earlier piece instead of re-explaining it from scratch. Confidence: 0.55
- If the author has no genuine firsthand experience for a voice/anecdote slot, he prefers to skip it (跳过) and let the passage cite the paper's conclusion, rather than inventing or forcing a personal anecdote. Confidence: 0.6
