#!/usr/bin/env python3
"""本篇 16 项质量核查中机器可查部分（第 9/10/11/12/14/15/16 项相关）。"""
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
TEXT = (HERE / "weixin.md").read_text()
BODY = TEXT.split("---", 2)[-1]

# 原声槽 8 处逐字（含两处明显错别字修正版；来源 outline.md ## 作者原声槽）
SLOTS = [
    '一开始做这个小实验，我还以为能看到很多个完全相同的结果，没想到其实非常微观层面的答案，还是保持了明显的多样性的，只是当我从更高的语义层面去审视的时候，才发现了真正的猫腻。',
    '其实以前我在看论文扫描到类似于token熵这样的名词的时候，并没有特别深入去思考这个名词背后意味着什么，也没有对它怎么影响模型的表达能力有特别直观的印象。直到具体做一些上手的小实验，才得到了更深入的一些体会。',
    '看起来不确定性更高的路径，居然能收敛到一个更小的一组答案上？一开始我是不太愿意相信的，不过相比于信任人类那不靠谱的直觉，我更愿意看看实际的数据跑出来是什么样的，毕竟概率论的世界里，人类的直觉是最不靠谱的存在。',
    '我觉得这就像工作或者生活里面，你身边那些喜欢扯车轱辘话的让你觉得有些讨厌的人们，看起来花里胡哨地堆砌了很多新名词，其实本质上就是对一件肤浅的事情不停地变换说法，让人觉得毫无深度。',
    '本文正在写着这个，结果用模型做裁判之后，它就开始来犯浑了。这个结果其实并没有看起来那么好笑，反而非常值得我们每个人警惕，很多似是而非的结论其实是大模型自己被语言的字面意思欺骗了！',
    '单纯从结果来看，就如我前一篇[《RL 越训越准，为什么反而越训越笨？》](https://mp.weixin.qq.com/s/o7C50Fqhs9IZiQryKhmc9g)所说的，RL更像是从概率上把一些可能性给抽走了，所以涨分数和能力天花板，本来就是同一把剪刀的两面。',
    '我原本以为它起码可以凑出来两三条，没想到它压根就没有一次能凑满3条不同的路径。',
    '我想这也是很强的大模型，依然需要和它一起工作的人有足够好的提问能力和批判性思维，才能发挥出来更大效用的底层逻辑，你认可这个判断吗？',
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
BODY_NOLINKTXT = re.sub(r"\[([^\]]*)\]\([^)]*\)", "", BODY)
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
seg = re.sub(r"(?m)^\d+\. .*$", "", seg)
seg = re.sub(r"(?m)^📖 .*$", "", seg)
seg = re.sub(r"(?s)🔥 \*\*热门文章\*\*：.*?(?=\*\*参考资料)", "", seg)
seg = re.sub(r"(?m)^\[.*\]\(.*\)\s*$", "", seg)
for s in SLOTS:
    seg = seg.replace(s, "")
for sent in re.split(r"[。！？\n]", seg):
    sent = sent.strip()
    if len(sent) > 60:
        print("   ·", sent[:80])

print("[9] 尾部链接检查")
chk("待发布" not in BODY, "无「待发布」残留")
chk("images/" not in BODY, "图片无 images/ 前缀")
chk(BODY.count("mp.weixin.qq.com") >= 5, "含多个微信真实链接")

print("[16] 转发/点赞欲抽查")
chk("如果只转一句话给同事" in BODY, "文末一句话总结卡")
chk("你认可这个判断吗" in BODY, "文末 30 秒可答互动问")
chk("点个赞" in BODY and "收藏" in BODY, "点赞/收藏引导")
chk(re.search(r"#语义熵", BODY) and "#数解AI" in BODY, "话题标签含关键词与 #数解AI")
tags = re.findall(r"#\S+", BODY.split("参考资料")[-1])
chk(3 <= len(tags) <= 5, f"话题标签 3-5 个（当前 {len(tags)}）")

print("[4] 配图引用存在性")
for m in re.finditer(r"!\[[^\]]*\]\(([^)]+)\)", BODY):
    p = HERE / m.group(1)
    chk(p.exists(), f"图片存在：{m.group(1)}")

print()
if fails:
    print(f"FAIL ×{len(fails)}")
    sys.exit(1)
print("ALL PASS（机器可查部分）")
