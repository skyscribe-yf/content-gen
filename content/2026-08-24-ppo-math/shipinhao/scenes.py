#!/usr/bin/env python3
"""《PPO只用0.2的clip，凭什么顶替0.01预算？》视频号 Manim 动画（竖屏 1080×1920）

6 个场景 S1-S6，与 storyboard.md 一一对应（强化学习原理系列第 7 篇）。
- 配音：MiniMax 精英男声（speech-2.8-turbo，speed 1.0，pitch +2）
- 时间轴：at_clip("S1-c01") 挂 tts/sentence-boundaries.json 的 clip 起点（先声音后动画门禁）
- 布局：整页规划（page_stack + layout_page / page_auto），上下留白各 ≤ 10%
- 动画降噪（决策 #51）：emphasize 全片 5 次（S1 bigMin / S3 row223 / S4 表盘同一 / S5 KL 上界 0.025 / S6 金句卡），
  v2 动效 3 处（S4 morph_to 公式拼桥 / S5 camera_zoom 成对推拉 / S1 breathe 点阵）；每页 1 个主视觉动效；
  数字台词全部配 counter_value / grow_bar（多根条用 _grow_bars 同拍生长）
- 预检器约定：段内多拍用「合并多动画 play（count≥2）」或 at_clip 边界锚定，不用裸 at()（at_not_on_boundary），
  不用 at_clip offset（checker 按 clip 原始起点算 next_at 会误报 overrun）

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

# 每段配音时长（tts_split.py 实测 tts/sN.wav），渲染时长 = 配音 + TAIL
VOICE_DUR = {"S1": 34.97, "S2": 40.29, "S3": 36.03, "S4": 33.93, "S5": 37.68, "S6": 40.82}
TAIL = 0.1

TRACK_W = 3.2


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


def _step_row(lab: str, ratio: float, value_text: str, color: str,
              lab_size: int = 24, track_w: float = TRACK_W) -> VGroup:
    """对比条：左标签 + 长度正比 ratio 的条（_grow_bars 用）+ 条右端数值。"""
    track = Rectangle(width=track_w, height=0.62, color=MUTED, stroke_width=1.5, fill_opacity=0)
    bar = Rectangle(width=max(track_w * ratio, 0.07), height=0.62, color=color,
                    fill_color=color, fill_opacity=0.8)
    bar.move_to(track.get_center())
    bar.align_to(track, LEFT)
    label = t(lab, lab_size, WHITE, "BOLD")
    label.next_to(track, LEFT, buff=0.38)
    val = t(value_text, 24, color, "BOLD")
    val.next_to(track, RIGHT, buff=0.38)
    val.align_to(track, DOWN)
    return VGroup(label, track, bar, val)


def _num_row(lab: str, width: float = 2.6, height: float = 1.1):
    """静态标签 + 动态数字槽位（同拍出现；动态值先占位后滚动）。"""
    slot = dynamic_slot(width, height)
    row = stable_row(t(lab, 26, WHITE, "BOLD"), slot, buff=0.40)
    return row, slot


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


def _rx(r: float) -> float:
    """r 值 → 数轴 x 坐标（0.8 → -1.6，1.0 → 0，1.2 → +1.6，1.3 → +2.4）。"""
    return (r - 1.0) * 8.0


def _r_axis() -> VGroup:
    """r 数轴 + [0.8, 1.2] 高亮带 + 0.8/1.0/1.2 刻度标签。"""
    base = Line(LEFT * 2.9, RIGHT * 2.9, color=MUTED, stroke_width=3)
    band = Rectangle(width=_rx(1.2) - _rx(0.8), height=0.44,
                     color=GREEN, stroke_width=1.5,
                     fill_color=GREEN, fill_opacity=0.14)
    band.move_to(ORIGIN)
    ticks = VGroup()
    for rv, lab in [(0.8, "0.8"), (1.0, "1.0"), (1.2, "1.2")]:
        tk = Line(UP * 0.14, DOWN * 0.14, color=MUTED, stroke_width=2.5)
        tk.move_to(RIGHT * _rx(rv))
        lb = t(lab, 24, WHITE, "BOLD")
        lb.next_to(tk, DOWN, buff=0.18)
        ticks.add(tk, lb)
    return VGroup(base, band, ticks)


def _mc_row(lab: str, va: float, vb: float, scale: float) -> VGroup:
    """蒙特卡洛一组：真值条（青）+ 公式条（黄）上下成对 + 数值标签。"""
    barA = Rectangle(width=va * scale, height=0.30, color=CYAN,
                     fill_color=CYAN, fill_opacity=0.8)
    barB = Rectangle(width=vb * scale, height=0.30, color=YELL,
                     fill_color=YELL, fill_opacity=0.8)
    bars = VGroup(barA, barB).arrange(DOWN, buff=0.10)
    labm = t(lab, 24, WHITE, "BOLD")
    labm.next_to(bars, LEFT, buff=0.30)
    val = t(f"{va:.4f} / {vb:.4f}", 21, MUTED)
    val.next_to(bars, RIGHT, buff=0.30)
    return VGroup(labm, bars, val)


# ---------------- S1 开场钩子：一行 min，凭什么顶替矩阵求逆 ----------------
class S1(_Base):
    def construct(self):
        self.bg()
        f = _footer(self)

        # 页1：深夜双 agent（c01-c04）
        head = _head("一句 clip，顶替矩阵求逆", 36)
        note = t("以 coding agent 训练为例", 24, MUTED)
        img = _img("s1-two-agents-round.png", 4.2)
        cB = _card("B：TRPO，每步先解矩阵求逆", 5.8, 1.3, RED, WHITE, 31, CARD_FILL, "BOLD")
        page1 = page_stack(head, note, img, cB, buff=0.8)
        layout_page(page1)

        self.at_clip("S1-c01")
        self.play(type_in(head, run_time=1.0), type_in(note, run_time=0.7), run_time=1.0)  # 0 -> 1.0
        self.at_clip("S1-c03")
        self.play(FadeIn(img, shift=DOWN * 0.05), run_time=0.8)                            # 5.50 -> 6.30
        self.at_clip("S1-c04")
        self.play_scroll_unroll(cB, run_time=1.1)                                          # 9.14 -> 10.24

        # 页2：10 亿参数，10^18 个数（c05-c06）
        head2 = _head("参数到 10 亿", 36)
        rowP, slotP = _num_row("N×N 矩阵元素个数")
        cells = VGroup(*[Rectangle(width=0.42, height=0.42, stroke_color=CYAN, stroke_width=1.2,
                                   fill_color=CYAN, fill_opacity=0.12)
                         for _ in range(66)])
        cells.arrange_in_grid(rows=6, cols=11, buff=0.06)
        mtx = MathTex(r"N\times N\ \Rightarrow\ 10^{18}", tex_to_color_map={r"10^{18}": YELL})
        mtx.set_width(4.6)
        cSand = _card("地球上所有沙子的量级", 5.6, 1.2, YELL, WHITE, 32, CARD_FILL, "BOLD")
        page2 = page_stack(head2, rowP, cells, mtx, cSand, buff=0.48)
        layout_page(page2)

        self.at_clip("S1-c05")
        self.play(FadeOut(head), FadeOut(note), FadeOut(img), FadeOut(cB),
                  type_in(head2, run_time=0.9), run_time=0.9)                              # 12.70 -> 13.60
        nP = self.counter_value(0, 10, suffix=" 亿", size=54, color=CYAN, run_time=0.8,
                                anchor=slotP,
                                extra_anims=[type_in(rowP[0], run_time=0.5)])              # 13.60 -> 14.40
        self.play(Create(cells), FadeIn(mtx), run_time=1.2)                                # 14.40 -> 15.60（主视觉：点阵洪水）
        self.at_clip("S1-c06")
        self.play_scroll_unroll(cSand, run_time=1.1)                                       # 16.91 -> 18.01
        self.breathe(cells, scale=1.03, run_time=1.4, loops=1)                             # 18.01 -> 19.41（v2 动效 1/3）

        # 页3：C 只多写了一行 min（c07-c08）
        head3 = _head("C 的全部改动", 36)
        bigMin = Text("min", font="Noto Sans CJK SC", weight="BOLD", color=GREEN)
        bigMin.set_width(4.0)
        cC = _card("C：只多写了一行 min", 5.8, 1.7, GREEN, WHITE, 34, CARD_FILL, "BOLD")
        cDawn = _card("天亮时 C 先交卷，效果还不差", 5.8, 1.5, CYAN, WHITE, 31, CARD_FILL, "BOLD")
        page3 = page_stack(head3, bigMin, cC, cDawn, buff=0.62)
        layout_page(page3)

        self.at_clip("S1-c07")
        self.play(FadeOut(head2), FadeOut(rowP), FadeOut(nP), FadeOut(cells), FadeOut(mtx),
                  FadeOut(cSand),
                  type_in(head3, run_time=0.9), type_in(bigMin, run_time=0.6), run_time=0.9)  # 19.57 -> 20.47
        self.play_scroll_unroll(cC, run_time=0.9)                                          # 20.47 -> 21.37
        self.at_clip("S1-c08")
        self.play_scroll_unroll(cDawn, run_time=1.1)                                       # 22.02 -> 23.12
        self.emphasize(bigMin, run_time=0.7)                                               # 23.12 -> 23.82（强调 1/5）
        self.wait(1.40)                                                                    # 23.85 -> 25.25

        # 页4：不信邪 → 服了 → 凭什么（c09-c11）
        line1 = t("一大堆二阶数学，被一行截断顶了？", 34, WHITE, "BOLD")
        line2 = t("C 偷的懒，不是胡来", 40, YELL, "BOLD")
        line3 = t("凭什么？", 54, YELL, "BOLD")
        page_auto(line1, line2, line3)

        self.at_clip("S1-c09")
        self.play(FadeOut(head3), FadeOut(bigMin), FadeOut(cC), FadeOut(cDawn),
                  type_in(line1, run_time=1.3), run_time=1.3)                              # 25.32 -> 26.62
        self.at_clip("S1-c10")
        self.play(type_in(line2, run_time=1.2), run_time=1.2)                              # 29.80 -> 31.00
        self.at_clip("S1-c11")
        self.play(type_in(line3, run_time=0.5), run_time=0.5)                              # 34.07 -> 34.57
        self.transition_out(line1, line2, line3, f, run_time=0.4)                          # 34.57 -> 34.97
        self.pad_to_voice()


# ---------------- S2 clip 公式：就三个符号 ----------------
class S2(_Base):
    def construct(self):
        self.bg()
        f = _footer(self)

        # 页1：目标函数（c01-c02）
        head = _head("PPO 2017：就三个符号", 36)
        formula = MathTex(
            r"L^{\mathrm{CLIP}}=\mathrm{E}\big[\min\big(rA,\ \mathrm{clip}(r,\,1{\pm}\epsilon)\,A\big)\big]",
            tex_to_color_map={r"\min": YELL, r"\mathrm{clip}": CYAN},
        )
        formula.set_width(6.6)
        rDef = MathTex(r"r=\frac{\pi_{\mathrm{new}}}{\pi_{\mathrm{old}}}",
                       tex_to_color_map={r"\pi_{\mathrm{new}}": GREEN})
        rDef.set_width(3.2)
        cR = _card("r：响应比 = 新概率 ÷ 旧概率", 5.8, 1.4, CYAN, WHITE, 31, CARD_FILL, "BOLD")
        page1 = page_stack(head, formula, rDef, cR, buff=1.1)
        layout_page(page1)

        self.at_clip("S2-c01")
        self.play(type_in(head, run_time=1.0), FadeIn(formula), FadeIn(rDef), run_time=1.0)  # 0 -> 1.0
        self.at_clip("S2-c02")
        self.play_scroll_unroll(cR, run_time=1.1)                                          # 4.10 -> 5.20

        # 页2：数轴夹子——1.3 被夹回 1.2（c03-c05）
        head2 = _head("夹住比率", 36)
        axgrp = _r_axis()
        rEq = MathTex(r"r=\frac{0.39}{0.30}=1.3", tex_to_color_map={r"1.3": RED})
        rEq.set_width(3.6)
        marker = Dot(point=RIGHT * _rx(1.0) + UP * 0.42, radius=0.10, color=YELL)
        wall = Line(UP * 0.55, DOWN * 0.55, color=RED, stroke_width=6)
        wall.move_to(RIGHT * _rx(1.2))
        over = t("超标", 34, RED, "BOLD")
        c036 = _card("只按 0.36 算，多的截掉", 5.6, 1.2, YELL, WHITE, 32, CARD_FILL, "BOLD")
        page2 = page_stack(head2, axgrp, rEq, over, c036, buff=0.9)
        layout_page(page2)
        ax_c = axgrp.get_center()
        marker.move_to(ax_c + RIGHT * _rx(1.0) + UP * 0.42)
        wall.move_to(ax_c + RIGHT * _rx(1.2))
        over.next_to(wall, UP, buff=0.18)

        self.at_clip("S2-c03")
        self.play(FadeOut(head), FadeOut(formula), FadeOut(rDef), FadeOut(cR),
                  type_in(head2, run_time=1.0), run_time=1.0)                              # 9.91 -> 10.91
        self.play(FadeIn(axgrp, shift=DOWN * 0.05), FadeIn(rEq), run_time=0.9)             # 10.91 -> 11.81
        self.play(marker.animate.move_to(ax_c + RIGHT * _rx(1.3) + UP * 0.42), run_time=1.3)  # 11.81 -> 13.11（主视觉：指针冲出）
        self.at_clip("S2-c04")
        self.play(marker.animate.set_color(RED).move_to(ax_c + RIGHT * _rx(1.2) + UP * 0.42),
                  Create(wall), type_in(over, run_time=0.5), run_time=1.1)                 # 16.39 -> 17.49（夹臂拍回）
        self.at_clip("S2-c05")
        self.play_scroll_unroll(c036, run_time=1.1)                                        # 21.05 -> 22.15

        # 页3：另外两个符号（c06-c09）
        head3 = _head("另外两个符号", 36)
        cA = _card("A：优势——这个动作比随便选好多少", 5.9, 1.3, GREEN, WHITE, 29, CARD_FILL, "BOLD")
        cE1 = _card("涨跌幅上限：默认 0.2", 5.6, 1.2, CYAN, WHITE, 32, CARD_FILL, "BOLD")
        cE2 = _card("r 只准在 0.8 ~ 1.2 里动", 5.6, 1.2, CYAN, WHITE, 32, CARD_FILL, "BOLD")
        c15 = _card("想 1.5？按 1.2 算", 5.0, 1.2, YELL, WHITE, 34, CARD_FILL, "BOLD")
        page3 = page_stack(head3, cA, cE1, cE2, c15, buff=0.62)
        layout_page(page3)

        self.at_clip("S2-c06")
        self.play(FadeOut(head2), FadeOut(axgrp), FadeOut(rEq), FadeOut(marker),
                  FadeOut(wall), FadeOut(over), FadeOut(c036),
                  type_in(head3, run_time=0.9), run_time=0.9)                              # 22.55 -> 23.45
        self.play_scroll_unroll(cA, run_time=1.1)                                          # 23.45 -> 24.55
        self.at_clip("S2-c07")
        self.play_scroll_unroll_many(cE1, cE2, run_time=1.1)                               # 27.14 -> 28.24
        self.at_clip("S2-c08")
        self.play_scroll_unroll(c15, run_time=1.0)                                         # 33.70 -> 34.70
        self.at_clip("S2-c09")
        self.play(Flash(c15), run_time=0.5)                                                # 34.79 -> 35.29

        # 页4：倍数 vs 距离（c10）
        line1 = t("夹住的是倍数", 36, WHITE, "BOLD")
        line2 = t("KL 预算是距离", 36, CYAN, "BOLD")
        line3 = t("这账怎么算？", 44, YELL, "BOLD")
        page_auto(line1, line2, line3)

        self.at_clip("S2-c10")
        self.play(FadeOut(head3), FadeOut(cA), FadeOut(cE1), FadeOut(cE2), FadeOut(c15),
                  type_in(line1, run_time=0.8), run_time=0.8)                              # 36.20 -> 37.00
        self.play(type_in(line2, run_time=0.8), type_in(line3, run_time=0.7), run_time=0.8)  # 37.00 -> 37.80
        self.wait(1.09)                                                                    # 37.80 -> 38.89
        self.transition_out(line1, line2, line3, f, run_time=0.6)                          # 38.89 -> 39.49
        self.wait(0.80)                                                                    # 39.49 -> 40.29（对齐配音收尾）
        self.pad_to_voice()


# ---------------- S3 取 log：0.8 那头更重 ----------------
class S3(_Base):
    def construct(self):
        self.bg()
        f = _footer(self)

        # 页1：取 log 的映射（c01-c03）
        head = _head("先取个对数", 36)
        raxgrp = _r_axis()
        raxlab = t("r 的刻度", 26, WHITE, "BOLD")
        logArrow = Arrow(UP * 0.32, DOWN * 0.32, buff=0, color=YELL, stroke_width=5,
                         max_tip_length_to_length_ratio=0.30)
        logLab = t("取 log", 28, YELL, "BOLD")
        arrowgrp = VGroup(logArrow, logLab).arrange(RIGHT, buff=0.30)
        # log 刻度：中线 + 左右不对称两段（0.223 vs 0.182，长度按值等比，scale=6）
        logbase = Line(LEFT * 2.4, RIGHT * 2.4, color=MUTED, stroke_width=3)
        midtk = Line(UP * 0.16, DOWN * 0.16, color=WHITE, stroke_width=3)
        midlab = t("1", 24, WHITE, "BOLD")
        midlab.next_to(midtk, DOWN, buff=0.16)
        barL = Rectangle(width=0.223 * 6, height=0.40, color=RED,
                         fill_color=RED, fill_opacity=0.75)
        barL.next_to(midtk, LEFT, buff=0.04)
        barL.align_to(midtk, UP).shift(DOWN * 0.02)
        barR = Rectangle(width=0.182 * 6, height=0.40, color=CYAN,
                         fill_color=CYAN, fill_opacity=0.75)
        barR.next_to(midtk, RIGHT, buff=0.04)
        barR.align_to(midtk, UP).shift(DOWN * 0.02)
        loggrp = VGroup(logbase, midtk, midlab, barL, barR)
        rowN, slotN = _num_row("log r 下界")
        rowP, slotP = _num_row("log r 上界")
        page1 = page_stack(head, raxgrp, raxlab, arrowgrp, loggrp, rowN, rowP, buff=0.42)
        layout_page(page1)

        self.at_clip("S3-c01")
        self.play(type_in(head, run_time=1.0), run_time=1.0)                               # 0 -> 1.0
        self.at_clip("S3-c02")
        self.play(FadeIn(raxgrp, shift=DOWN * 0.05), type_in(raxlab, run_time=0.6),
                  run_time=0.9)                                                            # 1.25 -> 2.15
        self.at_clip("S3-c03")
        self.play(GrowArrow(logArrow), type_in(logLab, run_time=0.5), run_time=0.8)         # 6.66 -> 7.46
        self.play(FadeIn(loggrp, shift=DOWN * 0.05),
                  type_in(rowN[0], run_time=0.5), type_in(rowP[0], run_time=0.5),
                  run_time=0.9)                                                            # 7.46 -> 8.36
        # 双数字同拍滚动：−0.223 与 +0.182 一起出现，不对称一目了然
        trP = ValueTracker(0)
        numP = DecimalNumber(0, mob_class=Text, num_decimal_places=3,
                             font_size=50, color=CYAN)
        numP.move_to(slotP.get_center())
        numP.add_updater(lambda m: m.set_value(trP.get_value()))
        self.add(numP)
        nN = self.counter_value(0, -0.223, decimals=3, size=50, color=RED, run_time=0.9,
                                anchor=slotN,
                                extra_anims=[trP.animate.set_value(0.182)])                # 8.36 -> 9.26（双数字同拍滚动）
        numP.clear_updaters()

        # 页2：不对称（c04-c06）
        head2 = _head("不对称？", 36)
        row182 = _step_row("涨 20%", 0.182 / 0.223, "+0.182", CYAN)
        row223 = _step_row("跌 20%", 1.0, "−0.223", RED)
        cCmp = _card("同样偏 20%，0.8 那头幅度大 22%", 5.9, 1.5, CYAN, WHITE, 30, CARD_FILL, "BOLD")
        cHeavy = _card("0.8 那头更重", 5.0, 1.3, RED, WHITE, 34, CARD_FILL, "BOLD")
        page2 = page_stack(head2, row182, row223, cCmp, cHeavy, buff=0.72)
        layout_page(page2)

        self.at_clip("S3-c04")
        self.play(FadeOut(head), FadeOut(raxgrp), FadeOut(raxlab), FadeOut(arrowgrp),
                  FadeOut(loggrp), FadeOut(rowN), FadeOut(nN), FadeOut(rowP), FadeOut(numP),
                  type_in(head2, run_time=0.9), run_time=0.9)                              # 13.50 -> 14.40
        _grow_bars(self, [
            (row182[2], TRACK_W * 0.182 / 0.223, "center",
             [type_in(row182[0], run_time=0.5), Create(row182[1]), type_in(row182[3], run_time=0.5)]),
            (row223[2], TRACK_W, "center",
             [type_in(row223[0], run_time=0.5), Create(row223[1]), type_in(row223[3], run_time=0.5)]),
        ], run_time=0.9)                                                                   # 14.40 -> 15.30（主视觉：双条对比）
        self.at_clip("S3-c05")
        self.emphasize(row223, run_time=0.7)                                               # 17.16 -> 17.86（强调 2/5）
        self.play_scroll_unroll(cCmp, run_time=1.1)                                        # 17.86 -> 18.96
        self.at_clip("S3-c06")
        self.play_scroll_unroll(cHeavy, run_time=1.0)                                      # 22.23 -> 23.23

        # 页3：返程票价（c07-c09）
        img = _img("s3-two-roads-round.png", 3.0)
        rowUp = _step_row("0.8 → 1 要爬", 1.0, "25%", RED)
        rowDown = _step_row("1.2 → 1 只跌", 16.7 / 25, "16.7%", CYAN)
        cReturn = _card("返程更贵", 4.6, 1.1, YELL, WHITE, 34, CARD_FILL, "BOLD")
        cBridge = _card("夹住了 log r，到 KL 还差一座桥", 5.9, 1.3, YELL, WHITE, 31, CARD_FILL, "BOLD")
        page3 = page_stack(img, rowUp, rowDown, cReturn, cBridge, buff=0.5)
        layout_page(page3)

        self.at_clip("S3-c07")
        self.play(FadeOut(head2), FadeOut(row182), FadeOut(row223), FadeOut(cCmp),
                  FadeOut(cHeavy),
                  FadeIn(img, shift=DOWN * 0.05), run_time=0.9)                            # 24.26 -> 25.16
        _grow_bars(self, [
            (rowUp[2], TRACK_W, "center",
             [type_in(rowUp[0], run_time=0.5), Create(rowUp[1]), type_in(rowUp[3], run_time=0.5)]),
            (rowDown[2], TRACK_W * 16.7 / 25, "center",
             [type_in(rowDown[0], run_time=0.5), Create(rowDown[1]), type_in(rowDown[3], run_time=0.5)]),
        ], run_time=0.9)                                                                   # 25.16 -> 26.06
        self.at_clip("S3-c08")
        self.play_scroll_unroll(cReturn, run_time=1.0)                                     # 30.67 -> 31.67
        self.at_clip("S3-c09")
        self.play_scroll_unroll(cBridge, run_time=1.1)                                     # 31.81 -> 32.91
        self.wait(2.52)                                                                    # 32.91 -> 35.43
        self.transition_out(img, rowUp, rowDown, cReturn, cBridge, f, run_time=0.6)        # 35.43 -> 36.03
        self.pad_to_voice()


# ---------------- S4 搭桥：两把表盘，同一台发动机 ----------------
class S4(_Base):
    def construct(self):
        self.bg()
        f = _footer(self)

        # 页1：公式拼桥（c01-c04）
        head = _head("把桥搭完", 36)
        eq1 = MathTex(r"\mathrm{KL}\approx\tfrac{1}{2}\,\delta\theta^{\top}F\,\delta\theta",
                      tex_to_color_map={r"F": CYAN})
        eq1.set_width(5.0)
        eq2 = MathTex(r"\log r\approx\delta\theta\cdot\nabla\log\pi",
                      tex_to_color_map={r"\log r": YELL})
        eq2.set_width(5.0)
        eq3 = MathTex(r"\mathrm{KL}\approx\tfrac{1}{2}\,\mathrm{E}\big[(\log r)^2\big]",
                      tex_to_color_map={r"(\log r)^2": YELL})
        eq3.set_width(5.6)
        cBridge = _card("两式一拼，桥通了", 5.4, 1.2, GREEN, WHITE, 33, CARD_FILL, "BOLD")
        page1 = page_stack(head, eq1, eq2, eq3, cBridge, buff=0.85)
        layout_page(page1)

        self.at_clip("S4-c01")
        self.play(type_in(head, run_time=1.0), run_time=1.0)                               # 0 -> 1.0
        self.at_clip("S4-c02")
        self.play(FadeIn(eq1), run_time=0.9)                                               # 4.06 -> 4.96
        self.at_clip("S4-c03")
        self.play(FadeIn(eq2), run_time=0.9)                                               # 6.70 -> 7.60
        self.at_clip("S4-c04")
        self.morph_to(VGroup(eq1, eq2), eq3, run_time=1.5)                                 # 10.76 -> 12.26（v2 动效 2/3：拼桥）
        self.play_scroll_unroll(cBridge, run_time=1.0)                                     # 12.26 -> 13.26

        # 页2：两个表盘（c05-c06）
        img = _img("s4-two-dials-round.png", 4.2)
        cDial = _card("TRPO 用 KL 量距离\nPPO 用 log r 看速度", 5.9, 1.6, CYAN, WHITE, 30, CARD_FILL, "BOLD")
        cSame = _card("量程不同，表盘同一", 5.4, 1.2, YELL, WHITE, 34, CARD_FILL, "BOLD")
        page2 = page_stack(img, cDial, cSame, buff=0.75)
        layout_page(page2)

        self.at_clip("S4-c05")
        self.play(FadeOut(head), FadeOut(eq3), FadeOut(cBridge),
                  FadeIn(img, shift=DOWN * 0.05), run_time=0.9)                            # 16.84 -> 17.74
        self.play_scroll_unroll(cDial, run_time=1.1)                                       # 17.74 -> 18.84
        self.at_clip("S4-c06")
        self.play_scroll_unroll(cSame, run_time=1.0)                                       # 21.66 -> 22.66
        self.emphasize(cSame, run_time=0.7)                                                # 22.66 -> 23.36（强调 3/5）

        # 页3：蒙特卡洛实测（c07-c09）
        head3 = _head("蒙特卡洛实测", 36)
        mc1 = _mc_row("第 1 组", 0.0012, 0.0012, 130)
        mc2 = _mc_row("第 2 组", 0.0053, 0.0054, 130)
        mc3 = _mc_row("第 3 组", 0.0225, 0.0229, 130)
        cErr = _card("500 类策略，误差全在 2% 以内", 5.9, 1.2, GREEN, WHITE, 30, CARD_FILL, "BOLD")
        cReal = _card("表盘是真的", 4.6, 1.1, YELL, WHITE, 36, CARD_FILL, "BOLD")
        cQ = _card("0.2 的夹子，能量出多大的 KL？", 5.9, 1.2, YELL, WHITE, 31, CARD_FILL, "BOLD")
        page3 = page_stack(head3, mc1, mc2, mc3, cErr, cReal, cQ, buff=0.34)
        layout_page(page3)

        self.at_clip("S4-c07")
        self.play(FadeOut(img), FadeOut(cDial), FadeOut(cSame),
                  type_in(head3, run_time=0.8), run_time=0.8)                              # 24.16 -> 24.96
        _grow_bars(self, [
            (mc1[1][0], 0.0012 * 130, "center",
             [type_in(mc1[0], run_time=0.4), FadeIn(mc1[2], run_time=0.4)]),
            (mc1[1][1], 0.0012 * 130, "center"),
        ], run_time=0.9)                                                                   # 24.96 -> 25.86
        _grow_bars(self, [
            (mc2[1][0], 0.0053 * 130, "center",
             [type_in(mc2[0], run_time=0.4), FadeIn(mc2[2], run_time=0.4)]),
            (mc2[1][1], 0.0054 * 130, "center"),
        ], run_time=0.9)                                                                   # 25.86 -> 26.76
        _grow_bars(self, [
            (mc3[1][0], 0.0225 * 130, "center",
             [type_in(mc3[0], run_time=0.4), FadeIn(mc3[2], run_time=0.4)]),
            (mc3[1][1], 0.0229 * 130, "center"),
        ], run_time=0.9)                                                                   # 26.76 -> 27.66
        self.at_clip("S4-c08")
        self.play_scroll_unroll(cErr, run_time=1.0)                                        # 29.10 -> 30.10
        self.at_clip("S4-c09")
        self.play_scroll_unroll_many(cReal, cQ, run_time=1.0)                              # 30.33 -> 31.33
        self.wait(0.40)                                                                    # 31.33 -> 31.73
        self.transition_out(head3, mc1, mc2, mc3, cErr, cReal, cQ, f, run_time=0.6)        # 31.73 -> 32.33
        self.wait(1.60)                                                                    # 32.33 -> 33.93（对齐配音收尾）
        self.pad_to_voice()


# ---------------- S5 换算：0.223 的夹子，夹出 0.025 的 KL ----------------
class S5(_Base):
    def construct(self):
        self.bg()
        f = _footer(self)

        # 页1：换算链（c01-c03）
        head = _head("两张牌一打", 36)
        eq1 = MathTex(r"|\log r|\le 0.223", tex_to_color_map={r"0.223": RED})
        eq1.set_width(4.2)
        eq2 = MathTex(r"\mathrm{E}[(\log r)^2]\le 0.0498",
                      tex_to_color_map={r"0.0498": CYAN})
        eq2.set_width(5.4)
        eq3 = MathTex(r"\mathrm{KL}\le\tfrac{1}{2}\times 0.0498")
        eq3.set_width(4.8)
        rowK, slotK = _num_row("KL 上界")
        page1 = page_stack(head, eq1, eq2, eq3, rowK, buff=1.0)
        layout_page(page1)

        self.at_clip("S5-c01")
        self.play(type_in(head, run_time=1.0), FadeIn(eq1), run_time=1.0)                  # 0 -> 1.0
        self.at_clip("S5-c02")
        self.play(FadeIn(eq2), run_time=0.9)                                               # 4.95 -> 5.85
        self.at_clip("S5-c03")
        nK = self.counter_value(0, 0.025, decimals=3, size=56, color=YELL, run_time=1.1,
                                anchor=slotK,
                                extra_anims=[FadeIn(eq3), type_in(rowK[0], run_time=0.6)])  # 9.00 -> 10.10
        self.emphasize(nK, run_time=0.7)                                                   # 10.10 -> 10.80（强调 4/5）

        # 页2：0.025 对 0.01（c04-c06）
        head2 = _head("0.025 对 0.01", 36)
        rowT = _step_row("TRPO 预算", 0.01 / 0.025, "0.01", CYAN)
        rowP2 = _step_row("PPO clip 上界", 1.0, "0.025", YELL)
        ratio = t("2.5 倍——同一个数量级", 30, RED, "BOLD")
        cSame = _card("不是精确相等，是量级相同", 5.8, 1.3, GREEN, WHITE, 32, CARD_FILL, "BOLD")
        page2 = page_stack(head2, rowT, rowP2, ratio, cSame, buff=0.9)
        layout_page(page2)

        self.at_clip("S5-c04")
        self.play(FadeOut(head), FadeOut(eq1), FadeOut(eq2), FadeOut(eq3), FadeOut(rowK),
                  FadeOut(nK),
                  type_in(head2, run_time=0.9), run_time=0.9)                              # 13.02 -> 13.92
        _grow_bars(self, [
            (rowT[2], TRACK_W * 0.4, "center",
             [type_in(rowT[0], run_time=0.5), Create(rowT[1]), type_in(rowT[3], run_time=0.5)]),
            (rowP2[2], TRACK_W, "center",
             [type_in(rowP2[0], run_time=0.5), Create(rowP2[1]), type_in(rowP2[3], run_time=0.5)]),
        ], run_time=0.9)                                                                   # 13.92 -> 14.82（主视觉：预算对比条）
        self.at_clip("S5-c05")
        self.camera_zoom_to(VGroup(rowT, rowP2), scale=0.9, run_time=0.9)                  # 16.11 -> 17.01（v2 动效 3/3 轻推，0.9 防越安全区）
        self.wait(1.2)                                                                     # 17.01 -> 18.21
        self.camera_zoom_to(run_time=0.9)                                                  # 18.21 -> 19.11（成对拉回）
        self.play(type_in(ratio, run_time=0.6), run_time=0.6)                              # 19.11 -> 19.71
        self.at_clip("S5-c06")
        self.play_scroll_unroll(cSame, run_time=1.1)                                       # 20.56 -> 21.66

        # 页3：实测刻度 + 截断分布（c07-c09，一页两段视觉）
        head3 = _head("实测：贴着上界走", 36)
        gauge_base = Line(LEFT * 3.3, RIGHT * 3.5, color=MUTED, stroke_width=3)
        tk01 = Line(UP * 0.18, DOWN * 0.18, color=CYAN, stroke_width=4)
        tk01.move_to(RIGHT * (0.01 * 150 - 3.1))
        lab01 = t("0.01", 24, CYAN, "BOLD")
        lab01.next_to(tk01, DOWN, buff=0.16)
        tk025 = Line(UP * 0.18, DOWN * 0.18, color=YELL, stroke_width=4)
        tk025.move_to(RIGHT * (0.025 * 150 - 3.1))
        lab025 = t("0.025 上界", 24, YELL, "BOLD")
        lab025.next_to(tk025, UP, buff=0.16)
        dot022 = Dot(point=RIGHT * (0.022 * 150 - 3.1) + UP * 0.40, radius=0.11, color=RED)
        lab022 = t("实测 0.022", 24, RED, "BOLD")
        lab022.next_to(dot022, UP, buff=0.14)
        gaugegrp = VGroup(gauge_base, tk01, lab01, tk025, lab025, dot022, lab022)
        ax = Axes(x_range=[0.55, 1.45, 0.1], y_range=[0, 1.2, 0.4],
                  x_length=5.8, y_length=2.4, tips=False,
                  axis_config={"stroke_color": MUTED, "stroke_width": 2})
        curve = ax.plot(lambda x: np.exp(-((x - 1.0) ** 2) / (2 * 0.12 ** 2)), color=CYAN)
        xs_l = np.linspace(0.55, 0.8, 40)
        ys_l = np.exp(-((xs_l - 1.0) ** 2) / (2 * 0.12 ** 2))
        tail_l = Polygon(*[ax.c2p(x, 0) for x in xs_l],
                         *[ax.c2p(x, y) for x, y in zip(xs_l, ys_l)][::-1],
                         stroke_width=0, fill_color=RED, fill_opacity=0.5)
        xs_r = np.linspace(1.2, 1.45, 40)
        ys_r = np.exp(-((xs_r - 1.0) ** 2) / (2 * 0.12 ** 2))
        tail_r = Polygon(*[ax.c2p(x, 0) for x in xs_r],
                         *[ax.c2p(x, y) for x, y in zip(xs_r, ys_r)][::-1],
                         stroke_width=0, fill_color=RED, fill_opacity=0.5)
        tk8 = DashedLine(ax.c2p(0.8, 0), ax.c2p(0.8, 1.05), color=MUTED, stroke_width=2)
        tk12 = DashedLine(ax.c2p(1.2, 0), ax.c2p(1.2, 1.05), color=MUTED, stroke_width=2)
        lab8 = t("0.8", 22, MUTED)
        lab8.next_to(tk8, DOWN, buff=0.10)
        lab12 = t("1.2", 22, MUTED)
        lab12.next_to(tk12, DOWN, buff=0.10)
        histgrp = VGroup(ax, curve, tk8, tk12, lab8, lab12)
        rowC, slotC = _num_row("被拍平的样本")
        cPaper = _card("KL 贴着上界走，不是纸面数字", 5.9, 1.2, GREEN, WHITE, 30, CARD_FILL, "BOLD")
        page3 = page_stack(head3, gaugegrp, histgrp, tail_l, tail_r, rowC, cPaper, buff=0.30)
        layout_page(page3)

        self.at_clip("S5-c07")
        self.play(FadeOut(head2), FadeOut(rowT), FadeOut(rowP2), FadeOut(ratio),
                  FadeOut(cSame),
                  type_in(head3, run_time=0.9), run_time=0.9)                              # 23.27 -> 24.17
        self.play(FadeIn(gaugegrp, shift=DOWN * 0.05), run_time=0.9)                       # 24.17 -> 25.10
        self.at_clip("S5-c08")
        self.play(FadeIn(histgrp, shift=DOWN * 0.05), FadeIn(tail_l), FadeIn(tail_r),
                  run_time=0.8)                                                            # 26.71 -> 27.51（主视觉：两尾拍平）
        nC = self.counter_value(0, 32.0, suffix="%", decimals=1, size=50, color=RED,
                                run_time=0.9, anchor=slotC,
                                extra_anims=[type_in(rowC[0], run_time=0.5)])              # 28.31 -> 29.21
        self.at_clip("S5-c09")
        self.play_scroll_unroll(cPaper, run_time=1.0)                                      # 30.33 -> 31.33

        # 页4：为什么没翻车（c10-c11）
        line1 = t("可 0.022 还是大于 0.01", 34, WHITE, "BOLD")
        line2 = t("PPO 为什么没翻车？", 40, WHITE, "BOLD")
        line3 = t("答案在 min", 46, YELL, "BOLD")
        page_auto(line1, line2, line3)

        self.at_clip("S5-c10")
        self.play(FadeOut(head3), FadeOut(gaugegrp), FadeOut(histgrp), FadeOut(tail_l),
                  FadeOut(tail_r), FadeOut(rowC), FadeOut(nC), FadeOut(cPaper),
                  type_in(line1, run_time=1.0), type_in(line2, run_time=0.9), run_time=1.3)  # 31.77 -> 33.07
        self.at_clip("S5-c11")
        self.play(type_in(line3, run_time=0.7), run_time=0.7)                              # 36.40 -> 37.10
        self.transition_out(line1, line2, line3, f, run_time=0.58)                         # 37.10 -> 37.68
        self.pad_to_voice()


# ---------------- S6 答案在 min：不记功，不记过 + 尾卡 ----------------
class S6(_Base):
    def construct(self):
        self.bg()
        f = _footer(self)

        def _clip_axes(x_length=4.6, y_length=2.6):
            ax = Axes(x_range=[0.6, 1.4, 0.2], y_range=[0.6, 1.4, 0.2],
                      x_length=x_length, y_length=y_length, tips=False,
                      axis_config={"stroke_color": MUTED, "stroke_width": 2})
            segL = Line(ax.c2p(0.6, 0.8), ax.c2p(0.8, 0.8), color=MUTED, stroke_width=4)
            segM = Line(ax.c2p(0.8, 0.8), ax.c2p(1.2, 1.2), color=YELL, stroke_width=6)
            segR = Line(ax.c2p(1.2, 1.2), ax.c2p(1.4, 1.2), color=MUTED, stroke_width=4)
            lab8 = t("0.8", 22, MUTED)
            lab8.next_to(ax.c2p(0.8, 0.6), DOWN, buff=0.12)
            lab12 = t("1.2", 22, MUTED)
            lab12.next_to(ax.c2p(1.2, 0.6), DOWN, buff=0.12)
            labOut = t("区间外：拍平", 22, MUTED)
            labIn = t("区间内：照常", 22, YELL)
            return ax, VGroup(segL, segM, segR), lab8, lab12, labOut, labIn

        # 页1：clip 平台几何 + 绩效比喻（c01-c03）
        head = _head("min：不记功，不记过", 36)
        ax, segs, lab8, lab12, labOut, labIn = _clip_axes()
        labOut.next_to(segs[0], UP, buff=0.22)
        labIn.next_to(segs[1], DOWN, buff=0.30)
        cGood = _card("好员工：奖金封顶 1.2 倍\n干出 1.5 也不记功", 5.9, 1.5, GREEN, WHITE, 29, CARD_FILL, "BOLD")
        cBad = _card("坏员工：罚也封顶 0.8\n摸到 0.5 不追加", 5.9, 1.5, CYAN, WHITE, 29, CARD_FILL, "BOLD")
        geomgrp1 = VGroup(ax, segs, lab8, lab12, labOut, labIn)
        page1 = page_stack(head, geomgrp1, cGood, cBad, buff=0.42)
        layout_page(page1)

        self.at_clip("S6-c01")
        self.play(type_in(head, run_time=1.0), Create(ax), run_time=1.0)                   # 0 -> 1.0
        self.play(Create(segs), FadeIn(lab8), FadeIn(lab12), type_in(labOut, run_time=0.5),
                  type_in(labIn, run_time=0.5), run_time=1.1)                              # 1.0 -> 2.1（主视觉：平台折线）
        self.at_clip("S6-c02")
        self.play_scroll_unroll(cGood, run_time=1.2)                                       # 3.95 -> 5.15
        self.at_clip("S6-c03")
        self.play_scroll_unroll(cBad, run_time=1.2)                                        # 5.83 -> 7.03

        # 页2：反向操作，min 不客气（c04-c07）
        head2 = _head("反向操作，min 不客气", 36)
        ax2, segs2, lab82, lab122, labOut2, labIn2 = _clip_axes(x_length=4.0, y_length=2.2)
        arL = Arrow(ax2.c2p(0.7, 0.70), ax2.c2p(0.7, 0.86), color=GREEN, stroke_width=6,
                    buff=0, max_tip_length_to_length_ratio=0.35)
        arR = Arrow(ax2.c2p(1.3, 1.30), ax2.c2p(1.3, 1.14), color=GREEN, stroke_width=6,
                    buff=0, max_tip_length_to_length_ratio=0.35)
        cRev = _card("把好员工压破 0.8、给摸鱼的抬破 1.2\n——梯度照常把比率拽回区间", 6.0, 1.6, GREEN, WHITE, 27, CARD_FILL, "BOLD")
        cGolden1 = _card("往外跑的步子不算数\n往里拽的力气照常使", 5.9, 1.7, YELL, WHITE, 32, CARD_FILL, "BOLD")
        geomgrp2 = VGroup(ax2, segs2, lab82, lab122)
        page2 = page_stack(head2, geomgrp2, arL, arR, cRev, cGolden1, buff=0.30)
        layout_page(page2)

        self.at_clip("S6-c04")
        self.play(FadeOut(head), FadeOut(geomgrp1), FadeOut(cGood), FadeOut(cBad),
                  type_in(head2, run_time=0.9), run_time=0.9)                              # 9.78 -> 10.68
        self.play(FadeIn(geomgrp2, shift=DOWN * 0.05), run_time=0.9)                       # 10.68 -> 11.58
        self.at_clip("S6-c05")
        self.play(GrowArrow(arL), GrowArrow(arR), run_time=0.9)                            # 13.70 -> 14.60
        self.play_scroll_unroll(cRev, run_time=1.1)                                        # 14.60 -> 15.70
        self.at_clip("S6-c07")
        self.play_scroll_unroll(cGolden1, run_time=1.2)                                    # 20.12 -> 21.32

        # 页3：限速牌金句（c08-c09）
        img = _img("s6-speed-limit-round.png", 3.4)
        cRuler = _card("不是信任域，是限速牌", 5.6, 1.2, CYAN, WHITE, 32, CARD_FILL, "BOLD")
        cGolden2 = _card("0.2 的截断，量出 0.025 的 KL", 5.9, 1.3, YELL, WHITE, 33, CARD_FILL, "BOLD")
        page3 = page_stack(img, cRuler, cGolden2, buff=0.8)
        layout_page(page3)

        self.at_clip("S6-c08")
        self.play(FadeOut(head2), FadeOut(geomgrp2), FadeOut(arL), FadeOut(arR),
                  FadeOut(cRev), FadeOut(cGolden1),
                  FadeIn(img, shift=DOWN * 0.05), run_time=0.9)                            # 24.16 -> 25.06
        self.play_scroll_unroll_many(cRuler, cGolden2, run_time=1.1)                       # 25.06 -> 26.16
        self.at_clip("S6-c09")
        self.emphasize(cGolden2, run_time=0.8)                                             # 31.03 -> 31.83（强调 5/5）

        # 页4：预告 + 互动 + 品牌尾卡（c10-c12）
        pre = t("下一篇：GAE——把优势 A 完整展开", 26, WHITE, "BOLD")
        title = t("《PPO只用0.2的clip，凭什么顶替0.01预算？》", 27, WHITE, "BOLD")
        title.set_width(6.9)
        q = t("你愿意为哪种偷懒买单？评论区聊聊", 28, WHITE, "BOLD")
        q.set_width(6.9)
        logo = ImageMobject(str(AVATAR))
        logo.scale_to_fit_width(2.7)
        follow = t("关注「数解AI」", 38, YELL, "BOLD")
        guide = t("查看公众号文章", 30, GREEN, "BOLD")
        page4 = page_stack(pre, title, q, logo, follow, guide, buff=0.5)
        layout_page(page4)

        self.at_clip("S6-c10")
        self.play(FadeOut(img), FadeOut(cRuler), FadeOut(cGolden2),
                  type_in(pre, run_time=1.0), run_time=1.0)                                # 33.45 -> 34.45
        self.play(type_in(title, run_time=1.2), run_time=1.2)                              # 34.45 -> 35.65
        self.at_clip("S6-c11")
        self.play(FadeIn(logo, shift=DOWN * 0.05), type_in(follow, run_time=0.9),
                  type_in(q, run_time=0.9), run_time=1.0)                                  # 37.53 -> 38.53
        self.at_clip("S6-c12")
        self.play(type_in(guide, run_time=0.5), run_time=0.5)                              # 39.56 -> 40.06
        self.wait(0.76)                                                                    # 40.06 -> 40.82
        self.pad_to_voice()
