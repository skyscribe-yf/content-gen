#!/usr/bin/env python3
"""《GAE：100步的功劳，为什么只认最近17步？》视频号 Manim 动画（竖屏 1080×1920）

6 个场景 S1-S6，与 storyboard.md 一一对应（强化学习原理系列第 8 篇）。
- 配音：MiniMax 精英男声（speech-2.8-turbo，speed 1.0，pitch +2），实测总长 340.66s
- 时间轴：at_clip("S1-c01") 挂 tts/sentence-boundaries.json 的 clip 起点（先声音后动画门禁；
 段边界经 ASR + silencedetect 双重定位修正——MiniMax 句子时间戳跨段导致原始切分错位 ~4-9s）
- 布局：整页规划（page_stack + layout_page / page_auto），上下留白各 ≤ 10%
- 动画降噪（决策 #51）：v2 动效 2 处（S3 camera_zoom 成对 / S4 trace_dot）；emphasize 5 次
  （S1 十七步 / S3 惊喜 / S5 六倍+八点五倍 / S6 金句）；每页 1 个主视觉动效
- 数字台词全配动效：counter_value（100 步/100 次/16.8 步/128.1/15.0）+ grow_bar（均摊双条/偏差三条）
- 概念图 3 张（yairouter 深蓝系，无数字）：s1-night-chain / s4-credit-fade / s6-trust-knob
- 预检器约定：段内多拍合并为一拍多动画 play（count≥2）或 at_clip 边界锚定；不用裸 at()；
  连续单动画 reveal 之间插 self.wait 断开 serial_animation

用法（shipinhao 目录内执行）：
  MANIM_STRICT_TIMELINE=1 MANIM_STRICT_WIDTH=1 python3 -m manim render -ql --disable_caching scenes.py S1 .. S6
  MANIM_STRICT_TIMELINE=1 MANIM_STRICT_WIDTH=1 python3 -m manim render -qm --disable_caching scenes.py S1 .. S6
"""
from __future__ import annotations

import pathlib
import sys

import numpy as np


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

# 每段配音时长（tts_split + ASR 修正边界后 ffprobe 实测 tts/sN.wav），渲染时长 = 配音 + TAIL
VOICE_DUR = {"S1": 44.11, "S2": 58.14, "S3": 61.49, "S4": 49.96, "S5": 59.10, "S6": 67.86}
TAIL = 0.1

GAMMA_LAMBDA = 0.9405


def _footer(self) -> Text:
    f = t("数解AI · 强化学习原理", 20, MUTED).to_edge(DOWN, buff=1.15)
    self.add(f)
    return f


def _head(text: str, size: float = 36) -> Text:
    return t(text, size, YELL, "BOLD")


def _img(name: str, width: float) -> ImageMobject:
    im = ImageMobject(str(IMG / name))
    im.scale_to_fit_width(width)
    return im


def _grow_bars(self, specs, run_time: float = 0.9, **kw):
    """多根条同一拍生长（预检器 serial-safe：单次 self.play 多动画）。
    specs: 每项 (bar, target_width, anchor[, extra_anims])，grow_bar 的多条版。"""
    trackers = []
    anims = []
    for spec in specs:
        bar, target, anchor = spec[0], spec[1], spec[2]
        extras = spec[3] if len(spec) > 3 else None
        tr = ValueTracker(0)
        left_bottom = bar.get_corner(DL)
        center_x = bar.get_center()[0]
        self.add(bar)

        def upd(m, bar=bar, tr=tr, anchor=anchor, lb=left_bottom, cx=center_x):
            w = tr.get_value()
            new = Rectangle(width=w, height=bar.height,
                            color=bar.get_stroke_color(),
                            fill_color=bar.get_fill_color(),
                            fill_opacity=bar.get_fill_opacity())
            if anchor == "center":
                new.move_to(np.array([cx, lb[1] + bar.height / 2, 0]))
            else:
                new.move_to(lb + RIGHT * w / 2, aligned_edge=DOWN)
            m.become(new)

        bar.add_updater(upd)
        trackers.append((bar, tr, target))
        anims.append(tr.animate.set_value(target))
        if extras:
            anims.extend(extras)
    self.play(*anims, run_time=run_time, **kw)
    for bar, tr, target in trackers:
        bar.clear_updaters()
        tr.set_value(target)
    return [b for b, _, _ in trackers]


def _dots(rows: int, cols: int, cell: float = 0.29, gap: float = 0.05,
          color: str = CYAN) -> VGroup:
    """rows×cols 点阵（100 步轨迹 / 100 次重复的脚本画图）。"""
    dots = VGroup(*[Rectangle(width=cell, height=cell, color=color, stroke_width=1.2,
                              fill_color=color, fill_opacity=0.35)
                    for _ in range(rows * cols)])
    dots.arrange_in_grid(rows=rows, cols=cols, buff=gap)
    return dots


def _bar_row(lab: str, val_text: str, color: str, ratio: float,
             track_w: float = 3.0, lab_size: int = 26, val_size: int = 26,
             track_h: float = 0.56) -> VGroup:
    """对比条行：左标签 + 底轨 + 目标宽度条 + 右端数值（条宽 = track_w × ratio）。
    条按最终几何入页（稳定 box），生长动画由 _grow_bars 播放。"""
    track = Rectangle(width=track_w, height=track_h, color=MUTED, stroke_width=1.5, fill_opacity=0)
    bar = Rectangle(width=track_w * ratio, height=track_h, color=color,
                    fill_color=color, fill_opacity=0.85)
    bar.move_to(track.get_center())
    bar.align_to(track, LEFT)
    label = t(lab, lab_size, WHITE, "BOLD")
    label.next_to(track, LEFT, buff=0.32)
    val = t(val_text, val_size, color, "BOLD")
    val.next_to(track, RIGHT, buff=0.32)
    val.align_to(track, DOWN)
    return VGroup(label, track, bar, val)


def _decay_axes() -> tuple[VGroup, VMobject]:
    """折扣衰减曲线：0.9405^l（l=0..25），标 1 步/10 步/20 步三点。"""
    ax = Axes(x_range=[0, 25, 5], y_range=[0, 1.05, 0.25],
              x_length=5.6, y_length=3.3,
              axis_config={"color": MUTED, "stroke_width": 2.5,
                           "include_numbers": True, "font_size": 20},
              tips=False)
    curve = ax.plot(lambda l: GAMMA_LAMBDA ** l, x_range=[0, 25], color=YELL, stroke_width=4)
    pts = VGroup()
    for l, lab in [(1, "1 步 0.941"), (10, "10 步 0.541"), (20, "20 步 0.293")]:
        p = ax.coords_to_point(l, GAMMA_LAMBDA ** l)
        dot = Dot(point=p, radius=0.07, color=YELL)
        lb = t(lab, 19, WHITE, "BOLD")
        lb.next_to(dot, UP, buff=0.14)
        pts.add(dot, lb)
    grp = VGroup(ax, curve, pts)
    return grp, curve


