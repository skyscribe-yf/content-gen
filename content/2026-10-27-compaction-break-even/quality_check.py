#!/usr/bin/env python3
"""本篇（C2 钱账）质量核查机器可查部分 + 作者口径（段落 ≤80 字 / 三级标题 / AI 句 ≤60 字）。
适配自 content/2026-10-25-context-compression-info-bound/quality_check.py（原声/数字/门禁按本篇重列）。"""
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
    return (not s) or s.startswith(("#", "!", "[", "🔥", "📖", "|")) or bool(re.match(r"^\d+\.\s", s))

def visible(par):
    """微信端可见文字：先删整张图片（含 alt），再把链接还原成链接文字。"""
    s = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", par)
    return re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", s)

def n_sent(par):
    return len([x for x in re.split(r"[。！？；!?;]", visible(par)) if cjk(x) >= 4])

# 原声 6 处逐字（来源 voices.md，2026-10-27 作者逐条手动输入；槽 1/4 笔误经作者确认更正）
SLOTS = [
    "表面看起来，应该是更短的上下文会降低token的开销，所以基于之前的认知，我一直是频繁去调用compact指令来及早压缩上下文，然而当我真正去查看长任务的开销，却发现其实成本甚至是在上升的。",
    "作为一个更相信数字而不是朴素直觉的人，仔细查看了具体请求的每一轮缓存命中情况后，我才发现盲目压缩之后的代价是如此之大，以至于需要好几轮的请求之后，缓存命中才慢慢上来，而这个缓慢爬坡的过程中的每一次请求，代价都极其高昂，因为缓存命中率低导致的开销可能是之前大请求的好几倍甚至是十倍以上。",
    "很多时候，缓存价格对实际账单的影响是巨大的，尤其是当今这个agent时代，不同的任务类型选择了不同的模型，对缓存定价策略的影响也并不像表面看起来那么明显。Coding类任务尤其是几乎完全由模型缓存的折扣系数决定，压缩带来的影响更甚。",
    "其实这笔账让Harness来计算，多少有些勉为其难，因为价格方面是非常市场化且动态调整的，但是让人来判断又总是不太可靠，除非你总是在稳定地使用一两个模型。类似于claude code或者codex的工具，可能会基于自家的模型来选择一个合适的解法，问题是当你用不同的模型，他们有着不同的定价逻辑的时候，这个决策反而可能不是最合理的。",
    "其实还有一个隐藏的要素，是上下文状态里面的混淆要素，牵扯到context rot,也需要动态纳入考量。目前这个阶段，很可能依赖于人对目前使用的模型的能力认知、价格定价机制有更综合的了解，在选择合适的设置，这方面更灵活可定义的harness比如pi coding agent会有更高的灵活性。但是毫无怀疑，相比于一年前，需要频繁手动compact的时机是少了很多了。",
    "我的感觉是更长的上下文支持和模型能力的提升，会逐渐边缘化压缩动作本身，然而人的综合判断兜底短期内都还不太会完全消失。",
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

# 待发布残留（放行项目规则允许的系列预告标注：C3 安全账）
_BODY_NP = BODY.replace("免费的（待发布）", "免费的")
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

# 承重数字在场（math_audit.md 口径：受控统计 n=51/49 + 官方价目，2026-10-26/27 核）
for d in ["77%", "26.8 万", "6.1 万", "1,006", "99.6%", "48.5%", "34,543", "98.3%",
          "1.35 倍", "31 倍", "0.02", "0.20", "10 倍", "$0.15", "$0.03", "19.3", "84%",
          "99 轮", "15 次", "0.1000", "clear_at_least", "267,916", "60,889", "2026-08-17"]:
    chk(d in BODY, f"承重数字缺失：{d}")

# 禁现（数据排除令：正文不得出现被排除 provider 的例子）
for w in ["opencode-go", "ollama-cloud", "commandcode", "xunfei", "讯飞", "170 轮", "20% 回本", "0.29", "0.23 元"]:
    chk(w not in BODY, f"排除名单/作废口径泄漏：{w}")

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
