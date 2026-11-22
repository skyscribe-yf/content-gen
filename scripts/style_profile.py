#!/usr/bin/env python3
"""蒸馏作者行文风格 profile——AI 味审查（docs/ai-flavor-review.md）rhythm lane 的对照基准。

语料（默认）= 作者原稿：content/*/draft.md + content/*/raw.md（最纯的「原文行文」信号）。
--include-published 时追加已发布 content/*/weixin.md（经后台回拉同步，次纯；贴图目录自动排除）。
--exclude <目录> 排除当前篇（避免把手写稿的原文混进基准，循环对照）。

输出：人读文本 profile（默认 stdout，供主 agent 内联进各审查 lane 的任务消息）；
      --json 机器版；--out <文件> 同时落盘（推荐存 .grill/<slug>-style-profile.txt）。

判读口径见输出末尾「判读口径」节；词表与 docs/article-quality-check.md 第 15 项、
branding/style-corpus/style-features.md 保持一致。
"""
import argparse
import json
import re
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONTENT = ROOT / "content"

# 作者口头禅/功能词候选（安全词，避开会在术语里误匹配的单字）
AUTHOR_WORDS = [
    "然而", "其实", "不过", "事实上", "实际上", "本质上", "某种程度上", "当然",
    "嘛", "呗", "说白了", "换句话说", "话说回来", "顺便", "基本上", "大概",
    "可能", "似乎", "简直", "压根", "顺手", "愣", "琢磨", "捋", "搞", "扯",
]
# AI 味词表（真讲师腔 + 塑料翻译腔 + 公文黑话；与 lexicon lane 提示词同源）
AI_WORDS = [
    "值得注意的是", "让我们来", "总而言之", "综上所述", "不难发现", "不难看出",
    "需要指出的是", "深入探讨", "全面分析", "起着至关重要的作用", "由上可知",
    "今天我们来聊聊", "随着AI的发展", "随着 AI 的发展", "表现优异", "具有显著优势",
    "综合来看", "在很大程度上", "旨在", "从而", "基于", "对于", "而言", "之一",
    "包括但不限于", "进行", "加以", "予以", "开展", "推进", "打造", "构建",
    "赋能", "抓手", "闭环", "颗粒度", "不仅", "而且", "使得", "通过",
    "的方式", "随着", "的同时", "在此基础上", "与此同时", "上述", "如下",
    "首先", "其次", "最后",
]

EXCLUDE_DIR_NAMES = {"test", "promote", "navigation", "collection-covers", "gradient-series"}


def is_tietu(p: Path) -> bool:
    """贴图轨道（手敲 digest / 截图转述）是另一体裁，禁混进贴图以外的长文基准。"""
    if any("tietu" in part for part in p.parts):
        return True
    try:
        head = p.read_text(encoding="utf-8")[:800]
    except (OSError, UnicodeDecodeError):
        return False
    return ("类型：贴图" in head) or ("图片消息" in head) or ("话题：<话题名>" in head)


def cjk(s: str) -> int:
    return len(re.findall(r"[\u4e00-\u9fff]", s))


def clean_text(raw: str) -> str:
    """去 frontmatter / 尾部热门区 / 注释 / 代码 / 公式 / 图片，链接还原为文字。"""
    s = raw
    if s.startswith("---"):
        parts = s.split("---", 2)
        if len(parts) >= 3:
            s = parts[2]
    s = re.split(r"^🔥", s, flags=re.M)[0]          # 热门文章区是脚本生成的，非作者行文
    s = re.sub(r"<!--.*?-->", " ", s, flags=re.S)   # HTML 注释
    s = re.sub(r"```.*?```", " ", s, flags=re.S)    # 代码块
    s = re.sub(r"\$\$.*?\$\$", " ", s, flags=re.S)  # 展示公式
    s = re.sub(r"\$[^$\n]+\$", " ", s)              # 内联公式
    s = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", s)     # 图片
    s = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", s)  # 链接 → 链接文字
    return s


