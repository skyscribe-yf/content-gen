# Lovart Canvas Browser Automation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (- [ ]) syntax for tracking.

**Goal:** Build an isolated Python CLI that reads one article's prompt files, drives Lovart Canvas through its visible UI, creates or reuses an article-specific project, downloads completed GPT Image 2 images, and resumes without duplicate submissions.

**Architecture:** Article parsing, manifest decisions, and daily-cap accounting remain deterministic and independent of the browser. A browser adapter launches Chrome with a persistent profile outside the repository and uses Chrome DevTools Protocol only for visible DOM interaction and downloads. It never accepts browser cookies or calls Lovart's internal HTTP APIs.

**Tech Stack:** Python 3.12 standard library, requests, installed websockets, Google Chrome, Chrome DevTools Protocol, unittest.

---

## File Structure

| File | Responsibility |
|---|---|
| scripts/lovart_canvas.py | CLI, prompt discovery, manifest, daily cap, Chrome/CDP lifecycle, visible Canvas adapter, download orchestration. |
| scripts/test_lovart_canvas.py | Unit tests for parsing, state decisions, Chrome commands, and fake-driver orchestration. No test opens Chrome or contacts Lovart. |
| docs/superpowers/specs/2026-07-12-lovart-canvas-automation-design.md | Approved behaviour contract. Do not alter during implementation without author direction. |

The implementation does not modify scripts/apimart_client.py, its tests, or the existing image-generation policy. This is a separately invoked, user-authorised browser helper.

### Task 1: Add deterministic article and prompt discovery (completed)

**Files:**

- Create: scripts/lovart_canvas.py
- Create: scripts/test_lovart_canvas.py

- [ ] **Step 1: Write the failing prompt-discovery tests**

    import tempfile
    import unittest
    from pathlib import Path

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
                    [(j.source.name, j.aspect_ratio, j.output.name, j.prompt) for j in plan.jobs],
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

- [ ] **Step 2: Run the test and verify that it fails because the module does not exist**

Run: python -m unittest scripts/test_lovart_canvas.py -v

Expected: ModuleNotFoundError: No module named lovart_canvas.

- [ ] **Step 3: Implement only parsing and data objects**

    from __future__ import annotations

    from dataclasses import dataclass
    from pathlib import Path
    import re


    @dataclass(frozen=True)
    class PromptJob:
        source: Path
        prompt: str
        aspect_ratio: str
        output: Path


    @dataclass(frozen=True)
    class ArticlePlan:
        article: Path
        project_name: str
        jobs: tuple[PromptJob, ...]


    def strip_front_matter(raw: str) -> str:
        match = re.match(r"^---\s*\n.*?\n---\s*\n?", raw, flags=re.DOTALL)
        return raw[match.end():].strip() if match else raw.strip()


    def article_title(article: Path) -> str:
        source = article / "weixin.md"
        if source.exists():
            match = re.search(
                r'^title:\s*["\']?(.+?)["\']?\s*$',
                source.read_text(encoding="utf-8"),
                flags=re.MULTILINE,
            )
            if match and match.group(1).strip():
                return match.group(1).strip()
        return article.name


    def discover_article(article: Path) -> ArticlePlan:
        article = article.resolve()
        prompt_dir = article / "prompts"
        if not prompt_dir.is_dir():
            raise ValueError(f"missing prompts directory: {prompt_dir}")
        jobs = []
        for source in sorted(prompt_dir.glob("*.md")):
            prompt = strip_front_matter(source.read_text(encoding="utf-8"))
            if not prompt:
                raise ValueError(f"{source.name} is empty after front matter")
            ratio = "21:9" if source.name.startswith("00-cover") else "1:1"
            jobs.append(PromptJob(source, prompt, ratio, article / "images" / f"{source.stem}.png"))
        if not jobs:
            raise ValueError(f"no prompt Markdown files found in {prompt_dir}")
        return ArticlePlan(article, article_title(article), tuple(jobs))

Do not add Chrome, manifest, or CLI code in this task.

- [ ] **Step 4: Run the discovery tests and verify they pass**

Run: python -m unittest scripts/test_lovart_canvas.py -v

Expected: both PromptDiscoveryTest tests pass.

