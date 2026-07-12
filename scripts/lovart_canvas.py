"""Generate article images through Lovart Canvas's visible browser UI.

This experimental helper is intentionally separate from the apimart client. It
reads article prompt Markdown files and will later drive a locally logged-in
browser rather than accepting exported cookies or private API credentials.
"""

from __future__ import annotations

import argparse
import asyncio
from dataclasses import dataclass, field
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import socket
import subprocess
import time
from urllib.parse import urlencode

import requests
import websockets


@dataclass(frozen=True)
class PromptJob:
    """One prompt file and its deterministic Lovart output contract."""

    source: Path
    prompt: str
    aspect_ratio: str
    output: Path

    @property
    def fingerprint(self) -> str:
        """Return the stable identity used to prevent duplicate submissions."""

        raw = json.dumps(
            {
                "model": "gpt-image-2",
                "prompt": self.prompt,
                "aspect_ratio": self.aspect_ratio,
            },
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class ArticlePlan:
    """The deterministic inputs required to generate one article's images."""

    article: Path
    project_name: str
    jobs: tuple[PromptJob, ...]


MANIFEST_NAME = "lovart-canvas.json"
MANIFEST_VERSION = 1
DAILY_LIMIT = 8
REUSABLE_STATUSES = {"submitted", "running", "completed"}


@dataclass
class Manifest:
    """Durable, article-local state for Lovart project and generation jobs."""

    project_id: str | None
    project_name: str
    project_url: str | None = None
    jobs: dict[str, dict] = field(default_factory=dict)
    submissions: list[dict] = field(default_factory=list)
    extras: dict = field(default_factory=dict)

    @classmethod
    def empty(cls, project_name: str) -> "Manifest":
        return cls(project_id=None, project_name=project_name)

    def record_submitted(self, job: PromptJob, submitted_at: str) -> None:
        self.jobs[job.fingerprint] = {
            "status": "submitted",
            "source": job.source.name,
            "prompt": job.prompt,
            "aspect_ratio": job.aspect_ratio,
            "output": str(job.output),
            "submitted_at": submitted_at,
        }
        self.submissions.append({"date": submitted_at[:10], "fingerprint": job.fingerprint})

    def mark_completed(self, job_fingerprint: str, output: str) -> None:
        self.jobs[job_fingerprint].update(status="completed", output=output)

    def record_failed(self, job: PromptJob, error: str) -> None:
        self.jobs[job.fingerprint] = {
            "status": "failed",
            "source": job.source.name,
            "prompt": job.prompt,
            "aspect_ratio": job.aspect_ratio,
            "output": str(job.output),
            "error": error,
        }

    def to_data(self) -> dict:
        return {
            **self.extras,
            "version": MANIFEST_VERSION,
            "project_id": self.project_id,
            "project_name": self.project_name,
            "project_url": self.project_url,
            "jobs": self.jobs,
            "submissions": self.submissions,
        }


def _manifest_path(article: Path) -> Path:
    return article / MANIFEST_NAME


def load_manifest(article: Path, project_name: str) -> Manifest:
    """Load strict manifest state without silently replacing malformed data."""

    path = _manifest_path(article)
    if not path.exists():
        return Manifest.empty(project_name)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"malformed Lovart manifest: {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"malformed Lovart manifest: {path}: expected object")

    jobs = data.get("jobs", {})
    submissions = data.get("submissions", [])
    if not isinstance(jobs, dict) or not isinstance(submissions, list):
        raise ValueError(f"malformed Lovart manifest: {path}: jobs/submissions have invalid types")

    known = {"version", "project_id", "project_name", "project_url", "jobs", "submissions"}
    extras = {key: value for key, value in data.items() if key not in known}
    project_id = data.get("project_id")
    project_url = data.get("project_url")
    if project_id is not None and not isinstance(project_id, str):
        raise ValueError(f"malformed Lovart manifest: {path}: project_id must be a string")
    if project_url is not None and not isinstance(project_url, str):
        raise ValueError(f"malformed Lovart manifest: {path}: project_url must be a string")
    return Manifest(
        project_id=project_id,
        project_name=data.get("project_name") if isinstance(data.get("project_name"), str) else project_name,
        project_url=project_url,
        jobs=jobs,
        submissions=submissions,
        extras=extras,
    )


def save_manifest(article: Path, manifest: Manifest) -> None:
    """Atomically persist state so an interrupted process cannot corrupt it."""

    path = _manifest_path(article)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f"{path.name}.tmp")
    payload = json.dumps(manifest.to_data(), ensure_ascii=False, indent=2)
    with temporary.open("w", encoding="utf-8") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())
    temporary.replace(path)


