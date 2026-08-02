# Task Plan: 2026-07-28–29 WeChat publishing

## Goal

Publish the two scheduled 大模型原理 articles at 20:00 Asia/Shanghai:

| Article | Publish time | Current status |
|---|---|---|
| Kimi K3 架构全貌 | 2026-07-28 20:00 | scheduled |
| SFT 微调 | 2026-07-29 20:00 | scheduled |

## Current Phase

Phase 2 — pre-publish verification

## Phases

### Phase 1: Confirm and record the schedule

- [x] Confirm Kimi K3 is the 2026-07-28 20:00 article.
- [x] Move SFT to 2026-07-29 20:00.
- [x] Align the SFT directory name and frontmatter with its publish date.
- [x] Mark both articles `scheduled` in `draft-status.yaml`.
- **Status:** complete

### Phase 2: Pre-publish verification

- [ ] Run the final article-quality and publish-preflight checks for Kimi K3.
- [ ] Confirm Kimi K3 has `00-cover.png`, correct image paths, topic tags, and no pending links.
- [ ] Run the final article-quality and publish-preflight checks for SFT.
- [ ] Confirm SFT has `00-cover.png`, correct image paths, topic tags, and no pending links.
- **Status:** in_progress

### Phase 3: Publish and backfill records

- [ ] Publish Kimi K3 at 2026-07-28 20:00 and immediately record its WeChat URL.
- [ ] Publish SFT at 2026-07-29 20:00 and immediately record its WeChat URL.
- [ ] Change each status to `published` only after the URL is recorded.
- **Status:** pending

## Decisions Made

| Decision | Rationale |
|---|---|
| Publish Kimi K3 first on 2026-07-28 at 20:00 | It is the current Kimi K3 architecture hot-topic insertion. |
| Publish SFT on 2026-07-29 at 20:00 | Preserve the daily 20:00 cadence while allowing the hot-topic article to go first. |
| Use absolute timestamps with Asia/Shanghai timezone | Avoid ambiguity around “today” and “tomorrow”. |

## Blocking Checks

- Kimi K3: `weixin.md`, outline, and `00-cover.png` are present; final checks remain.
- SFT: `draft.md`, `weixin.md`, and `00-cover.png` are present; final checks remain.
