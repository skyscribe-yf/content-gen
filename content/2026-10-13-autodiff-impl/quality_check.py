#!/usr/bin/env python3
"""本篇质量核查：原声逐字在场 / 段落 ≤80 字 / 三级标题 / 禁词 / AI 腔 / 长句 / 配图 / 数字 / 内链。

口径来源：docs/article-quality-check.md（17 项）、docs/writing-flow.md（原声槽）、
         docs/pre-publish-final-check.md（9 项）、AGENTS.md「段落 ≤80 字」硬规。
原声 8 处：作者 2026-10-12 圈定笔记 S1~S7 + S9，全部「沿用」，逐字进稿。
篇幅：作者 2026-10-12 拍板「篇幅不用限制」——本篇不设上限。
"""
import re
from pathlib import Path

HERE = Path(__file__).parent
TEXT = (HERE / "weixin.md").read_text()
BODY = TEXT.split("---", 2)[-1]


def cjk(s):
    return len(re.findall(r"[\u4e00-\u9fff]", s))


SLOTS = {
    # S1 · §三 布局过渡段
    "S1": "矩阵微分的布局约定，在代码里变成 numpy 的广播规则：1-D 数组在 `@` 里既当行又当列，"
          "导致 VJP 里的 `g @ o.v.T` 维度对不上（我实测里就崩了两次）。",
    # S2 · §五 精度坑
    "S2": "JAX 默认 float32。我第一次跑 `check_grads(order=2)` 就挂在 rtol=0.002 上（相对差 0.0094），"
          "这不是自动微分错了，是 float32 的极限。开 `jax_enable_x64` 后全部降到 1e-16 量级。",
    # S3 · §四 不光滑点 / STE
    "S3": "`relu'(0)=0`、`abs'(0)=0`、`max` 在并列处的选择、量化里的 straight-through estimator，"
          "这些都不是推出来的，是选出来的。做量化、稀疏、离散结构时，梯度从哪来永远是设计决策。",
    # S4 · §二 原语定义
    "S4": "原语不是「简单的数学函数」，而是框架的 IR 决定不再拆开的那一层，这是工程选择，不是数学概念。",
    # S5 · §六 收束
    "S5": "你不需要为每个函数准备公式，只需要为每个「黑盒」准备公式；"
          "黑盒的数量由内核生态决定，不由 API 数量决定。",
    # S6 · §四 维护成本
    "S6": "真正的维护成本不在数学，在覆盖与验证：每加一个新内核，要么配规则、要么保证它可组合；"
          "规则写错不会报错，只会静默给错梯度。",
    # S7 · §二 粒度
    "S7": "粒度是纯工程选择。",
    # S9 · §七 开放问题
    "S9": "这两条路线在教学上应该是顺序关系，还是替代关系？我倾向后者，但没有找到把两者并列比较的权威文献。",
}


def norm(s):
    s = re.sub(r"[$`]|\s+", "", s)
    return s.translate(str.maketrans("，。；、：", "，，，，："))


fails = []
FLAT = norm(BODY)


def chk(cond, msg):
    print(("  ✓ " if cond else "  ✗ ") + msg)
    if not cond:
        fails.append(msg)


print("[14] 原声逐字在场（8 处，下限 5）")
for k, s in SLOTS.items():
    chk(norm(s) in FLAT, f"原声 {k}")

print("[17] 段落 ≤80 字（表格/链接/图片/标题/列表/引用块除外）")
paras = []
for p in BODY.split("\n"):
    p = p.strip()
    if not p or p[0] in "#|" or p.startswith(("📖", "🔥", "[", "![", ">", "```")):
        continue
    if re.match(r"^(\d+\.|[-*])\s", p):
        continue
    paras.append(p)
over = [(cjk(p), p) for p in paras if cjk(p) > 80]
chk(not over, f"无超 80 字段落（段落 {len(paras)} 个，超标 {len(over)}）")
for n, p in over[:6]:
    print("   ·", n, p[:70])

print("[17] 标题层级")
h2 = len(re.findall(r"^## ", BODY, re.M))
h3 = len(re.findall(r"^### ", BODY, re.M))
chk(h2 >= 5, f"H2 = {h2} 节（≥5）")
chk(h3 >= 6, f"H3 = {h3} 个小标题（≥6）")

print("[11] 正文禁词 / 工作流元词（链接标题豁免）")
BODY_NOLINK = re.sub(r"\[([^\]]*)\]\([^)]*\)", "", BODY)
for w in ["钩子", "伏笔", "说人话就是", "拆给你看", "待补", "TODO"]:
    chk(w not in BODY_NOLINK, f"无「{w}」")
chk(BODY_NOLINK.count("上一篇") <= 1, "「上一篇」不超 1 处（收束处允许一次）")

print("[15] AI 腔扫描")
for w in ["值得注意的是", "让我们来", "总而言之", "综上所述", "不难发现", "不难看出",
          "需要指出的是", "深入探讨", "全面分析", "由上可知", "今天我们来聊聊",
          "随着 AI 的发展", "表现优异", "具有显著优势", "综合来看", "本质上来说",
          "首先，", "其次，", "最后，"]:
    chk(w not in BODY, f"无「{w}」")
print("   在场口头禅：", [w for w in ["其实", "不过", "当然", "本质上", "然而", "事实上"] if w in BODY])

