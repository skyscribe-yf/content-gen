#!/usr/bin/env python3
"""AI 味改写门禁（docs/ai-flavor-review.md 循环的机械闸门）。

orchestrator 在每轮 `ai-flavor-rewriter` 回传落盘后跑本脚本，比对改写前(pre) /
改写后(post) 两个版本的不变量。FAIL 项由 orchestrator 原样并入下一轮 findings
交回改写 lane——orchestrator 自己不修正文。

用法:
  python3 scripts/ai_flavor_gate.py <pre.md> <post.md> [--dir <文章目录>] [--max-delta 0.15]

--dir：给文章目录时，从 quality_check.json 读 slots 核原声逐字在场；目录有
       draft.md（手写稿分支）时逐段核作者原稿未被改写。
--max-delta：CJK 字数变化上限（默认 0.15）。

退出码 0 = 全部通过；1 = 有 FAIL（明细见输出末尾「门禁 FAIL」节，可直抄进下一轮 findings）。
"""
import difflib
import json
import re
import sys
from pathlib import Path

# 回归防线：这些词在作者语料基线 ≈0，改写后只许减少不许增多
HARD_AI_WORDS = [
    "值得注意的是", "让我们来", "总而言之", "综上所述", "不难发现", "不难看出",
    "需要指出的是", "深入探讨", "全面分析", "起着至关重要的作用", "由上可知",
    "今天我们来聊聊", "随着AI的发展", "随着 AI 的发展", "综合来看", "在很大程度上",
    "旨在", "从而", "随着", "的同时", "在此基础上", "与此同时", "包括但不限于",
    "不仅", "使得", "上述", "如下", "其一", "其二",
]


def cjk(s: str) -> int:
    return len(re.findall(r"[\u4e00-\u9fff]", s))


def flat(s: str) -> str:
    return re.sub(r"\s+", "", s)


def slot_score(slot: str, text: str) -> float:
    a, b = flat(slot), flat(text)
    if not a:
        return 0.0
    if a in b:
        return 1.0
    sm = difflib.SequenceMatcher(None, a, b)
    for block in sm.get_matching_blocks():
        if block.size >= len(a) * 0.9:
            return block.size / len(a)
    return sm.quick_ratio()


def frontmatter(text: str) -> dict:
    if not text.startswith("---"):
        return {}
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}
    fm = {}
    for ln in parts[1].splitlines():
        m = re.match(r"^([A-Za-z_]+):\s*(.*)$", ln.strip())
        if m:
            fm[m.group(1)] = m.group(2).strip().strip('"').strip("'")
    return fm


def body(text: str) -> str:
    return text.split("---", 2)[-1] if text.startswith("---") else text


def images(text: str):
    return sorted(re.findall(r"!\[[^\]]*\]\(([^)]+)\)", text))


def clean_body(text: str) -> str:
    """去 frontmatter / HTML 注释 / 代码块 / 公式 / 图片；链接还原为链接文字。"""
    s = text
    if s.startswith("---"):
        parts = s.split("---", 2)
        if len(parts) >= 3:
            s = parts[2]
    s = re.sub(r"<!--.*?-->", " ", s, flags=re.S)
    s = re.sub(r"```.*?```", " ", s, flags=re.S)
    s = re.sub(r"\$\$.*?\$\$", " ", s, flags=re.S)
    s = re.sub(r"\$[^$\n]+\$", " ", s)
    s = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", s)
    s = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", s)
    return s


def urls(text: str):
    return sorted(set(re.findall(r"https?://[^\s)\]\"']+", body(text))))


def formula_counts(text: str):
    disp = len(re.findall(r"\$\$.*?\$\$", text, re.S))
    inline = len(re.findall(r"\$[^$\n]+\$", text))
    return disp, inline


def paragraphs_of(text: str):
    s = clean_body(text)
    out = []
    for block in re.split(r"\n\s*\n", s):
        lines = []
        for ln in block.splitlines():
            t = ln.strip()
            if not t or t[0] in "#>|`" or t.startswith("!["):
                continue
            if re.match(r"^(\d+\.|[-*+])\s", t) or re.match(r"^https?://", t):
                continue
            lines.append(re.sub(r"\*{1,2}", "", t))
        if lines:
            out.append(" ".join(lines))
    return out


def best_match(para: str, candidates):
    """para 在候选段落里的最佳匹配分：quick_ratio 预筛 top3 再精算（省 O(n²) 精算）。"""
    flat_p = flat(para)
    ranked = sorted(candidates,
                    key=lambda q: -difflib.SequenceMatcher(None, flat_p, flat(q)).quick_ratio())
    return max((slot_score(para, q) for q in ranked[:3]), default=0.0)


