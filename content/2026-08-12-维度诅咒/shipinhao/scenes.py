#!/usr/bin/env python3
"""《高维空间为什么全是壳？内积才是那把尺子》视频号 Manim 动画（竖屏 1080×1920）

6 个场景 S1-S6，与 storyboard.md 一一对应。
- 配音：MiniMax 精英男声（speech-2.8-turbo，speed 1.0 pitch +2）
- 时间轴：at_clip("S1-c01") 挂 tts/sentence-boundaries.json 的 clip 起点（先声音后动画门禁）
- 布局：整页规划（page_stack + layout_page / page_auto），上下留白各 ≤10%
- 动画降噪：每页 1 个主视觉动效；emphasize 全片 5 次；v2 动效 2 处（camera_zoom 成对）
- 段末统一 transition_out（S6 尾卡除外，终幕驻屏）
用法（shipinhao 目录内执行）：
  python3 -m manim render -ql --disable_caching scenes.py S1 S2 S3 S4 S5 S6
  python3 -m manim render -qm --disable_caching scenes.py S1 S2 S3 S4 S5 S6
"""
from __future__ import annotations

import pathlib
import sys


def _scripts_dir() -> str:
    p = pathlib.Path(__file__).resolve().parent
    for _ in range(6):
        cand = p / "scripts"
        if (cand / "manim_helpers.py").exists():
            return str(cand)
        p = p.parent
    raise RuntimeError("找不到 scripts/manim_helpers.py")


sys.path.insert(0, _scripts_dir())
from manim_helpers import *

HERE = pathlib.Path(__file__).resolve().parent
IMG = HERE / "img"
AVATAR = HERE / "avatar-sjai-round.png"

# 每段配音时长（tts_split.py 实测），渲染时长 = 配音 + TAIL
VOICE_DUR = {"S1": 28.65, "S2": 37.29, "S3": 37.33, "S4": 33.58, "S5": 59.7, "S6": 24.69}
TAIL = 2.5


def _footer(self) -> Text:
    f = t("数解AI · 数学直觉", 20, MUTED).to_edge(DOWN, buff=1.15)
    self.add(f)
    return f


def _head(text: str, size: float = 38) -> Text:
    return t(text, size, YELL, "BOLD").to_edge(UP, buff=1.2)


# ---------------- S1 开场钩子：托里拆利小号 ----------------
class S1(_Base):
    def construct(self):
        self.bg()
        f = _footer(self)

        # 页1：概念图 + 标题（c01-c03）
        head = _head("体积有限，表面积却无穷大？", 36)
        img = ImageMobject(str(IMG / "trumpet-round.png"))
        img.scale_to_fit_width(6.0)
        note = t("y = 1/x 绕 x 轴旋转，从 1 转到无穷远", 26, MUTED)
        page1 = page_stack(img, note, buff=1.6)
        layout_page(page1)

        self.at_clip("S1-c01")
        self.play_parallel(type_in(head, run_time=1.1), FadeIn(img, shift=DOWN * 0.05),
                           run_time=1.1)
        self.at_clip("S1-c03")
        self.play(type_in(note, run_time=0.9))
        self.at_clip("S1-c04")

        # 页2：体积 π vs 表面积 ∞ 对比（c04-c07）
        head2 = _head("算出来的两个答案", 40)
        c1 = _card("体积 = π\n一个有限的数", 3.3, 3.6, GREEN, WHITE, 40, CARD_FILL, "BOLD")
        c2 = _card("表面积 = ∞\n无穷大", 3.3, 3.6, RED, WHITE, 40, CARD_FILL, "BOLD")
        cards = VGroup(c1, c2).arrange(RIGHT, buff=0.5)
        big = t("直觉和积分，打架了", 44, YELL, "BOLD")
        sub = t("和高维薄球壳一样，都是反直觉的典型", 28, WHITE)
        page2 = page_stack(cards, big, sub, buff=1.5)
        layout_page(page2)

        self.play(FadeOut(head), FadeOut(img), FadeOut(note),
                  type_in(head2, run_time=0.9), run_time=0.9)
        self.play_scroll_unroll_many(c1, c2, run_time=1.4)  # 主视觉：拉幕
        self.at_clip("S1-c06")
        self.play(type_in(big, run_time=0.9))
        self.at_clip("S1-c07")
        self.play(type_in(sub, run_time=0.9))
        self.at_clip("S1-c08")

        # 页3：悬念（c08）
        head3 = _head("可高维空间里，到底发生了什么？", 40)
        page3 = page_auto(head3)
        self.play(FadeOut(head2), FadeOut(cards), FadeOut(big), FadeOut(sub),
                  type_in(head3, run_time=1.0), run_time=1.0)
        self.wait(0.4)
        self.transition_out(head3, f, page3)
        self.pad_to_voice()


