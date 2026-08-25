#!/usr/bin/env python3
"""《显存被谁吃掉了？DeepSeek如何省下90%》视频号场景（MiniMax 内置男声版 2026-08-25）。

- 6 个场景 S1-S6，与 storyboard.md 一一对应（2026-08-25 拍板 6 段收紧）
- 配音：MiniMax 内置男声 male-qn-jingying（2026-08-25 弃用克隆音色，用户嫌节奏忽快忽慢）
- 时间轴锚点 = tts/sentence-boundaries.json 的 clip id（at_clip 精确挂接，字幕块粒度）
- 动画降噪：每页 1 个主视觉动效，其余静态 type_in/scroll_unroll 入场
- 概念图：img/s1-oom-round.png、s3-notes-round.png、s5-jl-round.png（AI 图禁数字）
- 数字全部脚本画图（grow_bar / counter_value）
"""
from __future__ import annotations

import pathlib
import sys


def _scripts_dir() -> str:
    p = pathlib.Path(__file__).resolve().parent
    for _ in range(6):
        candidate = p / "scripts"
        if (candidate / "manim_helpers.py").exists():
            return str(candidate)
        p = p.parent
    raise RuntimeError("找不到 scripts/manim_helpers.py")


sys.path.insert(0, _scripts_dir())
from manim_helpers import *


IMG = pathlib.Path(__file__).resolve().parent / "img"
ROOT = pathlib.Path(__file__).resolve().parent.parent.parent.parent  # content-gen/

# ffprobe tts/s1.wav ... tts/s6.wav（2026-08-25 重录：内置男声 male-qn-jingying，speed 1.0 pitch +2）
VOICE_DUR = {
    "S1": 29.44,
    "S2": 34.73,
    "S3": 34.39,
    "S4": 35.16,
    "S5": 37.21,
    "S6": 32.14,
}
TAIL = 2.5


def _header(label: str):
    return fit(t(label, 34, YELL, "BOLD"), 0.86).to_edge(UP, buff=1.12)


def _page(*mobjects, buff: float = 0.75):
    page = page_stack(*mobjects, buff=buff)
    layout_page(page)
    return page


def _image(name: str, width: float) -> ImageMobject:
    image = ImageMobject(str(IMG / name))
    image.scale_to_fit_width(width)
    return image


def _footer(scene):
    footer = t("数解AI · DeepSeek 技术解密", 20, MUTED).to_edge(DOWN, buff=1.15)
    scene.add(footer)
    return footer


def _fit(mob, max_w: float = 7.7):
    if mob.width > max_w:
        mob.set_width(max_w)
    return mob


def _reveal(scene, mob, run_time: float = 0.6, **kw):
    scene.play(type_in(mob, run_time), run_time=run_time, **kw)


def _reveal_title(scene, title, run_time: float = 0.6):
    scene.play(type_in(title, run_time), run_time=run_time)


def _label(text: str, size: float = 32, color: str = WHITE, weight: str = "BOLD"):
    return _fit(t(text, size, color, weight))


def _block(lines, size: float = 34, color: str = WHITE, weight: str = "BOLD",
           sub_size: float = 27, sub_color: str = MUTED):
    main = _fit(t(lines[0], size, color, weight))
    if len(lines) == 1:
        return main
    sub = _fit(t(lines[1], sub_size, sub_color))
    block = VGroup(main, sub).arrange(DOWN, buff=0.16)
    return block


def _leaves(mobject):
    children = getattr(mobject, "submobjects", ())
    if not children:
        return [mobject]
    leaves = []
    for child in children:
        leaves.extend(_leaves(child))
    return leaves


def _roots_for(scene, *targets):
    wanted = set()
    for target in targets:
        wanted.add(id(target))
        wanted.update(id(leaf) for leaf in _leaves(target))
    roots = []
    for root in list(scene.mobjects):
        ids = {id(root)}
        ids.update(id(leaf) for leaf in _leaves(root))
        if ids & wanted:
            roots.append(root)
    return roots


