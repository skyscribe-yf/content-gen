#!/usr/bin/env python3
"""本篇（MiniMax MSA）质量核查机器可查部分 + 作者口径（段落 ≤80 字 / AI 句 ≤60 字 / 原声禁入引用块）。
适配自 content/2026-10-28-compaction-constraint-survival/quality_check.py（原声/数字/门禁按本篇重列）。"""
import re
import sys
import difflib
from pathlib import Path

HERE = Path(__file__).parent
TEXT = (HERE / "weixin.md").read_text()
BODY = TEXT.split("---", 2)[-1]

# --published：已发布文章以后台正文为准，跳过成稿期门禁（原声/段落/长句/篇幅）。
PUBLISHED = "--published" in sys.argv


def cjk(s):
    return len(re.findall(r"[\u4e00-\u9fff]", s))


def flat(s):
    return re.sub(r"\s+", "", s)


# 尾部边界：热门文章 / 合集导航 / 参考资料 / 话题标签行之后不算正文
TAIL_RE = re.compile(r"\n(?=(?:🔥\s*\*\*热门文章|📖|\*\*参考资料|#[^\s#]))")
TAIL_MARK = TAIL_RE.search(BODY)
MAIN = BODY[:TAIL_MARK.start()] if TAIL_MARK else BODY


def slot_score(slot, text):
    """归一化后覆盖率：容忍 web 改写的小幅增删与标点替换。"""
    s, t = flat(slot), flat(text)
    if not s:
        return 0.0
    if s in t:
        return 1.0
    sm = difflib.SequenceMatcher(a=s, b=t, autojunk=False)
    return sum(b.size for b in sm.get_matching_blocks()) / len(s)


def is_tail_block(par):
    s = par.strip()
    return (not s) or s.startswith(("#", "!", "[", "🔥", "📖", "|")) or bool(re.match(r"^\d+\.\s", s))


def visible(par):
    """微信端可见文字：先删整张图片（含 alt），再把链接还原成链接文字。"""
    s = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", par)
    return re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", s)


def n_sent(par):
    return len([x for x in re.split(r"[。！？；!?;]", visible(par)) if cjk(x) >= 4])


# 原声 8 处（2026-10-29 作者逐条手动输入；槽 4 经作者口头授权「你看着优化一下」补一处漏字）
SLOTS = [
    "全量注意力还是稀疏注意力，在过去一段时间一直是一个争议的焦点。最初我看到 MiniMax 并不看好稀疏注意力、而想押注全量注意力的时候，其实对它技术方向充满了期待，希望它能走出一条不同于 DeepSeek 的路来。",
    "还是很希望这家当时位列前几的大模型厂商给出一条不同的解法，毕竟某国外前沿模型据说一直押注于全注意力机制。我猜测他们内部一定是经历了什么路线或者方向上的摇摆。",
    "按块级选择，相当于说我做了一系列事情之后，才会反思是不是要换一个走法。而按 token 级选择，那就更谨慎，也更灵活了，每走一步都得考虑考虑。",
    "其实这种想法在工程上屡见不鲜了。对于一些关键的模块，如果从一个随机数开始训练，它可能就四处乱撞，根本没有办法优化到一个好的状态。这个时候更需要的是一个类似于 warm up 的过程。",
    "这三个条件，精确的 softmax 之前文章已经讲了不少，反而是 kernel 协同容易被忽略。",
    "有时候理论上的数字，转化到实际工程落地，就是会有很大的损耗。这个损耗比其实也算非常优秀了，很多时候想有一倍提升都是超级困难的。这也是为什么架构优化和演进这么有趣的原因，以小博大的效果往往需要靠模型架构上的大大小小的创新。",
    "这无疑是一个非常冒险的决定，毕竟其他几家如 kimi 和 QWen 系列，都还遵循着相对保守一点的混合架构设定。具体效果如何，还是要看实际场景大量用户的校验了。",
    "你觉得几家大厂的稀疏注意力探索努力，MiniMax 在略微落后的情况下，还有机会完成逆袭吗？",
]

fails = []

FLAT = re.sub(r"\s+", "", BODY)
SLOT_FLAT = [re.sub(r"\s+", "", s) for s in SLOTS]


def is_voice(par: str) -> bool:
    p = flat(par)
    if not p:
        return False
    return any(p in flat(s) or flat(s) in p or slot_score(s, p) >= 0.85 for s in SLOTS)


def chk(cond, msg):
    if not cond:
        fails.append(msg)


if PUBLISHED:
    print("· --published：跳过原声 / 段落 / 长句门禁")
else:
    for i, s in enumerate(SLOTS, 1):
        chk(slot_score(s, flat(BODY)) >= 0.9, f"原声槽 {i}（相似度 {slot_score(s, flat(BODY)):.0%}）")
    chk(sum(1 for s in SLOTS if slot_score(s, flat(BODY)) >= 0.9) >= 5, "原声进稿不足 5 处")

# 作者硬约束：原声不得进引用块（> blockquote），直接做正文段落
quote_lines = [l for l in BODY.splitlines() if l.lstrip().startswith(">")]
for i, s in enumerate(SLOTS, 1):
    chk(not any(flat(s) and flat(s) in flat(l) for l in quote_lines),
        f"原声槽 {i} 出现在引用块（作者禁项）")

