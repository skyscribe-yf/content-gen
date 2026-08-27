#!/usr/bin/env python3
"""热门文章列表生成器 — 供公众号文章尾部「🔥 热门文章」块使用。

数据源（全部为项目内既有事实文件，不联网）：
  1. docs/wechat-data-audit-log.json —— 聚合所有审计快照的各文章「历史最高阅读量」，
     按阅读量降序取 Top N（最近一次审计自动包含在内）。
  2. 贴图过滤（贴图不计入热门）：合并三份清单
     - branding/style-corpus/publish-data*.json 中 item_show_type != 0 的标题
     - branding/style-corpus/tietu-corpus-summary.json 的标题
     - branding/style-corpus/tietu-extra.json 的人工补录（发布快照滞后时用）
  3. 链接解析：publish-data 的 content_url 优先；缺失时回退
     content/*/weixin.md 的 frontmatter（title + wechatUrl）精确匹配。

用法：
  python3 scripts/hot_articles.py                 # 人类可读表格（默认 Top 6）
  python3 scripts/hot_articles.py --md            # 尾部 markdown 块（含标题行，链接行以两个空格结尾=硬换行→<br>）
  python3 scripts/hot_articles.py --json          # JSON 结构
  python3 scripts/hot_articles.py --top 6 --md --cited content/2026-08-25-gae/weixin.md
        # --cited：追加该文正文/参考资料中引用的公众号文章（去重、排除当前篇）
  python3 scripts/hot_articles.py --exclude-title "某篇"   # 手动排除（默认随 --cited 自动排除当前篇）

配套规则：AGENTS.md「微信文章链接规则」；发布门禁 docs/pre-publish-final-check.md §6b。
"""
from __future__ import annotations