# ---------------- S2 维度诅咒：随机点远离 + 薄球壳 ----------------
class S2(_Base):
    def construct(self):
        self.bg()
        f = _footer(self)

        # 页1：概念图（c01-c03）
        head = _head("高维里，所有点都差不多远", 38)
        img = ImageMobject(str(IMG / "points-round.png"))
        img.scale_to_fit_width(5.8)
        note = t("随机抛出的点，互相之间的距离趋向无穷大", 28, WHITE)
        page1 = page_stack(img, note, buff=1.0)
        layout_page(page1)

        self.at_clip("S2-c01")
        self.play_parallel(type_in(head, run_time=1.1), FadeIn(img, shift=DOWN * 0.05),
                           run_time=1.1)
        self.at_clip("S2-c02")
        self.play(type_in(note, run_time=0.9))
        self.at_clip("S2-c04")

        # 页2：薄球壳曲线（c04-c06）
        head2 = _head("薄球壳：半径缩 5%，体积缩成 (0.95)^d", 30)
        axes = Axes(x_range=[0, 100, 20], y_range=[0, 1, 0.2],
                    x_length=6.4, y_length=3.6,
                    axis_config={"color": MUTED, "stroke_width": 2,
                                 "include_numbers": True, "font_size": 20})
        axes.set_x(0)
        curve = axes.plot(lambda x: 0.95 ** x, x_range=[0, 100],
                          color=YELL, stroke_width=5)
        lab = t("(0.95)^d → 0", 30, YELL, "BOLD")
        slot = dynamic_slot(2.4, 0.9)
        drow = stable_row(t("维度 d", 32, WHITE, "BOLD"), slot, buff=0.4)
        page2 = page_stack(axes, lab, drow, buff=1.2)
        layout_page(page2)

        self.play(FadeOut(head), FadeOut(img), FadeOut(note),
                  type_in(head2, run_time=0.9), run_time=0.9)
        self.play(FadeIn(axes), run_time=0.6)
        self.at_clip("S2-c05")
        self.play(Create(curve), run_time=1.6)  # 主视觉：指数衰减曲线
        self.at_clip("S2-c06")
        n = self.counter_value(0, 100, suffix=" 维", size=56, color=YELL,
                               run_time=1.4, anchor=slot,
                               extra_anims=[type_in(lab, run_time=0.6)])
        self.emphasize(lab, run_time=0.6)  # 1/5
        self.at_clip("S2-c07")

        # 页3：高斯分布薄壳（c07-c08）
        head3 = _head("高斯分布也一样", 40)
        gauss = gaussian_curve(0, 1, 1.4, color=CYAN)
        gauss.scale_to_fit_width(6.0)
        gauss.set_x(0)
        ring = Circle(radius=1.5, color=YELL, stroke_width=4)
        ring.set_x(0)
        ringlab = t("‖x‖ ≈ √d：薄薄一层壳，里面是空的", 30, WHITE, "BOLD")
        ringlab.next_to(ring, DOWN, buff=0.5)
        ringlab.set_x(0)
        page3 = page_stack(gauss, ring, ringlab, buff=1.4)
        layout_page(page3)

        self.play(FadeOut(head2), FadeOut(axes), FadeOut(curve), FadeOut(lab),
                  FadeOut(n), FadeOut(drow),
                  type_in(head3, run_time=0.9), run_time=0.9)
        self.play(Create(gauss), run_time=1.2)  # 主视觉：高斯曲线
        self.at_clip("S2-c08")
        self.play(FadeIn(ring), type_in(ringlab, run_time=0.9), run_time=0.9)
        self.at_clip("S2-c09")

        # 页4：悬念（c09）
        head4 = _head("空间没怪，是尺子不对？", 42)
        page4 = page_auto(head4)
        self.play(FadeOut(head3), FadeOut(gauss), FadeOut(ring), FadeOut(ringlab),
                  type_in(head4, run_time=1.0), run_time=1.0)
        self.wait(0.3)
        self.transition_out(head4, f, page4)
        self.pad_to_voice()