def paragraphs(s: str):
    """正文段落：跳过标题/引用/列表/表格/图片/纯 URL/粗体标签行；只留像散文的块。"""
    out = []
    for block in re.split(r"\n\s*\n", s):
        lines = []
        for ln in block.splitlines():
            t = ln.strip()
            if not t or t[0] in "#>|`":
                continue
            if t.startswith("**"):
                continue                      # 粗体标签行（**段 1（日期）——主题：**）
            if re.match(r"^(\d+\.|[-*+])\s", t) or t.startswith("!["):
                continue
            if re.match(r"^https?://", t):
                continue
            t = re.sub(r"\*{1,2}", "", t)     # 去残余强调标记
            t = re.sub(r"^#+\s*", "", t)      # 去行内残余标题记号
            if t:
                lines.append(t)
        if lines:
            out.append(" ".join(lines))
    return out


def prose_paras(paras):
    """只保留像散文的段落（≥2 句且 ≥60 字）——排除标签块/醒目句/残块，供段落统计用。"""
    out = []
    for p in paras:
        if "【" in p:                        # 模板脚手架（【作者填入】【图样：…】）
            continue
        if len(sentences(p)) >= 2 and cjk(p) >= 60:
            out.append(p)
    return out


def sentences(text: str):
    parts = re.findall(r"[^。！？!?…]+[。！？!?…]?", text)
    return [p.strip() for p in parts if cjk(p) >= 2]


def pct(sorted_vals, p):
    if not sorted_vals:
        return 0
    i = min(len(sorted_vals) - 1, max(0, round(p / 100 * (len(sorted_vals) - 1))))
    return sorted_vals[i]