- [ ] **Step 5: Commit the focused parsing layer**

    git add scripts/lovart_canvas.py scripts/test_lovart_canvas.py
    git commit -m "feat: discover Lovart article prompts"

### Task 2: Add an atomic, idempotent article-local manifest (completed)

**Files:**

- Modify: scripts/lovart_canvas.py
- Modify: scripts/test_lovart_canvas.py

- [ ] **Step 1: Write failing state-machine tests**

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

- [ ] **Step 2: Run the test and verify expected missing-symbol failures**

Run: python -m unittest scripts/test_lovart_canvas.py -v

Expected: failures for missing Manifest, PromptJob.fingerprint, new_jobs_for_run, and load_manifest.

- [ ] **Step 3: Implement fingerprinting, manifest selection, and atomic save**

    import hashlib
    import json
    import os
    from dataclasses import field

    MANIFEST_NAME = "lovart-canvas.json"
    DAILY_LIMIT = 8
    REUSABLE_STATUSES = {"submitted", "running", "completed"}


    @property
    def fingerprint(self: PromptJob) -> str:
        raw = json.dumps(
            {"model": "gpt-image-2", "prompt": self.prompt, "aspect_ratio": self.aspect_ratio},
            ensure_ascii=False, sort_keys=True, separators=(",", ":"),
        )
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()


    PromptJob.fingerprint = fingerprint


    @dataclass
    class Manifest:
        project_id: str | None
        project_name: str
        jobs: dict[str, dict] = field(default_factory=dict)
        submissions: list[dict] = field(default_factory=list)

        @classmethod
        def empty(cls, project_name: str) -> "Manifest":
            return cls(project_id=None, project_name=project_name)

        def record_submitted(self, job: PromptJob, submitted_at: str) -> None:
            self.jobs[job.fingerprint] = {
                "status": "submitted", "source": job.source.name, "prompt": job.prompt,
                "aspect_ratio": job.aspect_ratio, "output": str(job.output), "submitted_at": submitted_at,
            }
            self.submissions.append({"date": submitted_at[:10], "fingerprint": job.fingerprint})

        def mark_completed(self, job_fingerprint: str, output: str) -> None:
            self.jobs[job_fingerprint].update(status="completed", output=output)

        def record_failed(self, job: PromptJob, error: str) -> None:
            self.jobs[job.fingerprint] = {
                "status": "failed", "source": job.source.name, "prompt": job.prompt,
                "aspect_ratio": job.aspect_ratio, "output": str(job.output), "error": error,
            }


    def new_jobs_for_run(jobs, manifest: Manifest, today: str, retry_failed: bool) -> list[PromptJob]:
        remaining = DAILY_LIMIT - sum(item.get("date") == today for item in manifest.submissions)
        selected = []
        for job in jobs:
            status = manifest.jobs.get(job.fingerprint, {}).get("status")
            if status in REUSABLE_STATUSES or (status == "failed" and not retry_failed):
                continue
            if len(selected) >= max(remaining, 0):
                break
            selected.append(job)
        return selected

Implement load_manifest(article, project_name) with strict JSON validation and save_manifest(article, manifest) by writing JSON to lovart-canvas.json.tmp in the same directory, calling flush and os.fsync, then replacing lovart-canvas.json. Preserve any unknown top-level keys when loading and saving.

- [ ] **Step 4: Run the full test file**

Run: python -m unittest scripts/test_lovart_canvas.py -v

Expected: all tests pass; no network or browser process starts.

- [ ] **Step 5: Commit durable resume behaviour**

    git add scripts/lovart_canvas.py scripts/test_lovart_canvas.py
    git commit -m "feat: persist Lovart generation state"

### Task 3: Add persistent Chrome and CDP primitives without credentials (completed)

**Files:**

- Modify: scripts/lovart_canvas.py
- Modify: scripts/test_lovart_canvas.py

- [ ] **Step 1: Write a failing pure launch-command test**

    class ChromeLaunchTest(unittest.TestCase):
        def test_chrome_command_uses_external_profile_and_remote_debugging(self):
            command = lovart_canvas.chrome_command(
                chrome="/usr/bin/google-chrome", profile=Path("/tmp/lovart-profile"),
                port=9229, initial_url="https://www.lovart.ai/canvas",
            )
            self.assertEqual(command, [
                "/usr/bin/google-chrome", "--remote-debugging-port=9229",
                "--user-data-dir=/tmp/lovart-profile", "--no-first-run",
                "--no-default-browser-check", "https://www.lovart.ai/canvas",
            ])