# ---------------- S3 尺子不对：距离是内积的衍生物 ----------------
class S3(_Base):
    def construct(self):
        self.bg()
        f = _footer(self)

        # 页1：公式（c01-c03）
        head = _head("距离，是内积的衍生物", 40)
        formula = MathTex(r"\|u-v\|^2 = \langle u-v, u-v\rangle",
                          tex_to_color_map={r"\|u-v\|^2": YELL})
        formula.set_width(5.8)
        card = _card("长度、面积、体积，都是积分的结果——但距离，是内积的衍生物",
                     6.4, 3.4, CYAN, WHITE, 30)
        note = t("直觉的尺子，是为三维平直空间定制的", 26, MUTED)
        page1 = page_stack(formula, card, note, buff=1.4)
        layout_page(page1)

        self.at_clip("S3-c01")
        self.play(type_in(head, run_time=1.1))
        self.at_clip("S3-c02")
        self.play(FadeIn(formula), type_in(card, run_time=0.9), type_in(note, run_time=0.9), run_time=0.9)
        self.at_clip("S3-c03")
        self.camera_zoom_to(formula, scale=0.75, run_time=0.8)  # v2 动效 1/2：推近公式
        self.at_clip("S3-c04")
        self.camera_zoom_to(run_time=0.8)  # 拉回

        # 页2：衍生品当尺子 + 内积尺子（c04-c06）
        head2 = _head("我们一直把衍生品，当成了尺子本尊", 36)
        c_bad = _card("距离 = 尺子", 4.6, 1.8, MUTED, WHITE, 40, CARD_FILL, "BOLD")
        img = ImageMobject(str(IMG / "ruler-round.png"))
        img.scale_to_fit_width(3.8)
        c_good = _card("内积：衡量方向与投影", 4.6, 1.6, GREEN, WHITE, 34, CARD_FILL, "BOLD")
        page2 = page_stack(c_bad, img, c_good, buff=0.6)
        layout_page(page2)

        self.play(FadeOut(head), FadeOut(formula), FadeOut(card), FadeOut(note),
                  type_in(head2, run_time=0.9), run_time=0.9)
        self.play_scroll_unroll(c_bad, run_time=1.0)
        self.at_clip("S3-c05")
        cross = self.play_red_cross(c_bad)  # 主视觉：红叉否定
        self.wait(0.1)
        self.play(FadeIn(img, shift=DOWN * 0.05), run_time=0.7)
        self.wait(0.1)
        self.play_scroll_unroll(c_good, run_time=1.2)
        self.at_clip("S3-c06")
        self.wait(1.0)
        self.at_clip("S3-c07")

        # 页3：90° 夹角 + 直方图（c07-c10）
        head3 = _head("高维随机向量，几乎两两垂直", 38)
        a1 = Arrow(ORIGIN, RIGHT * 2.2, color=CYAN, stroke_width=6, buff=0)
        a2 = Arrow(ORIGIN, UP * 2.2, color=GREEN, stroke_width=6, buff=0)
        arc = Arc(radius=0.8, start_angle=0, angle=PI / 2, color=YELL, stroke_width=4)
        ang = t("90°", 34, YELL, "BOLD").next_to(arc, UR, buff=0.15)
        arrows = VGroup(a1, a2, arc, ang)
        axes = Axes(x_range=[0, 180, 30], y_range=[0, 1, 0.25],
                    x_length=6.4, y_length=3.0,
                    axis_config={"color": MUTED, "stroke_width": 2,
                                 "include_numbers": True, "font_size": 20})
        axes.set_x(0)
        bars = VGroup()
        for deg, h in [(30, 0.15), (60, 0.5), (90, 1.0), (120, 0.5), (150, 0.15)]:
            b = Rectangle(width=0.7, height=h * 2.4, color=CYAN,
                          fill_color=CYAN, fill_opacity=0.55)
            b.move_to(axes.c2p(deg, h * 1.2))
            bars.add(b)
        axgrp = VGroup(axes, bars)
        note3 = t("「接近」= 方向接近，距离说了不算", 28, WHITE)
        page3 = page_stack(arrows, axgrp, note3, buff=0.6)
        layout_page(page3)

        self.play(FadeOut(head2), FadeOut(c_bad), FadeOut(img), FadeOut(c_good),
                  FadeOut(cross),
                  type_in(head3, run_time=0.9), run_time=0.9)
        self.play(Create(a1), Create(a2), run_time=0.8)  # 主视觉：两向量
        self.play(Create(arc), type_in(ang, run_time=0.5), run_time=0.6)
        self.at_clip("S3-c08")
        self.play(FadeIn(axes), *[FadeIn(b, shift=UP * 0.05) for b in bars],
                  run_time=1.0)
        self.emphasize(ang, run_time=0.6)  # 2/5
        self.at_clip("S3-c09")
        self.play(type_in(note3, run_time=0.9))
        self.at_clip("S3-c11")

        # 页4：悬念（c11）
        head4 = _head("换一把尺子，能换来什么？", 42)
        page4 = page_auto(head4)
        self.play(FadeOut(head3), FadeOut(arrows), FadeOut(axes), FadeOut(bars),
                  FadeOut(note3),
                  type_in(head4, run_time=1.0), run_time=1.0)
        self.wait(0.3)
        self.transition_out(head4, f, page4)
        self.pad_to_voice()


