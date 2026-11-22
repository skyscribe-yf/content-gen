#!/usr/bin/env python3
"""《GRPO 省了一个 critic，长任务为什么反而崩了？》视频号 Manim 动画（竖屏 1080×1920）

6 个场景 S1-S6，与 storyboard.md 一一对应（强化学习原理系列路标⑨，前作 GAE 08-25）。
- 配音：MiniMax 精英男声（speech-2.8-turbo，speed 1.0，pitch +2），实测总长 321.42s
- 时间轴：at_clip("S1-c01") 挂 tts/sentence-boundaries.json 的 clip 起点（先声音后动画门禁；
 段边界经 ASR + silencedetect 修正——MiniMax 句子时间戳跨段导致 S3/S4 切点错位 ~3.3s，
  正确切点 171.47s，S4 语音起点 171.63s，见 fix_grpo_split.py）
- 布局：整页规划（page_stack + layout_page）/ 矮页自动排版（page_auto），上下留白相等
- 动画降噪（决策 #51）：v2 动效 2 处（S1 camera_zoom 成对 / S5 morph_to）；emphasize 5 次
  （S1 组内排名 / S2 信号越少 / S3 数学本体 / S4 长了65% / S6 同一个东西）；每页 1 个主视觉动效
- 数字台词全配动效：概率四级柱 grow_bar（0.003%→85.1%）+ 8206/4965 双条 + counter 43.3%
- 概念图 3 张（yairouter 深蓝系，无数字）：s1-empty-chair / s3-sixteen-sheets / s4-long-scroll
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

# 每段配音时长（fix_grpo_split.py 修正边界后 ffprobe 实测 tts/sN.wav），渲染时长 = 配音 + TAIL
VOICE_DUR = {"S1": 43.75, "S2": 75.07, "S3": 52.40, "S4": 57.04, "S5": 39.81, "S6": 53.10}
TAIL = 0.1


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


def _dots(rows: int, cols: int, cell: float = 0.62, gap: float = 0.12,
          color: str = CYAN) -> VGroup:
    """rows×cols 点阵（16 份答卷的脚本画图）。"""
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


def _card3(labels, colors, w: float = 2.1, h: float = 0.9, fs: float = 26) -> VGroup:
    """三卡横排（同宽同高，等距）。"""
    cards = [_card(lb, w, h, c, WHITE, fs, CARD_FILL, "BOLD")
             for lb, c in zip(labels, colors)]
    return VGroup(*cards).arrange(RIGHT, buff=0.45)


# ---------------- S1 开场钩子：省了一个 critic，崩在哪 ----------------
class S1(_Base):
    def construct(self):
        self.bg()
        f = _footer(self)

        # 页1：标题 + 空椅子概念图（c01-c03）
        head1 = t("省了一个 critic，", 42, YELL, "BOLD")
        head2 = t("长任务为什么反而崩了？", 42, YELL, "BOLD")
        note2 = t("以 DeepSeek-R1 训练为例", 24, MUTED)
        sub = t("省下的不只是显存，还有判断力", 30, CYAN, "BOLD")
        note = t("这条视频讲清楚，它到底崩在哪", 26, MUTED)
        img = _img("s1-empty-chair-round.png", 3.6)
        page1 = page_stack(head1, head2, note2, sub, img, note, buff=0.42)
        layout_page(page1)

        self.at_clip("S1-c01")
        self.play(type_in(head1, run_time=1.1), type_in(head2, run_time=1.1),
                  type_in(note2, run_time=0.7), run_time=1.1)                     # 0.00 -> 1.10
        self.at_clip("S1-c02")
        self.play(type_in(sub, run_time=0.8), FadeIn(img, shift=DOWN * 0.05),
                  run_time=0.8)                                                     # 3.62 -> 4.42
        self.at_clip("S1-c03")
        self.play(type_in(note, run_time=0.8), run_time=0.8)                        # 7.84 -> 8.64

        # 页2：16 份答卷 + 组内排名（c04-c06）
        head3 = _head("同一道题，采样 16 份答卷", 36)
        grid = _dots(4, 4, cell=0.68, gap=0.14)
        cOk = _card("对了 = 1", 2.6, 1.0, GREEN, WHITE, 30, CARD_FILL, "BOLD")
        cNo = _card("错了 = 0", 2.6, 1.0, RED, WHITE, 30, CARD_FILL, "BOLD")
        scoreRow = stable_row(cOk, cNo, buff=0.5)
        flow1 = t("组内减均值 → 除标准差", 30, CYAN, "BOLD")
        flow2 = t("每份答卷拿到相对成绩 A", 30, YELL, "BOLD")
        page2 = page_stack(head3, grid, scoreRow, flow1, flow2, buff=0.45)
        layout_page(page2)

        self.at_clip("S1-c04")
        self.play(FadeOut(head1), FadeOut(head2), FadeOut(note2), FadeOut(sub),
                  FadeOut(note), FadeOut(img),
                  type_in(head3, run_time=1.0),
                  Create(grid, run_time=1.3, lag_ratio=0.05), run_time=1.3)         # 10.86 -> 12.16
        self.at_clip("S1-c05")
        self.play_scroll_unroll_many(cOk, cNo, run_time=0.9)                        # 15.48 -> 16.38
        self.at_clip("S1-c06")
        self.play(type_in(flow1, run_time=0.8), type_in(flow2, run_time=0.8),
                  run_time=0.8)                                                     # 16.69 -> 17.49

        # 页3：critic vs GRPO（c07-c11）
        cPos = t("比组内平均好就是正，差就是负", 32, WHITE, "BOLD")
        cCritic1 = _card("critic：一格一格估", 6.4, 1.4, CYAN, WHITE, 30, CARD_FILL, "BOLD")
        cCritic2 = _card("走到这一步，还有多少希望", 6.4, 1.4, CYAN, WHITE, 30, CARD_FILL, "BOLD")
        cBig = _card("它是一个和策略一样大的网络", 6.4, 1.3, MUTED, WHITE, 30, CARD_FILL, "BOLD")
        cGrpo = _card("GRPO：看你在组里排第几", 6.4, 1.6, YELL, WHITE, 34, CARD_FILL, "BOLD")
        page_auto(cPos, cCritic1, cCritic2, cBig, cGrpo)

        self.at_clip("S1-c07")
        self.play(FadeOut(head3), FadeOut(grid), FadeOut(cOk), FadeOut(cNo),
                  FadeOut(flow1), FadeOut(flow2),
                  type_in(cPos, run_time=0.9), run_time=0.9)                        # 21.39 -> 22.29
        self.at_clip("S1-c08")
        self.play_scroll_unroll(cCritic1, run_time=1.0)                             # 24.28 -> 25.28
        self.at_clip("S1-c09")
        self.play_scroll_unroll(cCritic2, run_time=1.0)                             # 28.26 -> 29.26
        self.at_clip("S1-c10")
        self.play_scroll_unroll(cBig, run_time=1.0)                                 # 30.42 -> 31.42
        self.at_clip("S1-c11")
        self.play_scroll_unroll(cGrpo, run_time=1.0)                                # 33.23 -> 34.23
        self.wait(0.2)
        self.emphasize(cGrpo, run_time=0.7)                                         # 34.43 -> 35.13
        self.wait(0.3)
        self.camera_zoom_to(cGrpo, scale=0.6, run_time=0.8)                         # 35.43 -> 36.23
        self.wait(2.42)                                                             # -> 38.65

        # 页4：结尾悬念（c12-c13）
        cPure = _card("账面上，这是纯赚", 6.4, 1.4, CYAN, WHITE, 34, CARD_FILL, "BOLD")
        cWall = _card("但有三堵墙，都砌在「排名」这两个字上", 6.6, 1.7, YELL, WHITE, 32,
                      CARD_FILL, "BOLD")
        page_auto(cPure, cWall)

        self.at_clip("S1-c12")
        self.camera_zoom_to(run_time=0.7)                                           # 38.85 -> 39.55
        self.play(FadeOut(cPos), FadeOut(cCritic1), FadeOut(cCritic2), FadeOut(cBig),
                  FadeOut(cGrpo), type_in(cPure, run_time=0.8), run_time=0.8)       # 39.55 -> 40.35
        self.at_clip("S1-c13")
        self.play_scroll_unroll(cWall, run_time=1.0)                                # 40.40 -> 41.40
        self.wait(2.15)                                                             # -> 43.55
        self.transition_out(cPure, cWall, f, run_time=0.4)                          # 43.55 -> 43.95
        self.pad_to_voice()


# ---------------- S2 第一堵墙：全对的组，一步都没学到 ----------------
class S2(_Base):
    def construct(self):
        self.bg()
        f = _footer(self)

        # 页1：全对组零梯度（c01-c04）
        head1 = _head("第一堵墙：16 份答卷全对", 36)
        grid = _dots(4, 4, cell=0.62, gap=0.12, color=GREEN)
        cMean = _card("均值 = 1", 2.7, 1.0, CYAN, WHITE, 30, CARD_FILL, "BOLD")
        cStd = _card("标准差 = 0", 2.7, 1.0, CYAN, WHITE, 30, CARD_FILL, "BOLD")
        statRow = stable_row(cMean, cStd, buff=0.5)
        cDiv = _card("优势 = 0 除以 0，工程置 0", 6.4, 1.2, YELL, WHITE, 32, CARD_FILL, "BOLD")
        cZero = _card("整组梯度为零，这批样本白跑\n（全错同理）", 6.4, 1.5, RED, WHITE, 30,
                      CARD_FILL, "BOLD")
        page1 = page_stack(head1, grid, statRow, cDiv, cZero, buff=0.38)
        layout_page(page1)

        self.at_clip("S2-c01")
        self.play(type_in(head1, run_time=1.0),
                  Create(grid, run_time=1.3, lag_ratio=0.05), run_time=1.3)         # 0.00 -> 1.30
        self.at_clip("S2-c02")
        self.play_scroll_unroll_many(cMean, cStd, run_time=0.9)                     # 4.71 -> 5.61
        self.wait(0.2)
        self.play_scroll_unroll(cDiv, run_time=1.0)                                 # 5.81 -> 6.81
        self.at_clip("S2-c03")
        self.play_scroll_unroll(cZero, run_time=1.0)                                # 11.15 -> 12.15
        self.wait(0.2)
        cross = self.play_red_cross(cZero, run_time=0.65)                           # 12.35 -> 13.00

        # 页2：概率阶梯（c05-c11）
        head2 = _head("一组全同分的概率", 36)
        formula = MathTex(r"p^{16} + (1-p)^{16}", color=YELL).scale(1.15)
        pnote = t("p = 题目正确率", 24, MUTED)
        r1 = _bar_row("正确率 50%", "0.003%", CYAN, 0.035, track_h=0.72, lab_size=28, val_size=28)
        r2 = _bar_row("正确率 90%", "18.5%", CYAN, 0.44, track_h=0.72, lab_size=28, val_size=28)
        r3 = _bar_row("正确率 95%", "44.0%", YELL, 0.68, track_h=0.72, lab_size=28, val_size=28)
        r4 = _bar_row("正确率 99%", "85.1%", RED, 0.92, track_h=0.72, lab_size=28, val_size=28)
        page2 = page_stack(head2, formula, pnote, r1, r2, r3, r4, buff=0.45)
        layout_page(page2)

        self.at_clip("S2-c05")
        self.play(FadeOut(head1), FadeOut(grid), FadeOut(cMean), FadeOut(cStd),
                  FadeOut(cDiv), FadeOut(cZero), FadeOut(cross),
                  type_in(head2, run_time=0.9), Create(formula, run_time=1.0),
                  run_time=1.0)                                                     # 16.31 -> 17.31
        self.at_clip("S2-c07")
        self.play(type_in(pnote, run_time=0.6), run_time=0.6)                       # 21.84 -> 22.44
        self.at_clip("S2-c08")
        _grow_bars(self, [(r1[2], 3.0 * 0.035, "left",
                                [type_in(r1[0], run_time=0.5), Create(r1[1]),
                                 type_in(r1[3], run_time=0.5)])], run_time=1.0)     # 24.16 -> 25.16
        self.at_clip("S2-c09")
        _grow_bars(self, [(r2[2], 3.0 * 0.44, "left",
                                [type_in(r2[0], run_time=0.5), Create(r2[1]),
                                 type_in(r2[3], run_time=0.5)])], run_time=1.0)     # 29.17 -> 30.17
        self.at_clip("S2-c10")
        _grow_bars(self, [(r3[2], 3.0 * 0.68, "left",
                                [type_in(r3[0], run_time=0.5), Create(r3[1]),
                                 type_in(r3[3], run_time=0.5)])], run_time=1.0)     # 31.45 -> 32.45
        self.at_clip("S2-c11")
        _grow_bars(self, [(r4[2], 3.0 * 0.92, "left",
                                [type_in(r4[0], run_time=0.5), Create(r4[1]),
                                 type_in(r4[3], run_time=0.5)])], run_time=1.0)     # 33.27 -> 34.27

        # 页3：金句 + 概念图（c12-c13）
        cCard1 = _card("模型越练越强，简单题成批退化成全对组", 6.6, 1.4, CYAN, WHITE, 32,
                       CARD_FILL, "BOLD")
        line2 = t("训练得越好，信号反而越少了", 44, YELL, "BOLD")
        img = _img("s3-sixteen-sheets-round.png", 3.4)
        page_auto(cCard1, line2, img)

        self.at_clip("S2-c12")
        self.play(FadeOut(head2), FadeOut(formula), FadeOut(pnote),
                  *[FadeOut(m) for r in (r1, r2, r3, r4) for m in r],
                  type_in(cCard1, run_time=1.0), run_time=1.0)                      # 35.52 -> 36.52
        self.at_clip("S2-c13")
        self.play(FadeIn(img, shift=DOWN * 0.05), type_in(line2, run_time=1.0),
                  run_time=1.0)                                                     # 40.48 -> 41.48
        self.wait(0.2)
        self.emphasize(line2, run_time=0.7)                                         # 41.68 -> 42.38
        self.wait(3.20)                                                             # -> 45.58

        # 页4：难度偏差（c14-c17）
        note14 = t("反转还在后面", 30, MUTED, "BOLD")
        grid2 = _dots(4, 4, cell=0.68, gap=0.14, color=GREEN)
        grid2[-1].set_color(RED)
        ampNote = t("16 份对了 15 份：除以极小的标准差，\n微弱差异被放大成大梯度", 28, WHITE, "BOLD")
        cBias = _card("简单题和难题的权重，被系统性扭曲\n（Dr. GRPO 叫它难度偏差）", 6.6, 1.6,
                      RED, WHITE, 30, CARD_FILL, "BOLD")
        page4 = page_stack(note14, grid2, ampNote, cBias, buff=0.45)
        layout_page(page4)

        self.at_clip("S2-c14")
        self.play(FadeOut(cCard1), FadeOut(line2), FadeOut(img),
                  type_in(note14, run_time=0.7), run_time=0.7)                      # 45.78 -> 46.48
        self.at_clip("S2-c15")
        self.play(Create(grid2, run_time=1.2, lag_ratio=0.05), run_time=1.2)        # 47.32 -> 48.52
        self.at_clip("S2-c16")
        self.play(type_in(ampNote, run_time=1.0), run_time=1.0)                     # 51.29 -> 52.29
        self.at_clip("S2-c17")
        self.play_scroll_unroll(cBias, run_time=1.0)                                # 56.36 -> 57.36

        # 页5：DAPO 修法 + 结尾悬念（c18-c21）
        cDapo = _head("修法：DAPO 动态采样", 36)
        flow3 = t("过采样一批组 → 扔掉全对全错\n→ 补满有效样本再更新", 30, CYAN, "BOLD")
        cRes = _card("训练时间基本不变，收敛步数反而更少", 6.6, 1.3, GREEN, WHITE, 32,
                     CARD_FILL, "BOLD")
        cHook = _card("可第二堵墙，连修的法都还没人找到", 6.6, 1.5, YELL, WHITE, 34,
                      CARD_FILL, "BOLD")
        page_auto(cDapo, flow3, cRes, cHook)

        self.at_clip("S2-c18")
        self.play(FadeOut(note14), FadeOut(grid2), FadeOut(ampNote), FadeOut(cBias),
                  type_in(cDapo, run_time=0.9), type_in(flow3, run_time=1.0),
                  run_time=1.0)                                                     # 60.20 -> 61.20
        self.at_clip("S2-c20")
        self.play_scroll_unroll(cRes, run_time=1.0)                                 # 67.54 -> 68.54
        self.at_clip("S2-c21")
        self.play_scroll_unroll(cHook, run_time=1.0)                                # 71.87 -> 72.87
        self.wait(1.85)                                                             # -> 74.72
        self.transition_out(cDapo, flow3, cRes, cHook, f, run_time=0.4)             # 74.72 -> 75.12
        self.pad_to_voice()


# ---------------- S3 第二堵墙：一个总分，泼给几万个 token ----------------
class S3(_Base):
    def construct(self):
        self.bg()
        f = _footer(self)

        # 页1：output-level 同一个 A（c01-c04）
        head1 = _head("第二堵墙：一个总分，泼给几万个 token", 34)
        band = Rectangle(width=7.0, height=0.5, color=CARD_BORDER, stroke_width=2,
                         fill_color=CARD_FILL, fill_opacity=1.0)
        nodes = VGroup(*[Rectangle(width=0.42, height=0.42, color=MUTED, stroke_width=1.5,
                                   fill_color=CARD_FILL2, fill_opacity=1.0)
                         for _ in range(8)])
        nodes.arrange(RIGHT, buff=0.42)
        nodes.move_to(band.get_center())
        n3 = nodes[1]
        n3000 = nodes[-2]
        n3.set_color(YELL)
        n3000.set_color(YELL)
        lab3 = t("第 3 个 token", 22, YELL, "BOLD")
        lab3.next_to(n3, UP, buff=0.28)
        lab3000 = t("第 3000 个 token", 22, YELL, "BOLD")
        lab3000.next_to(n3000, UP, buff=0.28)
        aTag = t("整条序列共享同一个优势值 A", 30, CYAN, "BOLD")
        xa3 = t("× A", 24, WHITE, "BOLD")
        xa3.next_to(n3, DOWN, buff=0.28)
        xa3000 = t("× A", 24, WHITE, "BOLD")
        xa3000.next_to(n3000, DOWN, buff=0.28)
        page_auto(head1, VGroup(band, nodes, lab3, lab3000), aTag, VGroup(xa3, xa3000))

        self.at_clip("S3-c01")
        self.play(type_in(head1, run_time=1.0), Create(band, run_time=1.0),
                  Create(nodes, run_time=1.0, lag_ratio=0.08), run_time=1.2)        # 0.00 -> 1.20
        self.at_clip("S3-c02")
        self.play(type_in(aTag, run_time=0.7), run_time=0.7)                        # 3.88 -> 4.58
        self.at_clip("S3-c03")
        self.play(type_in(lab3, run_time=0.5), type_in(lab3000, run_time=0.5),
                  run_time=0.6)                                                     # 5.89 -> 6.49
        self.at_clip("S3-c04")
        self.play(type_in(xa3, run_time=0.5), type_in(xa3000, run_time=0.5),
                  run_time=0.5)                                                     # 9.15 -> 9.65

        # 页2：连坐（c05-c06）
        cGood = _card("好答案里面的浑招，也会被一同推高", 6.6, 1.5, YELL, WHITE, 32,
                      CARD_FILL, "BOLD")
        cBad = _card("一堆烂答案里面的妙手，却被连坐拉低", 6.6, 1.5, YELL, WHITE, 32,
                     CARD_FILL, "BOLD")
        lianzu = t("连坐", 46, RED, "BOLD")
        page_auto(cGood, cBad, lianzu)

        self.at_clip("S3-c05")
        self.play(FadeOut(head1), FadeOut(band), FadeOut(nodes), FadeOut(lab3),
                  FadeOut(lab3000), FadeOut(aTag), FadeOut(xa3), FadeOut(xa3000),
                  type_in(cGood, run_time=0.9), run_time=0.9)                       # 10.85 -> 11.75
        self.at_clip("S3-c06")
        self.play(type_in(cBad, run_time=0.9), run_time=0.9)                        # 13.49 -> 14.39
        self.wait(0.2)
        self.play(type_in(lianzu, run_time=0.6), run_time=0.6)                      # 14.59 -> 15.19

        # 页3：GAE vs GRPO 对比 + 长卷概念图（c07-c10）
        leftHead = t("有的方案：每步单独估值", 28, CYAN, "BOLD")
        fadeSquares = VGroup(*[Rectangle(width=0.5, height=0.5, color=CYAN, stroke_width=1.5,
                                         fill_color=CYAN, fill_opacity=0.85 - 0.07 * i)
                               for i in range(10)])
        fadeSquares.arrange(RIGHT, buff=0.12)
        rightHead = t("GRPO：终点一个总分，平摊几万 token", 28, YELL, "BOLD")
        img = _img("s4-long-scroll-round.png", 3.6)
        note10 = t("序列越长，每个 token 分到的信号越稀", 28, WHITE, "BOLD")
        page3 = page_stack(leftHead, fadeSquares, rightHead, img, note10, buff=0.55)
        layout_page(page3)

        self.at_clip("S3-c07")
        self.play(FadeOut(cGood), FadeOut(cBad), FadeOut(lianzu),
                  type_in(leftHead, run_time=0.8), run_time=0.8)                    # 16.38 -> 17.18
        self.at_clip("S3-c08")
        self.play(Create(fadeSquares, run_time=1.2, lag_ratio=0.08), run_time=1.2)  # 19.93 -> 21.13
        self.at_clip("S3-c09")
        self.play(type_in(rightHead, run_time=0.8), FadeIn(img, shift=DOWN * 0.05),
                  run_time=0.8)                                                     # 23.14 -> 23.94
        self.at_clip("S3-c10")
        self.play(type_in(note10, run_time=0.9), run_time=0.9)                      # 28.25 -> 29.15

        # 页4：数学本体（c11-c12）
        cLong = _card("长 CoT、长程 agent 任务，动辄几万 token", 6.6, 1.4, CYAN, WHITE,
                      32, CARD_FILL, "BOLD")
        line12 = t("这就是长程任务撑不住的数学本体", 40, YELL, "BOLD")
        page_auto(cLong, line12)

        self.at_clip("S3-c11")
        self.play(FadeOut(leftHead), FadeOut(fadeSquares), FadeOut(rightHead),
                  FadeOut(img), FadeOut(note10),
                  type_in(cLong, run_time=0.9), run_time=0.9)                       # 31.39 -> 32.29
        self.at_clip("S3-c12")
        self.play(type_in(line12, run_time=1.1), run_time=1.1)                      # 35.33 -> 36.43
        self.wait(0.2)
        self.emphasize(line12, run_time=0.7)                                        # 36.63 -> 37.33

        # 页5：没有修法 + 尾钩（c13-c17）
        cNoFix = _card("这堵墙至今没有修法", 6.4, 1.2, YELL, WHITE, 36, CARD_FILL, "BOLD")
        cDapoLoss = _card("DAPO 的 token-level loss", 6.4, 1.2, CYAN, WHITE, 32,
                          CARD_FILL, "BOLD")
        cOnly = _card("只是改了 loss 加权方式，分摊一动没动", 6.4, 1.3, RED, WHITE, 32,
                      CARD_FILL, "BOLD")
        cCritic = _card("critic 的位置，没人补上", 6.4, 1.2, RED, WHITE, 32, CARD_FILL, "BOLD")
        cHook3 = t("但长度这件事，还藏着更荒唐的第三堵", 30, YELL, "BOLD")
        page5 = page_stack(cNoFix, cDapoLoss, cOnly, cCritic, cHook3, buff=0.45)
        layout_page(page5)

        self.at_clip("S3-c13")
        self.play(FadeOut(cLong), FadeOut(line12),
                  type_in(cNoFix, run_time=0.9), run_time=0.9)                      # 38.00 -> 38.90
        self.at_clip("S3-c14")
        self.play_scroll_unroll(cDapoLoss, run_time=0.9)                            # 39.77 -> 40.67
        self.at_clip("S3-c15")
        self.play_scroll_unroll(cOnly, run_time=0.9)                                # 42.93 -> 43.83
        self.at_clip("S3-c16")
        self.play_scroll_unroll(cCritic, run_time=0.9)                              # 46.54 -> 47.44
        self.at_clip("S3-c17")
        self.play(type_in(cHook3, run_time=0.8), run_time=0.8)                      # 48.90 -> 49.70
        self.wait(2.10)                                                             # -> 51.80
        self.transition_out(cNoFix, cDapoLoss, cOnly, cCritic, cHook3, f, run_time=0.4)
        self.pad_to_voice()                                                         # -> 52.40


# ---------------- S4 第三堵墙：错了，还更啰嗦 ----------------
class S4(_Base):
    def construct(self):
        self.bg()
        f = _footer(self)

        # 页1：长度归一（c01-c04）
        head1 = _head("第三堵墙：错了，还更啰嗦", 36)
        cDivLen = _card("每份答卷还要按长度归一：除以回答长度", 6.6, 1.4, CYAN, WHITE, 32,
                        CARD_FILL, "BOLD")
        shortLab = t("短答卷：每个 token 摊到厚惩罚", 26, WHITE, "BOLD")
        shortBar = Rectangle(width=3.2, height=0.42, color=RED, fill_color=RED, fill_opacity=0.85)
        longLab = t("长答卷：惩罚被摊薄", 26, WHITE, "BOLD")
        longBar = Rectangle(width=3.2, height=0.12, color=RED, fill_color=RED, fill_opacity=0.85)
        shortRow = VGroup(shortLab, shortBar).arrange(DOWN, buff=0.22)
        longRow = VGroup(longLab, longBar).arrange(DOWN, buff=0.22)
        cLearn = _card("模型学到的：答案越长越好", 6.6, 1.4, YELL, WHITE, 34, CARD_FILL, "BOLD")
        page1 = page_stack(head1, cDivLen, shortRow, longRow, cLearn, buff=0.55)
        layout_page(page1)

        self.at_clip("S4-c01")
        self.play(type_in(head1, run_time=1.0), run_time=1.0)                       # 0.12 -> 1.12
        self.at_clip("S4-c02")
        self.play_scroll_unroll(cDivLen, run_time=1.0)                              # 5.25 -> 6.25
        self.at_clip("S4-c03")
        self.play(Create(shortBar), Create(longBar), type_in(shortLab, run_time=0.6),
                  type_in(longLab, run_time=0.6), run_time=0.9)                     # 6.63 -> 7.53
        self.at_clip("S4-c04")
        self.play_scroll_unroll(cLearn, run_time=1.0)                               # 11.17 -> 12.17

        # 页2：R1-Zero 实测双条（c05-c09）
        cDs = _card("老版本 DeepSeek 经常思考和输出过长", 6.6, 1.3, MUTED, WHITE, 32,
                    CARD_FILL, "BOLD")
        rWrong = _bar_row("错误回答", "8206 字符", RED, 0.96)
        rRight = _bar_row("正确回答", "4965 字符", GREEN, 0.58)
        c65 = t("错了，还长 65%", 40, YELL, "BOLD")
        page_auto(cDs, rWrong, rRight, c65)

        self.at_clip("S4-c05")
        self.play(FadeOut(head1), FadeOut(cDivLen), FadeOut(shortRow), FadeOut(longRow),
                  FadeOut(cLearn), type_in(cDs, run_time=1.0), run_time=1.0)        # 15.27 -> 16.27
        self.at_clip("S4-c07")
        _grow_bars(self, [(rWrong[2], 3.0 * 0.96, "left",
                                [type_in(rWrong[0], run_time=0.5), Create(rWrong[1]),
                                 type_in(rWrong[3], run_time=0.5)])], run_time=1.0)  # 21.60 -> 22.60
        self.at_clip("S4-c08")
        _grow_bars(self, [(rRight[2], 3.0 * 0.58, "left",
                                [type_in(rRight[0], run_time=0.5), Create(rRight[1]),
                                 type_in(rRight[3], run_time=0.5)])], run_time=1.0)  # 29.84 -> 30.84
        self.at_clip("S4-c09")
        self.play(type_in(c65, run_time=0.8), run_time=0.8)                         # 32.09 -> 32.89
        self.wait(0.2)
        self.emphasize(c65, run_time=0.7)                                           # 33.09 -> 33.79

        # 页3：GSPO（c10-c13）
        cQwen = _card("Qwen 团队撞上同一堵长度的墙", 6.6, 1.2, CYAN, WHITE, 32,
                      CARD_FILL, "BOLD")
        cNoise = _card("逐 token 的修正系数，噪声沿长序列累积", 6.6, 1.3, RED, WHITE, 30,
                       CARD_FILL, "BOLD")
        cCollapse = _card("训练崩到撤销检查点都救不回来", 6.6, 1.2, RED, WHITE, 32,
                          CARD_FILL, "BOLD")
        cGspo = _card("GSPO：把修正挪到整条序列一级", 6.6, 1.3, GREEN, WHITE, 32,
                      CARD_FILL, "BOLD")
        cQwen3 = t("Qwen3 的 RL 训练，用的就是它", 28, MUTED, "BOLD")
        page3 = page_stack(cQwen, cNoise, cCollapse, cGspo, cQwen3, buff=0.4)
        layout_page(page3)

        self.at_clip("S4-c10")
        self.play(FadeOut(cDs), *[FadeOut(m) for r in (rWrong, rRight) for m in r],
                  FadeOut(c65), type_in(cQwen, run_time=0.9), run_time=0.9)        # 34.43 -> 35.33
        self.at_clip("S4-c11")
        self.play_scroll_unroll_many(cNoise, cCollapse, run_time=1.0)               # 40.35 -> 41.35
        self.at_clip("S4-c12")
        self.play_scroll_unroll(cGspo, run_time=1.0)                                # 44.90 -> 45.90
        self.at_clip("S4-c13")
        self.play(type_in(cQwen3, run_time=0.7), run_time=0.7)                      # 48.48 -> 49.18

        # 页4：尾钩（c14-c15）
        q14 = t("可删掉除以长度，就完了吗？", 38, YELL, "BOLD")
        a15 = t("三堵墙，其实是同一个根源", 38, WHITE, "BOLD")
        page_auto(q14, a15)

        self.at_clip("S4-c14")
        self.play(FadeOut(cQwen), FadeOut(cNoise), FadeOut(cCollapse), FadeOut(cGspo),
                  FadeOut(cQwen3), type_in(q14, run_time=0.9), run_time=0.9)        # 51.88 -> 52.78
        self.at_clip("S4-c15")
        self.play(type_in(a15, run_time=0.9), run_time=0.9)                         # 54.33 -> 55.23
        self.wait(1.31)                                                             # -> 56.54
        self.transition_out(q14, a15, f, run_time=0.4)                              # 56.54 -> 56.94
        self.pad_to_voice()


# ---------------- S5 修法：Dr. GRPO 把两个除法全删了 ----------------
class S5(_Base):
    def construct(self):
        self.bg()
        f = _footer(self)

        # 页1：删掉两个除法（c01-c03）
        head1 = _head("修法：Dr. GRPO", 36)
        cGrpoObj = _card("GRPO 目标：组内减均值、除标准差、除长度", 6.6, 1.6, CYAN, WHITE, 32,
                         CARD_FILL, "BOLD")
        cFix = _card("优势 = r 减均值\n归一分母换成固定常数", 6.6, 1.6, GREEN, WHITE, 32,
                     CARD_FILL, "BOLD")
        page1 = page_auto(head1, cGrpoObj)

        self.at_clip("S5-c01")
        self.play(type_in(head1, run_time=0.9), run_time=0.9)                       # 0.00 -> 0.90
        self.wait(0.2)
        self.play_scroll_unroll(cGrpoObj, run_time=1.0)                             # 1.10 -> 2.10
        self.at_clip("S5-c02")
        cross = self.play_red_cross(cGrpoObj, run_time=0.65)                        # 5.26 -> 5.91
        self.wait(1.09)
        self.play(FadeOut(cross), run_time=0.3)                                     # 7.00 -> 7.30
        self.at_clip("S5-c03")
        self.morph_to(cGrpoObj, cFix, run_time=1.0)                                 # 7.40 -> 8.40

        # 页2：回到 PPO（c04）
        line4 = t("绕了一圈，回到 PPO 式的目标函数", 40, YELL, "BOLD")
        note4 = t("Dr. GRPO：Sea AI Lab", 26, MUTED)
        page_auto(line4, note4)

        self.at_clip("S5-c04")
        self.play(FadeOut(head1), FadeOut(cFix), type_in(line4, run_time=1.0),
                  type_in(note4, run_time=0.6), run_time=1.0)                       # 11.98 -> 12.98

        # 页3：战绩（c05-c06）
        labAIME = t("AIME 2024 · 7B 模型", 30, WHITE, "BOLD")
        cnt_slot = dynamic_slot(2.6, 1.1)
        cnt_row = stable_row(cnt_slot, buff=0.3)
        cHours = _card("8 卡 A100，跑 27 小时", 6.6, 1.3, CYAN, WHITE, 32, CARD_FILL, "BOLD")
        page_auto(labAIME, cnt_row, cHours)

        self.at_clip("S5-c05")
        self.play(FadeOut(line4), FadeOut(note4), type_in(labAIME, run_time=0.8),
                  run_time=0.8)                                                     # 15.79 -> 16.59
        self.wait(0.2)
        n433 = self.counter_value(0, 43.3, suffix="%", decimals=1, size=56, color=YELL,
                                  run_time=1.2, anchor=cnt_slot)                   # 16.79 -> 17.99
        self.at_clip("S5-c06")
        self.play_scroll_unroll(cHours, run_time=1.0)                               # 21.15 -> 22.15

        # 页4：三篇论文 + 尾钩（c07-c10）
        cDapo2 = _card("DAPO 补信号", 2.1, 0.9, CYAN, WHITE, 26, CARD_FILL, "BOLD")
        cDr2 = _card("Dr. GRPO 纠偏差", 2.1, 0.9, CYAN, WHITE, 26, CARD_FILL, "BOLD")
        cGspo2 = _card("GSPO 稳噪声", 2.1, 0.9, CYAN, WHITE, 26, CARD_FILL, "BOLD")
        row3cards = VGroup(cDapo2, cDr2, cGspo2).arrange(RIGHT, buff=0.45)
        note9 = t("三篇论文，各修一堵墙", 28, WHITE, "BOLD")
        cHook5 = _card("可那个被省掉的 critic，真的不需要吗？", 6.6, 1.5, YELL, WHITE, 34,
                       CARD_FILL, "BOLD")
        img = _img("s1-empty-chair-round.png", 3.0)
        page4 = page_stack(row3cards, note9, cHook5, img, buff=0.45)
        layout_page(page4)

        self.at_clip("S5-c07")
        self.play(FadeOut(labAIME), FadeOut(n433), FadeOut(cHours), run_time=0.4)   # 24.43 -> 24.83
        self.play_scroll_unroll_many(cDapo2, cDr2, run_time=1.0)                    # 24.83 -> 25.83
        self.at_clip("S5-c08")
        self.play_scroll_unroll(cGspo2, run_time=1.0)                               # 29.29 -> 30.29
        self.at_clip("S5-c09")
        self.play(type_in(note9, run_time=0.7), run_time=0.7)                       # 31.34 -> 32.04
        self.at_clip("S5-c10")
        self.play(FadeIn(img, shift=DOWN * 0.05), run_time=0.8)                     # 34.15 -> 34.95
        self.wait(0.2)
        self.play_scroll_unroll(cHook5, run_time=1.0)                               # 35.15 -> 36.15
        self.wait(3.26)                                                             # -> 39.41
        self.transition_out(row3cards, note9, cHook5, img, f, run_time=0.4)         # 39.41 -> 39.81
        self.pad_to_voice()


# ---------------- S6 收尾：省下的和失去的，是同一个东西 ----------------
class S6(_Base):
    def construct(self):
        self.bg()
        f = _footer(self)

        # 页1：同一根源（c01-c03）
        head1 = _head("三堵墙，同一个根源", 36)
        w1 = _card("信号消失", 2.1, 0.9, RED, WHITE, 26, CARD_FILL, "BOLD")
        w2 = _card("功劳平摊", 2.1, 0.9, RED, WHITE, 26, CARD_FILL, "BOLD")
        w3 = _card("长度带偏", 2.1, 0.9, RED, WHITE, 26, CARD_FILL, "BOLD")
        wallRow = VGroup(w1, w2, w3).arrange(RIGHT, buff=0.45)
        root = _card("组内排名", 5.0, 1.2, YELL, WHITE, 36, CARD_FILL, "BOLD")
        c3cond = _card("组内有差异、序列不太长、回答不太啰嗦时，便宜好用", 6.6, 1.4, CYAN,
                       WHITE, 30, CARD_FILL, "BOLD")
        page_auto(head1, wallRow, root, c3cond)

        self.at_clip("S6-c01")
        self.play(type_in(head1, run_time=0.9), run_time=0.9)                       # 0.00 -> 0.90
        self.wait(0.2)
        self.play_scroll_unroll_many(w1, w2, w3, run_time=1.0)                      # 1.10 -> 2.10
        self.at_clip("S6-c02")
        self.play(w1.animate.shift(DOWN * 0.35), w2.animate.shift(DOWN * 0.35),
                  w3.animate.shift(DOWN * 0.35), run_time=0.4)                    # 4.62 -> 5.02
        self.wait(0.2)
        self.play_scroll_unroll(root, run_time=0.8)                               # 5.22 -> 6.02
        self.at_clip("S6-c03")
        self.play_scroll_unroll(c3cond, run_time=1.0)                               # 6.59 -> 7.59

        # 页2：三条件打破（c04-c06）
        cBreak = t("长程任务把三个条件同时打破", 34, YELL, "BOLD")
        b1 = _card("没有差异", 2.1, 0.9, RED, WHITE, 26, CARD_FILL, "BOLD")
        b2 = _card("序列极长", 2.1, 0.9, RED, WHITE, 26, CARD_FILL, "BOLD")
        b3 = _card("惩罚被摊薄", 2.1, 0.9, RED, WHITE, 26, CARD_FILL, "BOLD")
        breakRow = VGroup(b1, b2, b3).arrange(RIGHT, buff=0.45)
        r1 = _card("没有信号", 2.1, 0.9, RED, WHITE, 26, CARD_FILL, "BOLD")
        r2 = _card("平摊黑锅", 2.1, 0.9, RED, WHITE, 26, CARD_FILL, "BOLD")
        r3 = _card("奖励啰嗦", 2.1, 0.9, RED, WHITE, 26, CARD_FILL, "BOLD")
        resRow = VGroup(r1, r2, r3).arrange(RIGHT, buff=0.45)
        page_auto(cBreak, breakRow, resRow)

        self.at_clip("S6-c04")
        self.play(FadeOut(head1), FadeOut(wallRow), FadeOut(root), FadeOut(c3cond),
                  type_in(cBreak, run_time=1.0), run_time=1.0)                      # 12.41 -> 13.41
        self.at_clip("S6-c05")
        self.play_scroll_unroll_many(b1, b2, b3, run_time=1.0)                      # 16.05 -> 17.05
        self.at_clip("S6-c06")
        self.play_scroll_unroll_many(r1, r2, r3, run_time=1.0)                      # 18.15 -> 19.15

        # 页3：三家 + 金句（c07-c09）
        f1 = _card("DAPO 补信号", 2.1, 0.9, GREEN, WHITE, 26, CARD_FILL, "BOLD")
        f2 = _card("Dr. GRPO 纠偏差", 2.1, 0.9, GREEN, WHITE, 26, CARD_FILL, "BOLD")
        f3 = _card("GSPO 稳噪声", 2.1, 0.9, GREEN, WHITE, 26, CARD_FILL, "BOLD")
        fixRow = VGroup(f1, f2, f3).arrange(RIGHT, buff=0.45)
        note8 = t("但没有一家把 critic 请回来", 30, WHITE, "BOLD")
        line9 = t("省下来的和失去的，竟然是同一个东西", 40, YELL, "BOLD")
        page_auto(fixRow, note8, line9)

        self.at_clip("S6-c07")
        self.play(FadeOut(cBreak), FadeOut(breakRow), FadeOut(resRow), run_time=0.4)  # 21.59 -> 21.99
        self.play_scroll_unroll_many(f1, f2, run_time=0.9)                          # 21.99 -> 22.89
        self.at_clip("S6-c08")
        self.play_scroll_unroll(f3, run_time=0.9)                                   # 25.30 -> 26.20
        self.wait(0.2)
        self.play(type_in(note8, run_time=0.8), run_time=0.8)                       # 26.40 -> 27.20
        self.at_clip("S6-c09")
        self.play(type_in(line9, run_time=1.1), run_time=1.1)                       # 29.51 -> 30.61
        self.wait(0.2)
        self.emphasize(line9, run_time=0.7)                                         # 30.81 -> 31.51

        # 页4：互动（c10-c12）
        n10 = t("agent 长程任务当道的今天", 30, WHITE, "BOLD")
        q11 = t("GRPO 是明日黄花，还是换个方式王者归来？", 34, YELL, "BOLD")
        n12 = t("评论区聊聊", 30, MUTED, "BOLD")
        page_auto(n10, q11, n12)

        self.at_clip("S6-c10")
        self.play(FadeOut(fixRow), FadeOut(note8), FadeOut(line9),
                  type_in(n10, run_time=0.8), run_time=0.8)                         # 32.87 -> 33.67
        self.at_clip("S6-c11")
        self.play(type_in(q11, run_time=1.0), run_time=1.0)                         # 36.95 -> 37.95
        self.wait(0.2)
        self.at_clip("S6-c12")
        self.play(type_in(n12, run_time=0.7), run_time=0.7)                         # 41.68 -> 42.38

        # 页5：品牌尾卡（c13-c14）
        avatar = ImageMobject(str(AVATAR))
        avatar.scale_to_fit_width(3.2)
        lFollow = t("关注「数解AI」", 40, YELL, "BOLD")
        lTitle = t("《GRPO 省了一个 critic，\n长任务为什么反而崩了？》", 30, WHITE, "BOLD")
        lGuide = t("查看公众号文章", 30, GREEN, "BOLD")
        lNext = t("下一篇：奖励函数——AI 钻空子的源头", 26, MUTED, "BOLD")
        page5 = page_stack(avatar, lFollow, lTitle, lGuide, lNext, buff=0.45)
        layout_page(page5)

        self.at_clip("S6-c13")
        self.play(FadeOut(n10), FadeOut(q11), FadeOut(n12), run_time=0.5)           # 42.97 -> 43.47
        self.play(FadeIn(avatar, shift=DOWN * 0.05), type_in(lNext, run_time=0.9),
                  run_time=0.9)                                                     # 43.47 -> 44.37
        self.at_clip("S6-c14")
        self.play(type_in(lFollow, run_time=0.9), type_in(lTitle, run_time=1.0),
                  type_in(lGuide, run_time=0.7), run_time=1.0)                       # 48.23 -> 49.23
        self.wait(3.27)                                                             # -> 52.50
        self.transition_out(avatar, lFollow, lTitle, lGuide, lNext, f, run_time=0.4)  # 52.50 -> 52.90
        self.pad_to_voice()
