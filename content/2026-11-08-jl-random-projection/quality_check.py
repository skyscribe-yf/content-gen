#!/usr/bin/env python3
"""本篇 16 项质量核查中机器可查部分 + 作者 2026-10-10 新增口径（段落 ≤80 字 / 三级标题）。"""
import re
from pathlib import Path

HERE = Path(__file__).parent
TEXT = (HERE / "weixin.md").read_text()
BODY = TEXT.split("---", 2)[-1]
def cjk(s):
    return len(re.findall(r"[\u4e00-\u9fff]", s))

# 原声 9 句逐字（来源 outline.md ## 作者原声槽，8 处）
# 槽 3b / 槽 4 各把 1 个「，」换成「。」用于分段（仅加标点，未增删任何字，已向作者声明）
SLOTS = [
    "当我第一次搭建一个一百多人的团队使用的向量知识库的时候，一点点存量文档放进去，就发现几百MB的postgresql数据库存储空间没有了。",
    "我仔细一估算，如果把全部文档放进去，按照默认的1536维设置，我的整个SSD剩余的几十个GB的空间可能都不够了。",
    "我会类比成是平均值的集中现象。",
    "其实仔细一思考，的确这个东西更多和点的个数关系更大，而维度只是一个表示层面的事情。",
    "人类的朴素直觉，对随机性的理解其实是一直以来都错的离谱。高维数据的结构和随机性，其实比朴素直觉的想象要规整的多。",
    "随机加上量化，看起来很笨的方法，其实在工程上有巨大的应用空间。学习出来的东西会吃掉很多随机的东西。",
    "很多工程上的奇思妙想，其实都有一个深刻的数学底层逻辑在那里支撑。数学之美，往往隐藏在那些看似复杂的工程应用公式的背后。",
    "其实理论和实践之间，往往还是隔着一道深沟。实际应用上，还是要看测试，根据自己的实际数据和场景来判定多少维度会是一个更好的平衡。",
    "做RAG的时候，你是否被选择多少维度困惑过？最后是怎样平衡准确度和存储占用之间的矛盾？",
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


print("[14] 原声逐字在场（9 个句子段 / 8 处，≥5 达标）")
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
chk(h2 >= 5 and h3 >= 2, f"H2={h2} 节、H3={h3} 个小标题（超 400 字段已拆）")

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
seg = re.sub(r"\$\$.*?\$\$", "", BODY, flags=re.S)
seg = re.sub(r"\$[^$]*\$", "", seg)
seg = re.sub(r"\((https?://[^)]+)\)", "()", seg)
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
chk("做RAG的时候，你是否被选择多少维度困惑过" in BODY, "文末互动问（维度困惑，作者原声）")
chk("点赞" in BODY and "收藏" in BODY, "点赞/收藏引导")
tags = re.findall(r"#\S+", BODY.strip().split("\n")[-1])
chk(3 <= len(tags) <= 5, f"话题标签 3-5 个（当前 {len(tags)}）")
chk("#数解AI" in BODY, "含 #数解AI")

print("[13] 爆款要素抽查")
chk("？" in TEXT.split("\n")[1], "标题疑问句")
chk("凭什么敢这么砍" in BODY, "驱动问题在开头亮明")
chk("回到开头的存储账" in BODY, "首尾闭环")

print("[1] 关键数字与文内口径一致")
for n in ["1536", "128", "600MB", "50MB", "5000", "640", "512", "576", "32768", "1/57",
          "1024", "1000 维", "2024", "2025"]:
    chk(n in BODY, f"数字在场 {n}")
chk("2026" in BODY, "年份口径在场（2026）")
chk("随机给下界，旋转给工程可行性依据，学习训练给现实优化求解路径" in BODY, "三层结论在场")
chk("Johnson-Lindenstrauss" in BODY, "术语 Johnson-Lindenstrauss 在场")
chk("Matryoshka" in BODY, "术语 Matryoshka 在场")

print()
print("PASS" if not fails else f"FAIL: {len(fails)} 项未过")
for f in fails:
    print("  ✗", f)
