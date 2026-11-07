#!/usr/bin/env python3
"""通用质量核查（机器可查部分）。替代过去每篇目录一份的 quality_check.py 副本。

用法:
  python3 scripts/quality_check.py <文章目录|weixin.md> [--published]

每篇定制项外置到文章目录的 quality_check.json：
  slots        作者原声句列表（逐字；容忍后台润色，相似度 ≥0.9 判在场）
  exempt       作者拍板豁免项（子集 of 段落超长/长句/篇幅），只提示不计 FAIL
  title_checks [{"text": "...", "label": "..."}] 标题必须包含的关键词/疑问句
  body_checks  同上，查正文
  numbers      承重数字列表（对回论文/台账）
  terms        本篇术语列表
  extra_terms  口径句（基座/算力/年份等）
  links        [{"id": "...", "label": "..."}] 必须出现的公众号文章内链 ID
  banned       本篇禁现词（分层纪律）
  body_min/body_max/all_max  篇幅口径（默认 1700/2300/2500）
  min_images   正文配图下限（默认 5）

缺 quality_check.json 时只跑通用门禁并提示跳过定制项（旧篇历史副本仍在各自目录）。
--published：发布后回拉模式，跳过成稿期门禁（原声/段落/长句/篇幅/爆款要素），
只查发布不变量（禁词/待发布/标签/图片路径/内链/承重数字/封面）。
"""
import difflib
import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent

_args = [a for a in sys.argv[1:] if not a.startswith("--")]
PUBLISHED = "--published" in sys.argv
if _args:
    _p = Path(_args[0])
    DIR = (_p if _p.is_dir() else _p.parent).resolve()
else:
    DIR = Path.cwd()

TEXT = (DIR / "weixin.md").read_text(encoding="utf-8")
BODY = TEXT.split("---", 2)[-1]

cfg = {}
_cfg_path = DIR / "quality_check.json"
if _cfg_path.exists():
    cfg = json.loads(_cfg_path.read_text(encoding="utf-8"))
else:
    print("⚠️ 无 quality_check.json——跳过本篇定制项（原声/承重数字/术语/内链）；"
          "旧篇历史副本仍在各自目录，新篇请建 quality_check.json")

SLOTS = cfg.get("slots", [])
EXEMPT = set(cfg.get("exempt", []))
NUMBERS = cfg.get("numbers", [])
TERMS = cfg.get("terms", [])
EXTRA_TERMS = cfg.get("extra_terms", [])
TITLE_CHECKS = cfg.get("title_checks", [])
BODY_CHECKS = cfg.get("body_checks", [])
LINKS = cfg.get("links", [])
BANNED_EXTRA = cfg.get("banned", [])
BODY_MIN = cfg.get("body_min", 1700)
BODY_MAX = cfg.get("body_max", 2300)
ALL_MAX = cfg.get("all_max", 2500)
MIN_IMAGES = cfg.get("min_images", 5)

fails = []


def cjk(s):
    return len(re.findall(r"[\u4e00-\u9fff]", s))


def flat(s):
    return re.sub(r"\s+", "", s)


# 尾部边界：热门文章 / 合集导航 / 参考资料 / 话题标签行之后不算正文
TAIL_RE = re.compile(r"\n(?=(?:🔥\s*\*\*热门文章|📖|\*\*参考资料|#[^\s#]))")
TAIL_MARK = TAIL_RE.search(BODY)
MAIN = BODY[:TAIL_MARK.start()] if TAIL_MARK else BODY

FLAT = flat(BODY)
SLOT_FLAT = [flat(s) for s in SLOTS]


def slot_score(slot, text):
    """归一化后覆盖率：容忍后台润色的小幅增删与标点替换。"""
    s, t = flat(slot), flat(text)
    if not s:
        return 0.0
    if s in t:
        return 1.0
    sm = difflib.SequenceMatcher(a=s, b=t, autojunk=False)
    return sum(b.size for b in sm.get_matching_blocks()) / len(s)


def is_voice(par: str) -> bool:
    f = flat(par)
    if not f:
        return False
    return any(f in s or s in f or slot_score(s, f) >= 0.85 for s in SLOTS)


def visible(par):
    """微信端可见文字：先删整张图片（含 alt），再把链接还原成链接文字。"""
    s = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", par)
    return re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", s)


def chk(cond, msg, gate=None):
    if gate and gate in EXEMPT:
        print(("  ✓ " if cond else "  ⚠ ") + msg + "（作者豁免，不计 FAIL）")
        return
    print(("  ✓ " if cond else "  ✗ ") + msg)
    if not cond:
        fails.append(msg)