def _var_axes() -> tuple[VGroup, VMobject]:
    """λ-方差扫描曲线（蒙特卡洛实测：60 万条轨迹），标 0.95→15.0 / 1→128.1。"""
    xs = [0, 0.5, 0.9, 0.95, 0.99, 1.0]
    ys = [1.03, 1.40, 6.95, 15.0, 60.9, 128.1]
    ax = Axes(x_range=[0, 1.0, 0.25], y_range=[0, 140, 35],
              x_length=5.6, y_length=3.6,
              axis_config={"color": MUTED, "stroke_width": 2.5,
                           "include_numbers": True, "font_size": 20},
              tips=False)
    curve = ax.plot_line_graph(x_values=xs, y_values=ys, line_color=RED,
                               stroke_width=4, add_vertex_dots=False)
    pts = VGroup()
    for x, y, lab, col in [(0.95, 15.0, "0.95 → 15.0", YELL), (1.0, 128.1, "1 → 128.1", RED)]:
        p = ax.coords_to_point(x, y)
        dot = Dot(point=p, radius=0.08, color=col)
        lb = t(lab, 20, col, "BOLD")
        lb.next_to(dot, UP if x < 1 else LEFT, buff=0.14)
        pts.add(dot, lb)
    grp = VGroup(ax, curve, pts)
    return grp, curve


def _diverge_axes() -> tuple[VGroup, VMobject]:
    """1/(1−x) 发散曲线：x=0.9405 → 16.8，x→1 时冲向 100。"""
    ax = Axes(x_range=[0.78, 0.96, 0.06], y_range=[0, 20, 5],
              x_length=5.6, y_length=3.2,
              axis_config={"color": MUTED, "stroke_width": 2.5,
                           "include_numbers": True, "font_size": 20},
              tips=False)
    curve = ax.plot(lambda x: 1.0 / (1.0 - x), x_range=[0.78, 0.955], color=CYAN, stroke_width=4)
    p168 = ax.coords_to_point(0.9405, 1.0 / (1.0 - 0.9405))
    dot = Dot(point=p168, radius=0.09, color=YELL)
    lab = t("0.9405 → 16.8", 20, YELL, "BOLD")
    lab.next_to(dot, UP, buff=0.14)
    arrow = Arrow(ax.coords_to_point(0.955, 17.5), ax.coords_to_point(0.955, 20.5),
                  color=RED, stroke_width=5, max_tip_length_to_length_ratio=0.25)
    lab2 = t("x→1：冲向 100", 20, RED, "BOLD")
    lab2.next_to(arrow, LEFT, buff=0.12)
    lab2.align_to(arrow, UP)
    grp = VGroup(ax, curve, dot, lab, arrow, lab2)
    return grp, curve


# ---------------- S1 开场钩子：一百步的功劳，为什么只认最近十七步 ----------------
class S1(_Base):
    def construct(self):
        self.bg()
        f = _footer(self)

        # 页1：标题 + 深夜概念图（c01-c02）
        head1 = t("一百步的功劳，", 40, YELL, "BOLD")
        head1b = t("为什么只认最近十七步？", 40, YELL, "BOLD")
        note = t("以 coding agent 训练为例", 24, MUTED)
        img = _img("s1-night-chain-round.png", 4.2)
        page1 = page_stack(head1, head1b, note, img, buff=0.65)
        layout_page(page1)

        self.at_clip("S1-c01")
        self.play(type_in(head1, run_time=1.1), type_in(head1b, run_time=1.1),
                  type_in(note, run_time=0.7), run_time=1.1)                        # 0.00 -> 1.10
        self.at_clip("S1-c02")
        self.play(FadeIn(img, shift=DOWN * 0.05), run_time=0.8)                    # 3.60 -> 4.40

        # 页2：一百步链 + 任务成功（c03-c04）
        head2 = _head("一条一百步的工具调用链", 36)
        grid = _dots(10, 10, cell=0.34, gap=0.06)
        cnt_slot = dynamic_slot(2.8, 1.0)
        okT = t("任务成功", 32, GREEN, "BOLD")
        cnt_row = stable_row(cnt_slot, okT, buff=0.5)
        page2 = page_stack(head2, grid, cnt_row, buff=0.8)
        layout_page(page2)

        self.at_clip("S1-c03")
        self.play(FadeOut(head1), FadeOut(head1b), FadeOut(note), FadeOut(img),
                  type_in(head2, run_time=1.0),
                  Create(grid, run_time=1.6, lag_ratio=0.06), run_time=1.6)         # 5.21 -> 6.81
        self.at_clip("S1-c04")
        n100 = self.counter_value(0, 100, suffix=" 步", size=56, color=CYAN, run_time=0.8,
                                  anchor=cnt_slot,
                                  extra_anims=[type_in(okT, run_time=0.5)])         # 9.61 -> 10.41

        # 页3：老板的提问（c05-c07）
        head3 = t("老板问：功劳记给谁？", 44, YELL, "BOLD")
        cBoss = t("总回报拿到了，可每一步到底立了多大功？", 34, WHITE)
        l3 = t("它愣了。", 30, MUTED)
        page_auto(head3, cBoss, l3)

        self.at_clip("S1-c05")
        self.play(FadeOut(head2), FadeOut(grid), FadeOut(n100), FadeOut(okT),
                  type_in(head3, run_time=1.0), run_time=1.0)                      # 10.61 -> 11.61
        self.at_clip("S1-c06")
        self.play(type_in(l3, run_time=0.8), run_time=0.8)                         # 12.61 -> 13.41
        self.at_clip("S1-c07")
        self.play(type_in(cBoss, run_time=1.3), run_time=1.3)                      # 13.61 -> 14.91

        # 页4：73 埋坑 / 81 填坑（c08）
        c73 = _card("73 步：埋了个坑", 6.2, 2.4, RED, WHITE, 34, CARD_FILL, "BOLD")
        c81 = _card("81 步：填上了坑", 6.2, 2.4, GREEN, WHITE, 34, CARD_FILL, "BOLD")
        lQ = t("谁记头功？", 60, YELL, "BOLD")
        page4 = page_stack(c73, c81, lQ, buff=0.8)
        layout_page(page4)

        self.at_clip("S1-c08")
        self.play(FadeOut(head3), FadeOut(cBoss), FadeOut(l3), run_time=0.5)       # 17.71 -> 18.21
        self.play_scroll_unroll_many(c73, c81, run_time=1.3)                       # 18.21 -> 19.51
        self.wait(0.4)
        self.play(type_in(lQ, run_time=0.9))                                       # 19.91 -> 20.81

        # 页5：策略梯度只给整条链打分（c09-c11）
        head4 = _head("策略梯度的账本", 36)
        cA = _card("只给整条链打分", 6.2, 1.6, CYAN, WHITE, 34, CARD_FILL, "BOLD")
        cB = _card("给不出每一步的分账", 6.2, 1.6, RED, WHITE, 34, CARD_FILL, "BOLD")
        cC = _card("训练需要分账：下一步往哪改，靠每一步的功劳", 6.2, 1.9, YELL, WHITE, 30,
                   CARD_FILL, "BOLD")
        page5 = page_stack(head4, cA, cB, cC, buff=0.65)
        layout_page(page5)

        self.at_clip("S1-c09")
        self.play(FadeOut(c73), FadeOut(c81), FadeOut(lQ),
                  type_in(head4, run_time=1.0), run_time=1.0)                      # 22.68 -> 23.68
        self.at_clip("S1-c10")
        self.play_scroll_unroll_many(cA, cC, run_time=1.3)                         # 27.62 -> 28.92
        self.at_clip("S1-c11")
        self.play_scroll_unroll(cB, run_time=1.0)                                  # 32.12 -> 33.12
        self.wait(0.3)
        cross = self.play_red_cross(cB, run_time=0.65)                             # 33.42 -> 34.07

        # 页6：金句（c12-c13）
        line1 = t("功劳按意外大小、按距离远近打折发放", 38, WHITE, "BOLD")
        line2 = t("一百步的功劳，大部分记给最近十七步", 48, YELL, "BOLD")
        page_auto(line1, line2)

        self.at_clip("S1-c12")
        self.play(FadeOut(head4), FadeOut(cA), FadeOut(cB), FadeOut(cC), FadeOut(cross),
                  type_in(line1, run_time=1.3), run_time=1.3)                      # 34.99 -> 36.29
        self.at_clip("S1-c13")
        self.play(type_in(line2, run_time=1.2), run_time=1.2)                      # 40.43 -> 41.63
        self.emphasize(line2, run_time=0.7)                                        # 41.63 -> 42.33
        self.wait(1.38)                                                            # -> 43.71
        self.transition_out(line1, line2, f, run_time=0.4)                         # 43.71 -> 44.11
        self.pad_to_voice()


