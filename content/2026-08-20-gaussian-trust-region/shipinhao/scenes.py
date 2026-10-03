#!/usr/bin/env python3
"""《多维高斯：为什么同一步长差1万倍？》视频号 Manim 动画（竖屏 1080×1920）

5 个场景 S1-S5，与 storyboard.md 一一对应（强化学习原理系列第 5 篇）。
- 配音：MiniMax 精英男声（speech-2.8-turbo，speed 1.0，pitch +2）
- 时间轴：at_clip("S1-c01") 挂 tts/sentence-boundaries.json 的 clip 起点（先声音后动画门禁）
- 布局：整页规划（page_stack + layout_page / page_auto），上下留白各 ≤ 10%
- 动画降噪（决策 #51）：emphasize 全片 3 次（S1 对比条 / S3 公式 / S5 概念图），
  v2 动效 0 处；每页 1 个主视觉动效；数字台词全部配 counter_value / grow_bar

用法（shipinhao 目录内执行）：
  MANIM_STRICT_TIMELINE=1 MANIM_STRICT_WIDTH=1 python3 -m manim render -ql --disable_caching scenes.py S1 S2 S3 S4 S5
  MANIM_STRICT_TIMELINE=1 MANIM_STRICT_WIDTH=1 python3 -m manim render -qm --disable_caching scenes.py S1 S2 S3 S4 S5
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
# scale=(动画时长-0.1)/source_duration 拉伸逐句字幕 → 段内字幕后移。
# 尾卡停留一律用显式 self.wait() 完成，不要靠加大 TAIL。
VOICE_DUR = {"S1": 37.97, "S2": 42.67, "S3": 35.33, "S4": 44.80, "S5": 49.59}
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


def _cloud(wide_axis: float, narrow_axis: float, color: str, n: int = 46) -> VGroup:
    """壳状椭圆云（脚本画，非 AI 图）：外圈稠密、中心留空。
    wide_axis/narrow_axis 为椭圆的宽轴/窄轴（用户单位），点数 n 控制密度。"""
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


def _step_row(lab: str, num: float, value_text: str, color: str) -> VGroup:
    """步长条：左侧标签 + 长度正比于 num 的实心条（**左端对齐**，两条共用同一起点）
    + 条右端数值。条按最终几何摆好；grow_bar(anchor="center") 在 target == 初始宽度时
    保持左缘不动（center_x 不漂移）——两条宽度不同但左缘同线。"""
    track = Rectangle(width=TRACK_W, height=0.72, color=MUTED, stroke_width=1.5, fill_opacity=0)
    bar = Rectangle(width=TRACK_W * num, height=0.72, color=color,
                    fill_color=color, fill_opacity=0.8)
    bar.move_to(track.get_center())
    bar.align_to(track, LEFT)
    label = t(lab, 30, WHITE, "BOLD")
    label.next_to(track, LEFT, buff=0.38)
    val = t(value_text, 26, color, "BOLD")
    val.next_to(track, RIGHT, buff=0.38)
    val.align_to(track, DOWN)
    return VGroup(label, track, bar, val)


# ---------------- S1 同一个 0.1，差一万倍 ----------------
class S1(_Base):
    def construct(self):
        self.bg()
        f = _footer(self)

        # 页1：两团云「长得一样」→ 同一 0.1 却两种命运（c01-c07）
        head = _head("同一个 0.1，效果差一万倍", 36)
        note_a12 = t("以 coding agent 改代码为例", 24, MUTED)
        lab0 = t("两团云：宽度一样，中心不同", 28, MUTED)
        same = VGroup(_cloud(2.6, 1.5, CYAN, n=34), _cloud(2.6, 1.5, CYAN, n=34))
        same.arrange(RIGHT, buff=1.5)
        lab1 = t("窄方向：KL = 0.5", 32, WHITE, "BOLD")
        bar1 = Rectangle(width=4.6, height=0.85, color=RED,
                         fill_color=RED, fill_opacity=0.75)
        g1 = VGroup(lab1, bar1).arrange(DOWN, buff=0.30)
        lab2 = t("宽方向：KL = 0.00005", 30, WHITE, "BOLD")
        bar2 = Rectangle(width=0.06, height=0.85, color=CYAN,
                         fill_color=CYAN, fill_opacity=0.75)
        g2 = VGroup(lab2, bar2).arrange(DOWN, buff=0.30)
        bars = VGroup(g1, g2).arrange(DOWN, buff=1.05)
        c1 = _card("窄方向翻天覆地\n宽方向几乎没动", 5.6, 2.2, YELL, WHITE, 32, CARD_FILL, "BOLD")
        page1 = page_stack(note_a12, lab0, same, bars, c1, buff=0.60)
        layout_page(page1)

        self.at_clip("S1-c01")
        self.play(type_in(head, run_time=1.0))                 # 0 -> 1.0（c01 0-4.55）
        self.wait(0.2)
        self.play(type_in(note_a12, run_time=0.7))             # 1.2 -> 1.9（A12 开场小字）
        self.at_clip("S1-c04")
        self.play(type_in(lab0, run_time=0.7), FadeIn(same, shift=DOWN * 0.05),
                  run_time=1.0)                                # 8.46 -> 9.46（c04 8.46-12.13）
        self.wait(2.3)
        self.at_clip("S1-c05")
        self.grow_bar(bar1, ValueTracker(0), 4.6, run_time=0.9, anchor="center",
                      extra_anims=[type_in(lab1, run_time=0.6)])   # 12.13 -> 13.03
        self.at_clip("S1-c06")
        self.grow_bar(bar2, ValueTracker(0), 0.06, run_time=0.6, anchor="center",
                      extra_anims=[type_in(lab2, run_time=0.6)])   # 16.79 -> 17.39
        self.wait(0.30)
        self.at_clip("S1-c07")
        self.play_scroll_unroll(c1, run_time=1.2)              # 21.89 -> 23.09
        self.emphasize(bars, run_time=0.7)                     # 23.09 -> 23.79（对比条，强调 1/3）

        # 页2：策略不是参数，是一团云（c08-c12）
        head2 = _head("策略不是参数，是一团云", 38)
        img = _img("s1-cloud-round.png", 3.1)
        c2 = _card("云有形状，直尺就失灵", 5.6, 1.6, YELL, WHITE, 34, CARD_FILL, "BOLD")
        pair = _card("μ 中心：管往哪走\nΣ 宽度：管飘不飘", 5.6, 1.9, GREEN, WHITE, 32, CARD_FILL, "BOLD")
        page2 = page_stack(head2, img, c2, pair, buff=0.75)
        layout_page(page2)

        self.play(FadeOut(head), FadeOut(note_a12), FadeOut(lab0), FadeOut(same),
                  FadeOut(g1), FadeOut(g2), FadeOut(c1),
                  type_in(head2, run_time=0.9), run_time=1.0)  # 23.79 -> 24.79（c08 25.00-26.09）
        self.play(FadeIn(img, shift=DOWN * 0.05), run_time=0.8)   # 24.79 -> 25.59（概念图）
        self.at_clip("S1-c09")
        self.play(type_in(c2, run_time=0.9))                       # 26.09 -> 26.99
        self.at_clip("S1-c11")
        self.play_scroll_unroll(pair, run_time=1.3)                 # 32.31 -> 33.61（主视觉：拉幕）
        self.wait(0.55)
        self.at_clip("S1-c12")
        self.wait(2.18)
        self.transition_out(head2, img, c2, pair, f)               # 36.36 -> 37.87
        self.pad_to_voice()                                        # -> 38.07


# ---------------- S2 云有形状：一个窄，一个宽 ----------------
class S2(_Base):
    def construct(self):
        self.bg()
        f = _footer(self)

        # 页1：两个方向，两种确定度（c01-c09）
        head = _head("两个方向，两种确定度", 38)
        c1 = _card("云窄，行为就稳\n每次都差不多", 5.9, 1.6, CYAN, WHITE, 32, CARD_FILL, "BOLD")
        c2 = _card("云宽，行为就飘\n这次这样，下次那样", 5.9, 1.6, GREEN, WHITE, 32, CARD_FILL, "BOLD")
        e1 = _cloud(4.2, 0.9, CYAN, n=40)
        e2 = _cloud(1.3, 2.6, GREEN, n=40)
        ell = VGroup(e1, e2).arrange(RIGHT, buff=1.0)
        page1 = page_stack(head, c1, c2, ell, buff=0.55)
        layout_page(page1)

        self.at_clip("S2-c01")
        self.play(type_in(head, run_time=1.0))                 # 0 -> 1.0（c01 0-2.51）
        self.at_clip("S2-c04")
        self.play_scroll_unroll(c1, run_time=1.1)              # 7.90 -> 9.00
        self.at_clip("S2-c05")
        self.play_scroll_unroll(c2, run_time=1.1)              # 10.99 -> 12.09
        self.at_clip("S2-c06")
        self.play(FadeIn(ell, shift=DOWN * 0.05), run_time=1.0)  # 14.71 -> 15.71（c06 讲到椭圆，主视觉）
        self.at_clip("S2-c07")
        self.wait(9.14)                                          # 19.86 -> 29.00（c07-c09 讲窄/宽方向，云已在场）

        # 页2：椭圆 + 高维壳（c10-c12）
        head2 = _head("一个窄，一个宽，拼成椭圆", 36)
        img = _img("s2-ellipse-round.png", 4.2)
        d1 = _card("云是二维的\n形状不是圆，是椭圆", 5.5, 1.5, YELL, WHITE, 32, CARD_FILL, "BOLD")
        note = t("维度一高，云的质量全挤到壳上", 27, MUTED)
        page2 = page_stack(head2, img, d1, note, buff=0.55)
        layout_page(page2)

        self.at_clip("S2-c10")
        self.play(FadeOut(head), FadeOut(c1), FadeOut(c2), FadeOut(ell),
                  type_in(head2, run_time=0.9), run_time=1.0)  # 29.00 -> 30.00（c10 29.00-32.22）
        self.at_clip("S2-c11")
        self.play_parallel(FadeIn(img, shift=DOWN * 0.05), type_in(note, run_time=0.8),
                           run_time=0.8)                              # 32.22 -> 33.02（主视觉 + 高维小字）
        self.at_clip("S2-c12")
        self.play_scroll_unroll(d1, run_time=1.1)                     # 36.80 -> 37.90

        # 页3：悬念（c13）
        line1 = t("两团云到底差多远，", 46, WHITE, "BOLD")
        line2 = t("拿什么量？", 46, YELL, "BOLD")
        page3 = page_auto(line1, line2)

        self.at_clip("S2-c13")
        self.play(FadeOut(head2), FadeOut(img), FadeOut(d1), FadeOut(note),
                  type_in(line1, run_time=0.9), run_time=1.0)  # 38.27 -> 39.27（c13 38.27-42.67）
        self.play(type_in(line2, run_time=1.0), run_time=1.0)      # 39.27 -> 40.27
        self.wait(2.30)
        self.transition_out(line1, line2, f)                       # 42.57 -> 43.17
        self.pad_to_voice()                                        # -> 42.77（配音内）


# ---------------- S3 揭盖：KL 是云与云的距离 ----------------
class S3(_Base):
    def construct(self):
        self.bg()
        f = _footer(self)

        # 页1：KL 公式（c01-c08）
        head = _head("KL：用旧策略走出的轨迹\n在新策略眼里有多意外", 34)
        formula = MathTex(r"\mathrm{KL}=\frac{1}{2}\,\Delta\mu^{\top}\Sigma^{-1}\Delta\mu",
                          tex_to_color_map={r"\Delta\mu^{\top}\Sigma^{-1}\Delta\mu": YELL})
        formula.set_width(6.2)
        c1 = _card("不是近似\n是精确等式", 5.5, 2.0, GREEN, WHITE, 34, CARD_FILL, "BOLD")
        note = t("Σ 相同，只有中心不同", 28, MUTED)
        page1 = page_stack(head, formula, c1, note, buff=0.92)
        layout_page(page1)

        self.at_clip("S3-c01")
        self.play(type_in(head, run_time=1.0))                 # 0 -> 1.0（c01 0-2.90）
        self.at_clip("S3-c03")
        self.play(FadeIn(formula), run_time=0.9)               # 7.34 -> 8.24（公式组装）
        self.emphasize(formula, run_time=0.7)                  # 8.24 -> 8.94（公式，强调 2/3）
        self.wait(2.40)
        self.at_clip("S3-c07")
        self.play_scroll_unroll(c1, run_time=1.2)              # 20.37 -> 21.57
        self.at_clip("S3-c08")
        self.play(type_in(note, run_time=0.7))                 # 25.16 -> 25.86（小字，停 ≥2s）

        # 页2：金句（c10）
        line1 = t("KL 量的不是坐标差，", 46, WHITE, "BOLD")
        line2 = t("是形状差", 46, YELL, "BOLD")
        page2 = page_auto(line1, line2)

        self.at_clip("S3-c10")
        self.play(FadeOut(head), FadeOut(formula), FadeOut(c1), FadeOut(note),
                  type_in(line1, run_time=0.9), run_time=1.0)  # 32.05 -> 33.05（c10 32.05-35.33）
        self.play(type_in(line2, run_time=1.0), run_time=1.0)      # 33.05 -> 34.05
        self.wait(1.28)
        self.transition_out(line1, line2, f)                       # 35.23 -> 35.83
        self.pad_to_voice()                                        # -> 35.43（配音内）


# ---------------- S4 揭盖二：尺子的刻度 F = Σ⁻¹ ----------------
class S4(_Base):
    def construct(self):
        self.bg()
        f = _footer(self)

        # 页1：两个 K 值 + 尺子刻度（c01-c11）
        head = _head("同一个 0.1，为什么差一万倍", 32)
        fcard = MathTex(r"\mathrm{KL}=\frac{\Delta\mu^{2}}{2\Sigma}",
                tex_to_color_map={r"\Delta\mu^{2}": YELL})
        fcard.set_width(4.6)
        lab1 = t("窄方向 Σ=0.01，F=100", 26, WHITE, "BOLD")
        slot1 = dynamic_slot(2.5, 1.4)
        row1 = stable_row(lab1, slot1, buff=0.40)
        lab2 = t("宽方向 Σ=100，F=0.01", 26, WHITE, "BOLD")
        slot2 = dynamic_slot(2.5, 1.4)
        row2 = stable_row(lab2, slot2, buff=0.40)
        c1 = _card("云越窄，尺子越敏感", 5.9, 1.9, YELL, WHITE, 32, CARD_FILL, "BOLD")
        page1 = page_stack(head, fcard, row1, row2, c1, buff=0.35)
        layout_page(page1)

        self.at_clip("S4-c01")
        self.play(type_in(head, run_time=1.0))                 # 0 -> 1.0（c01 0-2.87）
        self.at_clip("S4-c03")
        self.play(FadeIn(fcard), run_time=0.8)                 # 4.59 -> 5.39
        self.at_clip("S4-c05")
        n1 = self.counter_value(0, 0.5, decimals=1, size=52, color=RED,
                                run_time=1.0, anchor=slot1,
                                extra_anims=[type_in(lab1, run_time=0.6)])   # 12.06 -> 13.06
        self.at_clip("S4-c07")
        n2 = self.counter_value(0, 0.00005, decimals=5, size=52, color=GREEN,
                                run_time=1.0, anchor=slot2,
                                extra_anims=[type_in(lab2, run_time=0.6)])   # 19.85 -> 20.85（主视觉）
        self.at_clip("S4-c12")
        self.play_scroll_unroll(c1, run_time=1.1)              # 38.23 -> 39.33

        # 页2：反直觉金句（c13）
        line1 = t("越确定的策略，", 46, WHITE, "BOLD")
        line2 = t("越经不起推", 46, YELL, "BOLD")
        page2 = page_auto(line1, line2)

        self.at_clip("S4-c13")
        self.play(FadeOut(head), FadeOut(fcard), FadeOut(row1), FadeOut(n1),
                  FadeOut(row2), FadeOut(n2), FadeOut(c1),
                  type_in(line1, run_time=0.9), run_time=1.0)  # 40.39 -> 41.39（c13 40.39-44.80）
        self.play(type_in(line2, run_time=1.0), run_time=1.0)      # 41.39 -> 42.39
        self.wait(1.91)
        self.transition_out(line1, line2, f)                       # 44.30 -> 44.90
        self.pad_to_voice()                                        # -> 44.90


# ---------------- S5 限步 + TRPO 预告 + 互动 ----------------
class S5(_Base):
    def construct(self):
        self.bg()
        f = _footer(self)

        # 页1：信任域两根步长条（c01-c11）
        head = _head("那把尺子拿来干嘛？限步", 36)
        img = _img("s5-narrow-round.png", 2.4)
        c1 = _card("确定意味着云窄\n云窄意味着尺子敏感", 5.4, 1.4, YELL, WHITE, 32, CARD_FILL, "BOLD")
        row_a = _step_row("窄 Σ=0.01", 0.014 / 1.41, "0.014", RED)
        row_b = _step_row("宽 Σ=100", 1.0, "1.41", GREEN)
        page1 = page_stack(head, img, c1, row_a, row_b, buff=0.55)
        layout_page(page1)

        self.at_clip("S5-c01")
        self.play(type_in(head, run_time=1.0), FadeIn(img, shift=DOWN * 0.05),
                  run_time=1.0)                                 # 0 -> 1.0（c01 0-2.37，图随标题入场）
        self.wait(0.1)
        self.at_clip("S5-c02")
        self.play_scroll_unroll(c1, run_time=1.1)              # 2.37 -> 3.47
        self.at_clip("S5-c07")
        self.wait(5.0)
        self.at_clip("S5-c09")
        self.grow_bar(row_a[2], ValueTracker(0), TRACK_W * 0.014 / 1.41,
                      run_time=0.7, anchor="center",
                      extra_anims=[type_in(row_a[0], run_time=0.5), Create(row_a[1]),
                                   type_in(row_a[3], run_time=0.5)])   # 23.52 -> 24.22
        self.emphasize(img, run_time=0.7)                       # 24.22 -> 24.92（强调 3/3）
        self.at_clip("S5-c10")
        self.grow_bar(row_b[2], ValueTracker(0), TRACK_W,
                      run_time=1.0, anchor="center",
                      extra_anims=[type_in(row_b[0], run_time=0.6), Create(row_b[1]),
                                   type_in(row_b[3], run_time=0.6)])   # 28.29 -> 29.29（主视觉）

        # 页2：金句（c11-c13）
        line1 = t("不是更新太猛，", 44, WHITE, "BOLD")
        line2 = t("是云太窄", 44, YELL, "BOLD")
        line3 = t("经不起推", 44, WHITE, "BOLD")
        page2 = page_auto(line1, line2, line3)

        self.play(FadeOut(head), FadeOut(img), FadeOut(c1), FadeOut(row_a), FadeOut(row_b),
                  type_in(line1, run_time=0.9), run_time=1.0)  # 29.29 -> 30.29（c11 31.46 前）
        self.at_clip("S5-c11")
        self.play(type_in(line2, run_time=0.9), run_time=0.9)  # 31.46 -> 32.36
        self.play_parallel(type_in(line3, run_time=0.9), run_time=0.9)  # 32.36 -> 33.26
        self.at_clip("S5-c12")
        self.wait(1.48)

        # 页3：预告 + 互动 + 品牌尾卡（c12-c15）
        pre = t("下一篇：TRPO——拿着这把尺子去限步", 26, WHITE, "BOLD")
        title = t("《多维高斯：为什么同一步长差1万倍？》", 27, WHITE, "BOLD")
        title.set_width(6.9)
        q = t("你更信参数距离，还是分布距离？", 30, WHITE, "BOLD")
        q.set_width(6.9)
        logo = ImageMobject(str(AVATAR))
        logo.scale_to_fit_width(2.7)
        follow = t("关注「数解AI」", 38, YELL, "BOLD")
        guide = t("查看公众号文章", 30, GREEN, "BOLD")
        page3 = page_stack(pre, title, q, logo, follow, guide, buff=0.5)
        layout_page(page3)

        self.play(FadeOut(line1), FadeOut(line2), FadeOut(line3),
                  type_in(pre, run_time=1.0), run_time=1.0)    # 34.74 -> 35.74（c12 34.74-39.44）
        self.at_clip("S5-c13")
        self.play(type_in(title, run_time=1.0), type_in(q, run_time=1.0), run_time=1.0)  # 39.44 -> 40.44
        self.at_clip("S5-c14")
        self.play(FadeIn(logo, shift=DOWN * 0.05), type_in(follow, run_time=0.9),
                  run_time=0.9)                                # 43.11 -> 44.01（c14 43.11-48.22）
        self.play(type_in(guide, run_time=0.5))                # 44.01 -> 44.51（尾卡引导）
        self.wait(4.08)
        self.pad_to_voice()                                    # -> 49.69
