#!/usr/bin/env python3
"""《策略梯度是什么？直接改概率行不行》视频号 Manim 动画（竖屏 1080×1920）

6 个场景 S1-S6，与 storyboard.md 一一对应。
- 配音：MiniMax 精英男声（speech-2.8-turbo，speed 1.0 pitch +2）
- 时间轴：at_clip("S1-c01") 挂 tts/sentence-boundaries.json 的 clip 起点（先声音后动画门禁）
- 布局：整页规划（page_stack + layout_page / page_auto），上下留白各 ≤10%
- 动画降噪：emphasize 全片 5 次（S1 旋钮图 / S2 对数导数 / S3 绿那条 / S4 优势 / S5 红那行），
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
# ⚠️ TAIL 必须等于 build 脚本的 --tail（默认 0.1）：末段 mux 时长取
# max(配音+0.1, 动画时长)，若动画比「配音+0.1」长，build 会按
# scale=(动画时长-0.1)/source_duration 拉伸逐句字幕 → 段内字幕后移
# （2026-09-12 事故：TAIL 2.5 使 S6 字幕累积 +2.3s、末段 2.8s 静音）。
# 尾卡停留一律用显式 self.wait() 完成，不要靠加大 TAIL。
VOICE_DUR = {"S1": 37.035, "S2": 47.189, "S3": 49.664, "S4": 46.848, "S5": 49.237, "S6": 44.566}
TAIL = 0.1


def _footer(self) -> Text:
    f = t("数解AI · 强化学习原理", 20, MUTED).to_edge(DOWN, buff=1.15)
    self.add(f)
    return f


def _head(text: str, size: float = 38) -> Text:
    return t(text, size, YELL, "BOLD").to_edge(UP, buff=1.2)


def _img(name: str, width: float) -> ImageMobject:
    im = ImageMobject(str(IMG / name))
    im.scale_to_fit_width(width)
    return im


# ---------------- S1 今天不问账本，问概率 ----------------
class S1(_Base):
    def construct(self):
        self.bg()
        f = _footer(self)

        # 页1：概率双条（c01-c03）
        head = _head("今天不问账本，问概率", 40)
        note_a12 = t("以 coding agent 改代码为例", 24, MUTED)
        lab1 = t("跑测试 0.70", 30, WHITE, "BOLD")
        bar1 = Rectangle(width=4.4, height=0.85, color=CYAN,
                         fill_color=CYAN, fill_opacity=0.75)
        g1 = VGroup(lab1, bar1).arrange(DOWN, buff=0.32)
        lab2 = t("再改一处 0.30", 30, WHITE, "BOLD")
        bar2 = Rectangle(width=1.9, height=0.85, color=GREEN,
                         fill_color=GREEN, fill_opacity=0.75)
        g2 = VGroup(lab2, bar2).arrange(DOWN, buff=0.32)
        bars = VGroup(g1, g2).arrange(DOWN, buff=0.95)
        c1 = _card("习惯七成跑测试，三成再改", 5.8, 1.7, YELL, WHITE, 32, CARD_FILL, "BOLD")
        page1 = page_stack(note_a12, bars, c1, buff=1.1)
        layout_page(page1)

        self.at_clip("S1-c01")
        self.play(type_in(head, run_time=1.0))                 # 0 -> 1.0（c01 0-4.31）
        self.wait(0.2)                                         # 1.0 -> 1.2（标题与副题分拍）
        self.play(type_in(note_a12, run_time=0.7))             # 1.2 -> 1.9（A12 开场小字）
        self.at_clip("S1-c02")
        self.grow_bar(bar1, ValueTracker(0), 4.4, run_time=0.9, anchor="center",
                      extra_anims=[type_in(lab1, run_time=0.6)])   # 4.31 -> 5.21
        self.at_clip("S1-c03")
        self.grow_bar(bar2, ValueTracker(0), 1.9, run_time=0.8, anchor="center",
                      extra_anims=[type_in(lab2, run_time=0.6)])   # 7.06 -> 7.86
        self.wait(0.30)                                        # 条长完再落结论卡（有意分拍）
        self.play_scroll_unroll(c1, run_time=1.2)              # 8.16 -> 9.36（c03 7.06-9.60）
        self.wait(0.24)

        # 页2：旋钮（c04-c06）
        head2 = _head("这个习惯带着旋钮", 40)
        img = _img("s1-knob-round.png", 4.6)
        c2 = _card("世界怎么变你拧不动\n自己的习惯，可以拧", 5.8, 2.4, YELL, WHITE, 34, CARD_FILL, "BOLD")
        page2 = page_stack(img, c2, buff=1.2)
        layout_page(page2)

        self.play(FadeOut(head), FadeOut(note_a12), FadeOut(g1), FadeOut(g2), FadeOut(c1),
                  type_in(head2, run_time=0.9), FadeIn(img, shift=DOWN * 0.05),
                  run_time=1.1)                                # 9.60 -> 10.70（c04 9.60-12.94）
        self.at_clip("S1-c05")
        self.emphasize(img, run_time=0.7)                      # 12.94 -> 13.64（旋钮，强调 1/5）
        self.at_clip("S1-c06")
        self.play_scroll_unroll(c2, run_time=1.3)              # 18.22 -> 19.52（c06 18.22-21.96 主视觉：拉幕）
        self.wait(2.44)

        # 页3：θ 与 sigmoid（c07-c09）
        head3 = _head("新符号：西塔 θ 和 sigmoid", 38)
        note = t("θ 读作 theta，就是一个数", 28, MUTED)
        d1 = _card("θ：旋钮本身\n管「跑测试」的概率", 5.8, 2.3, CYAN, WHITE, 32, CARD_FILL, "BOLD")
        d2 = _card("σ(θ) 把 θ 压到 0 和 1 之间", 5.8, 1.9, GREEN, WHITE, 32, CARD_FILL, "BOLD")
        lab3 = t("θ ≈ 0.847 → π = 0.70", 36, WHITE, "BOLD")
        slot = dynamic_slot(2.0, 1.2)
        row3 = stable_row(lab3, slot, buff=0.5)
        page3 = page_stack(note, d1, d2, row3, buff=1.1)
        layout_page(page3)

        self.play(FadeOut(head2), FadeOut(img), FadeOut(c2),
                  type_in(head3, run_time=0.9), type_in(note, run_time=0.6),
                  run_time=1.1)                                # 21.96 -> 23.06（c07 21.96-26.88）
        self.play_scroll_unroll(d1, run_time=1.2)              # 23.06 -> 24.26
        self.at_clip("S1-c08")
        self.play_scroll_unroll(d2, run_time=1.2)              # 26.88 -> 28.08（c08 26.88-32.39）
        self.at_clip("S1-c09")
        n = self.counter_value(0, 0.847, decimals=3, size=64, color=YELL,
                               run_time=1.2, anchor=slot,
                               extra_anims=[type_in(lab3, run_time=0.7)])  # 32.39 -> 33.59（主视觉：数字滚动）
        self.wait(2.30)
        self.transition_out(head3, note, d1, d2, row3, n, f)   # 35.89 -> 36.49
        self.pad_to_voice()


# ---------------- S2 乘回去为什么合法 ----------------
class S2(_Base):
    def construct(self):
        self.bg()
        f = _footer(self)

        # 页1：目标 J（c01-c05）
        head = _head("目标是让回报平均变大", 38)
        form = MathTex(r"J(\theta)=\mathbb{E}[G]", tex_to_color_map={r"J(\theta)": YELL})
        form.set_width(4.6)
        chip1 = _card("七成：跑测试", 2.7, 1.6, CYAN, WHITE, 30, CARD_FILL, "BOLD")
        chip2 = _card("三成：再改", 2.7, 1.6, GREEN, WHITE, 30, CARD_FILL, "BOLD")
        chips = VGroup(chip1, chip2).arrange(RIGHT, buff=0.5)
        c1 = _card("平均里藏着概率\n对概率求导，容易拧出界", 5.8, 2.4, RED, WHITE, 32, CARD_FILL, "BOLD")
        page1 = page_stack(form, chips, c1, buff=1.4)
        layout_page(page1)

        self.at_clip("S2-c01")
        self.play_parallel(type_in(head, run_time=1.0), FadeIn(form), run_time=1.1)  # 0 -> 1.1
        self.at_clip("S2-c02")
        self.at_clip("S2-c03")
        self.play_scroll_unroll_many(chip1, chip2, run_time=1.3)   # 8.30 -> 9.60（c03 8.30-11.00）
        self.at_clip("S2-c04")
        self.at_clip("S2-c05")
        self.play_scroll_unroll(c1, run_time=1.3)              # 16.08 -> 17.38（c05 16.08-19.78 主视觉：拉幕）
        self.wait(2.40)

        # 页2：对数导数那一刀（c06-c09）
        head2 = _head("有一刀，专门砍这个别扭", 36)
        cut = MathTex(r"\nabla_\theta \pi_\theta=\pi_\theta\,\nabla_\theta\log\pi_\theta",
                      tex_to_color_map={r"\log\pi_\theta": YELL})
        cut.set_width(6.8)
        d1 = _card("log 的导数是 x 分之一，\n两边乘回去，小学数学", 5.8, 2.9, GREEN, WHITE, 32, CARD_FILL, "BOLD")
        note2 = t("这一刀，让梯度算得动", 30, YELL, "BOLD")
        page2 = page_stack(cut, d1, note2, buff=1.6)
        layout_page(page2)

        self.play(FadeOut(head), FadeOut(form), FadeOut(chip1), FadeOut(chip2), FadeOut(c1),
                  type_in(head2, run_time=0.9), FadeIn(cut), run_time=1.1)  # 19.78 -> 20.88（c06 19.78-23.09）
        self.emphasize(cut, run_time=0.7)                      # 20.88 -> 21.58（对数导数，强调 2/5）
        self.play(type_in(note2, run_time=0.7))                # 21.58 -> 22.28
        self.at_clip("S2-c07")
        self.at_clip("S2-c08")
        self.play_scroll_unroll(d1, run_time=1.2)              # 26.59 -> 27.79（c08 26.59-27.76）
        self.wait(1.97)

        # 页3：策略梯度 + 乘回去（c10-c15）
        head3 = _head("这就是策略梯度", 40)
        pg = MathTex(r"\nabla_\theta J=\mathbb{E}\big[G_t\,\nabla_\theta\log\pi_\theta(A_t\mid S_t)\big]",
                     tex_to_color_map={r"G_t": GREEN, r"\nabla_\theta\log\pi_\theta": YELL})
        pg.set_width(7.0)
        img = _img("s2-multiply-back-round.png", 3.8)
        c2 = _card("绿了，下次更容易选它\n红了，乘完是 0，等于没拧", 5.8, 2.4, YELL, WHITE, 32, CARD_FILL, "BOLD")
        page3 = page_stack(pg, img, c2, buff=1.0)
        layout_page(page3)

        self.play(FadeOut(head2), FadeOut(cut), FadeOut(d1), FadeOut(note2),
                  type_in(head3, run_time=0.9), FadeIn(pg), run_time=1.1)  # 30.58 -> 31.68（c10 30.58-37.89）
        self.at_clip("S2-c11")
        self.at_clip("S2-c12")
        self.play(FadeIn(img, shift=DOWN * 0.05), run_time=0.8)     # 38.72 -> 39.52（c12 38.72-39.56）
        self.at_clip("S2-c13")
        self.at_clip("S2-c14")
        self.play_scroll_unroll(c2, run_time=1.3)              # 42.06 -> 43.36（c14 42.06-44.36 主视觉：拉幕）
        self.at_clip("S2-c15")
        self.wait(2.39)
        self.transition_out(head3, pg, img, c2, f)             # 45.75 -> 46.35
        self.pad_to_voice()                                    # 46.35 -> 47.29（= 配音 + TAIL）


# ---------------- S3 手算两条轨迹：G 推了两笔 ----------------
class S3(_Base):
    def construct(self):
        self.bg()
        f = _footer(self)

        # 页1：参数与两条轨迹（c01-c07）
        head = _head("手算：同一把旋钮，看红和绿", 36)
        params = _card("π = 0.70　　θ ≈ 0.847　　α = 0.5", 5.8, 1.7, CYAN, WHITE, 32, CARD_FILL, "BOLD")
        red = _card("红：G = 0", 2.7, 3.0, RED, WHITE, 34, CARD_FILL, "BOLD")
        green = _card("绿：G = 1", 2.7, 3.0, GREEN, WHITE, 34, CARD_FILL, "BOLD")
        two = VGroup(red, green).arrange(RIGHT, buff=0.5)
        grad = _card("logπ 的梯度 = 1 − 0.70 = 0.30", 5.8, 1.7, YELL, WHITE, 32, CARD_FILL, "BOLD")
        page1 = page_stack(params, two, grad, buff=0.95)
        layout_page(page1)

        self.at_clip("S3-c01")
        self.play(type_in(head, run_time=1.0))                 # 0 -> 1.0（c01 0-1.69）
        self.at_clip("S3-c02")
        self.play_scroll_unroll_many(red, green, run_time=1.3)  # 1.69 -> 2.99（c02 1.69-5.48）
        self.at_clip("S3-c03")
        self.at_clip("S3-c04")
        self.at_clip("S3-c05")
        self.play_scroll_unroll(params, run_time=1.2)          # 11.90 -> 13.10（c05 11.90-17.60）
        self.at_clip("S3-c06")
        self.at_clip("S3-c07")
        self.play_scroll_unroll(grad, run_time=1.2)            # 19.34 -> 20.54（c07 19.34-23.19）
        self.wait(2.65)

        # 页2：红那条，旋钮不动（c08-c10）
        head2 = _head("红的那条：旋钮不动", 38)
        lab = t("π（跑测试）", 44, WHITE, "BOLD")
        slot = dynamic_slot(2.2, 1.4)
        row = stable_row(lab, slot, buff=0.6)
        d_red = _card("0.847 + 0.5 × 0 × 0.30\n= 0.847", 5.8, 1.8, RED, WHITE, 32, CARD_FILL, "BOLD")
        n_red = _card("失败乘回去是 0，等于没改", 5.8, 1.8, MUTED, WHITE, 32, CARD_FILL, "BOLD")
        page2 = page_stack(row, d_red, n_red, buff=1.3)
        layout_page(page2)

        self.play(FadeOut(head), FadeOut(params), FadeOut(red), FadeOut(green), FadeOut(grad),
                  type_in(head2, run_time=0.9), run_time=1.0)  # 23.19 -> 24.19（c08 23.19-27.73）
        self.at_clip("S3-c09")
        n1 = self.counter_value(0.70, 0.70, decimals=2, size=80, color=RED,
                                run_time=1.2, anchor=slot,
                                extra_anims=[type_in(lab, run_time=0.6)])  # 27.73 -> 28.93（主视觉：数字滚动）
        self.wait(0.10)                                        # 28.93 -> 29.03（数字与算式卡分拍）
        self.play_scroll_unroll(d_red, run_time=1.2)           # 29.03 -> 30.23（c09，配音念算式）
        self.wait(0.32)                                        # 30.23 -> 30.55（对齐 c10 边界）
        self.at_clip("S3-c10")
        self.play_scroll_unroll(n_red, run_time=1.2)           # 30.55 -> 31.75（c10 30.55-33.35）
        self.wait(0.05)                                        # 31.75 -> 31.80（与换页分拍）

        # 页3：绿那条，抬到 0.73（c11-c12）
        head3 = _head("绿的那条：抬到 0.73", 38)
        lab2 = t("π（跑测试）", 44, WHITE, "BOLD")
        slot2 = dynamic_slot(2.2, 1.4)
        row2 = stable_row(lab2, slot2, buff=0.6)
        d_green = _card("0.847 + 0.5 × 1 × 0.30\n= 0.997", 5.8, 1.8, GREEN, WHITE, 32, CARD_FILL, "BOLD")
        d_sig = _card("σ(0.997)：0.70 → 0.73", 5.8, 1.8, YELL, WHITE, 32, CARD_FILL, "BOLD")
        page3 = page_stack(row2, d_green, d_sig, buff=1.3)
        layout_page(page3)

        self.play(FadeOut(head2), FadeOut(n1), FadeOut(row), FadeOut(d_red), FadeOut(n_red),
                  type_in(head3, run_time=0.9), run_time=0.9)  # 31.80 -> 32.70（c10 内换页）
        self.wait(0.65)                                        # 32.70 -> 33.35（对齐 c11 边界）
        self.at_clip("S3-c11")
        self.wait(0.20)                                        # 33.35 -> 33.55（与拉幕分拍）
        self.play_scroll_unroll(d_green, run_time=1.2)         # 33.55 -> 34.75（c11 算式卡）
        self.wait(0.10)                                        # 34.75 -> 34.85（算式卡与数字分拍）
        n2 = self.counter_value(0.70, 0.73, decimals=2, size=80, color=GREEN,
                                run_time=1.2, anchor=slot2,
                                extra_anims=[type_in(lab2, run_time=0.6)])  # 34.85 -> 36.05
        self.wait(1.59)                                        # 36.05 -> 37.64（对齐 c12 边界）
        self.at_clip("S3-c12")
        self.play_scroll_unroll(d_sig, run_time=1.0)           # 37.64 -> 38.64（c12，卡片必须拉幕）
        self.emphasize(n2, run_time=0.7)                       # 38.64 -> 39.34（绿那条，强调 3/5）
        self.wait(3.67)                                        # 39.34 -> 43.01（对齐 c13 边界）

        # 页4：金句（c13-c14）
        line1 = t("赢的那条会教，输的那条沉默", 46, YELL, "BOLD")
        line2 = t("一半的课，老师没来", 46, WHITE, "BOLD")
        page4 = page_auto(line1, line2)

        self.play(FadeOut(head3), FadeOut(n2), FadeOut(row2), FadeOut(d_green), FadeOut(d_sig),
                  run_time=1.0)                                # 43.01 -> 44.01（c13 43.01-46.12）
        self.play(type_in(line1, run_time=1.0))                # 44.01 -> 45.01
        self.at_clip("S3-c14")
        self.play(type_in(line2, run_time=1.0))                # 46.12 -> 47.12（c14 46.12-49.66）
        self.wait(1.94)
        self.transition_out(line1, line2, f)                   # 49.06 -> 49.66
        self.pad_to_voice()


# ---------------- S4 揭盖：分数换成「比平均好多少」 ----------------
class S4(_Base):
    def construct(self):
        self.bg()
        f = _footer(self)

        # 页1：第一级，减掉基线（c01-c08）
        head = _head("第一级：减掉一个只跟状态有关的数", 32)
        form = MathTex(r"G - V(s)", tex_to_color_map={r"V(s)": CYAN})
        form.set_width(3.8)
        green = _card("绿：1 − 0.50 = +0.50", 5.8, 1.7, GREEN, WHITE, 32, CARD_FILL, "BOLD")
        red = _card("红：0 − 0.50 = −0.50", 5.8, 1.7, RED, WHITE, 32, CARD_FILL, "BOLD")
        base = _card("这个数叫基线，只跟状态有关", 5.8, 1.7, CYAN, WHITE, 32, CARD_FILL, "BOLD")
        page1 = page_stack(form, green, red, base, buff=0.95)
        layout_page(page1)

        self.at_clip("S4-c01")
        self.play(type_in(head, run_time=1.0))                 # 0 -> 1.0（c01 0-2.38）
        self.at_clip("S4-c02")
        self.play(FadeIn(form), run_time=0.8)                  # 2.38 -> 3.18
        self.at_clip("S4-c03")
        self.play_scroll_unroll_many(green, red, run_time=1.3)  # 5.50 -> 6.80（c03 5.50-9.36）
        self.at_clip("S4-c04")
        self.at_clip("S4-c05")
        self.at_clip("S4-c06")
        self.at_clip("S4-c07")
        self.at_clip("S4-c08")
        self.play_scroll_unroll(base, run_time=1.2)            # 20.51 -> 21.71（c08 20.51-23.51）
        self.wait(1.80)

        # 页2：第二级，优势（c09-c12）
        head2 = _head("第二级：这个动作比平均好多少", 32)
        v_card = _card("V(s)\n不挑动作的平均账", 2.7, 3.0, CYAN, WHITE, 32, CARD_FILL, "BOLD")
        q_card = _card("Q(s,a)\n把动作说死的那本账", 2.7, 3.0, GREEN, WHITE, 32, CARD_FILL, "BOLD")
        two = VGroup(v_card, q_card).arrange(RIGHT, buff=0.5)
        aform = MathTex(r"A(s,a)=Q(s,a)-V(s)", tex_to_color_map={r"A(s,a)": YELL})
        aform.set_width(6.2)
        habit = _card("你要改的是习惯，不是局面", 5.8, 1.7, YELL, WHITE, 32, CARD_FILL, "BOLD")
        page2 = page_stack(two, aform, habit, buff=1.4)
        layout_page(page2)

        self.play(FadeOut(head), FadeOut(form), FadeOut(green), FadeOut(red), FadeOut(base),
                  type_in(head2, run_time=0.9), run_time=1.0)  # 23.51 -> 24.51（c09 23.51-28.18）
        self.play_scroll_unroll_many(v_card, q_card, run_time=1.3)  # 24.51 -> 25.81
        self.at_clip("S4-c10")
        self.play(FadeIn(aform), run_time=0.9)                 # 28.18 -> 29.08（c10 28.18-33.25）
        self.emphasize(aform, run_time=0.7)                    # 29.08 -> 29.78（优势，强调 4/5）
        self.at_clip("S4-c11")
        self.at_clip("S4-c12")
        self.play_scroll_unroll(habit, run_time=1.2)           # 35.58 -> 36.78（c12 35.58-38.22）
        self.wait(1.44)

        # 页3：Actor-Critic（c13-c15）
        head3 = _head("这套班子叫 Actor-Critic", 36)
        img = _img("s4-critic-actor-round.png", 3.6)
        actor = _card("Actor\n被梯度推的策略", 2.7, 2.4, YELL, WHITE, 30, CARD_FILL, "BOLD")
        critic = _card("Critic\n打分的价值函数", 2.7, 2.4, CYAN, WHITE, 30, CARD_FILL, "BOLD")
        pair = VGroup(actor, critic).arrange(RIGHT, buff=0.5)
        d_delta = _card("δ 就是优势的现场估计", 5.8, 1.7, GREEN, WHITE, 32, CARD_FILL, "BOLD")
        page3 = page_stack(img, pair, d_delta, buff=0.6)
        layout_page(page3)

        self.play(FadeOut(head2), FadeOut(two), FadeOut(aform), FadeOut(habit),
                  type_in(head3, run_time=0.9), FadeIn(img, shift=DOWN * 0.05),
                  run_time=1.1)                                # 38.22 -> 39.32（c13 38.22-41.23）
        self.at_clip("S4-c14")
        self.play_scroll_unroll_many(actor, critic, run_time=1.3)  # 41.23 -> 42.53（c14 41.23-45.10）
        self.at_clip("S4-c15")
        self.play_scroll_unroll(d_delta, run_time=1.0)         # 45.10 -> 46.10（c15 45.10-46.85）
        self.transition_out(head3, img, pair, d_delta, f)      # 46.10 -> 46.70
        self.pad_to_voice()


# ---------------- S5 同一红、同一绿，换成 δ ----------------
class S5(_Base):
    def construct(self):
        self.bg()
        f = _footer(self)

        # 页1：更新式只换分数（c01-c02）
        head = _head("更新式只换了分数", 38)
        up = MathTex(r"\theta \leftarrow \theta + \alpha\,\delta\,\nabla_\theta\log\pi_\theta",
                     tex_to_color_map={r"\delta": YELL, r"\alpha": GREEN})
        up.set_width(7.0)
        params = _card("V(s₀) = 0.50　　α = 0.5　　∇logπ = 0.30", 5.8, 2.6, CYAN, WHITE, 32, CARD_FILL, "BOLD")
        note1 = t("分数从 G 换成 δ，别的都没动", 34, YELL, "BOLD")
        page1 = page_stack(up, params, note1, buff=1.9)
        layout_page(page1)

        self.at_clip("S5-c01")
        self.play_parallel(type_in(head, run_time=1.0), FadeIn(up), run_time=1.1)  # 0 -> 1.1（c01 0-3.09）
        self.at_clip("S5-c02")
        self.play_scroll_unroll(params, run_time=1.2)          # 3.09 -> 4.29（c02 3.09-6.09）
        self.wait(0.3)                                         # 4.29 -> 4.59（c02 内：分拍停顿）
        self.play(type_in(note1, run_time=0.7))                # 4.59 -> 5.29（c02 内：更新式说明）
        self.wait(1.10)

        # 页2：红降到 0.68（c03-c07）
        head2 = _head("红的那条：0.70 → 0.68", 36)
        lab = t("π（跑测试）", 44, WHITE, "BOLD")
        slot = dynamic_slot(2.2, 1.4)
        row = stable_row(lab, slot, buff=0.6)
        d1 = _card("δ = −0.50：\n0.847 + 0.5 × (−0.50) × 0.30", 5.8, 1.8, RED, WHITE, 30, CARD_FILL, "BOLD")
        d2 = _card("σ(0.772)：失败终于会教了", 5.8, 1.8, YELL, WHITE, 32, CARD_FILL, "BOLD")
        page2 = page_stack(row, d1, d2, buff=1.3)
        layout_page(page2)

        self.play(FadeOut(head), FadeOut(up), FadeOut(params), FadeOut(note1),
                  type_in(head2, run_time=0.9), run_time=1.0)  # 6.09 -> 7.09（c03 6.09-11.24）
        self.play_scroll_unroll(d1, run_time=1.2)              # 7.09 -> 8.29
        self.at_clip("S5-c04")
        self.at_clip("S5-c05")
        self.at_clip("S5-c06")
        n1 = self.counter_value(0.70, 0.68, decimals=2, size=80, color=RED,
                                run_time=1.2, anchor=slot,
                                extra_anims=[type_in(lab, run_time=0.6)])  # 18.65 -> 19.85（主视觉）
        self.wait(0.32)                                        # 19.85 -> 20.17（对齐 c07 边界）
        self.emphasize(n1, run_time=0.7)                       # 20.17 -> 20.87（红那行，强调 5/5）
        self.play_scroll_unroll(d2, run_time=1.0)              # 20.87 -> 21.87（c07，卡片必须拉幕）
        self.wait(0.72)                                        # 21.87 -> 22.59（c07 末）

        # 页3：绿到 0.72（c08-c10）
        head3 = _head("绿的那条：0.70 → 0.72", 36)
        lab2 = t("π（跑测试）", 44, WHITE, "BOLD")
        slot2 = dynamic_slot(2.2, 1.4)
        row2 = stable_row(lab2, slot2, buff=0.6)
        d3 = _card("δ = +0.50：算下来 0.922", 5.8, 1.8, GREEN, WHITE, 32, CARD_FILL, "BOLD")
        d4 = _card("还是往上，但幅度小一截", 5.8, 1.8, YELL, WHITE, 32, CARD_FILL, "BOLD")
        page3 = page_stack(row2, d3, d4, buff=1.3)
        layout_page(page3)

        self.play(FadeOut(head2), FadeOut(n1), FadeOut(row), FadeOut(d1), FadeOut(d2),
                  type_in(head3, run_time=0.9), run_time=1.0)  # 22.12 -> 23.12（c08 22.12-24.06）
        self.at_clip("S5-c08")
        self.play_scroll_unroll(d3, run_time=1.2)              # 24.06 -> 25.26（c08 24.06-29.73）
        self.at_clip("S5-c09")
        n2 = self.counter_value(0.70, 0.72, decimals=2, size=80, color=GREEN,
                                run_time=1.2, anchor=slot2,
                                extra_anims=[type_in(lab2, run_time=0.6)])  # 29.73 -> 30.93（主视觉）
        self.wait(1.63)                                        # 30.93 -> 32.56（对齐 c10 边界）
        self.at_clip("S5-c10")
        self.play_scroll_unroll(d4, run_time=1.2)              # 32.56 -> 33.76（c10 32.56-36.90）
        self.wait(3.14)

        # 页4：两列对比（c11-c13）
        head4 = _head("并排放：评委在场和不在场", 36)
        t1 = _card("用 G\n红 0.70 不动\n绿 0.73", 5.8, 2.2, CYAN, WHITE, 30, CARD_FILL, "BOLD")
        t2 = _card("用 δ\n红 0.68\n绿 0.72", 5.8, 2.2, YELL, WHITE, 30, CARD_FILL, "BOLD")
        line = t("差的就是红这一行", 46, YELL, "BOLD")
        page4 = page_stack(t1, t2, line, buff=1.1)
        layout_page(page4)

        self.play(FadeOut(head3), FadeOut(n2), FadeOut(row2), FadeOut(d3), FadeOut(d4),
                  type_in(head4, run_time=0.9), run_time=1.0)  # 36.90 -> 37.90（c11 36.90-40.63）
        self.play_scroll_unroll(t1, run_time=1.2)              # 37.90 -> 39.10
        self.at_clip("S5-c12")
        self.play_scroll_unroll(t2, run_time=1.2)              # 40.63 -> 41.83（c12 40.63-45.40）
        self.at_clip("S5-c13")
        self.play(type_in(line, run_time=0.9))                 # 45.40 -> 46.30（c13 45.40-49.24）
        self.wait(2.44)
        self.transition_out(head4, t1, t2, line, f)            # 48.14 -> 48.74
        self.pad_to_voice()                                    # 48.74 -> 49.34（= 配音 + TAIL）


# ---------------- S6 半句话 + 预告 + 互动 ----------------
class S6(_Base):
    def construct(self):
        self.bg()
        f = _footer(self)

        # 页1：表 or 网络（c01-c06）
        head = _head("半句话：表，还是网络", 38)
        c1 = _card("状态不多：Actor 和 Critic 是一张表", 5.8, 1.8, CYAN, WHITE, 32, CARD_FILL, "BOLD")
        c2 = _card("状态是代码、对话、长轨迹，\n格子铺不开，两边都换成网络", 5.8, 2.2, GREEN, WHITE, 32, CARD_FILL, "BOLD")
        c3 = _card("一边用 δ 做平账\n一边用 δ 乘 logπ 拧旋钮", 5.8, 2.2, YELL, WHITE, 32, CARD_FILL, "BOLD")
        page1 = page_stack(c1, c2, c3, buff=0.75)
        layout_page(page1)

        self.at_clip("S6-c01")
        self.play(type_in(head, run_time=1.0))                 # 0 -> 1.0（c01 0-1.09）
        self.at_clip("S6-c02")
        self.play_scroll_unroll(c1, run_time=1.2)              # 1.09 -> 2.29（c02 1.09-6.00）
        self.at_clip("S6-c03")
        self.play_scroll_unroll(c2, run_time=1.3)              # 6.00 -> 7.30（c03 6.00-9.45）
        self.at_clip("S6-c04")
        self.at_clip("S6-c05")
        self.play_scroll_unroll(c3, run_time=1.3)              # 11.11 -> 12.41（c05 11.11-14.81）
        self.wait(2.40)

        # 页2：拧太猛（c06-c10）
        head2 = _head("下一步的问题变了", 38)
        img = _img("s6-too-far-round.png", 3.9)
        line2 = t("不是能不能拧，\n是一次能拧多大", 40, YELL, "BOLD")
        c4 = _card("拧太猛，昨天会的今天忘\n那把尺子，下一篇再拿出来", 5.8, 2.2, RED, WHITE, 32, CARD_FILL, "BOLD")
        page2 = page_stack(img, line2, c4, buff=0.75)
        layout_page(page2)

        self.play(FadeOut(head), FadeOut(c1), FadeOut(c2), FadeOut(c3),
                  type_in(head2, run_time=0.9), FadeIn(img, shift=DOWN * 0.05),
                  run_time=1.1)                                # 14.81 -> 15.91（c06 14.81-17.93）
        self.at_clip("S6-c07")
        self.at_clip("S6-c08")
        self.at_clip("S6-c09")
        self.play(type_in(line2, run_time=1.0))                # 25.83 -> 26.83（c09 25.83-30.23 主视觉：金句）
        self.at_clip("S6-c10")
        self.play_scroll_unroll(c4, run_time=1.3)              # 30.23 -> 31.53（c10 30.23-36.46）
        self.wait(4.93)

        # 页3：预告 + 互动 + 品牌尾卡（c11-c13）
        pre = t("下一篇：TRPO——一步能拧多大", 28, WHITE, "BOLD")
        title = t("《策略梯度是什么？直接改概率行不行》", 28, WHITE, "BOLD")
        title.set_width(6.8)
        q = t("你更信整段回报，还是「比平均好多少」？", 30, WHITE, "BOLD")
        q.set_width(6.8)
        logo = ImageMobject(str(AVATAR))
        logo.scale_to_fit_width(2.8)
        follow = t("关注「数解AI」", 38, YELL, "BOLD")
        guide = t("查看公众号文章", 30, GREEN, "BOLD")
        page3 = page_stack(pre, title, q, logo, follow, guide, buff=0.5)
        layout_page(page3)

        self.play(FadeOut(head2), FadeOut(img), FadeOut(line2), FadeOut(c4),
                  type_in(pre, run_time=1.0), run_time=1.0)    # 36.46 -> 37.46（c11 36.46-39.72）
        self.at_clip("S6-c12")
        self.play(type_in(title, run_time=1.0), type_in(q, run_time=1.0), run_time=1.0)  # 39.72 -> 40.72
        self.at_clip("S6-c13")
        self.play(FadeIn(logo, shift=DOWN * 0.05), type_in(follow, run_time=0.9),
                  run_time=0.9)                                # 43.19 -> 44.09（c13 43.19-44.57）
        self.play(type_in(guide, run_time=0.5))                # 44.09 -> 44.59（尾卡引导）
        self.wait(0.08)                                        # 44.59 -> 44.67（尾卡停留，收在配音+TAIL）
        self.pad_to_voice()
