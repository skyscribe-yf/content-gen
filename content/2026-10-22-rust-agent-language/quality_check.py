#!/usr/bin/env python3
"""本篇质量核查中机器可查部分：原声逐字在场 + 段落 ≤80 字 + 标题分层 + 字数。"""
import re
from pathlib import Path

HERE = Path(__file__).parent
TEXT = (HERE / "weixin.md").read_text()
BODY = TEXT.split("---", 2)[-1]

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

print("[14] 原声逐字在场（15 个句子段 / 7 处，≥5 达标）")
for i, s in enumerate(SLOTS, 1):
    chk(re.sub(r"\s+", "", s) in FLAT, f"原声 {i}")

print("[17] 段落 ≤80 字（链接/标签块/列表除外）")
paras = [p.strip() for p in BODY.split("\n\n") if p.strip()]
over = []
for p in paras:
    if p.startswith(("#", "-", "*", "[", "🔥")) or re.match(r"^\d+\. ", p):
        continue
    # 去掉 markdown 链接只数可视文字
    vis = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", p)
    n = len(re.findall(r"[\u4e00-\u9fff]", vis)) + len(re.findall(r"[A-Za-z0-9]+", vis))
    if n > 80:
        over.append((n, p[:40]))
for n, t in over:
    chk(False, f"{n} 字：{t}…")
if not over:
    chk(True, "全部段落 ≤80 字")

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

print("[篇幅]")
vis_body = re.sub(r"\]\([^)]*\)", "]", BODY)  # URL 不可视，不计
vis_body = re.sub(r"!\[[^\]]*\]", "", vis_body)  # 图片引用（含 alt）微信端不显示，不计
cjk = len(re.findall(r"[\u4e00-\u9fff]", vis_body))
eng = len(re.findall(r"[A-Za-z0-9]+", vis_body))
chk(cjk + eng <= 2500, f"含尾部可视字数 {cjk+eng}（中文 {cjk} + 英文词 {eng}，≤2500）")

print()
print("FAIL" if fails else "ALL PASS")
