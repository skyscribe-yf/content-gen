import copy
import json
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import wechat_audit_log as audit


SEED = ROOT / "docs/wechat-data-audit-log.json"


class AuditLogTests(unittest.TestCase):
    def seed(self):
        return json.loads(SEED.read_text(encoding="utf-8"))

    def write_log(self, directory, log):
        path = Path(directory) / "audit.json"
        path.write_text(json.dumps(log, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return path

    def changed_snapshot(self, log, collected_at="2026-07-22T10:00:00+08:00"):
        snapshot = copy.deepcopy(log["audits"][0])
        snapshot["collectedAt"] = collected_at
        snapshot["content"]["readers30d"] = 2000
        snapshot["users"]["daily"]["new"] = 12
        snapshot["income"]["overview"]["programmaticRevenue"] = 8.25
        snapshot["income"]["overview"]["cumulativeRevenue"] = 8.25
        return snapshot

    def test_validate_accepts_seed_log(self):
        self.assertEqual(audit.validate_log(self.seed()), [])

    def test_append_rejects_duplicate_collected_at_without_changing_file(self):
        with TemporaryDirectory() as directory:
            path = self.write_log(directory, self.seed())
            before = path.read_bytes()
            with self.assertRaises(ValueError):
                audit.append_snapshot(path, self.seed()["audits"][0])
            self.assertEqual(path.read_bytes(), before)

    def test_append_round_trip_and_latest(self):
        with TemporaryDirectory() as directory:
            log = self.seed()
            path = self.write_log(directory, log)
            snapshot = self.changed_snapshot(log)
            audit.append_snapshot(path, snapshot)
            latest = audit.latest_snapshot(audit.load_log(path))
            self.assertEqual(latest["collectedAt"], "2026-07-22T10:00:00+08:00")
            self.assertEqual(latest["content"]["readers30d"], 2000)

    def test_show_date_uses_latest_snapshot_on_that_local_date(self):
        with TemporaryDirectory() as directory:
            log = self.seed()
            path = self.write_log(directory, log)
            audit.append_snapshot(path, self.changed_snapshot(log, "2026-07-22T10:00:00+08:00"))
            audit.append_snapshot(path, self.changed_snapshot(log, "2026-07-22T11:00:00+08:00"))
            found = audit.snapshot_for_date(audit.load_log(path), "2026-07-22")
            self.assertEqual(found["collectedAt"], "2026-07-22T11:00:00+08:00")

    def test_compare_returns_core_deltas(self):
        old = self.seed()["audits"][0]
        new = self.changed_snapshot(self.seed(), "2026-07-22T10:00:00+08:00")
        result = audit.compare_snapshots(old, new)
        self.assertEqual(result["metrics"]["readers30d"]["delta"], 78)
        self.assertEqual(result["metrics"]["dailyNewFollowers"]["delta"], 3)
        self.assertEqual(result["metrics"]["programmaticRevenue"]["delta"], 1.06)

    def test_invalid_percentage_and_negative_count_are_rejected(self):
        snapshot = self.seed()["audits"][0]
        snapshot["content"]["sources"]["recommendation"] = 101
        snapshot["content"]["daily"]["reads"] = -1
        errors = audit.validate_snapshot(snapshot)
        self.assertTrue(any("recommendation" in error for error in errors))
        self.assertTrue(any("reads" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