- [ ] **Step 2: Run the test and verify it fails for missing chrome_command**

Run: python -m unittest scripts/test_lovart_canvas.py -v

Expected: AttributeError for chrome_command.

- [ ] **Step 3: Implement Chrome lifecycle and an async CDP client**

    import asyncio
    import shutil
    import socket
    import subprocess
    import websockets

    DEFAULT_PROFILE = Path.home() / ".local" / "share" / "content-gen" / "lovart-chrome-profile"


    def chrome_command(chrome: str, profile: Path, port: int, initial_url: str) -> list[str]:
        return [
            chrome, f"--remote-debugging-port={port}", f"--user-data-dir={profile}",
            "--no-first-run", "--no-default-browser-check", initial_url,
        ]

Implement these exact boundaries:

- find_chrome searches GOOGLE_CHROME_BIN, then google-chrome, google-chrome-stable, and chromium with shutil.which; it raises RuntimeError("Google Chrome was not found; set GOOGLE_CHROME_BIN") if none exists.
- allocate_port binds 127.0.0.1:0, reads the assigned port, closes the socket, and returns the integer.
- launch_or_reuse_chrome(profile, url) creates the profile directory with mode 0o700, checks profile/DevToolsActivePort and http://127.0.0.1:port/json/version, otherwise starts subprocess.Popen(chrome_command(...), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL), and waits at most 30 seconds for webSocketDebuggerUrl.
- CdpClient wraps websockets.connect, maintains incrementing request IDs and pending futures, rejects protocol error replies, and exposes send(method, params=None, session_id=None, timeout=15).
- configure_page_session(cdp, target_id, image_dir) attaches with Target.attachToTarget and flatten=True, enables Page, Runtime, DOM, and Browser, then sends Page.setDownloadBehavior with behavior allow and downloadPath str(image_dir.resolve()).

No function may accept a Cookie header, serialised browser session, JWT, refresh token, usertoken, or read .env.

- [ ] **Step 4: Add a fake-CDP test and run all tests**

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
                ("Page.setDownloadBehavior",
                 {"behavior": "allow", "downloadPath": "/tmp/article/images"}, "session-1"),
                cdp.calls,
            )

Run: python -m unittest scripts/test_lovart_canvas.py -v

Expected: existing parsing/state tests and Chrome/CDP tests pass.

- [ ] **Step 5: Commit browser infrastructure**

    git add scripts/lovart_canvas.py scripts/test_lovart_canvas.py
    git commit -m "feat: launch isolated Lovart browser profile"

### Task 4: Implement the visible Lovart Canvas UI adapter (completed)

**Files:**

- Modify: scripts/lovart_canvas.py
- Modify: scripts/test_lovart_canvas.py

- [ ] **Step 1: Write failing selector and blocked-state tests using a fake page**

    class FakePage:
        def __init__(self, values):
            self.values = values
        async def evaluate(self, expression, arg=None):
            return self.values.pop(0)


    class LovartUiTest(unittest.IsolatedAsyncioTestCase):
        async def test_clicks_first_visible_candidate_and_raises_when_missing(self):
            page = FakePage([False, True])
            ui = lovart_canvas.LovartCanvasUi(page)
            await ui.click_first(
                ["[data-testid='nav-generate-menu-button']", "button[aria-label='Generate']"],
                "open generator",
            )

            missing = FakePage([False, False, '<input value="secret"><div>verification required</div>'])
            with self.assertRaisesRegex(lovart_canvas.LovartUiBlocked, "open generator") as caught:
                await lovart_canvas.LovartCanvasUi(missing).click_first(["one", "two"], "open generator")
            self.assertNotIn("secret", str(caught.exception))
            self.assertIn("verification", str(caught.exception))

- [ ] **Step 2: Run the test and verify missing-class failure**

Run: python -m unittest scripts/test_lovart_canvas.py -v

Expected: failure because LovartCanvasUi and LovartUiBlocked do not exist.

- [ ] **Step 3: Implement DOM-only UI actions and safe failure modes**

Implement Page.evaluate with Runtime.evaluate, passing all dynamic data through json.dumps rather than string interpolation. It returns result.result.value and raises when Chrome reports exceptionDetails.

