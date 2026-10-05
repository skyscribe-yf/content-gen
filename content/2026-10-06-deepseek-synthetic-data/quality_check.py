#!/usr/bin/env python3
"""本篇 16 项质量核查中机器可查部分（第 9/10/11/12/14/15/16 项相关）。"""
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
TEXT = (HERE / "weixin.md").read_text()
BODY = TEXT.split("---", 2)[-1]

# 原声槽 7 处逐字（含错别字修正版；来源 outline.md ## 作者原声槽）
SLOTS = [
    '其实早在大语言模型爆发前的深度学习时代，计算机视觉领域就大量引入了合成数据来提高模型预测任务的准确度。所以这样的能力被“迁移”到自然语言处理上，我觉得是非常顺理成章的。只是因为语言本身的灵活性看起来要高很多，所以这样做是否真的有效，也是我非常关注的一个问题。',
    '前几年阅读大量论文的时候，我就发现很多研究人员会反复强调数据处理管道操作的重要性，尤其是预训练阶段的语料精选处理和清洗，会严重影响训练出来的模型的基础能力，甚至这些数据如何预处理和筛选，不同比例的数据如何混合搭配，一直是各大模型厂商的不传之秘。到了后训练阶段，居然可以更粗糙地自己造，第一次看到的时候，我还是略微感到吃惊的。',
    '看到这个论断，我觉得毫无意外，毕竟现在基于概率的模型需要学习的就是一个看不见的概率分布，本质上是使用KL散度来衡量学习目标和看不见的真实分布的差距，并不断训练让二者尽可能地接近乃至重合，这一点前面文章已经写过了（[《KL散度：为什么整个AI共用一把尺子？》](https://mp.weixin.qq.com/s/G1PUOuwxURoo1Dp1pDfQMg)）。',
    '这个思路其实蛮巧妙的，因为深度学习早期发展所积累的经验，已经可以将判别模型的准确度推高到了一个很多方面远远超过人类专家水平的高度，那么其误差也是极小的。',
    '其实实验一开始，因为选择的题目过于简单，DeepSeek v4.1 flash总是能达到100％准确，直到我增加了难度之后，才把错误的答案给逼了出来！所以即便是有相当难度的挑战，重复跑上100次采样，这个通过率还是非常让人惊艳的。',
    '就如前一篇文章（[《问 AI 100 遍：100 种说法，为什么只算 1 种答案？》](https://mp.weixin.qq.com/s/c_Bi9arqz2K29BjCzmaIYQ)）说过的，这个语义上高度集中的现象其实严重制约了大模型的创造力。如果这样的合成数据太多，会将模型的表达能力，限制在一个很狭窄的通道上，导致它生成千篇一律、极其平庸无味的产物。这个现象，相信大部分人都已经体会到了。',
    '你有没有发现，让AI当裁判来判定的时候，他们的表现会非常平庸，甚至是千篇一律，错过真正有趣的结果？你是怎么克服这种问题的？',
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
chk("你是怎么克服这种问题的？" in BODY, "文末 30 秒可答互动问")
chk("点个赞" in BODY and "收藏" in BODY, "点赞/收藏引导")
chk(re.search(r"#合成数据", BODY) and "#数解AI" in BODY, "话题标签含关键词与 #数解AI")
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