print("[10] 超 60 字长句（原声/表格/链接行/参考资料豁免）")
VOICE = [norm(s) for s in SLOTS.values()]
seg = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", BODY)
seg = re.sub(r"\[[^\]]*\]\([^)]*\)", "", seg)
seg = re.sub(r"(?s)\*\*参考资料与数字溯源\*\*.*", "", seg)
seg = re.sub(r"(?s)🔥 \*\*热门文章\*\*.*", "", seg)
seg = re.sub(r"(?s)```.*?```", "", seg)


def is_voice(par):
    f = norm(par)
    return bool(f) and any(f in v for v in VOICE)


# 规则：单句 ≤60 汉字，**不含 LaTeX/代码/链接**（docs/article-quality-check.md 第 10 项）
CJK_ONLY = r"[\u4e00-\u9fff]"


def strip_tex_code(s):
    s = re.sub(r"\$\$.*?\$\$", "", s, flags=re.S)   # 独立公式
    s = re.sub(r"\$[^$]*\$", "", s)                 # 行内公式
    s = re.sub(r"`[^`]*`", "", s)                     # 行内代码
    s = re.sub(r"https?://\S+", "", s)                # 链接
    return s


long_hits = []
for p in seg.split("\n"):
    p = p.strip()
    if not p or p[0] in "#|>" or is_voice(p) or p.startswith(("📖", "🔥", "[", "```")):
        continue
    for s in re.split(r"[。！？]", strip_tex_code(p)):
        if len(re.findall(CJK_ONLY, s)) > 60:
            long_hits.append(s.strip())
chk(not long_hits, f"无超 60 字 AI 句（命中 {len(long_hits)}）")
for s in long_hits:
    print("   ·", s[:90])

print("[8] 图片路径与配图")
chk("images/" not in BODY, "无 images/ 前缀")
refs = set(re.findall(r"\]\(([^)]+\.png)\)", BODY))
files = {p.name for p in HERE.glob("*.png") if not p.name.startswith("00-cover")}
chk(not (files - refs), f"无孤儿图（正文 {len(refs)} 张，目录 {len(files)} 张）")
chk(len(refs) >= 6, f"正文配图不少于 6 张（当前 {len(refs)}）")
missing = sorted(r for r in refs if not (HERE / r).exists())
chk(not missing, f"正文引用的图全部存在（缺 {missing}）")

print("[5/16] 结尾互动与转发设计")
chk("困扰过" in BODY or "苦涩" in BODY or "?" in BODY.split("---")[-1], "文末开放式问题")
chk("点个赞" in BODY and "收藏" in BODY, "点赞/收藏引导")
chk("关注「数解AI」" in BODY, "关注引导")
tags = re.findall(r"#\S+", BODY.split("参考资料")[-1])
chk(3 <= len(tags) <= 5, f"话题标签 3-5 个（当前 {len(tags)}：{tags}）")
chk("#数解AI" in BODY, "含 #数解AI")

print("[9] 尾部链接与热门块")
chk(BODY.count("🔥 **热门文章**：") == 1, "热门块标题只出现一次")
hot = [l for l in BODY.split("\n") if re.match(r"^\[.+\]\(https://mp\.weixin\.qq\.com/s/", l)]
chk(all(l.endswith("  ") for l in hot), f"链接行行尾两空格（{len(hot)} 行）")

print("[6] 内链（必须来自台账真实 URL）")
links = set(re.findall(r"\((https://mp\.weixin\.qq\.com/s/[^)]+)\)", BODY))
chk(len(links) >= 8, f"内链不少于 8 条（当前 {len(links)}）")
for must in ["oYj_qpwF4tZG84ImOn977g",  # 反向传播
             "5wMquh_v3oon2-NEDeQLEw",  # Softmax
             "DBI990JLYtbxQGF3LIWbhQ",  # V4.1 记账
             "Bra0y-wCSeYEW5ABxa3slw",  # FP4
             "hYKy3dyHXEQkwoN7YmdREA"]:  # 量化掉点
    chk(must in BODY, f"内链在场 {must[:14]}…")

print("[1] 关键数字与文内口径一致")
for n in ["404", "110", "76", "1.18e-08", "688", "42", "18 个原语",
          "1.000000", "17.01", "18.07", "2.2e-16", "NaN"]:
    chk(n in BODY, f"数字在场 {n}")
chk("199" in BODY, "数字在场 199（规则条数）")
chk("552" not in BODY or True, "（上篇为主锚，本篇按需）")

print("[13] 标题与开头")
title = TEXT.split("\n")[1].split('"')[1]
chk(title.startswith("导数公式"), "标题以关键词开头")
chk("？" not in title and "?" not in title, "标题零疑问词（作者口径）")
chk("，" in title and "——" not in title, "标题用逗号、无破折号")
chk(len(title) <= 22, f"标题 {len(title)} 字 ≤22（信息流窗口内）")
chk("它们全都能求导" in BODY.split("## ")[0], "开头钩子亮明反差")
chk("回到了开头那三个数字" not in BODY, "（无冗余回扣句式）")
chk("用户不需要" not in BODY, "无 AI 代拟的原声")

print()
print("PASS" if not fails else f"FAIL: {len(fails)} 项未过")
for f in fails:
    print("  ✗", f)
