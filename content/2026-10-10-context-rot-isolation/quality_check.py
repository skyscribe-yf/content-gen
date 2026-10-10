#!/usr/bin/env python3
"""本篇 16 项质量核查中机器可查部分 + 作者 2026-10-10 新增口径（段落 ≤80 字 / 三级标题）。"""
import re
from pathlib import Path

HERE = Path(__file__).parent
TEXT = (HERE / "weixin.md").read_text()
BODY = TEXT.split("---", 2)[-1]
def cjk(s):
    return len(re.findall(r"[\u4e00-\u9fff]", s))

# 原声 8 处逐字（来源 outline.md ## 作者原声槽）
# 槽 3b / 槽 4 各把 1 个「，」换成「。」用于分段（仅加标点，未增删任何字，已向作者声明）
SLOTS = [
    "这个问题，基本上所有模型都会出现，也就是大家经常调侃的大模型流口水现象。所以懂行的朋友都知道一个会话不能复用太久，需要经常主动压缩上下文，或者fork重新开一个会话。",
    "我觉得最麻烦的地方在于这个开始含糊不清，看起来像是降智不遵循指令的情况是什么时候开始发生的，完全没有办法实现界定，很多时候只能凭借感觉和经验来判定。",
    "其实两个问题的后果都很严重，操作agent的人如果能有足够的背景知识来正确地判断具体是哪一种，然后有的放矢去应对更好。如果是发生了上下文冲突导致模型陷入困顿，那么及时下达转舵指令，帮助模型获取清晰而又无歧义的上下文，比放任它去猜测和胡乱验证要好得多。如果是因为太长导致上下文注意力涣散，那么及时fork或者是压缩上下文才是正解。",
    "这个问题其实还有更复杂的一面，是不同的agent的上下文压缩效果差异很多，比如codex就以极其优秀的上下文压缩能力著称，你可以放心地压缩三四次都不丢失太多智能。",
    "很多时候，我觉得无脑追逐超长上下文，然后对agent执行过程可能出现的大偏差弃之不顾的人，行为逻辑着实难以理解。",
    "因为他们可能压根就不在乎他们的钱包，也很可能不在乎所浪费的时间，加上很多模型提供商对于超过一定长度的上下文之后，会加倍收费的定价策略，可能这些人也毫不在意吧。",
    "是不是模型厂商就故意借口推理成本增加来收取高价格，然后给你提供的服务是打折扣的？自己需要多多判断吧。",
    "曾经有一次，我尝试让opencode去对一整天产生的巨量的代码变更做一次性审计，然后基于我那复杂的checklist来仔细审查，报告问题到github上面去。",
    "结果还没有读取完所有的diff,上下文就超了，自动压缩的结果又是乏善可陈的，真的是赔了夫人又折兵。",
    "自己根据实际的应用场景，编排和设计合理的分工场景，用好当下AI及其强大的一般推理能力，做好分治，就能从AI里面得到更多更好更快的结果。",
    "而这样，就需要操作Agent的人时不时盯着它的轨迹看看有没有纠偏，所以从人们把agent比作是harness的情况来看，还真的是需要人类时刻把好缰绳，不能放手吗？",
]

fails = []

FLAT = re.sub(r"\s+", "", BODY)          # 段落切分不影响逐字核验
SLOT_FLAT = [re.sub(r"\s+", "", s) for s in SLOTS]


def is_voice(par: str) -> bool:
    """该段落属于作者原声（原声可跨段拆分，故用扁平化包含判定）。"""
    f = re.sub(r"\s+", "", par)
    return bool(f) and any(f in s for s in SLOT_FLAT)


def chk(cond, msg):
    print(("  ✓ " if cond else "  ✗ ") + msg)
    if not cond:
        fails.append(msg)


print("[14] 原声逐字在场（11 个句子段 / 8 处，≥5 达标）")
for i, s in enumerate(SLOTS, 1):
    chk(re.sub(r"\s+", "", s) in FLAT, f"原声 {i}")

print("[新] 段落 ≤80 字（作者 2026-10-10；链接/标签块/列表除外）")
paras = []
for p in BODY.split("\n"):
    p = p.strip()
    if not p or p[0] in "#|" or p.startswith("📖") or p.startswith("🔥"):
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
            "随着AI的发展", "随着 AI 的发展", "表现优异", "具有显著优势", "综合来看"]
for w in ai_words:
    chk(w not in BODY, f"无「{w}」")

print("[12] 「拆」字逐处判断（链接标题豁免）")
hits = re.findall(r".{10}拆.{10}", BODY_NOLINKTXT)
if not hits:
    chk(True, "无「拆」字")
for m in hits:
    print("   ·", m.replace("\n", " "))

print("[10] 超 60 字长句（原声段落/参考资料/导航块豁免）")
seg = re.sub(r"\((https?://[^)]+)\)", "()", BODY)
seg = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", seg)
seg = re.sub(r"(?s)\*\*参考资料与数字溯源\*\*.*", "", seg)
seg = "\n".join(p for p in seg.split("\n") if not is_voice(p))
long_hits = [s.strip() for s in re.split(r"[。！？\n]", seg) if len(s.strip()) > 60]
chk(not long_hits, f"无超 60 字 AI 句（命中 {len(long_hits)}）")
for s in long_hits:
    print("   ·", s[:90])

print("[8] 图片路径与配图数量")
chk("images/" not in BODY, "无 images/ 前缀")
refs = set(re.findall(r"\]\(([^)]+\.png)\)", BODY))
missing = sorted(r for r in refs if not (HERE / r).exists())
chk(not missing, f"引用的图都存在（缺 {missing}）")
files = {p.name for p in HERE.glob("*.png") if not p.name.startswith("00-cover")}
chk(not (files - refs), f"无孤儿图（正文 {len(refs)} 张，目录 {len(files)} 张）")
chk(len(refs) >= 6, f"正文配图不少于 6 张（当前 {len(refs)}）")

print("[5/16] 结尾互动与转发设计")
chk("把好缰绳" in BODY, "文末互动问（缰绳反问，作者原声）")
chk("点个赞" in BODY and "收藏" in BODY, "点赞/收藏引导")
tags = re.findall(r"#\S+", BODY.split("参考资料")[-1])
chk(3 <= len(tags) <= 5, f"话题标签 3-5 个（当前 {len(tags)}）")
chk("#数解AI" in BODY, "含 #数解AI")

print("[13] 爆款要素抽查")
chk("？" in TEXT.split("\n")[1], "标题疑问句")
chk("它是先放弃了" in BODY, "驱动问题在开头亮明")
chk("回到开头那个跑了一夜的 agent" in BODY, "首尾闭环")

print("[1] 关键数字与文内口径一致")
for n in ["43.2%", "0.556", "0.302", "45.5%", "8.2", "194,480", "18 个模型",
          "12,570", "7,330", "0.9935", "0.87%", "150,000", "200,000",
          "25.6 万", "4 倍", "15 倍"]:
    chk(n in BODY, f"数字在场 {n}")
chk("2026" in BODY, "年份口径在场（2026）")
chk("Context Rot" in BODY, "术语 Context Rot 在场")
chk("参与权" in BODY, "自造术语 参与权 在场")

print()
print("PASS" if not fails else f"FAIL: {len(fails)} 项未过")
for f in fails:
    print("  ✗", f)