# ---------------- S4 祝福：内积空间 + 核方法 ----------------
class S4(_Base):
    def construct(self):
        self.bg()
        f = _footer(self)

        # 页1：对偶空间链路（c01-c05）
        head = _head("内积：向量空间 ↔ 对偶空间", 38)
        n1 = cnode("向量空间", CYAN, radius=1.0, fs=26)
        n2 = cnode("对偶空间", GREEN, radius=1.0, fs=26)
        row1 = VGroup(n1, n2).arrange(RIGHT, buff=2.6)
        dbl = VGroup(Arrow(n1.get_right(), n2.get_left(), color=YELL, stroke_width=4, buff=0.1),
                     Arrow(n2.get_left(), n1.get_right(), color=YELL, stroke_width=4, buff=0.1))
        row1g = VGroup(row1, dbl)
        note = t("每个线性泛函，都能写成和某个向量的内积", 28, WHITE)
        n3 = cnode("伴随算子", CYAN, radius=1.0, fs=26)
        n4 = cnode("谱定理 / 对角化", GREEN, radius=1.0, fs=26)
        row2 = VGroup(n3, n4).arrange(RIGHT, buff=2.6)
        ar = Arrow(n3.get_right(), n4.get_left(), color=YELL, stroke_width=4, buff=0.1)
        row2g = VGroup(row2, ar)
        page1 = page_stack(row1g, note, row2g, buff=1.4)
        layout_page(page1)

        self.at_clip("S4-c01")
        self.play(type_in(head, run_time=1.1))
        self.at_clip("S4-c02")
        self.play(FadeIn(n1), FadeIn(n2), Create(dbl), run_time=0.9)  # 主视觉：对应关系
        self.at_clip("S4-c03")
        self.play(type_in(note, run_time=0.9))
        self.at_clip("S4-c04")
        self.play(FadeIn(n3), FadeIn(n4), Create(ar), run_time=0.9)
        self.at_clip("S4-c06")

        # 页2：核方法链路（c06-c08）
        head2 = _head("核方法：升维求解，降维落回", 38)
        k1 = _card("有限维\n定义内积", 2.0, 2.8, CYAN, WHITE, 30, CARD_FILL, "BOLD")
        k2 = _card("无穷维特征空间\n求解", 2.0, 2.8, YELL, WHITE, 30, CARD_FILL, "BOLD")
        k3 = _card("有限维\n落回", 2.0, 2.8, GREEN, WHITE, 30, CARD_FILL, "BOLD")
        krow = VGroup(k1, k2, k3).arrange(RIGHT, buff=0.5)
        ka1 = Arrow(k1.get_right(), k2.get_left(), color=YELL, stroke_width=4, buff=0.1)
        ka2 = Arrow(k2.get_right(), k3.get_left(), color=YELL, stroke_width=4, buff=0.1)
        krowg = VGroup(krow, ka1, ka2)
        note2 = _card("升维和降维，用的都是同一把尺子", 6.0, 1.8, GREEN, WHITE, 32, CARD_FILL, "BOLD")
        sub = t("确定性问题 ↔ 随机概率问题，贴合得巧妙而自然", 26, MUTED)
        page2 = page_stack(krowg, note2, sub, buff=1.2)
        layout_page(page2)

        self.play(FadeOut(head), FadeOut(n1), FadeOut(n2), FadeOut(dbl),
                  FadeOut(note), FadeOut(n3), FadeOut(n4), FadeOut(ar),
                  type_in(head2, run_time=0.9), run_time=0.9)
        self.play_scroll_unroll_many(k1, k2, k3, run_time=1.4)  # 主视觉：三卡拉幕
        self.play(Create(ka1), Create(ka2), run_time=0.6)
        self.at_clip("S4-c08")
        self.play_scroll_unroll(note2, run_time=1.2)
        self.wait(0.1)
        self.play(type_in(sub, run_time=0.9))
        self.at_clip("S4-c09")

        # 页3：爆点（c09）
        head3 = _head("诅咒翻面，就是祝福", 52)
        page3 = page_auto(head3)
        self.play(FadeOut(head2), FadeOut(k1), FadeOut(k2), FadeOut(k3),
                  FadeOut(ka1), FadeOut(ka2), FadeOut(note2), FadeOut(sub),
                  type_in(head3, run_time=1.0), run_time=1.0)
        self.emphasize(head3, run_time=0.6)  # 3/5
        self.at_clip("S4-c10")

        # 页4：悬念（c10）
        head4 = _head("这把尺子，在 AI 里藏在哪？", 42)
        page4 = page_auto(head4)
        self.play(FadeOut(head3), type_in(head4, run_time=1.0), run_time=1.0)
        self.wait(0.3)
        self.transition_out(head4, f, page4)
        self.pad_to_voice()


