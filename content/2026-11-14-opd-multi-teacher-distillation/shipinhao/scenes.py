#!/usr/bin/env python3
"""《换个更强的老师，模型训练为什么反而崩了？》视频号 Manim 动画（竖屏 1080×1920）

6 个场景 S1-S6，与 storyboard.md 一一对应（开源大模型技术揭秘·原理篇，DeepSeek-V4 删 Mixed RL 换 OPD）。
- 配音：MiniMax 精英男声（speech-2.8-turbo，speed 1.0，pitch +2），实测总长 299.32s
- 时间轴：at_clip("S1-c01") 挂 tts/sentence-boundaries.json 的 clip 起点（先声音后动画门禁；
  段边界经 ASR + silencedetect 逐段验证：无跨段错位、段内无 ≥1.5s 静音）
- 布局：整页规划（page_stack + layout_page，页高 ≥ 显示带 80%）/ 矮页自动排版（page_auto）
- 动画降噪（决策 #51）：v2 动效 1 处（S4 morph_to 概率质量抽干）+ breathe 2 处；
  emphasize 5 次（S1 教出更差的学生 / S3 接近五倍 / S4 一个口音体系 / S5 均匀继承 / S6 金句 circumscribe）；
  每页 1 个主视觉动效；死空档用 breathe 续命
- 数字台词全配动效：0.9373→0.6003 崩塌条 + 六方案归一化分 grow_bar +
  0.04→0.19 / 0.30→0.21 counter 滚动 + S6 0.04/0.19 双 counter
- 概念图 3 张（yairouter 深蓝系，无数字）：s1-crossroads / s3-crash-lab /
  s4-apprentice-broadcaster（冷调重生成，与深蓝系列统一）
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

# 每段配音时长（tts_split.py 切分 + sentence-boundaries.json 实测 tts/sN.wav），渲染时长 = 配音 + TAIL
VOICE_DUR = {"S1": 53.16, "S2": 48.81, "S3": 55.21, "S4": 43.78, "S5": 57.69, "S6": 40.42}
TAIL = 0.1


def _footer(self) -> Text:
    f = t("数解AI · 大模型后训练", 20, MUTED).to_edge(DOWN, buff=1.15)
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


def _dist_bars(heights, color=YELL, bw: float = 0.5, gap: float = 0.28) -> VGroup:
    """垂直分布柱组（概率质量示意：柱高 = 概率占比，底部对齐）。"""
    bars = VGroup(*[Rectangle(width=bw, height=h, color=color, stroke_width=2,
                             fill_color=color, fill_opacity=0.8)
                    for h in heights])
    bars.arrange(RIGHT, buff=gap, aligned_edge=DOWN)
    return bars


def _fade_row(self, row: VGroup, run_time: float = 0.4):
    self.play(*[FadeOut(m) for m in row], run_time=run_time)


def _tout(self, *mobs, run_time: float = 0.4):
    """场景末转场：轻微下沉淡出（位移收窄到 0.35/0.25——helper 默认右滑 0.9 会把
    宽页内容推出画布，A5 全帧扫描记越界；GRPO 篇同款位移已为先例）。"""
    grp = Group(*mobs)
    self.play(grp.animate.shift(RIGHT * 0.35 + DOWN * 0.25).set_opacity(0),
              run_time=run_time, rate_func=smooth)
    self.remove(grp)


# ---------------- S1 开场钩子：换个更强的老师，为什么崩了 ----------------
class S1(_Base):
    def construct(self):
        self.bg()
        f = _footer(self)

        # 页1：标题 + 岔路概念图（c01-c02）
        head1 = t("换个更强的老师，", 44, YELL, "BOLD")
        head2 = t("模型训练为什么反而崩了？", 44, YELL, "BOLD")
        note2 = t("以 DeepSeek-V4 后训练为例", 24, MUTED)
        img = _img("s1-crossroads-round.png", 4.0)
        page1 = page_stack(head1, head2, note2, img, buff=0.5)
        layout_page(page1)

        self.at_clip("S1-c01")
        self.play(type_in(head1, run_time=1.2), run_time=1.2)                     # 0.00 -> 1.20
        self.at_clip("S1-c02")
        self.play(type_in(head2, run_time=1.2), type_in(note2, run_time=0.7),
                  FadeIn(img, shift=DOWN * 0.05), run_time=1.2)                  # 5.44 -> 6.64

        # 页2：Mixed RL 被删（c03-c05）
        head3 = _head("V3.2 收尾的标准做法", 36)
        cMixed = _card("Mixed RL：多领域数据混在一起，一锅大 RL 训到头", 6.6, 1.5,
                       CYAN, WHITE, 30, CARD_FILL, "BOLD")
        cDel = t("被整个删掉", 48, WHITE, "BOLD")
        cOpd = _card("换成了一套叫 OPD 的东西", 6.6, 1.6, YELL, WHITE, 34, CARD_FILL, "BOLD")
        note5 = t("名字上带蒸馏，干的是 RL 的活儿", 28, MUTED)
        page2 = page_stack(head3, cMixed, cDel, cOpd, note5, buff=0.65)
        layout_page(page2)

        self.at_clip("S1-c03")
        self.play(FadeOut(head1), FadeOut(head2), FadeOut(note2), FadeOut(img),
                  type_in(head3, run_time=0.9), run_time=0.9)                     # 7.95 -> 8.85
        self.at_clip("S1-c04")
        self.play_scroll_unroll(cMixed, run_time=1.0)                             # 12.37 -> 13.37
        self.wait(0.2)
        self.play(type_in(cDel, run_time=0.9), run_time=0.9)                      # 13.57 -> 14.47
        self.wait(0.2)
        cross = self.play_red_cross(cDel, run_time=0.65)                          # 14.67 -> 15.32
        self.at_clip("S1-c05")
        self.play_scroll_unroll(cOpd, run_time=1.0)                               # 15.90 -> 16.90
        self.wait(0.2)
        self.play(type_in(note5, run_time=0.7), run_time=0.7)                     # 17.10 -> 17.80

        # 页3：决策场景（c06-c10）
        head4 = _head("一个更普通的决策", 36)
        cRole = _card("你是后训练的负责人", 6.4, 1.2, CYAN, WHITE, 32, CARD_FILL, "BOLD")
        cMerge = t("数学域 RL 老师训好，\n几个分域老师合并出一个学生", 30, WHITE, "BOLD")
        cnt_slot = dynamic_slot(2.6, 1.1)
        cAsk = _card("有人说：换个更强的老师吧，单体分数高一大截", 6.6, 1.5,
                     CYAN, WHITE, 30, CARD_FILL, "BOLD")
        q1 = t("你换不换？", 48, YELL, "BOLD")
        page3 = page_stack(head4, cRole, cMerge, cnt_slot, cAsk, q1, buff=0.42)
        layout_page(page3)

        self.at_clip("S1-c06")
        self.play(FadeOut(head3), FadeOut(cMixed), FadeOut(cDel), FadeOut(cross),
                  FadeOut(cOpd), FadeOut(note5),
                  type_in(head4, run_time=0.9), run_time=0.9)                    # 17.85 -> 18.75
        self.at_clip("S1-c07")
        self.play_scroll_unroll(cRole, run_time=0.9)                              # 21.23 -> 22.13
        self.at_clip("S1-c08")
        self.play(type_in(cMerge, run_time=1.0), run_time=1.0)                    # 25.81 -> 26.81
        self.wait(0.2)
        num = self.counter_value(0, 0.9373, decimals=4, size=60, color=YELL,
                                 run_time=1.4, anchor=cnt_slot)                   # 27.01 -> 28.41
        self.at_clip("S1-c09")
        self.play_scroll_unroll(cAsk, run_time=1.1)                               # 30.69 -> 31.79
        self.at_clip("S1-c10")
        self.play(type_in(q1, run_time=0.9), run_time=0.9)                        # 35.44 -> 36.34

        # 页4：有人真换了 → 分数崩塌（c11-c13）
        cSwapped = t("有人真换了", 40, WHITE, "BOLD")
        rA = _bar_row("同源", "0.9373", CYAN, 1.0, track_w=2.6, track_h=0.75,
                      lab_size=28, val_size=28)
        rB = _bar_row("换强师", "0.6003", RED, 0.642, track_w=2.6, track_h=0.75,
                      lab_size=28, val_size=28)
        cDown = t("▼", 54, RED, "BOLD")
        cAime = _card("另一版更狠：AIME25 只剩 0.94%", 6.6, 1.4, RED, WHITE, 32,
                      CARD_FILL, "BOLD")
        page_auto(cSwapped, rA, cDown, rB, cAime)

        self.at_clip("S1-c11")
        self.play(FadeOut(head4), FadeOut(cRole), FadeOut(cMerge), FadeOut(cnt_slot),
                  FadeOut(num), FadeOut(cAsk), FadeOut(q1),
                  type_in(cSwapped, run_time=0.8), run_time=0.8)                  # 36.43 -> 37.23
        self.at_clip("S1-c12")
        _grow_bars(self, [(rA[2], 2.9, "left",
                            [type_in(rA[0], run_time=0.5), Create(rA[1]),
                             type_in(rA[3], run_time=0.5)])], run_time=1.0)       # 37.82 -> 38.82
        self.wait(0.2)
        _grow_bars(self, [(rB[2], 2.9 * 0.642, "left",
                            [type_in(rB[0], run_time=0.5), Create(rB[1]),
                             type_in(rB[3], run_time=0.5)])], run_time=1.0)       # 39.02 -> 40.02
        self.at_clip("S1-c13")
        self.play(FadeIn(cDown, shift=UP * 0.1), run_time=0.5)                    # 41.48 -> 41.98
        self.wait(0.2)
        self.play_scroll_unroll(cAime, run_time=1.0)                              # 42.18 -> 43.18
        self.wait(0.2)
        cross2 = self.play_red_cross(cAime, run_time=0.6)                         # 43.38 -> 43.98

        # 页5：结论（c14-c15）
        line14 = t("能力更强的老师，\n教出了更差的学生", 40, YELL, "BOLD")
        cRoot = _card("根源不在老师强不强，在学生答题的方式", 6.6, 1.5, CYAN, WHITE,
                      32, CARD_FILL, "BOLD")
        imgEnd = _img("s1-crossroads-round.png", 3.5)
        page5 = page_stack(line14, cRoot, imgEnd, buff=0.55)
        layout_page(page5)

        self.at_clip("S1-c14")
        self.play(FadeOut(cSwapped), FadeOut(rA), FadeOut(cDown), FadeOut(rB),
                  FadeOut(cAime), FadeOut(cross2), type_in(line14, run_time=1.0),
                  run_time=1.0)                                                   # 45.33 -> 46.33
        self.wait(0.2)
        self.emphasize(line14, run_time=0.7)                                      # 46.53 -> 47.23
        self.at_clip("S1-c15")
        self.play_scroll_unroll(cRoot, run_time=1.0)                              # 48.61 -> 49.61
        self.wait(0.3)
        self.play(FadeIn(imgEnd, shift=DOWN * 0.05), run_time=0.6)                # 49.91 -> 50.51
        self.wait(2.35)                                                           # -> 52.86
        _tout(self, line14, cRoot, imgEnd, f, run_time=0.4)                             # 52.86 -> 53.26
        self.pad_to_voice()


# ---------------- S2 两种学法，三种整合思路 ----------------
class S2(_Base):
    def construct(self):
        self.bg()
        f = _footer(self)

        # 页1：off-policy（c01-c05）
        head1 = _head("蒸馏有两种学法", 36)
        cOff1 = _card("在老师写好的答案上学", 6.5, 1.2, MUTED, WHITE, 30, CARD_FILL, "BOLD")
        cOff2 = _card("老师把整张把握表写下来，学生照着背", 6.5, 1.3, MUTED, WHITE,
                      28, CARD_FILL, "BOLD")
        cOff3 = t("这叫 off-policy", 34, WHITE, "BOLD")
        cOff4 = t("背的是老师的经验，不是自己的答卷", 30, WHITE, "BOLD")
        note1 = t("得分概率表，是老师在自己见过的答案上统计的", 26, MUTED)
        page1 = page_stack(head1, cOff1, cOff2, cOff3, cOff4, note1, buff=0.56)
        layout_page(page1)

        self.at_clip("S2-c01")
        self.play(type_in(head1, run_time=0.9), run_time=0.9)                     # 0.00 -> 0.90
        self.at_clip("S2-c03")
        self.play_scroll_unroll(cOff1, run_time=0.9)                              # 3.50 -> 4.40
        self.at_clip("S2-c04")
        self.play_scroll_unroll(cOff2, run_time=1.0)                              # 7.69 -> 8.69
        self.wait(0.2)
        self.play(type_in(cOff3, run_time=0.8), run_time=0.8)                      # 8.89 -> 9.69
        self.at_clip("S2-c05")
        self.play(type_in(cOff4, run_time=0.9), run_time=0.9)                      # 10.75 -> 11.65
        self.wait(0.2)
        cross1 = self.play_red_cross(cOff4, run_time=0.6)                         # 11.85 -> 12.45
        self.wait(0.2)
        self.play(type_in(note1, run_time=0.7), run_time=0.7)                     # 12.65 -> 13.35

        # 页2：on-policy（c06-c08）
        head2 = _head("另一种：on-policy", 36)
        cOn1 = _card("在自己写的答案上被老师改", 6.5, 1.2, GREEN, WHITE, 30, CARD_FILL, "BOLD")
        cOn2 = _card("学生自己答题，老师逐 token 打分", 6.5, 1.3, GREEN, WHITE, 28,
                     CARD_FILL, "BOLD")
        cOn3 = t("这叫 on-policy", 34, WHITE, "BOLD")
        cPick = _card("OPD 选的正是这条路", 6.6, 1.7, YELL, WHITE, 36, CARD_FILL, "BOLD")
        page2 = page_stack(head2, cOn1, cOn2, cOn3, cPick, buff=0.6)
        layout_page(page2)

        self.at_clip("S2-c06")
        self.play(FadeOut(head1), FadeOut(cOff1), FadeOut(cOff2), FadeOut(cOff3),
                  FadeOut(cOff4), FadeOut(cross1), FadeOut(note1),
                  type_in(head2, run_time=0.9), run_time=0.9)                    # 13.70 -> 14.60
        self.at_clip("S2-c07")
        self.play_scroll_unroll(cOn1, run_time=0.9)                              # 17.98 -> 18.88
        self.wait(0.2)
        self.play_scroll_unroll(cOn2, run_time=1.0)                              # 19.08 -> 20.08
        self.wait(0.2)
        self.play(type_in(cOn3, run_time=0.8), run_time=0.8)                      # 20.28 -> 21.08
        self.at_clip("S2-c08")
        self.play_scroll_unroll(cPick, run_time=1.0)                              # 22.08 -> 23.08

        # 页3：三种思路（c09-c10）
        head3 = _head("N 个专精模型合成一个，三种思路", 32)
        cardData = _card("数据空间混着训", 6.4, 1.1, MUTED, WHITE, 30, CARD_FILL, "BOLD")
        cardWeight = _card("权重空间做平均", 6.4, 1.1, MUTED, WHITE, 30, CARD_FILL, "BOLD")
        cardPolicy = _card("策略空间让老师改", 6.4, 1.2, YELL, WHITE, 32, CARD_FILL, "BOLD")
        page_auto(head3, cardData, cardWeight, cardPolicy)

        self.at_clip("S2-c09")
        self.play(FadeOut(head2), FadeOut(cOn1), FadeOut(cOn2), FadeOut(cOn3),
                  FadeOut(cPick), type_in(head3, run_time=1.0), run_time=1.0)    # 24.24 -> 25.24
        self.at_clip("S2-c10")
        self.play_scroll_unroll_many(cardData, cardWeight, run_time=1.0)          # 30.45 -> 31.45
        self.wait(0.2)
        self.play_scroll_unroll(cardPolicy, run_time=0.9)                         # 31.65 -> 32.55

        # 页4：六方案归一化分（c11-c15）
        head4 = _head("同源老师下，六方案归一化分", 32)
        r1 = _bar_row("朴素权重平均", "0.3280", MUTED, 0.351, track_w=3.0,
                      track_h=0.58, lab_size=25, val_size=25)
        r2 = _bar_row("级联 RL", "0.7752", MUTED, 0.828, track_w=3.0,
                      track_h=0.58, lab_size=25, val_size=25)
        r3 = _bar_row("off-policy 微调", "0.8241", MUTED, 0.880, track_w=3.0,
                      track_h=0.58, lab_size=25, val_size=25)
        r4 = _bar_row("任务算术合并", "0.8574", MUTED, 0.916, track_w=3.0,
                      track_h=0.58, lab_size=25, val_size=25)
        r5 = _bar_row("Mix-RL", "0.8818", CYAN, 0.942, track_w=3.0,
                      track_h=0.58, lab_size=25, val_size=25)
        r6 = _bar_row("OPD", "0.9373", YELL, 1.0, track_w=3.0,
                      track_h=0.58, lab_size=25, val_size=25)
        note6 = t("跨度 0.044，三种里面最小", 30, YELL, "BOLD")
        page4 = page_stack(head4, r1, r2, r3, r4, r5, r6, note6, buff=0.42)
        layout_page(page4)

        self.at_clip("S2-c11")
        self.play(FadeOut(head3), FadeOut(cardData), FadeOut(cardWeight),
                  FadeOut(cardPolicy), type_in(head4, run_time=0.9), run_time=0.9)  # 34.31 -> 35.21
        _grow_bars(self, [(r1[2], 3.0 * 0.351, "left",
                            [type_in(r1[0], run_time=0.4), Create(r1[1]),
                             type_in(r1[3], run_time=0.4)]),
                           (r2[2], 3.0 * 0.828, "left",
                            [type_in(r2[0], run_time=0.4), Create(r2[1]),
                             type_in(r2[3], run_time=0.4)])], run_time=1.0)       # 35.21 -> 36.21
        self.at_clip("S2-c12")
        _grow_bars(self, [(r3[2], 3.0 * 0.880, "left",
                            [type_in(r3[0], run_time=0.4), Create(r3[1]),
                             type_in(r3[3], run_time=0.4)]),
                           (r4[2], 3.0 * 0.916, "left",
                            [type_in(r4[0], run_time=0.4), Create(r4[1]),
                             type_in(r4[3], run_time=0.4)])], run_time=1.0)       # 38.06 -> 39.06
        self.at_clip("S2-c13")
        _grow_bars(self, [(r5[2], 3.0 * 0.942, "left",
                            [type_in(r5[0], run_time=0.4), Create(r5[1]),
                             type_in(r5[3], run_time=0.4)])], run_time=0.9)       # 40.44 -> 41.34
        self.wait(0.2)
        self.at_clip("S2-c14")
        _grow_bars(self, [(r6[2], 3.0, "left",
                            [type_in(r6[0], run_time=0.4), Create(r6[1]),
                             type_in(r6[3], run_time=0.4)])], run_time=1.0)       # 43.20 -> 44.20
        self.wait(0.2)
        self.play(type_in(note6, run_time=0.7), run_time=0.7)                     # 44.40 -> 45.10
        self.wait(0.2)
        self.breathe(r6, loops=2, run_time=1.0)                                   # 45.30 -> 47.30
        self.wait(0.5)                                                            # -> 47.80
        _tout(self, head4, *[m for r in (r1, r2, r3, r4, r5, r6) for m in r],
             note6, f, run_time=0.4)                                              # 47.80 -> 48.20
        self.pad_to_voice()


# ---------------- S3 换强师崩溃：三项诊断 ----------------
class S3(_Base):
    def construct(self):
        self.bg()
        f = _footer(self)

        # 页1：崩溃实验设置（c01-c03）
        head1 = _head("崩掉的那组实验", 36)
        img = _img("s3-crash-lab-round.png", 3.4)
        cFrom = _card("Math 老师：同源的 Qwen3-30B", 6.5, 1.2, CYAN, WHITE, 30,
                      CARD_FILL, "BOLD")
        cTo = _card("换成能力更强的 Qwen3-235B-A22B", 6.5, 1.2, RED, WHITE, 30,
                    CARD_FILL, "BOLD")
        cSame = t("别的对比条件一概不动", 30, WHITE, "BOLD")
        page1 = page_stack(head1, img, cFrom, cTo, cSame, buff=0.42)
        layout_page(page1)

        self.at_clip("S3-c01")
        self.play(type_in(head1, run_time=0.9), FadeIn(img, shift=DOWN * 0.05),
                  run_time=0.9)                                                   # 0.00 -> 0.90
        self.at_clip("S3-c02")
        self.play_scroll_unroll(cFrom, run_time=0.9)                              # 5.17 -> 6.07
        self.wait(0.2)
        self.play_scroll_unroll(cTo, run_time=0.9)                                # 6.27 -> 7.17
        self.at_clip("S3-c03")
        self.play(type_in(cSame, run_time=0.8), run_time=0.8)                      # 9.14 -> 9.94
        self.wait(0.2)
        self.breathe(img, loops=1, run_time=0.8)                                  # 10.14 -> 10.94

        # 页2：分数崩塌（c04-c06）
        head2 = _head("归一化得分，直接崩了", 36)
        rA = _bar_row("同源", "0.9373", CYAN, 1.0, track_w=2.6, track_h=0.75,
                      lab_size=28, val_size=28)
        rB = _bar_row("换强师", "0.6003", RED, 0.642, track_w=2.6, track_h=0.75,
                      lab_size=28, val_size=28)
        cDown = t("▼", 54, RED, "BOLD")
        cTopk = _card("top-k 截断版更惨：AIME25 只剩 0.94%", 6.6, 1.6, RED, WHITE, 32,
                      CARD_FILL, "BOLD")
        cWu = t("聊胜于无", 40, RED, "BOLD")
        page2 = page_stack(head2, rA, cDown, rB, cTopk, cWu, buff=0.45)
        layout_page(page2)

        self.at_clip("S3-c04")
        self.play(FadeOut(head1), FadeOut(img), FadeOut(cFrom), FadeOut(cTo),
                  FadeOut(cSame), type_in(head2, run_time=0.9), run_time=0.9)      # 11.13 -> 12.03
        _grow_bars(self, [(rA[2], 2.9, "left",
                            [type_in(rA[0], run_time=0.5), Create(rA[1]),
                             type_in(rA[3], run_time=0.5)])], run_time=1.0)       # 12.03 -> 13.03
        self.wait(0.2)
        _grow_bars(self, [(rB[2], 2.9 * 0.642, "left",
                            [type_in(rB[0], run_time=0.5), Create(rB[1]),
                             type_in(rB[3], run_time=0.5)])], run_time=1.0)       # 13.23 -> 14.23
        self.at_clip("S3-c05")
        self.play(FadeIn(cDown, shift=UP * 0.1), run_time=0.5)                    # 15.83 -> 16.33
        self.wait(0.2)
        self.play_scroll_unroll(cTopk, run_time=1.0)                              # 16.53 -> 17.53
        self.wait(0.2)
        cross = self.play_red_cross(cTopk, run_time=0.6)                          # 17.73 -> 18.33
        self.at_clip("S3-c06")
        self.play(type_in(cWu, run_time=0.7), run_time=0.7)                       # 21.35 -> 22.05

        # 页3：三项诊断（c07-c12）
        head3 = _head("三项诊断", 40)
        d1 = t("起始距离：逐 token 的 reverse-KL", 30, WHITE, "BOLD")
        slot1 = dynamic_slot(1.2, 1.1)
        slot2 = dynamic_slot(1.2, 1.1)
        d1Row = stable_row(t("同源", 26, CYAN, "BOLD"), slot1,
                           t("换强师", 26, RED, "BOLD"), slot2, buff=0.5)
        d2 = t("熵：输出在往单个模式塌缩", 30, WHITE, "BOLD")
        slot3 = dynamic_slot(1.2, 1.1)
        slot4 = dynamic_slot(1.2, 1.1)
        d2Row = stable_row(t("同源", 26, CYAN, "BOLD"), slot3,
                           t("换强师", 26, RED, "BOLD"), slot4, buff=0.5)
        d3 = _card("top-k 版跑了约 18 步，直接就发散了", 6.6, 1.4, RED, WHITE, 32,
                   CARD_FILL, "BOLD")
        page3 = page_stack(head3, d1, d1Row, d2, d2Row, d3, buff=0.48)
        layout_page(page3)

        self.at_clip("S3-c07")
        self.play(FadeOut(head2), FadeOut(rA), FadeOut(cDown), FadeOut(rB),
                  FadeOut(cTopk), FadeOut(cWu), FadeOut(cross),
                  type_in(head3, run_time=0.8), run_time=0.8)                     # 22.37 -> 23.17
        self.at_clip("S3-c08")
        self.play(type_in(d1, run_time=0.8), run_time=0.8)                        # 24.41 -> 25.21
        self.at_clip("S3-c09")
        self.play(FadeIn(d1Row), run_time=0.5)                                    # 29.33 -> 29.83
        self.wait(0.2)
        n1 = self.counter_value(0.04, 0.04, decimals=2, size=52, color=CYAN,
                                run_time=0.4, anchor=slot1)                       # 30.03 -> 30.43
        self.at_clip("S3-c10")
        n2 = self.counter_value(0.04, 0.19, decimals=2, size=52, color=RED,
                                run_time=1.0, anchor=slot2)                       # 32.38 -> 33.38
        self.wait(0.2)
        self.emphasize(VGroup(d1Row, n1, n2), run_time=0.7)                        # 33.58 -> 34.28
        self.at_clip("S3-c11")
        self.play(FadeOut(d1), FadeOut(d1Row), FadeOut(n1), FadeOut(n2),
                  type_in(d2, run_time=0.8), run_time=0.8)                        # 34.61 -> 35.41
        self.wait(0.2)
        self.play(FadeIn(d2Row), run_time=0.5)                                    # 35.61 -> 36.11
        self.wait(0.2)
        n3 = self.counter_value(0.30, 0.30, decimals=2, size=52, color=CYAN,
                                run_time=0.4, anchor=slot3)                       # 36.31 -> 36.71
        self.wait(0.2)
        n4 = self.counter_value(0.30, 0.21, decimals=2, size=52, color=RED,
                                run_time=1.0, anchor=slot4)                       # 36.91 -> 37.91
        self.at_clip("S3-c12")
        self.play(FadeOut(d2), FadeOut(d2Row), FadeOut(n3), FadeOut(n4),
                  type_in(d3, run_time=0.9), run_time=0.9)                        # 38.65 -> 39.55

        # 页4：工程坑（c13-c15）
        head4 = _head("工程上的坑", 36)
        cPit = _card("top-k 截断少了一项修正", 6.6, 1.3, YELL, WHITE, 32, CARD_FILL, "BOLD")
        cFix = _card("切掉一批词之后，要把学生原本会分给\n它们的概率补回来", 6.6, 1.6,
                     CYAN, WHITE, 30, CARD_FILL, "BOLD")
        cBug = t("不补，最优解变成让学生\n压根不碰 top-k 边缘", 30, RED, "BOLD")
        page_auto(head4, cPit, cFix, cBug)

        self.at_clip("S3-c13")
        self.play(FadeOut(head3), FadeOut(d3),
                  type_in(head4, run_time=0.8), run_time=0.8)                     # 42.11 -> 42.91
        self.at_clip("S3-c14")
        self.play_scroll_unroll(cPit, run_time=0.9)                               # 45.99 -> 46.89
        self.wait(0.2)
        self.play_scroll_unroll(cFix, run_time=1.1)                               # 47.09 -> 48.19
        self.at_clip("S3-c15")
        self.play(type_in(cBug, run_time=1.0), run_time=1.0)                      # 50.38 -> 51.38
        self.wait(0.2)
        cross2 = self.play_red_cross(cBug, run_time=0.6)                          # 51.58 -> 52.18
        self.wait(2.73)                                                           # -> 54.91
        _tout(self, head4, cPit, cFix, cBug, cross2, f, run_time=0.4)                   # 54.91 -> 55.31
        self.pad_to_voice()


# ---------------- S4 口音比喻：学徒与播音员 ----------------
class S4(_Base):
    def construct(self):
        self.bg()
        f = _footer(self)

        # 页1：学徒 × 播音员（c01-c03）
        head1 = _head("把数字翻译成故事", 36)
        img = _img("s4-apprentice-broadcaster-round.png", 3.4)
        cRoles = t("学生是带口音的学徒，\n老师是字正腔圆的播音员", 30, WHITE, "BOLD")
        cGap = _card("有问题的是：师生之间的口音体系差太远", 6.6, 1.5, YELL, WHITE, 32,
                     CARD_FILL, "BOLD")
        page1 = page_stack(head1, img, cRoles, cGap, buff=0.4)
        layout_page(page1)

        self.at_clip("S4-c01")
        self.play(type_in(head1, run_time=0.9), FadeIn(img, shift=DOWN * 0.05),
                  run_time=0.9)                                                   # 0.00 -> 0.90
        self.at_clip("S4-c02")
        self.play(type_in(cRoles, run_time=1.0), run_time=1.0)                    # 3.54 -> 4.54
        self.at_clip("S4-c03")
        self.play_scroll_unroll(cGap, run_time=1.0)                               # 5.78 -> 6.78
        self.wait(0.2)

        # 页2：硬掰（c04-c06）
        head2 = _head("纠正是怎么变成硬掰的", 36)
        cPress = t("老师每纠正一笔，都是把自己认定的\n唯一正确发音往学生身上按", 30, WHITE, "BOLD")
        cRange = t("学生够得着的音域，就那么宽", 32, CYAN, "BOLD")
        cForce = t("够不着的地方，纠正就变成硬掰", 34, YELL, "BOLD")
        page_auto(head2, cPress, cRange, cForce)

        self.at_clip("S4-c04")
        self.play(FadeOut(head1), FadeOut(img), FadeOut(cRoles), FadeOut(cGap),
                  type_in(head2, run_time=0.9), run_time=0.9)                     # 11.56 -> 12.46
        self.wait(0.2)
        self.play(type_in(cPress, run_time=1.1), run_time=1.1)                    # 12.66 -> 13.76
        self.at_clip("S4-c05")
        self.play(type_in(cRange, run_time=0.9), run_time=0.9)                    # 17.07 -> 17.97
        self.wait(0.2)
        self.at_clip("S4-c06")
        self.play(type_in(cForce, run_time=0.5), run_time=0.5)                    # 20.26 -> 20.76
        self.wait(0.15)
        cross = self.play_red_cross(cForce, run_time=0.5)                         # 20.91 -> 21.41

        # 页3：概率质量被抽干（c07-c09，morph_to v2 动效）
        head3 = _head("reverse-KL：认死理的模仿", 34)
        barsFull = _dist_bars([1.0, 0.85, 0.7, 0.55, 0.45, 0.35], color=CYAN)
        noteA = t("学生自身的概率质量被一点点抽干", 30, WHITE, "BOLD")
        noteB = t("摊到别的音上越来越少\n——这就是熵在掉的原因", 30, YELL, "BOLD")
        page_auto(head3, barsFull, noteA, noteB)
        # morph 目标必须在 page_auto 之后创建：page_auto 会缩放入页元素，
        # 提前创建的 barsDrained 不在页组里、拿不到同一变换，形变时会跳位
        barsDrained = _dist_bars([1.55, 0.55, 0.22, 0.12, 0.07, 0.05], color=YELL)
        barsDrained.scale(barsFull.width / 4.4)
        barsDrained.move_to(barsFull.get_center())
        barsDrained.align_to(barsFull, DOWN)

        self.at_clip("S4-c07")
        self.play(FadeOut(head2), FadeOut(cPress), FadeOut(cRange), FadeOut(cForce),
                  FadeOut(cross), type_in(head3, run_time=0.9),
                  Create(barsFull, run_time=0.9, lag_ratio=0.05), run_time=0.9)   # 21.54 -> 22.44
        self.at_clip("S4-c08")
        self.play(type_in(noteA, run_time=0.9), run_time=0.9)                     # 26.85 -> 27.75
        self.wait(0.2)
        self.morph_to(barsFull, barsDrained, run_time=1.2)                        # 27.95 -> 29.15
        self.at_clip("S4-c09")
        self.play(type_in(noteB, run_time=1.0), run_time=1.0)                     # 29.88 -> 30.88
        self.wait(0.2)

        # 页4：同源之稳（c10-c12）
        head4 = _head("同源老师为什么稳", 36)
        cSame = t("不是因为它更强", 34, WHITE, "BOLD")
        cAccent = t("是因为它和学生一个口音体系", 40, YELL, "BOLD")
        cReach = t("✔ 每一笔纠正，都落在学徒发得出的范围里", 30, GREEN, "BOLD")
        page_auto(head4, cSame, cAccent, cReach)

        self.at_clip("S4-c10")
        self.play(FadeOut(head3), FadeOut(barsDrained), FadeOut(noteA), FadeOut(noteB),
                  type_in(head4, run_time=0.9), run_time=0.9)                     # 34.05 -> 34.95
        self.wait(0.2)
        self.play(type_in(cSame, run_time=0.8), run_time=0.8)                     # 35.15 -> 35.95
        self.at_clip("S4-c11")
        self.play(type_in(cAccent, run_time=1.0), run_time=1.0)                   # 37.27 -> 38.27
        self.wait(0.2)
        self.emphasize(cAccent, run_time=0.7)                                     # 38.47 -> 39.17
        self.at_clip("S4-c12")
        self.play(type_in(cReach, run_time=1.0), run_time=1.0)                    # 39.92 -> 40.92
        self.wait(2.56)                                                           # -> 43.48
        _tout(self, head4, cSame, cAccent, cReach, f, run_time=0.4)                     # 43.48 -> 43.88
        self.pad_to_voice()


# ---------------- S5 一盆冷水，三家收敛 ----------------
class S5(_Base):
    def construct(self):
        self.bg()
        f = _footer(self)

        # 页1：冷水三域对比（c01-c08）
        head1 = _head("先泼一盆冷水", 36)
        cIntro = t("多教师版的 OPD，\n不是每一项都能稳定赢过老师", 28, WHITE, "BOLD")
        row1 = _card("AIME25    51.46 对  54.79", 6.6, 1.0, RED, WHITE, 30, CARD_FILL, "BOLD")
        row2 = _card("IFEval      93.84 对  95.50", 6.6, 1.0, RED, WHITE, 30, CARD_FILL, "BOLD")
        row3 = _card("SWE-bench  50.40 对  51.20", 6.6, 1.0, RED, WHITE, 30, CARD_FILL, "BOLD")
        cWin = _card("✔ 只有 AIME26 的 65.31 超了老师", 6.6, 1.3, GREEN, WHITE, 32,
                     CARD_FILL, "BOLD")
        cEven = t("合并的本质是均匀继承，\n不是全面超过", 38, YELL, "BOLD")
        page1 = page_stack(head1, cIntro, row1, row2, row3, cWin, cEven, buff=0.28)
        layout_page(page1)

        self.at_clip("S5-c01")
        self.play(type_in(head1, run_time=0.8), run_time=0.8)                     # 0.00 -> 0.80
        self.at_clip("S5-c02")
        self.play(type_in(cIntro, run_time=1.0), run_time=1.0)                    # 1.40 -> 2.40
        self.wait(0.2)
        self.at_clip("S5-c03")
        self.play_scroll_unroll(row1, run_time=0.8)                               # 6.22 -> 7.02
        self.at_clip("S5-c04")
        self.play_scroll_unroll(row2, run_time=0.8)                               # 10.56 -> 11.36
        self.at_clip("S5-c05")
        self.play_scroll_unroll(row3, run_time=0.8)                               # 14.89 -> 15.69
        self.at_clip("S5-c06")
        self.play_scroll_unroll(cWin, run_time=0.9)                               # 20.10 -> 21.00
        self.at_clip("S5-c07")
        self.play(type_in(cEven, run_time=1.1), run_time=1.1)                     # 23.60 -> 24.70
        self.wait(0.2)
        self.emphasize(cEven, run_time=0.7)                                       # 24.90 -> 25.60

        # 页2：三家收敛（c09-c15）
        head2 = _head("三家国产模型，同一个选择", 34)
        cDs1 = _card("DeepSeek-V4：Mixed RL 整个换成 OPD", 6.6, 1.1, CYAN, WHITE, 28,
                     CARD_FILL, "BOLD")
        cDs2 = _card("十多个领域专家各走 SFT 加 GRPO", 6.6, 1.2, CYAN, WHITE, 28,
                     CARD_FILL, "BOLD")
        cDs3 = _card("学生在自己的答卷上做全词表蒸馏", 6.6, 1.2, CYAN, WHITE, 28,
                     CARD_FILL, "BOLD")
        cKimi = _card("Kimi K3：3 领域 × 3 档 = 9 专家", 6.6, 1.2, CYAN, WHITE, 30,
                      CARD_FILL, "BOLD")
        cMiMo = _card("MiMo V2.6：升级 MOPD 平方，前缀流盯跑偏处", 6.6, 1.4, CYAN, WHITE,
                      28, CARD_FILL, "BOLD")
        page2 = page_stack(head2, cDs1, cDs2, cDs3, cKimi, cMiMo, buff=0.35)
        layout_page(page2)

        self.at_clip("S5-c09")
        self.play(FadeOut(head1), FadeOut(cIntro), FadeOut(row1), FadeOut(row2),
                  FadeOut(row3), FadeOut(cWin), FadeOut(cEven),
                  type_in(head2, run_time=0.9), run_time=0.9)                     # 29.50 -> 30.40
        self.at_clip("S5-c10")
        self.play_scroll_unroll(cDs1, run_time=0.9)                               # 33.11 -> 34.01
        self.wait(0.2)
        self.at_clip("S5-c11")
        self.play_scroll_unroll(cDs2, run_time=0.9)                               # 38.51 -> 39.41
        self.at_clip("S5-c12")
        self.play_scroll_unroll(cDs3, run_time=0.9)                               # 42.11 -> 43.01
        self.at_clip("S5-c13")
        self.play(FadeOut(cDs1), FadeOut(cDs2), FadeOut(cDs3), run_time=0.4)      # 45.41 -> 45.81
        self.wait(0.2)
        self.play_scroll_unroll(cKimi, run_time=0.9)                              # 46.01 -> 46.91
        self.at_clip("S5-c14")
        self.play(FadeOut(cKimi), run_time=0.4)                                   # 50.22 -> 50.62
        self.wait(0.2)
        self.play_scroll_unroll(cMiMo, run_time=1.1)                              # 50.82 -> 51.92
        self.at_clip("S5-c15")
        self.play(FadeOut(cMiMo), run_time=0.4)                                   # 54.26 -> 54.66
        self.wait(0.2)
        cConv = t("三家收敛到了同一条路径", 40, YELL, "BOLD")
        self.play(type_in(cConv, run_time=1.0), run_time=1.0)                     # 54.86 -> 55.86
        self.wait(1.78)                                                           # -> 57.64
        _tout(self, head2, cConv, f, run_time=0.4)                                      # 57.64 -> 58.04
        self.pad_to_voice()


# ---------------- S6 方法论：换之前，先量距离 ----------------
class S6(_Base):
    def construct(self):
        self.bg()
        f = _footer(self)

        # 页1：量距离（c01-c05）
        head1 = _head("怎么知道同不同源？", 38)
        cGuess = t("不用猜，初始 reverse-KL 量得出来", 32, CYAN, "BOLD")
        cHow = t("换之前，先让两个模型\n对同一批 prompt 各答各的", 30, WHITE, "BOLD")
        cDist = t("量一下起始距离", 34, YELL, "BOLD")
        slotS = dynamic_slot(1.3, 0.95)
        slotC = dynamic_slot(1.3, 0.95)
        cmpRow = stable_row(t("同源", 30, GREEN, "BOLD"), slotS,
                            t("换强师", 30, RED, "BOLD"), slotC, buff=0.55)
        cVerdict = t("就是稳和崩的差别", 38, WHITE, "BOLD")
        page1 = page_stack(head1, cGuess, cHow, cDist, cmpRow, cVerdict, buff=0.7)
        layout_page(page1)

        self.at_clip("S6-c01")
        self.play(type_in(head1, run_time=0.8), run_time=0.8)                     # 0.00 -> 0.80
        self.at_clip("S6-c02")
        self.play(type_in(cGuess, run_time=0.9), run_time=0.9)                    # 1.99 -> 2.89
        self.at_clip("S6-c03")
        self.play(type_in(cHow, run_time=1.0), run_time=1.0)                      # 6.17 -> 7.17
        self.at_clip("S6-c04")
        self.play(type_in(cDist, run_time=0.8), run_time=0.8)                     # 11.15 -> 11.95
        self.wait(0.2)
        self.at_clip("S6-c05")
        self.play(FadeIn(cmpRow), run_time=0.5)                                   # 12.94 -> 13.44
        self.wait(0.2)
        nS = self.counter_value(0, 0.04, decimals=2, size=56, color=GREEN,
                                run_time=1.0, anchor=slotS)                       # 13.64 -> 14.64
        self.wait(0.2)
        nC = self.counter_value(0, 0.19, decimals=2, size=56, color=RED,
                                run_time=1.0, anchor=slotC)                       # 14.84 -> 15.84
        self.wait(0.2)
        self.play(type_in(cVerdict, run_time=0.8), run_time=0.8)                  # 16.04 -> 16.84

        # 页2：成本对比（c06-c08）
        cCheap = _card("量一次：几百条 prompt 的前向计算", 6.6, 1.5, GREEN, WHITE, 30,
                       CARD_FILL, "BOLD")
        cExpensive = _card("崩一次：整轮后训练", 6.6, 1.5, RED, WHITE, 32, CARD_FILL, "BOLD")
        cLever = t("四两拨千斤", 44, YELL, "BOLD")
        page_auto(cCheap, cExpensive, cLever)

        self.at_clip("S6-c06")
        self.play(FadeOut(head1), FadeOut(cGuess), FadeOut(cHow), FadeOut(cDist),
                  FadeOut(cmpRow), FadeOut(nS), FadeOut(nC), FadeOut(cVerdict),
                  type_in(cCheap, run_time=0.9), run_time=0.9)                    # 17.25 -> 18.15
        self.at_clip("S6-c07")
        self.play_scroll_unroll(cExpensive, run_time=0.9)                         # 22.34 -> 23.24
        self.wait(0.2)
        self.at_clip("S6-c08")
        self.play(type_in(cLever, run_time=0.9), run_time=0.9)                    # 25.18 -> 26.08
        self.wait(0.2)

        # 页3：金句 + 互动（c09-c11）
        head3 = _head("最后一句", 36)
        line9 = t("选老师不是选最强的，\n是选和学生同源的", 42, YELL, "BOLD")
        q10 = t("换老师之前，\n你会先量一下起始距离吗？", 34, CYAN, "BOLD")
        n11 = t("评论区聊聊", 30, MUTED, "BOLD")
        page_auto(head3, line9, q10, n11)

        self.at_clip("S6-c09")
        self.play(FadeOut(cCheap), FadeOut(cExpensive), FadeOut(cLever),
                  type_in(head3, run_time=0.8), run_time=0.8)                    # 27.62 -> 28.42
        self.wait(0.2)
        self.play(type_in(line9, run_time=1.1), run_time=1.1)                    # 28.62 -> 29.72
        self.wait(0.2)
        self.emphasize(line9, mode="circumscribe", run_time=0.7)                  # 29.92 -> 30.62
        self.at_clip("S6-c10")
        self.play(type_in(q10, run_time=1.0), run_time=1.0)                       # 31.19 -> 32.19
        self.at_clip("S6-c11")
        self.play(type_in(n11, run_time=0.7), run_time=0.7)                       # 34.58 -> 35.28

        # 页4：品牌尾卡（c12）
        avatar = ImageMobject(str(AVATAR))
        avatar.scale_to_fit_width(3.2)
        lFollow = t("关注「数解AI」", 40, YELL, "BOLD")
        lTitle = t("《换个更强的老师，\n模型训练为什么反而崩了？》", 30, WHITE, "BOLD")
        lGuide = t("查看公众号文章", 30, GREEN, "BOLD")
        lNext = t("下一篇：AI 改自己的代码，两周烧掉两万二", 26, MUTED, "BOLD")
        page4 = page_stack(avatar, lFollow, lTitle, lGuide, lNext, buff=0.55)
        layout_page(page4)

        self.at_clip("S6-c12")
        self.play(FadeOut(head3), FadeOut(line9), FadeOut(q10), FadeOut(n11),
                  run_time=0.5)                                                   # 35.71 -> 36.21
        self.play(FadeIn(avatar, shift=DOWN * 0.05), type_in(lNext, run_time=0.9),
                  run_time=0.9)                                                   # 36.21 -> 37.11
        self.wait(0.2)
        self.play(type_in(lFollow, run_time=0.9), type_in(lTitle, run_time=1.0),
                  type_in(lGuide, run_time=0.7), run_time=1.0)                    # 37.31 -> 38.31
        self.wait(1.81)                                                           # -> 40.12
        _tout(self, avatar, lFollow, lTitle, lGuide, lNext, f, run_time=0.4)            # 40.12 -> 40.52
        self.pad_to_voice()
