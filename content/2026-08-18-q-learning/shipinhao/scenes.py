#!/usr/bin/env python3
"""《Q-learning是什么？没有转移表怎么解》视频号 Manim 动画（竖屏 1080×1920）

6 个场景 S1-S6，与 storyboard.md 一一对应。
- 配音：MiniMax 精英男声（speech-2.8-turbo，speed 1.0 pitch +2）
- 时间轴：at_clip("S1-c01") 挂 tts/sentence-boundaries.json 的 clip 起点（先声音后动画门禁）
- 布局：整页规划（page_stack + layout_page / page_auto），上下留白各 ≤10%
- 动画降噪：emphasize 全片 5 次（S1 P 表 / S2 max / S3 老师不用全对 / S4 0.67 / S5 max 0.40），
  v2 动效 0 处，每页 1 个主视觉动效；数字台词全部配 counter_value

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
VOICE_DUR = {"S1": 30.89, "S2": 34.05, "S3": 48.04, "S4": 55.38, "S5": 54.87, "S6": 42.33}
TAIL = 2.5


def _footer(self) -> Text:
    f = t("数解AI · 强化学习原理", 20, MUTED).to_edge(DOWN, buff=1.15)
    self.add(f)
    return f


def _head(text: str, size: float = 38) -> Text:
    return t(text, size, YELL, "BOLD").to_edge(UP, buff=1.2)


# ---------------- S1 开场钩子：方程里那张表，你没有 ----------------
class S1(_Base):
    def construct(self):
        self.bg()
        f = _footer(self)

        # 页1：贝尔曼方程 + P 表说明 + 红叉（c01-c03）
        head = _head("方程右边藏着一张表", 40)
        note_a12 = t("以 coding agent 修 bug 为例", 24, MUTED)
        form = MathTex(r"V^\pi(s)=\sum_a\pi(a\mid s)\sum_{s'}P(s'\mid s,a)\left[r+\gamma V^\pi(s')\right]",
                       tex_to_color_map={r"P(s'\mid s,a)": YELL})
        form.set_width(7.0)
        c0 = _card("P(s′|s,a)：从 s 做 a，跳到 s′ 的概率", 5.8, 2.8, CYAN, WHITE, 34, CARD_FILL, "BOLD")
        page1 = page_stack(note_a12, form, c0, buff=2.2)
        layout_page(page1)

        self.at_clip("S1-c01")
        self.play_parallel(type_in(head, run_time=1.0), type_in(note_a12, run_time=0.6),
                           FadeIn(form), run_time=1.1)  # 0 -> 1.1（c01 0-3.31）
        self.emphasize(form, run_time=0.7)               # 1.1 -> 1.8（P 表，强调 1/5）
        self.wait(1.33)
        self.at_clip("S1-c02")
        self.play_scroll_unroll(c0, run_time=1.2)        # 3.31 -> 4.51（c02 3.31-6.23）
        self.wait(1.54)
        self.at_clip("S1-c03")
        cross = self.play_red_cross(form, run_time=0.65)  # 6.23 -> 6.88（红叉盖 P 表，主视觉）
        self.wait(3.26)
        self.at_clip("S1-c04")

        # 页2：表不存在 + model 澄清（c04-c07）
        head2 = _head("这张表，根本不存在", 40)
        c1 = _card("改一行代码，测试变绿的概率", 5.8, 1.7, CYAN, WHITE, 32, CARD_FILL, "BOLD")
        c2 = _card("是 0.2 还是 0.8，没人知道", 5.8, 1.7, RED, WHITE, 32, CARD_FILL, "BOLD")
        c3 = _card("model = 转移表 + 奖励规则", 5.8, 1.7, GREEN, WHITE, 32, CARD_FILL, "BOLD")
        c4 = _card("不是大模型", 5.8, 1.7, YELL, WHITE, 32, CARD_FILL, "BOLD")
        page2 = page_stack(c1, c2, c3, c4, buff=0.7)
        layout_page(page2)

        self.play(FadeOut(head), FadeOut(form), FadeOut(cross), FadeOut(c0), FadeOut(note_a12),
                  type_in(head2, run_time=0.9), run_time=1.0)  # 10.32 -> 11.32（c04 10.32-14.80）
        self.play_scroll_unroll_many(c1, c2, run_time=1.3)     # 11.32 -> 12.62（c04 内）
        self.wait(2.0)
        self.at_clip("S1-c05")
        self.wait(0.89)
        self.at_clip("S1-c06")
        self.play_scroll_unroll_many(c3, c4, run_time=1.3)     # 15.87 -> 17.17（c06 15.87-20.65）
        self.wait(3.3)
        self.at_clip("S1-c07")
        self.wait(2.94)
        self.at_clip("S1-c08")

        # 页3：下棋有模拟器，修 bug 没有（c08-c09）
        head3 = _head("下棋有模拟器，修 bug 没有", 38)
        img = ImageMobject(str(IMG / "s1-empty-table-round.png"))
        img.scale_to_fit_width(4.8)
        c8 = _card("修 bug、写代码、对话：没有模拟器", 5.8, 1.6, RED, WHITE, 32, CARD_FILL, "BOLD")
        note3 = t("不是铺 Q 表，是看懂表背后的那一步", 30, WHITE, "BOLD")
        page3 = page_stack(img, c8, note3, buff=0.9)
        layout_page(page3)

        self.play(FadeOut(head2), FadeOut(c1), FadeOut(c2), FadeOut(c3), FadeOut(c4),
                  type_in(head3, run_time=0.9), FadeIn(img, shift=DOWN * 0.05),
                  run_time=1.1)                                # 23.77 -> 24.87（c08 23.77-26.88）
        self.play_scroll_unroll(c8, run_time=1.2)              # 24.87 -> 26.07（c08 内）
        self.wait(0.63)
        self.at_clip("S1-c09")
        self.play(type_in(note3, run_time=0.8))                # 26.88 -> 27.68（c09 26.88-30.89）
        self.wait(2.03)
        self.transition_out(head3, img, c8, note3, f, page3)   # 29.89 -> 30.49
        self.pad_to_voice()


# ---------------- S2 有表会怎么做 + 认符号 ----------------
class S2(_Base):
    def construct(self):
        self.bg()
        f = _footer(self)

        # 页1：有表 vs 没表（c01-c08）
        head = _head("有表，解方程；没表，走一步看一步", 34)
        img = ImageMobject(str(IMG / "s2-chess-bug-round.png"))
        img.scale_to_fit_width(4.0)
        c1 = _card("有 P：反复套最优方程，直到账做平", 5.8, 1.5, CYAN, WHITE, 30, CARD_FILL, "BOLD")
        c2 = _card("价值迭代", 5.8, 1.5, GREEN, WHITE, 30, CARD_FILL, "BOLD")
        c3 = _card("没表：走一步、看一眼，拿一次当样本", 5.8, 1.5, RED, WHITE, 30, CARD_FILL, "BOLD")
        page1 = page_stack(img, c1, c2, c3, buff=0.55)
        layout_page(page1)

        self.at_clip("S2-c01")
        self.play_parallel(type_in(head, run_time=1.0), FadeIn(img, shift=DOWN * 0.05),
                           run_time=1.0)                       # 0 -> 1.0（c01 0-1.45）
        self.wait(0.27)
        self.at_clip("S2-c02")
        self.play_scroll_unroll(c1, run_time=1.2)              # 1.45 -> 2.65（c02 1.45-5.17）
        self.wait(2.34)
        self.at_clip("S2-c03")
        self.wait(4.16)
        self.at_clip("S2-c04")
        self.play_scroll_unroll(c2, run_time=1.1)              # 9.51 -> 10.61（c04 9.51-11.36）
        self.wait(0.57)
        self.at_clip("S2-c05")
        self.wait(3.72)
        self.at_clip("S2-c06")
        self.play_scroll_unroll(c3, run_time=1.2)              # 15.26 -> 16.46（c06 15.26-17.20）
        self.wait(0.56)
        self.at_clip("S2-c07")
        self.wait(3.08)
        self.at_clip("S2-c08")
        self.wait(3.86)
        self.at_clip("S2-c09")

        # 页2：三个符号（c09-c11）
        head2 = _head("动手前，认两个符号", 40)
        d1 = _card("δ delta\n旧账和新情报的差", 5.6, 2.6, CYAN, WHITE, 34, CARD_FILL, "BOLD")
        d2 = _card("Q(s,a)\n把动作说死，值多少", 5.6, 2.6, GREEN, WHITE, 34, CARD_FILL, "BOLD")
        d3 = _card("max\n它才是主角", 5.6, 2.6, YELL, WHITE, 34, CARD_FILL, "BOLD")
        page2 = page_stack(d1, d2, d3, buff=0.8)
        layout_page(page2)

        self.play(FadeOut(head), FadeOut(img), FadeOut(c1), FadeOut(c2), FadeOut(c3),
                  type_in(head2, run_time=0.9), run_time=1.0)  # 24.50 -> 25.50（c09 24.50-29.10）
        self.play_scroll_unroll(d1, run_time=1.2)              # 25.50 -> 26.70（c09 内）
        self.wait(2.22)
        self.at_clip("S2-c10")
        self.play_scroll_unroll(d2, run_time=1.2)              # 29.10 -> 30.30（c10 29.10-31.21）
        self.wait(0.73)
        self.at_clip("S2-c11")
        self.play_scroll_unroll(d3, run_time=1.2)              # 31.21 -> 32.41（c11 31.21-34.05 主视觉：max 卡）
        self.emphasize(d3, run_time=0.7)                       # 32.41 -> 33.11（max 主角，强调 2/5）
        self.wait(0.26)
        self.transition_out(head2, d1, d2, d3, f, page2)       # 33.55 -> 34.15
        self.pad_to_voice()


# ---------------- S3 TD(0)：用下一步的估值当老师 ----------------
class S3(_Base):
    def construct(self):
        self.bg()
        f = _footer(self)

        # 页1：一次真实转移（c01-c03）
        head = _head("没有 P，只有一次真实转移", 38)
        n_s = cnode("s", CYAN, radius=0.55, fs=26)
        n_a = cnode("a", GREEN, radius=0.55, fs=26)
        n_r = cnode("r", YELL, radius=0.55, fs=26)
        n_sp = cnode("s′", CYAN, radius=0.55, fs=26)
        chain = VGroup(n_s, n_a, n_r, n_sp).arrange(RIGHT, buff=0.55)
        ar1 = Arrow(n_s.get_right(), n_a.get_left(), color=WHITE, stroke_width=4, buff=0.15)
        ar2 = Arrow(n_a.get_right(), n_r.get_left(), color=WHITE, stroke_width=4, buff=0.15)
        ar3 = Arrow(n_r.get_right(), n_sp.get_left(), color=WHITE, stroke_width=4, buff=0.15)
        c1 = _card("在 s 做 a，拿奖励 r，走到 s′", 5.8, 2.0, CYAN, WHITE, 32, CARD_FILL, "BOLD")
        c2 = _card("那就别平均了，用这一次替换求和", 5.8, 2.0, GREEN, WHITE, 32, CARD_FILL, "BOLD")
        page1 = page_stack(chain, c1, c2, buff=1.2)
        layout_page(page1)

        self.at_clip("S3-c01")
        self.play_parallel(type_in(head, run_time=1.0),
                           FadeIn(n_s), FadeIn(n_a), FadeIn(n_r), FadeIn(n_sp),
                           Create(ar1), Create(ar2), Create(ar3),
                           run_time=1.1)                       # 0 -> 1.1（c01 0-3.50）
        self.play_scroll_unroll(c1, run_time=1.2)              # 1.1 -> 2.3（c01 内）
        self.wait(1.02)
        self.at_clip("S3-c02")
        self.wait(1.77)
        self.at_clip("S3-c03")
        self.play_scroll_unroll(c2, run_time=1.2)              # 5.45 -> 6.65（c03 5.45-8.56）
        self.wait(1.73)
        self.at_clip("S3-c04")

        # 页2：新估价 = 奖励 + 折扣估值 + δ（c04-c06）
        head2 = _head("新估价：两样相加", 40)
        r1 = _card("刚拿到的奖励 R", 2.0, 3.4, GREEN, WHITE, 34, CARD_FILL, "BOLD")
        r2 = _card("下一步估值 V(s′)\n打个折扣 γ", 2.0, 3.4, CYAN, WHITE, 34, CARD_FILL, "BOLD")
        plus = t("＋", 48, WHITE, "BOLD")
        eq = t("＝", 48, WHITE, "BOLD")
        r3 = _card("新估价", 2.0, 3.4, YELL, WHITE, 34, CARD_FILL, "BOLD")
        row = VGroup(r1, plus, r2, eq, r3).arrange(RIGHT, buff=0.25)
        c3 = _card("δ = 新估价 − 旧账", 5.8, 2.7, RED, WHITE, 34, CARD_FILL, "BOLD")
        page2 = page_stack(row, c3, buff=1.5)
        layout_page(page2)

        self.play(FadeOut(head), FadeOut(n_s), FadeOut(n_a), FadeOut(n_r), FadeOut(n_sp),
                  FadeOut(ar1), FadeOut(ar2), FadeOut(ar3), FadeOut(c1), FadeOut(c2),
                  type_in(head2, run_time=0.9), run_time=1.0)  # 8.56 -> 9.56（c04 8.56-13.03）
        self.play_scroll_unroll_many(r1, r2, run_time=1.3)     # 9.56 -> 10.86（c04 内 主视觉：两卡）
        self.add(plus, eq)                                     # 10.86 静态符号
        self.wait(1.99)
        self.at_clip("S3-c05")
        self.wait(0.79)
        self.at_clip("S3-c06")
        self.play_scroll_unroll_many(r3, c3, run_time=1.3)     # 14.00 -> 15.30（c06 14.00-17.02）
        self.wait(1.54)
        self.at_clip("S3-c07")

        # 页3：更新式 + TD(0)（c07-c09）
        head3 = _head("账没做平，就改一笔", 40)
        d_form = MathTex(r"\delta_t = R_{t+1} + \gamma V(S_{t+1}) - V(S_t)",
                         tex_to_color_map={r"\delta_t": YELL})
        d_form.set_width(6.6)
        up_form = MathTex(r"V(S_t) \leftarrow V(S_t) + \alpha\,\delta_t",
                          tex_to_color_map={r"\alpha": GREEN, r"\delta_t": YELL})
        up_form.set_width(6.2)
        note3 = t("α = 学习率：这一笔差额，你信多少", 28, WHITE, "BOLD")
        c9 = _card("TD(0)：时序差分，只看一步", 5.8, 2.2, YELL, WHITE, 34, CARD_FILL, "BOLD")
        page3 = page_stack(d_form, up_form, note3, c9, buff=1.4)
        layout_page(page3)

        self.play(FadeOut(head2), FadeOut(r1), FadeOut(r2), FadeOut(r3),
                  FadeOut(plus), FadeOut(eq), FadeOut(c3),
                  type_in(head3, run_time=0.9), FadeIn(d_form), run_time=1.2)  # 17.02 -> 18.22（c07 17.02-20.52）
        self.wait(2.12)
        self.at_clip("S3-c08")
        self.play(FadeIn(up_form), run_time=1.0)               # 20.52 -> 21.52（c08 20.52-22.92）
        self.wait(1.22)
        self.at_clip("S3-c09")
        self.play_parallel(type_in(note3, run_time=0.8), run_time=0.8)  # 22.92 -> 23.72（c09 22.92-26.63）
        self.play_scroll_unroll(c9, run_time=1.2)              # 23.72 -> 24.92（c09 内）
        self.wait(1.53)
        self.at_clip("S3-c10")

        # 页4：错的老师（c10-c15）
        head4 = _head("错的老师，凭什么能教？", 40)
        img = ImageMobject(str(IMG / "s3-wrong-teacher-round.png"))
        img.scale_to_fit_width(3.6)
        c4 = _card("老师不用全对，只要多看见一步真实奖励", 5.8, 1.8, GREEN, WHITE, 32, CARD_FILL, "BOLD")
        c5 = _card("被样本推着，一步步逼近", 5.8, 1.8, YELL, WHITE, 32, CARD_FILL, "BOLD")
        page4 = page_stack(img, c4, c5, buff=0.8)
        layout_page(page4)

        self.play(FadeOut(head3), FadeOut(d_form), FadeOut(up_form), FadeOut(note3), FadeOut(c9),
                  type_in(head4, run_time=0.9), FadeIn(img, shift=DOWN * 0.05),
                  run_time=1.1)                                # 26.63 -> 27.73（c10 26.63-31.22）
        self.wait(3.31)
        self.at_clip("S3-c11")
        self.wait(1.55)
        self.at_clip("S3-c12")
        self.wait(2.54)
        self.at_clip("S3-c13")
        self.play_scroll_unroll(c4, run_time=1.3)              # 35.67 -> 36.97（c13 35.67-41.47 主视觉：拉幕）
        self.emphasize(c4, run_time=0.7)                       # 36.97 -> 37.67（老师不用全对，强调 3/5）
        self.wait(3.62)
        self.at_clip("S3-c14")
        self.wait(1.53)
        self.at_clip("S3-c15")
        self.play_scroll_unroll(c5, run_time=1.2)              # 43.18 -> 44.38（c15 43.18-48.04）
        self.wait(3.48)
        self.transition_out(head4, img, c4, c5, f, page4)      # 48.04 -> 48.64
        self.pad_to_voice()


# ---------------- S4 手算两笔：0.50 → 0.34 → 0.67 ----------------
class S4(_Base):
    def construct(self):
        self.bg()
        f = _footer(self)

        # 页1：状态与参数（c01-c07）
        head = _head("手算：跑测试，红或绿", 40)
        s0 = _card("s₀ 刚改完一处\n瞎估 0.50", 2.3, 3.6, YELL, WHITE, 34, CARD_FILL, "BOLD")
        red = _card("红：还要改\n估 0.20", 2.3, 3.6, RED, WHITE, 34, CARD_FILL, "BOLD")
        green = _card("绿：终局\n当场 +1", 2.3, 3.6, GREEN, WHITE, 34, CARD_FILL, "BOLD")
        row = VGroup(s0, red, green).arrange(RIGHT, buff=0.4)
        p1 = _card("γ = 0.9　α = 0.5", 5.4, 1.8, CYAN, WHITE, 32, CARD_FILL, "BOLD")
        page1 = page_stack(row, p1, buff=1.6)
        layout_page(page1)

        self.at_clip("S4-c01")
        self.play_parallel(type_in(head, run_time=1.0), run_time=1.0)  # 0 -> 1.0（c01 0-1.83）
        self.wait(0.65)
        self.at_clip("S4-c02")
        self.play_scroll_unroll(s0, run_time=1.2)              # 1.83 -> 3.03（c02 1.83-5.49）
        self.wait(2.28)
        self.at_clip("S4-c03")
        self.play_scroll_unroll_many(red, green, run_time=1.3)  # 5.49 -> 6.79（c03 5.49-8.46）
        self.wait(1.49)
        self.at_clip("S4-c04")
        self.wait(2.1)
        self.at_clip("S4-c05")
        self.wait(2.34)
        self.at_clip("S4-c06")
        self.wait(1.85)
        self.at_clip("S4-c07")
        self.play_scroll_unroll(p1, run_time=1.2)              # 15.29 -> 16.49（c07 15.29-18.38）
        self.wait(1.71)
        self.at_clip("S4-c08")

        # 页2：第一次红 0.50→0.34（c08-c12）
        head2 = _head("第一次，测试红了", 40)
        lab = t("V(s₀)", 72, WHITE, "BOLD")
        slot = dynamic_slot(4.4, 3.2)
        grow = stable_row(lab, slot, buff=0.8)
        d1 = _card("δ = 0 + 0.9×0.20 − 0.50 = −0.32", 5.8, 2.0, RED, WHITE, 32, CARD_FILL, "BOLD")
        d2 = _card("改一半：0.50 → 0.34", 5.8, 2.0, YELL, WHITE, 32, CARD_FILL, "BOLD")
        page2 = page_stack(grow, d1, d2, buff=0.8)
        layout_page(page2)

        self.play(FadeOut(head), FadeOut(s0), FadeOut(red), FadeOut(green), FadeOut(p1),
                  type_in(head2, run_time=0.9), run_time=1.0)  # 18.38 -> 19.38（c08 18.38-20.14）
        self.wait(0.58)
        self.at_clip("S4-c09")
        self.play_scroll_unroll(d1, run_time=1.2)              # 20.14 -> 21.34（c09 20.14-24.72 主视觉：δ 卡）
        self.wait(3.2)
        self.at_clip("S4-c10")
        self.wait(2.24)
        self.at_clip("S4-c11")
        self.wait(1.75)
        self.at_clip("S4-c12")
        n1 = self.counter_value(0.50, 0.34, decimals=2, size=80, color=YELL,
                                run_time=1.4, anchor=slot,
                                extra_anims=[type_in(lab, run_time=0.6),
                                             type_in(d2, run_time=0.8)])  # 29.07 -> 30.47（主视觉：0.50→0.34 滚动）
        self.wait(0.59)
        self.at_clip("S4-c13")

        # 页3：第二次绿 0.34→0.67（c13-c16）
        head3 = _head("第二次，测试绿了", 40)
        lab2 = t("V(s₀)", 72, WHITE, "BOLD")
        slot2 = dynamic_slot(4.4, 3.2)
        grow2 = stable_row(lab2, slot2, buff=0.8)
        d3 = _card("δ = 1 + 0.9×0 − 0.34 = 0.66", 5.8, 2.0, GREEN, WHITE, 32, CARD_FILL, "BOLD")
        d4 = _card("改一半：0.34 → 0.67", 5.8, 2.0, YELL, WHITE, 32, CARD_FILL, "BOLD")
        page3 = page_stack(grow2, d3, d4, buff=0.8)
        layout_page(page3)

        self.play(FadeOut(head2), FadeOut(n1), FadeOut(grow), FadeOut(d1), FadeOut(d2),
                  type_in(head3, run_time=0.9), run_time=1.0)  # 31.24 -> 32.24（c13 31.24-32.93）
        self.wait(0.51)
        self.at_clip("S4-c14")
        self.play_scroll_unroll(d3, run_time=1.2)              # 32.93 -> 34.13（c14 32.93-35.30）
        self.wait(0.99)
        self.at_clip("S4-c15")
        self.wait(2.93)
        self.at_clip("S4-c16")
        n2 = self.counter_value(0.34, 0.67, decimals=2, size=80, color=YELL,
                                run_time=1.2, anchor=slot2,
                                extra_anims=[type_in(lab2, run_time=0.6),
                                             type_in(d4, run_time=0.8)])  # 38.41 -> 39.61（主视觉：0.34→0.67 滚动）
        self.emphasize(n2, run_time=0.6)                       # 39.61 -> 40.21（0.67，强调 4/5）
        self.wait(0.05)
        self.at_clip("S4-c17")

        # 页4：结论（c17-c20）
        head4 = _head("没有正确答案，也没用到 P", 38)
        c5 = _card("红绿一半一半 → 长期平均 ≈ 0.59", 5.8, 2.2, CYAN, WHITE, 32, CARD_FILL, "BOLD")
        c6 = _card("两步走到 0.67，还在晃，方向对", 5.8, 2.2, GREEN, WHITE, 32, CARD_FILL, "BOLD")
        big = t("解不是代入，是走、看、改", 44, YELL, "BOLD")
        page4 = page_stack(c5, c6, big, buff=1.4)
        layout_page(page4)

        self.play(FadeOut(head3), FadeOut(n2), FadeOut(grow2), FadeOut(d3), FadeOut(d4),
                  type_in(head4, run_time=0.9), run_time=1.0)  # 40.53 -> 41.53（c17 40.53-44.57）
        self.play_scroll_unroll(c5, run_time=1.2)              # 41.53 -> 42.73（c17 内）
        self.wait(1.66)
        self.at_clip("S4-c18")
        self.play_scroll_unroll(c6, run_time=1.2)              # 44.57 -> 45.77（c18 44.57-48.40）
        self.wait(2.45)
        self.at_clip("S4-c19")
        self.wait(3.86)
        self.at_clip("S4-c20")
        self.play(type_in(big, run_time=0.9))                  # 52.44 -> 53.34（c20 52.44-55.38 主视觉：金句）
        self.wait(1.86)
        self.transition_out(head4, c5, c6, big, f, page4)      # 55.38 -> 55.98
        self.pad_to_voice()


# ---------------- S5 Q-learning：只多一个 max ----------------
class S5(_Base):
    def construct(self):
        self.bg()
        f = _footer(self)

        # 页1：Q 更新公式（c01-c04）
        head = _head("记账对象换成 Q，只多一个 max", 34)
        c0 = _card("Q(s,a)：站在 s，把动作 a 说死", 5.8, 2.4, CYAN, WHITE, 32, CARD_FILL, "BOLD")
        q_form = MathTex(r"Q(s,a) \leftarrow Q(s,a) + \alpha\left[R + \gamma \max_{a'} Q(s',a') - Q(s,a)\right]",
                         tex_to_color_map={r"\max_{a'}": YELL})
        q_form.set_width(6.8)
        c1 = _card("它解的是：每步都挑最好的动作，值多少", 5.8, 2.2, GREEN, WHITE, 32, CARD_FILL, "BOLD")
        page1 = page_stack(c0, q_form, c1, buff=1.4)
        layout_page(page1)

        self.at_clip("S5-c01")
        self.play_parallel(type_in(head, run_time=1.0), FadeIn(q_form), run_time=1.1)  # 0 -> 1.1（c01 0-3.37）
        self.play_scroll_unroll(c0, run_time=1.2)              # 1.1 -> 2.3（c01 内）
        self.wait(0.89)
        self.at_clip("S5-c02")
        self.wait(1.84)
        self.at_clip("S5-c03")
        self.wait(2.34)                                        # 5.39 -> 7.73（c03 5.39-7.91，max 已黄色高亮，不再 emphasize）
        self.at_clip("S5-c04")
        self.play_scroll_unroll(c1, run_time=1.2)             # 7.91 -> 9.11（c04 7.91-10.70）
        self.wait(1.41)
        self.at_clip("S5-c05")

        # 页2：四张估值卡（c05-c06）
        head2 = _head("先估四笔账", 40)
        a1 = _card("跑测试 0.60", 1.7, 4.2, CYAN, WHITE, 34, CARD_FILL, "BOLD")
        a2 = _card("再改一处 0.30", 1.7, 4.2, CYAN, WHITE, 34, CARD_FILL, "BOLD")
        a3 = _card("到红·重写 0.40", 1.7, 4.2, GREEN, WHITE, 34, CARD_FILL, "BOLD")
        a4 = _card("到红·回退 0.10", 1.7, 4.2, MUTED, WHITE, 34, CARD_FILL, "BOLD")
        row = VGroup(a1, a2, a3, a4).arrange(RIGHT, buff=0.3)
        note2 = t("Q(s,a)：站在 s，把动作 a 说死，值多少", 30, WHITE, "BOLD")
        page2 = page_stack(row, note2, buff=2.6)
        layout_page(page2)

        self.play(FadeOut(head), FadeOut(c0), FadeOut(q_form), FadeOut(c1),
                  type_in(head2, run_time=0.9), run_time=1.0)  # 10.70 -> 11.70（c05 10.70-14.98）
        self.play_scroll_unroll_many(a1, a2, run_time=1.3)     # 11.70 -> 13.00（c05 内）
        self.wait(0.3)                                         # 13.00 -> 13.30
        self.play(type_in(note2, run_time=0.8))                # 13.30 -> 14.10（c05 内：Q 定义说明，QA A10）
        self.wait(0.7)                                         # 14.10 -> 14.80
        self.at_clip("S5-c06")
        self.play_scroll_unroll_many(a3, a4, run_time=1.3)     # 14.98 -> 16.28（c06 14.98-18.79）
        self.wait(2.33)                                        # 16.28 -> 18.61
        self.at_clip("S5-c07")

        # 页3：第一次红 0.60→0.48（c07-c11）
        head3 = _head("第一次，红了：max(0.40, 0.10) = 0.40", 32)
        lab = t("Q(s₀,跑测试)", 48, WHITE, "BOLD")
        slot = dynamic_slot(3.4, 2.8)
        grow = stable_row(lab, slot, buff=0.7)
        d1 = _card("δ = 0 + 0.9×0.40 − 0.60 = −0.24", 5.8, 2.0, RED, WHITE, 32, CARD_FILL, "BOLD")
        d2 = _card("改一半：0.60 → 0.48", 5.8, 2.0, YELL, WHITE, 32, CARD_FILL, "BOLD")
        page3 = page_stack(grow, d1, d2, buff=0.8)
        layout_page(page3)

        self.play(FadeOut(head2), FadeOut(note2), FadeOut(a1), FadeOut(a2), FadeOut(a3), FadeOut(a4),
                  type_in(head3, run_time=0.9), run_time=1.0)  # 18.79 -> 19.79（c07 18.79-20.45；note2 此前漏删致霸屏至 S5 尾，2026-09-11 修复）
        self.wait(0.48)
        self.at_clip("S5-c08")
        self.play_scroll_unroll(d1, run_time=1.2)              # 20.45 -> 21.65（c08 20.45-23.98 主视觉：δ 卡）
        self.emphasize(d1, run_time=0.7)                       # 21.65 -> 22.35（max 0.40，强调 5/5）
        self.wait(1.45)
        self.at_clip("S5-c09")
        self.wait(2.87)
        self.at_clip("S5-c10")
        self.wait(2.02)
        self.at_clip("S5-c11")
        n1 = self.counter_value(0.60, 0.48, decimals=2, size=72, color=YELL,
                                run_time=1.4, anchor=slot,
                                extra_anims=[type_in(lab, run_time=0.6),
                                             type_in(d2, run_time=0.8)])  # 29.23 -> 30.63（主视觉：0.60→0.48 滚动）
        self.wait(0.11)
        self.at_clip("S5-c12")

        # 页4：第二次绿 0.48→0.74（c12-c14）
        head4 = _head("第二次，绿了", 40)
        lab2 = t("Q(s₀,跑测试)", 48, WHITE, "BOLD")
        slot2 = dynamic_slot(3.4, 2.8)
        grow2 = stable_row(lab2, slot2, buff=0.7)
        d3 = _card("δ = 1 + 0 − 0.48 = 0.52", 5.8, 2.0, GREEN, WHITE, 32, CARD_FILL, "BOLD")
        d4 = _card("改一半：0.48 → 0.74", 5.8, 2.0, YELL, WHITE, 32, CARD_FILL, "BOLD")
        page4 = page_stack(grow2, d3, d4, buff=0.8)
        layout_page(page4)

        self.play(FadeOut(head3), FadeOut(n1), FadeOut(grow), FadeOut(d1), FadeOut(d2),
                  type_in(head4, run_time=0.9), run_time=1.0)  # 30.92 -> 31.92（c12 30.92-32.24）
        self.wait(0.14)
        self.at_clip("S5-c13")
        self.play_scroll_unroll(d3, run_time=1.2)              # 32.24 -> 33.44（c13 32.24-33.55）
        self.wait(0.05)
        self.at_clip("S5-c14")
        n2 = self.counter_value(0.48, 0.74, decimals=2, size=72, color=YELL,
                                run_time=1.4, anchor=slot2,
                                extra_anims=[type_in(lab2, run_time=0.6),
                                             type_in(d4, run_time=0.8)])  # 33.55 -> 34.95（主视觉：0.48→0.74 滚动）
        self.wait(2.0)
        self.at_clip("S5-c15")

        # 页5：TD vs Q 对比 + SARSA（c15-c19）
        head5 = _head("差别在红那一步", 40)
        img = ImageMobject(str(IMG / "s5-max-choice-round.png"))
        img.scale_to_fit_width(3.4)
        t1 = _card("TD 用 V(红) = 0.20", 2.7, 2.8, CYAN, WHITE, 34, CARD_FILL, "BOLD")
        t2 = _card("Q 用 max = 0.40", 2.7, 2.8, YELL, WHITE, 34, CARD_FILL, "BOLD")
        vs = t("VS", 44, WHITE, "BOLD")
        row2 = VGroup(t1, vs, t2).arrange(RIGHT, buff=0.4)
        sarsa = _card("max 换成实际动作 → SARSA（跟正在用的策略）", 5.8, 1.8, MUTED, WHITE, 30, CARD_FILL, "BOLD")
        page5 = page_stack(img, row2, sarsa, buff=0.8)
        layout_page(page5)

        self.play(FadeOut(head4), FadeOut(n2), FadeOut(grow2), FadeOut(d3), FadeOut(d4),
                  type_in(head5, run_time=0.9), FadeIn(img, shift=DOWN * 0.05),
                  run_time=1.0)                                # 37.13 -> 38.13（c15 37.13-40.33）
        self.play_scroll_unroll(t1, run_time=1.2)              # 38.13 -> 39.33（c15 内）
        self.wait(0.82)
        self.at_clip("S5-c16")
        self.play_scroll_unroll(t2, run_time=1.2)              # 40.33 -> 41.53（c16 40.33-44.75 主视觉：对比卡）
        self.wait(3.04)
        self.at_clip("S5-c17")
        self.wait(4.52)
        self.at_clip("S5-c18")
        self.play_scroll_unroll(sarsa, run_time=1.2)           # 49.45 -> 50.65（c18 49.45-53.40）
        self.wait(2.57)
        self.at_clip("S5-c19")
        self.wait(1.29)
        self.transition_out(head5, img, t1, t2, vs, sarsa, f, page5)  # 54.87 -> 55.47
        self.pad_to_voice()


# ---------------- S6 后训练半句话 + 预告 + 互动 ----------------
class S6(_Base):
    def construct(self):
        self.bg()
        f = _footer(self)

        # 页1：critic / Q-learning / GRPO（c01-c05）
        head = _head("后训练里，谁在用这笔账？", 38)
        c1 = _card("critic 学 V = 今天的 TD\n下一步当老师", 5.8, 2.2, CYAN, WHITE, 32, CARD_FILL, "BOLD")
        c2 = _card("Q-learning：老师换成 max Q", 5.8, 2.2, GREEN, WHITE, 32, CARD_FILL, "BOLD")
        c3 = _card("GRPO：连老师都不要\n同题平均分当基线", 5.8, 2.2, RED, WHITE, 32, CARD_FILL, "BOLD")
        page1 = page_stack(c1, c2, c3, buff=0.8)
        layout_page(page1)

        self.at_clip("S6-c01")
        self.play_parallel(type_in(head, run_time=0.9), run_time=0.9)  # 0 -> 0.9（c01 0-1.03）
        self.wait(0.05)
        self.at_clip("S6-c02")
        self.play_scroll_unroll(c1, run_time=1.2)             # 1.03 -> 2.23（c02 1.03-6.02）
        self.wait(3.61)
        self.at_clip("S6-c03")
        self.play_scroll_unroll(c2, run_time=1.2)             # 6.02 -> 7.22（c03 6.02-9.62）
        self.wait(2.22)
        self.at_clip("S6-c04")
        self.play_scroll_unroll(c3, run_time=1.2)             # 9.62 -> 10.82（c04 9.62-14.81 主视觉：三卡）
        self.wait(3.81)
        self.at_clip("S6-c05")
        self.wait(2.37)
        self.at_clip("S6-c06")

        # 页2：Watkins 1989 同一种老师（c06-c08）
        head2 = _head("1989 年 Watkins 写下的更新", 36)
        big = t("同一种「下一步当老师」", 46, YELL, "BOLD")
        c4 = _card("今天后训练里用的，和 1989 年写下的，是同一笔账", 5.8, 2.4, GREEN, WHITE, 32, CARD_FILL, "BOLD")
        c5 = _card("不是铺 Q 表，是看懂表背后的那一步", 5.8, 2.4, CYAN, WHITE, 32, CARD_FILL, "BOLD")
        page2 = page_stack(big, c4, c5, buff=1.2)
        layout_page(page2)

        self.play(FadeOut(head), FadeOut(c1), FadeOut(c2), FadeOut(c3),
                  type_in(head2, run_time=0.9), run_time=1.0)  # 17.36 -> 18.36（c06 17.36-23.60）
        self.play(type_in(big, run_time=0.9))                  # 18.36 -> 19.26（c06 内 主视觉：金句）
        self.wait(4.16)
        self.at_clip("S6-c07")
        self.wait(1.83)
        self.at_clip("S6-c08")
        self.play_scroll_unroll_many(c4, c5, run_time=1.4)    # 25.61 -> 27.01（c08 25.61-30.21）
        self.wait(3.02)
        self.at_clip("S6-c09")

        # 页3：预告 + 互动 + 品牌尾卡（c09-c12）
        pre = t("下一篇：策略梯度——不估账本，直接拧概率", 28, WHITE, "BOLD")
        title = t("《Q-learning是什么？没有转移表怎么解》", 28, WHITE, "BOLD")
        title.set_width(6.8)
        q = t("你更信「下一步估值」，还是「同题平均分」？", 30, WHITE, "BOLD")
        q.set_width(6.8)
        logo = ImageMobject(str(AVATAR))
        logo.scale_to_fit_width(2.8)
        follow = t("关注「数解AI」", 38, YELL, "BOLD")
        guide = t("查看公众号文章", 30, GREEN, "BOLD")
        page3 = page_stack(pre, title, q, logo, follow, guide, buff=0.5)
        layout_page(page3)

        self.play(FadeOut(head2), FadeOut(big), FadeOut(c4), FadeOut(c5),
                  type_in(pre, run_time=1.0), run_time=1.0)    # 30.21 -> 31.21（c09 30.21-34.77）
        self.wait(3.38)
        self.at_clip("S6-c10")
        self.play(type_in(title, run_time=1.0))                # 34.77 -> 35.77（c10 34.77-38.91）
        self.wait(2.96)
        self.at_clip("S6-c11")
        self.play(type_in(q, run_time=1.0))                    # 38.91 -> 39.91（c11 38.91-41.14）
        self.wait(1.05)
        self.at_clip("S6-c12")
        self.play(FadeIn(logo, shift=DOWN * 0.05), type_in(follow, run_time=0.9),
                  run_time=0.9)                                # 41.14 -> 42.04（c12 41.14-42.33）
        self.wait(0.29)                                        # 42.04 -> 42.33
        self.play(type_in(guide, run_time=0.7))                # 42.33 -> 43.03（尾卡引导）
        self.wait(3.8)                                         # 43.03 -> 46.83（尾卡停留 2s 加长，2026-09-11 用户确认：多停留显示公众号）
        self.pad_to_voice()
