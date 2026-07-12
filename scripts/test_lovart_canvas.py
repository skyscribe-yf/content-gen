import sys
import subprocess
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


class ChromeLaunchTest(unittest.TestCase):
    def test_chrome_command_uses_external_profile_and_remote_debugging(self):
        command = lovart_canvas.chrome_command(
            chrome="/usr/bin/google-chrome",
            profile=Path("/tmp/lovart-profile"),
            port=9229,
            initial_url="https://www.lovart.ai/canvas",
        )

        self.assertEqual(
            command,
            [
                "/usr/bin/google-chrome",
                "--remote-debugging-port=9229",
                "--user-data-dir=/tmp/lovart-profile",
                "--no-first-run",
                "--no-default-browser-check",
                "https://www.lovart.ai/canvas",
            ],
        )


class FakeCdp:
    def __init__(self):
        self.calls = []

    async def send(self, method, params=None, session_id=None, timeout=15):
        self.calls.append((method, params, session_id))
        return {"sessionId": "session-1"} if method == "Target.attachToTarget" else {}


class PageSessionTest(unittest.IsolatedAsyncioTestCase):
    async def test_configure_downloads_uses_article_image_directory(self):
        cdp = FakeCdp()
        await lovart_canvas.configure_page_session(cdp, "target-1", Path("/tmp/article/images"))

        self.assertIn(
            (
                "Page.setDownloadBehavior",
                {"behavior": "allow", "downloadPath": "/tmp/article/images"},
                "session-1",
            ),
            cdp.calls,
        )


class FakePage:
    def __init__(self, values):
        self.values = values
        self.calls = []

    async def evaluate(self, expression, argument=None):
        self.calls.append((expression, argument))
        return self.values.pop(0)


class LovartUiTest(unittest.IsolatedAsyncioTestCase):
    async def test_clicks_first_visible_candidate_and_raises_when_missing(self):
        page = FakePage([False, True])
        ui = lovart_canvas.LovartCanvasUi(page, Path("/tmp/article/images"))

        await ui.click_first(
            ["[data-testid='nav-generate-menu-button']", "button[aria-label='Generate']"],
            "open generator",
        )

        missing = FakePage([False, False, '<input value="secret"><div>verification required</div>'])
        with self.assertRaisesRegex(lovart_canvas.LovartUiBlocked, "open generator") as caught:
            await lovart_canvas.LovartCanvasUi(missing, Path("/tmp/article/images")).click_first(
                ["one", "two"], "open generator"
            )

        self.assertNotIn("secret", str(caught.exception))
        self.assertIn("verification", str(caught.exception))

    async def test_model_selection_never_clicks_an_unspecified_model_option(self):
        class RecordingPage:
            def __init__(self):
                self.calls = []

            async def evaluate(self, expression, argument=None):
                self.calls.append((expression, argument))
                return argument.get("text") == "GPT Image 2" if isinstance(argument, dict) else False

        page = RecordingPage()
        await lovart_canvas.LovartCanvasUi(page, Path("/tmp/article/images"))._select_model()

        selectors = [argument.get("selector") for _, argument in page.calls if isinstance(argument, dict)]
        texts = [argument.get("text") for _, argument in page.calls if isinstance(argument, dict)]
        self.assertNotIn("[data-testid*='model-option']", selectors)
        self.assertIn("GPT Image 2", texts)


class FakeLovartUi:
    def __init__(self):
        self.created_for = []
        self.generated = []
        self.project_url = "https://www.lovart.ai/canvas?projectId=project-123"

    async def ensure_project(self, name):
        self.created_for.append(name)
        return "project-123"

    async def generate_and_download(self, job):
        self.generated.append(job.fingerprint)
        job.output.parent.mkdir(parents=True, exist_ok=True)
        job.output.write_bytes(b"png")
        return job.output


class OrchestrationTest(unittest.IsolatedAsyncioTestCase):
    async def test_run_records_project_and_skips_completed_job_on_second_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            article = Path(tmp) / "article"
            (article / "prompts").mkdir(parents=True)
            (article / "prompts" / "00-cover.md").write_text("cover", encoding="utf-8")
            ui = FakeLovartUi()

            await lovart_canvas.run_article(article, ui=ui, today="2026-07-12", max_new=8)
            await lovart_canvas.run_article(article, ui=ui, today="2026-07-12", max_new=8)

            self.assertEqual(len(ui.generated), 1)
            self.assertEqual(lovart_canvas.load_manifest(article, "article").project_id, "project-123")

    async def test_dry_run_never_creates_project_or_writes_images(self):
        with tempfile.TemporaryDirectory() as tmp:
            article = Path(tmp) / "article"
            (article / "prompts").mkdir(parents=True)
            (article / "prompts" / "00-cover.md").write_text("cover", encoding="utf-8")
            ui = FakeLovartUi()

            summary = await lovart_canvas.run_article(
                article, ui=ui, today="2026-07-12", max_new=8, dry_run=True
            )

            self.assertEqual([job.aspect_ratio for job in summary.eligible], ["21:9"])
            self.assertEqual(ui.created_for, [])
            self.assertEqual(ui.generated, [])
            self.assertFalse((article / "images").exists())

    async def test_max_new_never_exceeds_eight(self):
        with self.assertRaisesRegex(ValueError, "max-new.*8"):
            await lovart_canvas.run_article(
                Path("/tmp/article"), ui=FakeLovartUi(), today="2026-07-12", max_new=9
            )

    async def test_dry_run_reports_when_ninth_job_exceeds_daily_cap(self):
        with tempfile.TemporaryDirectory() as tmp:
            article = Path(tmp) / "article"
            prompts = article / "prompts"
            prompts.mkdir(parents=True)
            for index in range(9):
                (prompts / f"{index:02d}.md").write_text(f"prompt {index}", encoding="utf-8")

            summary = await lovart_canvas.run_article(
                article, ui=FakeLovartUi(), today="2026-07-12", max_new=8, dry_run=True
            )

            self.assertEqual(len(summary.eligible), 8)
            self.assertTrue(summary.cap_reached)


class CliTest(unittest.TestCase):
    def test_dry_run_works_when_executed_as_a_script(self):
        with tempfile.TemporaryDirectory() as tmp:
            article = Path(tmp) / "article"
            (article / "prompts").mkdir(parents=True)
            (article / "prompts" / "00-cover.md").write_text("cover", encoding="utf-8")

            result = subprocess.run(
                [
                    sys.executable,
                    str(Path(lovart_canvas.__file__)),
                    "--article",
                    str(article),
                    "--dry-run",
                ],
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Dry run: article", result.stdout)
            self.assertIn("00-cover.md (21:9)", result.stdout)


if __name__ == "__main__":
    unittest.main()
