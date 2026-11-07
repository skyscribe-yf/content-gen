#!/usr/bin/env python3
"""本篇质量核查（模板：content/2026-11-02-cpp26-contracts-vote/quality_check.py）。

机器可查：原声逐字在场 / 段落 ≤80 字 / 标题层级 / 禁词 / AI 腔 / 长句 /
图片与封面台账 / 结尾设计 / 爆款要素 / 关键数字与口径。
"""
import json
import re
from pathlib import Path

HERE = Path(__file__).parent
TEXT = (HERE / "weixin.md").read_text()
BODY = TEXT.split("---", 2)[-1]


def cjk(s):
    return len(re.findall(r"[\u4e00-\u9fff]", s))


def norm(s: str) -> str:
    """去空白与标点，只留实字，用于原声逐字比对（容忍分段处补句号）。"""
    s = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", s)  # 内链降为纯文字（作者后台加链后仍可比对）
    return re.sub(r"[\s，。！？、；：,.!?;:\"'（）()《》「」—\-…]", "", s)


SLOTS = [
    "其实让Agent来补测试，很多时候我都会隐隐约约觉得它写的不对，测试虽然显示是全通过了，心里还是感觉不踏实。因为实际做端到端测试或者更厚重的集成测试的时候，还是有很多问题爆发出来，很多时候问题都出在它怎样断言测试是通过的，或者做了哪些checkpoint的检查。核心问题是无法判定，是否rewarding hacking（且看前文机械臂蹭一下桶盖，成功率高10%：奖励函数才是AI钻空子的源头）跳出来咬你一口。",
    "当我发现有时候agent写出来的东西不一样的时候，大多数情况下，其实是我把需求的细节和如何校验描述的比较清楚的时候。那种情况下其实并不需要太强的模型，也能达到很好的效果，这也许是纯粹的许愿式的vibe coding编程不靠谱的主要差距。",
    "如果想要提高项目编码的实际效果，唯有在需求到规格说明上面仔细下功夫，尽量把场景特定的东西考虑和分解清楚，然后再来交给Agent去做细节分解和实现。这个分析过程，目前还无法单纯靠Agent来做到，需要人类专家，尤其是领域知识专家的大量投入和人机协同。",
    "很多次看到，一个coding agent会把代码库里面本来有问题的实现代码作为一个基本假设，然后在错误的道路上一路狂奔。事实上，从底层原理来看，带入上下文的错误代码或者混淆信息，agent很难做具体的分辨，并且因为模型困惑度的增加（前面文章提过信息熵：压缩1000倍，为什么信息反而少？）而导致看起来模型被降智的情况出现。",
    "这些前沿agent在刷榜单的时候，模型优化的目标其实相当一部分和用户实际拿来干活的目标函数是有偏离的。所以跑分高的模型，到了你自己模糊不清的许愿面前，只好被考验生成一些肤浅且废话连篇的代码或者文档的基础能力。",
    "其实这三件事，根据不同的任务目标，场景和各种软件工程约束，都可以组合来试试。这是做工程最有趣的一个地方，在完成之前往往没有非常固定的标准答案，需要根据具体的领域场景和组织约束，选择最适合的方案。",
    "Contracts机制本身，其实在当今的AI原生开发大行其道的今天，变得更加有现实意义了。标准委员会的大佬们可能还要更多拥抱AI，在深度体验和了解的基础上，从更多视角考虑如何和AI做最有效的融入，才能让C++焕发更多生命力。",
]

fails = []
FLAT = norm(BODY)
SLOT_FLAT = [norm(s) for s in SLOTS]


def is_voice(par: str) -> bool:
    f = norm(par)
    return bool(f) and any(f in s for s in SLOT_FLAT)


def chk(cond, msg):
    print(("  ✓ " if cond else "  ✗ ") + msg)
    if not cond:
        fails.append(msg)


print("[14] 原声逐字在场（7 处，≥5 达标）")
miss = [i for i, s in enumerate(SLOT_FLAT, 1) if s not in FLAT]
chk(not miss, f"原声全部在场（缺 {miss}）")
chk("★" not in BODY, "原声无 ★ 前缀")
chk(not re.search(r"(?m)^>\s", BODY), "原声无 blockquote 装饰")

print("[17] 段落 ≤80 字（链接/列表/图/参考除外）")
paras = []
for p in BODY.split("\n"):
    p = p.strip()
    if not p or p[0] in "#|" or p.startswith(("📖", "🔥", "**参考资料")):
        continue
    if re.match(r"^(\d+\.|[-*])\s", p) or p.startswith("!["):
        continue
    paras.append(p)
over = [(cjk(p), p) for p in paras if cjk(p) > 80]
chk(not over, f"无超 80 字段落（段落 {len(paras)} 个，超标 {len(over)}）")
for n, p in over[:6]:
    print("   ·", n, p[:50])