def new_jobs_for_run(
    jobs: list[PromptJob] | tuple[PromptJob, ...],
    manifest: Manifest,
    today: str,
    retry_failed: bool,
) -> list[PromptJob]:
    """Select at most the remaining daily allowance without duplicating work."""

    remaining = DAILY_LIMIT - sum(entry.get("date") == today for entry in manifest.submissions)
    selected: list[PromptJob] = []
    for job in jobs:
        status = manifest.jobs.get(job.fingerprint, {}).get("status")
        if status in REUSABLE_STATUSES or (status == "failed" and not retry_failed):
            continue
        if len(selected) >= max(remaining, 0):
            break
        selected.append(job)
    return selected


DEFAULT_PROFILE = Path.home() / ".local" / "share" / "content-gen" / "lovart-chrome-profile"
LOVART_CANVAS_URL = "https://www.lovart.ai/canvas"


def chrome_command(chrome: str, profile: Path, port: int, initial_url: str) -> list[str]:
    """Build Chrome's visible, isolated CDP launch command."""

    return [
        chrome,
        f"--remote-debugging-port={port}",
        f"--user-data-dir={profile}",
        "--no-first-run",
        "--no-default-browser-check",
        initial_url,
    ]


def find_chrome() -> str:
    """Find a locally installed Chrome binary without reading user credentials."""

    candidates = [os.environ.get("GOOGLE_CHROME_BIN", ""), "google-chrome", "google-chrome-stable", "chromium"]
    for candidate in candidates:
        if not candidate:
            continue
        resolved = candidate if os.path.isabs(candidate) and os.path.exists(candidate) else shutil.which(candidate)
        if resolved:
            return resolved
    raise RuntimeError("Google Chrome was not found; set GOOGLE_CHROME_BIN")


def allocate_port() -> int:
    """Reserve a currently free loopback port for Chrome remote debugging."""

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
        listener.bind(("127.0.0.1", 0))
        return int(listener.getsockname()[1])


def _debug_websocket_url(port: int) -> str | None:
    try:
        response = requests.get(f"http://127.0.0.1:{port}/json/version", timeout=1)
        response.raise_for_status()
        websocket_url = response.json().get("webSocketDebuggerUrl")
        return websocket_url if isinstance(websocket_url, str) else None
    except (requests.RequestException, ValueError):
        return None


def _existing_debug_port(profile: Path) -> int | None:
    port_file = profile / "DevToolsActivePort"
    try:
        port = int(port_file.read_text(encoding="utf-8").splitlines()[0])
    except (OSError, ValueError, IndexError):
        return None
    return port if port > 0 else None


@dataclass
class ChromeConnection:
    port: int
    browser_ws_url: str
    process: subprocess.Popen | None


