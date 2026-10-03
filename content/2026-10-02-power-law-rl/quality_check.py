#!/usr/bin/env python3
"""本篇 16 项质量核查中机器可查部分（第 9/10/11/12/14/15/16 项相关）。"""
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
TEXT = (HERE / "weixin.md").read_text()
BODY = TEXT.split("---", 2)[-1]

# 原声槽 7 处逐字（槽 3「我向→我想」明显错别字修正版；来源 outline.md ## 作者原声槽）
SLOTS = [
    "因为在学校和各种教科书、科普材料里面见到太多高斯分布的内容，我一直以为被叫做自然分布的高斯分布是这个物理世界里面最普遍的规律，但是显示这个世界并不是这样的。大量的财经新闻和其他专业的描述都让我隐隐约约意识到，其实这个世界充满了长尾，高斯分布那个随指数衰减极快的良好分布，还是太过于理想化了，不能描述更普遍而又复杂的现象。",
    "最典型的例子就是世界上的收入差距，大量的普通人处于低收入的长尾上，以至于如果你拿财富500排行榜去算平均，就会得到一个一段离谱的结果，相信所有人都被这种身边统计学蒙蔽过自己的直觉。",
    "这个规模之小，的确令人感到诧异。然而这真的能成立吗？我想最后还要看事实的检验。",
    "其实这个研究本身也还不能算是盖棺定论，如果据此就说是RL毫无用处，可能也太过武断了一些，因为不经过RL手法中做复杂的后训练，谁也不知道怎么样让分布变窄，以及变到何种程度。",
    "这其实有点像人类专家所经历的狭窄领域的反复实践和训练，你在一个细分的领域上面把一系列看起来极其复杂的技能都快速内化了之后，那些通用领域的技能，反而变得生疏了起来。",
    "听起来似乎有点离谱，但是没办法，涨分和天花板，就是同一把剪刀的两个不同的侧面。",
    "其实社区里，也有大量对近期的前沿coding模型其他方面能力退化的抱怨和不满。你是否认可这种取舍和权衡：用少得几分的写代码能力，换取模型写文章写的更好？",
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
chk("appmsgalbum" not in BODY or "mp.weixin.qq.com" in BODY, "系列导航为微信 URL 或箭头链")
chk(BODY.count("mp.weixin.qq.com") >= 5, "含多个微信真实链接")
chk("待发布" not in BODY, "无「待发布」残留")
chk("images/" not in BODY, "图片无 images/ 前缀")

print("[16] 转发/点赞欲抽查")
chk("如果只转一句话给同事" in BODY, "文末一句话总结卡")
chk("评论区聊聊" in BODY, "文末 30 秒可答互动问")
chk(re.search(r"#幂律分布", BODY) and "#数解AI" in BODY, "话题标签含关键词与 #数解AI")
tags = re.findall(r"#\S+", BODY.split("参考资料")[-1])
chk(3 <= len(tags) <= 5, f"话题标签 3-5 个（当前 {len(tags)}）")

print("[配图] 图片引用存在性")
for m in re.finditer(r"!\[[^\]]*\]\(([^)]+)\)", BODY):
    p = HERE / m.group(1)
    chk(p.exists(), f"图片存在：{m.group(1)}")

print()
if fails:
    print(f"FAIL ×{len(fails)}")
    sys.exit(1)
print("ALL PASS（机器可查部分）")