def _clear(scene, page, *extras, run_time: float = 0.28):
    roots = _roots_for(scene, page, *extras)
    if roots:
        scene.play(FadeOut(*roots), run_time=run_time)
        scene.remove(*roots)


def _dissolve(scene, *targets, run_time: float = 1.05):
    """溶解式换页：元素像素化成同色小方块 → 方块随机方向飞散淡出。"""
    roots = _roots_for(scene, *targets)
    if not roots:
        return
    rng = np.random.default_rng(20260824)
    shards: list[VGroup] = []
    whole: list = []
    for root in roots:
        w, h = root.width, root.height
        if w < 0.08 or h < 0.08:
            whole.append(root)
            shards.append(None)
            continue
        color = root.get_color()
        ncols = max(2, min(22, int(w / 0.22)))
        nrows = max(2, min(8, int(h / 0.22) + 1))
        cell_w, cell_h = w / ncols, h / nrows
        left, bottom = root.get_left()[0], root.get_bottom()[1]
        grid = VGroup()
        for i in range(ncols):
            for j in range(nrows):
                cell = Rectangle(width=cell_w * 1.08, height=cell_h * 1.08,
                                 fill_color=color, fill_opacity=0.95,
                                 stroke_width=0)
                cell.move_to(np.array([left + cell_w * (i + 0.5),
                                       bottom + cell_h * (j + 0.5), 0]))
                grid.add(cell)
        shards.append(grid)
    appear = [root.animate.set_opacity(0) for root in roots]
    appear += [g.animate.set_opacity(1.0) for g in shards if g is not None]
    if appear:
        scene.play(*appear, run_time=0.25 * run_time, rate_func=smooth)
    fly = []
    for grid in shards:
        if grid is None:
            continue
        for cell in grid:
            vx = rng.uniform(-1.1, 1.1)
            vy = rng.uniform(-1.0, 0.6) - 0.15
            fly.append(cell.animate.shift(np.array([vx, vy, 0])).set_opacity(0))
    for root in whole:
        fly.append(root.animate.shift(DOWN * 0.6).set_opacity(0))
    if fly:
        scene.play(*fly, run_time=0.75 * run_time, rate_func=smooth)
    scene.remove(*roots, *[g for g in shards if g is not None])


# ---------------- S1 开场钩子：显存被谁吃了 ----------------
class S1(_Base):
    def construct(self):
        self.bg()
        footer = _footer(self)
        head = _header("显存，被谁吃掉了？")

        # 页 1：4090 + 权重 4GB（静态）
        gpu = _block(("RTX 4090", "24GB 显存"), 62, CYAN, "BOLD", 44)
        weight = _block(("7B 模型 · 4-bit", "模型权重只占 4GB 多"), 52, WHITE, "BOLD", 38)
        line = _fit(t("模型权重加载完，就不动了", 46, WHITE, "BOLD"))
        page1 = _page(gpu, weight, line, buff=1.95)
        note0 = t("以 DeepSeek-V3 为例", 24, MUTED).next_to(head, DOWN, buff=0.5)

        self.at_clip("s1-c01")
        _reveal_title(self, head, 0.7)
        self.play(FadeIn(note0, shift=DOWN * 0.05), run_time=0.4)
        self.at_clip("s1-c02")
        _reveal(self, gpu, 0.62)
        self.at_clip("s1-c03")
        _reveal(self, weight, 0.62)
        self.at_clip("s1-c05")
        _reveal(self, line, 0.62)

        # 页 2：论文拖入 → OOM
        pdf = _block(("30 页 PDF", "切完 ≈2.5 万 token"), 72, GREEN, "BOLD", 52)
        oom = _label("聊了没几轮，OOM！", 96, RED, "BOLD")
        page2 = _page(pdf, oom, buff=4.6)
        self.at_clip("s1-c06")
        _clear(self, page1)
        _reveal_title(self, pdf, 0.6)
        self.at_clip("s1-c07")
        _reveal(self, oom, 0.62)
        self.at_clip("s1-c08")
        self.emphasize(oom, mode="circumscribe", color=RED, run_time=0.55)

        # 页 3：权重条静止 + KV 条匀速涨（grow 主视觉）
        kv_line = _fit(t("显存却在匀速涨，每多一句 +几十 MB", 42, WHITE, "BOLD"))
        kv_lab = _label("KV 缓存（在长）", 40, YELL, "BOLD")
        kv_bar = Rectangle(width=0.4, height=1.6, color=YELL,
                           fill_color=YELL, fill_opacity=0.55)
        question = _label("什么东西在长？", 64, YELL, "BOLD")
        page3 = _page(kv_line, kv_lab, kv_bar, question, buff=1.4)
        self.at_clip("s1-c09")
        _clear(self, page2)
        _reveal(self, kv_line, 0.7)
        self.at_clip("s1-c10")
        _reveal(self, kv_lab, 0.5)
        self.grow_bar(kv_bar, ValueTracker(0.1), 3.6, run_time=3.0, anchor="center")
        self.at_clip("s1-c11")
        _reveal(self, question, 0.7)
        self.wait(1.0)
        _dissolve(self, head, footer, page3, note0)
        self.pad_to_voice()


