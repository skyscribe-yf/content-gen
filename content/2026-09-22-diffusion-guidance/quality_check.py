#!/usr/bin/env python3
"""篇 3 质量核查（自动化部分）：
  1. 正文字数（CJK）  2. 禁词  3. 长句（>60 字）  4. 原声槽逐字在场
  5. 加粗失效（CommonMark flanking）  6. 图片路径（无 images/ 前缀、文件存在）
  7. 「待发布」残留   8. 公式数量与中文入公式检查   9. AI 腔检测
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
md = (ROOT / "weixin.md").read_text()
body = md.split("---", 2)[2] if md.startswith("---") else md

# ---- 1. CJK 字数 ----------------------------------------------------------
cjk = re.findall(r"[\u4e00-\u9fff]", body)
print(f"[1] CJK 字数（正文含尾部）: {len(cjk)}")

# ---- 2. 禁词 --------------------------------------------------------------
BAN = ["同事", "首先", "其次", "最后，", "综上所述", "总而言之", "赋能", "抓手",
       "闭环", "颗粒度", "对齐一下", "打法", "复盘一下", "众所周知", "毋庸置疑",
       "值得一提的是", "不难发现", "由此可见", "让我们", "本文将", "需要注意的是"]
hits = [(w, body.count(w)) for w in BAN if body.count(w)]
print(f"[2] 禁词: {'0 处 ✅' if not hits else hits}")

# ---- 3. 长句 --------------------------------------------------------------
longs = []
for para in body.split("\n"):
    p = para.strip()
    if not p or p.startswith(("#", "[", "📖", "🔥", "**", ">", "|", "-", "1.", "2.", "3.", "4.", "5.", "6.", "7.", "8.")):
        continue
    for sent in re.split(r"(?<=[。！？])", p):
        s = re.sub(r"\$[^$]*\$", "X", sent)
        n = len(re.findall(r"[\u4e00-\u9fff]", s))
        if n > 60:
            longs.append((n, s[:70]))
print(f"[3] 超 60 字长句: {len(longs)} 处")
for n, s in longs:
    print(f"     ({n} 字) {s}…")

# ---- 4. 原声槽 ------------------------------------------------------------
outline = (ROOT / "outline.md").read_text()
slots = re.findall(r"- 原句：(.+)", outline)
print(f"[4] 原声槽 {len(slots)} 处；逐字在场核查：")
allin = True
for i, s in enumerate(slots, 1):
    s2 = s.strip()
    # 允许正文中把长句拆开（只加句号/换行），这里按「去标点后子串包含」判定
    key = re.sub(r"[，。？！；：\s]", "", s2)[:40]
    flat = re.sub(r"[，。？！；：\s]", "", body)
    ok = key in flat
    allin &= ok
    print(f"     槽{i}: {'✅' if ok else '✗ 缺失'} {s2[:40]}…")
print(f"     合计 {'5/5 全部逐字在场 ✅' if allin else '有缺 ❌'}")

# ---- 5. 加粗失效（按 CommonMark flanking 规则做开/闭配对）------------------
import unicodedata

PUNCT_EXTRA = set("。，、；：？！""''（）《》「」·—…")


def _is_punct(ch):
    if not ch:
        return False
    return ch in PUNCT_EXTRA or (ch.isascii() and not ch.isalnum() and not ch.isspace())


def _is_space(ch):
    return ch == "" or ch.isspace()


def _flank(s, i, j):
    b = s[i - 1] if i > 0 else ""
    a = s[j] if j < len(s) else ""
    b_p, b_s, a_p, a_s = _is_punct(b), _is_space(b), _is_punct(a), _is_space(a)
    left = (not a_s) and ((not a_p) or (b_s or b_p))
    right = (not b_s) and ((not b_p) or (a_s or a_p))
    return left, right


bad_bold = []
for line in body.split("\n"):
    inside = False
    for m in re.finditer(r"\*\*", line):
        left, right = _flank(line, m.start(), m.end())
        if not inside:
            if left:
                inside = True
        elif right:
            inside = False
        else:
            bad_bold.append(line[max(0, m.start() - 24):m.end() + 12])
print(f"[5] 加粗失效(CommonMark flanking): {len(bad_bold)} 处 "
      f"{'✅' if not bad_bold else bad_bold[:2]}")

# ---- 6. 图片路径 ----------------------------------------------------------
imgs = re.findall(r"!\[[^\]]*\]\(([^)]+)\)", body)
print(f"[6] 正文图片引用 {len(imgs)} 张：")
for im in imgs:
    p = ROOT / im
    flag = "✅" if (p.exists() and "images/" not in im) else "✗"
    print(f"     {flag} {im}")

# ---- 7. 待发布残留 --------------------------------------------------------
print(f"[7] 「待发布 / 待补」残留: {body.count('待发布') + body.count('TODO')} 处")

# ---- 8. 公式 --------------------------------------------------------------
formulas = re.findall(r"\$\$.*?\$\$", body, re.S)
inline = re.findall(r"(?<!\$)\$(?!\$)[^$]+(?<!\$)\$(?!\$)", body)
bad_cjk = [f[:40] for f in formulas if re.search(r"\\text\{[^}]*[\u4e00-\u9fff]", f)]
bad_under = [f[:40] for f in formulas if re.search(r"\\underbrace\{[^}]*[\u4e00-\u9fff]", f)]
print(f"[8] 独立公式 {len(formulas)} 条 / 内联 {len(inline)} 条；"
      f"中文入公式(\\text/\\underbrace): {len(bad_cjk)+len(bad_under)} 处 "
      f"{'✅' if not bad_cjk and not bad_under else bad_cjk + bad_under}")

# ---- 9. AI 腔 -------------------------------------------------------------
AI_ISH = ["其实说到这里", "我们不难看出", "接下来让我们", "由此我们可以",
          "这也就不难理解", "总而言之", "换句话说，我们", "可以说，"]
h2 = [(w, body.count(w)) for w in AI_ISH if body.count(w)]
print(f"[9] AI 腔短语: {'0 处 ✅' if not h2 else h2}")

# ---- 10. 尾部与结构 -------------------------------------------------------
tail = body[-500:]
tags = re.findall(r"#[\u4e00-\u9fffA-Za-z]+", tail)
print(f"[10] 话题标签: {len(tags)} 个 {tags}")
print(f"     H2 数: {len(re.findall(r'(?m)^## ', body))} | "
      f"H3 数: {len(re.findall(r'(?m)^### ', body))}")
print(f"     封面是否混入正文: {'✗ 有' if '00-cover.png' in body else '✅ 无'}")
