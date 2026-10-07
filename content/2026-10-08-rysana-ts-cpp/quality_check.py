#!/usr/bin/env python3
"""本篇 16 项质量核查中机器可查部分（第 4/9/10/11/12/14/15/16 项）。"""
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
TEXT = (HERE / "weixin.md").read_text()
BODY = TEXT.split("---", 2)[-1]
BODY_LINKTXT = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", BODY)  # 链接还原为可见文字（生稿逐字以可见文本为准）

# 原声槽 9 处逐字（来源 outline.md ## 作者原声槽）
SLOTS = [
    '第一次看到这个项目，还是觉得有点终于有人愿意干这种苦力活了，以今天AI模型的能力，多久可以干完呢？原来Anders团队做的架构选择终于是在AI时代被推翻了吗？',
    '其实重写导致项目整体翻车，工作量被严重低估，问题难度在项目临近正式交付阶段，随着测试推进被急速放大，最终导致项目难产的例子可是屡见不鲜，可以说是软件工程的经典难题了，所谓Fred Brooks所说的焦油坑就是描述这种问题的，所以我猜想这也是微软宁愿选择移植也不重写的基本逻辑。',
    '其实几个月前的最前沿AI，拿来写最复杂的项目也是屡屡碰壁的，改了东边漏了西边，按下葫芦起了瓢的事情可是屡见不鲜，更不要说是大模型早期常见的死循环现象和严重的reward hacking现象了。',
    '不知道这个费用是否是纯API费用，还是多个账号的订阅？反正是氪金的装备还是要有的，换算成程序员工资的话，也没有表面看起来那么多了，关键是这个几天时间有些太夸张了，甚至这个像素级的复刻才是当前AI模型恐怖实力的最直接表征！',
    '随着agentic coding实践的加速落地，我估计很多人都会发现，本地跑工具验证，或者其他脚本运行的时间，很多时候都已经大大超出了LLM推理和网络延迟的部分，我个人的比例甚至是1：3以上了，所以这些被调用的小工具，编译器检查，测试case验证等操作如果能被提速，是可以降低整体的等待时间的。当然如果你的场景都是跑一些玩具项目，从来不做验证，只靠一把梭哈，那么收益就很小了。',
    '后面两个数字还是让我情不自禁地换算了一下人民币等值是多少钱，居然超过一百万了！试想又有多少软件项目自身的价值能够超过一百万？',
    '整体上我觉得还是很魔幻，尽管后遗症也是客观存在的，还是需要多一些乐观积极的态度，采用胡适之先生提倡的思维，加上一些小心的求证就好了。',
    '一度编程语言作为软件架构最大决策的这个基本逻辑，已经被改写了',
    '不是说编程语言这个架构决策变得完全无足轻重了，而是它考虑的要素和约束完全不同了。',
    '如果能在token管够的情况下，改写你手头的复杂项目，你希望选择哪门编程语言，主要考虑是什么？',
]

fails = []


def chk(cond, msg):
    print(("  ✓ " if cond else "  ✗ ") + msg)
    if not cond:
        fails.append(msg)


print("[14] 原声槽逐字在场（链接按其可见文字计）")
for i, s in enumerate(SLOTS, 1):
    chk(s in BODY_LINKTXT, f"槽 {i}")

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

print("[10] 超 60 字长句（原声句/参考文献/导航/热门块/英文引语豁免）")
seg = re.sub(r"\((https?://[^)]+)\)", "()", BODY_LINKTXT)
seg = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", seg)
seg = re.sub(r"^\|.*$", "", seg, flags=re.M)
seg = re.sub(r"(?m)^\d+\. .*$", "", seg)
seg = re.sub(r"(?s)🔥 \*\*热门文章\*\*：.*?(?=\*\*参考资料)", "", seg)
seg = re.sub(r"(?m)^\[.*\]\(.*\)\s*$", "", seg)
seg = re.sub(r"(?m)^>.*$", "", seg)  # 英文推文引语
for s in SLOTS:
    seg = seg.replace(s, "")
for sent in re.split(r"[。！？\n]", seg):
    sent = sent.strip()
    if len(sent) > 60:
        print("   ·", sent[:90])

print("[9] 尾部链接检查")
chk("待发布" not in BODY, "无「待发布」残留")
chk("待补链接" not in BODY, "无「待补链接」残留")
chk("images/" not in BODY, "图片无 images/ 前缀")
chk(BODY.count("mp.weixin.qq.com") >= 5, "含多个微信真实链接")

print("[16] 转发/点赞欲抽查")
chk("如果只转一句话给同事" in BODY, "文末一句话总结卡")
chk("你希望选择哪门编程语言" in BODY, "文末 30 秒可答互动问")
chk("点个赞" in BODY and "收藏" in BODY, "点赞/收藏引导")
chk("#数解AI" in BODY and "#TypeScript" in BODY, "话题标签含关键词与 #数解AI")
tags = re.findall(r"#\S+", BODY.split("参考资料")[-1])
chk(3 <= len(tags) <= 5, f"话题标签 3-5 个（当前 {len(tags)}）")

print("[4] 配图引用存在性（生成前允许未就绪，生成后必须全过）")
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
