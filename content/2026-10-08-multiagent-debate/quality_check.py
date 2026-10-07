#!/usr/bin/env python3
"""本篇 16 项质量核查中机器可查部分（第 4/9/10/11/12/14/15/16 项）。"""
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
TEXT = (HERE / "weixin.md").read_text()
BODY = TEXT.split("---", 2)[-1]

# 原声槽 6 处逐字（来源 outline.md ## 作者原声槽；槽 6 为文末互动问句，不计原声配额）
SLOTS = [
    '有一次我需要完成一个工作量很大的并行文献搜索任务，这个处理流程从结构上显然更适合多agent并发，我用kimi coding plan的agent swarm功能，直接开启20个并行的子代理，每个负责2～3个话题的搜索和深度分析工作，并让它们各自产生一个总结汇报，最后主agent接收这些浓缩的处理结果，再进一步收尾处理。原本感觉需要很久的处理任务，只用了大约很短的时间就全部完成了。',
    '还有一次实验，我并行派出去的子代理尝试从不同的角度对同一个问题做深层次分析，每个agent都耗费了很长时间做内部推理和总结，可惜最后返回的分析互相之间是有冲突的。外层的orchestrator代理收到它们的反馈之后，顿时陷入了迷茫，还是耗费了大量的token来二次验证和慢慢咀嚼，最后才得出了一个不那么靠谱的结论，真的是既浪费了时间，又浪费了token，换来了不必要的上下文污染导致的模型困惑度急剧上升，进而带来看起来的模型降智。',
    '我后来仔细思考了一下，发现这个冲突是必然会发生的。每个子代理只带着一部分自己的上下文输入，然后依据模型自身训练时候所熟悉的思维链轨迹、策略空间一路往前吐下一个token，它的每个动作背后都藏着对前面策略搜索方向的动态采样噪音，如果这些子代理不是同一个厂家训练的模型，本身策略空间可能就有差异，但是执行过程中，这些子代理互相之间，又没有做必要的协作和通信，等到最后产生完整的输出之后，才被强行拼凑到了一起做后续处理，产生冲突之后，结果看起来就是模型摆烂了。',
    '我觉得这笔账有时候其实非常难完全计算清楚：很多时候我们使用多agent完成任务的时候，会组合不同成本结构和推理能力的模型，把简单任务派发给廉价但是又足够使用的模型，总体成本反而可能是有节省的，并且时间上也得到了节约，前提是不要产生严重的打架冲突。反过来，如果是喜欢什么事情都上最前沿的模型，施加最高的思考强度，那么成本上肯定吃不消的。',
    '我现在使用的经验其实就这么几条，说白了都是让容易分发的任务快速派出去，复杂有深度的任务自己干，或者采用一个复杂一点的编排流程，将复杂的部分交给一个能力更强的模型来做收敛，同时仔细安排指令提示词，避免模型无脑接收输入的合成提示导致停摆。',
    '你用子代理完成的最值钱的一种用法是什么场景？最不划算的又是哪一种呢？说说你的看法。',
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
for s in SLOTS:
    seg = seg.replace(s, "")
long_hits = 0
for para in [p for p in seg.split("\n") if p.strip() and not p.strip().startswith("#")]:
    for sent in re.split(r"(?<=[。！？；])", para):
        s2 = re.sub(r"[*`>\-]", "", sent.strip())
        cjk = len(re.findall(r"[\u4e00-\u9fff]", s2))
        if cjk > 60:
            long_hits += 1
            print(f"   · {cjk} 汉字：{s2[:52]}…")
if long_hits == 0:
    print("  ✓ 无超 60 字 AI 句")

print("[4] 可视字数（去 URL/图片/表格语法，含尾部）")
vis = re.sub(r"\((https?://[^)]+)\)", "()", BODY)
vis = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", vis)
vis = re.sub(r"\[hot_articles 占位[^\]]*\]", "", vis)
vis = re.sub(r"[#*`>｜]", "", vis)
vis_cn = re.sub(r"\s", "", vis)
print(f"   可视字符总数（含标点）：{len(vis_cn)}")
chk(len(vis_cn) <= 2800, f"≤2800（10-07 作者口径：稍多没关系；当前 {len(vis_cn)}）")

print("[发布前待办] 占位符盘点（渲染前必须清零，当前阶段允许存在）")
for pat in ["【合集页URL待填】", "hot_articles 占位"]:
    print(f"   · {pat} × {BODY.count(pat)}")

print()
if fails:
    print(f"FAIL: {len(fails)} 项未过")
    sys.exit(1)
print("PASS: 机器可查项全部通过")