def collect(files):
    """返回（ prose 全文, 散文段列表, 句子列表）。句子只从过滤后的段落里切——
    标题/引用/列表/标签行的脚手架不得进统计。"""
    prose_blocks, paras = [], []
    for f in files:
        try:
            raw = f.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        s = clean_text(raw)
        file_paras = paragraphs(s)
        if not file_paras:
            continue
        paras.extend(file_paras)
        prose_blocks.extend(file_paras)
    text = "\n".join(prose_blocks)
    sents = [x for p in paras for x in sentences(p)]
    return text, paras, sents


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--include-published", action="store_true",
                    help="追加已发布 content/*/weixin.md（frontmatter wechatUrl 非空）")
    ap.add_argument("--exclude", default="",
                    help="排除目录（当前篇，避免循环对照），如 content/2026-11-15-foo")
    ap.add_argument("--out", default="", help="人读 profile 同时写入该文件")
    ap.add_argument("--json", action="store_true", help="输出机器版 JSON")
    args = ap.parse_args()

    excl = Path(args.exclude).resolve() if args.exclude else None

    def wanted(p: Path) -> bool:
        if excl and (p.parent.resolve() == excl or excl in p.parents):
            return False
        if any(part in EXCLUDE_DIR_NAMES for part in p.parts):
            return False
        return not is_tietu(p)

    files = []
    for name in ("draft.md", "raw.md"):
        files += [p for p in sorted(CONTENT.glob(f"*/{name}")) if wanted(p)]
    src = "作者原稿 draft.md + raw.md"
    if args.include_published:
        pub = []
        for p in sorted(CONTENT.glob("*/weixin.md")):
            if not wanted(p):
                continue
            head = p.read_text(encoding="utf-8")[:600]
            m = re.search(r'wechatUrl:\s*["\']?(https?://\S+)', head)
            if m:
                pub.append(p)
        files += pub
        src += f" + 已发布 weixin.md（{len(pub)} 篇）"

    if not files:
        print("❌ 语料为空：content/ 下找不到 draft.md / raw.md", file=sys.stderr)
        sys.exit(1)

    text, paras_all, sents = collect(files)
    total_cjk = cjk(text)
    if total_cjk < 500 or len(sents) < 30:
        print(f"❌ 语料太小（{total_cjk} 字 / {len(sents)} 句），profile 不可信", file=sys.stderr)
        sys.exit(1)

    sents = [x for x in sents if "【" not in x]      # 模板脚手架句
    paras = prose_paras(paras_all)                   # 段落统计只用散文段
    lens = sorted(cjk(x) for x in sents)
    n = len(lens)
    short = sum(1 for x in lens if x < 15)
    mid = sum(1 for x in lens if 15 <= x <= 40)
    long_ = n - short - mid
    para_sent_counts = [len(sentences(p)) for p in paras]
    para_lens = sorted(cjk(p) for p in paras)

    def per100(word):
        return text.count(word) / total_cjk * 100

    author_freq = [(w, per100(w)) for w in AUTHOR_WORDS]
    author_freq = [(w, f) for w, f in author_freq if f > 0][:12]
    ai_freq = sorted(((w, per100(w)) for w in AI_WORDS), key=lambda t: -t[1])[:18]

    q_ratio = sum(1 for x in sents if x.rstrip().endswith(("？", "?"))) / n
    ex_ratio = sum(1 for x in sents if x.rstrip().endswith(("！", "!"))) / n
    comma = text.count("，") / total_cjk * 100
    first_person = (text.count("我") + text.count("你")) / total_cjk * 100

    reps_long = sorted(sents, key=lambda x: -cjk(x))[:3]
    reps_short = sorted((x for x in sents if cjk(x) >= 10), key=cjk)[:3]

    def clip(s, k=88):
        s = re.sub(r"\s+", " ", s).strip()
        s = re.sub(r"[#*>]+", "", s)
        return s if len(s) <= k else s[:k] + "…"

    med = statistics.median(lens)
    lines = []
    lines.append(f"# 作者行文 profile（style_profile.py 生成；{len(files)} 篇 / {total_cjk} 字；语料：{src}）")
    lines.append("## 句长（CJK 字符/句）")
    lines.append(f"中位数 {med:.0f} | 均值 {statistics.mean(lens):.0f} | p10 {pct(lens,10)} | p90 {pct(lens,90)} | "
                 f"短句(<15) {short/n:.0%} | 中句(15-40) {mid/n:.0%} | 长句(>40) {long_/n:.0%}")
    lines.append("## 段落")
    lines.append(f"每段句数 中位数 {statistics.median(para_sent_counts):.0f} | 段长 中位数 {statistics.median(para_lens):.0f} 字 | "
                 f"段长 p90 {pct(para_lens,90)} | 段落数 {len(paras)}")
    lines.append("## 标点与口吻")
    lines.append(f"逗号密度 {comma:.1f}/百字 | 第一人称(我/你) {first_person:.1f}/百字 | 问句 {q_ratio:.0%} | 感叹句 {ex_ratio:.0%}")
    lines.append("## 作者高频功能词（每百字；这些不是 AI 腔，禁删）")
    lines.append(" | ".join(f"{w} {f:.2f}" for w, f in author_freq) or "（无）")
    lines.append("## AI 味词在作者语料中的频率（每百字；接近 0 = 本文出现即可疑）")
    lines.append(" | ".join(f"{w} {f:.2f}" for w, f in ai_freq) or "（无）")
    lines.append("## 代表长句（节奏对照）")
    lines += [f"- {clip(s)}" for s in reps_long]
    lines.append("## 代表短句（节奏对照）")
    lines += [f"- {clip(s)}" for s in reps_short]
    lines.append("## 判读口径（rhythm lane 对照用）")
    lines.append(f"- 本文句长中位数偏离作者中位数（{med:.0f}）超 50% → 节奏异常，逐段查")
    lines.append(f"- 连续 ≥4 句句长落在 [{med*0.9:.0f}, {med*1.1:.0f}] → 匀速套路，拆长补短")
    lines.append("- 每段句数恒为 3 且 ≥4 段 → 模板段，合段或变句数")
    lines.append(f"- 短句占比 <{max(8, short/n*100-6):.0f}% 或缺 >40 字长句 → 长句链无喘息")
    lines.append("- AI 味词本文频率 > 作者基线 5 倍 → 重点嫌疑，逐处替换")
    profile = "\n".join(lines)

    if args.json:
        print(json.dumps({
            "files": len(files), "cjk": total_cjk, "sentences": n, "paragraphs": len(paras),
            "sent_len": {"median": med, "mean": statistics.mean(lens),
                         "p10": pct(lens, 10), "p90": pct(lens, 90),
                         "short_pct": short / n, "mid_pct": mid / n, "long_pct": long_ / n},
            "para_sent_median": statistics.median(para_sent_counts),
            "para_len_median": statistics.median(para_lens),
            "comma_per100": comma, "first_person_per100": first_person,
            "question_ratio": q_ratio, "exclam_ratio": ex_ratio,
            "author_words": author_freq, "ai_words": ai_freq,
        }, ensure_ascii=False, indent=1))
    else:
        print(profile)

    if args.out:
        outp = Path(args.out)
        outp.parent.mkdir(parents=True, exist_ok=True)
        outp.write_text(profile + "\n", encoding="utf-8")
        print(f"\n（已写入 {outp}）", file=sys.stderr)


if __name__ == "__main__":
    main()