# ---------------- S2 KV 缓存：阅读笔记 ----------------
class S2(_Base):
    def construct(self):
        self.bg()
        footer = _footer(self)
        head = _header("KV 缓存：模型的阅读笔记")

        # 页 1：定义 + 10GB 对比（grow 主视觉）
        line1 = _label("7B 模型 · 2.5 万上下文", 60, WHITE, "BOLD")
        line2 = _label("KV 缓存涨到 10GB — 比模型大一倍多", 48, YELL, "BOLD")
        bar_w = Rectangle(width=0, height=1.8, color=CYAN,
                          fill_color=CYAN, fill_opacity=0.3)
        page1 = _page(line1, line2, bar_w, buff=2.2)
        self.at_clip("s2-c01")
        _reveal_title(self, head, 0.7)
        self.at_clip("s2-c02")
        _reveal(self, line1)
        self.at_clip("s2-c04")
        _reveal(self, line2, 0.7)
        self.at_clip("s2-c05")
        self.grow_bar(bar_w, ValueTracker(0.1), 3.6, run_time=1.65, anchor="center")

        # 页 2：四因子公式（乘在一起）
        title2 = _label("体量 = 四件事，全乘在一起", 56, WHITE, "BOLD")
        f1 = _card("层数", 1.45, 2.3, CYAN, WHITE, 36)
        f2 = _card("上下文长度", 1.45, 2.3, GREEN, WHITE, 36)
        f3 = _card("KV 头数", 1.45, 2.3, YELL, WHITE, 36)
        f4 = _card("每头维度", 1.45, 2.3, CYAN, WHITE, 36)
        cards = [f1, f2, f3, f4]
        with_x = VGroup()
        mul_signs = []
        for i, c in enumerate(cards):
            with_x.add(c)
            if i < 3:
                m = t("×", 24, MUTED, "BOLD")
                mul_signs.append(m)
                with_x.add(m)
        with_x.arrange(RIGHT, buff=0.15)
        foot2 = _label("一个都绕不过去", 44, YELL, "BOLD")
        page2 = _page(title2, with_x, foot2, buff=1.9)
        self.at_clip("s2-c06")
        _clear(self, page1)
        _reveal(self, title2, 0.6)
        self.at_clip("s2-c07")
        self.play_scroll_unroll_many(*cards, run_time=1.2)
        self.at_clip("s2-c08")
        self.play_parallel(FadeIn(VGroup(*mul_signs), run_time=0.4),
                           type_in(foot2, 0.5), run_time=0.5)

        # 页 3：线性增长 32K → 128K 翻 4 倍（grow 主视觉）
        title3 = _label("线性增长：32K → 128K，缓存翻 4 倍", 50, WHITE, "BOLD")
        bar_heights = [1.6, 2.0, 2.4, 2.8]
        bars = VGroup(*[Rectangle(width=0.9, height=h, color=GREEN,
                                  fill_color=GREEN, fill_opacity=0.35)
                        for h in bar_heights])
        bars.arrange(RIGHT, buff=0.7)
        labels3 = VGroup(*[t(lab, 26, MUTED, "BOLD") for lab in ["32K", "64K", "96K", "128K"]])
        for lb, bar in zip(labels3, bars):
            lb.next_to(bar, DOWN, buff=0.3)
        page3 = _page(title3, bars, labels3, buff=1.7)
        self.at_clip("s2-c09")
        _clear(self, page2)
        _reveal(self, title3, 0.7)
        self.at_clip("s2-c10")
        for b in bars:
            self.grow_bar(b, ValueTracker(0.1), 0.9, run_time=0.6)
        self.at_clip("s2-c11")
        self.play(FadeIn(labels3, shift=UP * 0.05), run_time=0.4)

        # 页 4：权重没涨，显存见底 + 除非砍一个数
        w1 = _label("权重一个字没涨", 60, WHITE, "BOLD")
        w2 = _label("显存却见底了", 72, RED, "BOLD")
        w3 = _label("除非——砍掉一个数", 80, YELL, "BOLD")
        page4 = _page(w1, w2, w3, buff=2.2)
        self.at_clip("s2-c12")
        _clear(self, page3)
        self.play_parallel(type_in(w1, 0.6), type_in(w2, 0.6), run_time=0.6)
        self.at_clip("s2-c13")
        _reveal(self, w3, 0.8)
        self.emphasize(w3, mode="circumscribe", color=YELL, run_time=0.55)
        self.wait(1.0)
        _dissolve(self, head, footer, page4)
        self.pad_to_voice()


