#!/usr/bin/env python3
"""本篇 16 项质量核查中机器可查部分（第 8/10/11/12/14/15/16 项相关）。"""
import re
from pathlib import Path

HERE = Path(__file__).parent
TEXT = (HERE / "weixin.md").read_text()
BODY = TEXT.split("---", 2)[-1]

# 原声槽 7 处逐字（来源 outline.md ## 作者原声槽；槽 1 沿用 + 槽 2-7 已填）
SLOTS = [
    "这年头，反转可太多了。",
    "已经见到太多不经实践就盲目吸引眼球的自媒体瞎震惊后，我早就对这些数字免疫了，看到这些数字，第一印象就是想去查查看，背后是否有猫腻？",
    "对于高强度实践了AI coding一年多的我来说，想要达成某方面特别好的效果，还是要使用者付出很多精力做指令下发，和不断调整的。",
    "以今天AI产生代码的速度之高，一一查看早就不太现实了，但是基本的架构选择和技术决策，和AI简单聊两句让它给一个事实陈述，绝大部分情况下准确率还是相当高的。类似这种看起来非常傻的代码，并不能算作语言不行，更多应该看作是，指挥agent来生成代码的人，没有一个持续一致的心智模型来引导AI持续创造和维护所期望的代码行为边界。",
    "代码没有人读，但是设计决策和可维护性方面的高层规划，还是需要人来做的，因为LLM至今，在实践上还困在概率采样的世界里尝试做非常复杂的短期高精度模式匹配，超长程任务都还是一个巨大挑战，更不要说跨越几天，几周，甚至几个月的一致性考虑和约束，目前来看，都还有非常多的问题需要人类来维持。",
    "不得不说在自媒体持续轰炸之下，现在人们的注意力是越来越短了，然而好饭不怕晚，有些残酷的事实真相还是需要比较长的时间才能水落石出，或者甚至是跌宕起伏，难见终章。",
    "在大家都不看代码疯狂vibe coding的当下，你觉得这些性能方面的喧嚣和编程语言的争论是否结束了，还是鹿死谁手，尤未可知呢？",
]

fails = []


def chk(cond, msg):
    print(("  ✓ " if cond else "  ✗ ") + msg)
    if not cond:
        fails.append(msg)


print("[14] 原声槽逐字在场（7 处，≥5 达标）")
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
hits = re.findall(r".{10}拆.{10}", BODY_NOLINKTXT)
if not hits:
    chk(True, "无「拆」字")
for m in hits:
    print("   ·", m.replace("\n", " "))

print("[10] 超 60 字长句（原声句/参考资料/导航块豁免）")
seg = re.sub(r"\((https?://[^)]+)\)", "()", BODY)
seg = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", seg)
seg = re.sub(r"\$[^$]+\$", "MATH", seg)
seg = re.sub(r"(?s)\*\*参考资料与数字溯源\*\*.*", "", seg)
for s in SLOTS:
    seg = seg.replace(s, "")
long_hits = [s.strip() for s in re.split(r"[。！？\n]", seg) if len(s.strip()) > 60]
chk(not long_hits, f"无超 60 字 AI 句（命中 {len(long_hits)}）")
for s in long_hits:
    print("   ·", s[:90])

print("[8] 图片路径检查")
chk("images/" not in BODY, "无 images/ 前缀")
refs = set(re.findall(r"\]\(([^)]+\.png)\)", BODY))
missing = sorted(r for r in refs if not (HERE / r).exists())
chk(not missing, f"引用的图都存在（缺 {missing}）")
# 孤儿图守卫：目录内除封面/底图外的 png 必须都被正文引用
files = {p.name for p in HERE.glob("*.png")
         if not p.name.startswith("00-cover")}
chk(not (files - refs), f"无孤儿图（正文 {len(refs)} 张，目录 {len(files)} 张）")
chk(len(refs) >= 6, f"正文配图不少于 6 张（当前 {len(refs)}）")

print("[5/16] 结尾互动与转发设计")
chk("留言区聊聊" in BODY, "文末 30 秒可答互动问（4.4 还是 150）")
chk("点个赞" in BODY and "收藏" in BODY, "点赞/收藏引导")
tags = re.findall(r"#\S+", BODY.split("参考资料")[-1])
chk(3 <= len(tags) <= 5, f"话题标签 3-5 个（当前 {len(tags)}）")
chk("#数解AI" in BODY, "含 #数解AI")

print("[13] 爆款要素抽查")
chk("？\n" in TEXT or "？\r" in TEXT, "标题疑问句")
chk("150 倍和 4.4 倍，不是同一轮成绩" in BODY, "驱动问题在开头亮明")
chk("回到开头那句判断" in BODY, "首尾闭环（结尾回扣开头判断）")

print("[1] 关键数字与文内口径一致")
chk("36,260" in BODY and "241" in BODY and "722" in BODY and "3,860" in BODY, "房间页四数在场")
chk("4.4 倍" in BODY and "大约 11 倍" in BODY, "初版 4.4 / 规划 11 在场")
chk("398" not in BODY, "未重数的 398 未写死")
chk("第三方" in BODY, "第三方口径已标明")
chk("Good old C is now in the lead" in BODY, "C 反超原话在场")

print()
print("PASS" if not fails else f"FAIL: {len(fails)} 项未过")
for f in fails:
    print("  ✗", f)
