#!/usr/bin/env python3
"""本篇质量核查中机器可查部分（第 4/10/11/12/14/15/16 项 + 恢复期 B.3/B.5）。"""
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
TEXT = (HERE / "weixin.md").read_text()
BODY = TEXT.split("---", 2)[-1]

# 原声槽逐字（来源 outline.md ## 作者原声槽；槽 9 为文末互动问句）
SLOTS = [
    '后面发现任务迟迟没有完成，仔细查看agent执行轨迹才发现这个问题。',
    '很多时候，我不得不提醒自己这个有点反常的事实：对于没有实际产生任何结果的工具调用，agent不得不自己给模型创造一条实际上不存在的错误，阅读和排查agent运行轨迹的时候，不需要对这种行为大惊小怪。',
    '其实不确定性的东西交给模型作为输入，更容易让模型对不确定的输入产生困惑，进而推高幻觉，导致要么任务执行失败，要么后续需要花费更多轮次的反复验证来找补。',
    '其实在agent没有进化出来更好的机制之前，我还是更信赖物理层面的隔离那种看起来很土鳖的方案，浪费一点磁盘空间，施加一些操作系统层面的文件锁来避免并发踩踏，但是主观上我还是希望agent的设计可以更好地处理这种情况，降低用户的心智负担。',
    '其实我觉得这种取舍并没有一种放之四海皆准的套路，还是要看具体任务的场景，毕竟这是传统数据库设计也没有取得共识的地方，可靠性、可用性在分布式设计面前本身就必须要权衡。如果模型调用非常便宜，时间成本也不高，那么事后探测重试，也未尝不可。反之，就需要更安全的方案了。',
    '有时候两个子agent都觉得自己需要做同一件事，进而改动了同一份文件，最后到了需要合并的时候，才发现产生了冲突，此时虽然两个独立任务都认为自己在做正确的事，合在一起就不尽然了。',
    '这个边界的界定很多时候就比较麻烦了，模型自己很多时候并没有一个一致性很高的心智 - 本质上它完全是无状态的大金鱼，agent工具的作者自然是不可能知道除非你使用的agent不是一个通用的工具而是一个领域特化的app, 用户和业务方显然是知道的，但是他们可能根本就没有直接和agent打交道。',
    'durable的名字看起来很抽象，其实它就是一个账本，里面可靠地记录着所有的任务情况，具有良好的结构信息，可以让agent随时来翻阅决定如何调度各种工具以及如何与底层的LLM模型通信将目标持续往前推进。',
    '你觉得这个Durable机制的设计能解决你平时遇到的痛点吗',
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
for w in ["钩子", "伏笔", "说人话就是", "上一篇", "在上一篇", "篇N", "拆给你看", "值得注意"]:
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

print("[4] 字数（口径：CJK 汉字数，对齐 10-05 篇 outline 的「全篇 CJK ≤2500」）")
vis = re.sub(r"\((https?://[^)]+)\)", "()", BODY)
vis = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", vis)
vis = re.sub(r"[#*`>｜]", "", vis)
vis_cn = re.sub(r"\s", "", vis)
cjk_total = len(re.findall(r"[\u4e00-\u9fff]", BODY))
print(f"   CJK 汉字总数={cjk_total}（含尾部） / 可视字符={len(vis_cn)}")
chk(cjk_total <= 6500, f"≤6500 汉字（作者 2026-10-09 口径「长一点没有问题的」，覆盖 B.3 的 5k 上限；当前 {cjk_total}）")

print("[B.5] 开头 100 字白盒")
head = re.sub(r"[#*`>]", "", BODY)[:100]
chk(not re.search(r"上篇|上一篇|篇\d|在上一篇", head), f"开头 100 字无系列导航：{head[:40]}…")

print("[16-B4] 文末互动杠杆")
tail = BODY[-2200:]
chk("点个赞" in tail and "关注「数解AI」" in tail, "文末有点赞/关注引导")
chk(SLOTS[8] in tail, "文末有可回答问题（槽 9）")
chk("**一句话：" in BODY, "文末有一句话总结卡（分享借口）")

print("[7] 图片路径（同级、无 images/ 前缀）")
for m in re.finditer(r"!\[[^\]]*\]\(([^)]+)\)", BODY):
    chk("/" not in m.group(1), f"图片同级：{m.group(1)}")

print()
if fails:
    print(f"FAIL: {len(fails)} 项未过")
    sys.exit(1)
print("PASS: 机器可查项全部通过")