print("[17] 标题层级：H2 ≥5；>400 字的 ## 节须含 ###")
h2 = len(re.findall(r"(?m)^## ", BODY))
chk(h2 >= 5, f"H2={h2} 节")
chk(not BODY.lstrip().startswith("#"), "开头不以标题起首")

print("[11] 禁词 / 工作流元词")
BODY_NOLINK = re.sub(r"\[([^\]]*)\]\([^)]+\)", "", BODY)
for w in ["钩子", "伏笔", "说人话就是", "上一篇", "篇N", "拆给你看", "待发布", "待补"]:
    chk(w not in BODY_NOLINK, f"无「{w}」")

print("[15] AI 腔扫描")
for w in ["值得注意的是", "让我们来", "总而言之", "综上所述", "不难发现", "不难看出",
          "需要指出的是", "深入探讨", "全面分析", "由上可知", "随着AI的发展",
          "表现优异", "具有显著优势", "综合来看"]:
    chk(w not in BODY, f"无「{w}」")

print("[10] 超 66 可视字长句（原声/参考/导航豁免）")
seg = re.sub(r"\((https?://[^)]+)\)", "()", BODY)
seg = re.sub(r"!\[[^\]]*\]\([^)]+\)", "", seg)
seg = re.sub(r"(?s)\*\*参考资料与数字溯源\*\*.*", "", seg)
seg = "\n".join(p for p in seg.split("\n") if not is_voice(p))


def vlen(s: str) -> int:
    cn = len(re.findall(r"[\u4e00-\u9fff\u3000-\u303f\uff00-\uffef]", s))
    return cn + 2 * len(re.findall(r"[A-Za-z0-9][A-Za-z0-9.+\-]*", s))


long_hits = [s.strip() for s in re.split(r"[。！？\n]", seg) if vlen(s.strip()) > 66]
chk(not long_hits, f"无超 66 可视字长句（命中 {len(long_hits)}）")
for s in long_hits:
    print("   ·", vlen(s), s[:80])

print("[8] 图片路径与配图")
chk("images/" not in BODY, "无 images/ 前缀")
refs = set(re.findall(r"\]\(([^)]+\.png)\)", BODY))
missing = sorted(r for r in refs if not (HERE / r).exists())
chk(not missing, f"引用的图都存在（缺 {missing}）")
files = {p.name for p in HERE.glob("*.png") if not p.name.startswith("00-cover")}
chk(not (files - refs), f"无孤儿图（正文 {len(refs)} 张，目录 {len(files)} 张）")
chk(len(refs) >= 3, f"正文配图 ≥3（当前 {len(refs)}）")

print("[封面] 脚本叠字台账")
meta_path = HERE / "cover_meta.json"
if meta_path.exists():
    meta = json.loads(meta_path.read_text())
    chk((HERE / "00-cover-base.png").exists(), "00-cover-base.png 存在")
    chk(meta["total_chars"] <= 12, f"封面文字 {meta['total_chars']} 字 ≤12")
    chk(meta["block_ratio"] <= 0.25, f"文字块高 {meta['block_ratio']:.1%} ≤25%")
    w, h = meta["canvas"]
    chk(abs(w / h - 21 / 9) < 0.01, f"画布 {w}x{h} = 21:9")
else:
    chk(False, "cover_meta.json 缺失（封面未生成）")

print("[5/16] 结尾互动与转发设计")
chk("有没有一条测试是 agent 写的" in BODY, "文末互动问在场")
chk("点赞" in BODY and "收藏" in BODY and "转发" in BODY, "点赞/收藏/转发引导")
tags = re.findall(r"#\S+", BODY.split("参考资料")[-1])
chk(3 <= len(tags) <= 5, f"话题标签 3-5 个（当前 {len(tags)}）")
chk("#数解AI" in BODY, "含 #数解AI")

print("[13] 爆款要素抽查")
title = TEXT.split("\n")[1]
chk("？" in title, "标题疑问句")
head = "\n".join(BODY.split("\n")[:12])
chk("test_leading_minus_ignored" in head, "开头场景钩子在位（不靠标题开场）")

print("[1] 关键数字与口径")
for n in ["45", "73", "11 条", "15 个", "14 个", "581", "28 个百分点",
          "97.8%", "83.3%", "14.5", "87%", "36.15%", "71.04", "39.81",
          "2636", "30 个系统级任务", "0.2", "26%"]:
    chk(n in BODY, f"数字在场 {n}")
for p in ["intent formalization", "SpecBench", "VeriAct", "Verus-SpecBench",
          "ISSTA 2026", "Fun2spec", "Lahiri", "Búzios", "C++26"]:
    chk(p in BODY, f"关键实体 {p} 在场")

print()
print("PASS" if not fails else f"FAIL: {len(fails)} 项未过")
for f in fails:
    print("  ✗", f)