# ---------------- S5 AI：注意力 = 内积；MLA；V4 ----------------
class S5(_Base):
    def construct(self):
        self.bg()
        f = _footer(self)

        # 页1：注意力公式（c01-c03）
        head = _head("注意力 = 内积", 40)
        formula = MathTex(
            r"\mathrm{Attention}(Q,K,V)=\mathrm{softmax}\left(\frac{QK^\top}{\sqrt{d_k}}\right)V",
            tex_to_color_map={r"QK^\top": YELL})
        formula.set_width(6.2)
        card = _card("QKᵀ 的每一格，都是 query 和 key 的内积", 6.4, 2.6, CYAN, WHITE, 32, CARD_FILL, "BOLD")
        note = t("谁和谁「相关」，数学上就是内积大不大", 26, MUTED)
        page1 = page_stack(formula, card, note, buff=1.6)
        layout_page(page1)

        self.at_clip("S5-c01")
        self.play(type_in(head, run_time=1.1))
        self.at_clip("S5-c02")
        self.play(FadeIn(formula), run_time=0.9)
        self.at_clip("S5-c03")
        self.play(type_in(card, run_time=0.9), type_in(note, run_time=0.9), run_time=0.9)
        self.camera_zoom_to(formula, scale=0.7, run_time=0.8)  # v2 动效 2/2：推近公式
        self.at_clip("S5-c04")
        self.camera_zoom_to(run_time=0.8)  # 拉回

        # 页2：稀疏矩阵（c04-c05）
        head2 = _head("无关的 query/key：内积 ≈ 0", 38)
        cells = VGroup()
        for r in range(4):
            for c in range(4):
                on = (r == c)
                cell = RoundedRectangle(corner_radius=0.12, width=1.05, height=1.05,
                                        color=YELL if on else MUTED, stroke_width=2,
                                        fill_color=YELL if on else MUTED,
                                        fill_opacity=0.55 if on else 0.12)
                cells.add(cell)
        cells.arrange_in_grid(4, 4, buff=0.16)
        qlab = t("Q", 30, CYAN, "BOLD").next_to(cells, LEFT, buff=0.5)
        klab = t("K", 30, GREEN, "BOLD").next_to(cells, UP, buff=0.4)
        note2 = t("注意力权重：天然稀疏", 32, WHITE, "BOLD")
        page2 = page_stack(cells, note2, buff=1.9)
        layout_page(page2)

        self.play(FadeOut(head), FadeOut(formula), FadeOut(card), FadeOut(note),
                  type_in(head2, run_time=0.9), run_time=0.9)
        self.play(*[FadeIn(c, scale=0.6) for c in cells], run_time=1.2)  # 主视觉：矩阵点亮
        self.play(FadeIn(qlab), FadeIn(klab), run_time=0.5)
        self.at_clip("S5-c05")
        self.play(type_in(note2, run_time=0.9))
        self.at_clip("S5-c06")

        # 页3：MLA 链路（c06-c08）
        head3 = _head("MLA：K/V 压进隐空间", 38)
        m1 = _card("K / V", 1.9, 2.4, CYAN, WHITE, 36, CARD_FILL, "BOLD")
        m2 = _card("隐空间\n(低秩)", 1.9, 2.4, YELL, WHITE, 30, CARD_FILL, "BOLD")
        m3 = _card("展开\n再用", 1.9, 2.4, GREEN, WHITE, 30, CARD_FILL, "BOLD")
        mrow = VGroup(m1, m2, m3).arrange(RIGHT, buff=0.6)
        ma1 = Arrow(m1.get_right(), m2.get_left(), color=YELL, stroke_width=4, buff=0.1)
        ma2 = Arrow(m2.get_right(), m3.get_left(), color=YELL, stroke_width=4, buff=0.1)
        mrowg = VGroup(mrow, ma1, ma2)
        relnote = t("有关系 / 没关系，分得清清楚楚", 30, WHITE)
        note3 = _card("压缩掉冗余，留下方向——信息不丢", 6.0, 1.8, GREEN, WHITE, 30, CARD_FILL, "BOLD")
        page3 = page_stack(relnote, mrowg, note3, buff=1.2)
        layout_page(page3)

        self.play(FadeOut(head2), FadeOut(cells), FadeOut(qlab), FadeOut(klab),
                  FadeOut(note2),
                  type_in(head3, run_time=0.9), run_time=0.9)
        self.play(type_in(relnote, run_time=0.9))
        self.at_clip("S5-c07")
        self.play_scroll_unroll_many(m1, m2, m3, run_time=1.4)  # 主视觉：三卡拉幕
        self.play(Create(ma1), Create(ma2), run_time=0.6)
        self.at_clip("S5-c08")
        self.play_scroll_unroll(note3, run_time=1.2)
        self.at_clip("S5-c09")

        # 页4：爆点 + 低维结构（c09-c12）
        head4 = _head("为什么压缩了信息还不丢？", 40)
        d1 = _card("语义方向，不需要几千维", 5.6, 2.2, CYAN, WHITE, 34, CARD_FILL, "BOLD")
        d2 = _card("数据躺在一个低维结构上", 5.6, 2.2, YELL, WHITE, 34, CARD_FILL, "BOLD")
        drow = VGroup(d1, d2).arrange(DOWN, buff=0.6)
        note4 = t("压缩掉的是冗余，留下的是方向", 30, WHITE)
        page4 = page_stack(drow, note4, buff=1.6)
        layout_page(page4)

        self.play(FadeOut(head3), FadeOut(m1), FadeOut(m2), FadeOut(m3),
                  FadeOut(ma1), FadeOut(ma2), FadeOut(note3), FadeOut(relnote),
                  type_in(head4, run_time=1.0), run_time=1.0)
        self.emphasize(head4, run_time=0.6)  # 5/5
        self.at_clip("S5-c10")
        self.play_scroll_unroll_many(d1, d2, run_time=1.4)  # 主视觉：两卡拉幕
        self.at_clip("S5-c12")
        self.play(type_in(note4, run_time=0.9))
        self.at_clip("S5-c13")

        # 页5：V4 先筛后算（c13-c14）
        head5 = _head("DeepSeek-V4：先筛后算", 38)
        v1 = _card("128K token\n压缩成小块", 3.2, 2.0, CYAN, WHITE, 28, CARD_FILL, "BOLD")
        v2 = _card("Indexer\n挑出该看的块", 3.2, 2.0, YELL, WHITE, 28, CARD_FILL, "BOLD")
        v3 = _card("核心注意力\n只算挑出来的", 3.2, 2.0, GREEN, WHITE, 28, CARD_FILL, "BOLD")
        vrow1 = VGroup(v1, v2).arrange(RIGHT, buff=0.6)
        va1 = Arrow(v1.get_right(), v2.get_left(), color=YELL, stroke_width=4, buff=0.1)
        vrow1g = VGroup(vrow1, va1)
        note5 = t("不再压缩所有 KV——先筛，再算", 30, WHITE)
        page5 = page_stack(vrow1g, v3, note5, buff=1.3)
        layout_page(page5)
        va2 = Arrow(v2.get_bottom(), v3.get_top(), color=YELL, stroke_width=4, buff=0.1)

        self.play(FadeOut(head4), FadeOut(d1), FadeOut(d2), FadeOut(note4),
                  type_in(head5, run_time=0.9), run_time=0.9)
        self.play_scroll_unroll_many(v1, v2, run_time=1.2)  # 主视觉：两卡拉幕
        self.wait(0.1)
        self.play(Create(va1), run_time=0.5)
        self.at_clip("S5-c14")
        self.play_scroll_unroll(v3, run_time=1.2)
        self.wait(0.1)
        self.play(Create(va2), type_in(note5, run_time=0.9), run_time=0.9)
        self.at_clip("S5-c15")

        # 页6：收束（c15-c16）
        head6 = _head("两种策略，同一个赌注", 40)
        r1 = _card("低秩 = 方向少", 3.2, 3.0, CYAN, WHITE, 38, CARD_FILL, "BOLD")
        r2 = _card("稀疏 = 位置少", 3.2, 3.0, GREEN, WHITE, 38, CARD_FILL, "BOLD")
        rrow = VGroup(r1, r2).arrange(RIGHT, buff=0.6)
        big6 = t("高维结构，其实是稀疏的", 40, YELL, "BOLD")
        sub6 = t("低秩和稀疏，押的是同一个赌注", 28, WHITE)
        page6 = page_stack(rrow, big6, sub6, buff=1.6)
        layout_page(page6)

        self.play(FadeOut(head5), FadeOut(v1), FadeOut(v2), FadeOut(v3),
                  FadeOut(va1), FadeOut(va2), FadeOut(note5),
                  type_in(head6, run_time=0.9), run_time=0.9)
        self.play_scroll_unroll_many(r1, r2, run_time=1.3)  # 主视觉：两卡拉幕
        self.at_clip("S5-c16")
        self.play(type_in(big6, run_time=0.9))
        self.wait(0.5)
        self.transition_out(head6, f, r1, r2, big6, sub6)
        self.pad_to_voice()