def launch_or_reuse_chrome(profile: Path, initial_url: str) -> ChromeConnection:
    """Reuse the dedicated profile's Chrome or start it visibly and await CDP."""

    profile.mkdir(parents=True, exist_ok=True, mode=0o700)
    try:
        profile.chmod(0o700)
    except OSError:
        pass

    existing_port = _existing_debug_port(profile)
    if existing_port:
        existing_ws_url = _debug_websocket_url(existing_port)
        if existing_ws_url:
            return ChromeConnection(existing_port, existing_ws_url, process=None)

    port = allocate_port()
    process = subprocess.Popen(
        chrome_command(find_chrome(), profile, port, initial_url),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline:
        websocket_url = _debug_websocket_url(port)
        if websocket_url:
            return ChromeConnection(port, websocket_url, process=process)
        time.sleep(0.2)
    raise RuntimeError("Chrome did not expose a DevTools endpoint within 30 seconds")


class CdpClient:
    """Small async Chrome DevTools Protocol client used by the Canvas adapter."""

    def __init__(self, websocket):
        self._websocket = websocket
        self._next_id = 0
        self._pending: dict[int, asyncio.Future] = {}
        self._reader_task = asyncio.create_task(self._read_messages())

    @classmethod
    async def connect(cls, websocket_url: str) -> "CdpClient":
        return cls(await websockets.connect(websocket_url, max_size=50 * 1024 * 1024))

    async def _read_messages(self) -> None:
        try:
            async for raw in self._websocket:
                message = json.loads(raw)
                request_id = message.get("id")
                if not isinstance(request_id, int):
                    continue
                pending = self._pending.pop(request_id, None)
                if pending is None or pending.done():
                    continue
                if "error" in message:
                    pending.set_exception(RuntimeError(message["error"].get("message", "CDP request failed")))
                else:
                    pending.set_result(message.get("result", {}))
        except Exception as exc:
            for pending in self._pending.values():
                if not pending.done():
                    pending.set_exception(RuntimeError(f"CDP connection closed: {exc}"))
            self._pending.clear()

    async def send(self, method: str, params: dict | None = None, session_id: str | None = None, timeout: float = 15):
        self._next_id += 1
        request_id = self._next_id
        request = {"id": request_id, "method": method}
        if params is not None:
            request["params"] = params
        if session_id is not None:
            request["sessionId"] = session_id
        future = asyncio.get_running_loop().create_future()
        self._pending[request_id] = future
        await self._websocket.send(json.dumps(request))
        try:
            return await asyncio.wait_for(future, timeout)
        finally:
            self._pending.pop(request_id, None)

    async def close(self) -> None:
        self._reader_task.cancel()
        try:
            await self._reader_task
        except asyncio.CancelledError:
            pass
        await self._websocket.close()


async def configure_page_session(cdp: CdpClient, target_id: str, image_dir: Path) -> str:
    """Attach to a Chrome page and allow its normal UI downloads into images/."""

    attached = await cdp.send("Target.attachToTarget", {"targetId": target_id, "flatten": True})
    session_id = attached["sessionId"]
    for domain in ("Page", "Runtime", "DOM"):
        await cdp.send(f"{domain}.enable", session_id=session_id)
    await cdp.send(
        "Page.setDownloadBehavior",
        {"behavior": "allow", "downloadPath": str(image_dir.resolve())},
        session_id=session_id,
    )
    return session_id


class LovartUiBlocked(RuntimeError):
    """The visible site cannot safely continue without author intervention."""

    def __init__(self, action: str, snapshot: str):
        super().__init__(f"Lovart UI blocked while trying to {action}: {snapshot}")
        self.action = action
        self.snapshot = snapshot


def _sanitize_snapshot(raw: object) -> str:
    """Report page state without retaining form values, prompts, or other content."""

    text = str(raw).lower()
    signals = [
        signal
        for signal in ("login", "sign in", "verification", "verify", "验证码", "quota", "credit", "insufficient")
        if signal in text
    ]
    return "page state: " + (", ".join(signals) if signals else "required controls not visible")


class CdpPage:
    """A single CDP target session with safe JavaScript argument transport."""

    def __init__(self, cdp: CdpClient, session_id: str):
        self._cdp = cdp
        self._session_id = session_id

    async def evaluate(self, function: str, argument: object | None = None):
        encoded = json.dumps(argument, ensure_ascii=False)
        expression = f"({function})({encoded})"
        result = await self._cdp.send(
            "Runtime.evaluate",
            {"expression": expression, "returnByValue": True, "awaitPromise": True},
            session_id=self._session_id,
        )
        if result.get("exceptionDetails"):
            raise RuntimeError("Canvas DOM evaluation failed")
        return result.get("result", {}).get("value")

    async def navigate(self, url: str) -> None:
        await self._cdp.send("Page.navigate", {"url": url}, session_id=self._session_id)


async def open_canvas_page(cdp: CdpClient, url: str, image_dir: Path) -> CdpPage:
    """Open or reuse a Lovart Canvas tab and attach a CDP page session."""

    target_info = await cdp.send("Target.getTargets")
    targets = target_info.get("targetInfos", [])
    target = next(
        (
            item
            for item in targets
            if item.get("type") == "page" and "lovart.ai/canvas" in item.get("url", "")
        ),
        None,
    )
    if target is None:
        created = await cdp.send("Target.createTarget", {"url": url})
        target_id = created["targetId"]
    else:
        target_id = target["targetId"]
    session_id = await configure_page_session(cdp, target_id, image_dir)
    page = CdpPage(cdp, session_id)
    await page.navigate(url)
    return page


_CLICK_ELEMENT = """
({ selector, text }) => {
  const visible = (el) => !!el && !!(el.offsetWidth || el.offsetHeight || el.getClientRects().length);
  const candidates = selector
    ? [...document.querySelectorAll(selector)]
    : [...document.querySelectorAll('button,[role="button"],label,span')];
  const element = candidates.find((el) => visible(el) && (!text || el.textContent.trim().toLowerCase() === text.toLowerCase()));
  if (!element) return false;
  element.click();
  return true;
}
"""

_FILL_ELEMENT = """
({ selectors, text }) => {
  const visible = (el) => !!el && !!(el.offsetWidth || el.offsetHeight || el.getClientRects().length);
  const element = selectors.flatMap((selector) => [...document.querySelectorAll(selector)]).find(visible);
  if (!element) return false;
  if (element instanceof HTMLInputElement || element instanceof HTMLTextAreaElement) {
    const prototype = element instanceof HTMLInputElement ? HTMLInputElement.prototype : HTMLTextAreaElement.prototype;
    Object.getOwnPropertyDescriptor(prototype, 'value').set.call(element, text);
    element.dispatchEvent(new Event('input', { bubbles: true }));
    element.dispatchEvent(new Event('change', { bubbles: true }));
  } else {
    element.textContent = text;
    element.dispatchEvent(new InputEvent('input', { bubbles: true, inputType: 'insertText', data: text }));
  }
  element.focus();
  return true;
}
"""

_PAGE_SNAPSHOT = "() => document.body ? document.body.innerHTML : ''"
_PAGE_URL = "() => location.href"
_IMAGE_STATE = """
() => {
  const pageText = (document.body?.innerText || '').toLowerCase();
  const warning = ['insufficient', 'quota', 'credit', 'login', 'verification', 'verify', '验证码']
    .find((word) => pageText.includes(word)) || '';
  const urls = [...document.querySelectorAll('img[src]')]
    .map((image) => image.currentSrc || image.src)
    .filter((url) => url && !url.startsWith('data:'));
  return { warning, urls };
}
"""

_CLICK_DOWNLOAD = """
({ imageUrl }) => {
  const visible = (el) => !!el && !!(el.offsetWidth || el.offsetHeight || el.getClientRects().length);
  const image = [...document.querySelectorAll('img[src]')]
    .find((item) => (item.currentSrc || item.src) === imageUrl);
  if (!image) return false;
  const container = image.closest('[data-testid], [role="dialog"], figure, li, div') || image.parentElement;
  const button = [...container.querySelectorAll('button,[role="button"],a')]
    .find((item) => visible(item) && ['download', '下载'].includes(item.textContent.trim().toLowerCase()));
  if (!button) return false;
  button.click();
  return true;
}
"""


class LovartCanvasUi:
    """Drive only normal, visible Lovart Canvas controls through a CDP page."""

    def __init__(self, page, image_dir: Path):
        self.page = page
        self.image_dir = image_dir
        self.project_url: str | None = None

    async def _snapshot(self) -> str:
        try:
            return _sanitize_snapshot(await self.page.evaluate(_PAGE_SNAPSHOT))
        except Exception:
            return "page state: unavailable"

    async def _try_click(self, selector: str | None = None, text: str | None = None) -> bool:
        return bool(await self.page.evaluate(_CLICK_ELEMENT, {"selector": selector, "text": text}))

    async def click_first(self, selectors: list[str], action: str, text: str | None = None) -> None:
        for selector in selectors:
            if await self._try_click(selector=selector):
                return
        if text and await self._try_click(text=text):
            return
        raise LovartUiBlocked(action, await self._snapshot())

    async def _click_labels(self, selectors: list[str], labels: list[str], action: str) -> None:
        for selector in selectors:
            if await self._try_click(selector=selector):
                return
        for label in labels:
            if await self._try_click(text=label):
                return
        raise LovartUiBlocked(action, await self._snapshot())

    async def _fill(self, selectors: list[str], text: str, action: str) -> None:
        if not await self.page.evaluate(_FILL_ELEMENT, {"selectors": selectors, "text": text}):
            raise LovartUiBlocked(action, await self._snapshot())

    async def _current_url(self) -> str:
        url = await self.page.evaluate(_PAGE_URL)
        return url if isinstance(url, str) else ""

    async def ensure_project(self, project_name: str) -> str:
        """Return a current project ID, creating a named project through the UI if needed."""

        url = await self._current_url()
        match = re.search(r"[?&]projectId=([^&]+)", url)
        if match:
            self.project_url = url
            return match.group(1)

        await self._click_labels(
            ["[data-testid='new-project']", "[data-testid='canvas-new-project']"],
            ["New project", "新建项目"],
            "create project",
        )
        await self._fill(
            ["input[name='projectName']", "input[placeholder*='project' i]", "input[placeholder*='项目']"],
            project_name,
            "enter project name",
        )
        await self._click_labels(
            ["button[type='submit']", "[data-testid='create-project']"],
            ["Create", "创建"],
            "confirm project creation",
        )
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            url = await self._current_url()
            match = re.search(r"[?&]projectId=([^&]+)", url)
            if match:
                self.project_url = url
                return match.group(1)
            await asyncio.sleep(0.5)
        raise LovartUiBlocked("wait for created project", await self._snapshot())

    async def _open_image_generator(self) -> None:
        await self._click_labels(
            ["[data-testid='nav-generate-menu-button']", "[data-testid='generate-menu-trigger']"],
            ["Generate", "生成"],
            "open generator",
        )
        await self._click_labels(
            ["[data-testid='generate-menu-image']"],
            ["Image", "图片"],
            "select image generation",
        )

    async def _select_model(self) -> None:
        for selector in ("[data-testid*='model-trigger']", "[aria-label*='Model']"):
            if await self._try_click(selector=selector):
                break
        await self._click_labels(
            ["[data-testid*='model-option']"],
            ["GPT Image 2", "GPT Image"],
            "select GPT Image 2",
        )

    async def _select_aspect_ratio(self, aspect_ratio: str) -> None:
        await self._click_labels(
            [f"[data-value='{aspect_ratio}']", f"[data-testid*='aspect'][data-value='{aspect_ratio}']"],
            [aspect_ratio],
            f"select {aspect_ratio} aspect ratio",
        )

    async def _image_urls(self) -> set[str]:
        state = await self.page.evaluate(_IMAGE_STATE)
        if not isinstance(state, dict):
            raise LovartUiBlocked("inspect generated images", await self._snapshot())
        warning = state.get("warning", "")
        if warning:
            raise LovartUiBlocked("inspect generated images", f"page state: {warning}")
        return {url for url in state.get("urls", []) if isinstance(url, str)}

    async def wait_for_generated_image(self, before_urls: set[str]) -> str:
        deadline = time.monotonic() + 180
        while time.monotonic() < deadline:
            image_urls = await self._image_urls()
            created = image_urls - before_urls
            if created:
                return sorted(created)[0]
            await asyncio.sleep(2)
        raise LovartUiBlocked("wait for image generation", await self._snapshot())

    async def download_image(self, job: PromptJob, image_url: str) -> Path:
        self.image_dir.mkdir(parents=True, exist_ok=True)
        started = time.time()
        if not await self.page.evaluate(_CLICK_DOWNLOAD, {"imageUrl": image_url}):
            raise LovartUiBlocked("download generated image", await self._snapshot())
        deadline = time.monotonic() + 60
        suffixes = {".png", ".jpg", ".jpeg", ".webp"}
        while time.monotonic() < deadline:
            candidates = [
                path
                for path in self.image_dir.iterdir()
                if path.suffix.lower() in suffixes and path.stat().st_mtime >= started
            ]
            if candidates:
                if job.output.exists():
                    raise RuntimeError(f"refusing to overwrite existing output: {job.output}")
                newest = max(candidates, key=lambda path: path.stat().st_mtime)
                newest.replace(job.output)
                return job.output
            await asyncio.sleep(1)
        raise LovartUiBlocked("wait for image download", await self._snapshot())

    async def generate_and_download(self, job: PromptJob) -> Path:
        """Submit one visible image request and download its completed result."""

        before_urls = await self._image_urls()
        await self._open_image_generator()
        await self._select_model()
        await self._select_aspect_ratio(job.aspect_ratio)
        await self._fill(
            ["textarea", "[contenteditable='true']", "input[placeholder*='prompt' i]"],
            job.prompt,
            "enter image prompt",
        )
        await self._click_labels(
            ["button[type='submit']", "[data-testid*='generate-button']"],
            ["Generate", "生成"],
            "submit image generation",
        )
        image_url = await self.wait_for_generated_image(before_urls)
        return await self.download_image(job, image_url)


@dataclass(frozen=True)
class RunSummary:
    """A non-sensitive account of one planned or completed article run."""

    project_name: str
    eligible: tuple[PromptJob, ...]
    submitted: int
    completed: int
    skipped: int
    cap_reached: bool


def _remaining_daily_allowance(manifest: Manifest, today: str) -> int:
    return max(DAILY_LIMIT - sum(entry.get("date") == today for entry in manifest.submissions), 0)


def _sanitized_error(error: Exception) -> str:
    if isinstance(error, LovartUiBlocked):
        return str(error)
    return f"{type(error).__name__}: generation stopped before completion"


async def run_article(
    article: Path,
    ui,
    today: str,
    max_new: int,
    retry_failed: bool = False,
    dry_run: bool = False,
) -> RunSummary:
    """Generate a safely resumable, sequential batch for one article."""

    if not 1 <= max_new <= DAILY_LIMIT:
        raise ValueError(f"max-new must be between 1 and {DAILY_LIMIT}")

    plan = discover_article(article)
    manifest = load_manifest(plan.article, plan.project_name)
    for job in plan.jobs:
        record = manifest.jobs.get(job.fingerprint, {})
        if record.get("status") == "completed" and not job.output.is_file():
            raise RuntimeError(f"completed manifest entry is missing its output: {job.output}")

    daily_allowance = _remaining_daily_allowance(manifest, today)
    candidates = new_jobs_for_run(plan.jobs, manifest, today=today, retry_failed=retry_failed)
    eligible = tuple(candidates[:max_new])
    skipped = len(plan.jobs) - len(eligible)
    cap_reached = daily_allowance == 0 or len(candidates) > len(eligible)
    summary = RunSummary(
        project_name=plan.project_name,
        eligible=eligible,
        submitted=0,
        completed=0,
        skipped=skipped,
        cap_reached=cap_reached,
    )
    if dry_run or not eligible:
        return summary
    if ui is None:
        raise ValueError("a Lovart UI driver is required for a non-dry run")

    if not manifest.project_id:
        manifest.project_id = await ui.ensure_project(plan.project_name)
        manifest.project_url = getattr(ui, "project_url", None)
        save_manifest(plan.article, manifest)

    submitted = 0
    completed = 0
    for job in eligible:
        if job.output.exists():
            raise RuntimeError(f"refusing to submit while output already exists: {job.output}")
        manifest.record_submitted(job, datetime.now().astimezone().isoformat())
        save_manifest(plan.article, manifest)
        submitted += 1
        try:
            output = await ui.generate_and_download(job)
            if Path(output) != job.output or not job.output.is_file() or job.output.stat().st_size == 0:
                raise RuntimeError("Lovart download did not produce the expected non-empty output")
        except Exception as exc:
            manifest.jobs[job.fingerprint]["last_error"] = _sanitized_error(exc)
            save_manifest(plan.article, manifest)
            raise
        manifest.mark_completed(job.fingerprint, str(job.output))
        save_manifest(plan.article, manifest)
        completed += 1

    return RunSummary(
        project_name=summary.project_name,
        eligible=summary.eligible,
        submitted=submitted,
        completed=completed,
        skipped=summary.skipped,
        cap_reached=summary.cap_reached,
    )


def _canvas_url(manifest: Manifest) -> str:
    if manifest.project_url:
        return manifest.project_url
    if manifest.project_id:
        return f"{LOVART_CANVAS_URL}?{urlencode({'projectId': manifest.project_id})}"
    return LOVART_CANVAS_URL


async def run_with_browser(article: Path, profile: Path, retry_failed: bool, max_new: int) -> RunSummary:
    """Preflight local state before launching Chrome, then run through the visible UI."""

    if not 1 <= max_new <= DAILY_LIMIT:
        raise ValueError(f"max-new must be between 1 and {DAILY_LIMIT}")
    plan = discover_article(article)
    manifest = load_manifest(plan.article, plan.project_name)
    image_dir = plan.article / "images"
    image_dir.mkdir(parents=True, exist_ok=True)
    connection = launch_or_reuse_chrome(profile, _canvas_url(manifest))
    cdp = await CdpClient.connect(connection.browser_ws_url)
    try:
        page = await open_canvas_page(cdp, _canvas_url(manifest), image_dir)
        await asyncio.sleep(2)
        return await run_article(
            plan.article,
            ui=LovartCanvasUi(page, image_dir),
            today=datetime.now().astimezone().date().isoformat(),
            max_new=max_new,
            retry_failed=retry_failed,
        )
    finally:
        await cdp.close()


def _print_summary(summary: RunSummary, dry_run: bool) -> None:
    prefix = "Dry run" if dry_run else "Lovart run"
    print(f"{prefix}: {summary.project_name}")
    for job in summary.eligible:
        print(f"  {'would generate' if dry_run else 'generated'} {job.source.name} ({job.aspect_ratio}) -> {job.output}")
    print(
        f"  submitted={summary.submitted} completed={summary.completed} "
        f"skipped={summary.skipped} cap_reached={summary.cap_reached}"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate one article's images through Lovart Canvas")
    parser.add_argument("--article", type=Path, required=True)
    parser.add_argument("--profile-dir", type=Path, default=DEFAULT_PROFILE)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--retry-failed", action="store_true")
    parser.add_argument("--max-new", type=int, default=DAILY_LIMIT)
    args = parser.parse_args(argv)
    today = datetime.now().astimezone().date().isoformat()
    try:
        if args.dry_run:
            summary = asyncio.run(
                run_article(args.article, ui=None, today=today, max_new=args.max_new, dry_run=True)
            )
        else:
            summary = asyncio.run(
                run_with_browser(args.article, args.profile_dir, args.retry_failed, args.max_new)
            )
    except (LovartUiBlocked, RuntimeError, ValueError) as exc:
        print(f"❌ {_sanitized_error(exc)}")
        return 2
    _print_summary(summary, args.dry_run)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


def strip_front_matter(raw: str) -> str:
    """Return Markdown body after an optional leading YAML front-matter block."""

    match = re.match(r"^---\s*\n.*?\n---\s*\n?", raw, flags=re.DOTALL)
    return raw[match.end() :].strip() if match else raw.strip()


def article_title(article: Path) -> str:
    """Use the published WeChat title when available, otherwise the directory name."""

    source = article / "weixin.md"
    if not source.exists():
        return article.name

    match = re.search(
        r'^title:\s*(?:"([^"]+)"|\'([^\']+)\'|([^#\n]+))\s*$',
        source.read_text(encoding="utf-8"),
        flags=re.MULTILINE,
    )
    if not match:
        return article.name

    return next((value.strip() for value in match.groups() if value and value.strip()), article.name)


def discover_article(article: Path) -> ArticlePlan:
    """Read and validate the prompt files for one article directory."""

    article = article.resolve()
    prompt_dir = article / "prompts"
    if not prompt_dir.is_dir():
        raise ValueError(f"missing prompts directory: {prompt_dir}")

    jobs: list[PromptJob] = []
    for source in sorted(prompt_dir.glob("*.md")):
        prompt = strip_front_matter(source.read_text(encoding="utf-8"))
        if not prompt:
            raise ValueError(f"{source.name} is empty after front matter")
        aspect_ratio = "21:9" if source.name.startswith("00-cover") else "1:1"
        jobs.append(
            PromptJob(
                source=source,
                prompt=prompt,
                aspect_ratio=aspect_ratio,
                output=article / "images" / f"{source.stem}.png",
            )
        )

    if not jobs:
        raise ValueError(f"no prompt Markdown files found in {prompt_dir}")
    return ArticlePlan(article=article, project_name=article_title(article), jobs=tuple(jobs))
