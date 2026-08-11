#!/usr/bin/env python3
"""按台词特征自动插入 MiniMax 拟声标签（speech-2.8 系列，22 个固定标签）。

规则映射（2026-08-11 A/B 实测：标签版听感最好，每段 ≤2 个标签）:
  段首问句钩子   → (breath)   先吸气再开口，设疑感
  转折爆点       → <#0.5#>   转折词（但/但是/可是/然而/不过）前显式停顿 0.5s
                  （2026-08-12 修正：原 (inhale) 被用户否掉——拟声标签只管发声
                   不管停留，转折前要「停留」用显式停顿）
  数字对比       → (gasps)    对比词（对/比/vs）后的数字前，突出数据差
  无奈/安抚      → (sighs)    别慌/别急/算了/唉 前
  语气词         → (emm)      嗯/呃/其实 前，思考停顿

约束:
  - 标签只进 TTS 输入文本，勿写入 tts.txt（字幕基准，见 SKILL.md）
  - 已含同标签的行跳过（幂等），不会重复插
  - 整段生成（full.txt）同样可用：MiniMax 2.8 原生支持，可直接手写进文本


用法:
  python3 scripts/add_tts_tags.py --text "为什么 loss 一直抖？但别慌。"
  python3 scripts/add_tts_tags.py --text-file /tmp/tts_s1.txt --out /tmp/tts_s1_tagged.txt
  python3 scripts/add_tts_tags.py --self-test
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

RULES = [
    # (name, tag, find_fn) — 按优先级依次尝试，插满 max_tags 即停
    (
        "breath",
        "(breath)",
        lambda s: (
            0
            if re.match(r"^(怎么|为什么|凭什么|为何|多少|哪|谁|什么|难道|是不是)", s)
            or re.match(r"^[^，。！!]{0,4}[？?]", s)
            else None
        ),
    ),
    (
        "pause",
        "<#0.5#>",
        lambda s: min(
            (p for kw in ("但是", "可是", "然而", "不过", "但") if (p := s.find(kw)) > 0),
            default=None,
        ),
    ),
    (
        "gasps",
        "(gasps)",
        lambda s: (
            m.start(2)
            if (m := re.search(r"(对|比|vs|VS)\s*(\d[\d.,]*\s*(?:MB|GB|KB|TB|%|倍|万|亿))", s))
            else None
        ),
    ),
    (
        "sighs",
        "(sighs)",
        lambda s: next((s.find(kw) for kw in ("别慌", "别急", "算了", "唉") if kw in s), None),
    ),
    (
        "emm",
        "(emm)",
        lambda s: next((s.find(kw) for kw in ("嗯", "呃", "其实") if kw in s), None),
    ),
]


def tag_line(line: str, max_tags: int = 2) -> str:
    s = line.strip()
    if not s:
        return line
    for name, tag, find in RULES:
        if tag in s:
            continue  # 幂等：已有同标签
        n = sum(s.count(f"({r[0]})") for r in RULES)
        if n >= max_tags:
            break
        pos = find(s)
        if pos is None:
            continue
        s = s[:pos] + tag + " " + s[pos:]
    return s


def process(text: str, max_tags: int) -> str:
    return "\n".join(tag_line(ln, max_tags) for ln in text.splitlines())


def self_test() -> None:
    cases = [
        # (输入, 期望, 说明)
        ("为什么 loss 一直抖？但别慌，我们先看直觉。",
         "(breath) 为什么 loss 一直抖？<#0.5#> 但(sighs) 别慌，我们先看直觉。", "问句钩子+转折"),
        ("9MB 对 72MB——省了 8 倍。",
         "9MB 对 (gasps) 72MB——省了 8 倍。", "数字对比"),
        ("嗯，其实很简单。",
         "(emm) 嗯，其实很简单。", "语气词"),
        ("别慌，这集我们从直觉讲起。",
         "(sighs) 别慌，这集我们从直觉讲起。", "安抚"),
        ("梯度下降的直觉很简单。",
         "梯度下降的直觉很简单。", "无特征不加"),
        ("(sighs) 别慌，已经处理过了。",
         "(sighs) 别慌，已经处理过了。", "幂等不重复"),
        ("但问题是，这里有个坑。",
         "但问题是，这里有个坑。", "段首转折不加"),
    ]
    for inp, want, note in cases:
        got = tag_line(inp)
        assert got == want, f"[{note}] FAIL\n  in:  {inp}\n  got: {got}\n  want:{want}"
        print(f"ok  {note}: {got}")
    print("self-test passed")


def main() -> None:
    p = argparse.ArgumentParser(description="自动插入 MiniMax 拟声标签")
    p.add_argument("--text", help="Inline text")
    p.add_argument("--text-file", help="Path to input text file")
    p.add_argument("--out", help="Write result to file (default: stdout)")
    p.add_argument("--max-tags", type=int, default=2, help="每段最多标签数 (默认 2)")
    p.add_argument("--self-test", action="store_true", help="运行内置自检")
    args = p.parse_args()

    if args.self_test:
        self_test()
        return

    if args.text_file:
        text = Path(args.text_file).read_text(encoding="utf-8")
    elif args.text:
        text = args.text
    else:
        raise SystemExit("Provide --text or --text-file")

    out = process(text, args.max_tags)
    if args.out:
        Path(args.out).write_text(out, encoding="utf-8")
        print(f"saved {args.out}", file=sys.stderr)
    else:
        sys.stdout.write(out + ("\n" if not out.endswith("\n") else ""))


if __name__ == "__main__":
    main()
