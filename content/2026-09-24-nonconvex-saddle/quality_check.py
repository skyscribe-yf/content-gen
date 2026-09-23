#!/usr/bin/env python3
"""非凸/鞍点篇 · 质量核查（自动化部分）
  1. CJK 字数  2. 禁词  3. 长句（>60 字，原声豁免）  4. 原声槽逐字在场
  5. 加粗失效  6. 图片路径  7. 「待发布」残留  8. 公式与中文入公式
  9. AI 腔  10. 话题标签  11. 实验/一手数字在场  12. 段落句数
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
md = (ROOT / "weixin.md").read_text(encoding="utf-8")
body = md.split("---", 2)[2] if md.startswith("---") else md
slots_md = (ROOT / "slots.md").read_text(encoding="utf-8")

# ---- 1. CJK 字数 ----------------------------------------------------------
cjk = re.findall(r"[\u4e00-\u9fff]", body)
tail_start = body.find("📖 **AI中的数学**")
body_main = body[:tail_start] if tail_start > 0 else body
cjk_main = re.findall(r"[\u4e00-\u9fff]", body_main)
print(f"[1] 正文 CJK: {len(cjk_main)}｜含尾部总计: {len(cjk)}  (本篇口径：正文 ≈3.4k，含尾部 ≤4k)")

# ---- 2. 禁词 --------------------------------------------------------------
BAN = ["钩子", "伏笔", "综上所述", "总而言之", "值得一提的是", "不难发现", "不难看出",
       "由此可见", "让我们", "本文将", "需要注意的是", "说人话就是", "赋能", "抓手",
       "颗粒度", "众所周知", "毋庸置疑", "值得注意的是", "深入探讨", "全面分析", "由上可知"]
hits = [(w, body.count(w)) for w in BAN if body.count(w)]
print(f"[2] 禁词/元词: {'0 处 ✅' if not hits else hits}")

# ---- 4. 原声槽（读 slots.md 的【进稿版】） --------------------------------
slots = re.findall(r"^【进稿版】(.+)$", slots_md, re.M)
flat = re.sub(r"[，。？！；：、\s\u3000“”「」（）]", "", body)
print(f"[4] 原声槽 {len(slots)} 处；逐字在场：")
allin = True
for i, s in enumerate(slots, 1):
    key = re.sub(r"[，。？！；：、\s\u3000“”「」（）]", "", s)
    ok = key in flat
    allin &= ok
    print(f"     槽{i}: {'✅' if ok else '✗ 缺失'}  {s[:34]}…")
print(f"     合计: {'全部逐字在场 ✅' if allin else '有缺 ❌'}")
slot_keys = [re.sub(r"[，。？！；：、\s\u3000“”「」（）]", "", s) for s in slots]

# ---- 3. 长句（原声段落豁免） ----------------------------------------------
longs = []
for para in body.split("\n"):
    p = para.strip()
    if not p or p[0] in "#[📖🔥|>$" or p.startswith("**") or re.match(r"^\d+\.", p):
        continue
    pf = re.sub(r"[，。？！；：、\s\u3000]", "", p)
    if any(k and k in pf for k in slot_keys):
        continue
    for sent in re.split(r"(?<=[。！？])", p):
        s = re.sub(r"\$[^$]*\$", "X", sent)
        n = len(re.findall(r"[\u4e00-\u9fff]", s))
        if n > 60:
            longs.append((n, s[:70]))
print(f"[3] 超 60 字长句（原声豁免后）: {len(longs)} 处 {'✅' if not longs else ''}")
for n, s in longs:
    print(f"     ({n} 字) {s}…")

# ---- 5. 加粗失效 ----------------------------------------------------------
CJK = r"\u4e00-\u9fff"
PUNCT = "。，、；：？！（）《》「」·—…％%"
bad_bold = []
for m in re.finditer(r"\*\*(.+?)\*\*", body, re.S):
    inner, before, after = m.group(1), body[:m.start()], body[m.end():m.end() + 1]
    if not inner:
        continue
    first, last = inner[0], inner[-1]
    if before and re.match(f"[{CJK}{PUNCT}]", before[-1]) and (first.isspace() or first in PUNCT):
        bad_bold.append(("开", m.group(0)[:30]))
    if after and re.match(f"[{CJK}{PUNCT}]", after) and (last.isspace() or last in PUNCT):
        bad_bold.append(("闭", m.group(0)[:30]))
print(f"[5] 加粗失效: {'0 处 ✅' if not bad_bold else bad_bold}")

# ---- 6. 图片路径 ----------------------------------------------------------
imgs = re.findall(r"!\[[^\]]*\]\(([^)]+)\)", body)
missing = [i for i in imgs if not (ROOT / i).exists()]
print(f"[6] 图片 {len(imgs)} 张｜images/ 前缀: {'有 ❌' if any('images/' in i for i in imgs) else '无 ✅'}"
      f"｜待出图: {missing if missing else '无（全部已存在）✅'}")

# ---- 7. 待发布残留 --------------------------------------------------------
print(f"[7] 「待发布」残留: {body.count('待发布')} 处 {'✅' if body.count('待发布') == 0 else '❌'}")

# ---- 8. 公式 --------------------------------------------------------------
display = re.findall(r"\$\$(.+?)\$\$", body, re.S)
inline = re.findall(r"(?<!\$)\$([^$\n]+)\$(?!\$)", body)
cn_in_math = [f for f in display + inline if re.search(r"[\u4e00-\u9fff]", f)]
print(f"[8] 公式 display {len(display)} 条 / inline {len(inline)} 条｜中文入公式: {cn_in_math if cn_in_math else '0 ✅'}")

# ---- 9. AI 腔 -------------------------------------------------------------
AI_PAT = r"值得注意的是|让我们来|总而言之|综上所述|不难发现|不难看出|需要指出的是|深入探讨|全面分析|由上可知|今天我们来聊聊|随着 ?AI 的发展"
ai_hits = re.findall(AI_PAT, body)
print(f"[9] AI 腔: {ai_hits if ai_hits else '0 ✅'}｜「说人话就是」: {body.count('说人话就是')}")

# ---- 10. 话题标签 ---------------------------------------------------------
tags = re.findall(r"#\S+", body.strip().split("\n")[-1])
print(f"[10] 话题标签 {len(tags)} 个: {tags}")

# ---- 11. 实验/一手数字在场 ------------------------------------------------
NUMS = ["50.0%", "14.6%", "2.46%", "0.0125%", "0.121", "0.500", "0.68", "49.5%",
        "29.3%", "46.7%", "1.203", "0.0038", "0.00080", "1.4e-17", "5.6e-17", "1.242",
        "0.744", "0.741", "0.978", "313 倍", "0.02", "4000"]
miss = [n for n in NUMS if n not in body]
print(f"[11] 实验/一手数字在场: {'全部在场 ✅' if not miss else '缺: ' + str(miss)}")

# ---- 12. 段落句数 ---------------------------------------------------------
bad_para = []
for para in body_main.split("\n"):
    p = para.strip()
    if not p or p[0] in "#[📖🔥|>$" or p.startswith("**") or re.match(r"^\d+\.", p):
        continue
    n = len(re.findall(r"[。！？]", p))
    if n > 3:
        bad_para.append((n, p[:40]))
print(f"[12] 超 3 句段落: {len(bad_para)} 处 {bad_para if bad_para else '✅'}")
