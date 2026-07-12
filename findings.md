# Findings: WeChat Backend Audit — 2026-07-11

## Requirements

- Refresh WeChat Official Account backend data and derive history-based insights.
- Update project documentation without treating account-level metrics as article-level causal evidence.

## Backend Snapshot

- Content analysis covers 2026-06-11 to 2026-07-10: 628 unique readers.
- Traffic mix: recommendation 32.8%, chat sessions 27.4%, official-account homepage 26.1%, Moments 8.6%, account messages 7.0%, other 5.6%, Search 1.4%.
- 2026-07-10 daily metrics: 152 reads, 18 shares, 15 comments.
- Article table: loss function 150, backpropagation 119, Adam 105, residual connection 92, Softmax 61, long-context 38, gradient descent 35, old agile article 25.
- User analysis ends on 2026-07-10: 141 cumulative followers; 15 new, 0 unfollows, and 15 net new that day. Acquisition mix: article page 76 (53.9%), other 33 (23.4%), card sharing 26 (18.44%), Search 5 (3.55%), QR 1 (0.71%).
- The live dashboard showed 142 total users and a new MoE article published on 2026-07-11. Neither is included in the daily analytics cutoff.

## Decisions

| Decision | Rationale |
|---|---|
| Mark Adam's 105 reads as same-day, roughly 12-hour data | It was published at 11:40 on 2026-07-10, while the report ends at midnight. |
| Treat 2026-07-09 to 2026-07-11 as a cadence exception, not evidence for a title result | Consecutive publication confounds distribution and violates the documented two-day interval. |

## Issues Encountered

| Issue | Resolution |
|---|---|
| Stored cookie initially returned “please log in again” | Injected the saved cookie into Chromium through CDP, then reloaded the homepage. |
