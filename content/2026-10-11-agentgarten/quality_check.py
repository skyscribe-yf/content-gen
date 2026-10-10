#!/usr/bin/env python3
"""本篇质量核查中机器可查部分：原声逐字在场 / 段落 ≤80 字 / 三级标题 / 禁词 / AI 腔 / 长句 / 配图 / 数字口径。

口径来源：docs/article-quality-check.md（17 项）、docs/writing-flow.md（原声槽）、
         docs/pre-publish-final-check.md（9 项）、AGENTS.md「段落 ≤80 字」硬规。
原声 14 处逐字来自 outline.md ## 作者原声槽（作者 2026-10-11 拍板：不开空槽，全部沿用笔记 §6/§7 原文）。
"""
import re
from pathlib import Path

HERE = Path(__file__).parent
TEXT = (HERE / "weixin.md").read_text()
BODY = TEXT.split("---", 2)[-1]


def cjk(s):
    return len(re.findall(r"[\u4e00-\u9fff]", s))


SLOTS = [
    # C1
    "从这个角度来思考，其实 AGI 并不是普通公众想象的那样，真的可以从底层逻辑上，能代替人类去探索未知的世界。",
    # C2
    "一个本体论就是错的代码世界，可以完美地一致、确定、可复现：它是一个运行良好的错误宇宙。",
    # C3
    "可验证性没有被“获得”，只是被“转移”，且转移过程中丢失了原图。",
    # C4
    "虚妄不是一个明确的错误，而是生成时无人审视的建模选择，被确定性执行放大成了物理定律。",
    # C5
    "这与 durable execution 的教训同构：replay 一万次一致，不能证明第一次记录的语义解读是对的。",
    # C6
    "损失是范式级的默认行为，不是优化失败的副产品。",
    # C7
    "最深层的损失是那些从未成为记录候选物的 mundane 具身经验——而那恰恰是物理直觉和可供性的基座。",
    # C8
    "多样性可以被再注入：温度、噪声、domain randomization、novelty search——代价只是算力。但这些方法只能在数据支撑集内部重新排列，支撑集之外一点也补不了。",
    # C9
    "整个技术栈里现实接触通道只有一条窄缝（AgentGarten 里就是渲染器的训练视频）——“真”的总量由最窄的通道决定。",
    # C10
    "绝望只属于主观体验区（永久丢失、无法重测）；物理世界有活的实验通道，没那么绝望。",
    # C11
    "模型自己的采样永远落在自己分布的支撑集里——探索半径被生成器本身锁死。",
    # C12
    "黑客帝国采集的是状态（人当传感器，输出脑波）——溯因不住在状态里，住在行动里；西部世界采集的是正在运转的溯因器（客人在追自己的目标，每个行动都是一次活的猜测）——不是数据库，是溯因器的原位观测站。",
    # C13
    "园区的正确设计目标不是“采集代表性的人类”，而是引导人们去做没做过的事、体验没经历过的体验——把采集问题变成体验课程设计问题，最大化溯因器的运转密度。",
    # C14
    "AgentGarten 是给“压缩后的世界”造游乐场；打破压缩需要的是给“活着的世界”造窗口。",
]
# C8 拆段处补一个「。」之外无改动；C12 拆段处补「；」之外无改动。均为原句自带句读处，未增删字。

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


print("[14] 原声逐字在场（14 处，下限 5）")
for i, s in enumerate(SLOTS, 1):
    chk(re.sub(r"\s+", "", s) in FLAT, f"原声 C{i}")

print("[新] 段落 ≤80 字（链接/标签块/列表除外）")
paras = []
for p in BODY.split("\n"):
    p = p.strip()
    if not p or p[0] in "#|" or p.startswith("📖") or p.startswith("🔥") or p.startswith("["):
        continue
    if re.match(r"^(\d+\.|[-*])\s", p) or p.startswith("!["):
        continue
    paras.append(p)
over = [(cjk(p), p) for p in paras]
over = [x for x in over if x[0] > 80]
chk(not over, f"无超 80 字段落（段落 {len(paras)} 个，超标 {len(over)}）")
for n, p in over[:5]:
    print("   ·", n, p[:60])