def skip_in_published():
    if PUBLISHED:
        print("  · --published：跳过成稿期门禁")
        return True
    return False


print(f"[14] 原声逐字在场（{len(SLOTS)} 句，≥5 达标）")
if not SLOTS:
    print("  · 无 slots 配置，跳过")
elif not skip_in_published():
    for i, s in enumerate(SLOTS, 1):
        chk(slot_score(s, BODY) >= 0.9, f"原声 {i}（相似度 {slot_score(s, BODY):.0%}）")
    # 作者硬约束：原声不得进引用块（> blockquote），直接做正文段落
    quote_lines = [l for l in BODY.splitlines() if l.lstrip().startswith(">")]
    for i, s in enumerate(SLOTS, 1):
        chk(not any(flat(s) and flat(s) in flat(l) for l in quote_lines),
            f"原声 {i} 未进引用块（作者禁项）")

print("[17] 开头禁标题开场（2026-11-01 口径）")
if skip_in_published():
    pass
else:
    first = next(l.strip() for l in BODY.split("\n") if l.strip())
    title_line = TEXT.split("\n")[1]
    chk(not first.startswith("#"), "正文首段不是标题")
    chk(first[:12] not in title_line, "正文首段没有抄标题")

print("[17] 段落 ≤80 字（原声段落按门禁豁免：逐字不改写）")
paras = []
for p in BODY.split("\n"):
    p = p.strip()
    if not p or p[0] in "#|" or p.startswith("🔥") or p.startswith("**"):
        continue
    if re.match(r"^(\d+\.|[-*])\s", p) or p.startswith("!["):
        continue
    paras.append(p)
over = [(cjk(p), p) for p in paras if cjk(p) > 80]
voice_over = [(n, p) for n, p in over if is_voice(p)]
ai_over = [(n, p) for n, p in over if not is_voice(p)]
if not skip_in_published():
    if ai_over:
        chk(False, f"非原声超 80 字段落 {len(ai_over)} 处", gate="段落超长")
        for n, p in ai_over[:5]:
            print("   ·", n, p[:60])
    else:
        chk(True, f"非原声段落均在 80 字内（段落 {len(paras)} 个）")
    print(f"   · 原声豁免 {len(voice_over)} 处：{[n for n, _ in voice_over]}")

print("[17] 标题层级与分节篇幅（超 400 字的节必补 ###）")
h2 = re.findall(r"^## (.+)$", BODY, re.M)
h3_total = len(re.findall(r"^### ", BODY, re.M))
chk(len(h2) >= 5, f"H2={len(h2)} 节（≥5）")
chk(h3_total >= 2, f"H3={h3_total} 个小标题（≥2）")
secs = re.split(r"^## .+$", BODY, flags=re.M)[1:]
bad = []
for name, body in zip(h2, secs):
    n = cjk(re.sub(r"!\[[^\]]*\]\([^)]*\)", "", body))
    if n > 400 and "### " not in body:
        bad.append((name, n))
chk(not bad, f"超 400 字的节都已补 H3（未补：{bad}）")

print("[11] 禁词 / 工作流元词（链接标题豁免）")
BODY_NOLINK = re.sub(r"\[([^\]]*)\]\([^)]*\)", "", BODY)
for w in ["上一篇", "在上一篇", "篇N", "待发布", "待补", "钩子", "伏笔", "拆给你看"] + BANNED_EXTRA:
    chk(w not in BODY_NOLINK, f"无「{w}」")

print("[15] AI 腔扫描")
for w in ["值得注意的是", "让我们来", "总而言之", "综上所述", "不难发现", "不难看出",
          "需要指出的是", "深入探讨", "全面分析", "由上可知", "表现优异", "具有显著优势",
          "综合来看", "随着AI的发展", "随着 AI 的发展"]:
    chk(w not in BODY, f"无「{w}」")

print("[10] 超 60 字长句（原声段落 / 参考资料豁免）")
seg = re.sub(r"\$[^$]*\$", "", BODY)
seg = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", seg)
seg = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", seg)
seg = re.sub(r"(?s)\*\*参考资料与数字溯源\*\*.*", "", seg)
seg = "\n".join(p for p in seg.split("\n") if not is_voice(p))
long_hits = [s.strip() for s in re.split(r"[。！？\n]", seg) if len(s.strip()) > 60]
if not skip_in_published():
    if long_hits:
        chk(False, f"非原声超 60 字长句 {len(long_hits)} 处", gate="长句")
        for s in long_hits[:5]:
            print("   ·", s[:90])
    else:
        chk(True, "非原声无超 60 字长句")

