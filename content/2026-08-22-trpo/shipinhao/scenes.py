#!/usr/bin/env python3
"""《梯度一步踩爆50倍预算，TRPO为什么敢走？》视频号 Manim 动画（竖屏 1080×1920）

6 个场景 S1-S6，与 storyboard.md 一一对应（强化学习原理系列第 6 篇）。
- 配音：MiniMax 精英男声（speech-2.8-turbo，speed 1.0，pitch +2）
- 时间轴：at_clip("S1-c01") 挂 tts/sentence-boundaries.json 的 clip 起点（先声音后动画门禁）
- 布局：整页规划（page_stack + layout_page / page_auto），上下留白各 ≤ 10%
- 动画降噪（决策 #51）：emphasize 全片 5 次（S1 wiggle A / S1 步长条 / S2 50 倍 / S4 自然梯度 / S5 预算用满），
  v2 动效 3 处（S4 camera_zoom 成对推拉 / S3 breathe / S4 breathe）；每页 1 个主视觉动效；数字台词全部配 counter_value / grow_bar

用法（shipinhao 目录内执行）：
  MANIM_STRICT_TIMELINE=1 MANIM_STRICT_WIDTH=1 python3 -m manim render -ql --disable_caching scenes.py S1 S2 S3 S4 S5 S6
  MANIM_STRICT_TIMELINE=1 MANIM_STRICT_WIDTH=1 python3 -m manim render -qm --disable_caching scenes.py S1 S2 S3 S4 S5 S6
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

# 每段配音时长（ffprobe 实测 tts/sN.wav），渲染时长 = 配音 + TAIL
# ⚠️ TAIL 必须等于 build 脚本的 --tail（默认 0.1）：末段 mux 时长取 max(配音+0.1, 动画时长)，
# 动画比「配音+0.1」长会触发 build 拉伸字幕 → 段内字幕后移。尾卡停留用显式 wait()。
VOICE_DUR = {"S1": 32.60, "S2": 34.47, "S3": 33.11, "S4": 36.69, "S5": 32.68, "S6": 37.85}
TAIL = 0.1


def _footer(self) -> Text:
    f = t("数解AI · 强化学习原理", 20, MUTED).to_edge(DOWN, buff=1.15)
    self.add(f)
    return f


def _head(text: str, size: float = 38) -> Text:
    return t(text, size, YELL, "BOLD")


def _img(name: str, width: float) -> ImageMobject:
    im = ImageMobject(str(IMG / name))
    im.scale_to_fit_width(width)
    return im


def _cloud(wide_axis: float, narrow_axis: float, color: str, n: int = 46) -> VGroup:
    """壳状椭圆云（脚本画，非 AI 图）：外圈稠密、中心留空。"""
    dots = VGroup()
    for i in range(n):
        a = 2 * PI * i / n
        x = 0.5 * wide_axis * np.cos(a)
        y = 0.5 * narrow_axis * np.sin(a)
        r = 0.055 * (1.0 + 0.6 * ((i * 7) % 3))
        d = Dot(point=[x, y, 0], radius=r, color=color).set_opacity(0.55 + 0.3 * ((i * 5) % 3) / 2)
        dots.add(d)
    return dots


TRACK_W = 3.4


def _step_row(lab: str, num: float, value_text: str, color: str, lab_size: int = 28) -> VGroup:
    """步长条：左标签 + 长度正比于 num 的条（左端对齐，两条共用起点）+ 条右端数值。"""
    track = Rectangle(width=TRACK_W, height=0.7, color=MUTED, stroke_width=1.5, fill_opacity=0)
    bar = Rectangle(width=max(TRACK_W * num, 0.07), height=0.7, color=color,
                    fill_color=color, fill_opacity=0.8)
    bar.move_to(track.get_center())
    bar.align_to(track, LEFT)
    label = t(lab, lab_size, WHITE, "BOLD")
    label.next_to(track, LEFT, buff=0.38)
    val = t(value_text, 26, color, "BOLD")
    val.next_to(track, RIGHT, buff=0.38)
    val.align_to(track, DOWN)
    return VGroup(label, track, bar, val)


def _num_row(lab: str, width: float = 2.6, height: float = 1.1):
    """静态标签 + 动态数字槽位（同拍出现；动态值先占位后滚动）。"""
    slot = dynamic_slot(width, height)
    row = stable_row(t(lab, 26, WHITE, "BOLD"), slot, buff=0.40)
    return row, slot


# ---------------- S1 开场：同一个梯度，两种命运 ----------------
class S1(_Base):
    def construct(self):
        self.bg()
        f = _footer(self)

        # 页1：两个 agent 分屏，一夜之后两种命运（c01-c07）
        head = _head("同一个梯度，两种命运", 38)
        note = t("以 coding agent 改代码为例", 24, MUTED)
        img = _img("s1-two-agents-round.png", 3.4)
        cA = _card("A：普通梯度上升\n一步一个脚印，窄方向踩爆", 5.5, 1.5, RED, WHITE, 29, CARD_FILL, "BOLD")
        cB = _card("B：每步先量新旧差多远\n稳稳变强", 5.5, 1.5, GREEN, WHITE, 29, CARD_FILL, "BOLD")
        cJ = _card("差别不在学了多少，在一步走多大", 5.6, 1.4, YELL, WHITE, 32, CARD_FILL, "BOLD")
        page1 = page_stack(head, note, img, cA, cB, cJ, buff=0.52)
        layout_page(page1)

        self.at_clip("S1-c01")
        self.play(type_in(head, run_time=1.0), type_in(note, run_time=0.7), run_time=1.0)  # 0 -> 1.0（A12 小字同拍）
        self.at_clip("S1-c03")
        self.play(FadeIn(img, shift=DOWN * 0.05), run_time=0.8)   # 4.97 -> 5.77
        self.at_clip("S1-c04")
        self.play_scroll_unroll(cA, run_time=1.1)                 # 9.75 -> 10.85
        self.at_clip("S1-c05")
        self.play_scroll_unroll(cB, run_time=1.1)                 # 12.89 -> 13.99
        self.at_clip("S1-c06")
        self.emphasize(cA, mode="wiggle", run_time=0.8)           # 16.09 -> 16.89（强调 1/5）
        self.at_clip("S1-c07")
        self.play_scroll_unroll(cJ, run_time=1.2)                 # 20.48 -> 21.68

        # 页2：预算复习——上限知道了，谁说了算（c08-c09）
        head2 = _head("上限知道了，谁说了算？", 36)
        c0 = _card("预算是 0.01 圈出的那颗椭圆", 5.4, 1.5, CYAN, WHITE, 32, CARD_FILL, "BOLD")
        row_a = _step_row("窄方向", 0.014 / 1.41, "0.014", RED)
        row_b = _step_row("宽方向", 1.0, "1.41", GREEN)
        page2 = page_stack(head2, c0, row_a, row_b, buff=1.2)
        layout_page(page2)

        self.at_clip("S1-c08")
        self.play(FadeOut(head), FadeOut(note), FadeOut(img), FadeOut(cA), FadeOut(cB),
                  FadeOut(cJ), type_in(head2, run_time=0.9), run_time=1.0)   # 23.87 -> 24.87
        self.play_scroll_unroll(c0, run_time=1.1)                            # 24.87 -> 25.97
        self.wait(0.15)
        self.grow_bar(row_a[2], ValueTracker(0), TRACK_W * 0.014 / 1.41, run_time=0.8,
                      anchor="center",
                      extra_anims=[type_in(row_a[0], run_time=0.5), Create(row_a[1]),
                                   type_in(row_a[3], run_time=0.5)])         # 25.97 -> 26.77
        self.at_clip("S1-c09")
        self.grow_bar(row_b[2], ValueTracker(0), TRACK_W, run_time=1.0, anchor="center",
                      extra_anims=[type_in(row_b[0], run_time=0.6), Create(row_b[1]),
                                   type_in(row_b[3], run_time=0.6)])         # 29.11 -> 30.11（主视觉）
        self.emphasize(VGroup(row_a, row_b), run_time=0.7)                   # 强调 2/5
        self.wait(1.19)                                                      # 30.81 -> 32.00（转场对齐末句收尾，勿留空屏）
        self.transition_out(head2, c0, row_a, row_b, f)                      # 32.00 -> 32.60
        self.pad_to_voice()


# ---------------- S2 普通梯度：一脚踩爆 50 倍 ----------------
class S2(_Base):
    def construct(self):
        self.bg()
        f = _footer(self)

        # 页1：KL 0.5 vs 预算 0.01，踩爆 50 倍（c01-c05）
        head = _head("普通梯度：一脚踩爆 50 倍", 36)
        formula = MathTex(r"\mathrm{KL}=\frac{1}{2}\cdot\frac{0.1^{2}}{0.01}\approx 0.5",
                          tex_to_color_map={r"0.5": RED})
        formula.set_width(5.8)
        lab1 = t("这一脚的 KL", 30, WHITE, "BOLD")
        bar1 = Rectangle(width=4.6, height=0.78, color=RED, fill_color=RED, fill_opacity=0.75)
        g1 = VGroup(lab1, bar1).arrange(DOWN, buff=0.26)
        lab2 = t("预算只有 0.01", 28, WHITE, "BOLD")
        bar2 = Rectangle(width=0.09, height=0.78, color=CYAN, fill_color=CYAN, fill_opacity=0.75)
        g2 = VGroup(lab2, bar2).arrange(DOWN, buff=0.26)
        bars = VGroup(g1, g2).arrange(DOWN, buff=0.85)
        cloud1 = _cloud(3.2, 1.1, CYAN, n=40)
        ctr1 = Dot(point=ORIGIN, radius=0.07, color=WHITE)
        ar_n = Arrow(ORIGIN, RIGHT * 0.8, buff=0, color=RED, stroke_width=5,
                     max_tip_length_to_length_ratio=0.30)
        ar_w = Arrow(ORIGIN, UP * 0.7, buff=0, color=GREEN, stroke_width=5,
                     max_tip_length_to_length_ratio=0.30)
        gstep = t("两个方向，梯度都说各走 0.1", 25, MUTED)
        gstep.next_to(cloud1, DOWN, buff=0.22)
        cloudgrp1 = VGroup(cloud1, ctr1, ar_n, ar_w, gstep)
        slot = dynamic_slot(3.2, 1.2)
        row = stable_row(t("踩了预算", 30, WHITE, "BOLD"), slot, buff=0.40)
        page1 = page_stack(head, formula, cloudgrp1, bars, row, buff=0.34)
        layout_page(page1)

        self.at_clip("S2-c01")
        self.play(type_in(head, run_time=1.0))                        # 0 -> 1.0
        self.at_clip("S2-c02")
        self.play(FadeIn(formula), run_time=0.8)                      # 1.54 -> 2.34
        self.at_clip("S2-c03")
        self.play(FadeIn(cloudgrp1, shift=DOWN * 0.05), run_time=0.9)  # 6.59 -> 7.49
        self.at_clip("S2-c04")
        self.grow_bar(bar1, ValueTracker(0), 4.6, run_time=0.8, anchor="center",
                      extra_anims=[type_in(lab1, run_time=0.6)])      # 11.85 -> 12.65
        self.wait(1.2)
        self.grow_bar(bar2, ValueTracker(0), 0.09, run_time=0.6, anchor="center",
                      extra_anims=[type_in(lab2, run_time=0.5)])      # 13.85 -> 14.45
        self.at_clip("S2-c05")
        n50 = self.counter_value(0, 50, suffix=" 倍", size=58, color=RED, run_time=1.0,
                                 anchor=slot,
                                 extra_anims=[type_in(row[0], run_time=0.6)])  # 14.96 -> 15.96
        self.emphasize(n50, run_time=0.7)                             # 强调 3/5

        # 页2：云窄的地方经不起大步（c06-c09）
        head2 = _head("云窄的地方，经不起大步", 36)
        cloud = _cloud(3.8, 1.25, CYAN, n=42)
        ctr = Dot(point=ORIGIN, radius=0.08, color=WHITE)
        arrow = Arrow(ORIGIN, RIGHT * 0.62, buff=0, color=YELL, stroke_width=6,
                      max_tip_length_to_length_ratio=0.28)
        arrow.next_to(ctr, RIGHT, buff=0.06)
        sig = t("云宽 σ = 0.1", 26, CYAN, "BOLD")
        sig.next_to(cloud, LEFT, buff=0.35)
        step = t("均值挪 0.1 = 一个标准差", 24, YELL, "BOLD")
        step.next_to(cloud, DOWN, buff=0.30)
        fit(step, 0.56)
        slot2 = dynamic_slot(3.0, 1.2)
        row2 = stable_row(t("昨天九成半会做的事", 28, WHITE, "BOLD"), slot2, buff=0.40)
        cJ = _card("不是学太快，是云窄经不起大步", 5.6, 1.5, YELL, WHITE, 32, CARD_FILL, "BOLD")
        cloudgrp = VGroup(cloud, ctr, arrow, sig, step)
        page2 = page_stack(head2, cloudgrp, row2, cJ, buff=0.82)
        layout_page(page2)

        self.at_clip("S2-c06")
        self.play(FadeOut(head), FadeOut(formula), FadeOut(g1), FadeOut(g2), FadeOut(row),
                  FadeOut(n50), FadeOut(cloudgrp1),
                  type_in(head2, run_time=0.9), run_time=1.0)  # 19.70 -> 20.70
        self.play(FadeIn(cloudgrp, shift=DOWN * 0.05), run_time=0.8)          # 20.70 -> 21.50
        self.at_clip("S2-c07")
        self.play(GrowArrow(arrow), type_in(sig, run_time=0.6), type_in(step, run_time=0.7),
                  run_time=0.9)                                              # 23.45 -> 24.35
        self.at_clip("S2-c08")
        n84 = self.counter_value(0.954, 0.840, decimals=3, size=54, color=YELL, run_time=1.1,
                                 anchor=slot2,
                                 extra_anims=[type_in(row2[0], run_time=0.6)])  # 26.59 -> 27.69
        self.wait(1.2)
        self.at_clip("S2-c09")
        self.play_scroll_unroll(cJ, run_time=1.2)                        # 30.34 -> 31.54
        self.wait(2.33)                                                  # 31.54 -> 33.87（转场对齐末句收尾）
        self.transition_out(head2, cloudgrp, row2, n84, cJ, f)           # 33.87 -> 34.47
        self.pad_to_voice()


# ---------------- S3 揭盖：旧轨迹给新策略预打分 ----------------
class S3(_Base):
    def construct(self):
        self.bg()
        f = _footer(self)

        # 页1：旧轨迹还在仓库，新策略先给自己估分（c01-c04）
        head = _head("旧轨迹给新策略预打分", 38)
        img = _img("s3-old-tracks-round.png", 3.3)
        formula = MathTex(r"r=\frac{\pi_{\mathrm{new}}(a\mid s)}{\pi_{\mathrm{old}}(a\mid s)}",
                          tex_to_color_map={r"\pi_{\mathrm{new}}": GREEN})
        formula.set_width(4.2)
        c1 = _card("新策略不用重跑环境\n拿旧轨迹估自己的分", 5.5, 1.5, CYAN, WHITE, 30, CARD_FILL, "BOLD")
        c2 = _card("这个 trick 叫重要性采样", 5.4, 1.3, YELL, WHITE, 32, CARD_FILL, "BOLD")
        page1 = page_stack(head, img, formula, c1, c2, buff=0.55)
        layout_page(page1)

        self.at_clip("S3-c01")
        self.play(type_in(head, run_time=1.0), FadeIn(img, shift=DOWN * 0.05), run_time=1.0)  # 0 -> 1.0
        self.at_clip("S3-c02")
        self.play_scroll_unroll(c1, run_time=1.1)                        # 3.73 -> 4.83
        self.at_clip("S3-c03")
        self.play(FadeIn(formula), run_time=0.8)                         # 8.08 -> 8.88
        self.at_clip("S3-c04")
        self.play_scroll_unroll(c2, run_time=1.1)                        # 12.20 -> 13.30

        # 页2：权重从 1 涨到 2.67（c05-c09）
        head2 = _head("回报乘权重，加起来", 36)
        old = t("旧策略走某条路：0.30", 28, WHITE, "BOLD")
        slot = dynamic_slot(2.6, 1.2)
        rownew = stable_row(t("新策略想提到 0.80 →", 28, WHITE, "BOLD"), slot, buff=0.40)
        c3 = _card("每条轨迹的回报 × 权重\n加起来 = 新策略的期望回报", 5.6, 1.7, GREEN, WHITE, 30, CARD_FILL, "BOLD")
        c4 = _card("它回答一个问题：往哪走", 5.4, 1.4, YELL, WHITE, 32, CARD_FILL, "BOLD")
        page2 = page_stack(head2, old, rownew, c3, c4, buff=0.62)
        layout_page(page2)

        self.at_clip("S3-c05")
        self.play(FadeOut(head), FadeOut(img), FadeOut(formula), FadeOut(c1), FadeOut(c2),
                  type_in(head2, run_time=0.9), type_in(old, run_time=0.7), run_time=1.0)  # 15.33 -> 16.33
        self.at_clip("S3-c06")
        w = self.counter_value(1.0, 2.67, decimals=2, size=56, color=YELL, run_time=1.1,
                               anchor=slot,
                               extra_anims=[type_in(rownew[0], run_time=0.7)])  # 19.26 -> 20.36
        self.wait(1.2)
        self.at_clip("S3-c07")
        self.play_scroll_unroll(c3, run_time=1.2)                        # 22.60 -> 23.80
        self.at_clip("S3-c08")
        self.breathe(c3, scale=1.03, run_time=1.6, loops=1)              # 27.88 -> 29.48（v2 动效 2/3）
        self.at_clip("S3-c09")
        self.play_scroll_unroll(c4, run_time=1.1)                        # 30.30 -> 31.40
        self.wait(1.11)                                                  # 31.40 -> 32.51（转场对齐末句收尾）
        self.transition_out(head2, old, rownew, w, c3, c4, f)            # 32.51 -> 33.11
        self.pad_to_voice()


# ---------------- S4 曲率 + 罚金：自然梯度出世 ----------------
class S4(_Base):
    def construct(self):
        self.bg()
        f = _footer(self)

        # 页1：二阶泰勒请进曲率，Fisher 是刻度的倒数（c01-c06）
        head = _head("梯度看不到弯度", 38)
        formula = MathTex(r"\frac{1}{2}\Delta\theta^{\top}F\,\Delta\theta\le\delta",
                          tex_to_color_map={r"F": YELL})
        formula.set_width(5.4)
        c0 = _card("F 叫 Fisher 信息矩阵\n就是云宽度的倒数", 5.5, 1.5, CYAN, WHITE, 30, CARD_FILL, "BOLD")
        rowA, slotA = _num_row("窄方向刻度")
        rowB, slotB = _num_row("宽方向刻度")
        page1 = page_stack(head, formula, c0, rowA, rowB, buff=0.58)
        layout_page(page1)

        self.at_clip("S4-c01")
        self.play(type_in(head, run_time=1.0))                     # 0 -> 1.0
        self.at_clip("S4-c02")
        self.play(FadeIn(formula), run_time=0.8)                   # 4.49 -> 5.29
        self.at_clip("S4-c03")
        self.camera_zoom_to(formula, scale=0.78, run_time=1.0)     # 10.68 -> 11.68（v2 动效 1/3，讲二阶展开时推近）
        self.wait(0.8)
        self.at_clip("S4-c04")
        self.camera_zoom_to(run_time=0.9)                          # 13.63 -> 14.53（成对拉回）
        self.play_scroll_unroll(c0, run_time=1.1)                  # 14.53 -> 15.63
        self.at_clip("S4-c05")
        nA = self.counter_value(0, 100, size=52, color=YELL, run_time=0.8, anchor=slotA,
                                extra_anims=[type_in(rowA[0], run_time=0.5)])   # 16.95 -> 17.75
        self.at_clip("S4-c06")
        nB = self.counter_value(0, 0.01, decimals=2, size=52, color=CYAN, run_time=0.8,
                                anchor=slotB,
                                extra_anims=[type_in(rowB[0], run_time=0.5)])   # 20.83 -> 21.63

        # 页2：拉格朗日——把约束折成罚金（c07-c10）
        head2 = _head("拉格朗日：把约束折成罚金", 34)
        img = _img("s4-fine-line-round.png", 2.9)
        c1 = _card("超一个单位，罚 lambda 个罚金", 5.5, 1.3, RED, WHITE, 30, CARD_FILL, "BOLD")
        f2 = MathTex(r"\Delta\theta=\frac{1}{\lambda}F^{-1}g",
                     tex_to_color_map={r"F^{-1}g": YELL})
        f2.set_width(3.6)
        c2 = _card("Fisher 逆乘梯度，就是自然梯度", 5.5, 1.5, GREEN, WHITE, 30, CARD_FILL, "BOLD")
        page2 = page_stack(head2, img, c1, f2, c2, buff=0.48)
        layout_page(page2)

        self.at_clip("S4-c07")
        self.play(FadeOut(head), FadeOut(formula), FadeOut(c0), FadeOut(rowA), FadeOut(nA),
                  FadeOut(rowB), FadeOut(nB),
                  type_in(head2, run_time=0.9), FadeIn(img, shift=DOWN * 0.05), run_time=1.0)  # 22.50 -> 23.50
        self.play_scroll_unroll(c1, run_time=1.1)                 # 23.50 -> 24.60
        self.at_clip("S4-c08")
        self.breathe(c1, scale=1.03, run_time=1.6, loops=1)       # 26.21 -> 27.81（v2 动效 3/3）
        self.at_clip("S4-c09")
        self.play(FadeIn(f2), run_time=0.8)                       # 30.51 -> 31.31
        self.emphasize(f2, run_time=0.7)                          # 强调 4/5
        self.at_clip("S4-c10")
        self.play_scroll_unroll(c2, run_time=1.1)                 # 35.00 -> 36.10
        self.transition_out(head2, img, c1, f2, c2, f)
        self.pad_to_voice()


# ---------------- S5 闭式解：步长自动算 ----------------
class S5(_Base):
    def construct(self):
        self.bg()
        f = _footer(self)

        # 页1：自然梯度把梯度掰弯了（c01-c03）
        head = _head("自然梯度把梯度掰弯了", 38)
        lab = t("梯度说：两个方向各走一半", 28, WHITE, "BOLD")
        TOT = 4.7
        g1 = Rectangle(width=TOT / 2 - 0.15, height=0.7, color=MUTED, fill_color=MUTED, fill_opacity=0.6)
        g2 = Rectangle(width=TOT / 2 - 0.15, height=0.7, color=MUTED, fill_color=MUTED, fill_opacity=0.6)
        rowg = VGroup(g1, g2).arrange(RIGHT, buff=0.30)
        rowg_lab = VGroup(lab, rowg).arrange(DOWN, buff=0.24)
        lab2 = t("Fisher 逆说：窄方向几乎不动，宽方向走满", 26, YELL, "BOLD")
        nat1 = Rectangle(width=0.07, height=0.7, color=RED,
                         fill_color=RED, fill_opacity=0.8)
        nat2 = Rectangle(width=TOT - 0.37, height=0.7, color=GREEN,
                         fill_color=GREEN, fill_opacity=0.8)
        rown = VGroup(nat1, nat2).arrange(RIGHT, buff=0.30)
        rown_lab = VGroup(lab2, rown).arrange(DOWN, buff=0.24)
        c0 = _card("比例差一万倍", 5.0, 1.4, YELL, WHITE, 34, CARD_FILL, "BOLD")
        page1 = page_stack(head, rowg_lab, rown_lab, c0, buff=1.05)
        layout_page(page1)

        self.at_clip("S5-c01")
        self.play(type_in(head, run_time=1.0))                       # 0 -> 1.0
        self.at_clip("S5-c02")
        self.play_parallel(type_in(lab, run_time=0.6), Create(g1), Create(g2), run_time=0.8)
        self.play_parallel(type_in(lab2, run_time=0.7), Create(nat1), Create(nat2), run_time=0.8)
        self.at_clip("S5-c03")
        self.play_scroll_unroll(c0, run_time=1.1)                    # 8.09 -> 9.19

        # 页2：闭式解（c04-c08）
        head2 = _head("最优解恰好把预算用完", 36)
        f2 = MathTex(r"\theta_{\mathrm{new}}=\theta_{\mathrm{old}}"
                     r"+\sqrt{\frac{2\delta}{g^{\top}F^{-1}g}}\;F^{-1}g",
                     tex_to_color_map={r"\sqrt{\frac{2\delta}{g^{\top}F^{-1}g}}": YELL})
        f2.set_width(6.4)
        c1 = _card("方向看梯度，大小看曲率", 5.4, 1.5, GREEN, WHITE, 34, CARD_FILL, "BOLD")
        c2 = _card("lambda 有闭式解\n一步正好踩满预算", 5.4, 1.5, CYAN, WHITE, 30, CARD_FILL, "BOLD")
        page2 = page_stack(head2, f2, c1, c2, buff=0.9)
        layout_page(page2)

        self.at_clip("S5-c04")
        self.play(FadeOut(head), FadeOut(rowg_lab), FadeOut(rown_lab), FadeOut(c0),
                  type_in(head2, run_time=0.9), run_time=1.0)        # 9.54 -> 10.54
        self.play(FadeIn(f2), run_time=0.9)                          # 10.54 -> 11.44
        self.at_clip("S5-c05")
        self.play_scroll_unroll(c1, run_time=1.1)                    # 13.97 -> 15.07
        self.at_clip("S5-c06")
        self.play_scroll_unroll(c2, run_time=1.1)                    # 17.07 -> 18.17

        # 页3：验算——窄 0.00014，宽 1.414，KL 恰好 0.01（c08-c10）
        head3 = _head("同一份梯度，一步不差", 36)
        rowA, slotA = _num_row("窄方向挪")
        rowB, slotB = _num_row("宽方向挪")
        rowK, slotK = _num_row("这一步的 KL")
        page3 = page_stack(head3, rowA, rowB, rowK, buff=1.25)
        layout_page(page3)

        self.at_clip("S5-c08")
        self.play(FadeOut(head2), FadeOut(f2), FadeOut(c1), FadeOut(c2),
                  type_in(head3, run_time=0.9), run_time=1.0)        # 22.01 -> 23.01
        nA = self.counter_value(0, 0.00014, decimals=5, size=50, color=RED, run_time=1.0,
                                anchor=slotA,
                                extra_anims=[type_in(rowA[0], run_time=0.6)])   # 23.01 -> 24.01
        self.at_clip("S5-c09")
        nB = self.counter_value(0, 1.414, decimals=3, size=50, color=GREEN, run_time=1.0,
                                anchor=slotB,
                                extra_anims=[type_in(rowB[0], run_time=0.6)])   # 25.91 -> 26.91
        self.at_clip("S5-c10")
        nK = self.counter_value(0, 0.01, decimals=2, size=50, color=YELL, run_time=1.0,
                                anchor=slotK,
                                extra_anims=[type_in(rowK[0], run_time=0.6)])   # 30.27 -> 31.27
        self.emphasize(nK, run_time=0.7)                                    # 强调 5/5（预算用满）
        self.wait(0.11)                                                     # 31.97 -> 32.08（转场对齐末句收尾）
        self.transition_out(head3, rowA, nA, rowB, nB, rowK, nK, f)         # 32.08 -> 32.68
        self.pad_to_voice()


# ---------------- S6 TRPO 是谁 + 家族 + 预告 ----------------
class S6(_Base):
    def construct(self):
        self.bg()
        f = _footer(self)

        # 页1：TRPO 是谁（c01-c04）
        head = _head("TRPO：信任域策略优化", 36)
        img = _img("s6-brake-round.png", 2.9)
        c0 = _card("Schulman，2015 年提出", 5.2, 1.3, YELL, WHITE, 32, CARD_FILL, "BOLD")
        c1 = _card("每次更新，只信任旧策略周围的一小圈", 5.6, 1.3, CYAN, WHITE, 30, CARD_FILL, "BOLD")
        c2 = _card("保证代理目标不降", 5.6, 1.2, GREEN, WHITE, 30, CARD_FILL, "BOLD")
        c2b = _card("求逆太贵，改用共轭梯度", 5.6, 1.2, CYAN, WHITE, 30, CARD_FILL, "BOLD")
        page1 = page_stack(head, img, c0, c1, c2, c2b, buff=0.48)
        layout_page(page1)

        self.at_clip("S6-c01")
        self.play(type_in(head, run_time=1.0), FadeIn(img, shift=DOWN * 0.05), run_time=1.0)
        self.play_scroll_unroll(c0, run_time=1.1)                  # 1.0 -> 2.1
        self.at_clip("S6-c02")
        self.play_scroll_unroll(c1, run_time=1.2)                  # 6.00 -> 7.20
        self.at_clip("S6-c03")
        self.play_scroll_unroll(c2, run_time=1.1)                  # 11.44 -> 12.54
        self.at_clip("S6-c04")
        self.play_scroll_unroll(c2b, run_time=1.1)                 # 13.42 -> 14.52

        # 页2：同一个家族三代（c05-c06）
        head2 = _head("同一个家族，三代", 38)
        n1 = cnode("TRPO\n给刹车", YELL)
        n2 = cnode("PPO\n拧成代码", GREEN)
        n3 = cnode("GRPO\n删一半", CYAN)
        chain = VGroup(n1, n2, n3).arrange(RIGHT, buff=0.75)
        a1 = Arrow(n1.get_right() + RIGHT * 0.05, n2.get_left() + LEFT * 0.05,
                   buff=0, color=MUTED, stroke_width=5, max_tip_length_to_length_ratio=0.25)
        a2 = Arrow(n2.get_right() + RIGHT * 0.05, n3.get_left() + LEFT * 0.05,
                   buff=0, color=MUTED, stroke_width=5, max_tip_length_to_length_ratio=0.25)
        c3 = _card("TRPO 给刹车 → PPO 拧成代码 → GRPO 删一半", 5.8, 1.6, YELL, WHITE, 26, CARD_FILL, "BOLD")
        chaingrp = VGroup(chain, a1, a2)
        page2 = page_stack(head2, chaingrp, c3, buff=1.6)
        layout_page(page2)

        self.at_clip("S6-c05")
        self.play(FadeOut(head), FadeOut(img), FadeOut(c0), FadeOut(c1), FadeOut(c2), FadeOut(c2b),
                  type_in(head2, run_time=0.9), run_time=1.0)      # 16.97 -> 17.97
        self.play_parallel(FadeIn(n1, shift=DOWN * 0.05), run_time=0.5)
        self.play_parallel(FadeIn(n2, shift=DOWN * 0.05), GrowArrow(a1), run_time=0.5)
        self.at_clip("S6-c06")
        self.play_parallel(FadeIn(n3, shift=DOWN * 0.05), GrowArrow(a2), run_time=0.6)  # 20.13 -> 20.73
        self.play_scroll_unroll(c3, run_time=1.1)                  # 20.73 -> 21.83

        # 页3：预告 + 互动 + 品牌尾卡（c07-c10）
        pre = t("下一篇：PPO——一句 clip 换掉这桌数学", 26, WHITE, "BOLD")
        title = t("《梯度一步踩爆50倍预算，TRPO为什么敢走？》", 27, WHITE, "BOLD")
        title.set_width(6.9)
        q = t("先严格推出闭式解，再交给计算机算，你意外吗？", 28, WHITE, "BOLD")
        q.set_width(6.9)
        logo = ImageMobject(str(AVATAR))
        logo.scale_to_fit_width(2.7)
        follow = t("关注「数解AI」", 38, YELL, "BOLD")
        guide = t("查看公众号文章", 30, GREEN, "BOLD")
        page3 = page_stack(pre, title, q, logo, follow, guide, buff=0.5)
        layout_page(page3)

        self.at_clip("S6-c07")
        self.play(FadeOut(head2), FadeOut(n1), FadeOut(n2), FadeOut(n3), FadeOut(a1), FadeOut(a2),
                  FadeOut(c3),
                  type_in(pre, run_time=1.0), type_in(title, run_time=1.0), run_time=1.0)  # 24.67 -> 25.67
        self.at_clip("S6-c08")
        self.play(FadeIn(logo, shift=DOWN * 0.05), type_in(follow, run_time=0.9),
                  type_in(q, run_time=1.0), run_time=1.0)          # 30.17 -> 31.17
        self.at_clip("S6-c10")
        self.play(type_in(guide, run_time=0.5))                    # 36.48 -> 36.98
        self.wait(0.87)
        self.pad_to_voice()
