#!/usr/bin/env python3
"""本篇质量核查中机器可查部分：原声逐字在场 / 段落 ≤80 字 / 三级标题 / 禁词 / AI 腔 / 长句 / 配图 / 数字口径。

口径来源：docs/article-quality-check.md（17 项）、docs/writing-flow.md（原声槽）、
         docs/pre-publish-final-check.md（9 项）、AGENTS.md「段落 ≤80 字」硬规。
原声 7 处来自 outline.md ## 作者原声槽（槽 1/2/4/5/6/7 作者手打，槽 3 作者确认沿用笔记 §7.1）。
标点归一：原声可在自带句读处加句号/分段（门禁允许，不增删字）。
"""
import re
from pathlib import Path

HERE = Path(__file__).parent
TEXT = (HERE / "weixin.md").read_text()
BODY = TEXT.split("---", 2)[-1]


def cjk(s):
    return len(re.findall(r"[\u4e00-\u9fff]", s))


SLOTS = [
    # 槽 1 · 开头钩子之后（作者手打，亲历）
    "其实我一开始并不明白人们为什么要搞出来看起来超级复杂的矩阵微分，后来学习大规模的反向传播实现遇到自动微分，才明白它原来有这么大的用处。",
    # 槽 2 · §1 数值微分段尾（作者手打，吐槽）
    "数值微分可以用来近似求解，但是因为计算机浮点数表示上的天然不足，很多时候会出现离谱的误差，所以如果有办法得到精确的解，没有人愿意用数值解。",
    # 槽 3 · §3 段尾（沿用笔记 §7.1）
    "第一版 `jac` 写的是 `J[:, j] = pulled_back_vector`。它在 softmax 检查里通过了——因为 $\\operatorname{diag}(p)-pp^\\top$ 是对称矩阵，行列搞反看不出来。是 `y = Ax` 的检查抓住的（相对误差 1.7e+00）。",
    # 槽 3 第二段
    "教训：用形状检查求导实现，一定要挑非对称的函数。对称的测试用例是「能过但没有信息量」的测试。",
    # 槽 4 · §4 读表之后（作者手打，判断）
    "事实上，很多时候由于一些特殊的无法精确求得解析解情况的存在，完全零误差是不太能做到的，反而一个稳定的可预期误差会显得更有意义。",
    # 槽 5 · §5 用重算换内存段尾（作者手打，判断；原句在自带句读处分成三段）
    "其实在计算机科学领域，一切都不是白得的，凡事都总有代价，仔细思考一下就会明白，这里的内存换计算时间全是因为计算的代价太过昂贵，所以才需要把大量需要重新计算的数据保存在显卡内存里面重复利用。因此你应该容易理解为什么训练需要那么多的显存了。",
    # 槽 6 · §6 回扣开头（作者手打，判断）
    "其实自动微分并没有改变任何数学上的严格性，和链式法则的运作方式，它只是通过一个简单的形式上的变化，就实现了化腐朽为神奇的快速反向传播。",
    # 槽 7 · 文末互动问（作者手打）
    "你是否被自动微分形式上的晦涩实现所困扰过或者仔细思考过它的本质？",
]


def norm(s):
    s = re.sub(r"\\operatorname\{([a-z]+)\}", r"\1", s)
    s = s.replace("^\\top", "^T").replace("\\top", "T")
    s = re.sub(r"[$\s]", "", s)
    s = re.sub(r"\*\*|`", "", s)
    return s.translate(str.maketrans("，。；、：", "，，，，："))


fails = []
FLAT = norm(BODY)


def chk(cond, msg):
    print(("  ✓ " if cond else "  ✗ ") + msg)
    if not cond:
        fails.append(msg)


print("[14] 原声逐字在场（7 处，下限 5）")
for i, s in enumerate(SLOTS, 1):
    chk(norm(s) in FLAT, f"原声槽 {i}")

print("[17] 段落 ≤80 字（表格/链接/图片/标题/列表除外）")
paras = []
for p in BODY.split("\n"):
    p = p.strip()
    if not p or p[0] in "#|" or p.startswith(("📖", "🔥", "[", "![")):
        continue
    if re.match(r"^(\d+\.|[-*])\s", p):
        continue
    paras.append(p)
over = [(cjk(p), p) for p in paras if cjk(p) > 80]
chk(not over, f"无超 80 字段落（段落 {len(paras)} 个，超标 {len(over)}）")
for n, p in over[:5]:
    print("   ·", n, p[:60])

print("[17] 标题层级：H2 节 + H3 小标题")
h2 = len(re.findall(r"^## ", BODY, re.M))
h3 = len(re.findall(r"^### ", BODY, re.M))
chk(h2 >= 5, f"H2 = {h2} 节（≥5）")
chk(h3 >= 6, f"H3 = {h3} 个小标题（≥6）")

print("[11] 正文禁词 / 工作流元词（链接标题豁免）")
BODY_NOLINK = re.sub(r"\[([^\]]*)\]\([^)]*\)", "", BODY)
for w in ["钩子", "伏笔", "说人话就是", "上一篇", "在上一篇", "篇N", "拆给你看", "待发布", "待补", "TODO"]:
    chk(w not in BODY_NOLINK, f"无「{w}」")

