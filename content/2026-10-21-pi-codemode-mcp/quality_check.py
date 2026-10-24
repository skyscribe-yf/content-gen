#!/usr/bin/env python3
"""本篇 16 项质量核查中机器可查部分 + 作者 2026-10-10 新增口径（段落 ≤80 字 / 三级标题）。
适配自 content/2026-10-10-context-rot-isolation/quality_check.py（原声/数字/爆项按本篇重列）。"""
import re
import sys
import difflib
from pathlib import Path

HERE = Path(__file__).parent
TEXT = (HERE / "weixin.md").read_text()
BODY = TEXT.split("---", 2)[-1]

# --published：文章已发布（正文以后台为准）时跳过成稿期门禁（原声/段落/长句/篇幅），
# 只保留发布后仍必须成立的不变量（链接、标签、图片路径、数字、禁词）。
PUBLISHED = "--published" in sys.argv

def cjk(s):
    return len(re.findall(r"[\u4e00-\u9fff]", s))

def flat(s):
    return re.sub(r"\s+", "", s)

# 尾部边界：热门文章 / 合集导航 / 参考资料 / 话题标签行之后都不算正文。
# 不再依赖「📖」单一行（作者可能在后台删掉合集导航行）。
TAIL_RE = re.compile(r"\n(?=(?:🔥\s*\*\*热门文章|📖|\*\*参考资料|#[^\s#]))")
TAIL_MARK = TAIL_RE.search(BODY)
MAIN = BODY[:TAIL_MARK.start()] if TAIL_MARK else BODY

def slot_score(slot, text):
    """原声相似度：归一化后最长匹配覆盖率（容忍 web 改写的小幅增删/标点替换）。"""
    s, t = flat(slot), flat(text)
    if not s:
        return 0.0
    if s in t:
        return 1.0
    sm = difflib.SequenceMatcher(a=s, b=t, autojunk=False)
    return sum(b.size for b in sm.get_matching_blocks()) / len(s)

def slot_ok(slot, min_ratio=0.9):
    return slot_score(slot, flat(BODY)) >= min_ratio

def is_voice(par):
    """段落属于作者原声（原声可跨段拆分/被后台小改）。"""
    p = flat(par)
    if not p:
        return False
    return any(p in flat(s) or flat(s) in p or slot_score(s, p) >= 0.85 for s in SLOTS)

def is_tail_block(par):
    s = par.strip()
    return (not s) or s.startswith(("#", "!", "[", "🔥", "📖")) or bool(re.match(r"^\d+\.\s", s))

def visible(par):
    """微信端可见文字：先删整张图片（含 alt），再把链接还原成链接文字。"""
    s = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", par)
    return re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", s)

def n_sent(par):
    return len([x for x in re.split(r"[。！？；!?;]", visible(par)) if cjk(x) >= 4])

# 原声 7 处逐字（来源 outline.md ## 作者原声槽）
# 槽 1 / 槽 2 / 槽 4 / 槽 5 在自带句读处加句号并分段（仅加标点，未增删任何字，已向作者声明）
SLOTS = [
    "Pi社区反对了这么久的MCP，最后靠这个codemode才悄悄把mcp给请了回来。MCP果真有这么不堪吗？",
    "一年以前，我曾经深受Copilot智障的影响却不明所以。因为同样的Claude Sonnet模型，在其他工具里面用愣是效果比Copilot里面好不少。后来才发现微软给的上下文窗口本身就很小，而Github官方的工具就要一次性占掉大量的上下文，导致干不了多少活，就会触发自动压缩了。偏偏微软还很“贴心”地把压缩行为给隐藏了起来。那时候很多任务干一半就戛然而止的情况是屡见不鲜，让人觉得麻烦不已。没有人觉得agent可以变得非常有用，然而这才是一两年前的事情而已。",
    "当时我就好奇，对MCP的支持究竟会走到一个什么样的地步？他们会把MCP重新加回来吗？",
    "这就好比是一个非常聪明的经理，去指导新来乍到但是有一些工作经验的老手。交代任务的时候只需要给一个略微模糊的要求，和可以使用的资源，老手便能通过自己已有的经验去尝试探索和完成往往就能达到不错的效果。反之，如果这名经理都事无巨细地交代所有步骤，他自己的宝贵的精力会很快耗费殆尽而效果未必就会更好。",
    "那么，pi作者说的所谓的vibed bias，又是什么意思呢。",
    "那么是否可以说，在模型快速迭代的今天，即便是开源agent harness标杆的pi，也是在靠感觉来做优化，是吗？这样真的就靠谱吗？",
    "但是这个问题的核心，就是期望解决日益增长的context需求，和模型有限的context window大小之间的矛盾，以及很麻烦的注意力退化问题，对吗？",
]

fails = []

FLAT = re.sub(r"\s+", "", BODY)
SLOT_FLAT = [re.sub(r"\s+", "", s) for s in SLOTS]


def is_voice(par: str) -> bool:
    """该段落属于作者原声（原声可跨段拆分，故用扁平化包含判定）。"""
    f = re.sub(r"\s+", "", par)
    return bool(f) and any(f in s for s in SLOT_FLAT)


def chk(cond, msg):
    print(("  ✓ " if cond else "  ✗ ") + msg)
    if not cond:
        fails.append(msg)


print("[14] 原声逐字在场（7 处，≥5 达标；归一化相似度 ≥90%，容忍 web 小改）")
if PUBLISHED:
    print("  · --published：跳过成稿期原声校验")
else:
    for i, s in enumerate(SLOTS, 1):
        chk(slot_ok(s), f"原声 {i}（相似度 {slot_score(s, flat(BODY)):.0%}）")

