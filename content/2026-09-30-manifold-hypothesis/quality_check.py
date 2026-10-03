#!/usr/bin/env python3
"""本篇 16 项质量核查中机器可查部分（第 9/10/11/12/14/15/16 项相关）。"""
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
TEXT = (HERE / "weixin.md").read_text()
BODY = TEXT.split("---", 2)[-1]

# 原声槽 7 处（逐字，来源 outline.md ## 作者原声槽）
SLOTS = [
    "第一次看到这个结论，我有点不敢相信自己的眼睛，这么复杂的神经网络，学到的内在维度怎么可能只有不到50呢？",
    "我第一次看VAE模型的编码器可以通过主成分分析，压缩显示在一个二维平面上，从而清晰地看到识别出来的数字各自处于什么区域，以及他们模糊的边界的时候，觉得特别神奇，那些抽象而又难以理解的东西，居然可以在二维空间里具象化地展示出来。",
    "其实有时候理论方向的论文往往充满了矛盾，但是可能是迫于各方面的压力不得不随随便便就发出来，早已是司空见惯的了。因为有时候一些深刻的洞见，就是稀少而珍贵的，真正能经历时间考验的想法，还是需要一些天时地利人和等各方面的因素都满足才行的。",
    "我觉得现在的AI表现的太过于强大，甚至会让我们不由得忘掉了机器学习/数据科学那些最基本的原理：一切网络所能习得的结构，本质上都是来自于对数据的拟合，模型之所以可以学习出这样的结构来，很多时候其实是人们交给它的数据本身具备类似的结构，或者起码看起来具有类似的结构（在损失函数所定义的误差最小化意义上看如此）。",
    "一个上亿甚至数十亿参数规模的模型，在拿到自己的领域数据中做几十万参数的微调，就真能将特定评测基准上的表现大幅拉高两位数的百分点，这是BERT时代我已经在很多论文里面看到的数据。如今基础模型的参数容量更大，需要的参数量占比反而更小，这是各种实验反复证实了有效的方法，并不是纯理论上的构想。",
    "你觉得流形的说法是否是AI钻了空子，还是说这个世界本质上就是如此？",
    "其实有时候也不能说古早时期的哲学家就真的用寓言的方式提前揭示了这时间一切的秘密，科学的发展一直都是螺旋上升的过程，今天的人们对世界的认识和发掘比古人要深刻的多，只是很多时候认识的越深刻，被推翻的那些似是而非的直觉谬误就越多，这是一个很自然的探索、发现、认识、总结的过程。",
]

fails = []


def chk(cond, msg):
    print(("  ✓ " if cond else "  ✗ ") + msg)
    if not cond:
        fails.append(msg)


print("[14] 原声槽逐字在场")
for i, s in enumerate(SLOTS, 1):
    chk(s in BODY, f"槽 {i}")

print("[11] 正文禁词 / 工作流元词（链接标题豁免）")
BODY_NOLINKTXT = re.sub(r"\[([^\]]*)\]\([^)]*\)", "", BODY)  # 去掉所有链接的显示文字
for w in ["钩子", "伏笔", "说人话就是", "上一篇", "在上一篇", "篇N", "拆给你看"]:
    chk(w not in BODY_NOLINKTXT, f"无「{w}」")

print("[15] AI 腔扫描")
ai_words = ["值得注意的是", "让我们来", "总而言之", "综上所述", "不难发现", "不难看出",
            "需要指出的是", "深入探讨", "全面分析", "由上可知", "今天我们来聊聊",
            "随着AI的发展", "随着 AI 的发展", "表现优异", "具有显著优势", "综合来看"]
for w in ai_words:
    chk(w not in BODY, f"无「{w}」")

print("[12] 「拆」字逐处判断（链接标题豁免）")
for m in re.finditer(r".{10}拆.{10}", BODY_NOLINKTXT):
    print("   ·", m.group(0).replace("\n", " "))

print("[10] 超 60 字长句（原声句/参考文献/导航/热门块豁免）")
seg = re.sub(r"\((https?://[^)]+)\)", "()", BODY)
seg = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", seg)
seg = re.sub(r"\$[^$]+\$", "MATH", seg)
seg = re.sub(r"^\|.*$", "", seg, flags=re.M)
# 豁免：编号参考文献行、系列导航行、热门文章块（表头到参考文献之间）、纯链接行
seg = re.sub(r"(?m)^\d+\. .*$", "", seg)
seg = re.sub(r"(?m)^📖 .*$", "", seg)
seg = re.sub(r"(?s)🔥 \*\*热门文章\*\*：.*?(?=\*\*参考资料)", "", seg)
seg = re.sub(r"(?m)^\[.*\]\(.*\)\s*$", "", seg)
long_hits = []
for sent in re.split(r"[。？！？\?]", seg):
    s = sent.strip()
    if not s or any(s[:24] in t for t in SLOTS):
        continue
    n = len(re.sub(r"[（(【\[][^）)】\]]*", "", s))
    n = len(re.sub(r"[\s*]", "", s.replace("MATH", "")))  # 口径：汉字+标点，不含空白/**/公式
    if n > 60:
        long_hits.append((n, s))
for n, s in long_hits:
    print(f"   ✗ {n} 字：{s[:50]}…")
chk(not long_hits, f"无 AI 句超 60 字（命中 {len(long_hits)}）")

print("[4] 配图核查")
imgs = re.findall(r"!\[[^\]]*\]\(([^)]+)\)", BODY)
chk(len(imgs) >= 4, f"正文图 {len(imgs)} 张 ≥4")
for im in imgs:
    chk((HERE / im).exists(), f"存在 {im}")
    chk(not im.startswith("images/"), f"路径无 images/ 前缀：{im}")

print("[16] 转发/点赞要素")
chk("如果只转一句话" in BODY, "一句话总结卡")
chk("评论区" in BODY, "文末可回答问题")
chk(("点赞" in BODY or "点个赞" in BODY) and "关注" in BODY, "点赞/关注引导")

print("[篇幅]")
body_v = re.sub(r"\((https?://[^)]+)\)", "", BODY)
body_v = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", body_v)
body_v = re.sub(r"\s", "", body_v)
print(f"   正文可视字符（含尾部）≈ {len(body_v)}")

print("[标签]")
tag_lines = [l for l in BODY.splitlines() if re.fullmatch(r"#\S+( #\S+)+", l.strip())]
tags = tag_lines[-1].split() if tag_lines else []
chk(3 <= len(tags) <= 5, f"话题标签 {len(tags)} 个：{tags}")
chk("#数解AI" in tags, "含 #数解AI")

print()
print("FAIL" if fails else "ALL PASS (machine checks)")
sys.exit(1 if fails else 0)