print("[新] 标题层级：H2 节 + H3 小标题")
h2 = len(re.findall(r"^## ", BODY, re.M))
h3 = len(re.findall(r"^### ", BODY, re.M))
chk(h2 >= 5 and h3 >= 6, f"H2={h2} 节、H3={h3} 个小标题")

print("[11] 正文禁词 / 工作流元词（链接标题豁免）")
BODY_NOLINKTXT = re.sub(r"\[([^\]]*)\]\([^)]*\)", "", BODY)
for w in ["钩子", "伏笔", "说人话就是", "上一篇", "在上一篇", "篇N", "拆给你看", "待发布", "待补"]:
    chk(w not in BODY_NOLINKTXT, f"无「{w}」")

print("[15] AI 腔扫描")
ai_words = ["值得注意的是", "让我们来", "总而言之", "综上所述", "不难发现", "不难看出",
            "需要指出的是", "深入探讨", "全面分析", "由上可知", "今天我们来聊聊",
            "随着AI的发展", "随着 AI 的发展", "表现优异", "具有显著优势", "综合来看",
            "首先，", "其次，", "最后，" ]
for w in ai_words:
    chk(w not in BODY, f"无「{w}」")

print("[12] 「拆」字逐处判断（链接标题豁免；提示项，不判失败）")
for m in re.findall(r".{10}拆.{10}", BODY_NOLINKTXT):
    print("   ·", m.replace("\n", " "))
print("   （若超过 2 处，成稿前逐处判断是否可用「切开/分成/读完」替换）")

print("[10] 超 60 字长句（原声段落/参考资料/列表/链接行豁免）")
seg = re.sub(r"\((https?://[^)]+)\)", "()", BODY)
seg = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", seg)
seg = re.sub(r"\[[^\]]*\]\([^)]*\)", "", seg)
seg = re.sub(r"(?s)\*\*参考资料与数字溯源\*\*.*", "", seg)
seg = "\n".join(p for p in seg.split("\n") if not is_voice(p) and not p.strip().startswith("|") and not p.strip().startswith("📖"))
long_hits = [s.strip() for s in re.split(r"[。！？\n]", seg) if len(s.strip()) > 60]
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
print("   · 尚无文件的引用（配图未生成）：", missing if missing else "无")

print("[5/16] 结尾互动与转发设计")
chk("评论区聊聊" in BODY, "文末开放式问题")
chk("点个赞" in BODY and "收藏" in BODY, "点赞/收藏引导")
chk("关注「数解AI」" in BODY, "关注引导")
tags = re.findall(r"#\S+", BODY.split("参考资料")[-1])
chk(3 <= len(tags) <= 5, f"话题标签 3-5 个（当前 {len(tags)}：{tags}）")
chk("#数解AI" in BODY, "含 #数解AI")

print("[6b] 热门文章块")
chk("🔥 **热门文章**：" in BODY, "热门块存在（hot_articles.py 生成格式）")
chk("HOT_ARTICLES_HERE" not in BODY, "占位符已替换")
hot = [l for l in BODY.split("\n") if re.match(r"^\[.+\]\(https://mp\.weixin\.qq\.com/s/", l)]
chk(all(l.endswith("  ") for l in hot), f"热门/引用行行尾两空格（{len(hot)} 行）")

print("[1] 关键数字与文内口径一致")
for n in ["2,500 万", "7,500 万", "第 4 轮", "第 10 轮", "36.5 帧", "438.8 毫秒", "480×832",
          "414.4 毫秒", "1 亿"]:
    chk(n in BODY, f"数字在场 {n}")
chk("2026" in BODY, "年份口径在场（2026）")
chk("2026 年 10 月 8 日" in BODY, "论文日期在场")
for t in ["世界模型", "代码世界", "溯因", "playbook", "几何"]:
    chk(t in BODY, f"术语在场 {t}")

print("[13] 爆款要素抽查")
chk("1 亿" in TEXT.split("\n")[1], "标题含数字反差")
chk("OpenAI" in TEXT.split("\n")[1][:24], "品牌词前置（22 字窗口内）")
chk("差别在它换了一块练习场" in BODY, "驱动句在开头亮明")
chk("回到开头那两组数字" in BODY, "首尾闭环")

print()
print("PASS" if not fails else f"FAIL: {len(fails)} 项未过")
for f in fails:
    print("  ✗", f)
