#!/usr/bin/env python3
"""本篇质量核查中机器可查部分：原声逐字在场 / 段落 ≤80 字 / 三级标题 / 禁词 / AI 腔 / 长句 / 配图 / 数字口径。

口径来源：docs/article-quality-check.md（17 项）、docs/writing-flow.md（原声槽）、
         docs/pre-publish-final-check.md（9 项）、AGENTS.md「段落 ≤80 字」硬规。
原声 8 处来自 outline.md ## 作者原声槽（8 槽全部走完，2026-10-15）。
入稿时对原声做过的改动只有错别字级一处在 outline.md 记账：
  槽 4：`不应给被滥用` → `不应被滥用`；`最是最好` → `就是最好`
"""
import re
from pathlib import Path

HERE = Path(__file__).parent
TEXT = (HERE / "weixin.md").read_text()
BODY = TEXT.split("---", 2)[-1]


def cjk(s):
    return len(re.findall(r"[\u4e00-\u9fff]", s))


SLOTS = [
    # 槽 1 · 开头数字钩子之后（作者手打，提问 + 判断）
    "这个真的只是通过刻意硬凑，给构造出来的数学玩具吗？",
    "不过从个人的角度来看，LLM 模型发展到今天，其实很多底层逻辑还是有不少缺口需要去补，靠朴素直觉硬玩炼丹术总不是长久之计。",
    "理论解释略微落后于实践是可以的，但是一直跟不上来就不利于长期健康发展。",
    # 槽 2 · §1 落点句之后（作者手打，行业观察 + 提问）
    "看到多家的注意力机制设计，我发现其实大家都还是单纯地按照 token 对应的向量表示之间的内积得分来挑最大这个共性，为什么就没有人尝试用一些不一样的方法来处理呢？难道这真的是唯一正确的路径吗",
    # 槽 3 · §2 公式之后（沿用）
    "这个错位其实来自 value 的方向差异，不是质量本身。",
    # 槽 4 · §3 复刻数字之后（作者手打，亲历 + 类比）
    "看到这个数字，总算有一些不一样的视角能看出来点东西了，原来学习得到的分数高也并不一定就等价于产出就是最好的。就像按照某个单一KPI计算得分最好的项目，未必实际效果就是最好的一样，任何方法都不应被滥用成为唯一标准，这个世界还是很复杂的。",
    # 槽 5 · §4 三条边界之后（作者手打，措辞强度）
    "我倾向于认为，质量排行其实并不是任何时候都是错误的，而仅仅是有些时候显得失真，需要更好的工具来完善它。",
    # 槽 6 · §5 双重极端之后（沿用）
    "增益随上下文长度变大，更可能是质量分布趋向极端（attention sink / 汇聚）导致的污染，而不是方向各向同性化。",
    # 槽 7 · §7 sink 段（沿用）
    "稠密 softmax 里像是变相去除了不太影响矩阵相似性的项——sink 承接了 softmax 必须分配出去的质量，但它的 value 贡献趋零，所以对输出无害。",
    # 槽 8 · 文末互动问（作者手打）
    "你觉得长上下文、稀疏架构的设计，是否会更多考虑本文讨论的方向吗",
]

PLANNED_IMAGES = ["01-66x-98.png", "02-direction-scan.png"]


def norm(s):
    s = re.sub(r"[$\s]", "", s)
    s = re.sub(r"\*\*|`", "", s)
    s = s.translate(str.maketrans("，。；、：", "，，，，："))
    return s


fails = []
FLAT = norm(BODY)


def chk(cond, msg):
    print(("  ✓ " if cond else "  ✗ ") + msg)
    if not cond:
        fails.append(msg)


print("[14] 原声逐字在场（8 槽 / 下限 5）")
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
for n, p in over[:8]:
    print("   ·", n, p[:70])

print("[17] 标题层级：H2 节 + H3 小标题")
h2 = len(re.findall(r"^## ", BODY, re.M))
h3 = len(re.findall(r"^### ", BODY, re.M))
chk(h2 >= 5, f"H2 = {h2} 节（≥5）")
chk(h3 >= 6, f"H3 = {h3} 个小标题（≥6）")

print("[11] 正文禁词 / 工作流元词（链接标题豁免）")
BODY_NOLINK = re.sub(r"\[([^\]]*)\]\([^)]*\)", "", BODY)
for w in ["钩子", "伏笔", "说人话就是", "上一篇", "在上一篇", "篇N", "拆给你看",
          "待发布", "待补", "TODO", "第 N 篇", "（待"]:
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
    return bool(f) and any(f in v or v in f for v in VOICE)


