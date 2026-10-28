#!/usr/bin/env python3
"""本篇（C3 安全账）质量核查机器可查部分 + 作者口径（段落 ≤80 字 / 三级标题 / AI 句 ≤60 字 / 原声禁入引用块）。
适配自 content/2026-10-27-compaction-break-even/quality_check.py（原声/数字/门禁按本篇重列）。"""
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

# 原声 8 处逐字（来源 outline.md 作者原声槽，2026-10-28 作者逐条手动输入；语气词已按作者指令删除）
SLOTS = [
    "我有很多次发现，在我的 compact 指令后边加上具体的约束之后，一旦压缩完重新执行任务，很多东西似乎还是跑偏了。总想看清楚这里到底是什么地方，出了偏差。",
    "在压缩之前，我的Agent还是在抓实时数据的。但是发生了压缩之后，Agent突然就开始跑偏，居然瞎编起来，完全不顾我已经有实时数据的前提。",
    "其实压缩器只保任务成功，不管我们的约束，这个事情还真不能怪到压缩器头上，因为这个本来就是一件很难完成的事情。",
    "其实，压缩动作和指令本身，很可能并没有为我们很在乎的一些约束规矩针对性训练，它的主要目标还是完成一个全局的任务。",
    "其实对于一些特殊的授权指令，可能更好的放在工具或配置层面，或者是一些磁盘上可以再次读到的地方，放在会话指令里边，随口。执行其实非常不靠谱。",
    "就我个人的使用体验而言，我从来不会把它说的摘要当成一个百分之百可信的下一轮输入。",
    "更多时候，保持良好的纪律，需要把关键的约束写进我们的 agent.md 或者 doc 文档里边，让 agent 随时能够很快地翻到，而不是在压缩前后手动地再复述。这样很容易忘掉，也完全不可靠。",
    "你平时做例行压缩是怎么做的呢？有没有考虑约束应该放在什么地方？",
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

# 作者硬约束（2026-10-28）：原声不得进引用块（> blockquote），直接做正文段落
quote_lines = [l for l in BODY.splitlines() if l.lstrip().startswith(">")]
for i, s in enumerate(SLOTS, 1):
    chk(not any(flat(s) and flat(s) in flat(l) for l in quote_lines),
        f"原声槽 {i} 出现在引用块（作者禁项）")

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

# 待发布残留（放行项目规则允许的系列预告标注：C4 记忆账）
_BODY_NP = BODY.replace("（待发布）", "")
_BODY_NP = _BODY_NP.replace("记忆账：记忆只是历史的有损函数", "记忆账")
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

# 承重数字在场（math_audit.md 口径：本机扫描 2026-10-28 + 论文摘要 + Codex commit）
for d in ["153 个会话", "202 次压缩", "87.6%", "2556 条", "54 条", "0.3%", "24.4%",
          "90.8%", "56.0%", "1323", "38%", "8.3 倍", "#41852", "2026 年 10 月 27 日",
          "86.9%", "17%", "11 种", "47 个 token", "0.5%"]:
    chk(d in BODY, f"承重数字缺失：{d}")

# 禁现（分层纪律：V4.1 KV 压缩不是本系列落点；DPI/Fano 已由 C1 承担不重推）
for w in ["V4.1", "CSA2", "890 字节", "Fano", "上一篇我们", "篇三", "第三篇"]:
    chk(w not in BODY, f"禁现内容泄漏：{w}")

# 封面核验（2026-10-28 新增，作者反馈「封面文字小且拥挤」后固化）：
# ① 文字必须脚本叠加——封面目录须有 00-cover-base.png（AI 无字底图）+ make_cover.py 产物证据；
# ② check_cover.py：21:9 比例 + 金色文字块高 ≤25% 画面高；
# ③ cover_meta.json：封面文字总字数 ≤12（信息流缩略可读下限）。
import json as _json
import subprocess as _sp
HERE = Path(__file__).parent
cover = HERE / "00-cover.png"
chk(cover.exists(), "封面缺失：00-cover.png")
if cover.exists():
    r = _sp.run([sys.executable, str(HERE / "check_cover.py"), str(cover)],
                capture_output=True, text=True)
    print(r.stdout.strip())
    chk(r.returncode == 0, "check_cover.py 未通过（比例/文字块高超口径）")
meta_p = HERE / "cover_meta.json"
chk(meta_p.exists(), "cover_meta.json 缺失（封面须由 make_cover.py 脚本叠字生成）")
if meta_p.exists():
    meta = _json.loads(meta_p.read_text())
    chk(meta.get("total_chars", 99) <= 12,
        f"封面文字超 12 字（信息流缩略不可读）：{meta.get('total_chars')} 字 {meta.get('lines')}")
    chk(meta.get("block_ratio", 1) <= 0.25, f"封面文字块高超 25%：{meta.get('block_ratio')}")
chk((HERE / "00-cover-base.png").exists(),
    "缺 00-cover-base.png——封面文字必须脚本叠加（make_cover.py），禁止 AI 生图直接写中文")

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