# ---------------- S2 只记总账，训练就瞎了 ----------------
class S2(_Base):
    def construct(self):
        self.bg()
        f = _footer(self)

        # 页1：做法 A（c01-c03）
        head = t("为什么不能总账照发？", 40, YELL, "BOLD")
        cA = t("做法A：总回报平均摊给每一步", 34, WHITE)
        l2 = t("两个坑", 54, YELL, "BOLD")
        page_auto(head, cA, l2)

        self.at_clip("S2-c01")
        self.play(type_in(head, run_time=1.0), run_time=1.0)                      # 0.01 -> 1.01
        self.at_clip("S2-c02")
        self.play(type_in(cA, run_time=1.2), run_time=1.2)                        # 2.19 -> 3.39
        self.at_clip("S2-c03")
        self.play(type_in(l2, run_time=0.7), run_time=0.7)                        # 5.45 -> 6.15

        # 页2：方差爆炸（c04-c07）
        head2 = _head("坑一：方差爆炸", 38)
        grid2 = _dots(10, 10, cell=0.27, gap=0.045, color=RED)
        cnt2_slot = dynamic_slot(2.8, 1.0)
        cVar = _card("每步都背全链路的运气波动，学不出稳定方向", 6.2, 1.8, RED, WHITE, 30,
                     CARD_FILL, "BOLD")
        page2 = page_stack(head2, grid2, cnt2_slot, cVar, buff=0.6)
        layout_page(page2)

        self.at_clip("S2-c04")
        self.play(FadeOut(head), FadeOut(cA), FadeOut(l2),
                  type_in(head2, run_time=1.0), run_time=1.0)                      # 6.52 -> 7.52
        self.at_clip("S2-c05")
        n100b = self.counter_value(0, 100, suffix=" 次", size=52, color=RED, run_time=0.9,
                                   anchor=cnt2_slot)                              # 11.10 -> 12.00
        self.at_clip("S2-c06")
        self.play(Create(grid2, run_time=1.4, lag_ratio=0.06), run_time=1.4)       # 12.75 -> 14.15
        self.at_clip("S2-c07")
        self.play_scroll_unroll(cVar, run_time=1.2)                               # 16.60 -> 17.80

        # 页3：功劳均摊（c08-c11）
        head3 = _head("坑二：功劳均摊", 38)
        bar73 = _bar_row("73 步 埋坑", "拖后腿", RED, 1.0, track_w=2.8, lab_size=24, val_size=22)
        bar81 = _bar_row("81 步 修复", "力挽狂澜", GREEN, 1.0, track_w=2.8, lab_size=24, val_size=22)
        bars = VGroup(bar73, bar81).arrange(DOWN, buff=0.45)
        cSame = _card("两步记功一样多", 6.0, 2.2, MUTED, WHITE, 34, CARD_FILL, "BOLD")
        lTurn = t("转折点，被淹没了", 34, YELL, "BOLD")
        page3 = page_stack(head3, bars, cSame, lTurn, buff=0.9)
        layout_page(page3)

        self.at_clip("S2-c08")
        self.play(FadeOut(head2), FadeOut(grid2), FadeOut(cnt2_slot), FadeOut(n100b),
                  FadeOut(cVar), type_in(head3, run_time=1.0), run_time=1.0)       # 18.27 -> 19.27
        self.at_clip("S2-c09")
        self._grow_bars_local([
            (bar73[2], 2.8, "left",
             [type_in(bar73[0], run_time=0.5), Create(bar73[1]), type_in(bar73[3], run_time=0.5)]),
            (bar81[2], 2.8, "left",
             [type_in(bar81[0], run_time=0.5), Create(bar81[1]), type_in(bar81[3], run_time=0.5)]),
        ], run_time=1.3)                                                          # 22.15 -> 23.45
        self.at_clip("S2-c10")
        self.play_scroll_unroll(cSame, run_time=1.1)                              # 25.35 -> 26.45
        self.at_clip("S2-c11")
        cross2 = self.play_red_cross(cSame, run_time=0.65)                        # 28.58 -> 29.23
        self.wait(0.25)
        self.play(type_in(lTurn, run_time=0.9))                                    # 29.48 -> 30.38

        # 页4：全归最后一步也不行（c12-c16）
        head4 = t("全归最后一步？", 40, YELL, "BOLD")
        cKick = _card("临门一脚，没有前面九十九步，踢不进去", 6.4, 2.4, CYAN, WHITE, 32,
                      CARD_FILL, "BOLD")
        cBug = _card("bug 第八十一步才爆雷，第七十三步永远不知道自己埋了雷", 6.4, 2.6, RED,
                     WHITE, 30, CARD_FILL, "BOLD")
        page4 = page_stack(head4, cKick, cBug, buff=0.8)
        layout_page(page4)

        self.at_clip("S2-c12")
        self.play(FadeOut(head3), FadeOut(bars), FadeOut(lTurn), FadeOut(cSame),
                  FadeOut(cross2), type_in(head4, run_time=1.0), run_time=1.0)     # 30.66 -> 31.66
        self.at_clip("S2-c13")
        self.play_scroll_unroll(cKick, run_time=1.3)                              # 32.51 -> 33.81
        self.at_clip("S2-c14")
        self.play(FadeOut(cKick), run_time=0.5)                                   # 38.24 -> 38.74
        self.wait(0.2)                                                          # -> 38.94
        self.play_scroll_unroll(cBug, run_time=1.2)                               # 38.94 -> 40.14
        self.at_clip("S2-c16")
        self.play(Flash(cBug), run_time=0.5)                                      # 47.91 -> 48.41

        # 页5：蒙特卡洛 + 悬念（c17-c18）
        lMC = t("总回报给每步各记一份，业界叫蒙特卡洛", 36, WHITE)
        lQ2 = t("可光有总账不行，单步的尺子怎么造？", 44, YELL, "BOLD")
        page_auto(lMC, lQ2)

        self.at_clip("S2-c17")
        self.play(FadeOut(head4), FadeOut(cBug), type_in(lMC, run_time=1.3),
                  run_time=1.3)                                                   # 49.75 -> 51.05
        self.at_clip("S2-c18")
        self.play(type_in(lQ2, run_time=1.2), run_time=1.2)                       # 55.02 -> 56.22
        self.wait(1.52)                                                           # -> 57.74
        self.transition_out(lMC, lQ2, f, run_time=0.4)                            # 57.74 -> 58.14
        self.pad_to_voice()

    def _grow_bars_local(self, specs, run_time: float = 0.9, **kw):
        return _grow_bars(self, specs, run_time=run_time, **kw)


