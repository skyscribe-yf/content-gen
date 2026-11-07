#!/usr/bin/env python3
"""本篇质量核查（机器可查部分）：原声逐字 / 段落 ≤80 / 禁词 / AI 腔 / 长句 /
配图 / 结尾设计 / 承重数字对回论文 / 与 11-04 篇分工。"""
import re
from pathlib import Path

HERE = Path(__file__).parent
TEXT = (HERE / "weixin.md").read_text()
BODY = TEXT.split("---", 2)[-1]


def cjk(s):
    return len(re.findall(r"[\u4e00-\u9fff]", s))


# 作者原声 5 处逐字（来源 outline.md ## 作者原声槽；槽 5 在「。」处拆成两段，未增删字）
SLOTS = [
    "很多次我发现让一个agent自己review自己写的文字里面的一致性，它煞有其事地跑了很多轮检查后告诉我一切都很干净，等我仔细一读，发现很多地方都不是那么回事儿。",
    "为什么要这样？我理解并不能靠一个简单的数据清洗技巧就给糊弄过去了，最核心的问题在于数据本身是否足够好地能契合整体后训练的奖励目标。",
    "乍一看这个结果似乎有些意外，给了标准答案还不能救回来吗？背后深层次的原因一定是值得琢磨的。",
    "很多时候，一致并不一定就意味着是正确的。众口铄金这个成语早已经告诉我们了事情的背后没有那么简单，而后训练的目标是为了得到正确的结论，并不是仅寻求一致性。",
    "其实对于深度学习整体的历程来看，很多先驱们的工作都是在努力更好地平衡准确率和多样性，从而让模型的表现能保持足够好的综合表现而不是深度拟合了不具有代表性的训练数据/样本。",
    "从这个角度看，大模型后训练机制上的探索，其实还是很好地继承了深度学习的基本底层逻辑。",
]

fails = []
FLAT = re.sub(r"\s+", "", BODY)
SLOT_FLAT = [re.sub(r"\s+", "", s) for s in SLOTS]


def is_voice(par: str) -> bool:
    f = re.sub(r"\s+", "", par)
    return bool(f) and any(f in s for s in SLOT_FLAT)


def chk(cond, msg):
    print(("  ✓ " if cond else "  ✗ ") + msg)
    if not cond:
        fails.append(msg)


print("[14] 原声逐字在场（6 句 / 5 处，≥5 达标）")
for i, s in enumerate(SLOTS, 1):
    chk(re.sub(r"\s+", "", s) in FLAT, f"原声 {i}")

print("[17] 开头禁标题开场（2026-11-01 口径）")
first = next(l.strip() for l in BODY.split("\n") if l.strip())
title_line = TEXT.split("\n")[1]
chk(not first.startswith("#"), "正文首段不是标题")
chk(first[:12] not in title_line, "正文首段没有抄标题")

# 作者 2026-11-07 拍板豁免（改稿产生，不压回、不计 FAIL）：
#   ① 段落 >80 字 1 处（「熊样子」那段，拆了会弱掉情绪）；
#   ② 非原声长句 2 处（作者改写的两处引言）；
#   ③ 篇幅：正文 ≤2300 / 全文 ≤2500（本稿 2309 / 2624）。
# 以上三项复检时只提示，不计入 FAIL，后果由作者承担。
EXEMPT = {"段落超长", "长句", "篇幅"}

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
if ai_over:
    print(f"  ⚠ 非原声超 80 字段落 {len(ai_over)} 处（作者豁免，不计 FAIL）")
    for n, p in ai_over[:5]:
        print("   ·", n, p[:60])
else:
    print(f"  ✓ 非原声段落均在 80 字内（段落 {len(paras)} 个）")
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
for w in ["上一篇", "在上一篇", "篇N", "待发布", "待补", "钩子", "伏笔", "拆给你看"]:
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
if long_hits:
    print(f"  ⚠ 非原声超 60 字长句 {len(long_hits)} 处（作者豁免，不计 FAIL）")
    for s in long_hits[:5]:
        print("   ·", s[:90])
else:
    print("  ✓ 非原声无超 60 字长句")

print("[8] 配图")
chk("images/" not in BODY, "无 images/ 前缀")
refs = set(re.findall(r"\]\(([^)]+\.png)\)", BODY))
missing = sorted(r for r in refs if not (HERE / r).exists())
chk(not missing, f"引用的图都存在（缺 {missing}）")
files = {p.name for p in HERE.glob("*.png") if not p.name.startswith("00-cover-raw")}
orphan = sorted(files - refs - {"00-cover.png", "00-cover-base.png"})
chk(not orphan, f"无孤儿图（孤儿 {orphan}）")
chk(len(refs) >= 5, f"正文配图 ≥5 张（当前 {len(refs)}）")
chk((HERE / "00-cover-base.png").exists() or (HERE / "00-cover-raw.png").exists(),
    "存在无字底图（脚本叠字流水线证据）")

print("[5/16] 结尾设计")
print("  ⚠ 文末互动问：作者 2026-11-07 拍板不补（不计 FAIL）")
chk("点赞" in BODY and "收藏" in BODY, "点赞/收藏引导")
chk("📖" not in BODY, "无合集导航块（2026-11-07 口径）")
chk("下一篇" not in BODY, "无下一篇预告")
tags = re.findall(r"#\S+", BODY.strip().split("\n")[-1])
chk(3 <= len(tags) <= 5, f"话题标签 3-5 个（当前 {len(tags)}）")
chk("#数解AI" in BODY, "含 #数解AI")

print("[13] 爆款要素")
chk("？" in TEXT.split("\n")[1], "标题疑问句")
chk("标准答案" in TEXT.split("\n")[1], "标题关键词前置（标准答案）")
chk("两遍" in BODY, "可操作判据（跑两遍）在正文")

print("[1] 承重数字对回论文（arXiv:2605.22217v1）")
for n in ["0.71", "0.67", "0.002", "0.006", "0.007", "0.16", "0.44", "0.674",
          "0.668", "0.651", "0.004", "0.329", "0.313", "0.305", "0.316",
          "0.619", "0.420", "0.481", "0.686", "150", "450", "500", "16", "0.7%"]:
    chk(n in BODY, f"数字在场 {n}")
chk("Qwen3-4B-Base" in BODY, "基座口径在场")
chk("8 张 A100" in BODY, "算力口径在场")
chk("2026" in BODY, "年份口径在场")

print("[18] 术语与分工")
for t in ["数据门控", "奖励接地", "Grounded Proposer Paradox", "自洽"]:
    chk(t in BODY, f"术语在场「{t}」")
chk("_7aP6jaNXZU0NSQ1UcfMWA" in BODY, "内链 11-04 补测试篇（分工声明）")
chk("ZiQlEtB-vL5nzJo7ye4RvA" in BODY, "内链 篇1 自出题篇")

print("[19] 篇幅")
n_body = cjk(BODY.split("🔥 **热门文章**")[0])
n_all = cjk(BODY)
if not (1700 <= n_body <= 2300):
    print(f"  ⚠ 正文 {n_body} 字（口径 1700–2300；作者豁免，不计 FAIL）")
else:
    print(f"  ✓ 正文 {n_body} 字（1700–2300）")
if n_all > 2500:
    print(f"  ⚠ 全文 {n_all} 字（口径 ≤2500；作者豁免，不计 FAIL）")
else:
    print(f"  ✓ 全文 {n_all} 字（≤2500）")

print()
print("PASS" if not fails else f"FAIL: {len(fails)} 项未过")
for f in fails:
    print("  ✗", f)
