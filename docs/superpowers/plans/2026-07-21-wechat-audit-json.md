# WeChat Audit JSON Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Persist WeChat audit numbers locally in a validated JSON log and provide a dependency-free Python CLI for append, validation, loading, and date comparison.

**Architecture:** `docs/wechat-data-audit-log.json` is the canonical numeric store. `docs/wechat-data-audit-log.schema.json` describes the log and snapshot shape. `scripts/wechat_audit_log.py` implements the small command-line interface with Python's standard library; Markdown docs remain human-readable summaries and point to the JSON source of truth.

**Tech Stack:** Python 3 standard library (`argparse`, `datetime`, `json`, `pathlib`, `tempfile`, `unittest`), JSON Schema Draft 2020-12.

---

### Task 1: Create the canonical audit snapshot

**Files:**
- Create: `docs/wechat-data-audit-log.json`
- Create: `docs/wechat-data-audit-log.schema.json`

- [ ] **Step 1: Write the current snapshot as normalized JSON**

Create the top-level shape below and populate every value from the 2026-07-21 audit. Use English stable keys for queries, preserve Chinese article titles, use `null` for unavailable percentages/eCPM, and keep the 7-day income period separate from the content period:

```json
{
  "schemaVersion": 1,
  "account": "数解AI",
  "audits": [
    {
      "collectedAt": "2026-07-21T14:08:34+08:00",
      "dataThrough": "2026-07-20",
      "periods": {
        "content": {"from": "2026-06-21", "to": "2026-07-20"},
        "users": {"from": "2026-06-20", "to": "2026-07-20"},
        "income": {"from": "2026-07-14", "to": "2026-07-20"}
      },
      "content": {
        "readers30d": 1922,
        "daily": {"date": "2026-07-20", "reads": 148, "shares": 21, "comments": 2},
        "sources": {
          "recommendation": 57.5,
          "accountHome": 15.5,
          "chatSession": 13.9,
          "officialMessage": 7.3,
          "other": 7.2,
          "moments": 4.2,
          "search": 1.1
        },
        "articles": []
      },
      "users": {
        "daily": {"date": "2026-07-20", "new": 9, "cancelled": 0, "net": 9, "total": 241},
        "channelTotal": 242,
        "channels": {},
        "trend": []
      },
      "income": {
        "overview": {
          "cumulativeRevenue": 7.19,
          "programmaticRevenue": 7.19,
          "yesterdayIncrement": 0.34,
          "mutualSelectionRevenue": 0.0,
          "commerceRevenue": 0.0
        },
        "articleIncomeAvailable": false,
        "slots": {}
      },
      "notes": ["渠道构成合计为 242，用户分析累计关注为 241，保留后台原始口径。"]
    }
  ]
}
```

Replace the illustrative empty arrays/objects with the complete current article table, user channel table, 07/01–07/20 user trend, and four income-slot summaries/daily rows from `docs/wechat-data-audit-log.md`.

- [ ] **Step 2: Define the JSON Schema**

Create a Draft 2020-12 schema with `$defs` for `date`, `dateTime`, `percentage`, `nonNegativeInteger`, `money`, `period`, `content`, `users`, `incomeSummary`, `incomeSlot`, and `audit`. Require the top-level `schemaVersion`, `account`, and `audits`; require each audit's `collectedAt`, `dataThrough`, `periods`, `content`, `users`, `income`, and `notes`; set `additionalProperties: false` for fixed objects and use typed `additionalProperties` for extensible source/channel/slot maps.

- [ ] **Step 3: Verify the seed files parse**

Run:

```bash
python -m json.tool docs/wechat-data-audit-log.json >/dev/null
python -m json.tool docs/wechat-data-audit-log.schema.json >/dev/null
```

Expected: both commands exit 0 with no output.

### Task 2: Write the CLI tests first

**Files:**
- Create: `tests/test_wechat_audit_log.py`

- [ ] **Step 1: Add tests for the public CLI functions**

Use `unittest` and `tempfile.TemporaryDirectory`. Import `scripts/wechat_audit_log.py` after it exists. Add these six test methods with concrete assertions:

- `test_validate_accepts_seed_log`: load the seed JSON and assert `validate_log` returns an empty list.
- `test_append_rejects_duplicate_collected_at_without_changing_file`: append the existing audit again, assert `ValueError`, and assert the file bytes are unchanged.
- `test_append_round_trip_and_latest`: append a later snapshot with `readers30d` 2000, then assert `latest_snapshot` returns that snapshot.
- `test_show_date_uses_latest_snapshot_on_that_local_date`: append two snapshots with the same local date and different times, then assert the later one is returned.
- `test_compare_returns_core_deltas`: compare snapshots with readers 1922/2000, new followers 9/12, and cumulative revenue 7.19/8.25; assert deltas 78, 3, and 1.06.
- `test_invalid_percentage_and_negative_count_are_rejected`: mutate a source percentage to 101 and a read count to -1; assert both mutations produce validation errors.

The fixture should copy the seed log to a temporary path, deep-copy the seed snapshot before mutation, and use `json.dumps(snapshot, ensure_ascii=False)` when writing test input snapshots.

- [ ] **Step 2: Run the tests before implementation**

Run:

```bash
python -m unittest discover -s tests -p 'test_wechat_audit_log.py' -v
```

Expected: FAIL because `scripts/wechat_audit_log.py` does not yet exist.

### Task 3: Implement the dependency-free CLI

**Files:**
- Create: `scripts/wechat_audit_log.py`

- [ ] **Step 1: Implement load and validation helpers**

Implement these importable functions with the exact signatures: `load_log(path: Path) -> dict`, `validate_log(log: dict) -> list[str]`, `validate_snapshot(snapshot: dict) -> list[str]`, `append_snapshot(path: Path, snapshot: dict) -> None`, `latest_snapshot(log: dict) -> dict | None`, `snapshot_for_date(log: dict, date: str) -> dict | None`, and `compare_snapshots(old: dict, new: dict) -> dict`.

`validate_log` must check schema version, required objects, ISO dates with timezone, non-negative counts/money, and 0–100 percentages. It must return human-readable errors instead of modifying input. `append_snapshot` must reject duplicate `collectedAt`, validate before writing, write to a sibling temporary file, then replace the original with `Path.replace()`.

- [ ] **Step 2: Implement the CLI parser and output**

Use `argparse` with subcommands `validate`, `append`, `latest`, `show`, and `compare`. Print JSON to stdout for data commands; print `valid` for successful validation; return exit code 2 for invalid input or missing dates. `show` and `compare` must select the latest snapshot whose `collectedAt` local date equals the requested date.

- [ ] **Step 3: Run the tests after implementation**

Run:

```bash
python -m unittest discover -s tests -p 'test_wechat_audit_log.py' -v
```

Expected: all tests PASS.

- [ ] **Step 4: Run manual CLI checks**

Run:

```bash
python scripts/wechat_audit_log.py validate
python scripts/wechat_audit_log.py latest | python -m json.tool >/dev/null
python scripts/wechat_audit_log.py show --date 2026-07-21 | python -m json.tool >/dev/null
```

Expected: `valid`, then the two JSON commands exit 0.

### Task 4: Integrate the local log into the audit skill and docs

**Files:**
- Modify: `.agents/skills/wechat-data-audit/SKILL.md`
- Modify: `docs/wechat-data-audit-log.md`
- Modify: `AGENTS.md`

- [ ] **Step 1: Add the local-history phase to the skill**

Add a phase before Cookie login:

```text
Phase 0: Load local audit history
1. Run `python scripts/wechat_audit_log.py latest` before collecting data.
2. Use the latest snapshot as the comparison baseline; do not rely on the backend for older windows.
3. After collection, normalize the new snapshot and save it to `/tmp/audit-snapshot.json`.
4. Run `python scripts/wechat_audit_log.py append --input /tmp/audit-snapshot.json`.
5. Run `python scripts/wechat_audit_log.py validate` before updating insight documents.
6. Treat `docs/wechat-data-audit-log.json` as the numeric source of truth; Markdown documents contain interpretation.
```

Document the stable key mapping for content, users, and income slots, and state that missing eCPM/CTR values are `null`.

- [ ] **Step 2: Mark the Markdown log as a human-readable view**

Add a note near the top of `docs/wechat-data-audit-log.md` linking to `wechat-data-audit-log.json` and stating that future numeric updates must append JSON first.

- [ ] **Step 3: Make the local JSON log discoverable**

Add to `AGENTS.md` under the WeChat data audit rules:

```markdown
- 数字事实源：[`docs/wechat-data-audit-log.json`](docs/wechat-data-audit-log.json)，结构见同名 `.schema.json`，操作脚本为 `scripts/wechat_audit_log.py`
```

### Task 5: Final verification

**Files:**
- Verify: `docs/wechat-data-audit-log.json`
- Verify: `docs/wechat-data-audit-log.schema.json`
- Verify: `scripts/wechat_audit_log.py`
- Verify: `tests/test_wechat_audit_log.py`
- Verify: `.agents/skills/wechat-data-audit/SKILL.md`

- [ ] **Step 1: Run JSON, unit, CLI, and diff checks**

Run:

```bash
python -m json.tool docs/wechat-data-audit-log.json >/dev/null
python -m json.tool docs/wechat-data-audit-log.schema.json >/dev/null
python -m unittest discover -s tests -p 'test_wechat_audit_log.py' -v
python scripts/wechat_audit_log.py validate
python scripts/wechat_audit_log.py compare --from 2026-07-21 --to 2026-07-21

git diff --check -- AGENTS.md .agents/skills/wechat-data-audit/SKILL.md docs/wechat-data-audit-log.md docs/wechat-data-audit-log.json docs/wechat-data-audit-log.schema.json scripts/wechat_audit_log.py tests/test_wechat_audit_log.py
```

Expected: JSON parsing succeeds, all unit tests pass, validation prints `valid`, compare prints zero deltas for the same snapshot, and the targeted diff check exits 0.

- [ ] **Step 2: Confirm the skill workflow references every new file**

Run:

```bash
rg -n 'wechat-data-audit-log|wechat_audit_log.py|Phase 0|append --input|validate' .agents/skills/wechat-data-audit/SKILL.md AGENTS.md docs/wechat-data-audit-log.md
```

Expected: matches for the JSON log, schema, script, local-history phase, append command, and validation command.
