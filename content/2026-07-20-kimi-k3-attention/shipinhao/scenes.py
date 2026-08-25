#!/usr/bin/env python3
"""《Kimi K3：KDA怎么撑住1M上下文？》视频号场景（MiniMax 内置男声版 2026-08-26）。

- 6 个场景 S1-S6，与 storyboard.md 一一对应（同 07-21 MLA 款）
- 配音：MiniMax 内置男声 male-qn-jingying，speed 1.0 pitch +2
- 时间轴锚点 = tts/sentence-boundaries.json 的 clip id（at_clip 精确挂接，标点级 clip）
- 动画降噪：每页 1 个主视觉动效，其余静态 type_in/scroll_unroll 入场
- 概念图：img/s1-agent-round.png、s3-stenographer-round.png（AI 图禁数字）
- 数字全部脚本画图（grow_bar / counter_value）
- 结尾：品牌尾卡含公众号文章引导（当期文章标题 + 查看公众号文章 · 图文全解）
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

# ffprobe tts/s1.wav ... tts/s6.wav（内置男声 male-qn-jingying，speed 1.0 pitch +2）
VOICE_DUR = {
    "S1": 27.05,
    "S2": 30.29,
    "S3": 39.68,
    "S4": 34.39,
    "S5": 40.11,
    "S6": 40.70,
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
    rng = np.random.default_rng(20260720)
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
            fly.append(cell.animate.shift((vx, vy, 0)).set_opacity(0))
    for root in whole:
        fly.append(root.animate.shift(DOWN * 0.6).set_opacity(0))
    if fly:
        scene.play(*fly, run_time=0.75 * run_time, rate_func=smooth)
    scene.remove(*roots, *[g for g in shards if g is not None])


# ---------------- S1 开场钩子：1M 难的不是塞进去 ----------------
class S1(_Base):
    def construct(self):
        self.bg()
        footer = _footer(self)
        head = _header("Kimi K3：1M 上下文")

        # 页 1：数字卡 + 核心句（counter 主视觉）
        num1 = dynamic_slot(2.6, 1.0)
        num2 = dynamic_slot(2.6, 1.0)
        core = _label("难的不是塞进去，而是又快又准地用起来", 44, YELL, "BOLD")
        page1 = _page(num1, num2, core, buff=6.4)
        note0 = t("本片以 Kimi K3 为例", 24, MUTED).next_to(head, DOWN, buff=0.5)
        self.at_clip("s1-c01")
        self.play_parallel(type_in(head, 0.7), FadeIn(note0, shift=DOWN * 0.05),
                           run_time=0.7)
        self.at_clip("s1-c02")
        cnt1 = self.counter_value(0, 2.8, suffix="T 参数", decimals=1, size=58, color=CYAN,
                                  run_time=1.1, anchor=num1)
        self.at_clip("s1-c03")
        cnt2 = self.counter_value(0, 1, suffix="M token 上下文", size=58, color=GREEN,
                                  run_time=1.1, anchor=num2)
        self.at_clip("s1-c06")
        _reveal(self, core, 0.8)

        # 页 2：Agent 读完代码仓库（概念图主视觉）
        img = _image("s1-agent-round.png", 5.0)
        q = _label("还记得一开始那条「不能动支付接口」的约束吗？", 40, YELL, "BOLD")
        page2 = _page(img, q, buff=6.4)
        self.at_clip("s1-c08")
        _clear(self, page1, cnt1, cnt2)
        self.play(FadeIn(img, shift=DOWN * 0.05), run_time=0.8)
        self.at_clip("s1-c12")
        _reveal(self, q, 0.9)

        # 页 3：两难（收尾爆点）
        p31 = _label("不能每次把一百万 token 从头翻到尾", 44, WHITE, "BOLD")
        p32 = _label("也不能为了快，把要命的约束忘掉", 44, RED, "BOLD")
        page3 = page_auto(p31, p32)
        self.at_clip("s1-c13")
        _clear(self, page2)
        _reveal(self, p31, 0.8)
        self.at_clip("s1-c14")
        _reveal(self, p32, 0.8)
        self.wait(1.0)
        _dissolve(self, head, footer, page3, note0)
        self.pad_to_voice()


# ---------------- S2 两道墙：KV 缓存 + O(T²) ----------------
class S2(_Base):
    def construct(self):
        self.bg()
        footer = _footer(self)
        head = _header("长历史的两道墙")

        # 页 1：KV 缓存定义（先澄清误解）
        line1 = _label("新 token：旧 K、V 不重算，存进 KV 缓存", 48, WHITE, "BOLD")
        line2 = _label("省了重做旧题，没省掉查完整段历史", 44, YELL, "BOLD")
        page1 = page_auto(line1, line2)
        self.at_clip("s2-c01")
        _reveal_title(self, head, 0.7)
        self.at_clip("s2-c02")
        _reveal(self, line1, 0.8)
        self.at_clip("s2-c04")
        _reveal(self, line2, 0.8)

        # 页 2：10 万 → 100 万，查询多 10 倍（grow 主视觉）
        t2 = _label("历史 10 万 → 100 万 token", 46, WHITE, "BOLD")
        lab2 = _label("每次查询要面对的历史位置", 38, MUTED, "BOLD")
        bar_w = Rectangle(width=0, height=1.8, color=GREEN,
                          fill_color=GREEN, fill_opacity=0.35)
        num10 = _label("10 倍", 56, GREEN, "BOLD")
        page2 = _page(t2, lab2, bar_w, num10, buff=1.4)
        self.at_clip("s2-c07")
        _clear(self, page1)
        _reveal(self, t2, 0.7)
        self.at_clip("s2-c08")
        _reveal(self, lab2, 0.6)
        self.at_clip("s2-c09")
        self.grow_bar(bar_w, ValueTracker(0.1), 3.6, run_time=1.2, anchor="center",
                      extra_anims=[type_in(num10, 0.8)])

        # 页 3：预填充配对 100 倍 + O(T²) 墙（数字对比爆点）
        t3 = _label("预填充：位置两两配对", 46, WHITE, "BOLD")
        f1 = _label("长度翻 10 倍", 44, CYAN, "BOLD")
        arrow = t("→", 40, MUTED, "BOLD")
        lab100 = _label("配对工作量翻 ", 44, RED, "BOLD")
        slot100 = dynamic_slot(2.0, 1.0)
        row = VGroup(f1, arrow, lab100, slot100).arrange(RIGHT, buff=0.35)
        wall = _label("这就是 O(T²) 的墙", 60, YELL, "BOLD")
        page3 = _page(t3, row, wall, buff=6.4)
        self.at_clip("s2-c10")
        _clear(self, page2)
        _reveal(self, t3, 0.7)
        self.at_clip("s2-c14")
        self.play_parallel(type_in(f1, 0.6), type_in(arrow, 0.4), type_in(lab100, 0.6),
                           run_time=0.7)
        self.at_clip("s2-c15")
        cnt100 = self.counter_value(0, 100, suffix=" 倍", size=52, color=RED,
                                    run_time=1.2, anchor=slot100)
        self.at_clip("s2-c16")
        _reveal(self, wall, 0.9)
        self.emphasize(wall, mode="circumscribe", color=YELL, run_time=0.6)
        self.wait(0.5)
        _dissolve(self, head, footer, page3, cnt100)
        self.pad_to_voice()


# ---------------- S3 线性注意力：会议速记 ----------------
class S3(_Base):
    def construct(self):
        self.bg()
        footer = _footer(self)
        head = _header("线性注意力：别翻录音，写速记")

        # 页 1：固定大小的状态（定义）
        line1 = _label("不逐页翻历史，维护一个固定大小的状态", 46, WHITE, "BOLD")
        line2 = _label("读到新 token → 更新状态；下一个直接读状态", 44, GREEN, "BOLD")
        page1 = page_auto(line1, line2)
        self.at_clip("s3-c01")
        _reveal_title(self, head, 0.7)
        self.at_clip("s3-c02")
        _reveal(self, line1, 0.8)
        self.at_clip("s3-c04")
        _reveal(self, line2, 0.9)

        # 页 2：录音 vs 速记员概念图（主视觉插图）
        img = _image("s3-stenographer-round.png", 5.2)
        cap = _label("还是那场会：录音回放 → 速记员持续写笔记", 36, WHITE, "BOLD")
        page2 = _page(img, cap, buff=1.8)
        self.at_clip("s3-c07")
        _clear(self, page1)
        self.play(FadeIn(img, shift=DOWN * 0.05), run_time=0.8)
        self.at_clip("s3-c10")
        _reveal(self, cap, 0.7)

        # 页 3：10 分钟 → 100 分钟只延长 10 倍（counter 主视觉）
        t3 = _label("会议 10 分钟 → 100 分钟", 52, WHITE, "BOLD")
        slot = dynamic_slot(3.0, 1.0)
        note3 = _label("速记工作量只延长 10 倍", 42, YELL, "BOLD")
        page3 = _page(t3, slot, note3, buff=6.4)
        self.at_clip("s3-c13")
        _clear(self, page2)
        _reveal(self, t3, 0.7)
        self.at_clip("s3-c14")
        cnt3 = self.counter_value(0, 10, suffix=" 倍", size=64, color=YELL,
                                  run_time=1.2, anchor=slot)
        self.at_clip("s3-c15")
        _reveal(self, note3, 0.7)
        self.wait(0.5)

        # 页 4：KDA = Delta（门控）
        k1 = _label("KDA 的关键词：Delta（变化量）", 52, CYAN, "BOLD")
        k2 = _label("新信息 = 「对已有记忆做多少修改」", 42, WHITE, "BOLD")
        k3 = _label("门控决定：保留 / 衰减 / 放大", 42, GREEN, "BOLD")
        page4 = page_auto(k1, k2, k3)
        self.at_clip("s3-c17")
        _clear(self, page3, cnt3)
        _reveal(self, k1, 0.7)
        self.at_clip("s3-c18")
        _reveal(self, k2, 0.8)
        self.at_clip("s3-c19")
        _reveal(self, k3, 0.8)
        self.wait(0.6)
        _dissolve(self, head, footer, page4)
        self.pad_to_voice()


# ---------------- S4 速记会漏：有限状态的取舍 ----------------
class S4(_Base):
    def construct(self):
        self.bg()
        footer = _footer(self)
        head = _header("但只靠速记，会漏")

        # 页 1：转折爆点
        q = _label("速记会不会漏掉关键原话？", 56, YELL, "BOLD")
        a = _label("会——所有有限状态记忆的取舍", 44, WHITE, "BOLD")
        page1 = page_auto(q, a)
        self.at_clip("s4-c01")
        _reveal_title(self, head, 0.7)
        self.at_clip("s4-c02")
        _reveal(self, q, 0.8)
        self.at_clip("s4-c04")
        _reveal(self, a, 0.8)

        # 页 2：速记 vs 原话（原话高亮爆点）
        note = _label("会议里大部分内容，写成…", 34, MUTED, "BOLD")
        card1 = _card("速记：决定采用方案 A，风险由小王评估", 6.8, 1.6, CYAN, WHITE, 28)
        card2 = _card("原话：方案 A 可以用，但支付接口绝对不能改", 6.8, 1.6, RED, WHITE, 28)
        page2 = _page(note, card1, card2, buff=6.4)
        self.at_clip("s4-c05")
        _clear(self, page1)
        _reveal(self, note, 0.6)
        self.at_clip("s4-c06")
        self.play_scroll_unroll(card1, run_time=0.9)
        self.at_clip("s4-c10")
        self.play_scroll_unroll(card2, run_time=1.0)
        self.emphasize(card2, mode="circumscribe", color=RED, run_time=0.6)

        # 页 3：后果对比
        c1 = _label("闲聊：小误差", 40, GREEN, "BOLD")
        c2 = _label("长程编程 / 合同审阅：可能改变结果", 42, RED, "BOLD")
        page3 = page_auto(c1, c2)
        self.at_clip("s4-c13")
        _clear(self, page2)
        _reveal(self, c1, 0.7)
        self.at_clip("s4-c16")
        _reveal(self, c2, 0.8)
        self.wait(0.7)
        _dissolve(self, head, footer, page3)
        self.pad_to_voice()


# ---------------- S5 KDA 的答案：3 次速记 + 1 次全局回看 ----------------
class S5(_Base):
    def construct(self):
        self.bg()
        footer = _footer(self)
        head = _header("KDA 的答案：分工")

        # 页 1：引出（不是所有层都当速记员）
        p1a = _label("不是所有注意力层", 52, WHITE, "BOLD")
        p1b = _label("都只当速记员", 64, YELL, "BOLD")
        page1 = page_auto(p1a, p1b)
        self.at_clip("s5-c01")
        _reveal_title(self, head, 0.7)
        _reveal(self, p1a, 0.7)
        self.at_clip("s5-c02")
        _reveal(self, p1b, 0.8)

        # 页 2：3:1 层结构图（Create 逐段主视觉）
        t2 = _label("3 个 KDA 层 + 1 个全局注意力层", 46, YELL, "BOLD")
        blocks = [_block(["KDA", "速记"], 40, CYAN, "BOLD", 24),
                  _block(["KDA", "速记"], 40, CYAN, "BOLD", 24),
                  _block(["KDA", "速记"], 40, CYAN, "BOLD", 24),
                  _block(["全局注意力", "回看"], 34, GREEN, "BOLD", 24)]
        row = VGroup(*blocks).arrange(RIGHT, buff=0.5)
        loop = _label("→ 重复", 36, MUTED, "BOLD")
        page2 = _page(t2, row, loop, buff=3.2)
        self.at_clip("s5-c03")
        _clear(self, page1)
        _reveal(self, t2, 0.6)
        self.at_clip("s5-c04")
        self.play(FadeIn(blocks[0], shift=UP * 0.1), run_time=0.5)
        self.at_clip("s5-c05")
        self.play(FadeIn(blocks[1], shift=UP * 0.1), run_time=0.5)
        self.at_clip("s5-c07")
        self.play(FadeIn(blocks[2], shift=UP * 0.1), run_time=0.5)
        self.at_clip("s5-c10")
        self.play(FadeIn(blocks[3], shift=UP * 0.1), run_time=0.5)
        self.at_clip("s5-c11")
        _reveal(self, loop, 0.6)

        # 页 3：分工说明
        p3 = _label("速记：让会议继续开下去", 44, CYAN, "BOLD")
        p4 = _label("全局回看：必要时重建精确联系", 44, GREEN, "BOLD")
        page3 = page_auto(p3, p4)
        self.at_clip("s5-c12")
        _clear(self, page2)
        _reveal(self, p3, 0.8)
        self.at_clip("s5-c14")
        _reveal(self, p4, 0.8)

        # 页 4：口径（爆点）
        c1 = _label("注意一个口径：", 40, WHITE, "BOLD")
        c2 = _label("K3 未披露层级配比；3:1 来自 Kimi Linear 公开架构", 40, YELL, "BOLD")
        page4 = page_auto(c1, c2)
        self.at_clip("s5-c16")
        _clear(self, page3)
        _reveal(self, c1, 0.7)
        self.at_clip("s5-c18")
        _reveal(self, c2, 0.9)
        self.emphasize(c2, mode="circumscribe", color=YELL, run_time=0.6)
        self.wait(1.2)
        _dissolve(self, head, footer, page4)
        self.pad_to_voice()


# ---------------- S6 总结 + 互动 + 公众号引导 + 尾卡 ----------------
class S6(_Base):
    def construct(self):
        self.bg()
        footer = _footer(self)
        head = _header("KDA 不是更快的摘要器")

        # 页 1：总结 + 2.8T 澄清
        c1 = _card("分工：多数时候快速整理", 6.4, 1.6, CYAN, WHITE, 32)
        c2 = _card("关键时刻仍能全局回看", 6.4, 1.6, GREEN, WHITE, 32)
        note = _label("2.8T 参数不是原因——上下文长度才是", 36, MUTED, "BOLD")
        page = _page(c1, c2, note, buff=6.4)
        self.at_clip("s6-c01")
        _reveal_title(self, head, 0.7)
        self.at_clip("s6-c02")
        self.play_scroll_unroll(c1, run_time=0.9)
        self.at_clip("s6-c04")
        self.play_scroll_unroll(c2, run_time=0.9)
        self.at_clip("s6-c05")
        _reveal(self, note, 0.7)

        # 页 2：互动问题
        q1 = _label("你会多留几层做全局回看，", 44, WHITE, "BOLD")
        q2 = _label("还是把更多层交给会议速记？", 44, YELL, "BOLD")
        discuss = _label("评论区聊聊！", 52, GREEN, "BOLD")
        page2 = page_auto(q1, q2, discuss)
        self.at_clip("s6-c09")
        _clear(self, page)
        _reveal(self, q1, 0.8)
        self.at_clip("s6-c10")
        _reveal(self, q2, 0.8)
        self.at_clip("s6-c12")
        _reveal(self, discuss, 0.7)

        # 页 3：公众号引导 + 尾卡
        guide1 = _label("完整图文版在公众号「数解AI」", 44, WHITE, "BOLD")
        guide2 = _label("点下方扩展链接查看", 36, GREEN, "BOLD")
        page3 = page_auto(guide1, guide2)
        self.at_clip("s6-c13")
        _clear(self, page2, head, footer)
        _reveal(self, guide1, 0.8)
        self.at_clip("s6-c14")
        _reveal(self, guide2, 0.7)
        self.wait(0.6)

        # 尾卡
        avatar = ImageMobject(str(ROOT / "avatar-sjai-round.png"))
        avatar.scale_to_fit_width(3.4)
        follow = _label("关注「数解AI」", 46, YELL, "BOLD")
        t_title = _fit(t("《Kimi K3：KDA怎么撑住1M上下文？》", 28, WHITE, "BOLD"), 7.4)
        guide = _label("查看公众号文章 · 图文全解", 26, GREEN, "BOLD")
        next_p = _label("下一篇：DeepSeek 的 MLA", 24, MUTED, "BOLD")
        tail = _page(avatar, follow, t_title, guide, next_p, buff=0.9)
        self.at_clip("s6-c15")
        _clear(self, page3)
        self.play(FadeIn(avatar, scale=1.5), run_time=0.8)
        self.at_clip("s6-c18")
        _reveal(self, follow, 0.7)
        _reveal(self, t_title, 0.7)
        _reveal(self, guide, 0.7)
        _reveal(self, next_p, 0.7)
        self.wait(1.5)
        self.pad_to_voice()
