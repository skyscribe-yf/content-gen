#!/usr/bin/env python3
"""《马尔可夫决策过程：AI 怎么在不确定里做选择》视频号 Manim 动画（竖屏 1080×1920）

6 个场景 S1-S6，与 storyboard.md 一一对应。
- 配音：MiniMax 精英男声（speech-2.8-turbo，speed 1.0 pitch +2）
- 时间轴：at_clip("S1-c01") 挂 tts/sentence-boundaries.json 的 clip 起点（先声音后动画门禁）
- 布局：整页规划（page_stack + layout_page / page_auto），上下留白各 ≤10%
- 动画降噪：每页 1 个主视觉动效；emphasize 全片 4 次；v2 动效 0 处
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
VOICE_DUR = {"S1": 30.09, "S2": 39.0, "S3": 46.18, "S4": 43.85, "S5": 46.58, "S6": 54.29}
TAIL = 2.5


def _footer(self) -> Text:
    f = t("数解AI · 强化学习原理", 20, MUTED).to_edge(DOWN, buff=1.15)
    self.add(f)
    return f


def _head(text: str, size: float = 38) -> Text:
    return t(text, size, YELL, "BOLD").to_edge(UP, buff=1.2)


# ---------------- S1 开场钩子：agent 修 bug ----------------
class S1(_Base):
    def construct(self):
        self.bg()
        f = _footer(self)

        # 页1：概念图 + 30 次工具（c01-c03）
        head = _head("AI 修 bug，要调 30 次工具", 38)
        img = ImageMobject(str(IMG / "agent-round.png"))
        img.scale_to_fit_width(5.0)
        note0 = t("以 coding agent 修 bug 为例", 24, MUTED)
        lab = t("工具调用次数", 32, WHITE, "BOLD")
        slot = dynamic_slot(2.2, 0.9)
        crow = stable_row(lab, slot, buff=0.4)
        page1 = page_stack(img, note0, crow, buff=1.0)
        layout_page(page1)

        self.at_clip("S1-c01")
        self.play_parallel(type_in(head, run_time=1.1), FadeIn(img, shift=DOWN * 0.05),
                           type_in(note0, run_time=0.6), run_time=1.1)
        self.at_clip("S1-c02")
        n = self.counter_value(0, 30, suffix=" 次", size=64, color=YELL,
                                run_time=1.2, anchor=slot,
                                extra_anims=[type_in(lab, run_time=0.6)])  # 主视觉：数字滚动
        self.at_clip("S1-c04")

        # 页2：轨迹链 + 第 3 步红叉（c04-c05）
        head2 = _head("第 3 步，方向偏了一点", 38)
        segs = VGroup(*[Rectangle(width=0.55, height=1.1, color=CYAN,
                                  fill_color=CYAN, fill_opacity=0.35) for _ in range(10)])
        segs.arrange(RIGHT, buff=0.18)
        c1 = _card("第 3 步：跳过测试，直接改配置", 5.6, 1.6, CYAN, WHITE, 30, CARD_FILL, "BOLD")
        c2 = _card("后面 27 步：全在错误方向上打转", 5.6, 1.6, RED, WHITE, 30, CARD_FILL, "BOLD")
        note = t("最后交上来一份「修好」的代码，测试还是红的", 24, WHITE)
        page2 = page_stack(segs, c1, c2, note, buff=1.0)
        layout_page(page2)

        self.play(FadeOut(head), FadeOut(img), FadeOut(n), FadeOut(crow), FadeOut(note0),
                  type_in(head2, run_time=0.9), run_time=0.9)
        self.play(*[Create(s) for s in segs], run_time=1.2, lag_ratio=0.2)  # 主视觉：轨迹逐段
        self.wait(0.1)
        cross = self.play_red_cross(segs[2])
        self.at_clip("S1-c05")
        self.play_scroll_unroll_many(c1, c2, run_time=1.3)
        self.wait(0.1)
        self.play(type_in(note, run_time=0.9))
        self.at_clip("S1-c06")

        # 页3：序列决策宿命（c06-c07）
        head3 = _head("这不是 agent 笨", 40)
        big = t("序列决策的宿命", 52, YELL, "BOLD")
        c3 = _card("每一步都影响后面", 5.6, 2.0, CYAN, WHITE, 36, CARD_FILL, "BOLD")
        c4 = _card("你永远不知道当前这一步是不是最优的", 5.6, 2.0, GREEN, WHITE, 32, CARD_FILL, "BOLD")
        page3 = page_stack(big, c3, c4, buff=1.3)
        layout_page(page3)

        self.play(FadeOut(head2), FadeOut(segs), FadeOut(c1), FadeOut(c2),
                  FadeOut(note), FadeOut(cross),
                  type_in(head3, run_time=0.9), run_time=0.9)
        self.play(type_in(big, run_time=0.9))
        self.wait(0.1)
        self.play_scroll_unroll(c3, run_time=1.2)  # 主视觉：拉幕
        self.at_clip("S1-c07")
        self.play_scroll_unroll(c4, run_time=1.2)
        self.at_clip("S1-c08")

        # 页4：悬念（c08）
        head4 = _head("那怎么办？", 48)
        page4 = page_auto(head4)
        self.play(FadeOut(head3), FadeOut(big), FadeOut(c3), FadeOut(c4),
                  type_in(head4, run_time=1.0), run_time=1.0)
        self.wait(0.2)
        self.transition_out(head4, f, page4)
        self.pad_to_voice()


# ---------------- S2 随机过程：世界是随机的 ----------------
class S2(_Base):
    def construct(self):
        self.bg()
        f = _footer(self)

        # 页1：单步 vs 序列（c01-c04）
        head = _head("两种决策", 40)
        c1 = _card("单步决策\n中午吃什么，选了就完了", 5.6, 2.2, GREEN, WHITE, 32, CARD_FILL, "BOLD")
        c2 = _card("序列决策\n修 bug、下棋、写代码、开车", 5.6, 2.2, YELL, WHITE, 32, CARD_FILL, "BOLD")
        note = t("每一步的选择，都会改变你下一步面对的处境", 26, WHITE)
        page1 = page_stack(c1, c2, note, buff=1.4)
        layout_page(page1)

        self.at_clip("S2-c01")
        self.play(type_in(head, run_time=1.1))
        self.at_clip("S2-c02")
        self.play_scroll_unroll(c1, run_time=1.2)  # 主视觉：拉幕
        self.at_clip("S2-c03")
        self.play_scroll_unroll(c2, run_time=1.2)
        self.at_clip("S2-c04")
        self.play(type_in(note, run_time=0.9))
        self.at_clip("S2-c05")

        # 页2：世界是随机的 + 状态序列（c05-c08）
        head2 = _head("世界是随机的", 40)
        r1 = _card("机器人：迈一步，可能被气流留在原地", 5.6, 1.2, CYAN, WHITE, 28, CARD_FILL, "BOLD")
        r2 = _card("围棋：对手怎么应，你控制不了", 5.6, 1.2, GREEN, WHITE, 28, CARD_FILL, "BOLD")
        r3 = _card("agent：工具返回什么，不能完全预料", 5.6, 1.2, YELL, WHITE, 28, CARD_FILL, "BOLD")
        rrow = VGroup(r1, r2, r3).arrange(DOWN, buff=0.5)
        s1 = cnode("S₁", CYAN, radius=0.6, fs=24)
        s2 = cnode("S₂", CYAN, radius=0.6, fs=24)
        s3 = cnode("S₃", CYAN, radius=0.6, fs=24)
        sd = cnode("…", MUTED, radius=0.6, fs=28)
        srow = VGroup(s1, s2, s3, sd).arrange(RIGHT, buff=0.8)
        sa1 = Arrow(s1.get_right(), s2.get_left(), color=YELL, stroke_width=4, buff=0.1)
        sa2 = Arrow(s2.get_right(), s3.get_left(), color=YELL, stroke_width=4, buff=0.1)
        sa3 = Arrow(s3.get_right(), sd.get_left(), color=YELL, stroke_width=4, buff=0.1)
        srowg = VGroup(srow, sa1, sa2, sa3)
        note2 = t("一串状态随时间演化，每一步带着概率", 28, WHITE)
        page2 = page_stack(rrow, srowg, note2, buff=0.9)
        layout_page(page2)

        self.play(FadeOut(head), FadeOut(c1), FadeOut(c2), FadeOut(note),
                  type_in(head2, run_time=0.9), run_time=0.9)
        self.play_scroll_unroll_many(r1, r2, r3, run_time=1.4)  # 主视觉：三卡拉幕
        self.at_clip("S2-c07")
        self.play(FadeIn(s1), FadeIn(s2), FadeIn(s3), FadeIn(sd),
                  Create(sa1), Create(sa2), Create(sa3), run_time=1.2)
        self.at_clip("S2-c08")
        self.play(type_in(note2, run_time=0.9))
        self.at_clip("S2-c09")

        # 页3：悬念（c09-c10）
        head3 = _head("数学家说：给序列决策，造一套语言", 36)
        page3 = page_auto(head3)
        self.play(FadeOut(head2), FadeOut(r1), FadeOut(r2), FadeOut(r3),
                  FadeOut(s1), FadeOut(s2), FadeOut(s3), FadeOut(sd),
                  FadeOut(sa1), FadeOut(sa2), FadeOut(sa3), FadeOut(note2),
                  type_in(head3, run_time=1.0), run_time=1.0)
        self.at_clip("S2-c10")
        head4 = _head("这套语言的第一块，是什么？", 42)
        page4 = page_auto(head4)
        self.play(FadeOut(head3), type_in(head4, run_time=1.0), run_time=1.0)
        self.wait(0.3)
        self.transition_out(head4, f, page4)
        self.pad_to_voice()


# ---------------- S3 马尔可夫性质：健忘 ----------------
class S3(_Base):
    def construct(self):
        self.bg()
        f = _footer(self)

        # 页1：健忘爆点（c01-c03）
        head = _head("马尔可夫性质", 40)
        big = t("健忘", 88, YELL, "BOLD")
        c1 = _card("下一步的状态，只依赖当前状态", 5.6, 1.6, CYAN, WHITE, 32, CARD_FILL, "BOLD")
        c2 = _card("和更早的历史，无关", 5.6, 1.6, GREEN, WHITE, 32, CARD_FILL, "BOLD")
        page1 = page_stack(big, c1, c2, buff=1.6)
        layout_page(page1)

        self.at_clip("S3-c01")
        self.play(type_in(head, run_time=1.1))
        self.at_clip("S3-c03")
        self.play(type_in(big, run_time=0.9))
        self.emphasize(big, run_time=0.6)  # 1/4
        self.at_clip("S3-c04")
        self.play_scroll_unroll_many(c1, c2, run_time=1.3)  # 主视觉：两卡拉幕
        self.at_clip("S3-c05")

        # 页2：公式（c05-c07）
        head2 = _head("写成公式", 40)
        formula = MathTex(
            r"P(s_{t+1}\mid s_t) = P(s_{t+1}\mid s_t, s_{t-1}, s_{t-2}, \ldots)",
            tex_to_color_map={r"P(s_{t+1}\mid s_t)": YELL})
        formula.set_width(6.4)
        c3 = _card("只看当前状态 = 看完整个历史", 5.6, 1.8, CYAN, WHITE, 32, CARD_FILL, "BOLD")
        c4 = _card("该记的，都已经记在当前状态里了", 5.6, 1.8, GREEN, WHITE, 32, CARD_FILL, "BOLD")
        page2 = page_stack(formula, c3, c4, buff=1.6)
        layout_page(page2)

        self.play(FadeOut(head), FadeOut(big), FadeOut(c1), FadeOut(c2),
                  type_in(head2, run_time=0.9), run_time=0.9)
        self.play(FadeIn(formula), run_time=0.9)  # 主视觉：公式
        self.at_clip("S3-c06")
        self.play_scroll_unroll(c3, run_time=1.2)
        self.at_clip("S3-c07")
        self.play_scroll_unroll(c4, run_time=1.2)
        self.at_clip("S3-c08")

        # 页3：转移矩阵（c08-c09）
        head3 = _head("转移矩阵：每一行加起来必须等于 1", 32)
        cells = VGroup()
        vals = [[0.3, 0.7, 0], [0, 0.6, 0.4], [0, 0, 1]]
        for r in range(3):
            for c in range(3):
                cell = RoundedRectangle(corner_radius=0.1, width=1.4, height=1.0,
                                        color=MUTED, stroke_width=2,
                                        fill_color=CARD_FILL, fill_opacity=1.0)
                num = t(str(vals[r][c]), 30, WHITE, "BOLD")
                num.move_to(cell.get_center())
                cells.add(VGroup(cell, num))
        cells.arrange_in_grid(3, 3, buff=0.12)
        lab = t("每一行加起来必须等于 1", 30, YELL, "BOLD")
        c5 = _card("从任何状态出发，下一步总要去某个地方", 5.6, 1.4, CYAN, WHITE, 30, CARD_FILL, "BOLD")
        page3 = page_stack(cells, lab, c5, buff=1.2)
        layout_page(page3)

        self.play(FadeOut(head2), FadeOut(formula), FadeOut(c3), FadeOut(c4),
                  type_in(head3, run_time=0.9), run_time=0.9)
        self.play(*[FadeIn(g, scale=0.7) for g in cells], run_time=1.2)  # 主视觉：矩阵点亮
        self.at_clip("S3-c09")
        self.play(type_in(lab, run_time=0.9))
        self.wait(0.1)
        self.play_scroll_unroll(c5, run_time=1.2)
        self.at_clip("S3-c10")

        # 页4：工程抽象（c10-c12）
        head4 = _head("真实世界哪来这么干净的健忘？", 38)
        d1 = _card("不是世界的真相", 5.6, 2.2, MUTED, WHITE, 36, CARD_FILL, "BOLD")
        d2 = _card("是工程抽象", 5.6, 2.2, YELL, WHITE, 36, CARD_FILL, "BOLD")
        note4 = t("把影响下一步的所有信息，都塞进状态里", 28, WHITE)
        page4 = page_stack(d1, d2, note4, buff=1.4)
        layout_page(page4)

        self.play(FadeOut(head3), FadeOut(cells), FadeOut(lab), FadeOut(c5),
                  type_in(head4, run_time=0.9), run_time=0.9)
        self.play_scroll_unroll(d1, run_time=1.2)
        self.at_clip("S3-c11")
        self.play_scroll_unroll(d2, run_time=1.2)  # 主视觉：拉幕
        self.at_clip("S3-c12")
        self.play(type_in(note4, run_time=0.9))
        self.at_clip("S3-c13")

        # 页5：悬念（c13）
        head5 = _head("那大模型，算不算马尔可夫过程？", 36)
        page5 = page_auto(head5)
        self.play(FadeOut(head4), FadeOut(d1), FadeOut(d2), FadeOut(note4),
                  type_in(head5, run_time=1.0), run_time=1.0)
        self.wait(0.3)
        self.transition_out(head5, f, page5)
        self.pad_to_voice()


# ---------------- S4 反常识：大模型 = 高阶马尔可夫 ----------------
class S4(_Base):
    def construct(self):
        self.bg()
        f = _footer(self)

        # 页1：窗口示意（c01-c06）
        big_ok = t("算。", 60, YELL, "BOLD")
        head = _head("大模型：上下文窗口内的高阶马尔可夫", 32)
        win = RoundedRectangle(corner_radius=0.2, width=6.6, height=2.4,
                               color=YELL, stroke_width=3,
                               fill_color=CARD_FILL, fill_opacity=1.0)
        toks = VGroup(*[RoundedRectangle(corner_radius=0.1, width=0.62, height=0.62,
                                         color=CYAN, stroke_width=2,
                                         fill_color=CYAN, fill_opacity=0.4)
                        for _ in range(8)])
        toks.arrange_in_grid(2, 4, buff=0.18)
        toks.move_to(win.get_center())
        winlab = t("上下文窗口", 26, YELL, "BOLD").next_to(win, UP, buff=0.3)
        out1 = RoundedRectangle(corner_radius=0.1, width=0.62, height=0.62,
                                color=MUTED, stroke_width=2,
                                fill_color=MUTED, fill_opacity=0.25)
        out2 = RoundedRectangle(corner_radius=0.1, width=0.62, height=0.62,
                                color=MUTED, stroke_width=2,
                                fill_color=MUTED, fill_opacity=0.25)
        outg = VGroup(out1, out2).arrange(RIGHT, buff=0.3)
        outg.next_to(win, DOWN, buff=0.5)
        outlab = t("窗口外：完全健忘", 26, MUTED).next_to(outg, DOWN, buff=0.3)
        wgrp = VGroup(win, toks, winlab, outg, outlab)
        note = t("每生成一个 token，只依赖当前上下文", 28, WHITE)
        page1 = page_stack(big_ok, wgrp, note, buff=1.0)
        layout_page(page1)

        self.at_clip("S4-c01")
        self.play(type_in(big_ok, run_time=0.3))
        self.at_clip("S4-c02")
        self.play(type_in(head, run_time=1.0))
        self.play(FadeIn(win), FadeIn(winlab), run_time=0.7)
        self.play(*[FadeIn(tk, scale=0.5) for tk in toks], run_time=1.0)  # 主视觉：窗口点亮
        self.at_clip("S4-c04")
        self.play(FadeIn(out1), FadeIn(out2), run_time=0.4)
        c1 = Line(outg.get_corner(UL) + RIGHT * 0.15 + DOWN * 0.15,
                  outg.get_corner(DR) + LEFT * 0.15 + UP * 0.15,
                  color=RED, stroke_width=14)
        c2 = Line(outg.get_corner(UR) + LEFT * 0.15 + DOWN * 0.15,
                  outg.get_corner(DL) + RIGHT * 0.15 + UP * 0.15,
                  color=RED, stroke_width=14)
        cross = VGroup(c1, c2)
        self.play(GrowFromCenter(c1), GrowFromCenter(c2), run_time=0.4)
        self.play(cross.animate.scale(1.1), run_time=0.1)
        self.wait(0.05)
        self.play(cross.animate.scale(1 / 1.1), run_time=0.1)
        self.at_clip("S4-c05")
        self.play(type_in(outlab, run_time=0.6))
        self.at_clip("S4-c06")
        self.play(type_in(note, run_time=0.9))
        self.at_clip("S4-c07")

        # 页2：N-gram → 大模型 + 128K vs 5 阶（c07-c11）
        head2 = _head("同一个思路的升级", 40)
        g1 = _card("N-gram：显式的高阶马尔可夫", 5.6, 1.4, CYAN, WHITE, 30, CARD_FILL, "BOLD")
        g2 = _card("大模型：状态变成隐表示", 5.6, 1.4, GREEN, WHITE, 30, CARD_FILL, "BOLD")
        lab2 = t("上下文窗口", 32, WHITE, "BOLD")
        slot = dynamic_slot(2.6, 0.9)
        wrow = stable_row(lab2, slot, buff=0.4)
        k1 = _card("128K 阶", 3.0, 1.6, YELL, WHITE, 40, CARD_FILL, "BOLD")
        k2 = _card("经典 5 阶", 3.0, 1.6, MUTED, WHITE, 40, CARD_FILL, "BOLD")
        krow = VGroup(k1, k2).arrange(RIGHT, buff=0.6)
        note2 = t("骨架没变，变的只是「状态」的记法", 28, WHITE)
        page2 = page_stack(g1, g2, wrow, krow, note2, buff=0.7)
        layout_page(page2)

        self.play(FadeOut(head), FadeOut(win), FadeOut(toks), FadeOut(winlab),
                  FadeOut(out1), FadeOut(out2), FadeOut(outlab), FadeOut(note),
                  FadeOut(cross),
                  type_in(head2, run_time=0.9), run_time=0.9)
        self.play_scroll_unroll_many(g1, g2, run_time=1.3)  # 主视觉：两卡拉幕
        self.at_clip("S4-c08")
        n = self.counter_value(0, 128, suffix="K", size=64, color=YELL,
                               run_time=1.4, anchor=slot,
                               extra_anims=[type_in(lab2, run_time=0.6)])
        self.at_clip("S4-c09")
        self.play_scroll_unroll_many(k1, k2, run_time=1.3)
        self.emphasize(k1, run_time=0.6)  # 2/4
        self.at_clip("S4-c11")
        self.play(type_in(note2, run_time=0.9))
        self.at_clip("S4-c12")

        # 页3：agent 长任务崩（c12-c13）
        head3 = _head("agent 长任务为什么容易崩？", 38)
        e1 = _card("不是模型笨", 5.6, 2.2, GREEN, WHITE, 36, CARD_FILL, "BOLD")
        e2 = _card("是「状态」里装不下那么长的历史", 5.6, 2.2, RED, WHITE, 32, CARD_FILL, "BOLD")
        note3 = t("历史一长，该记的记不住", 28, WHITE)
        page3 = page_stack(e1, e2, note3, buff=1.4)
        layout_page(page3)

        self.play(FadeOut(head2), FadeOut(g1), FadeOut(g2), FadeOut(n),
                  FadeOut(wrow), FadeOut(k1), FadeOut(k2), FadeOut(note2),
                  type_in(head3, run_time=0.9), run_time=0.9)
        self.play_scroll_unroll(e1, run_time=1.2)
        self.at_clip("S4-c13")
        self.play_scroll_unroll(e2, run_time=1.2)  # 主视觉：拉幕
        self.wait(0.1)
        self.play(type_in(note3, run_time=0.9))
        self.at_clip("S4-c14")

        # 页4：悬念（c14）
        head4 = _head("那怎么让 AI 做决策？", 42)
        page4 = page_auto(head4)
        self.play(FadeOut(head3), FadeOut(e1), FadeOut(e2), FadeOut(note3),
                  type_in(head4, run_time=1.0), run_time=1.0)
        self.wait(0.2)
        self.transition_out(head4, f, page4)
        self.pad_to_voice()


# ---------------- S5 MDP 五元组 ----------------
class S5(_Base):
    def construct(self):
        self.bg()
        f = _footer(self)

        # 页1：五元组（c01-c06）
        head = _head("MDP：五个要素", 40)
        big = t("S · A · P · R · γ", 44, YELL, "BOLD")
        m1 = _card("S\n状态集合", 2.0, 1.8, CYAN, WHITE, 28, CARD_FILL, "BOLD")
        m2 = _card("A\n动作集合", 2.0, 1.8, GREEN, WHITE, 28, CARD_FILL, "BOLD")
        m3 = _card("P\n转移概率", 2.0, 1.8, YELL, WHITE, 28, CARD_FILL, "BOLD")
        row1 = VGroup(m1, m2, m3).arrange(RIGHT, buff=0.4)
        m4 = _card("R\n奖励函数", 2.0, 1.8, CYAN, WHITE, 28, CARD_FILL, "BOLD")
        m5 = _card("γ\n折扣因子", 2.0, 1.8, GREEN, WHITE, 28, CARD_FILL, "BOLD")
        row2 = VGroup(m4, m5).arrange(RIGHT, buff=0.4)
        note = t("在状态 s 做动作 a，转移到 s' 的概率", 28, WHITE)
        page1 = page_stack(big, row1, row2, note, buff=1.0)
        layout_page(page1)

        self.at_clip("S5-c01")
        self.play(type_in(head, run_time=1.1), type_in(big, run_time=0.9), run_time=1.1)
        self.at_clip("S5-c02")
        self.play_scroll_unroll_many(m1, m2, m3, run_time=1.3)  # 主视觉：三卡拉幕
        self.at_clip("S5-c05")
        self.play_scroll_unroll_many(m4, m5, run_time=1.2)
        self.at_clip("S5-c06")
        self.play(type_in(note, run_time=0.9))
        self.at_clip("S5-c07")

        # 页2：策略（c07-c09）
        head2 = _head("智能体怎么选动作？", 40)
        p1 = _card("策略 π(a|s)：给定状态，选动作的概率", 6.0, 2.6, YELL, WHITE, 32, CARD_FILL, "BOLD")
        p2 = _card("随机性不是缺点——探索需要它", 6.0, 2.4, GREEN, WHITE, 32, CARD_FILL, "BOLD")
        page2 = page_stack(p1, p2, buff=2.0)
        layout_page(page2)

        self.play(FadeOut(head), FadeOut(big), FadeOut(m1), FadeOut(m2), FadeOut(m3),
                  FadeOut(m4), FadeOut(m5), FadeOut(note),
                  type_in(head2, run_time=0.9), run_time=0.9)
        self.play_scroll_unroll(p1, run_time=1.2)  # 主视觉：拉幕
        self.at_clip("S5-c09")
        self.play_scroll_unroll(p2, run_time=1.2)
        self.emphasize(p2, run_time=0.6)  # 3/4
        self.at_clip("S5-c10")

        # 页3：轨迹 + 修 bug 例子（c10-c12）
        head3 = _head("一串状态，叫轨迹", 40)
        t1 = cnode("S₁", CYAN, radius=0.5, fs=22)
        t2 = cnode("S₂", CYAN, radius=0.5, fs=22)
        t3 = cnode("S₃", CYAN, radius=0.5, fs=22)
        td = cnode("…", MUTED, radius=0.5, fs=26)
        t30 = cnode("S₃₀", GREEN, radius=0.5, fs=20)
        trow = VGroup(t1, t2, t3, td, t30).arrange(RIGHT, buff=0.5)
        ta1 = Arrow(t1.get_right(), t2.get_left(), color=YELL, stroke_width=4, buff=0.1)
        ta2 = Arrow(t2.get_right(), t3.get_left(), color=YELL, stroke_width=4, buff=0.1)
        ta3 = Arrow(t3.get_right(), td.get_left(), color=YELL, stroke_width=4, buff=0.1)
        ta4 = Arrow(td.get_right(), t30.get_left(), color=YELL, stroke_width=4, buff=0.1)
        trowg = VGroup(trow, ta1, ta2, ta3, ta4)
        q1 = _card("状态：代码库 + 测试日志", 5.6, 1.6, CYAN, WHITE, 30, CARD_FILL, "BOLD")
        q2 = _card("动作：调哪个工具", 5.6, 1.6, GREEN, WHITE, 30, CARD_FILL, "BOLD")
        q3 = _card("奖励：测试全绿 +1", 5.6, 1.6, YELL, WHITE, 30, CARD_FILL, "BOLD")
        qrow = VGroup(q1, q2, q3).arrange(DOWN, buff=0.4)
        page3 = page_stack(trowg, qrow, buff=1.2)
        layout_page(page3)

        self.play(FadeOut(head2), FadeOut(p1), FadeOut(p2),
                  type_in(head3, run_time=0.9), run_time=0.9)
        self.play(FadeIn(t1), FadeIn(t2), FadeIn(t3), FadeIn(td), FadeIn(t30),
                  Create(ta1), Create(ta2), Create(ta3), Create(ta4), run_time=1.2)  # 主视觉：轨迹链
        self.at_clip("S5-c11")
        self.play_scroll_unroll_many(q1, q2, q3, run_time=1.4)
        self.at_clip("S5-c13")

        # 页4：悬念（c13）
        head4 = _head("可奖励只有最后才有，中间怎么知道哪一步走对了？", 36)
        page4 = page_auto(head4)
        self.play(FadeOut(head3), FadeOut(t1), FadeOut(t2), FadeOut(t3),
                  FadeOut(td), FadeOut(t30), FadeOut(ta1), FadeOut(ta2),
                  FadeOut(ta3), FadeOut(ta4), FadeOut(q1), FadeOut(q2), FadeOut(q3),
                  type_in(head4, run_time=1.0), run_time=1.0)
        self.wait(0.3)
        self.transition_out(head4, f, page4)
        self.pad_to_voice()


# ---------------- S6 回报与折扣 + 品牌尾卡 ----------------
class S6(_Base):
    def construct(self):
        self.bg()
        f = _footer(self)

        # 页1：回报公式（c01-c03）
        head = _head("折扣回报", 40)
        formula = MathTex(
            r"G_t = \sum_{k=t+1}^{T} \gamma^{\,k-t-1} R_k",
            tex_to_color_map={r"\gamma^{\,k-t-1}": YELL})
        formula.set_width(6.0)
        c1 = _card("目标不是眼前这一步，而是整条轨迹的回报", 6.4, 2.6, CYAN, WHITE, 32, CARD_FILL, "BOLD")
        note = t("离现在越远的奖励，折得越狠", 28, WHITE)
        page1 = page_stack(formula, c1, note, buff=1.7)
        layout_page(page1)

        self.at_clip("S6-c01")
        self.play(type_in(head, run_time=1.0))
        self.at_clip("S6-c02")
        self.play(FadeIn(formula), run_time=0.9)  # 主视觉：公式
        self.wait(0.1)
        self.play_scroll_unroll(c1, run_time=1.2)
        self.wait(0.1)
        self.play(type_in(note, run_time=0.9))
        self.at_clip("S6-c04")

        # 页2：3 步账（c04-c07）
        head2 = _head("算一笔账：3 步，0、0、+1，γ = 0.9", 28)
        r0 = _card("第 0 步\n0", 2.0, 2.6, MUTED, WHITE, 34, CARD_FILL, "BOLD")
        r1 = _card("第 1 步\n0", 2.0, 2.6, MUTED, WHITE, 34, CARD_FILL, "BOLD")
        r2 = _card("第 2 步\n+1", 2.0, 2.6, GREEN, WHITE, 34, CARD_FILL, "BOLD")
        rrow = VGroup(r0, r1, r2).arrange(RIGHT, buff=0.5)
        lab = t("记在第 0 步账上的回报", 32, WHITE, "BOLD")
        slot = dynamic_slot(2.6, 0.9)
        grow = stable_row(lab, slot, buff=0.4)
        big = t("长远账：把终局的功劳，折算回每一步", 32, YELL, "BOLD")
        page2 = page_stack(rrow, grow, big, buff=1.6)
        layout_page(page2)

        self.play(FadeOut(head), FadeOut(formula), FadeOut(c1), FadeOut(note),
                  type_in(head2, run_time=0.9), run_time=0.9)
        self.play_scroll_unroll_many(r0, r1, r2, run_time=1.3)  # 主视觉：三卡拉幕
        self.at_clip("S6-c06")
        n = self.counter_value(0, 0.81, decimals=2, size=64, color=YELL,
                               run_time=1.4, anchor=slot,
                               extra_anims=[type_in(lab, run_time=0.6)])
        self.at_clip("S6-c07")
        self.play(type_in(big, run_time=0.9))
        self.emphasize(big, run_time=0.6)  # 4/4
        self.at_clip("S6-c08")

        # 页3：γ 旋钮（c08-c10）
        head3 = _head("γ 是个很妙的旋钮", 40)
        g1 = _card("调小：只顾眼前", 5.6, 1.8, CYAN, WHITE, 34, CARD_FILL, "BOLD")
        g2 = _card("调大：愿意为远期忍耐", 5.6, 1.8, GREEN, WHITE, 34, CARD_FILL, "BOLD")
        lab3 = t("耐心差距", 32, WHITE, "BOLD")
        slot3 = dynamic_slot(2.6, 0.9)
        grow3 = stable_row(lab3, slot3, buff=0.4)
        note3 = t("0.9 和 0.99 看着差不多，耐心差了 10 倍", 26, WHITE)
        page3 = page_stack(g1, g2, grow3, note3, buff=1.0)
        layout_page(page3)

        self.play(FadeOut(head2), FadeOut(r0), FadeOut(r1), FadeOut(r2),
                  FadeOut(n), FadeOut(grow), FadeOut(big),
                  type_in(head3, run_time=0.9), run_time=0.9)
        self.play_scroll_unroll_many(g1, g2, run_time=1.3)  # 主视觉：两卡拉幕
        self.at_clip("S6-c10")
        n3 = self.counter_value(0, 10, suffix=" 倍", size=64, color=YELL,
                                run_time=1.2, anchor=slot3,
                                extra_anims=[type_in(lab3, run_time=0.6)])
        self.wait(0.1)
        self.play(type_in(note3, run_time=0.9))
        self.at_clip("S6-c11")

        # 页4：预告 + 互动 + 品牌尾卡（c11-c14，终幕驻屏）
        pre = t("下一篇：Bellman 方程——怎么算这笔账", 28, WHITE, "BOLD")
        q = t("你遇到过 AI「只看眼前」的翻车现场吗？", 32, WHITE, "BOLD")
        logo = ImageMobject(str(AVATAR))
        logo.scale_to_fit_width(2.8)
        follow = t("关注「数解AI」", 38, YELL, "BOLD")
        title = t("《马尔可夫决策过程：AI 怎么在不确定里做选择》", 28, WHITE, "BOLD")
        title.set_width(6.8)
        guide = t("查看公众号文章", 30, GREEN, "BOLD")
        page4 = page_stack(pre, q, logo, follow, title, guide, buff=0.5)
        layout_page(page4)

        self.play(FadeOut(head3), FadeOut(g1), FadeOut(g2), FadeOut(n3),
                  FadeOut(grow3), FadeOut(note3),
                  type_in(pre, run_time=0.9), run_time=0.9)
        self.at_clip("S6-c12")
        self.play(type_in(q, run_time=1.0))
        self.at_clip("S6-c13")
        self.play(FadeIn(logo, shift=DOWN * 0.05), type_in(follow, run_time=0.9), run_time=0.9)
        self.at_clip("S6-c14")
        self.play(type_in(title, run_time=1.0))
        self.wait(0.1)
        self.play(type_in(guide, run_time=0.8))
        self.wait(1.0)
        self.pad_to_voice()
