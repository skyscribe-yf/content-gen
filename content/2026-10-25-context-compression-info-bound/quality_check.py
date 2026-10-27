#!/usr/bin/env python3
"""本篇 16 项质量核查中机器可查部分 + 作者口径（段落 ≤80 字 / 三级标题 / AI 句 ≤60 字）。
适配自 content/2026-10-21-pi-codemode-mcp/quality_check.py（原声/数字/爆项按本篇重列）。"""
import re
import sys
import difflib
from pathlib import Path

HERE = Path(__file__).parent
TEXT = (HERE / "weixin.md").read_text()
BODY = TEXT.split("---", 2)[-1]

# --published：已发布文章以后台正文为准，跳过成稿期门禁（原声/段落/长句/篇幅）。
PUBLISHED = "--published" in sys.argv

def cjk(s):
    return len(re.findall(r"[\u4e00-\u9fff]", s))

def flat(s):
    return re.sub(r"\s+", "", s)

# 尾部边界：热门文章 / 合集导航 / 参考资料 / 话题标签行之后不算正文
# （2026-10-24：作者在后台删掉了「📖 合集导航」行，不能再以它为唯一边界）。
TAIL_RE = re.compile(r"\n(?=(?:🔥\s*\*\*热门文章|📖|\*\*参考资料|#[^\s#]))")
TAIL_MARK = TAIL_RE.search(BODY)
MAIN = BODY[:TAIL_MARK.start()] if TAIL_MARK else BODY

def slot_score(slot, text):
    """归一化后覆盖率：容忍 web 改写的小幅增删与标点替换。"""
    s, t = flat(slot), flat(text)
    if not s:
        return 0.0
    if s in t:
        return 1.0
    sm = difflib.SequenceMatcher(a=s, b=t, autojunk=False)
    return sum(b.size for b in sm.get_matching_blocks()) / len(s)

def is_tail_block(par):
    s = par.strip()
    return (not s) or s.startswith(("#", "!", "[", "🔥", "📖")) or bool(re.match(r"^\d+\.\s", s))

def visible(par):
    """微信端可见文字：先删整张图片（含 alt），再把链接还原成链接文字。"""
    s = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", par)
    return re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", s)

def n_sent(par):
    return len([x for x in re.split(r"[。！？；!?;]", visible(par)) if cjk(x) >= 4])

# 原声 6 处逐字（来源 voices.md，2026-10-24 作者逐条手动输入）
SLOTS = [
    "我本来以为还能找到一些压缩后翻车的蛛丝马迹的，毕竟这个问题前两年可是相当严重和普遍的，尽管这一年来模型侧的进步挺多的。",
    "其实回头看我之前的数据，那时候的工作任务更加复杂，很多并行的任务在推进，一旦压缩就会变得支离破碎，难以继续。而后续的干净，只不过是我交给agent的任务更加干净清爽了许多罢了。",
    "看到压缩后的上下文窗口瞬间回到了5%，我一开始还有点窃喜，后来发现它忘记了太多的东西，很多事情都需要重新试探和人工纠偏。",
    "这个案例真正让我明白的是，压缩并没有什么魔法，有很多细节对后续步骤很重要的时候，如何学会判断哪些东西不应该丢才是更加关键的。",
    "大概是某一次复杂任务，压缩之后的反复纠偏让我感到了深深的厌烦，所以后续我不自然地改变了自己和agent交互的习惯，在我的项目提示词里面写好了这条规矩：重要的状态一定要先落入磁盘，压缩的东西丢失了细节，回头到文件里面找一下就简单了。",
    "下次看到有人无脑宣传agent加上了记忆就可以克服大模型本身的上下文窗口限制，我想你得反问一句：信息量真的能等于或者超过原始信息吗？因为这个问题，本质上是由信息论来决定的。",
]

fails = []

FLAT = re.sub(r"\s+", "", BODY)
SLOT_FLAT = [re.sub(r"\s+", "", s) for s in SLOTS]


def is_voice(par: str) -> bool:
    p = flat(par)
    if not p:
        return False
    return any(p in flat(s) or flat(s) in p or slot_score(s, p) >= 0.85 for s in SLOTS)