# ---------------- S3 意外：分账的基本单位 ----------------
class S3(_Base):
    def construct(self):
        self.bg()
        f = _footer(self)

        # 页1：δ 公式（c01-c04）
        head = _head("造一把单步尺子", 38)
        formula = MathTex(r"\delta_t = r_t + \gamma\, V(s_{t+1}) - V(s_t)",
                          tex_to_color_map={r"\delta_t": YELL, r"r_t": CYAN,
                                            r"V(s_{t+1})": GREEN, r"V(s_t)": MUTED})
        formula.set_width(6.2)
        lDelta = t("这一步的意外", 40, YELL, "BOLD")
        cF = _card("现实比预期好多少：实际奖励，加打折的未来，减出发前的估值", 6.4, 3.0,
                   YELL, WHITE, 30, CARD_FILL, "BOLD")
        page1 = page_stack(head, formula, lDelta, cF, buff=0.95)
        layout_page(page1)

        self.at_clip("S3-c01")
        self.play(type_in(head, run_time=1.0), FadeIn(formula), run_time=1.0)      # 0.00 -> 1.00
        self.at_clip("S3-c02")
        self.play(type_in(lDelta, run_time=0.8), run_time=0.8)                     # 3.81 -> 4.61
        self.at_clip("S3-c03")
        self.play_scroll_unroll(cF, run_time=1.2)                                 # 5.71 -> 6.91
        self.at_clip("S3-c04")
        self.camera_zoom_to(formula, run_time=0.8)                                # 10.09 -> 10.89
        self.camera_zoom_to(run_time=0.8)                                         # 10.89 -> 11.69

        # 页2：三个符号熟人（c05-c07）
        head2 = _head("三个符号全是熟人", 36)
        cR = _card("奖励 r：这一步实际拿到的", 6.2, 1.5, CYAN, WHITE, 32, CARD_FILL, "BOLD")
        cV = _card("值函数 V：从这里往后还能拿到多少", 6.2, 1.7, GREEN, WHITE, 30,
                   CARD_FILL, "BOLD")
        cG = _card("折扣 γ：未来打九折再九折", 6.2, 1.5, YELL, WHITE, 32, CARD_FILL, "BOLD")
        page2 = page_stack(head2, cR, cV, cG, buff=0.7)
        layout_page(page2)

        self.at_clip("S3-c05")
        self.play(FadeOut(head), FadeOut(formula), FadeOut(lDelta), FadeOut(cF),
                  type_in(head2, run_time=1.0), run_time=1.0)                      # 12.00 -> 13.00
        self.at_clip("S3-c06")
        self.play_scroll_unroll_many(cR, cV, run_time=1.3)                         # 16.87 -> 18.17
        self.at_clip("S3-c07")
        self.play_scroll_unroll(cG, run_time=1.1)                                 # 20.80 -> 21.90

        # 页3：正负零三态（c08-c11）
        head3 = _head("意外的三个符号", 36)
        cPos = _card("大于零：现实比预期好，记功", 6.2, 1.5, GREEN, WHITE, 30, CARD_FILL, "BOLD")
        cNeg = _card("小于零：这一步走错了，扣分", 6.2, 1.5, RED, WHITE, 30, CARD_FILL, "BOLD")
        cZero = _card("等于零：一切如常，无事发生", 6.2, 1.5, MUTED, WHITE, 30, CARD_FILL, "BOLD")
        page3 = page_stack(head3, cPos, cNeg, cZero, buff=0.8)
        layout_page(page3)

        self.at_clip("S3-c08")
        self.play(FadeOut(head2), FadeOut(cR), FadeOut(cV), FadeOut(cG),
                  type_in(head3, run_time=1.0), run_time=1.0)                      # 23.58 -> 24.58
        self.at_clip("S3-c09")
        self.play_scroll_unroll(cPos, run_time=0.9)                               # 26.56 -> 27.46
        self.at_clip("S3-c10")
        self.play_scroll_unroll(cNeg, run_time=0.9)                               # 28.21 -> 29.11
        self.at_clip("S3-c11")
        self.play_scroll_unroll(cZero, run_time=0.9)                              # 29.86 -> 30.76

        # 页4：学名 TD error（c12-c13）
        head4 = t("这个意外，学名 TD error", 40, YELL, "BOLD")
        lTD = t("别管名字，记住它是意外", 34, WHITE)
        page_auto(head4, lTD)

        self.at_clip("S3-c12")
        self.play(FadeOut(head3), FadeOut(cPos), FadeOut(cNeg), FadeOut(cZero),
                  type_in(head4, run_time=1.0), run_time=1.0)                      # 31.99 -> 32.99
        self.at_clip("S3-c13")
        self.play(type_in(lTD, run_time=1.0), run_time=1.0)                       # 35.53 -> 36.53

        # 页5：预期差不是绝对收获（c14-c17）
        head5 = _head("意外是预期差，不是绝对收获", 38)
        cA1 = _card("一步只赚 0.1，预期 0.05，意外是正的", 6.4, 1.9, GREEN, WHITE, 30,
                    CARD_FILL, "BOLD")
        cA2 = _card("一步赚 5，预期 6，意外是负的", 6.4, 1.9, RED, WHITE, 30,
                    CARD_FILL, "BOLD")
        barA = _bar_row("意外", "+0.05", GREEN, 0.32, track_w=2.8, lab_size=22, val_size=22)
        barB = _bar_row("意外", "-1", RED, 0.62, track_w=2.8, lab_size=22, val_size=22)
        bars2 = VGroup(barA, barB).arrange(DOWN, buff=0.45)
        lGold = t("功劳不看收获，看惊喜", 48, YELL, "BOLD")
        page5 = page_stack(head5, cA1, cA2, bars2, lGold, buff=0.7)
        layout_page(page5)

        self.at_clip("S3-c14")
        self.play(FadeOut(head4), FadeOut(lTD), type_in(head5, run_time=1.1),
                  run_time=1.1)                                                   # 38.46 -> 39.56
        self.at_clip("S3-c15")
        self.play_scroll_unroll(cA1, run_time=1.2)                                # 43.81 -> 45.01
        self.wait(0.3)
        self._grow_bars_local([
            (barA[2], 2.8 * 0.32, "left",
             [type_in(barA[0], run_time=0.4), Create(barA[1]), type_in(barA[3], run_time=0.4)]),
        ], run_time=0.7)                                                          # 45.31 -> 46.01
        self.at_clip("S3-c16")
        self.play_scroll_unroll(cA2, run_time=1.2)                                # 48.85 -> 50.05
        self.wait(0.3)
        self._grow_bars_local([
            (barB[2], 2.8 * 0.62, "left",
             [type_in(barB[0], run_time=0.4), Create(barB[1]), type_in(barB[3], run_time=0.4)]),
        ], run_time=0.7)                                                          # 50.35 -> 51.05
        self.at_clip("S3-c17")
        self.play(type_in(lGold, run_time=1.0), run_time=1.0)                     # 54.62 -> 55.62
        self.emphasize(lGold, run_time=0.7)                                       # 55.62 -> 56.32

        # 页6：悬念（c18）
        lQ3 = t("可惊喜只有一步，一百步的总功劳怎么汇总？", 44, YELL, "BOLD")
        page_auto(lQ3)

        self.at_clip("S3-c18")
        self.play(FadeOut(head5), FadeOut(cA1), FadeOut(cA2), FadeOut(bars2),
                  FadeOut(lGold), type_in(lQ3, run_time=1.2), run_time=1.2)        # 57.47 -> 58.67
        self.wait(2.42)                                                           # -> 61.09
        self.transition_out(lQ3, f, run_time=0.4)                                 # 61.09 -> 61.49
        self.pad_to_voice()

    def _grow_bars_local(self, specs, run_time: float = 0.9, **kw):
        return _grow_bars(self, specs, run_time=run_time, **kw)