# ---------------- S3 便利贴直觉：GQA vs MLA ----------------
class S3(_Base):
    def construct(self):
        self.bg()
        footer = _footer(self)
        head = _header("实习生与 200 张便利贴")

        # 页 1：便利贴墙概念图（主视觉插图）
        img = _image("s3-notes-round.png", 5.4)
        cap = _label("一小时，墙上 200 张", 40, WHITE, "BOLD")
        page1 = _page(img, cap, buff=1.1)
        self.at_clip("s3-c01")
        _reveal_title(self, head, 0.7)
        self.at_clip("s3-c02")
        self.play(FadeIn(img, shift=DOWN * 0.05), run_time=0.8)
        self.at_clip("s3-c03")
        _reveal(self, cap, 0.6)

        # 页 2：老板提问（问句爆点）
        q = _label("老板问：第一分钟，老张说了什么？", 58, YELL, "BOLD")
        a = _label("你翻了半天才找到——找的过程比会还长", 40, WHITE, "BOLD")
        page2 = _page(q, a, buff=6.1)
        self.at_clip("s3-c04")
        _clear(self, page1)
        _reveal(self, q, 0.7)
        self.at_clip("s3-c05")
        _reveal(self, a, 0.7)

        # 页 3：GQA vs 真正想要的
        gqa = _card("GQA：少雇几个人，共用一份记录", 6.6, 2.2, GREEN, WHITE, 30)
        want = _card("你真正想要的：每张便利贴只写一行关键词", 6.6, 2.2, YELL, WHITE, 30)
        page3 = _page(gqa, want, buff=3.1)
        self.at_clip("s3-c06")
        _clear(self, page2, run_time=0.22)
        self.at_clip("s3-c07")
        self.play_scroll_unroll(gqa, run_time=0.9)
        self.at_clip("s3-c09")
        self.play_scroll_unroll(want, run_time=1.0)
        self.wait(0.6)
        self.emphasize(want, mode="circumscribe", color=YELL, run_time=0.55)

        # 页 4：MLA 直觉（收尾）
        line1 = _label("这就是 MLA 的直觉", 56, WHITE, "BOLD")
        line2 = _block(("GQA：少记几份笔记", "MLA：把笔记写得更短"),
                       52, CYAN, "BOLD", 44, GREEN)
        page4 = _page(line1, line2, buff=4.9)
        self.at_clip("s3-c10")
        _clear(self, page3)
        _reveal(self, line1, 0.7)
        self.at_clip("s3-c11")
        _reveal(self, line2, 0.8)
        self.wait(1.2)
        _dissolve(self, head, footer, page4)
        self.pad_to_voice()


