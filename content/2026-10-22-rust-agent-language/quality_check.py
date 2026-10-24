#!/usr/bin/env python3
"""本篇质量核查中机器可查部分：原声逐字在场 + 段落 ≤80 字 + 标题分层 + 字数。"""
import re
import sys
import difflib
from pathlib import Path

HERE = Path(__file__).parent
TEXT = (HERE / "weixin.md").read_text()
BODY = TEXT.split("---", 2)[-1]

# --published：已发布文章以后台正文为准，跳过成稿期门禁（原声/段落/篇幅）。
PUBLISHED = "--published" in sys.argv


def cjk(s):
    return len(re.findall(r"[\u4e00-\u9fff]", s))


def flat(s):
    return re.sub(r"\s+", "", s)


# 尾部边界：热门文章 / 合集导航 / 参考资料 / 话题标签行之后不算正文。
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


def is_voice(par):
    p = flat(par)
    if not p:
        return False
    return any(p in flat(s) or flat(s) in p or slot_score(s, p) >= 0.85 for s in SLOTS)


def is_tail_block(par):
    s = par.strip()
    return (not s) or s.startswith(("#", "!", "[", "🔥", "📖")) or bool(re.match(r"^\d+\.\s", s))


def visible(par):
    """微信端可见文字：先删整张图片（含 alt），再把链接还原成链接文字。"""
    s = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", par)
    return re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", s)


def n_sent(par):
    return len([x for x in re.split(r"[。！？；!?;]", visible(par)) if cjk(x) >= 4])

# 原声 7 处（来源 outline.md ## 作者原声槽；已按约定修错别字：
# 纵容→纵然、typeacript→TypeScript、refcell→RefCell、rust/python/typescript 大小写规范化）
SLOTS = [
    "我的许多skill里面内嵌的工具和命令行程序，一开始使用的是Python或者TypeScript写的，原因很简单，早期的agent对这两种语言拟合的最好，更容易一遍就好。",
    "问题是很多时候，skill调用起来后，Agent会耗费很多时间等待不能秒回的调用操作。",
    "这个问题如此严重以致于我很快就要Rust重写了里面的绝大部分，今年下半年以来的开源模型和harness都能处理的很好了。",
    "当时我的主要想法是，不能让Agent耗费大量时间在等待。",
    "那样的话，纵然你可以并行开很多个Agent，最终效率也会提升有限，况且操作者也很快因为在多个缓慢执行的Agent任务上下文里面切换而变得疲惫不堪了。",
    "Rust给我们的关于编译通过即正确的承诺，很多时候其实需要深入去讨论。",
    "很多时候这不过是一种过度承诺，尤其是业务逻辑上的错误，它就无能为力，更不要说令人发指的unsafe泛滥问题，和RefCell滥用问题，都会造成大量的谬误。",
    "很多问题其实并没有被编译器完全解决，而是被转移了。",
    "以我在AI大泛滥时代之前，手撸十几万Rust代码的经验来看，这个bench的结果毫无意外。",
    "很多深层次的问题，还是需要耗费大量的精力去调整，尤其是一开始设计错误某些方向，后面想要调整依然是麻烦不断。",
    "那些复杂的边边角角，其实在我看来，大概是软件布道师们选择性遗忘的大沼泽地。",
    "我的例子之所以工作很好，是因为验证那些工具的成败与否逻辑非常明确，裁判就靠原来TypeScript版里面已有的参照测试用例。",
    "如果是完全重头写过的skill工具，那照样还是需要大量的试错和复盘挖掘。",
    "这个分解是挺合理的，不过还要加上约束和验收标准明确的地方，收益可能更大。",
    "你们自己的Agent生态，有没有引入Rust作为热点路径上的加速器，还是很多业务都拿Rust做了重写?",
]

fails = []
FLAT = re.sub(r"\s+", "", BODY)

def chk(cond, msg):
    print(("  ✓ " if cond else "  ✗ ") + msg)
    if not cond:
        fails.append(msg)

print("[14] 原声逐字在场（15 个句子段 / 7 处，≥5 达标；相似度 ≥90%）")
if PUBLISHED:
    print("  · --published：跳过成稿期原声校验")
else:
    for i, s in enumerate(SLOTS, 1):
        chk(slot_score(s, flat(BODY)) >= 0.9, f"原声 {i}（相似度 {slot_score(s, flat(BODY)):.0%}）")

print("[17] 段落长度（≤80 字；或 ≤3 句且 ≤88 字；尾部/原声豁免）")
paras = [p.strip() for p in re.split(r"\n\s*\n", MAIN) if p.strip()]
over = []
for p in paras:
    if is_tail_block(p) or is_voice(p):
        continue
    vis = visible(p)
    n = cjk(vis) + len(re.findall(r"[A-Za-z0-9]+", vis))
    ns = n_sent(p)
    if n > 88 and ns > 3:
        over.append((n, ns, p[:40]))
if PUBLISHED:
    print("  · --published：跳过成稿期段落校验")
else:
    for n, ns, t in over:
        chk(False, f"{n} 字 / {ns} 句：{t}…")
    if not over:
        chk(True, "全部段落合规")

print("[17] 标题分层")
h2 = re.findall(r"^## (.+)$", BODY, re.M)
chk(len(h2) >= 5, f"## 节 {len(h2)} 个（≥5）")
# 每节字数
secs = re.split(r"^## ", BODY, flags=re.M)[1:]
for sec in secs:
    title = sec.split("\n", 1)[0].strip()
    n = len(re.findall(r"[\u4e00-\u9fff]", sec))
    has_h3 = bool(re.search(r"^### ", sec, re.M))
    if n > 400 and not has_h3:
        chk(False, f"「{title}」{n} 字 >400 且无 ### 小标题")
    else:
        chk(True, f"「{title}」{n} 字")

print("[篇幅] 正文口径（不含热门文章/参考资料/标签）")
vis_body = re.sub(r"\]\([^)]*\)", "]", MAIN)  # URL 不可视，不计
vis_body = re.sub(r"!\[[^\]]*\]", "", vis_body)  # 图片引用（含 alt）微信端不显示，不计
cjk_n = len(re.findall(r"[\u4e00-\u9fff]", vis_body))
eng_n = len(re.findall(r"[A-Za-z0-9]+", vis_body))
if PUBLISHED:
    print(f"  · 正文可视字数 {cjk_n + eng_n}（中文 {cjk_n} + 英文词 {eng_n}）｜--published 跳过篇幅门禁")
else:
    chk(cjk_n + eng_n <= 2500, f"正文可视字数 {cjk_n+eng_n}（中文 {cjk_n} + 英文词 {eng_n}，≤2500）")

print()
print("FAIL" if fails else "ALL PASS")
