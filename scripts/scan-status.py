#!/usr/bin/env python3
"""Scan content/ directories and detect file presence for draft-status.yaml.

Usage:
  python3 scripts/scan-status.py               # print status table
  python3 scripts/scan-status.py --summary      # print summary only
  python3 scripts/scan-status.py --check slug   # check one article
"""

import os
import sys
from pathlib import Path

CONTENT_DIR = Path(__file__).resolve().parent.parent / "content"

STATUS_ORDER = ["published", "scheduled", "ready", "drafting", "planned"]


def scan_article(dirpath: Path) -> dict:
    return {
        "slug": dirpath.name,
        "weixin": (dirpath / "weixin.md").exists(),
        "draft": (dirpath / "draft.md").exists(),
        "outline": (dirpath / "outline.md").exists(),
        "cover": (dirpath / "00-cover.png").exists(),
    }


def guess_status(files: dict) -> str:
    """Heuristic: infer status from files present."""
    if files["weixin"]:
        # Check if wechatUrl is in frontmatter → published
        wf = CONTENT_DIR / files["slug"] / "weixin.md"
        if wf.exists():
            text = wf.read_text(encoding="utf-8")
            if "wechatUrl:" in text:
                return "published"
            return "scheduled"  # weixin.md exists but no wechatUrl yet
    if files["draft"]:
        return "drafting"
    if files["outline"]:
        return "drafting"
    return "planned"


def scan_all():
    articles = []
    if not CONTENT_DIR.exists():
        print("content/ directory not found", file=sys.stderr)
        return articles
    for entry in sorted(CONTENT_DIR.iterdir()):
        if not entry.is_dir() or entry.name.startswith("."):
            continue
        files = scan_article(entry)
        # Only include directories that look like articles (have actual content files)
        if files["weixin"] or files["draft"] or files["outline"]:
            articles.append(files)
    return articles


def print_table(articles: list):
    header = f"{'SLUG':<35} {'WXN':>3} {'DRF':>3} {'OUT':>3} {'COV':>3} {'STATUS':>10}"
    print(header)
    print("-" * len(header))
    for a in articles:
        status = guess_status(a)
        print(
            f"{a['slug']:<35} "
            f"{'✓' if a['weixin'] else ' ':>3} "
            f"{'✓' if a['draft'] else ' ':>3} "
            f"{'✓' if a['outline'] else ' ':>3} "
            f"{'✓' if a['cover'] else ' ':>3} "
            f"{status:>10}"
        )


def print_summary(articles: list):
    counts = {s: 0 for s in STATUS_ORDER}
    for a in articles:
        counts[guess_status(a)] += 1
    drafting = [a["slug"] for a in articles if guess_status(a) == "drafting"]
    ready = [a["slug"] for a in articles if guess_status(a) == "ready"]

    print(f"Total: {len(articles)} articles in content/")
    print()
    for s in STATUS_ORDER:
        print(f"  {s:<10}: {counts[s]}")
    if drafting:
        print(f"\nDrafting: {', '.join(drafting)}")
    if ready:
        print(f"Ready:    {', '.join(ready)}")
    if not drafting and not ready:
        print("\nNo drafts in progress — queue is empty.")


if __name__ == "__main__":
    articles = scan_all()
    if not articles:
        sys.exit(1)

    if "--summary" in sys.argv or "-s" in sys.argv:
        print_summary(articles)
    elif "--check" in sys.argv:
        idx = sys.argv.index("--check")
        slug = sys.argv[idx + 1]
        match = [a for a in articles if a["slug"] == slug]
        if match:
            a = match[0]
            print(f"slug:    {a['slug']}")
            print(f"weixin:  {a['weixin']}")
            print(f"draft:   {a['draft']}")
            print(f"outline: {a['outline']}")
            print(f"cover:   {a['cover']}")
            print(f"status:  {guess_status(a)}")
        else:
            print(f"Not found: {slug}")
    else:
        print_table(articles)