def main():
    argv = sys.argv[1:]
    if len(argv) < 2 or argv[0].startswith("--"):
        print(__doc__)
        sys.exit(2)
    pre_p, post_p = Path(argv[0]), Path(argv[1])
    pre, post = pre_p.read_text(encoding="utf-8"), post_p.read_text(encoding="utf-8")

    def flag_value(name, default=None):
        return argv[argv.index(name) + 1] if name in argv else default

    max_delta = float(flag_value("--max-delta", "0.15"))
    _dir = flag_value("--dir")
    art_dir = Path(_dir) if _dir else None

    results = []  # (ok, label, detail, fix)

    def chk(cond, label, detail="", fix=""):
        results.append((bool(cond), label, detail, fix))

    # 1 frontmatter
    fm_pre, fm_post = frontmatter(pre), frontmatter(post)
    diff_fm = {k: (fm_pre.get(k), fm_post.get(k)) for k in set(fm_pre) | set(fm_post)
               if fm_pre.get(k) != fm_post.get(k)}
    chk(not diff_fm, "frontmatter 未变", f"漂移字段：{diff_fm}" if diff_fm else "",
        "恢复 frontmatter 原值")

    # 2 占位符
    n_pre, n_post = pre.count("【作者填入】"), post.count("【作者填入】")
    chk(n_pre == n_post, "【作者填入】占位符数量不变", f"pre={n_pre} post={n_post}",
        "按 pre 版恢复占位符（位置与数量）")

    # 3 图片引用集合
    img_pre, img_post = images(pre), images(post)
    chk(img_pre == img_post, "图片占位集合不变",
        f"丢失：{set(img_pre)-set(img_post)}；新增：{set(img_post)-set(img_pre)}",
        "恢复 pre 版的图片占位（文件名与数量）")

    # 4 公式数量
    f_pre, f_post = formula_counts(pre), formula_counts(post)
    chk(f_pre == f_post, "公式数量不变", f"pre(独立/内联)={f_pre} post={f_post}",
        "恢复被改动/丢失的公式")

    # 5 URL 集合（含内链）
    u_pre, u_post = urls(pre), urls(post)
    chk(u_pre == u_post, "URL 集合不变",
        f"丢失：{set(u_pre)-set(u_post)}；新增：{set(u_post)-set(u_pre)}",
        "恢复 pre 版的全部链接")

    # 6 热门文章占位行
    chk(("<!-- HOT_ARTICLES -->" in pre) == ("<!-- HOT_ARTICLES -->" in post),
        "HOT_ARTICLES 占位行在位", "post 丢失占位行" if "<!-- HOT_ARTICLES -->" in pre else "",
        "在尾部原位恢复 <!-- HOT_ARTICLES --> 占位行")

    # 7 原声未被改写破坏
    # slots：绝对阈值（与 quality_check.py 终检口径一致，≥0.9）
    # draft.md 段落：相对阈值（post 不得比 pre 更差 >5%）——历史篇成稿匹配度本就
    # 不满 0.85，绝对阈值会误报；本门禁管的是「本轮改写没进一步破坏原声」。
    slots, voice_fails = [], []
    if art_dir:
        cfg_p = art_dir / "quality_check.json"
        if cfg_p.exists():
            slots = json.loads(cfg_p.read_text(encoding="utf-8")).get("slots", [])
        for i, s in enumerate(slots, 1):
            sc = slot_score(s, post)
            if sc < 0.9:
                voice_fails.append(f"slot {i}（相似度 {sc:.0%}）")
        draft_p = art_dir / "draft.md"
        if draft_p.exists():
            pre_paras = paragraphs_of(pre)
            post_paras = paragraphs_of(post)
            for p in paragraphs_of(draft_p.read_text(encoding="utf-8")):
                if cjk(p) < 40 or "【" in p:
                    continue
                b_post = best_match(p, post_paras)
                b_pre = best_match(p, pre_paras)
                if b_post < b_pre - 0.05:
                    voice_fails.append(f"draft 段（{b_pre:.0%}→{b_post:.0%}）：{p[:36]}…")
    chk(not voice_fails, "原声未被改写破坏（slots ≥0.9；draft 段不降 >5%）",
        "；".join(voice_fails[:6]) if voice_fails else "",
        "按原稿逐字恢复被进一步改写的原声句")

    # 8 字数变化
    c_pre, c_post = cjk(pre), cjk(post)
    delta = abs(c_post - c_pre) / max(c_pre, 1)
    chk(delta <= max_delta, f"CJK 字数变化 ≤{max_delta:.0%}", f"{c_pre} → {c_post}（{delta:+.1%}）",
        "收紧改动范围：只改 findings 指向的位置")

    # 9 AI 味词回归（post 只许少不许多）
    regr = []
    for w in HARD_AI_WORDS:
        a, b = pre.count(w), post.count(w)
        if b > a:
            regr.append(f"{w} {a}→{b}")
    chk(not regr, "硬 AI 味词未新增", "；".join(regr) if regr else "",
        "换掉新增的 AI 味词（口语替换）")

    # 10 结构底线
    h2_post = len(re.findall(r"^## ", post, re.M))
    chk(h2_post >= 5, "## 节 ≥5", f"post H2={h2_post}", "补回被合并/删掉的节标题")
    first = next((l.strip() for l in body(post).splitlines() if l.strip()), "")
    chk(not first.startswith("#"), "正文首段非标题开场", f"首行：{first[:30]}",
        "把标题改成钩子文本开头")

    n_fail = sum(1 for ok, *_ in results if not ok)
    print("════ AI 味改写门禁 ════")
    for ok, label, detail, fix in results:
        print(("  ✓ " if ok else "  ✗ ") + label + (f"｜{detail}" if detail and not ok else ""))
    if n_fail:
        print(f"\n## 门禁 FAIL（作为下一轮 findings 交给 ai-flavor-rewriter）")
        for i, (ok, label, detail, fix) in enumerate((r for r in results if not r[0]), 1):
            print(f"| GATE-{i} | FAIL | 全文 | {label} | {detail} | {fix} | 机械门禁 |")
    print(f"\n{'✅ 门禁全部通过' if not n_fail else f'⛔ 门禁 FAIL {n_fail} 项'}")
    sys.exit(0 if not n_fail else 1)


if __name__ == "__main__":
    main()