import argparse
import glob
import html
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_tietu_titles() -> set[str]:
    """三份来源合并的贴图标题集。"""
    titles: set[str] = set()

    for f in glob.glob(os.path.join(REPO, "branding/style-corpus/publish-data*.json")):
        try:
            data = json.load(open(f, encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        for item in data.get("publish_list", []):
            try:
                info = json.loads(html.unescape(item.get("publish_info", "")))
            except json.JSONDecodeError:
                continue
            for app in info.get("appmsg_info", []):
                if app.get("title") and app.get("item_show_type") not in (None, 0):
                    titles.add(app["title"])

    summary = os.path.join(REPO, "branding/style-corpus/tietu-corpus-summary.json")
    if os.path.exists(summary):
        for e in json.load(open(summary, encoding="utf-8")):
            if e.get("title"):
                titles.add(e["title"])

    extra = os.path.join(REPO, "branding/style-corpus/tietu-extra.json")
    if os.path.exists(extra):
        titles.update(json.load(open(extra, encoding="utf-8")).get("titles", []))

    return titles


def aggregate_reads() -> dict[str, int]:
    """跨全部审计快照，聚合每篇文章的历史最高阅读量。"""
    log = os.path.join(REPO, "docs/wechat-data-audit-log.json")
    data = json.load(open(log, encoding="utf-8"))
    best: dict[str, int] = {}
    for audit in data.get("audits", []):
        for art in audit.get("content", {}).get("articles", []):
            t, r = art.get("title", ""), art.get("reads", 0)
            if t and r > best.get(t, 0):
                best[t] = r
    return best


def url_from_publish_data() -> dict[str, str]:
    """publish-data 里的标题 → content_url。"""
    urls: dict[str, str] = {}
    for f in glob.glob(os.path.join(REPO, "branding/style-corpus/publish-data*.json")):
        try:
            data = json.load(open(f, encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        for item in data.get("publish_list", []):
            try:
                info = json.loads(html.unescape(item.get("publish_info", "")))
            except json.JSONDecodeError:
                continue
            for app in info.get("appmsg_info", []):
                if app.get("title") and app.get("content_url"):
                    urls.setdefault(app["title"], app["content_url"])
    return urls


def frontmatter_maps() -> tuple[dict[str, str], dict[str, str]]:
    """content/*/weixin.md 的 frontmatter：返回 (归一化标题→wechatUrl, wechatUrl→原始标题)。"""
    by_title: dict[str, str] = {}
    by_url: dict[str, str] = {}
    for f in glob.glob(os.path.join(REPO, "content/*/weixin.md")):
        text = open(f, encoding="utf-8").read()
        m = re.search(r"^title:\s*[\"']?([^\"'\n]+)", text, re.M)
        u = re.search(r"^wechatUrl:\s*[\"']?(https?://[^\"'\n]+)", text, re.M)
        if m and u:
            raw = m.group(1).strip()
            by_title[norm(raw)] = u.group(1)
            by_url.setdefault(u.group(1), raw)
    return by_title, by_url


def canonical_title(url: str, fm_by_url: dict[str, str], pub_urls: dict[str, str]) -> str:
    """URL → 正式标题：frontmatter 反查优先，publish-data 反查兜底。"""
    if url in fm_by_url:
        return fm_by_url[url]
    for t, u in pub_urls.items():
        if u == url:
            return t
    return url


def norm(s: str) -> str:
    """标题归一化：去空白、全半角标点统一。"""
    table = str.maketrans("？！，。：；（）", "?!,.:;()")
    return re.sub(r"\s+", "", s).translate(table)


def resolve_url(title: str, pub_urls: dict[str, str], fm_urls: dict[str, str]) -> str:
    if title in pub_urls:
        return pub_urls[title]
    return fm_urls.get(norm(title), "")


def extract_cited(md_path: str) -> list[tuple[str, str]]:
    """从文章提取 (标题, 微信URL) 的引用列表，只收单篇链接，去重保序。"""
    text = open(md_path, encoding="utf-8").read()
    out, seen = [], set()
    for m in re.finditer(r"\[([^\]]+)\]\((https://mp\.weixin\.qq\.com/s/[A-Za-z0-9_-]+)\)", text):
        title, url = m.group(1).strip(), m.group(2)
        title = re.sub(r"[*`>]", "", title)
        if url not in seen:
            seen.add(url)
            out.append((title, url))
    return out


def current_meta(md_path: str | None) -> tuple[str, str]:
    if not md_path:
        return "", ""
    text = open(md_path, encoding="utf-8").read()
    m = re.search(r"^title:\s*[\"']?([^\"'\n]+)", text, re.M)
    u = re.search(r"^wechatUrl:\s*[\"']?(https?://[^\"'\n]+)", text, re.M)
    return (m.group(1).strip() if m else ""), (u.group(1) if u else "")


def main() -> int:
    ap = argparse.ArgumentParser(description="生成公众号尾部热门文章列表")
    ap.add_argument("--top", type=int, default=6, help="榜单条数（默认 6）")
    ap.add_argument("--cited", metavar="WEIXIN_MD", help="追加该文引用的相关公众号文章")
    ap.add_argument("--exclude-title", help="额外排除的标题")
    ap.add_argument("--md", action="store_true", help="输出 markdown 块")
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    ap.add_argument("--self-check", action="store_true", help="回归自检（断言当前榜单锚点）")
    args = ap.parse_args()

    tietu = {norm(t) for t in load_tietu_titles()}

    reads = aggregate_reads()
    pub_urls = url_from_publish_data()
    fm_urls, fm_by_url = frontmatter_maps()

    # 排序并过滤
    cur_title, cur_url = "", ""
    if args.cited:
        cur_title, cur_url = current_meta(args.cited)
    exclude = set()
    if args.exclude_title:
        exclude.add(norm(args.exclude_title))
    if cur_title:
        exclude.add(norm(cur_title))

    rows: list[tuple[str, int, str]] = []
    for title, r in sorted(reads.items(), key=lambda kv: -kv[1]):
        if norm(title) in tietu or norm(title) in exclude:
            continue
        url = resolve_url(title, pub_urls, fm_urls)
        if not url:
            print(f"⚠️ 无 URL，跳过：{title}（{r} 读）", file=sys.stderr)
            continue
        rows.append((title, r, url))
    rows = rows[: args.top]

    if args.self_check:
        # 回归锚点：2026-08-27 审计后的文章 Top 6（贴图已过滤）。榜单结构变化时更新此断言。
        expected = ["KV缓存存进SSD：慢50倍的硬盘，为什么反而更快？",
                    "高维空间为什么全是壳？内积才是那把尺子",
                    "学习率怎么自动调？Adam 优化器拆给你看",
                    "DeepSeek-V4为何不用MLA？",
                    "高斯为什么二阶就够？非线性去哪了",
                    "SFT微调：1万条数据就能让模型听话？"]
        got = [t for t, _, _ in rows]
        assert got == expected, f"榜单漂移：{got}"
        assert all(u.startswith("https://mp.weixin.qq.com/s/") for _, _, u in rows)
        assert "严重过拟合的Deepseek，和魔幻的价格" not in got
        print(f"自检通过：Top {len(rows)} 与锚点一致")
        return 0

    if args.json:
        print(json.dumps(
            [{"title": t, "reads": r, "url": u} for t, r, u in rows],
            ensure_ascii=False, indent=2))
        return 0

    if args.md:
        print("🔥 **热门文章**：")
        print()
        for t, r, u in rows:
            print(f"[{t}]({u})  ")
        if args.cited:
            top_urls = {u for _, _, u in rows}
            for _, u in extract_cited(args.cited):
                if u == cur_url or u in top_urls:
                    continue
                print(f"[{canonical_title(u, fm_by_url, pub_urls)}]({u})  ")
                top_urls.add(u)
        return 0

    # 人类可读表格
    width = max(len(t) for t, _, _ in rows)
    for t, r, u in rows:
        print(f"{r:>6}  {t:<{width}}  {u}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
