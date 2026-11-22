#!/usr/bin/env python3
"""Convert Markdown to WeChat HTML using mdnice (Playwright automation)."""

import sys
import argparse
import os


def convert(markdown_path: str, theme: str = "scienceBlue", code_theme: str = "atom-one-dark") -> str:
    from mdnice import to_wechat

    options = {
        "theme": theme,
        "code_theme": code_theme,
        "mac_style": False,
        "headless": True,
        "wait_timeout": 60,
        "retry_count": 2,
    }
    proxy = os.environ.get("MDNICE_PROXY")
    if proxy:
        options["proxy"] = {"server": proxy}
    # 2026-11-15：mdnice 包默认首选镜像 xiaoqiangclub.github.io/md/ 已 404（Playwright 等
    # .CodeMirror 白等 60 秒超时才走备用），把 wechat-api.ts 的 120s 子进程上限耗光导致存稿失败。
    # MDNICE_URL 环境变量可指定首选镜像；不设则用已验证可用的 whaoa 备用址。
    options["editor_url"] = os.environ.get("MDNICE_URL", "https://whaoa.github.io/markdown-nice/")
    html = to_wechat(markdown_path, **options)
    return html


def main():
    parser = argparse.ArgumentParser(description="Convert Markdown to WeChat HTML via mdnice")
    parser.add_argument("markdown", help="Path to markdown file")
    parser.add_argument("--theme", default="scienceBlue", help="Article theme (default: scienceBlue)")
    parser.add_argument("--code-theme", default="atom-one-dark", help="Code theme")
    parser.add_argument("--output", help="Output HTML file path (default: stdout)")
    args = parser.parse_args()

    html = convert(args.markdown, theme=args.theme, code_theme=args.code_theme)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"HTML saved to {args.output} ({len(html)} bytes)", file=sys.stderr)
    else:
        print(html)


if __name__ == "__main__":
    main()