LovartCanvasUi.click_first(selectors, action, text=None) evaluates this function once per candidate, then once with the optional text fallback:

    ({ selector, text }) => {
      const visible = (el) => !!el && !!(el.offsetWidth || el.offsetHeight || el.getClientRects().length);
      const element = selector
        ? [...document.querySelectorAll(selector)].find(visible)
        : [...document.querySelectorAll('button,[role="button"],label,span')]
            .find((el) => visible(el) && el.textContent.trim().toLowerCase() === text.toLowerCase());
      if (!element) return false;
      element.click();
      return true;
    }

Use these candidates in order:

| Action | CSS candidates | Text fallback |
|---|---|---|
| Open creation menu | data-testid nav-generate-menu-button; data-testid generate-menu-trigger | Generate; 生成 |
| Select image creation | data-testid generate-menu-image | Image; 图片 |
| Select model | data-testid contains model; button aria-haspopup dialog | GPT Image 2; GPT Image |
| Select 21:9 | data-value 21:9; aspect test ID with value 21:9 | 21:9 |
| Select 1:1 | data-value 1:1; aspect test ID with value 1:1 | 1:1 |
| Submit | button type submit; test ID containing generate-button | Generate; 生成 |

set_prompt(prompt) finds the first visible textarea, contenteditable=true, or input whose placeholder contains prompt. It uses the native value setter then input and change events for form fields; it sets textContent and dispatches a bubbling InputEvent for contenteditable.

ensure_project(project_name) returns the existing projectId from location.href. If absent, it opens the Canvas project list, activates New project or 新建项目, fills the name dialog, and waits 30 seconds for projectId=([^&]+) in the URL. wait_for_generated_image(before_urls) polls visible non-data img src URLs every two seconds for up to 180 seconds. download_image(job, image_url) clicks Download or 下载 in the image ancestor, polls the configured directory for a fresh PNG, JPEG, or WebP, and renames it to job.output only if it does not already exist.

A missing control, login, verification, quota, credit dialog, or timeout raises LovartUiBlocked(action, sanitized_dom_snapshot). Sanitisation removes input values, truncates at 4,000 characters, and does not log prompts or credentials. The adapter never attempts a bypass or calls a private Lovart endpoint.

- [ ] **Step 4: Run the full fake-UI test file**

Run: python -m unittest scripts/test_lovart_canvas.py -v

Expected: all tests pass and no browser opens.

- [ ] **Step 5: Commit the visible UI adapter**

    git add scripts/lovart_canvas.py scripts/test_lovart_canvas.py
    git commit -m "feat: automate Lovart Canvas generation UI"

### Task 5: Wire the safe CLI, resume behaviour, and dry-run mode (completed)

**Files:**

- Modify: scripts/lovart_canvas.py
- Modify: scripts/test_lovart_canvas.py

- [ ] **Step 1: Write a failing orchestration test with a fake UI**

    class FakeLovartUi:
        def __init__(self):
            self.created_for = []
            self.generated = []
        async def ensure_project(self, name):
            self.created_for.append(name)
            return "project-123"
        async def generate_and_download(self, job):
            self.generated.append(job.fingerprint)
            job.output.parent.mkdir(parents=True, exist_ok=True)
            job.output.write_bytes(b"png")


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

- [ ] **Step 2: Run the test and verify it fails for missing run_article**

Run: python -m unittest scripts/test_lovart_canvas.py -v

Expected: AttributeError for run_article.

- [ ] **Step 3: Implement orchestration and argparse**

Define a RunSummary dataclass with eligible jobs and integer submitted, completed, skipped, and cap_reached counters. run_article(article, ui, today, max_new, retry_failed=False, dry_run=False) returns this summary and must:

1. call discover_article and load_manifest;
2. reject max_new below one or above eight before a UI call;
3. call new_jobs_for_run and slice to max_new;
4. in dry-run, return project name and eligible jobs without ensure_project, images, or manifest write;
5. for actual jobs with no project ID, call ui.ensure_project(plan.project_name), record project_id, and save;
6. immediately before ui.generate_and_download(job), call record_submitted with datetime.now().astimezone().isoformat() and save;
7. after a verified non-empty output, mark it completed and save;
8. on LovartUiBlocked or any exception, preserve submitted, set only a sanitised last_error, save, print it, and stop with exit code two. It does not submit another job.