print("[新] 段落长度（≤80 字；或 ≤3 句且 ≤88 字；尾部/原声豁免）")
over = []
paras = [p.strip() for p in re.split(r"\n\s*\n", MAIN) if p.strip()]
for p in paras:
    if is_tail_block(p) or is_voice(p):
        continue
    vis = visible(p)
    n, ns = cjk(vis), n_sent(p)
    if n > 88 and ns > 3:
        over.append((n, ns, p))
if PUBLISHED:
    print("  · --published：跳过成稿期段落校验")
else:
    chk(not over, f"无超长段落（超 88 字且 >3 句：{[(n, ns) for n, ns, _ in over]}）")
    for n, ns, p in over[:5]:
        print("   ·", n, "字 /", ns, "句：", p[:60])

print("[新] 标题层级：H2 节 + H3 小标题")
h2 = len(re.findall(r"^## ", BODY, re.M))
h3 = len(re.findall(r"^### ", BODY, re.M))
chk(h2 >= 5, f"H2={h2} 节、H3={h3} 个小标题")
sections = re.split(r"^## ", BODY, flags=re.M)[1:]
def sec_cjk(s):
    s = re.sub(r"(?s)🔥.*", "", s)
    s = re.sub(r"(?s)\*\*参考资料与数字溯源\*\*.*", "", s)
    s = "\n".join(l for l in s.split("\n") if not l.strip().startswith("📖"))
    return cjk(s)
bad = [s.split("\n")[0][:20] for s in sections if sec_cjk(s) > 400 and "###" not in s]
chk(not bad, f"超 400 字的节都有 ###（缺失：{bad}）")

print("[11] 正文禁词 / 工作流元词（链接标题豁免）")
BODY_NOLINKTXT = re.sub(r"\[([^\]]*)\]\([^)]*\)", "", BODY)
for w in ["钩子", "伏笔", "说人话就是", "上一篇", "在上一篇", "篇N", "拆给你看", "待发布", "待补"]:
    chk(w not in BODY_NOLINKTXT, f"无「{w}」")

print("[15] AI 腔扫描")
ai_words = ["值得注意的是", "让我们来", "总而言之", "综上所述", "不难发现", "不难看出",
            "需要指出的是", "深入探讨", "全面分析", "由上可知", "今天我们来聊聊",
            "随着AI的发展", "随着 AI 的发展", "表现优异", "具有显著优势", "综合来看"]
for w in ai_words:
    chk(w not in BODY, f"无「{w}」")

print("[12] 「拆」字逐处判断（链接标题豁免）")
hits = re.findall(r".{10}拆.{10}", BODY_NOLINKTXT)
if not hits:
    chk(True, "无「拆」字")
for m in hits:
    print("   ·", m.replace("\n", " "))

print("[10] 超 60 字长句（+10% 容差 = 66 字；原声/尾部豁免）")
long_hits = []
for p in re.split(r"\n\s*\n", MAIN):
    if is_voice(p):
        continue
    for s in re.split(r"[。！？\n]", visible(p)):
        s = s.strip()
        if len(s) > 66:
            long_hits.append(s)
if PUBLISHED:
    print("  · --published：跳过成稿期长句校验")
else:
    chk(not long_hits, f"无超 60 字 AI 句（命中 {len(long_hits)}）")
    for s in long_hits:
        print("   ·", s[:90])

print("[8] 图片路径与配图数量（作者口径：正文 ≥4 张）")
chk("images/" not in BODY, "无 images/ 前缀")
refs = set(re.findall(r"\]\(([^)]+\.png)\)", BODY))
missing = sorted(r for r in refs if not (HERE / r).exists())
chk(not missing, f"引用的图都存在（缺 {missing}）")
files = {p.name for p in HERE.glob("*.png") if not p.name.startswith("00-cover")}
chk(not (files - refs), f"无孤儿图（正文 {len(refs)} 张，目录 {len(files)} 张）")
chk(len(refs) >= 4, f"正文配图不少于 4 张（当前 {len(refs)}）")

print("[5/16] 结尾互动与转发设计")
chk("注意力退化问题，对吗" in BODY, "文末互动问（作者原声 Q3 在场）")
chk("点个赞" in BODY and "收藏" in BODY, "点赞/收藏引导")
tags = re.findall(r"#\S+", BODY.strip().split("\n")[-1])
chk(3 <= len(tags) <= 5, f"话题标签 3-5 个（当前 {len(tags)}）")
chk("#数解AI" in BODY, "含 #数解AI")

print("[13] 爆款要素抽查")
title_line = TEXT.split("\n")[1]
chk("MCP" in title_line and "请" in title_line, "标题反常冲突 + MCP 关键词前置（作者口径：不用疑问句）")
chk("MCP果真有这么不堪吗" in BODY[:600], "驱动问题在开头亮明（Q7）")
chk("回到开头那个问题" in BODY, "首尾闭环（开头问题结尾回答）")

print("[1] 关键数字与文内口径一致")
for n in ["128k", "1M", "34k", "80k", "146k", "200k", "73%", "13 个",
          "672", "360", "2000 行", "1 MiB", "66 个"]:
    chk(n in BODY, f"数字在场 {n}")
chk("2026" in BODY, "年份口径在场（2026）")
chk("Context Rot" in BODY, "前文回引 Context Rot 在场")
chk("Pi Durable" in BODY, "前文回引 Pi Durable 在场")

print()
print("PASS" if not fails else f"FAIL: {len(fails)} 项未过")
for f in fails:
    print("  ✗", f)