print("[8] 配图")
chk("images/" not in BODY, "无 images/ 前缀")
refs = set(re.findall(r"\]\(([^)]+\.png)\)", BODY))
missing = sorted(r for r in refs if not (DIR / r).exists())
chk(not missing, f"引用的图都存在（缺 {missing}）")
files = {p.name for p in DIR.glob("*.png") if not p.name.startswith("00-cover-raw")}
orphan = sorted(files - refs - {"00-cover.png", "00-cover-base.png"})
chk(not orphan, f"无孤儿图（孤儿 {orphan}）")
chk(len(refs) >= MIN_IMAGES, f"正文配图 ≥{MIN_IMAGES} 张（当前 {len(refs)}）")
chk((DIR / "00-cover-base.png").exists() or (DIR / "00-cover-raw.png").exists(),
    "存在无字底图（脚本叠字流水线证据）")

print("[5/16] 结尾设计")
chk("点赞" in BODY and "收藏" in BODY, "点赞/收藏引导")
chk("📖" not in BODY, "无合集导航块（2026-11-07 口径）")
chk("下一篇" not in BODY, "无下一篇预告")
tags = re.findall(r"#\S+", BODY.strip().split("\n")[-1])
chk(3 <= len(tags) <= 5, f"话题标签 3-5 个（当前 {len(tags)}）")
chk("#数解AI" in BODY, "含 #数解AI")

print("[13] 爆款要素")
if TITLE_CHECKS and not PUBLISHED:
    for t in TITLE_CHECKS:
        chk(t["text"] in TEXT.split("\n")[1], t.get("label", f"标题含「{t['text']}」"))
for b in BODY_CHECKS:
    if not PUBLISHED:
        chk(b["text"] in BODY, b.get("label", f"正文含「{b['text']}」"))

print("[1] 承重数字对回论文")
if cfg.get("arxiv"):
    print(f"  · 口径来源：{cfg['arxiv']}")
for n in NUMBERS:
    chk(n in BODY, f"数字在场 {n}")
for t in EXTRA_TERMS:
    chk(t in BODY, f"口径在场 {t}")

print("[18] 术语与分工")
for t in TERMS:
    chk(t in BODY, f"术语在场「{t}」")
for l in LINKS:
    chk(l["id"] in BODY, l.get("label", f"内链 {l['id']}"))

print("[19] 篇幅")
n_body = cjk(BODY.split("🔥 **热门文章**")[0])
n_all = cjk(BODY)
if not skip_in_published():
    chk(BODY_MIN <= n_body <= BODY_MAX, f"正文 {n_body} 字（口径 {BODY_MIN}–{BODY_MAX}）", gate="篇幅")
    chk(n_all <= ALL_MAX, f"全文 {n_all} 字（口径 ≤{ALL_MAX}）", gate="篇幅")

# 内链必须微信 URL
links = re.findall(r"\]\((https?://[^)]+)\)", BODY)
chk(all("mp.weixin.qq.com" in l for l in links), f"非微信外链：{links}")

print("[封面] 脚本叠字流水线")
cover = DIR / "00-cover.png"
chk(cover.exists(), "封面 00-cover.png 在场")
if cover.exists():
    r = subprocess.run([sys.executable, str(HERE / "check_cover.py"), str(cover)],
                       capture_output=True, text=True)
    print(r.stdout.strip())
    chk(r.returncode == 0, "check_cover.py 通过（21:9 比例 / 文字块高 / 每行字高）")
meta_p = DIR / "cover_meta.json"
chk(meta_p.exists(), "cover_meta.json 在场（脚本叠字流水线证据）")
if meta_p.exists():
    meta = json.loads(meta_p.read_text(encoding="utf-8"))
    chk(meta.get("total_chars", 99) <= 12,
        f"封面文字超 12 字（信息流缩略不可读）：{meta.get('total_chars')} 字 {meta.get('lines')}")
    chk(meta.get("block_ratio", 1) <= 0.25, f"封面文字块高超 25%：{meta.get('block_ratio')}")

print()
print(f"原声 {sum(1 for s in SLOTS if slot_score(s, BODY) >= 0.9)}/{len(SLOTS)} | "
      f"图 {len(refs)} 张 | 内链 {len(links)} 条")
print("PASS" if not fails else f"FAIL: {len(fails)} 项未过")
for f in fails:
    print("  ✗", f)
sys.exit(0 if not fails else 1)