Add the options article (required Path), profile-dir (default DEFAULT_PROFILE), dry-run, retry-failed, and max-new (default DAILY_LIMIT).

In main, validate the article before launching Chrome. An actual run creates images, launches/reuses the profile, opens the recorded Canvas URL when project_id exists, constructs LovartCanvasUi, then invokes asyncio.run(run_article(...)). The summary lists submitted, completed, skipped, and cap-reached counts. There is no token or cookie option.

- [ ] **Step 4: Add dry-run and cap tests, then run the full suite**

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

Run: python -m unittest scripts/test_lovart_canvas.py -v

Expected: all discovery, manifest, Chrome, UI-fake, and orchestration tests pass.

- [ ] **Step 5: Commit the usable CLI**

    git add scripts/lovart_canvas.py scripts/test_lovart_canvas.py
    git commit -m "feat: add resumable Lovart Canvas CLI"

### Task 6: Perform a safe one-image live validation (in progress)

**Files:**

- Modify: scripts/lovart_canvas.py only if the smoke test exposes a real selector mismatch or deterministic error.
- Modify: scripts/test_lovart_canvas.py first for every deterministic correction.

- [ ] **Step 1: Validate dry-run without browser or credits**

Run:

    tmp=$(mktemp -d)
    mkdir -p "$tmp/article/prompts"
    printf '%s\n' '---' 'title: "Lovart smoke test"' '---' 'body' > "$tmp/article/weixin.md"
    printf '%s\n' 'A simple blue circle on white.' > "$tmp/article/prompts/00-cover.md"
    python scripts/lovart_canvas.py --article "$tmp/article" --dry-run

Expected: project name Lovart smoke test, source 00-cover.md, ratio 21:9, output ending images/00-cover.png; Chrome does not launch.

- [ ] **Step 2: Run one deliberate live smoke generation only after manual login**

Run:

    python scripts/lovart_canvas.py \
      --article "$tmp/article" \
      --profile-dir "$HOME/.local/share/content-gen/lovart-chrome-profile" \
      --max-new 1

Expected: Lovart opens for normal manual login if needed; one Canvas project is created or recorded; at most one GPT Image 2 job is submitted; the manifest is saved as submitted before the request; success leaves non-empty images/00-cover.png and status completed. If Lovart asks for verification or quota confirmation, stop without bypassing it and inspect the manifest instead of retrying.

- [ ] **Step 3: Verify idempotent real-world resume before any second image**

Run the exact command from Step 2 again.

Expected: the cover job is skipped; it does not click Generate or use a second daily credit. lovart-canvas.json contains only one submission record for the fingerprint.

- [ ] **Step 4: Correct real UI differences test-first**

For an exact selector, sanitisation, or output conflict difference, first add the matching unittest case, run it to see failure, then make the minimum correction and rerun the full test file. Do not make speculative UI changes and do not resubmit the smoke prompt.

- [ ] **Step 5: Run final verification and commit only if Task 6 changed code**

Run:

    python -m unittest scripts/test_lovart_canvas.py -v
    git diff --check
    git status --short

Expected: all tests pass, whitespace checking has no output, and only this feature's files are staged. If Task 6 changed code:

    git add scripts/lovart_canvas.py scripts/test_lovart_canvas.py
    git commit -m "fix: harden Lovart Canvas smoke flow"

## Plan Self-Review

| Approved design requirement | Implementing task |
|---|---|
| Prompt files, title fallback, cover and regular aspect rules, output names | Task 1 |
| Article-local project ID, fingerprinted resume, never duplicate, explicit retry | Tasks 2 and 5 |
| Persistent local manual-login profile and no copied credentials | Task 3 |
| Visible Canvas UI, project creation, GPT Image 2, download, safe stop | Task 4 |
| Eight-job daily cap, sequential flow, dry-run, CLI | Tasks 2 and 5 |
| Unit tests and one-image manual smoke test | Tasks 1–6 |
| No backend replacement, private API, or credit/CAPTCHA bypass | All tasks |

The plan contains no incomplete implementation markers. Names are consistent throughout: PromptJob.fingerprint, Manifest, new_jobs_for_run, LovartCanvasUi, LovartUiBlocked, and run_article.