# ---------------- S4 功劳分摊器：把意外按指数打折汇总 ----------------
class S4(_Base):
    def construct(self):
        self.bg()
        f = _footer(self)

        # 页1：GAE 公式（c01-c04）
        head = _head("把意外收进来，越远折得越狠", 36)
        formula2 = MathTex(r"\hat{A}_t = \sum_{l=0}^{\infty} (\gamma\lambda)^l\, \delta_{t+l}",
                           tex_to_color_map={r"\hat{A}_t": YELL, r"\delta_{t+l}": CYAN})
        formula2.set_width(6.4)
        lSub = t("以某一步为起点，", 30, WHITE)
        lSub1b = t("把往后的每一步意外都收进来", 30, WHITE)
        lSub2 = t("越远，折得越狠", 36, YELL, "BOLD")
        cGAE = _card("这就是 GAE 的全部", 6.0, 1.8, YELL, WHITE, 34, CARD_FILL, "BOLD")
        page1 = page_stack(head, formula2, lSub, lSub1b, lSub2, cGAE, buff=0.65)
        layout_page(page1)

        self.at_clip("S4-c01")
        self.play(type_in(head, run_time=1.0), FadeIn(formula2), run_time=1.0)     # 0.00 -> 1.00
        self.at_clip("S4-c02")
        self.play(type_in(lSub, run_time=1.3), type_in(lSub1b, run_time=1.3),
                  run_time=1.3)                                                   # 4.12 -> 5.42
        self.at_clip("S4-c03")
        self.play(type_in(lSub2, run_time=0.8), run_time=0.8)                      # 8.43 -> 9.23
        self.at_clip("S4-c04")
        self.play_scroll_unroll(cGAE, run_time=1.0)                               # 9.80 -> 10.80

        # 页2：折扣衰减曲线（c05-c07）
        head2 = t("γλ = 0.9405", 40, YELL, "BOLD")
        decay, curve = _decay_axes()
        c94 = _card("折一次剩百分之九十四，折到第二十步只剩三成", 6.4, 1.8, CYAN, WHITE,
                    30, CARD_FILL, "BOLD")
        page2 = page_stack(head2, decay, c94, buff=0.75)
        layout_page(page2)

        self.at_clip("S4-c05")
        self.play(FadeOut(head), FadeOut(formula2), FadeOut(lSub), FadeOut(lSub1b),
                  FadeOut(lSub2), FadeOut(cGAE), type_in(head2, run_time=1.0),
                  run_time=1.0)                                                   # 11.87 -> 12.87
        self.at_clip("S4-c06")
        self.play(FadeIn(decay, shift=DOWN * 0.05), Create(curve, run_time=1.4),
                  run_time=1.4)                                                   # 16.60 -> 18.00
        dot = self.trace_dot(curve, run_time=1.6)                                 # 18.00 -> 19.60
        self.at_clip("S4-c07")
        self.play_scroll_unroll(c94, run_time=1.2)                                # 21.78 -> 22.98

        # 页3：功劳回传概念图（c08-c09）
        head3 = _head("越传越淡", 36)
        img = _img("s4-credit-fade-round.png", 4.3)
        lFade = t("传得出去，但越传越淡", 32, WHITE)
        page3 = page_stack(head3, img, lFade, buff=0.9)
        layout_page(page3)

        self.at_clip("S4-c08")
        self.play(FadeOut(head2), FadeOut(decay), FadeOut(curve), FadeOut(dot),
                  FadeOut(c94), type_in(head3, run_time=0.9),
                  FadeIn(img, shift=DOWN * 0.05), run_time=0.9)                    # 24.46 -> 25.36
        self.at_clip("S4-c09")
        self.play(type_in(lFade, run_time=0.9), run_time=0.9)                      # 28.80 -> 29.70

        # 页4：73/81 回传（c10-c11）
        head4 = _head("记功，但不是满功", 36)
        n73 = Dot(point=LEFT * 2.2, radius=0.2, color=RED)
        n81 = Dot(point=RIGHT * 2.2, radius=0.2, color=GREEN)
        base = Line(LEFT * 3.0, RIGHT * 3.0, color=MUTED, stroke_width=2.5)
        back = Arrow(n81.get_left() + LEFT * 0.15, n73.get_right() + RIGHT * 0.15,
                     color=YELL, stroke_width=4.5, max_tip_length_to_length_ratio=0.22)
        l73 = t("73 埋坑", 28, RED, "BOLD")
        l73.next_to(n73, DOWN, buff=0.22)
        l81 = t("81 填坑", 28, GREEN, "BOLD")
        l81.next_to(n81, DOWN, buff=0.22)
        lBack = t("意外要打八次折才传回来", 30, YELL, "BOLD")
        lBack.next_to(back, UP, buff=0.2)
        row = VGroup(base, n73, n81, back, l73, l81, lBack)
        cFade = _card("81 步的意外按折扣传到 73 步头上：记功，但不是满功", 6.4, 3.0,
                      YELL, WHITE, 30, CARD_FILL, "BOLD")
        page4 = page_stack(head4, row, cFade, buff=1.0)
        layout_page(page4)

        self.at_clip("S4-c10")
        self.play(FadeOut(head3), FadeOut(img), FadeOut(lFade),
                  type_in(head4, run_time=1.0), run_time=1.0)                      # 29.99 -> 30.99
        self.play(FadeIn(row, shift=UP * 0.05), run_time=0.7)                      # 30.99 -> 31.69
        self.at_clip("S4-c11")
        self.play_scroll_unroll(cFade, run_time=1.1)                              # 36.12 -> 37.22

        # 页5：有效视野（c12-c13）
        head5 = _head("有效视野", 40)
        formula3 = MathTex(r"\frac{1}{1-\gamma\lambda}",
                           tex_to_color_map={r"\gamma\lambda": YELL})
        formula3.set_width(3.6)
        cEff = _card("GAE 实际上看多远", 6.0, 1.6, CYAN, WHITE, 34, CARD_FILL, "BOLD")
        cnt_slot = dynamic_slot(3.0, 1.1)
        page5 = page_stack(head5, formula3, cEff, cnt_slot, buff=0.85)
        layout_page(page5)

        self.at_clip("S4-c12")
        self.play(FadeOut(head4), FadeOut(row), FadeOut(cFade),
                  type_in(head5, run_time=1.0), FadeIn(formula3), run_time=1.0)    # 38.29 -> 39.29
        self.play_scroll_unroll(cEff, run_time=1.1)                               # 39.29 -> 40.39
        self.at_clip("S4-c13")
        n168 = self.counter_value(0, 16.8, suffix=" 步", decimals=1, size=60, color=YELL,
                                  run_time=1.1, anchor=cnt_slot)                  # 43.26 -> 44.36

        # 页6：悬念（c14）
        lQ4 = t("那这套折扣，到底看多远？", 40, YELL, "BOLD")
        page_auto(lQ4)

        self.at_clip("S4-c14")
        self.play(FadeOut(head5), FadeOut(formula3), FadeOut(cEff), FadeOut(n168),
                  type_in(lQ4, run_time=1.0), run_time=1.0)                        # 47.37 -> 48.37
        self.wait(1.19)                                                           # -> 49.56
        self.transition_out(lQ4, f, run_time=0.4)                                 # 49.56 -> 49.96
        self.pad_to_voice()


