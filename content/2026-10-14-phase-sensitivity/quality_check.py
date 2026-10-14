#!/usr/bin/env python3
"""本篇质量核查中机器可查部分：原声逐字在场 / 段落 ≤80 字 / 三级标题 / 禁词 / AI 腔 / 长句 / 配图 / 数字口径。

口径来源：docs/article-quality-check.md（17 项）、docs/writing-flow.md（原声槽）、
         docs/pre-publish-final-check.md（9 项）、AGENTS.md「段落 ≤80 字」硬规。
原声 7 处来自 outline.md ## 作者原声槽（槽 1–7 全部作者手打，2026-10-12 逐槽采集）。
入稿时对原声做过的改动只有两类，均在 outline.md 备注里记账：
  ① 错别字级：槽 4 `连个` → `两个`；槽 2 `deepseek` → `DeepSeek`
  ② 排版级（不增删任何字）：中英之间加半角空格、槽 4 半角逗号 → 全角逗号
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
    "我感觉那个任务迟迟没有结束，花的时间比预期的要长不少，待翻看了具体思维链才发现原来前面很大一段翻车了。",
    # 槽 2 · §4 机制段之后（作者手打，判断）
    "很难说这是不是DeepSeek有意为之还是不可避免的缺陷，本来长上下文下做到极致压缩的注意力就相当困难，不应该因为这样的缺陷就认为是节省显存的设计本身有问题。",
    # 槽 3 · §5 定理边界之后（作者手打，判断/质疑）
    "其实这篇文章的很多理想化的假设，还是让我有些隐隐的担心。不过理论方向有些时候也不得不如此了。",
    # 槽 4 · §6 两个现场（作者手打，亲历）
    "当时我在修复一个稍微复杂一点的 bug，需要修改的上下文，恰好关联到两个非常相似的模块，文件名字只有后缀不同，里面的实现也是非常样板化的 python 代码。",
    # 槽 5 · §6 推断句之后（作者指定的措辞强度）
    "我倾向于认为",
    # 槽 6 · §7 处置段（作者手打，亲历/经验）
    "其实发现了 agent 走偏，短短几个字的回复给它一点点提示，它马上就从泥坑里爬出来了。即便遇到不起作用的时候，及时 fork 新会话即可。",
    # 槽 7 · 文末互动问（作者手打）
    "你有没有留意到DeepSeek突然在任务一开始就跑偏读错代码的时候？你觉得DeepSeek官方是否已经修复了这个问题？",
]

PLANNED_IMAGES = ["01-code-flip.png", "02-residue-gap.png", "03-knockout.png",
                  "04-gate-preference.png", "05-average-hides.png", "06-same-bet.png"]


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
chk(refs == set(PLANNED_IMAGES), f"正文引用与配图规划一致（引用 {len(refs)} 张）")
files = {p.name for p in HERE.glob("*.png") if not p.name.startswith("00-cover")}
chk(not (files - refs), f"无孤儿图（正文 {len(refs)} 张，目录 {len(files)} 张）")
chk(len(refs) >= 6, f"正文配图不少于 6 张（当前 {len(refs)}）")
missing = sorted(r for r in refs if not (HERE / r).exists())
print(f"   ⏳ 待生成（本项不计失败，配图环节完成后再判）：{missing}")

print("[5/16] 结尾互动与转发设计")
chk("跑偏读错代码的时候" in BODY, "文末开放式问题（原声互动问）")
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

print("[1] 关键数字与文内口径一致")
for n in ["两万 token", "88 行", "16k 个键值对", "40.23", "34.77", "19.14", "14.84", "6.09",
          "75.3", "19.2", "9.9%", "58.4%", "1/128", "52.6、72.1、91.4、84.4"]:
    chk(n in BODY, f"数字在场 {n}")
chk("`8`" in BODY and "`32`" in BODY, "代码补全例的两个答案在场")
chk("80.47 对 81.25" in BODY, "r 与 r+4 对齐的例证在场")
chk("2026-09-28" in BODY, "论文提交日期在场")

print("[12/17] 三处边界声明在场")
chk("不构成" in BODY, "边界①：论文自划「不构成普遍原因」")
chk("论文没有测相似性这个维度" in BODY, "边界②：相似污染是推断")
chk("抽风的原因" in BODY, "边界③：已收窄中文媒体口径")

print("[13] 爆款要素抽查")
title = TEXT.split("\n")[1].split('"')[1]
chk("2 万 token" in title, "标题含数字反差")
chk(title.endswith("？"), "标题为疑问句")
chk("大约两万 token" in BODY.split("## ")[0], "开头钩子亮明量级（正文口径「大约」）")
chk("取错地方" in BODY, "核心区分「取错地方 ≠ 记错」在场")
chk("fork" in BODY and "提示" in BODY, "给出一条可带走的处置（两级）")

print()
print("PASS" if not fails else f"FAIL: {len(fails)} 项未过")
for f in fails:
    print("  ✗", f)