# ---------------- S6 总结 + 品牌尾卡 ----------------
class S6(_Base):
    def construct(self):
        self.bg()
        f = _footer(self)

        # 页1：三样缺一不可（c01-c03）
        head = _head("三样缺一不可", 40)
        c1 = _card("微积分\n反直觉的推导", 2.1, 3.4, CYAN, WHITE, 30, CARD_FILL, "BOLD")
        c2 = _card("高维统计\n随机结构的真相", 2.1, 3.4, GREEN, WHITE, 30, CARD_FILL, "BOLD")
        c3 = _card("线性代数\n那把尺子", 2.1, 3.4, YELL, WHITE, 30, CARD_FILL, "BOLD")
        crow = VGroup(c1, c2, c3).arrange(RIGHT, buff=0.4)
        note1 = t("这些当年「没什么用」的课", 28, WHITE)
        note2 = t("正在 AI 的每一层里大放异彩", 28, WHITE)
        page1 = page_stack(crow, note1, note2, buff=1.5)
        layout_page(page1)

        self.at_clip("S6-c01")
        self.play(type_in(head, run_time=1.1))
        self.at_clip("S6-c02")
        self.play_scroll_unroll_many(c1, c2, c3, run_time=1.4)  # 主视觉：三卡拉幕
        self.at_clip("S6-c03")
        self.play(type_in(note1, run_time=0.9), type_in(note2, run_time=0.9), run_time=0.9)
        self.at_clip("S6-c04")

        # 页2：互动 + 品牌尾卡（c04-c07，终幕驻屏）
        q = t("你当年被哪个高维结论骗过？", 36, WHITE, "BOLD")
        logo = ImageMobject(str(AVATAR))
        logo.scale_to_fit_width(3.4)
        follow = t("关注「数解AI」", 40, YELL, "BOLD")
        title = t("《高维空间为什么全是壳？内积才是那把尺子》", 30, WHITE, "BOLD")
        title.set_width(6.8)
        guide = t("查看公众号文章", 32, GREEN, "BOLD")
        page2 = page_stack(q, logo, follow, title, guide, buff=0.6)
        layout_page(page2)

        self.play(FadeOut(head), FadeOut(c1), FadeOut(c2), FadeOut(c3),
                  FadeOut(note1), FadeOut(note2),
                  type_in(q, run_time=1.0), run_time=1.0)
        self.at_clip("S6-c05")
        self.play(FadeIn(logo, shift=DOWN * 0.05), type_in(follow, run_time=0.9), run_time=0.9)
        self.at_clip("S6-c06")
        self.play(type_in(title, run_time=1.0))
        self.at_clip("S6-c07")
        self.play(type_in(guide, run_time=0.8))
        self.wait(1.0)
        self.pad_to_voice()