# 段落长度：≤80 字；或 ≤3 句且 ≤88 字（尾部/原声豁免）
paras = [p for p in re.split(r"\n\s*\n", MAIN) if p.strip() and not is_tail_block(p)]
over = []
for i, p in enumerate(paras):
    if is_voice(p):
        continue
    vis = visible(p)
    n, ns = cjk(vis), n_sent(p)
    if n > 88 and ns > 3:
        over.append((i + 1, n, ns))
if not PUBLISHED:
    chk(not over, f"超长段落（>88 字且 >3 句）：{over}")

# AI 句 ≤60 字（+10% 容差 = 66 字；原声/尾部豁免）
sent_over = []
for p in paras:
    if is_voice(p):
        continue
    for s in re.split(r"[。！？；]", visible(p)):
        n = cjk(s)
        if n > 66:
            sent_over.append((n, s.strip()[:30]))
if not PUBLISHED:
    chk(not sent_over, f"超 60 字 AI 句：{sent_over}")

# 禁词 / AI 腔
BANNED = ["值得注意的是", "让我们来", "总而言之", "综上所述", "不难发现", "不难看出", "需要指出的是",
          "深入探讨", "全面分析", "起着至关重要的作用", "由上可知", "随着 AI 的发展", "今天我们来聊聊",
          "说人话就是", "伏笔"]
hits = [w for w in BANNED if w in BODY]
chk(not hits, f"禁词命中：{hits}")

# 待发布残留
chk("（待发布）" not in BODY, "残留（待发布）")

# 话题标签
tags = re.findall(r"#\S+", BODY.splitlines()[-1] if BODY.strip() else "")
chk(3 <= len(tags) <= 5 and any("数解AI" in t for t in tags), f"话题标签异常：{tags}")

# 图片同级路径（无 images/ 前缀）
imgs = re.findall(r"!\[[^\]]*\]\(([^)]+)\)", BODY)
chk(all(not i.startswith("images/") for i in imgs), "图片带 images/ 前缀")
chk(len(imgs) >= 4, f"正文图不足 4 张：{len(imgs)}")
for i in imgs:
    chk((HERE / i).exists(), f"图片文件缺失：{i}")

# 正文内链必须微信 URL（参考资料里的 arXiv / HF 不算内链）
links = re.findall(r"\]\((https?://[^)]+)\)", MAIN)
chk(all("mp.weixin.qq.com" in l for l in links), f"非微信外链：{[l for l in links if 'mp.weixin.qq.com' not in l]}")
chk(len(links) >= 7, f"正文内链不足 7 条：{len(links)}")

# 承重数字在场（论文 / 官方博客口径）
for d in ["2048", "128", "16", "28.4", "14.2", "7.6", "456B", "45.9B", "229.9B", "9.8B",
          "428B", "23B", "192K", "2.6T", "400B", "40B", "109B", "3T",
          "−0.60", "−2.10", "+0.12", "−1.35", "1/20"]:
    chk(d in BODY, f"承重数字缺失：{d}")

# 禁现（口径纪律）
for w in ["四个月", "洗漱", "13.3%", "Space Bunny", "从第一天", "DeepSWE"]:
    chk(w not in BODY, f"禁现内容泄漏：{w}")

# 封面核验
import json as _json
import subprocess as _sp
cover = HERE / "00-cover.png"
chk(cover.exists(), "封面缺失：00-cover.png")
if cover.exists():
    r = _sp.run([sys.executable, str(HERE / "check_cover.py"), str(cover)],
                capture_output=True, text=True)
    print(r.stdout.strip())
    chk(r.returncode == 0, "check_cover.py 未通过（比例/文字块高超口径）")
meta_p = HERE / "cover_meta.json"
chk(meta_p.exists(), "cover_meta.json 缺失（封面须由 make_cover.py 脚本叠字生成）")
if meta_p.exists():
    meta = _json.loads(meta_p.read_text())
    chk(meta.get("total_chars", 99) <= 12,
        f"封面文字超 12 字（信息流缩略不可读）：{meta.get('total_chars')} 字 {meta.get('lines')}")
    chk(meta.get("block_ratio", 1) <= 0.25, f"封面文字块高超 25%：{meta.get('block_ratio')}")
chk((HERE / "00-cover-base.png").exists(),
    "缺 00-cover-base.png——封面文字必须脚本叠加（make_cover.py），禁止 AI 生图直接写中文")

# 字数（正文口径，去掉 frontmatter 与尾部块）
def sec_cjk(s):
    return cjk(re.sub(r"!\[[^\]]*\]\([^)]+\)", "", s))


n = sec_cjk(MAIN)
print(f"正文 CJK 字数（不含热门/参考资料/标签）：{n}")
if PUBLISHED:
    print("  · --published：跳过成稿期篇幅门禁")
else:
    chk(n <= 2300, f"正文超 2300：{n}")

print(f"原声 {sum(1 for s in SLOTS if slot_score(s, flat(BODY)) >= 0.9)}/{len(SLOTS)} | 图 {len(imgs)} 张 | 内链 {len(links)} 条")
print("PASS" if not fails else f"FAIL: {len(fails)} 项未过")
for f in fails:
    print(" -", f)
