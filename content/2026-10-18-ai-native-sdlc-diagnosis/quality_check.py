#!/usr/bin/env python3
import re
from pathlib import Path

HERE = Path(__file__).parent
TEXT = (HERE / "weixin.md").read_text()
BODY = TEXT.split("---", 2)[-1]

def cjk(s):
    return len(re.findall(r"[\u4e00-\u9fff]", s))

SLOTS = [
    "当你想要按照软件工程的流程要求去开发和交付正儿八经的软件的时候，很多营销宣传的口号都会立马被打回原形。",
    "商业软件所期望的各种非功能约束，领域特定的需求范式，软件需求和测试如何拉通对齐，这些核心挑战其实都远远称不上被完美解决。",
    "Antrhopic 公司根据自己企业内部实践推出来的 AI 原生 SDLC 方案，推出来已经有挺长时间了。这些来自于最前沿公司内部的软件工程实践，是否真的可以推广到很多传统商业软件公司，用于助力其他非 AI 开发公司的业务，我个人一直是持有大大的疑问的。",
    "软件本身的领域复杂性，就不是千篇一律的，充满了模糊空间，而 LLM 技术本身，从底层原理上看，就非常容易受到不确定性本身的影响——你给他的东西越含糊不清，他的困惑度就越大，很容易给你生成出来一大堆看似正确，其实内行看来错的离谱的成品出来。",
    "各种软件千人千面，各种技术上的非技术上的约束混杂期间，是否所有的东西都可以用堆 token 来完成，这是很多做 agent 评测和玩具 coding 项目的人从来都不会关心的事情。",
    "不过毕竟，它山之石可以攻玉，对于 Anthropic 这种工作方式，探讨和研究的价值还是很高的。",
]
fails = []
FLAT = re.sub(r"\s+", "", BODY)
SLOT_FLAT = [re.sub(r"\s+", "", s.replace("Antrhopic","Anthropic")) for s in SLOTS]

def chk(cond, msg):
    print(("  ✓ " if cond else "  ✗ ") + msg)
    if not cond:
        fails.append(msg)

print("[14] 原声逐字在场（≥5）")
for i, s in enumerate(SLOTS, 1):
    sf = re.sub(r"\s+", "", s.replace("Antrhopic","Anthropic"))
    chk(sf in FLAT, f"原声 {i}")

print("[新] 段落 ≤80 字")
paras = []
for p in BODY.split("\n"):
    p = p.strip()
    if not p or p[0] in "#|" or p.startswith("📖") or p.startswith("🔥") or p.startswith("!["):
        continue
    if re.match(r"^(\d+\.|[-*])\s", p):
        continue
    paras.append(p)
over = [(cjk(p), p) for p in paras if cjk(p) > 80]
chk(not over, f"无超 80 字段落（段落 {len(paras)} 个，超标 {len(over)}）")
for n, p in over[:5]:
    print("   ·", n, p[:60])

print("[新] 标题层级")
h2 = len(re.findall(r"^## ", BODY, re.M))
h3 = len(re.findall(r"^### ", BODY, re.M))
chk(h2 >= 5, f"H2={h2} 节（需≥5）")
# H3 not strictly required if no section >400 words; just report
print(f"   H3={h3}")

print("[11] 正文禁词")
BODY_NOLINKTXT = re.sub(r"\[([^\]]*)\]\([^)]*\)", "", BODY)
for w in ["钩子", "伏笔", "说人话就是"]:
    chk(w not in BODY_NOLINKTXT, f"无「{w}」")

print("[15] AI 腔扫描")
ai_words = ["值得注意的是", "让我们来", "总而言之", "综上所述", "不难发现", "不难看出",
            "需要指出的是", "深入探讨", "全面分析", "由上可知", "今天我们来聊聊"]
for w in ai_words:
    chk(w not in BODY, f"无「{w}」")

print("[10] 超 60 字长句（原声/参考资料/导航豁免）")
seg = re.sub(r"\((https?://[^)]+)\)", "()", BODY)
seg = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", seg)
seg = "\n".join(p for p in seg.split("\n") if not any(re.sub(r"\s+","",p) in s for s in SLOT_FLAT))
# skip table rows and list items (not prose sentences)
seg = "\n".join(p for p in seg.split("\n") if not p.strip().startswith("|") and not re.match(r"^\s*[-*\d]", p.strip()))
long_hits = [s.strip() for s in re.split(r"[。！？\n]", seg) if len(s.strip()) > 60 and not s.strip().startswith("**") and "→" not in s]
chk(not long_hits, f"无超 60 字 AI 句（命中 {len(long_hits)}）")

print("[8] 图片路径与配图数量")
chk("images/" not in BODY, "无 images/ 前缀")
refs = set(re.findall(r"\]\(([^)]+\.png)\)", BODY))
missing = sorted(r for r in refs if not (HERE / r).exists())
chk(not missing, f"引用的图都存在（缺 {missing}）")
chk(len(refs) >= 4, f"正文配图≥4 张（当前 {len(refs)}）")

print("[5/16] 结尾互动与转发设计")
chk("#数解AI" in BODY, "含 #数解AI")
tags = re.findall(r"#\S+", BODY.split("参考资料")[-1] if "参考资料" in BODY else BODY)
# tags at end
tail_tags = re.findall(r"#\S+", BODY[-200:])
chk(3 <= len(tail_tags) <= 5, f"话题标签 3-5 个（当前 {len(tail_tags)}）")

print("[13] 爆款要素抽查")
chk(("？" in TEXT.split("\n")[1]) or ("吗" in TEXT.split("\n")[1]) or ("呢" in TEXT.split("\n")[1]) if len(TEXT.split("\n"))>1 else False, "标题疑问句")
chk("📖" in BODY or "软件工程合集" in BODY, "系列导航在场")

print()
print("PASS" if not fails else f"FAIL: {len(fails)} 项未过")
for f in fails:
    print("  ✗", f)
