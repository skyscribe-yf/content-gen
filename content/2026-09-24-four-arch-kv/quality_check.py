#!/usr/bin/env python3
"""四家架构篇 · 质量核查（自动化部分）

  1. CJK 字数  2. 禁词  3. 长句（>60 字，原声豁免）  4. 原声槽逐字在场
  5. 加粗失效  6. 图片路径/数量  7. 「待发布」残留  8. 公式与中文入公式
  9. AI 腔  10. 话题标签  11. 一手数字在场  12. 段落句数  13. 尾部热门榜格式
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
md = (ROOT / "weixin.md").read_text(encoding="utf-8")
body = md.split("---", 2)[2] if md.startswith("---") else md
slots_md = (ROOT / "slots.md").read_text(encoding="utf-8")

# ---- 1. CJK 字数 ----------------------------------------------------------
cjk = re.findall(r"[\u4e00-\u9fff]", body)
tail_start = body.find("📖 本文收进")
body_main = body[:tail_start] if tail_start > 0 else body
cjk_main = re.findall(r"[\u4e00-\u9fff]", body_main)
print(f"[1] 正文 CJK: {len(cjk_main)}｜含尾部总计: {len(cjk)}  (口径：正文 ≈2k，含尾部 ≤2.5k)")

# ---- 2. 禁词 --------------------------------------------------------------
BAN = ["钩子", "伏笔", "综上所述", "总而言之", "值得一提的是", "不难发现", "不难看出",
       "由此可见", "让我们", "本文将", "需要注意的是", "说人话就是", "赋能", "抓手",
       "颗粒度", "众所周知", "毋庸置疑", "值得注意的是", "深入探讨", "全面分析", "由上可知"]
hits = [(w, body.count(w)) for w in BAN if body.count(w)]
print(f"[2] 禁词/元词: {'0 处 ✅' if not hits else hits}")

# ---- 4. 原声槽（读 slots.md 的【进稿版】） --------------------------------
slots = re.findall(r"^【进稿版】(.+)$", slots_md, re.M)
flat = re.sub(r"[，。？！；：、\s\u3000“”「」（）]", "", body)
print(f"[4] 原声槽 {len(slots)} 处（下限 5）；逐字在场：")
allin = True
for i, s in enumerate(slots, 1):
    key = re.sub(r"[，。？！；：、\s\u3000“”「」（）]", "", s)
    ok = key in flat
    allin &= ok
    print(f"     槽{i}: {'✅' if ok else '✗ 缺失'}  {s[:34]}…")
print(f"     合计: {'全部逐字在场 ✅' if allin else '有缺 ❌'}"
      f"｜门禁: {'过 ✅' if len(slots) >= 5 and allin else '未过 ❌'}")
slot_keys = [re.sub(r"[，。？！；：、\s\u3000“”「」（）]", "", s) for s in slots]

# ---- 3. 长句（原声段落豁免） ----------------------------------------------
longs = []
for para in body.split("\n"):
    p = para.strip()
    if not p or p[0] in "#[📖🔥|>$" or p.startswith("**") or re.match(r"^\d+\.", p):
        continue
    pf = re.sub(r"[，。？！；：、\s\u3000“”「」（）]", "", p)  # 与槽位 key 同口径剥离引号
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

# ---- 6. 图片路径/数量 -----------------------------------------------------
imgs = re.findall(r"!\[[^\]]*\]\(([^)]+)\)", body)
missing = [i for i in imgs if not (ROOT / i).exists()]
cover_in_body = "00-cover.png" in imgs
print(f"[6] 正文图 {len(imgs)} 张（+封面 1）｜images/ 前缀: {'有 ❌' if any('images/' in i for i in imgs) else '无 ✅'}"
      f"｜缺文件: {missing if missing else '无 ✅'}｜封面混入正文: {'是 ❌' if cover_in_body else '否 ✅'}"
      f"｜数量: {'≥4 ✅' if len(imgs) + 1 >= 4 else '<4 ❌'}")

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
bad_tags = [t for t in tags if " " in t or "#" in t[1:]]
print(f"[10] 话题标签 {len(tags)} 个: {tags}｜无空格: {'✅' if not bad_tags else bad_tags}")

# ---- 11. 一手数字在场 -----------------------------------------------------
NUMS = ["0.93 GB", "2.69 GB", "6.3 GB", "13.7 GB", "15 倍", "24 倍", "890", "178", "356",
        "512", "545", "1,088 B", "2,560", "5,995", "13,056", "16 KB", "16 GB", "1,048,576",
        "2,048", "16,384", "196B", "4.44 倍", "2.92 倍", "25 层", "1,024", "128", "3.01 倍",
        "64 维", "5 层", "3 层", "11 层", "12 层", "4 层"]
miss = [n for n in NUMS if n not in body]
print(f"[11] 一手数字在场: {'全部在场 ✅' if not miss else '缺: ' + str(miss)}")

# ---- 12. 段落句数 ---------------------------------------------------------
bad_para = []
for para in body_main.split("\n"):
    p = para.strip()
    if not p or p[0] in "#[📖🔥|>$" or p.startswith("**") or p.startswith("|") or re.match(r"^\d+\.", p):
        continue
    if any(k and k in re.sub(r"[，。？！；：、\s\u3000“”「」（）]", "", p) for k in slot_keys):
        continue  # 原声段落豁免
    n = len(re.findall(r"[。！？]", p))
    if n > 3:
        bad_para.append((n, p[:40]))
print(f"[12] 超 3 句段落: {len(bad_para)} 处 {bad_para if bad_para else '✅'}")

# ---- 13. 尾部热门榜格式 ---------------------------------------------------
tail = body[tail_start:] if tail_start > 0 else ""
lines = [l for l in tail.split("\n") if l.startswith("[") and "](" in l]
no_twospace = [l[:34] for l in lines if not l.endswith("  ")]
blank_between = bool(re.search(r"\]\(https://mp\.weixin\.qq\.com/s/[^)]+\)  \n\n\[", tail))
print(f"[13] 热门榜 {len(lines)} 行｜行尾两空格缺失: {no_twospace if no_twospace else '0 ✅'}"
      f"｜行间空行: {'有 ❌' if blank_between else '无 ✅'}")
print(f"     下一篇预告: {'有 ✅' if '下一篇' in tail else '缺 ❌'}"
      f"｜互动引导: {'有 ✅' if ('赞' in tail and '关注' in tail and '收藏' in tail) else '缺 ❌'}"
      f"｜合集: {'有 ✅' if '合集' in tail else '缺 ❌'}")
