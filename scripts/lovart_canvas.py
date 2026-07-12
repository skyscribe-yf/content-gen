"""Generate article images through Lovart Canvas's visible browser UI.

This experimental helper is intentionally separate from the apimart client. It
reads article prompt Markdown files and will later drive a locally logged-in
browser rather than accepting exported cookies or private API credentials.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re


@dataclass(frozen=True)
class PromptJob:
    """One prompt file and its deterministic Lovart output contract."""

    source: Path
    prompt: str
    aspect_ratio: str
    output: Path


@dataclass(frozen=True)
class ArticlePlan:
    """The deterministic inputs required to generate one article's images."""

    article: Path
    project_name: str
    jobs: tuple[PromptJob, ...]


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