# ---------------- S4 MLA 三步 ----------------
class S4(_Base):
    def construct(self):
        self.bg()
        footer = _footer(self)
        head = _header("MLA 三步")

        # 页 1：第一步 摘要（512 维，counter 主视觉）
        step1 = _label("① 写摘要：K、V → 512 维小向量", 46, YELL, "BOLD")
        note = _label("不是随便删——是训练学出来的", 34, MUTED)
        slot = dynamic_slot(2.2, 1.0)
        page1 = _page(step1, slot, note, buff=2.6)
        self.at_clip("s4-c01")
        _reveal_title(self, head, 0.7)
        self.at_clip("s4-c02")
        _reveal(self, step1, 0.7)
        self.at_clip("s4-c03")
        num512 = self.counter_value(0, 512, suffix=" 维", size=64, color=YELL,
                                    run_time=1.2, anchor=slot)
        self.at_clip("s4-c04")
        _reveal(self, note, 0.6)

        # 页 2：第二步 改写提问（转折）
        step2 = _label("② 不解压，改写提问方式", 50, GREEN, "BOLD")
        q = _label("我卡了三天：摘要不还原，怎么算？", 50, WHITE, "BOLD")
        page2 = _page(step2, q, buff=5.8)
        self.at_clip("s4-c05")
        _clear(self, page1, num512)
        _reveal(self, step2, 0.7)
        self.at_clip("s4-c06")
        _reveal(self, q, 0.8)

        # 页 3：矩阵结合律（核心，主视觉公式）
        title = _label("矩阵结合律：一行搞定", 44, YELL, "BOLD")
        f1 = MathTex(r"Q^T \cdot (W^{UK} \cdot c^{KV})", color=WHITE)
        f2 = MathTex(r"= (Q^T \cdot W^{UK}) \cdot c^{KV}", color=WHITE)
        formula = VGroup(f1, f2).arrange(DOWN, buff=0.6)
        res = _label("结果一模一样", 48, GREEN, "BOLD")
        page3 = _page(title, formula, res, buff=2.2)
        self.at_clip("s4-c07")
        _clear(self, page2)
        _reveal(self, title, 0.6)
        self.at_clip("s4-c08")
        self.play(FadeIn(f1), run_time=0.8)
        self.at_clip("s4-c09")
        self.play_parallel(FadeIn(f2, run_time=0.8), type_in(res, 0.6), run_time=0.8)
        self.at_clip("s4-c10")
        self.emphasize(res, mode="circumscribe", color=GREEN, run_time=0.55)
        self.wait(1.0)

        # 页 4：第三步 RoPE 解耦
        step3 = _label("③ 位置单独记：RoPE 走独立通道", 44, CYAN, "BOLD")
        c1 = _label("内容：cᴷⱽ（摘要）", 38, WHITE, "BOLD")
        c2 = _label("位置：RoPE key（索引卡）", 38, WHITE, "BOLD")
        page4 = _page(step3, c1, c2, buff=2.9)
        self.at_clip("s4-c11")
        _clear(self, page3)
        _reveal(self, step3, 0.7)
        self.at_clip("s4-c12")
        _reveal(self, c1, 0.6)
        self.at_clip("s4-c13")
        _reveal(self, c2, 0.6)
        self.wait(1.0)
        _dissolve(self, head, footer, page4)
        self.pad_to_voice()


