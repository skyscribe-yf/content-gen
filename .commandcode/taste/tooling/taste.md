# Tooling

- Source ~/.bash_env to obtain environment variables rather than hardcoding values. Confidence: 0.9
- For the ollama-cloud codex profile, use the ollama-cloud gemma model (e.g., gemma4:31b-cloud) for OCR/image-understanding tasks, routed through a local proxy; don't use external proxies for image inspection. Confidence: 0.8
- When a tool/service seems broken (e.g., mdnice, API keys), don't silently fall back to an alternative or assume credentials expired — retry and investigate the real cause first. Confidence: 0.7
- Image generation via lovart.ai canvas (gpt-image-2): use one lovart project per article and create a new project for each new article; for aspect-ratio issues, input explicit pixel dimensions. Confidence: 0.7
- Do NOT regenerate images based on the agent's own quality judgment — post the draft/images for the user to review and decide; only regenerate what the user explicitly requests (this rule should live in the agent's instructions). Confidence: 0.9
- Save generated cover/images under the article's dated content folder (e.g., content/YYYY-MM-DD-标题/cover.png). Confidence: 0.7
- Git workflow: edit directly on the current branch; commit and push changes when a milestone is done. Confidence: 0.7
- Uses the user's real environment for experiments (autodl GPU, token-stats data); monitor training progress/GPU periodically and save intermediate checkpoints and evidence for article writing. Confidence: 0.7