# ---------------- S5 0.05 的距离：16.8 步和 100 步 ----------------
class S5(_Base):
    def construct(self):
        self.bg()
        f = _footer(self)

        # 页1：16.8 vs 100（c01-c04）
        head = _head("把数值放进去", 36)
        labA = t("λ=0.95", 32, WHITE, "BOLD")
        labB = t("λ=1", 32, CYAN, "BOLD")
        slotA = dynamic_slot(2.2, 1.1)
        slotB = dynamic_slot(2.2, 1.1)
        stepT = t("步", 30, MUTED, "BOLD")
        labs = stable_row(labA, labB, buff=1.9)
        cnts = stable_row(slotA, VGroup(slotB, stepT).arrange(RIGHT, buff=0.15), buff=1.9)
        c6x = _card("只差 0.05，差了 6 倍", 6.2, 2.2, YELL, WHITE, 36, CARD_FILL, "BOLD")
        page1 = page_stack(head, labs, cnts, c6x, buff=1.0)
        layout_page(page1)

        self.at_clip("S5-c01")
        self.play(type_in(head, run_time=0.8), run_time=0.8)                      # 0.00 -> 0.80
        self.at_clip("S5-c02")
        n1 = self.counter_value(0, 16.8, suffix=" 步", decimals=1, size=56, color=YELL,
                                run_time=1.2, anchor=slotA,
                                extra_anims=[type_in(labA, run_time=0.5)])         # 1.44 -> 2.64
        self.at_clip("S5-c03")
        self.wait(0.3)
        tr2 = ValueTracker(0)
        num2 = DecimalNumber(0, mob_class=Text, num_decimal_places=0, font_size=56, color=CYAN)
        num2.move_to(slotB.get_center())
        num2.add_updater(lambda m: m.set_value(tr2.get_value()))
        self.add(num2)
        self.play(tr2.animate.set_value(100), type_in(labB, run_time=0.5),
                  type_in(stepT, run_time=0.5), run_time=1.1)                      # 5.95 -> 7.05
        self.at_clip("S5-c04")
        self.play_scroll_unroll(c6x, run_time=1.0)                                # 8.41 -> 9.41
        self.emphasize(c6x, run_time=0.7)                                         # 9.41 -> 10.11

        # 页2：为什么敏感（c05-c07）
        head2 = t("为什么敏感？", 40, YELL, "BOLD")
        dive, curve2 = _diverge_axes()
        lD1 = t("x 越逼近 1，越发散", 32, WHITE)
        lD2 = t("越接近全部看，越容不得折扣", 36, YELL, "BOLD")
        page2 = page_stack(head2, dive, lD1, lD2, buff=0.85)
        layout_page(page2)

        self.at_clip("S5-c05")
        self.play(FadeOut(head), FadeOut(labs), FadeOut(cnts), FadeOut(num2),
                  FadeOut(stepT), FadeOut(c6x), FadeOut(n1), type_in(head2, run_time=0.9),
                  run_time=0.9)                                                   # 10.87 -> 11.77
        self.at_clip("S5-c06")
        self.play(FadeIn(dive, shift=DOWN * 0.05), Create(curve2, run_time=1.2),
                  type_in(lD1, run_time=0.8), run_time=1.2)                       # 12.30 -> 13.50
        self.at_clip("S5-c07")
        self.play(type_in(lD2, run_time=1.0), run_time=1.0)                       # 15.64 -> 16.64

        # 页3：旋钮三档（c08-c11）
        head3 = _head("λ 旋钮三档", 36)
        c0 = _card("λ=0：只看这一步的意外", 6.2, 1.6, GREEN, WHITE, 32, CARD_FILL, "BOLD")
        c1 = _card("λ=1：看全程，等价蒙特卡洛", 6.2, 1.6, RED, WHITE, 32, CARD_FILL, "BOLD")
        c95 = _card("λ=0.95：中间档，最近 17 步全收", 6.2, 1.6, YELL, WHITE, 32,
                    CARD_FILL, "BOLD")
        page3 = page_stack(head3, c0, c1, c95, buff=0.8)
        layout_page(page3)

        self.at_clip("S5-c08")
        self.play(FadeOut(head2), FadeOut(dive), FadeOut(curve2), FadeOut(lD1),
                  FadeOut(lD2), type_in(head3, run_time=0.9), run_time=0.9)        # 18.96 -> 19.86
        self.at_clip("S5-c09")
        self.play_scroll_unroll_many(c0, c1, run_time=1.2)                        # 21.72 -> 22.92
        self.at_clip("S5-c10")
        self.play_scroll_unroll(c95, run_time=1.0)                                # 24.67 -> 25.67
        self.at_clip("S5-c11")
        lQ5 = t("那为什么都用 0.95，没人敢用 1？", 40, YELL, "BOLD")
        page_auto(lQ5)
        self.play(FadeOut(head3), FadeOut(c0), FadeOut(c1), FadeOut(c95),
                  type_in(lQ5, run_time=1.1), run_time=1.1)                       # 26.44 -> 27.54

        # 页4：实测方差（c12-c15）
        head4 = _head("三十格走廊，六十万条轨迹", 36)
        varg, curve3 = _var_axes()
        lab128 = t("λ=1", 26, RED, "BOLD")
        lab15 = t("λ=0.95", 26, YELL, "BOLD")
        slot128 = dynamic_slot(2.2, 1.0)
        slot15 = dynamic_slot(2.2, 1.0)
        cntRow = stable_row(lab128, slot128, lab15, slot15, buff=0.55)
        l85 = t("八点五倍", 40, YELL, "BOLD")
        page4 = page_stack(head4, varg, cntRow, l85, buff=0.7)
        layout_page(page4)

        self.at_clip("S5-c12")
        self.play(FadeOut(lQ5), type_in(head4, run_time=1.0), run_time=1.0)        # 29.88 -> 30.88
        self.at_clip("S5-c13")
        self.play(FadeIn(varg, shift=DOWN * 0.05), Create(curve3, run_time=1.3),
                  type_in(lab128, run_time=0.5), type_in(lab15, run_time=0.5),
                  run_time=1.3)                                                   # 33.97 -> 35.27
        self.at_clip("S5-c14")
        n128 = self.counter_value(0, 128.1, decimals=1, size=52, color=RED, run_time=1.0,
                                  anchor=slot128)                                 # 36.21 -> 37.21
        self.at_clip("S5-c15")
        n15 = self.counter_value(0, 15.0, decimals=1, size=52, color=YELL, run_time=1.0,
                                 anchor=slot15)                                   # 38.87 -> 39.87
        self.wait(0.3)
        self.play(type_in(l85, run_time=0.8))                                      # 40.17 -> 40.97
        self.emphasize(l85, run_time=0.7)                                         # 40.97 -> 41.67

        # 页5：为什么真实反而方差最大（c16-c18）
        head5 = _head("为什么真实反而方差最大？", 38)
        cLuck = _card("一百份运气叠起来，方差不炸才怪", 6.2, 2.4, CYAN, WHITE, 32,
                      CARD_FILL, "BOLD")
        cNoise = _card("0.95 只收最近 17 步，远处噪声被折扣挡在门外", 6.2, 2.6, GREEN,
                       WHITE, 30, CARD_FILL, "BOLD")
        page5 = page_stack(head5, cLuck, cNoise, buff=0.95)
        layout_page(page5)

        self.at_clip("S5-c16")
        self.play(FadeOut(head4), FadeOut(varg), FadeOut(curve3), FadeOut(cntRow),
                  FadeOut(l85), FadeOut(n128), FadeOut(n15),
                  type_in(head5, run_time=1.0), run_time=1.0)                      # 43.36 -> 44.36
        self.at_clip("S5-c17")
        self.play_scroll_unroll(cLuck, run_time=1.2)                              # 45.70 -> 46.90
        self.at_clip("S5-c18")
        self.play_scroll_unroll(cNoise, run_time=1.2)                             # 48.82 -> 50.02

        # 页6：金句 + 悬念（c19-c20）
        lGold5 = t("真实，不等于好用", 48, YELL, "BOLD")
        lQ6 = t("可 critic 估错了，这笔账怎么算？", 40, YELL, "BOLD")
        page_auto(lGold5, lQ6)

        self.at_clip("S5-c19")
        self.play(FadeOut(head5), FadeOut(cLuck), FadeOut(cNoise),
                  type_in(lGold5, run_time=1.0), run_time=1.0)                     # 53.49 -> 54.49
        self.at_clip("S5-c20")
        self.play(type_in(lQ6, run_time=1.1), run_time=1.1)                       # 55.25 -> 56.35
        self.wait(2.35)                                                           # -> 58.70
        self.transition_out(lGold5, lQ6, f, run_time=0.4)                         # 58.70 -> 59.10
        self.pad_to_voice()


