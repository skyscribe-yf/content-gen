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

# 原声 7 处逐字（来源 outline.md ## 原声槽规划）
SLOTS = [
    "Anthropic又是如何处理MCP带来的上下文严重膨胀的问题呢？codex如何应对这个挑战？",
    "同样的问题，雷同的设计，难道这真的是巧合吗？",
    "对于我个人而言，透明可审计一直是至关重要的。要不然，编辑在哪个地方跑偏了，事后怎么追查原因，怎么做针对性改进呢？",
    # 槽 4 于 2026-10-24 按作者后台改写版重录（bash 脚本版 + 强化学习补充句）
    "大概一年前，模型还不是那么聪明的时候，经常会不知不觉地组合出一个看起来很弱的bash脚本来，这样的脚本最终很可能会产出海量的输出，倾倒在本来就捉襟见肘的上下文里面。这个问题其实并没有随着模型进化被完全解决，大规模强化学习训练其实仅仅是部分缓解了问题。除了去努力优化工具的命令提示和文档外，类似context mode这样的工具一直是备受欢迎的一种解决方案。",
    "我其实非常能理解他们设计方面的谨慎，因为目前细则上还是不太具有明显的确定性收益。很多时候具体效果还不得不量体裁衣，视具体情况而定。",
    "目前这个阶段，务实的态度还是根据实际的需求场景和测试效果，多测试多改进，并密切关注进一步的演进才是正解。",
    "还有一个至关重要的问题，是如何更好地维护上下文窗口内信息的密度和混淆情况，有空下次再探讨吧。",
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

# 待发布残留
chk("（待发布）" not in BODY, "残留（待发布）")

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

# 承重数字在场（本轮一手核实）
for d in ["36781", "29486", "29122", "10%", "2000 行", "1 MiB", "off by default", "10K 到 20K"]:
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