def chk(cond, msg):
    if not cond:
        fails.append(msg)


if PUBLISHED:
    print("· --published：跳过原声 / 段落 / 长句门禁")
else:
    for i, s in enumerate(SLOTS, 1):
        chk(slot_score(s, flat(BODY)) >= 0.9, f"原声槽 {i}（相似度 {slot_score(s, flat(BODY)):.0%}）")

# 段落长度：≤80 字；或 ≤3 句且 ≤88 字（尾部/原声豁免）
paras = [p for p in re.split(r"\n\s*\n", MAIN) if p.strip() and not is_tail_block(p)]
over = []
for i, p in enumerate(paras):
    if is_voice(p):
        continue
    vis = visible(p)
    n, ns = cjk(vis), n_sent(p)
    if n > 88 and ns > 3:
        over.append((i + 1, n, ns))
if not PUBLISHED:
    chk(not over, f"超长段落（>88 字且 >3 句）：{over}")

# AI 句 ≤60 字（+10% 容差 = 66 字；原声/尾部豁免）
sent_over = []
for p in paras:
    if is_voice(p):
        continue
    for s in re.split(r"[。！？；]", visible(p)):
        n = cjk(s)
        if n > 66:
            sent_over.append((n, s.strip()[:30]))
if not PUBLISHED:
    chk(not sent_over, f"超 60 字 AI 句：{sent_over}")

# 禁词 / AI 腔
BANNED = ["值得注意的是", "让我们来", "总而言之", "综上所述", "不难发现", "不难看出", "需要指出的是",
          "深入探讨", "全面分析", "起着至关重要的作用", "由上可知", "随着 AI 的发展", "今天我们来聊聊",
          "说人话就是", "伏笔"]
hits = [w for w in BANNED if w in BODY]
chk(not hits, f"禁词命中：{hits}")

# 待发布残留（放行项目规则允许的系列预告标注）
_BODY_NP = BODY.replace("记忆账（待发布）", "记忆账")
chk("（待发布）" not in _BODY_NP, "残留（待发布）")

# 话题标签
tags = re.findall(r"#\S+", BODY.splitlines()[-1] if BODY.strip() else "")
chk(3 <= len(tags) <= 5 and any("数解AI" in t for t in tags), f"话题标签异常：{tags}")

# 图片同级路径（无 images/ 前缀）
imgs = re.findall(r"!\[[^\]]*\]\(([^)]+)\)", BODY)
chk(all(not i.startswith("images/") for i in imgs), "图片带 images/ 前缀")
chk(len(imgs) >= 4, f"正文图不足 4 张：{len(imgs)}")

# 内链必须微信 URL
links = re.findall(r"\]\((https?://[^)]+)\)", BODY)
chk(all("mp.weixin.qq.com" in l for l in links), f"非微信外链：{links}")

# 承重数字在场（math_audit.md 已核：202/153/457 本机与 AppWorld；88.7% 推导；三个中位数为 2026-10-24 扫描）
for d in ["202 次", "153 个", "457", "88.7%", "195,536", "182,331", "62,610", "26–54%", "4102", "2510.00615", "2407.18901"]:
    chk(d in BODY, f"承重数字缺失：{d}")

# 字数（正文口径，去掉 frontmatter 与尾部块）
def sec_cjk(s):
    return cjk(re.sub(r"!\[[^\]]*\]\([^)]+\)", "", s))

n = sec_cjk(MAIN)
print(f"正文 CJK 字数（不含热门/参考资料/标签）：{n}")
if PUBLISHED:
    print("  · --published：跳过成稿期篇幅门禁")
else:
    chk(n <= 2300, f"正文超 2300：{n}")

print(f"原声 {sum(1 for s in SLOTS if slot_score(s, flat(BODY)) >= 0.9)}/{len(SLOTS)} | 图 {len(imgs)} 张 | 内链 {len(links)} 条")
print("PASS" if not fails else f"FAIL: {len(fails)} 项未过")
for f in fails:
    print(" -", f)
