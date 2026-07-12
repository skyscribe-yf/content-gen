import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lovart_canvas


class PromptDiscoveryTest(unittest.TestCase):
    def make_article(self, root: Path) -> Path:
        article = root / "2026-07-20-tokenizer"
        (article / "prompts").mkdir(parents=True)
        (article / "weixin.md").write_text(
            '---\ntitle: "Tokenizer：AI 如何切词"\n---\n正文', encoding="utf-8"
        )
        return article

    def test_discovers_sorted_prompts_strips_front_matter_and_derives_outputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            article = self.make_article(Path(tmp))
            (article / "prompts" / "02-vector.md").write_text("vector prompt", encoding="utf-8")
            (article / "prompts" / "00-cover.md").write_text(
                "---\nartist: author\n---\ncover prompt", encoding="utf-8"
            )

            plan = lovart_canvas.discover_article(article)

            self.assertEqual(plan.project_name, "Tokenizer：AI 如何切词")
            self.assertEqual(
                [(job.source.name, job.aspect_ratio, job.output.name, job.prompt) for job in plan.jobs],
                [
                    ("00-cover.md", "21:9", "00-cover.png", "cover prompt"),
                    ("02-vector.md", "1:1", "02-vector.png", "vector prompt"),
                ],
            )

    def test_falls_back_to_directory_name_and_rejects_empty_prompt(self):
        with tempfile.TemporaryDirectory() as tmp:
            article = Path(tmp) / "2026-07-20-tokenizer"
            (article / "prompts").mkdir(parents=True)
            (article / "prompts" / "01-empty.md").write_text("---\na: b\n---\n", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "01-empty.md.*empty"):
                lovart_canvas.discover_article(article)


class ManifestTest(unittest.TestCase):
    def test_completed_and_pending_fingerprints_are_not_new_submissions(self):
        job = lovart_canvas.PromptJob(
            Path("00-cover.md"), "same prompt", "21:9", Path("images/00-cover.png")
        )
        manifest = lovart_canvas.Manifest.empty("Article")
        manifest.record_submitted(job, submitted_at="2026-07-12T09:00:00+08:00")
        self.assertEqual(
            lovart_canvas.new_jobs_for_run([job], manifest, today="2026-07-12", retry_failed=False),
            [],
        )

        manifest.mark_completed(job.fingerprint, "images/00-cover.png")
        self.assertEqual(
            lovart_canvas.new_jobs_for_run([job], manifest, today="2026-07-12", retry_failed=False),
            [],
        )

    def test_failed_jobs_need_explicit_retry_and_daily_cap_is_eight(self):
        first = lovart_canvas.PromptJob(Path("01.md"), "one", "1:1", Path("images/01.png"))
        second = lovart_canvas.PromptJob(Path("02.md"), "two", "1:1", Path("images/02.png"))
        manifest = lovart_canvas.Manifest.empty("Article")
        manifest.record_failed(first, "Lovart rejected the prompt")
        self.assertEqual(
            lovart_canvas.new_jobs_for_run([first], manifest, today="2026-07-12", retry_failed=False),
            [],
        )
        self.assertEqual(
            lovart_canvas.new_jobs_for_run([first], manifest, today="2026-07-12", retry_failed=True),
            [first],
        )

        manifest.submissions.extend({"date": "2026-07-12", "fingerprint": str(n)} for n in range(8))
        self.assertEqual(
            lovart_canvas.new_jobs_for_run([second], manifest, today="2026-07-12", retry_failed=False),
            [],
        )

    def test_malformed_manifest_stops_before_browser_launch(self):
        with tempfile.TemporaryDirectory() as tmp:
            article = Path(tmp)
            (article / "lovart-canvas.json").write_text("{not JSON", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "malformed Lovart manifest"):
                lovart_canvas.load_manifest(article, "Article")


if __name__ == "__main__":
    unittest.main()