long_hits = []
for p in seg.split("\n"):
    p = p.strip()
    if not p or p[0] in "#|$" or is_voice(p) or p.startswith(("📖", "🔥", "[")):
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
chk(refs == set(PLANNED_IMAGES), f"正文引用与配图规划一致（引用 {len(refs)} 张）")
files = {p.name for p in HERE.glob("*.png") if not p.name.startswith("00-cover")}
chk(not (files - refs), f"无孤儿图（正文 {len(refs)} 张，目录 {len(files)} 张）")
missing = sorted(r for r in refs if not (HERE / r).exists())
chk(not missing, f"配图文件已生成（缺 {missing}）")

print("[5/16] 结尾互动与转发设计")
chk("是否会更多考虑本文讨论的方向" in BODY, "文末开放式问题（原声互动问）")
chk("点个赞" in BODY and "收藏" in BODY, "点赞/收藏引导")
chk("关注「数解AI」" in BODY, "关注引导")
tags = re.findall(r"#\S+", BODY.split("参考资料")[-1])
chk(3 <= len(tags) <= 5, f"话题标签 3-5 个（当前 {len(tags)}：{tags}）")
chk("#数解AI" in BODY, "含 #数解AI")

print("[9] 尾部链接与热门块")
chk("🔥 **热门文章**：" in BODY, "热门块存在")
chk(BODY.count("🔥 **热门文章**：") == 1, "热门块标题只出现一次")
hot = [l for l in BODY.split("\n") if re.match(r"^\[.+\]\(https://mp\.weixin\.qq\.com/s/", l)]
chk(len(hot) >= 6, f"热门块链接 ≥6 行（当前 {len(hot)}）")
chk(all(l.endswith("  ") for l in hot), f"链接行行尾两空格（{len(hot)} 行）")
hot_titles = [re.match(r"^\[(.+?)\]", l).group(1) for l in hot]
chk(len(hot_titles) == len(set(hot_titles)), "热门块标题无重复")

print("[1] 关键数字与文内口径一致")
for n in ["66 倍", "98%", "3%", "2158", "19.18", "484.44", "37.1%", "92.8%", "50.6%",
          "1.000", "0.774", "42.5%", "60.1%", "56.2%", "11/12", "87.60", "88.09",
          "47.14", "47.99", "1.28", "0.48", "1.45", "2.16", "3.65",
          "+0.41%", "+2.10%", "+2.34%", "+7.17%", "2048", "2026-10-07"]:
    chk(n in BODY, f"数字在场 {n}")

print("[12/17] 四处自曝 / 边界声明在场")
chk("精确最优解" in BODY, "自曝①：逐元素排序是错目标的精确最优解")
chk("最小的那个提升是 **+0.48**" in BODY, "自曝②：主动摆出最小增益 +0.48")
chk("practical boundary" in BODY and "矫正器" in BODY, "自曝③：耦合成本（候选集差则救不回）")
chk("参考，不是严格上界" in BODY, "自曝④：全注意力是参考不是严格上界")
chk("必须**不对称**" in BODY, "自测边界①：不对称才看得见")
chk("代价随预算收紧而放大" in BODY, "自测边界②：预算")
chk("单列内部根本不存在抵消" in BODY, "自测边界③：单列看不见")
chk("看的是两条线分开的那一段，不是绝对值" in BODY, "图下必写的那句（非绝对值）")

print("[13] 爆款要素抽查")
title = TEXT.split("\n")[1].split('"')[1]
chk("66 倍" in title and "98%" in title, "标题含双数字反差")
chk(title.endswith("？"), "标题为疑问句")
chk("矩阵乘法" in BODY.split("## ")[0] or "算例" in BODY.split("## ")[0], "开头钩子亮明是什么")
intro = BODY.split("## ")[0]
chk(re.search(r"(第 ?\d+ ?篇|上一篇|在上一篇)", intro) is None, "开头零导航")
chk("值得再问一句" in BODY and "做错了" in BODY, "落点口径：提醒不是打脸")
chk("数学玩具" in BODY, "第七节回应开头的问题")

print("[6] 内链（微信 URL，5 处）")
for u in ["HIBJliEXWtVyJqvH_Ocbog", "HHMNEdCYThOjCLRozQorhg", "1GATyW40jkh1YxuvwVbpUA",
          "QcZUcxYZUw27_J2ykESUHA", "7BdQlueJrRJ5f-x3v_2VqA"]:
    chk(u in BODY, f"内链在场 …/{u}")

print()
print("PASS" if not fails else f"FAIL: {len(fails)} 项未过")
for f in fails:
    print("  ✗", f)
