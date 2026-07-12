# Task Plan: 2026-07-21 FFN article draft

## Goal
Create a verified first draft for the scheduled FFN article, including the runnable numerical example, current-model evidence, and a compliant image plan.

## Current Phase
Phase 5 — delivery

## Phases

### Phase 1: Requirements and design validation
- [x] Complete the author interview and record the grill log.
- [x] Confirm title, schedule, scope, series boundaries, and teaching metaphor.
- [x] Present the proposed article design and obtain approval.
- [x] Obtain author review of the written design specification.
- [x] Create a task-level execution plan.
- **Status:** complete

### Phase 2: Evidence and experiment preparation
- [x] Verify current Chinese-model configuration data from primary sources.
- [x] Implement and run the fixed-matrix FFN example before inserting it in prose.
- [x] Record cited facts and output in findings.md.
- **Status:** complete

### Phase 3: Draft and visual-source plan
- [x] Create `2026-07-21-FFN/` with outline, draft, and prompt-source files.
- [x] Draft the article with Unicode-only mathematics and series links.
- [x] Define at least four image prompts; do not generate images in this phase.
- **Status:** complete

### Phase 4: Quality review
- [x] Run article-quality checks for accuracy, logic, runnable code, localization, images, and calls to action.
- [x] Verify date directory, title length, keywords, and link rules.
- **Status:** complete

### Phase 5: Delivery
- [x] Hand off the draft and identify remaining publishing assets.
- **Status:** complete

## Decisions Made
| Decision | Rationale |
|---|---|
| Publish 2026-07-21 | Follows the 2026-07-19 attention article and preserves the minimum two-day interval. |
| Use the “roundtable → thinking room” metaphor | Clearly distinguishes cross-token attention from per-token FFN work. |
| Use a fixed-matrix numerical example | Lets readers verify feature gating rather than inspect random output. |
| Avoid a spec commit in this session | The shared worktree has extensive unrelated modifications; committing risks including user work. |

## Errors Encountered
| Error | Attempt | Resolution |
|---|---:|---|
| Looked for title guidance at `content/docs/` | 1 | Located the project documentation at `../docs/article-title-seo.md`. |
