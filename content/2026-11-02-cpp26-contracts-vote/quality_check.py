#!/usr/bin/env python3
"""本篇质量核查（模板：content/2026-10-10-context-rot-isolation/quality_check.py）。

机器可查部分：原声逐字在场 / 段落 ≤80 字 / 标题层级（>400 字段落须有 ###）/
禁词 / AI 腔 / 长句 / 图片路径与封面台账 / 结尾设计 / 爆款要素 / 关键数字与口径。
"""
import json
import re
from pathlib import Path

HERE = Path(__file__).parent
TEXT = (HERE / "weixin.md").read_text()
BODY = TEXT.split("---", 2)[-1]


def cjk(s):
    return len(re.findall(r"[\u4e00-\u9fff]", s))


# 作者原声 7 处（来源 outline.md ## 作者原声槽，逐字；一处可含多句）
SLOTS = [
    "作为一名深耕 C++ 技术十几年，然后这几年逐渐转移了主要注意力的老技术人，看到这个新闻甚至有点恍如隔世。难道 C++0x 最后变成十六进制数 0xa 的历史还要重演？这都什么年代了，他们所争论的话题，是否还能够让这门古老、复杂、高效但是又僵化的语言具备更持久一些的生命力？",
    "这个就好比只在 DEBUG 模式下打开的 assert，如果关键的逻辑有一些放在了这个 assert 里面被展开计算，正式发给用户的软件行为就会和开发模式下不尽相同。",
    "其实我倒是挺能理解 Bjarne 推崇的固化的方式，而不是仅仅作为语言机制层面的约束。但是考虑到各种历史上的语言演化过程中的僵化和决策进度缓慢的问题，可能 Sutter 的略微激进的方式更能适应当今这个快速变化的世界。",
    "根据我个人使用 AI 的经验来看，现在主流的大模型的指令遵循能力已经非常强，以至于到了过于僵化、照单全收的境地。代码里面存在的一些注释和文档，只要被 agent 读取到了，就会被一股脑纳入到后续步骤的推理中去。尽管这个过程还带有一些概率上的不确定性，叠加上已有的 RLVR 技术和环境里面的验证手段，很多错误的采样轨迹其实大多情况下也会被很好地掩盖过去。",
    "有时候 AI 一次性写出来上万行的代码，我其实很难仔细地逐一阅读和审查这些代码，只能做到草草看个大概。",
    "这个世界变化真是大。还记得，没几年前某次 CppCon 大会上，对委员会核心成员的 grill the panel 环节互动里面，还有一个专门处理文案工作的小姐姐，被 Herb Sutter 隆重介绍过。这位小姐姐的工作，显然已经被 Claude 替代了吧。",
    "尽管是纯文字的规格，还是有很多环境方面的约束，和自动化执行的测试验收方式可以来检查这些规格。",
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


print("[14] 原声逐字在场（7 处，≥5 达标）")
miss = [i for i, s in enumerate(SLOTS, 1) if re.sub(r"\s+", "", s) not in FLAT]
chk(not miss, f"原声全部在场（缺 {miss}）")
chk("★" not in BODY and "> " not in BODY.replace("→ ", ""), "原声无 ★ 前缀 / 无 blockquote 装饰")

print("[新] 段落 ≤80 字（链接/标签块/列表/图除外）")
paras = []
for p in BODY.split("\n"):
    p = p.strip()
    if not p or p[0] in "#|" or p.startswith(("📖", "🔥")):
        continue
    if re.match(r"^(\d+\.|[-*])\s", p) or p.startswith("!["):
        continue
    paras.append(p)
over = [(cjk(p), p) for p in paras if cjk(p) > 80]
chk(not over, f"无超 80 字段落（段落 {len(paras)} 个，超标 {len(over)}）")
for n, p in over[:5]:
    print("   ·", n, p[:60])

print("[新] 标题层级：H2 ≥5；>400 字的 ## 节须含 ###")
h2 = len(re.findall(r"(?m)^## ", BODY))
chk(h2 >= 5, f"H2={h2} 节")
secs = re.split(r"(?m)^(## .+)$", BODY)
bad = []
for i in range(1, len(secs), 2):
    body = secs[i + 1]
    if cjk(body) > 400 and "### " not in body:
        bad.append(secs[i])
chk(not bad, f"超 400 字段落均有 ### 小标题（违规 {bad}）")

print("[11] 正文禁词 / 工作流元词")
BODY_NOLINKTXT = re.sub(r"\[([^\]]*)\]\([^)]+\)", "", BODY)
for w in ["钩子", "伏笔", "说人话就是", "上一篇", "篇N", "拆给你看", "待发布", "待补", "死了"]:
    chk(w not in BODY_NOLINKTXT, f"无「{w}」")

print("[15] AI 腔扫描")
for w in ["值得注意的是", "让我们来", "总而言之", "综上所述", "不难发现", "不难看出",
          "需要指出的是", "深入探讨", "全面分析", "由上可知", "今天我们来聊聊",
          "随着AI的发展", "随着 AI 的发展", "表现优异", "具有显著优势", "综合来看"]:
    chk(w not in BODY, f"无「{w}」")

print("[12] 「拆」字逐处判断")
for m in re.findall(r".{8}拆.{8}", BODY_NOLINKTXT):
    print("   ·", m.replace("\n", " "))

print("[10] 超 60 汉字长句（口径：article-quality-check 第 10 项，脚本阈值 66；原声/参考资料/导航块豁免）")
seg = re.sub(r"\((https?://[^)]+)\)", "()", BODY)
seg = re.sub(r"!\[[^\]]*\]\([^)]+\)", "", seg)
seg = re.sub(r"(?s)\*\*参考资料与数字溯源\*\*.*", "", seg)
seg = "\n".join(p for p in seg.split("\n") if not is_voice(p))


def vlen(s: str) -> int:
    """可视字数：汉字与中文标点计 1，西文/数字词条计 2（一条约 1-2 字）。"""
    cn = len(re.findall(r"[\u4e00-\u9fff\u3000-\u303f\uff00-\uffef]", s))
    return cn + 2 * len(re.findall(r"[A-Za-z0-9][A-Za-z0-9.+\-]*", s))


long_hits = [s.strip() for s in re.split(r"[。！？\n]", seg) if vlen(s.strip()) > 66]
chk(not long_hits, f"无超 66 可视字长句（命中 {len(long_hits)}）")
for s in long_hits:
    print("   ·", vlen(s), s[:90])

print("[8] 图片路径与配图")
chk("images/" not in BODY, "无 images/ 前缀")
refs = set(re.findall(r"\]\(([^)]+\.png)\)", BODY))
missing = sorted(r for r in refs if not (HERE / r).exists())
chk(not missing, f"引用的图都存在（缺 {missing}）")
files = {p.name for p in HERE.glob("*.png") if not p.name.startswith("00-cover")}
chk(not (files - refs), f"无孤儿图（正文 {len(refs)} 张，目录 {len(files)} 张）")

print("[封面] 脚本叠字台账（AGENTS.md 封面硬规则）")
meta = json.loads((HERE / "cover_meta.json").read_text())
chk((HERE / "00-cover-base.png").exists(), "00-cover-base.png 存在（无字底图 = 脚本叠字证据）")
chk(meta["total_chars"] <= 12, f"封面文字 {meta['total_chars']} 字 ≤12")
chk(meta["block_ratio"] <= 0.25, f"文字块高 {meta['block_ratio']:.1%} ≤25%")
w, h = meta["canvas"]
chk(abs(w / h - 21 / 9) < 0.01, f"画布 {w}x{h} = 21:9")

print("[5/16] 结尾互动与转发设计")
chk("你的项目里，那些检查是随时可以关掉的吗" in BODY, "文末互动问在场")
chk("点赞" in BODY and "收藏" in BODY and "转发" in BODY, "点赞/收藏/转发引导")
tags = re.findall(r"#\S+", BODY.split("参考资料")[-1])
chk(3 <= len(tags) <= 5, f"话题标签 3-5 个（当前 {len(tags)}）")
chk("#数解AI" in BODY, "含 #数解AI")

print("[13] 爆款要素抽查")
chk("？" in TEXT.split("\n")[1], "标题疑问句")
head = "\n".join(BODY.split("\n")[:12])
chk("如果检查可以随时关掉" in head, "驱动问题在开头亮明")
chk("规格谁来验" in BODY, "下一篇预告在位")

print("[1] 关键数字与口径纪律")
for n in ["12", "14", "20", "9", "22", "114:12:3", "0.3%", "18.13", "87%",
          "36 个月", "2027", "0xa", "2019", "2026-10-24", "11 月 16 日"]:
    chk(n in BODY, f"数字在场 {n}")
for w in ["据报道", "据知"]:
    chk(w in BODY, f"hedging 口径「{w}」在场")
for p in ["P2900", "P4334R0", "P4208R0", "P4433R0", "P3846R1", "P4381R0",
          "Reply-to: Claude Opus 4.6", "intent formalization"]:
    chk(p in BODY, f"关键实体 {p} 在场")

print()
print("PASS" if not fails else f"FAIL: {len(fails)} 项未过")
for f in fails:
    print("  ✗", f)
