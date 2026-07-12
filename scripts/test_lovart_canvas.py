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

    def test_uses_draft_title_when_weixin_source_is_not_created_yet(self):
        with tempfile.TemporaryDirectory() as tmp:
            article = Path(tmp) / "2026-07-21-FFN"
            (article / "prompts").mkdir(parents=True)
            (article / "prompts" / "00-cover.md").write_text("cover", encoding="utf-8")
            (article / "draft.md").write_text('---\ntitle: "FFN article title"\n---\n正文', encoding="utf-8")

            self.assertEqual(lovart_canvas.discover_article(article).project_name, "FFN article title")


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

    def test_deferred_job_is_not_selected_or_counted_as_a_submission(self):
        job = lovart_canvas.PromptJob(Path("00-cover.md"), "cover", "21:9", Path("images/00-cover.png"))
        manifest = lovart_canvas.Manifest.empty("Article")
        manifest.jobs[job.fingerprint] = {"status": "deferred"}

        self.assertEqual(
            lovart_canvas.new_jobs_for_run([job], manifest, today="2026-07-12", retry_failed=True),
            [],
        )


class ArtifactDownloadTest(unittest.TestCase):
    def test_uses_original_lovart_artifact_instead_of_preview_resize(self):
        preview = "https://a.lovart.ai/artifacts/generator/image.png?x-oss-process=image/resize,w_512,m_lfit/format,webp"

        self.assertEqual(
            lovart_canvas.artifact_download_url(preview),
            "https://a.lovart.ai/artifacts/generator/image.png",
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

    def test_chrome_command_can_use_an_existing_proxy_server(self):
        command = lovart_canvas.chrome_command(
            chrome="/usr/bin/google-chrome",
            profile=Path("/tmp/lovart-profile"),
            port=9229,
            initial_url="https://www.lovart.ai/canvas",
            proxy_server="http://127.0.0.1:7890",
        )

        self.assertIn("--proxy-server=http://127.0.0.1:7890", command)

    def test_proxy_from_environment_drops_credentials(self):
        self.assertEqual(
            lovart_canvas.proxy_server_from_environment({"https_proxy": "http://name:secret@127.0.0.1:7890"}),
            "http://127.0.0.1:7890",
        )

    def test_chrome_launch_options_detach_the_visible_browser_from_cli_lifetime(self):
        options = lovart_canvas.chrome_launch_options()

        self.assertTrue(options["start_new_session"])

    def test_finds_running_profile_debug_port_from_process_line(self):
        profile = Path("/tmp/lovart-profile")
        lines = [
            "agent 123 0.0 chrome --remote-debugging-port=41407 "
            "--user-data-dir=/tmp/lovart-profile --no-first-run",
            "agent 124 0.0 chrome --remote-debugging-port=9222 --user-data-dir=/tmp/other-profile",
        ]

        self.assertEqual(lovart_canvas.running_debug_port_from_process_lines(lines, profile), 41407)


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

        self.assertIn(("Page.bringToFront", None, "session-1"), cdp.calls)
        self.assertIn(
            (
                "Page.setDownloadBehavior",
                {"behavior": "allow", "downloadPath": "/tmp/article/images"},
                "session-1",
            ),
            cdp.calls,
        )


class CanvasReadyTest(unittest.IsolatedAsyncioTestCase):
    async def test_waits_for_canvas_root_before_generation_controls(self):
        class LoadingPage:
            def __init__(self):
                self.values = [
                    {"rootLength": 0, "hasLoginFrame": False},
                    {"rootLength": 1200, "hasLoginFrame": False},
                ]

            async def evaluate(self, expression, argument=None):
                return self.values.pop(0)

        await lovart_canvas.wait_for_canvas_ready(LoadingPage(), timeout_seconds=1)


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

    async def test_model_selection_uses_the_live_gpt_image_2_control(self):
        class RecordingPage:
            def __init__(self):
                self.calls = []
                self.model_menu_open = False
                self.model_selected = False

            async def evaluate(self, expression, argument=None):
                self.calls.append((expression, argument))
                selector = argument.get("selector") if isinstance(argument, dict) else None
                if expression == lovart_canvas._CONTROL_VISIBLE:
                    return selector == "[data-testid='generator-model-option-openai/gpt-image-2']" and self.model_menu_open
                if expression == lovart_canvas._MODEL_OPTION_SELECTED:
                    return self.model_selected
                if selector == "[data-testid='generator-model-button']":
                    self.model_menu_open = True
                    return True
                if selector == "[data-testid='generator-model-option-openai/gpt-image-2']":
                    self.model_selected = True
                    return True
                return False

        page = RecordingPage()
        await lovart_canvas.LovartCanvasUi(page, Path("/tmp/article/images"))._select_model()

        selectors = [
            argument.get("selector")
            for expression, argument in page.calls
            if expression == lovart_canvas._CLICK_ELEMENT and isinstance(argument, dict)
        ]
        texts = [argument.get("text") for _, argument in page.calls if isinstance(argument, dict)]
        self.assertIn("[data-testid='generator-model-button']", selectors)
        self.assertIn("[data-testid='generator-model-option-openai/gpt-image-2']", selectors)
        self.assertNotIn("GPT Image 1.5", texts)

    async def test_model_selection_keeps_existing_gpt_image_2_choice(self):
        class SelectedPage:
            def __init__(self):
                self.calls = []

            async def evaluate(self, expression, argument=None):
                self.calls.append((expression, argument))
                return expression == lovart_canvas._ACTIVE_GPT_IMAGE_2

        page = SelectedPage()
        await lovart_canvas.LovartCanvasUi(page, Path("/tmp/article/images"))._select_model()

        self.assertEqual(page.calls, [(lovart_canvas._ACTIVE_GPT_IMAGE_2, None)])

    async def test_image_generation_switches_to_the_live_image_mode(self):
        class RecordingPage:
            def __init__(self):
                self.calls = []
                self.image_mode = False
                self.mode_menu_open = False

            async def evaluate(self, expression, argument=None):
                self.calls.append((expression, argument))
                selector = argument.get("selector") if isinstance(argument, dict) else None
                if expression == lovart_canvas._CONTROL_VISIBLE:
                    if selector == "[data-testid='generator-model-button']":
                        return self.image_mode
                    return selector == "[data-testid='agent-mode-switch-option-image']" and self.mode_menu_open
                if selector == "[data-testid='agent-mode-switch-trigger']":
                    self.mode_menu_open = True
                    return True
                if selector == "[data-testid='agent-mode-switch-option-image']":
                    self.mode_menu_open = False
                    self.image_mode = True
                    return True
                return False

        page = RecordingPage()
        await lovart_canvas.LovartCanvasUi(page, Path("/tmp/article/images"))._open_image_generator()

        selectors = [
            argument.get("selector")
            for expression, argument in page.calls
            if expression == lovart_canvas._CLICK_ELEMENT and isinstance(argument, dict)
        ]
        self.assertLess(
            selectors.index("[data-testid='agent-mode-switch-trigger']"),
            selectors.index("[data-testid='agent-mode-switch-option-image']"),
        )

    async def test_aspect_ratio_opens_live_parameters_before_selecting_ratio(self):
        class RecordingPage:
            def __init__(self):
                self.calls = []

            async def evaluate(self, expression, argument=None):
                self.calls.append((expression, argument))
                if expression == lovart_canvas._SET_CUSTOM_DIMENSIONS:
                    return True
                return argument.get("selector") == "[data-testid='agent-image-generator-multi-params-button']" or argument.get("text") == "21:9"

        page = RecordingPage()
        await lovart_canvas.LovartCanvasUi(page, Path("/tmp/article/images"))._select_aspect_ratio("21:9")

        selectors = [argument.get("selector") for _, argument in page.calls if isinstance(argument, dict)]
        texts = [argument.get("text") for _, argument in page.calls if isinstance(argument, dict)]
        self.assertEqual(selectors[0], "[data-testid='agent-image-generator-multi-params-button']")
        self.assertIn((lovart_canvas._SET_CUSTOM_DIMENSIONS, {"width": 1792, "height": 768}), page.calls)

    async def test_custom_dimensions_enter_exact_cover_pixels(self):
        class DimensionsPage:
            def __init__(self):
                self.calls = []

            async def evaluate(self, expression, argument=None):
                self.calls.append((expression, argument))
                return expression == lovart_canvas._SET_CUSTOM_DIMENSIONS

        page = DimensionsPage()
        await lovart_canvas.LovartCanvasUi(page, Path("/tmp/article/images"))._set_custom_dimensions(1792, 768)

        self.assertIn((lovart_canvas._SET_CUSTOM_DIMENSIONS, {"width": 1792, "height": 768}), page.calls)

    async def test_generated_image_scan_excludes_tracking_pixels(self):
        class ImageStatePage:
            async def evaluate(self, expression, argument=None):
                return {
                    "warning": "",
                    "urls": [
                        "https://bat.bing.com/action/0?event=pageLoad",
                        "https://lovart-persist-us.oss-us-east-1.aliyuncs.com/output/final-image.png",
                    ],
                }

        urls = await lovart_canvas.LovartCanvasUi(ImageStatePage(), Path("/tmp/article/images"))._image_urls()

        self.assertEqual(urls, {"https://lovart-persist-us.oss-us-east-1.aliyuncs.com/output/final-image.png"})

    async def test_submit_uses_enabled_live_image_button(self):
        class SubmitPage:
            def __init__(self):
                self.calls = []

            async def evaluate(self, expression, argument=None):
                self.calls.append((expression, argument))
                if expression == lovart_canvas._CONTROL_ENABLED:
                    return True
                return argument.get("selector") == "[data-testid='agent-image-generator-submit-button']"

        page = SubmitPage()
        await lovart_canvas.LovartCanvasUi(page, Path("/tmp/article/images"))._submit_image_generation()

        selectors = [
            argument.get("selector")
            for expression, argument in page.calls
            if expression == lovart_canvas._CLICK_ELEMENT and isinstance(argument, dict)
        ]
        self.assertEqual(selectors, ["[data-testid='agent-image-generator-submit-button']"])

    async def test_project_creation_opens_the_live_brand_menu_first(self):
        class RecordingPage:
            def __init__(self):
                self.calls = []

            async def evaluate(self, expression, argument=None):
                self.calls.append((expression, argument))
                return argument.get("selector") == "[data-testid='brand-menu-button']"

        page = RecordingPage()
        await lovart_canvas.LovartCanvasUi(page, Path("/tmp/article/images"))._open_project_menu()

        selectors = [argument.get("selector") for _, argument in page.calls if isinstance(argument, dict)]
        self.assertEqual(selectors, ["[data-testid='brand-menu-button']"])

    async def test_ui_prefers_trusted_page_clicks_when_available(self):
        class TrustedClickPage:
            def __init__(self):
                self.calls = []

            async def click(self, selector=None, text=None):
                self.calls.append((selector, text))
                return True

            async def evaluate(self, expression, argument=None):
                raise AssertionError("DOM click fallback must not be used when a trusted click is available")

        page = TrustedClickPage()
        clicked = await lovart_canvas.LovartCanvasUi(page, Path("/tmp/article/images"))._try_click(
            selector="[data-testid='generate-menu-image']"
        )

        self.assertTrue(clicked)
        self.assertEqual(page.calls, [("[data-testid='generate-menu-image']", None)])

    async def test_ui_prefers_trusted_page_text_entry_when_available(self):
        class TrustedFillPage:
            def __init__(self):
                self.calls = []

            async def fill(self, selector, text):
                self.calls.append((selector, text))
                return True

            async def evaluate(self, expression, argument=None):
                if expression == lovart_canvas._FIELD_CONTAINS:
                    return True
                raise AssertionError("DOM fill fallback must not be used when trusted text entry is available")

        page = TrustedFillPage()
        await lovart_canvas.LovartCanvasUi(page, Path("/tmp/article/images"))._fill(
            ["[data-testid='agent-image-generator-prompt']"], "a prompt", "enter image prompt"
        )

        self.assertEqual(page.calls, [("[data-testid='agent-image-generator-prompt']", "a prompt")])

    async def test_ui_falls_back_to_dom_input_when_trusted_entry_is_not_reflected(self):
        class FallbackFillPage:
            def __init__(self):
                self.contains_checks = 0
                self.fallback_called = False

            async def fill(self, selector, text):
                return True

            async def evaluate(self, expression, argument=None):
                if expression == lovart_canvas._FIELD_CONTAINS:
                    self.contains_checks += 1
                    return self.contains_checks > 1
                if expression == lovart_canvas._FILL_ELEMENT:
                    self.fallback_called = True
                    return True
                raise AssertionError("unexpected page evaluation")

        page = FallbackFillPage()
        await lovart_canvas.LovartCanvasUi(page, Path("/tmp/article/images"))._fill(
            ["[data-testid='agent-image-generator-prompt']"], "a prompt", "enter image prompt"
        )
        self.assertTrue(page.fallback_called)

    async def test_dismisses_the_brand_kit_prompt_before_using_canvas_controls(self):
        class SkipPage:
            def __init__(self):
                self.calls = []

            async def evaluate(self, expression, argument=None):
                self.calls.append(argument)
                return argument.get("text") == "Skip"

        page = SkipPage()
        dismissed = await lovart_canvas.LovartCanvasUi(page, Path("/tmp/article/images")).dismiss_overlays()

        self.assertTrue(dismissed)
        self.assertIn({"selector": "[data-testid='brand-kit-skip-button']", "text": None}, page.calls)
        self.assertIn({"selector": None, "text": "Skip"}, page.calls)


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
