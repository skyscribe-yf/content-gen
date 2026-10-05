#!/usr/bin/env python3
"""本篇 16 项质量核查中机器可查部分（第 4/9/10/11/12/14/15/16 项）。"""
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
TEXT = (HERE / "weixin.md").read_text()
BODY = TEXT.split("---", 2)[-1]

# 原声槽 8 处逐字（来源 outline.md ## 作者原声槽）
SLOTS = [
    '我用opencode改一个自己项目的代码，它经常选择性忽略我写在docs目录里面的一些关键要求，自作主张按照自己的理解去执行，导致最后出来的结果完全不符合预期需要后续再来纠偏。',
    '其实我们自己用多了就会知道，尽管agent的能力一直在飞速进化，它一直还是只有一个“金鱼记忆”，每次推理开始的时候，它都依赖于输入给他的前缀提示。很多工程上照搬人类记忆的做法，尝试为它施加大记忆恢复术的方法，都会遇到各种各样的后遗症。',
    '自己做RAG类似的应用的时候，就发现这方面的问题非常突出，相似度捞回来的东西经常遗漏最关键的一部分，即便是加上了reranker机制，还是没法做到完全可靠。',
    '关于最深层次的理解，不是浮于表面形式的那种相似性，其实目前的embedding机制天生还是有很大缺陷，距离非常完美的程度还有很大差距，所以没有办法把需要的东西都捞回来。',
    '这个例子实在是太过于典型了，众所周知目前agent的进化速度飞快，用来写代码做项目，每次产生大量的思考过程输出和工具调用，没有人能一直盯着看的，所以有时候混入的一些猫腻，只有事后才发现，但是即使这时候你想去强迫它更正，才发现它完全不太听你的指挥，这些问题都不是简单一句“指令遵循能力不好”可以带过去的。',
    'zcode的记忆机制其实挺有趣的，很多时候它可以自动完成一些机械重复的工作，极大提高缓存命中率和token效率，然而最近的上传代码事件，还是引起了社区很大的反感，毕竟隐私的东西，有几个人会不在意呢？不过话说回来，它按照项目文件夹保留的内部记忆，很多时候还是非常有用的，有点hermes agent的那个味道了。',
    '其实模型还是非常善于捕捉文本表面的相似性，但是有时候有些专业术语或者领域黑话方面的东西，召回的内容让领域专家一看就明白，但是模型自己却会陷入极大的困惑中不能自拔，很多幻觉就因此爆发了。',
    '你被各种agent的记忆机制坑过吗？你是如何发现这类问题，又是怎么绕过去的？如果你自己设计agent,记忆机制你会怎么选？',
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
seg = re.sub(r"^\|.*$", "", seg, flags=re.M)
seg = re.sub(r"(?m)^\d+\. .*$", "", seg)
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
chk("待补链接" not in BODY, "无「待补链接」残留")
chk("images/" not in BODY, "图片无 images/ 前缀")
chk(BODY.count("mp.weixin.qq.com") >= 5, "含多个微信真实链接")

print("[16] 转发/点赞欲抽查")
chk("如果只转一句话给同事" in BODY, "文末一句话总结卡")
chk("你被各种agent的记忆机制坑过吗" in BODY, "文末 30 秒可答互动问")
chk("点个赞" in BODY and "收藏" in BODY, "点赞/收藏引导")
chk("#数解AI" in BODY and "#Agent记忆" in BODY, "话题标签含关键词与 #数解AI")
tags = re.findall(r"#\S+", BODY.split("参考资料")[-1])
chk(3 <= len(tags) <= 5, f"话题标签 3-5 个（当前 {len(tags)}）")

print("[4] 配图引用存在性")
for m in re.finditer(r"!\[[^\]]*\]\(([^)]+)\)", BODY):
    p = HERE / m.group(1)
    chk(p.exists(), f"图片存在：{m.group(1)}")

print("[篇幅] 全篇 CJK 计数")
cjk = len(re.findall(r"[\u4e00-\u9fff]", BODY))
chk(cjk <= 2500, f"全篇 CJK {cjk} ≤ 2500")

print()
if fails:
    print(f"FAIL ×{len(fails)}")
    sys.exit(1)
print("ALL PASS（机器可查部分）")