print("[15] AI 腔扫描")
for w in ["值得注意的是", "让我们来", "总而言之", "综上所述", "不难发现", "不难看出",
          "需要指出的是", "深入探讨", "全面分析", "由上可知", "今天我们来聊聊",
          "随着AI的发展", "随着 AI 的发展", "表现优异", "具有显著优势", "综合来看",
          "本质上来说", "首先，", "其次，", "最后，"]:
    chk(w not in BODY, f"无「{w}」")

print("[15] 作者口头禅（信息项，不判失败）")
print("   在场口头禅：", [w for w in ["其实", "不过", "当然", "本质上", "然而", "事实上"] if w in BODY])

print("[10] 超 60 字长句（原声段落/参考资料/表格/📖与热门链接行豁免）")
VOICE = [norm(s) for s in SLOTS]
seg = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", BODY)
seg = re.sub(r"\[[^\]]*\]\([^)]*\)", "", seg)
seg = re.sub(r"(?s)\*\*参考资料与数字溯源\*\*.*", "", seg)
seg = re.sub(r"(?s)🔥 \*\*热门文章\*\*.*", "", seg)


def is_voice(par):
    f = norm(par)
    return bool(f) and any(f in v for v in VOICE)


long_hits = []
for p in seg.split("\n"):
    p = p.strip()
    if not p or p[0] in "#|" or is_voice(p) or p.startswith(("📖", "🔥", "[")):
        continue
    for s in re.split(r"[。！？]", p):
        if len(s.strip()) > 60:
            long_hits.append(s.strip())
chk(not long_hits, f"无超 60 字 AI 句（命中 {len(long_hits)}）")
for s in long_hits:
    print("   ·", s[:90])

print("[8] 图片路径与配图数量")
chk("images/" not in BODY, "无 images/ 前缀")
refs = set(re.findall(r"\]\(([^)]+\.png)\)", BODY))
missing = sorted(r for r in refs if not (HERE / r).exists())
files = {p.name for p in HERE.glob("*.png") if not p.name.startswith("00-cover")}
chk(not (files - refs), f"无孤儿图（正文 {len(refs)} 张，目录 {len(files)} 张）")
chk(len(refs) >= 6, f"正文配图不少于 6 张（当前 {len(refs)}）")
chk(not missing, f"正文引用的图全部存在（缺 {missing}）")

print("[5/16] 结尾互动与转发设计")
chk("困扰过或者仔细思考过它的本质" in BODY, "文末开放式问题（原声互动问）")
chk("点个赞" in BODY and "收藏" in BODY, "点赞/收藏引导")
chk("关注「数解AI」" in BODY, "关注引导")
tags = re.findall(r"#\S+", BODY.split("参考资料")[-1])
chk(3 <= len(tags) <= 5, f"话题标签 3-5 个（当前 {len(tags)}：{tags}）")
chk("#数解AI" in BODY, "含 #数解AI")

print("[9] 尾部链接与热门块")
chk("🔥 **热门文章**：" in BODY, "热门块存在")
chk(BODY.count("🔥 **热门文章**：") == 1, "热门块标题只出现一次")
hot = [l for l in BODY.split("\n") if re.match(r"^\[.+\]\(https://mp\.weixin\.qq\.com/s/", l)]
chk(all(l.endswith("  ") for l in hot), f"链接行行尾两空格（{len(hot)} 行）")
chk("（待发布）" not in BODY, "无「（待发布）」残留")

print("[1] 关键数字与文内口径一致")
for n in ["5520 亿", "552B", "3765.5 ms", "2.0 ms", "近两千倍", "1.2e-03", "2.3e-09",
          "6.3e-10", "1.3e-09", "1.7e+00", "4096", "3 倍"]:
    chk(n in BODY, f"数字在场 {n}")
chk("2026" in BODY, "年份口径在场")
chk("V4.1-Flash" in BODY, "主锚模型 V4.1-Flash 在正文在场（不只参考资料）")
chk("Kimi K3" in BODY.split("**参考资料")[0], "Kimi K3 量级对照在正文在场")
chk("我自己就写错过" not in BODY, "无 AI 代拟的第一人称句")

print("[13] 爆款要素抽查")
title = TEXT.split("\n")[1].split('"')[1]
chk("几千亿" in title and "几千倍" in title, "标题含数字反差")
chk(not title.endswith("？"), "标题为陈述句（后台发布标题为准，见 draft-status.yaml 2026-10-15 修正）")
chk("5520 亿个导数" in BODY.split("## ")[0], "开头钩子亮明量级")
chk("5520 亿个导数不是一个个算出来的" in BODY, "首尾闭环（回扣开头）")
chk("判断标准只有一条" in BODY, "给出一条可带走的判断")

print()
print("PASS" if not fails else f"FAIL: {len(fails)} 项未过")
for f in fails:
    print("  ✗", f)
