"""Generate article images through Lovart Canvas's visible browser UI.

This experimental helper is intentionally separate from the apimart client. It
reads article prompt Markdown files and will later drive a locally logged-in
browser rather than accepting exported cookies or private API credentials.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import socket
import subprocess
import time

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