# ---------------- S5 省 90% ----------------
class S5(_Base):
    def construct(self):
        self.bg()
        footer = _footer(self)
        head = _header("省 90%：到底怎么比的？")

        # 页 1：对照实验
        note = _label("DeepSeek 论文：同架构，只换注意力", 46, WHITE, "BOLD")
        vs = _label("MHA vs MLA", 64, YELL, "BOLD")
        page1 = _page(note, vs, buff=5.9)
        self.at_clip("s5-c01")
        _reveal_title(self, head, 0.7)
        self.at_clip("s5-c02")
        _reveal(self, note, 0.7)
        self.at_clip("s5-c03")
        _reveal(self, vs, 0.7)

        # 页 2：小规模 110.6K → 15.6K（14%，counter 动效）
        t2 = _label("小规模模型", 34, WHITE, "BOLD")
        lab1 = _label("MHA 每 token", 40, CYAN, "BOLD")
        num1 = dynamic_slot(3.0, 0.9)
        lab2 = _label("MLA 每 token", 40, GREEN, "BOLD")
        num2 = dynamic_slot(3.0, 0.9)
        page2 = _page(t2, lab1, num1, lab2, num2, buff=1.3)
        self.at_clip("s5-c04")
        _clear(self, page1)
        self.play_parallel(type_in(t2, 0.4), type_in(lab1, 0.6), run_time=0.6)
        cnt1 = self.counter_value(0, 110.6, suffix="K 元素", decimals=1, size=56, color=CYAN,
                                  run_time=1.4, anchor=num1)
        self.at_clip("s5-c05")
        _reveal(self, lab2, 0.6)
        cnt2 = self.counter_value(0, 15.6, suffix="K 元素 — 14%", decimals=1, size=56, color=GREEN,
                                  run_time=1.4, anchor=num2)

        # 页 3：大规模 86 万 → 3.4 万（4%，counter 动效）
        t3 = _label("更大规模模型", 34, WHITE, "BOLD")
        lab3 = _label("MHA 每 token", 40, CYAN, "BOLD")
        num3 = dynamic_slot(3.0, 0.9)
        lab4 = _label("MLA 每 token", 40, RED, "BOLD")
        num4 = dynamic_slot(3.0, 0.9)
        page3 = _page(t3, lab3, num3, lab4, num4, buff=1.3)
        self.at_clip("s5-c06")
        _clear(self, page2, cnt1, cnt2, run_time=0.2)
        self.play_parallel(type_in(t3, 0.4), type_in(lab3, 0.5), run_time=0.5)
        cnt3 = self.counter_value(0, 860.2, suffix="K 元素", decimals=1, size=56, color=CYAN,
                                  run_time=0.7, anchor=num3)
        self.at_clip("s5-c07")
        _reveal(self, lab4, 0.5)
        cnt4 = self.counter_value(0, 34.6, suffix="K 元素 — 只剩 4%", decimals=1, size=56, color=RED,
                                  run_time=0.8, anchor=num4)

        # 页 4：90% 通俗说法 + 省的是 KV 缓存
        p41 = _label("90% 是通俗说法", 50, WHITE, "BOLD")
        p42 = _label("省的是 KV 缓存这笔账，不是全部显存", 54, YELL, "BOLD")
        page4 = _page(p41, p42, buff=6.0)
        self.at_clip("s5-c09")
        _clear(self, page3, cnt3, cnt4)
        _reveal(self, p41, 0.6)
        self.at_clip("s5-c10")
        _reveal(self, p42, 0.8)
        self.at_clip("s5-c12")
        self.emphasize(p42, mode="circumscribe", color=YELL, run_time=0.55)

        # 页 5：JL 引理（概念图）
        img = _image("s5-jl-round.png", 5.44)
        cap = _label("高维点投到低维：坐标丢，距离关系在", 36, WHITE, "BOLD")
        page5 = _page(img, cap, buff=1.15)
        self.at_clip("s5-c13")
        _clear(self, page4)
        self.play(FadeIn(img, shift=DOWN * 0.05), run_time=0.8)
        self.at_clip("s5-c14")
        _reveal(self, cap, 0.7)

        # 页 6：三页提纲（比喻收尾）
        line61 = _label("就像考前，把教材压成三页提纲", 48, WHITE, "BOLD")
        line62 = _label("练出来的提纲，比逐页翻书好用", 40, MUTED, "BOLD")
        page6 = _page(line61, line62, buff=6.0)
        self.at_clip("s5-c16")
        _clear(self, page5)
        _reveal(self, line61, 0.7)
        _reveal(self, line62, 0.6)
        self.wait(0.9)
        _dissolve(self, head, footer, page6)
        self.pad_to_voice()


