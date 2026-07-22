import copy
import json
import sys
import unittest
from html.parser import HTMLParser
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import wechat_audit_report as report


SEED = ROOT / "docs/wechat-data-audit-log.json"


class DocumentParser(HTMLParser):
    pass


class AuditReportTests(unittest.TestCase):
    def seed(self):
        log = json.loads(SEED.read_text(encoding="utf-8"))
        log["audits"] = log["audits"][:1]
        return log

    def snapshot(self, log, collected_at):
        snapshot = copy.deepcopy(log["audits"][0])
        snapshot["collectedAt"] = collected_at
        return snapshot

    def test_default_selects_latest_snapshot(self):
        log = self.seed()
        selected = report.select_snapshot(log)
        self.assertEqual(selected["collectedAt"], "2026-07-21T14:08:34+08:00")

    def test_date_selects_latest_snapshot_on_local_date(self):
        log = self.seed()
        log["audits"].extend([
            self.snapshot(log, "2026-07-22T09:00:00+08:00"),
            self.snapshot(log, "2026-07-22T11:00:00+08:00"),
        ])
        selected = report.select_snapshot(log, "2026-07-22")
        self.assertEqual(selected["collectedAt"], "2026-07-22T11:00:00+08:00")

    def test_previous_snapshot_and_deltas(self):
        log = self.seed()
        previous = self.snapshot(log, "2026-07-20T14:00:00+08:00")
        previous["content"]["readers30d"] = 1800
        previous["users"]["daily"]["new"] = 5
        previous["income"]["overview"]["programmaticRevenue"] = 6.09
        log["audits"].insert(0, previous)
        current = report.select_snapshot(log)
        self.assertIs(report.previous_snapshot(log, current), previous)
        deltas = report.compute_deltas(previous, current)
        self.assertEqual(deltas["readers30d"]["delta"], 122)
        self.assertEqual(deltas["dailyNewFollowers"]["delta"], 4)
        self.assertEqual(deltas["programmaticRevenue"]["delta"], 1.10)

    def test_no_previous_snapshot_has_no_baseline(self):
        log = self.seed()
        current = report.select_snapshot(log)
        self.assertIsNone(report.previous_snapshot(log, current))
        self.assertEqual(report.compute_deltas(None, current), {})

    def test_render_contains_dashboard_and_detail_sections(self):
        html = report.render_report(self.seed())
        for text in ("公众号审计报告", "数解AI", "1,922", "学习率怎么自动调", "文中广告", "暂无基线"):
            self.assertIn(text, html)
        self.assertNotIn("https://", html)
        self.assertNotIn("http://", html)
        DocumentParser().feed(html)

    def test_render_escapes_titles_and_embeds_snapshot_safely(self):
        log = self.seed()
        log["audits"][0]["content"]["articles"][0]["title"] = '<script>alert("x")</script>'
        html = report.render_report(log)
        self.assertIn("&lt;script&gt;alert(&quot;x&quot;)&lt;/script&gt;", html)
        self.assertNotIn('<script>alert("x")</script>', html)
        self.assertIn('id="audit-data"', html)
        DocumentParser().feed(html)

    def test_article_income_is_rendered(self):
        log = self.seed()
        log["audits"][0]["income"]["articleIncome"] = {
            "scope": "仅展示文章发布后7日内的收入数据",
            "articles": [{
                "date": "2026-07-10",
                "title": "测试文章",
                "original": True,
                "revenue": 0.8,
                "slots": {"inline": {"revenue": 0.46, "share": 57.5}},
            }],
        }
        html = report.render_report(log)
        self.assertIn("文章广告收入", html)
        self.assertIn("测试文章", html)
        self.assertIn("¥0.46", html)
        DocumentParser().feed(html)

    def test_generate_report_writes_parseable_utf8_file(self):
        with TemporaryDirectory() as directory:
            output = Path(directory) / "report.html"
            result = report.generate_report(SEED, output)
            self.assertEqual(result, output)
            generated = output.read_text(encoding="utf-8")
            self.assertIn("数解AI", generated)
            DocumentParser().feed(generated)


if __name__ == "__main__":
    unittest.main()