# ---------------- S6 λ 是信任旋钮 + 结账 + 尾卡 ----------------
class S6(_Base):
    def construct(self):
        self.bg()
        f = _footer(self)

        # 页1：critic 老师网络（c01-c03）
        head = _head("λ=1 不是没有代价的自由", 36)
        cTeach = _card("critic 是给每步估值的老师网络，现实中永远有拟合误差", 6.4, 3.8,
                       CYAN, WHITE, 32, CARD_FILL, "BOLD")
        lNote = t("RLHF 的老朋友", 28, MUTED)
        page1 = page_stack(head, cTeach, lNote, buff=1.2)
        layout_page(page1)

        self.at_clip("S6-c01")
        self.play(type_in(head, run_time=1.0), run_time=1.0)                      # 0.00 -> 1.00
        self.at_clip("S6-c02")
        self.play_scroll_unroll(cTeach, run_time=1.2)                             # 3.07 -> 4.27
        self.at_clip("S6-c03")
        self.play(type_in(lNote, run_time=0.8), run_time=0.8)                     # 6.02 -> 6.82

        # 页2：误差进账三条（c04-c06）
        head2 = _head("误差怎么进账", 36)
        b1 = _bar_row("λ=1", "-0.39", RED, 1.0, track_w=2.6, lab_size=26, val_size=26, track_h=0.9)
        b2 = _bar_row("λ=0.95", "-0.09", YELL, 0.23, track_w=2.6, lab_size=26, val_size=26, track_h=0.9)
        b3 = _bar_row("λ=0", "-0.00", GREEN, 0.04, track_w=2.6, lab_size=26, val_size=26, track_h=0.9)
        bars3 = VGroup(b1, b2, b3).arrange(DOWN, buff=0.5)
        lNote2 = t("λ 小，误差只影响相邻步；λ 大，误差走完全程", 28, MUTED)
        page2 = page_stack(head2, bars3, lNote2, buff=1.3)
        layout_page(page2)

        self.at_clip("S6-c04")
        self.play(FadeOut(head), FadeOut(cTeach), FadeOut(lNote),
                  type_in(head2, run_time=1.0), run_time=1.0)                      # 8.02 -> 9.02
        self.at_clip("S6-c05")
        self._grow_bars_local([
            (b1[2], 2.6, "left",
             [type_in(b1[0], run_time=0.4), Create(b1[1]), type_in(b1[3], run_time=0.4)]),
            (b2[2], 2.6 * 0.23, "left",
             [type_in(b2[0], run_time=0.4), Create(b2[1]), type_in(b2[3], run_time=0.4)]),
        ], run_time=1.3)                                                          # 13.86 -> 15.16
        self.at_clip("S6-c06")
        self._grow_bars_local([
            (b3[2], 2.6 * 0.04, "left",
             [type_in(b3[0], run_time=0.4), Create(b3[1]), type_in(b3[3], run_time=0.4)]),
        ], run_time=0.8)                                                          # 18.30 -> 19.10
        self.play(type_in(lNote2, run_time=0.8), run_time=0.8)                    # 19.10 -> 19.90

        # 页3：信任旋钮 + 往 0 拨（c07-c08）
        head3 = _head("λ 是信任旋钮", 36)
        img = _img("s6-trust-knob-round.png", 4.2)
        c0d = _card("往 0 拨：方差最小，但把 critic 当圣旨", 6.2, 1.8, GREEN, WHITE, 30,
                    CARD_FILL, "BOLD")
        page3 = page_stack(head3, img, c0d, buff=1.0)
        layout_page(page3)

        self.at_clip("S6-c07")
        self.play(FadeOut(head2), FadeOut(bars3), FadeOut(lNote2),
                  type_in(head3, run_time=1.0), FadeIn(img, shift=DOWN * 0.05),
                  run_time=1.0)                                                   # 23.18 -> 24.18
        self.at_clip("S6-c08")
        self.play_scroll_unroll(c0d, run_time=1.2)                                # 26.32 -> 27.52

        # 页4：往 1 拨 + 0.95 的智慧（c09-c11）
        head4 = _head("往 1 拨", 36)
        c1d = _card("只信实测，可方差炸裂", 6.2, 2.2, RED, WHITE, 32, CARD_FILL, "BOLD")
        c95d = _card("0.95 的智慧：信最近 17 步的实测功劳，远处交给折扣，critic 只当辅助",
                     6.2, 2.6, YELL, WHITE, 28, CARD_FILL, "BOLD")
        page4 = page_stack(head4, c1d, c95d, buff=1.0)
        layout_page(page4)

        self.at_clip("S6-c09")
        self.play(FadeOut(head3), FadeOut(img), FadeOut(c0d),
                  type_in(head4, run_time=0.9), run_time=0.9)                      # 28.69 -> 29.59
        self.at_clip("S6-c10")
        self.play_scroll_unroll(c1d, run_time=1.2)                                # 31.64 -> 32.84
        self.at_clip("S6-c11")
        self.play_scroll_unroll(c95d, run_time=1.3)                               # 35.57 -> 36.87

        # 页5：工程平衡点（c12-c13）
        head5 = t("这就是 PPO 默认 0.95 的原因", 40, YELL, "BOLD")
        lPPO1 = t("不是玄学，是工程平衡点", 44, WHITE, "BOLD")
        page_auto(head5, lPPO1)

        self.at_clip("S6-c12")
        self.play(FadeOut(head4), FadeOut(c1d), FadeOut(c95d),
                  type_in(head5, run_time=1.1), run_time=1.1)                      # 39.21 -> 40.31
        self.at_clip("S6-c13")
        self.play(type_in(lPPO1, run_time=1.0), run_time=1.0)                     # 42.86 -> 43.86

        # 页6：结账 + 金句（c14-c17）
        head6 = _head("结账", 40)
        l1 = t("功劳不归最后一步，也不均分", 34, WHITE)
        l2 = t("每步记的是意外，按折扣往后传", 34, WHITE)
        lGold6 = t("GAE 不是估回报，是把功劳打折发放", 44, YELL, "BOLD")
        page_auto(head6, l1, l2, lGold6)

        self.at_clip("S6-c14")
        self.play(FadeOut(head5), FadeOut(lPPO1), type_in(head6, run_time=0.9),
                  run_time=0.9)                                                   # 45.82 -> 46.72
        self.at_clip("S6-c15")
        self.play(type_in(l1, run_time=1.0), run_time=1.0)                        # 49.69 -> 50.69
        self.at_clip("S6-c16")
        self.play(type_in(l2, run_time=1.0), run_time=1.0)                        # 51.52 -> 52.52
        self.at_clip("S6-c17")
        self.play(type_in(lGold6, run_time=1.3), run_time=1.3)                    # 53.77 -> 55.07
        self.emphasize(lGold6, run_time=0.8)                                      # 55.07 -> 55.87

        # 页7：品牌尾卡（c18-c20）
        avatar = ImageMobject(str(AVATAR))
        avatar.scale_to_fit_width(3.4)
        lFollow = t("关注「数解AI」", 40, YELL, "BOLD")
        lTitle = t("GAE：100步的功劳，\n为什么只认最近17步？", 30, WHITE, "BOLD",
                   line_spacing=0.7)
        lGuide = t("查看公众号文章", 30, GREEN, "BOLD")
        lNext = t("下一篇：GRPO 把 critic 连锅端", 26, MUTED)
        lQ7 = t("团队分功劳，你见过最离谱的算法？", 30, YELL)
        page7 = page_stack(avatar, lFollow, lTitle, lGuide, lNext, lQ7, buff=0.38)
        layout_page(page7)

        self.at_clip("S6-c18")
        self.play(FadeOut(head6), FadeOut(l1), FadeOut(l2), FadeOut(lGold6),
                  FadeIn(avatar, shift=DOWN * 0.05), type_in(lFollow, run_time=0.9),
                  run_time=0.9)                                                   # 58.53 -> 59.43
        self.at_clip("S6-c19")
        self.play(type_in(lTitle, run_time=1.2), run_time=1.2)                    # 62.30 -> 63.50
        self.at_clip("S6-c20")
        self.play(type_in(lGuide, run_time=0.7), type_in(lNext, run_time=0.7),
                  type_in(lQ7, run_time=0.7), run_time=0.9)                        # 66.47 -> 67.37
        self.pad_to_voice()

    def _grow_bars_local(self, specs, run_time: float = 0.9, **kw):
        return _grow_bars(self, specs, run_time=run_time, **kw)