# ---------------- S6 回到显存账 + 尾卡 ----------------
class S6(_Base):
    def construct(self):
        self.bg()
        footer = _footer(self)
        head = _header("回到显存这笔账")

        # 页 1：三卡总结
        c1 = _card("低秩摘要：只存 512 维", 6.0, 1.6, CYAN, WHITE, 30)
        c2 = _card("矩阵吸收：不还原就提问", 6.0, 1.6, GREEN, WHITE, 30)
        c3 = _card("解耦 RoPE：位置单独记", 6.0, 1.6, YELL, WHITE, 30)
        page1 = _page(c1, c2, c3, buff=1.2)
        self.at_clip("s6-c01")
        _reveal_title(self, head, 0.7)
        self.at_clip("s6-c02")
        self.play_scroll_unroll(c1, run_time=1.0)
        self.at_clip("s6-c03")
        self.play_scroll_unroll(c2, run_time=1.0)
        self.at_clip("s6-c04")
        self.play_scroll_unroll(c3, run_time=1.0)
        self.wait(1.2)

        # 页 2：三问（互动铺垫）
        q1 = _label("下次看到 128K 上下文：", 48, WHITE, "BOLD")
        q2 = _label("每个 token 留下多少 KV 缓存？", 50, YELL, "BOLD")
        q3 = _label("MHA、GQA，还是 MLA？", 42, CYAN, "BOLD")
        page2 = _page(q1, q2, q3, buff=2.6)
        self.at_clip("s6-c05")
        _clear(self, page1)
        _reveal(self, q1, 0.7)
        self.at_clip("s6-c06")
        _reveal(self, q2, 0.8)
        self.at_clip("s6-c07")
        _reveal(self, q3, 0.7)

        # 页 3：互动问题 + 预告 + 尾卡
        q4 = _label("你愿意为长上下文多买显存，", 40, WHITE, "BOLD")
        q5 = _label("还是接受记忆压成摘要？", 40, WHITE, "BOLD")
        discuss = _label("评论区聊聊！", 58, YELL, "BOLD")
        page3 = _page(q4, q5, discuss, buff=2.7)
        self.at_clip("s6-c08")
        _clear(self, page2)
        _reveal(self, q4, 0.8)
        self.at_clip("s6-c09")
        _reveal(self, q5, 0.8)
        self.at_clip("s6-c10")
        _reveal(self, discuss, 0.8)
        self.wait(0.3)

        # 尾卡
        avatar = ImageMobject(str(ROOT / "avatar-sjai-round.png"))
        avatar.scale_to_fit_width(3.6)
        follow = _label("关注「数解AI」", 46, YELL, "BOLD")
        t_title = _fit(t("《显存被谁吃掉了？DeepSeek如何省下90%》", 28, WHITE, "BOLD"), 7.4)
        guide = _label("下一篇：存放知识的 FFN", 34, GREEN, "BOLD")
        page4 = _page(avatar, follow, t_title, guide, buff=1.3)
        self.at_clip("s6-c11")
        _clear(self, page3, head, footer)
        self.play(FadeIn(avatar, scale=1.5), run_time=0.8)
        self.at_clip("s6-c12")
        _reveal(self, follow, 0.7)
        _reveal(self, t_title, 0.7)
        _reveal(self, guide, 0.7)
        self.wait(1.6)
        self.pad_to_voice()
