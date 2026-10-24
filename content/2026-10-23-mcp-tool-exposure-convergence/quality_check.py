#!/usr/bin/env python3
"""本篇 16 项质量核查中机器可查部分 + 作者口径（段落 ≤80 字 / 三级标题 / AI 句 ≤60 字）。
适配自 content/2026-10-21-pi-codemode-mcp/quality_check.py（原声/数字/爆项按本篇重列）。"""
import re
from pathlib import Path

HERE = Path(__file__).parent
TEXT = (HERE / "weixin.md").read_text()
BODY = TEXT.split("---", 2)[-1]
def cjk(s):
    return len(re.findall(r"[\u4e00-\u9fff]", s))

# 原声 7 处逐字（来源 outline.md ## 原声槽规划）
SLOTS = [
    "Anthropic又是如何处理MCP带来的上下文严重膨胀的问题呢？codex如何应对这个挑战？",
    "同样的问题，雷同的设计，难道这真的是巧合吗？",
    "对于我个人而言，透明可审计一直是至关重要的。要不然，编辑在哪个地方跑偏了，事后怎么追查原因，怎么做针对性改进呢？",
    "大概一年前，模型还不是那么聪明的时候，经常会不知不觉地产出海量的输出倾倒在本来就捉襟见肘的上下文里面。这个问题其实并没有随着模型进化被完全解决，除了去努力优化工具的命令提示和文档外，类似context mode这样的工具一直是备受欢迎的一种解决方案。",
    "我其实非常能理解他们设计方面的谨慎，因为目前细则上还是不太具有明显的确定性收益。很多时候具体效果还不得不量体裁衣，视具体情况而定。",
    "目前这个阶段，务实的态度还是根据实际的需求场景和测试效果，多测试多改进，并密切关注进一步的演进才是正解。",
    "还有一个至关重要的问题，是如何更好地维护上下文窗口内信息的密度和混淆情况，有空下次再探讨吧。",
]

fails = []

FLAT = re.sub(r"\s+", "", BODY)
SLOT_FLAT = [re.sub(r"\s+", "", s) for s in SLOTS]


def is_voice(par: str) -> bool:
    p = re.sub(r"\s+", "", par)
    return any(s in p or p in s for s in SLOT_FLAT)


def chk(cond, msg):
    if not cond:
        fails.append(msg)


for i, s in enumerate(SLOTS, 1):
    chk(s.replace(" ", "") in FLAT, f"原声槽 {i} 不在正文")

# 段落 ≤80 字（原声豁免；📖 合集导航及之后的尾部块不算正文）
MAIN = BODY.split("📖")[0]
paras = [p for p in re.split(r"\n\s*\n", MAIN) if p.strip() and not p.strip().startswith(("#", "!"))]
over = [(i + 1, cjk(p)) for i, p in enumerate(paras) if cjk(p) > 80 and not is_voice(p)]
chk(not over, f"超 80 字段落（非原声）：{over}")

# AI 句 ≤60 字（原声豁免；句号/问号/叹号/分号切句）
sent_over = []
for p in paras:
    if is_voice(p):
        continue
    for s in re.split(r"[。！？；]", p):
        n = cjk(s)
        if n > 60:
            sent_over.append((n, s.strip()[:30]))
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

body_only = BODY.split("📖")[0].split("**参考资料")[0]
n = sec_cjk(body_only)
print(f"正文 CJK 字数（含标题、图注外）：{n}")
chk(n <= 2300, f"正文超 2300：{n}")

print(f"原声 {sum(1 for s in SLOTS if s.replace(' ', '') in FLAT)}/{len(SLOTS)} | 图 {len(imgs)} 张 | 内链 {len(links)} 条")
print("PASS" if not fails else f"FAIL: {len(fails)} 项未过")
for f in fails:
    print(" -", f)
