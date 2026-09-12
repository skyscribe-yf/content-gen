#!/usr/bin/env python3
"""《贝尔曼方程：为什么只看下一步就够了？》视频号 Manim 动画（竖屏 1080×1920）

6 个场景 S1-S6，与 storyboard.md 一一对应。
- 配音：MiniMax 精英男声（speech-2.8-turbo，speed 1.0 pitch +2）
- 时间轴：at_clip("S1-c01") 挂 tts/sentence-boundaries.json 的 clip 起点（先声音后动画门禁）
- 布局：整页规划（page_stack + layout_page / page_auto），上下留白各 ≤10%
- 动画降噪（2026-09-07 打磨轮 1）：emphasize 全片仅 5 次（S1/S2/S4/S5/S6 各 1 次核心爆点），
  v2 动效 0 处，每页 1 个主视觉动效；动作结束不跨句（预检 action_overrun=0）

用法（shipinhao 目录内执行）：
  MANIM_STRICT_TIMELINE=1 python3 -m manim render -ql --disable_caching scenes.py S1 S2 S3 S4 S5 S6
  MANIM_STRICT_TIMELINE=1 python3 -m manim render -qm --disable_caching scenes.py S1 S2 S3 S4 S5 S6
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
VOICE_DUR = {"S1": 22.27, "S2": 28.59, "S3": 30.72, "S4": 35.50, "S5": 37.03, "S6": 42.76}
TAIL = 2.5


def _footer(self) -> Text:
    f = t("数解AI · 强化学习原理", 20, MUTED).to_edge(DOWN, buff=1.15)
    self.add(f)
    return f


def _head(text: str, size: float = 38) -> Text:
    return t(text, size, YELL, "BOLD").to_edge(UP, buff=1.2)


# ---------------- S1 开场钩子：决策在现在，奖励在未来 ----------------
class S1(_Base):
    def construct(self):
        self.bg()
        f = _footer(self)

        # 页1：时间轴 3..30 步 + 第 3 步红标（c01-c03）
        head = _head("决策在现在，奖励在未来", 40)
        note_a12 = t("以 coding agent 修 bug 为例", 24, MUTED)
        n_segs = 7  # 浓缩显示步进
        segs = VGroup(*[Rectangle(width=0.72, height=1.8, color=CYAN,
                                  fill_color=CYAN, fill_opacity=0.35) for _ in range(n_segs)])
        segs.arrange(RIGHT, buff=0.22)
        segs[0].set_color(RED).set_fill(RED, opacity=0.35)  # 第 3 步标红
        lab3 = t("第 3 步", 22, RED, "BOLD").next_to(segs[0], DOWN, buff=0.3)
        lab30 = t("第 30 步", 22, MUTED, "BOLD").next_to(segs[-1], DOWN, buff=0.3)
        c1 = _card("第 3 步：做决定", 5.2, 1.7, CYAN, WHITE, 30, CARD_FILL, "BOLD")
        c2 = _card("后面 27 步：全是未来奖励", 5.2, 1.7, RED, WHITE, 30, CARD_FILL, "BOLD")
        page1 = page_stack(note_a12, segs, lab3, lab30, c1, c2, buff=1.0)
        layout_page(page1)

        self.at_clip("S1-c01")
        self.play_parallel(type_in(head, run_time=1.0), type_in(note_a12, run_time=0.6),
                           *[FadeIn(s, scale=0.6) for s in segs],
                           type_in(lab3, run_time=0.5), type_in(lab30, run_time=0.5),
                           run_time=1.1)  # 0 -> 1.1（c01 0-3.52）
        self.emphasize(segs[0], run_time=0.6)  # 1.1 -> 1.7（第 3 步，强调 1/5）
        self.wait(1.667)                        # 1.7 -> 3.52
        self.at_clip("S1-c02")
        self.play_scroll_unroll(c1, run_time=1.1)  # 3.52 -> 4.62（c02 3.52-5.86）
        self.wait(1.095)
        self.at_clip("S1-c03")
        self.play_scroll_unroll(c2, run_time=1.1)  # 5.86 -> 6.96（c03 5.86-7.72）
        self.wait(0.609)
        self.at_clip("S1-c04")

        # 页2：价值函数一口价（c04-c09）
        head2 = _head("那到底该看什么？", 40)
        big = t("看一个数", 62, YELL, "BOLD")
        d1 = _card("把从当前到终局的所有未来奖励", 5.8, 1.6, CYAN, WHITE, 32, CARD_FILL, "BOLD")
        d2 = _card("压成「当下值多少钱」", 5.8, 1.6, GREEN, WHITE, 32, CARD_FILL, "BOLD")
        d3 = _card("它叫价值函数", 5.8, 1.6, WHITE, WHITE, 32, CARD_FILL, "BOLD")
        d4 = _card("算它的记账法，叫贝尔曼方程", 5.8, 1.6, YELL, WHITE, 32, CARD_FILL, "BOLD")
        page2 = page_stack(big, d1, d2, d3, d4, buff=0.7)
        layout_page(page2)

        self.play(FadeOut(head), FadeOut(segs), FadeOut(lab3), FadeOut(lab30),
                  FadeOut(c1), FadeOut(c2), FadeOut(note_a12),
                  type_in(head2, run_time=0.9), run_time=0.9)  # 7.72 -> 8.62（c04 7.72-9.89）
        self.wait(1.121)
        self.at_clip("S1-c05")
        self.play(type_in(big, run_time=0.8))  # 9.89 -> 10.69（c05 9.89-10.89）
        self.wait(0.050)
        self.at_clip("S1-c06")
        self.play_scroll_unroll_many(d1, d2, run_time=1.3)  # 10.89 -> 12.19（c06 10.89-14.67 主视觉：两卡拉幕）
        self.wait(2.330)
        self.at_clip("S1-c07")
        self.play_scroll_unroll(d3, run_time=1.1)  # 14.67 -> 15.77（c07 14.67-16.46）
        self.wait(0.540)
        self.at_clip("S1-c08")
        self.play_scroll_unroll(d4, run_time=1.1)  # 16.46 -> 17.56（c08 16.46-17.95）
        self.at_clip("S1-c09")
        self.wait(0.5)                            # 17.95 -> 18.45（c09 17.95-22.27）
        self.transition_out(head2, big, d1, d2, d3, d4, f, page2)  # 18.45 -> 19.05
        self.pad_to_voice()


# ---------------- S2 路径爆炸：3^30 ----------------
class S2(_Base):
    def construct(self):
        self.bg()
        f = _footer(self)

        # 页1：概念图 + 追问（c01-c02）
        head = _head("展开每条未来，算一遍再平均？", 36)
        img = ImageMobject(str(IMG / "s2-tree-round.png"))
        img.scale_to_fit_width(5.6)
        note = t("组合爆炸：分支越来越多", 30, WHITE)
        note2 = t("每步 3 种可能，30 步后有多少条？", 30, WHITE)
        page1 = page_stack(img, note, note2, buff=0.9)
        layout_page(page1)

        self.at_clip("S2-c01")
        self.play_parallel(type_in(head, run_time=1.0), FadeIn(img, shift=DOWN * 0.05),
                           type_in(note, run_time=0.7), run_time=1.1)  # 0 -> 1.1（c01 0-3.86）
        self.wait(2.608)
        self.at_clip("S2-c02")
        self.play(type_in(note2, run_time=0.7))  # 3.86 -> 4.56（c02 3.86-5.89）
        self.wait(1.178)
        self.at_clip("S2-c03")

        # 页2：3^30 滚动爆点（c03-c05）
        head2 = _head("哪怕每步 3 种可能，30 步", 36)
        base = t("3", 80, YELL, "BOLD")
        exp = t("30", 52, YELL, "BOLD")
        exp.next_to(base, UR, buff=0.0)
        pow_g = VGroup(base, exp)
        eq = t("＝", 76, WHITE, "BOLD")
        slot = dynamic_slot(5.0, 1.5)
        label = t("万亿条路径", 48, WHITE, "BOLD")
        page2 = page_stack(pow_g, eq, slot, label, buff=1.1)
        layout_page(page2)

        self.play(FadeOut(head), FadeOut(img), FadeOut(note), FadeOut(note2),
                  type_in(head2, run_time=0.9), run_time=0.9)  # 5.89 -> 6.79（c03 5.89-7.01）
        self.wait(0.070)
        self.at_clip("S2-c04")
        self.play_parallel(type_in(pow_g, run_time=0.7), type_in(eq, run_time=0.4),
                           run_time=0.8)  # 7.01 -> 7.81（c04 7.01-11.04）
        self.wait(3.082)
        self.at_clip("S2-c05")
        n1 = self.counter_value(0, 205.9, decimals=1, size=72, color=YELL,
                                run_time=2.6, anchor=slot,
                                extra_anims=[type_in(label, run_time=0.8)])  # 11.04 -> 13.64（主视觉：数字滚动+标签）
        self.emphasize(n1, run_time=0.7)     # 13.64 -> 14.34（205.9 万亿，强调 2/5）
        self.wait(1.801)
        self.at_clip("S2-c06")

        # 页3：计算机扛不住 + 压缩原因（c06-c09）
        head3 = _head("计算机也扛不住", 40)
        c1 = _card("必须压缩：用每个状态的一个数", 5.8, 1.8, CYAN, WHITE, 32, CARD_FILL, "BOLD")
        c2 = _card("换掉指数多条未来路径", 5.8, 1.8, GREEN, WHITE, 32, CARD_FILL, "BOLD")
        c3 = _card("这个数，就是价值函数", 5.8, 1.8, YELL, WHITE, 32, CARD_FILL, "BOLD")
        page3 = page_stack(c1, c2, c3, buff=1.0)
        layout_page(page3)

        self.play(FadeOut(head2), FadeOut(pow_g), FadeOut(eq), FadeOut(n1), FadeOut(label),
                  type_in(head3, run_time=0.8), run_time=1.3)  # 16.29 -> 17.59（c06 16.29-19.03）
        self.wait(1.293)
        self.at_clip("S2-c07")
        self.play_scroll_unroll(c1, run_time=1.2)  # 19.03 -> 20.23（c07 19.03-22.87）
        self.wait(2.491)
        self.at_clip("S2-c08")
        self.play_scroll_unroll(c2, run_time=1.2)  # 22.87 -> 24.07（c08 22.87-24.98）
        self.wait(0.762)
        self.at_clip("S2-c09")
        self.play_scroll_unroll(c3, run_time=1.1)  # 24.98 -> 26.08（c09 24.98-26.94）
        self.wait(0.705)
        self.at_clip("S2-c10")

        # 页4：悬念
        head4 = _head("先立一条铁律，才能写公式", 38)
        page4 = page_auto(head4)
        self.play(FadeOut(head3), FadeOut(c1), FadeOut(c2), FadeOut(c3),
                  type_in(head4, run_time=0.9), run_time=0.9)  # 26.94 -> 27.84（c10 26.94-28.59）
        self.wait(0.4)
        self.transition_out(head4, f, page4)  # 28.24 -> 28.84
        self.pad_to_voice()


# ---------------- S3 符号 + V 的一口价 ----------------
class S3(_Base):
    def construct(self):
        self.bg()
        f = _footer(self)

        # 页1：大小写对照（c01-c03）
        head = _head("大写 vs 小写", 40)
        up = _card("大写 S, A, R, G\n骰子还没掷，随机变量", 5.6, 2.5, CYAN, WHITE, 32, CARD_FILL, "BOLD")
        down = _card("小写 s, a, r\n骰子已落地，确定的值", 5.6, 2.5, GREEN, WHITE, 32, CARD_FILL, "BOLD")
        note = t("记住这条，后面所有公式都看得懂", 28, YELL, "BOLD")
        page1 = page_stack(up, down, note, buff=1.0)
        layout_page(page1)

        self.at_clip("S3-c01")
        self.play_scroll_unroll(up, run_time=1.4)  # 0 -> 1.4（c01 0-4.62 主视觉：拉幕）
        self.wait(3.067)
        self.at_clip("S3-c02")
        self.play_scroll_unroll(down, run_time=1.4)  # 4.62 -> 6.02（c02 4.62-9.33）
        self.wait(3.167)
        self.at_clip("S3-c03")
        self.play(type_in(note, run_time=0.9))     # 9.33 -> 10.23（c03 9.33-12.53）
        self.wait(2.143)
        self.at_clip("S3-c04")

        # 页2：V 的定义（c04-c05）
        head2 = _head("价值函数：一口价", 40)
        formula = MathTex(r"V^\pi(s) = \mathbb{E}_\pi\left[G_t \mid S_t = s\right]",
                          tex_to_color_map={r"V^\pi(s)": YELL})
        formula.set_width(6.6)
        c1 = _card("站在 s，按策略 π 走下去", 5.8, 1.8, CYAN, WHITE, 32, CARD_FILL, "BOLD")
        c2 = _card("所有可能路径的回报，按概率平均", 5.8, 1.8, GREEN, WHITE, 32, CARD_FILL, "BOLD")
        page2 = page_stack(formula, c1, c2, buff=1.5)
        layout_page(page2)

        self.play(FadeOut(head), FadeOut(up), FadeOut(down), FadeOut(note),
                  type_in(head2, run_time=0.8), FadeIn(formula), run_time=1.1)  # 12.53 -> 13.63
        self.play_scroll_unroll(c1, run_time=1.2)  # 13.63 -> 14.83（c04 12.53-16.92 内）
        self.wait(1.942)
        self.at_clip("S3-c05")
        self.play_scroll_unroll(c2, run_time=1.2)  # 16.92 -> 18.12（c05 16.92-20.07）
        self.wait(1.805)
        self.at_clip("S3-c06")

        # 页3：买二手车（c06-c08）
        head3 = _head("就像买二手车", 40)
        big = t("一个数，算进所有「可能」", 40, YELL, "BOLD")
        g1 = _card("不等未来十年每张维修单都开出来", 5.8, 2.0, CYAN, WHITE, 32, CARD_FILL, "BOLD")
        g2 = _card("这一口价，把未来全算进去了", 5.8, 2.0, GREEN, WHITE, 32, CARD_FILL, "BOLD")
        page3 = page_stack(big, g1, g2, buff=1.4)
        layout_page(page3)

        self.play(FadeOut(head2), FadeOut(formula), FadeOut(c1), FadeOut(c2),
                  type_in(head3, run_time=0.8), run_time=1.3)  # 20.07 -> 21.37（c06 20.07-25.71）
        self.play_scroll_unroll(g1, run_time=1.3)  # 21.37 -> 22.67（c06 内）
        self.wait(2.891)
        self.at_clip("S3-c07")
        self.play(type_in(big, run_time=0.8))      # 25.71 -> 26.51（c07 25.71-26.92）
        self.wait(0.259)
        self.at_clip("S3-c08")
        self.play_scroll_unroll(g2, run_time=1.2)  # 26.92 -> 28.12（c08 26.92-30.72 主视觉：拉幕）
        self.wait(0.4)
        self.transition_out(head3, f, big, g1, g2, page3)  # 28.52 -> 29.12
        self.pad_to_voice()


# ---------------- S4 贝尔曼推导：只看下一步 ----------------
class S4(_Base):
    def construct(self):
        self.bg()
        f = _footer(self)

        # 页1：长账单 → 撕成两半（c01-c05）
        head = _head("把无限长的账单，折成两步", 38)
        bill = _card("R₁ + γR₂ + γ²R₃ + γ³R₄ + …", 6.0, 2.0, CYAN, WHITE, 36, CARD_FILL, "BOLD")
        today = _card("今天：R₁", 2.7, 3.0, YELL, WHITE, 40, CARD_FILL, "BOLD")
        tomorrow = _card("明天一整本 × γ", 3.6, 3.0, GREEN, WHITE, 34, CARD_FILL, "BOLD")
        split = VGroup(today, tomorrow).arrange(RIGHT, buff=1.2)
        page1 = page_stack(head, bill, split, buff=1.3)
        layout_page(page1)
        plus = t("＋", 60, WHITE, "BOLD")
        plus.move_to(split.get_center())  # 静态置于两卡之间，不进整页 box

        self.at_clip("S4-c01")
        self.play_scroll_unroll(bill, run_time=1.2)  # 0 -> 1.2（c01 0-3.92 主视觉：长账单拉幕）
        self.wait(4.316)
        self.at_clip("S4-c03")
        self.wait(2.856)                               # 5.67 -> 6.87（c03 5.67-8.67 内静态停留）
        self.at_clip("S4-c04")
        self.wait(2.602)                              # 8.67 -> 11.42（c04 8.67-11.42）
        self.at_clip("S4-c05")
        self.play(FadeOut(bill), run_time=0.3)       # 11.42 -> 11.72（撕掉长账单）
        self.wait(0.3)                               # 11.72 -> 12.02（账单清场）
        today_n, tomorrow_n = self.play_scroll_unroll_many(today, tomorrow, run_time=0.9)  # 12.02 -> 12.92（主视觉：撕两半）
        self.add(plus)                               # 12.92 起静态「＋」在中间
        self.wait(2.994)                              # 12.92 -> 16.07（c05 11.42-16.07 内）
        self.at_clip("S4-c06")

        # 页2：认出明天 = 明天的总账（c06-c07）
        head2 = _head("明天那本，其实是明天的总账", 38)
        f1 = _card("明天的总账 G₁₊₁", 5.4, 2.6, WHITE, WHITE, 36, CARD_FILL, "BOLD")
        ar = t("＝", 72, YELL, "BOLD")
        f2 = _card("站在明天路口的一口价 V(s′)", 5.4, 2.6, GREEN, WHITE, 36, CARD_FILL, "BOLD")
        page2 = page_stack(f1, ar, f2, buff=0.8)
        layout_page(page2)

        self.play(FadeOut(head), FadeOut(today), FadeOut(tomorrow), FadeOut(plus),
                  type_in(head2, run_time=0.9), run_time=1.0)  # 16.07 -> 17.07（c06 16.07-20.25）
        self.play_scroll_unroll(f1, run_time=1.2)  # 17.07 -> 18.27（c06 内）
        self.wait(1.830)
        self.at_clip("S4-c07")
        self.add(ar)                               # 等号装饰，静态出现（20.25）
        self.play_scroll_unroll(f2, run_time=1.2)  # 20.25 -> 21.45（c07 20.25-25.05 主视觉：拉幕）
        self.wait(3.447)
        self.at_clip("S4-c08")

        # 页3：标准形式 + 结论（c08-c11）
        head3 = _head("今天的价值 = 今天的奖励 + 折现的明天", 30)
        form = MathTex(r"V^\pi(s) = \sum_a\pi(a\mid s)\sum_{s'}P(s'\mid s,a)\left[r+\gamma V^\pi(s')\right]",
                       tex_to_color_map={r"V^\pi(s)": YELL})
        form.set_width(6.6)
        concl = _card("只看一步 = 透过明天，看完全程", 5.8, 3.6, GREEN, WHITE, 34, CARD_FILL, "BOLD")
        page3 = page_stack(form, concl, buff=3.0)
        layout_page(page3)

        self.play(FadeOut(head2), FadeOut(f1), FadeOut(ar), FadeOut(f2),
                  type_in(head3, run_time=0.9), FadeIn(form), run_time=1.3)  # 25.05 -> 26.35（主视觉：标准式）
        self.wait(0.185)
        self.at_clip("S4-c09")
        self.emphasize(form, run_time=0.7)         # 26.68 -> 27.38（贝尔曼方程，强调 3/5）
        self.wait(3.677)
        self.at_clip("S4-c10")
        self.play_scroll_unroll(concl, run_time=1.2)  # 31.21 -> 32.41（c10 31.21-33.47 内）
        self.wait(0.913)
        self.at_clip("S4-c11")
        self.wait(0.5)                             # 33.47 -> 33.97（c11 33.47-35.50）
        self.transition_out(head3, form, concl, f, page3)  # 33.97 -> 34.57
        self.pad_to_voice()


# ---------------- S5 三态链倒推，对账 0.81 ----------------
class S5(_Base):
    def construct(self):
        self.bg()
        f = _footer(self)

        # 页1：地铁三站（c01-c03）
        head = _head("三个状态一条地铁线", 40)
        img = ImageMobject(str(IMG / "s5-metro-round.png"))
        img.scale_to_fit_width(5.0)
        c1 = _card("A 上车，B 换乘，C 到站", 5.4, 1.4, CYAN, WHITE, 30, CARD_FILL, "BOLD")
        c2 = _card("只有到站 +1，折扣 γ = 0.9", 5.4, 1.4, GREEN, WHITE, 30, CARD_FILL, "BOLD")
        page1 = page_stack(img, c1, c2, buff=0.8)
        layout_page(page1)

        self.at_clip("S5-c01")
        self.play_parallel(type_in(head, run_time=1.0), FadeIn(img, shift=DOWN * 0.05),
                           run_time=1.0)  # 0 -> 1.0（c01 0-3.41）
        self.wait(2.263)
        self.at_clip("S5-c02")
        self.play_scroll_unroll(c1, run_time=1.1)  # 3.41 -> 4.51（c02 3.41-5.82）
        self.wait(1.159)
        self.at_clip("S5-c03")
        self.play_scroll_unroll(c2, run_time=1.1)  # 5.82 -> 6.92（c03 5.82-9.33）
        self.wait(2.262)
        self.at_clip("S5-c04")

        # 页2：笨办法 0.81（c04-c05）
        head2 = _head("笨办法：终点 +1 折两次回到 A", 32)
        lab = t("G(A)", 84, WHITE, "BOLD")
        slot = dynamic_slot(5.6, 3.6)
        grow = stable_row(lab, slot, buff=0.9)
        note = t("0.9 × 0.9 × 1 = 0.81", 64, WHITE, "BOLD")
        page2 = page_stack(grow, note, buff=2.8)
        layout_page(page2)

        self.play(FadeOut(head), FadeOut(img), FadeOut(c1), FadeOut(c2),
                  type_in(head2, run_time=0.9), run_time=0.9)  # 9.33 -> 10.23（c04 9.33-14.84）
        n1 = self.counter_value(0, 0.81, decimals=2, size=72, color=YELL,
                                run_time=1.2, anchor=slot,
                                extra_anims=[type_in(lab, run_time=0.6),
                                             type_in(note, run_time=0.8)])  # 10.23 -> 11.43（主视觉：0.81 滚动）
        self.emphasize(n1, run_time=0.6)         # 11.43 -> 12.03（对账 0.81，强调 4/5）
        self.wait(2.654)
        self.at_clip("S5-c05")
        self.wait(1.297)                          # 14.84 -> 16.29（c05 14.84-16.29 静态驻屏）
        self.at_clip("S5-c06")

        # 页3：倒推 C→B→A（c06-c09）
        head3 = _head("用方程倒推：从终点传信封", 36)
        a = _card("A\n0.81", 2.2, 4.6, YELL, WHITE, 34, CARD_FILL, "BOLD")
        b = _card("B\n0.9", 2.2, 4.6, CYAN, WHITE, 34, CARD_FILL, "BOLD")
        c = _card("C\n1", 2.2, 4.6, GREEN, WHITE, 34, CARD_FILL, "BOLD")
        chain = VGroup(a, b, c).arrange(RIGHT, buff=0.4)
        ar1 = Arrow(a.get_right(), b.get_left(), color=YELL, stroke_width=4, buff=0.15)
        ar2 = Arrow(b.get_right(), c.get_left(), color=YELL, stroke_width=4, buff=0.15)
        note3 = t("奖励在 C→终局当场到账，不打折", 40, RED, "BOLD")
        page3 = page_stack(chain, note3, buff=2.0)
        layout_page(page3)

        self.play(FadeOut(head2), FadeOut(n1), FadeOut(grow), FadeOut(note),
                  type_in(head3, run_time=0.9),
                  FadeIn(a), FadeIn(b), FadeIn(c), Create(ar1), Create(ar2),
                  run_time=1.3)  # 16.29 -> 17.59（c06 16.29-18.15 主视觉：三态链点亮）
        self.wait(0.412)
        self.at_clip("S5-c07")
        self.wait(4.087)                          # 18.15 -> 22.38（c07 18.15-22.38 三态链驻屏）
        self.at_clip("S5-c08")
        self.play(type_in(note3, run_time=0.9))  # 22.38 -> 23.28（c08 22.38-26.83）
        self.wait(3.392)
        self.at_clip("S5-c09")

        # 页4：倒推结果（c09-c10）
        head4 = _head("从终点往回传信封", 36)
        big = t("0.81", 150, YELL, "BOLD")
        note4a = t("C = 1 →  B = 0.9 →  A = 0.81", 56, WHITE, "BOLD")
        note4b = t("与笨办法一致，严丝合缝", 40, GREEN, "BOLD")
        page4 = page_stack(big, note4a, note4b, buff=2.8)
        layout_page(page4)

        self.play(FadeOut(head3), FadeOut(a), FadeOut(b), FadeOut(c),
                  FadeOut(ar1), FadeOut(ar2), FadeOut(note3),
                  type_in(head4, run_time=0.9), run_time=1.0)  # 26.83 -> 27.83（c09 26.83-31.97）
        self.play_parallel(type_in(big, run_time=0.9),
                           type_in(note4a, run_time=0.9), run_time=1.0)  # 27.83 -> 28.83（主视觉：终值+链路）
        self.wait(2.998)
        self.at_clip("S5-c10")
        self.play(type_in(note4b, run_time=0.9))  # 31.97 -> 32.87（c10 31.97-33.88）
        self.wait(0.860)
        self.at_clip("S5-c11")

        # 页5：结尾金句（c11）
        note4 = t("未来的长度，被 C 一口吞掉了", 32, WHITE, "BOLD")
        page5 = page_auto(note4)
        self.play(FadeOut(head4), FadeOut(big), FadeOut(note4a), FadeOut(note4b),
                  type_in(note4, run_time=0.9), run_time=0.9)  # 33.88 -> 34.78（c11 33.88-37.03 内）
        self.transition_out(note4, f, page5)     # 34.78 -> 35.38
        self.pad_to_voice()


# ---------------- S6 只看一步=全局 + 三家用法 + 预告 ----------------
class S6(_Base):
    def construct(self):
        self.bg()
        f = _footer(self)

        # 页1：不动点自洽（c01-c03）
        head = _head("不是循环，是自洽（不动点）", 38)
        c1 = _card("V(s′) 里压着 s′ 之后的全部未来", 5.8, 2.2, CYAN, WHITE, 34, CARD_FILL, "BOLD")
        c2 = _card("账无论怎么绕，最后都平在同一个点上", 5.8, 2.2, GREEN, WHITE, 34, CARD_FILL, "BOLD")
        note = t("看下一步 = 透过 S′ 看完全程", 32, YELL, "BOLD")
        page1 = page_stack(c1, c2, note, buff=1.2)
        layout_page(page1)

        self.at_clip("S6-c01")
        self.play_scroll_unroll(c1, run_time=1.3)  # 0 -> 1.3（c01 0-6.34 主视觉：拉幕）
        self.wait(4.886)
        self.at_clip("S6-c02")
        self.play(type_in(note, run_time=0.9))     # 6.34 -> 7.24（c02 6.34-9.51）
        self.wait(2.123)
        self.at_clip("S6-c03")
        self.play_scroll_unroll(c2, run_time=1.3)  # 9.51 -> 10.81（c03 9.51-13.72）
        self.emphasize(c2, run_time=0.7)           # 10.81 -> 11.51（不动点，强调 5/5）
        self.wait(2.064)
        self.at_clip("S6-c04")

        # 页2：三种走法（c04-c08）
        head2 = _head("真实大模型怎么用它？", 40)
        q1 = _card("Q-learning：真正在解方程", 5.8, 2.0, YELL, WHITE, 30, CARD_FILL, "BOLD")
        q2 = _card("PPO：只用一半（critic 打分）", 5.8, 2.0, CYAN, WHITE, 30, CARD_FILL, "BOLD")
        q3 = _card("GRPO：绕开（组内平均当基线）", 5.8, 2.0, GREEN, WHITE, 30, CARD_FILL, "BOLD")
        page2 = page_stack(q1, q2, q3, buff=0.8)
        layout_page(page2)

        self.play(FadeOut(head), FadeOut(c1), FadeOut(c2), FadeOut(note),
                  type_in(head2, run_time=0.9), run_time=0.9)  # 13.72 -> 14.62（c04 13.72-15.65）
        self.wait(0.874)
        self.at_clip("S6-c05")
        self.play_scroll_unroll(q1, run_time=1.2)  # 15.65 -> 16.85（c05 15.65-18.50）
        self.wait(1.498)
        self.at_clip("S6-c06")
        self.play_scroll_unroll(q2, run_time=1.2)  # 18.50 -> 19.70（c06 18.50-23.06）
        self.wait(3.212)
        self.at_clip("S6-c07")
        self.play_scroll_unroll(q3, run_time=1.2)  # 23.06 -> 24.26（c07 23.06-26.24）
        self.wait(1.829)
        self.at_clip("S6-c08")
        self.wait(4.520)                            # 26.24 -> 30.91（c08 26.24-30.91 三卡驻屏）
        self.at_clip("S6-c09")

        # 页3：预告 + 互动 + 品牌尾卡（c09-c13，终幕驻屏）
        pre = t("下一篇：TD 和 Q-learning", 28, WHITE, "BOLD")
        title = t("《贝尔曼方程：为什么只看下一步就够了？》", 28, WHITE, "BOLD")
        title.set_width(6.8)
        q = t("你希望 coding agent 估哪一笔账？", 30, WHITE, "BOLD")
        logo = ImageMobject(str(AVATAR))
        logo.scale_to_fit_width(2.8)
        follow = t("关注「数解AI」", 38, YELL, "BOLD")
        guide = t("查看公众号文章", 30, GREEN, "BOLD")
        page3 = page_stack(pre, title, q, logo, follow, guide, buff=0.5)
        layout_page(page3)

        self.play(FadeOut(head2), FadeOut(q1), FadeOut(q2), FadeOut(q3),
                  type_in(pre, run_time=1.0), run_time=1.0)  # 30.91 -> 31.91（c09 30.91-34.22）
        self.wait(2.167)
        self.at_clip("S6-c10")
        self.play(type_in(title, run_time=1.0))    # 34.22 -> 35.22（c10 34.22-37.64）
        self.wait(2.267)
        self.at_clip("S6-c11")
        self.play(type_in(q, run_time=1.0))        # 37.64 -> 38.64（c11 37.64-40.45）
        self.wait(1.655)
        self.at_clip("S6-c12")
        self.play(FadeIn(logo, shift=DOWN * 0.05), type_in(follow, run_time=0.9),
                  run_time=0.9)                    # 40.45 -> 41.34（c12 40.45-41.85）
        self.wait(0.353)
        self.at_clip("S6-c13")
        self.play(type_in(guide, run_time=0.7))    # 41.85 -> 42.55（c13 41.85-42.76）
        self.wait(0.21)
        self.pad_to_voice()
