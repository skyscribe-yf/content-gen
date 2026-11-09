#!/usr/bin/env python3
"""《向量检索为什么敢随机降维？1536 维砍到 128，精度几乎不掉》视频号 Manim 动画（竖屏 1080×1920）

6 个场景 S1-S6，与 storyboard.md 一一对应（数学直觉系列，断更 3 个月重启第一期）。
- 配音：MiniMax 精英男声（speech-2.8-turbo，speed 1.0，pitch +2）
- 时间轴：at_clip("Sx-cNN") 挂 tts/sentence-boundaries.json 的 clip 起点（先声音后动画门禁）
- 布局：整页规划（page_stack + layout_page / page_auto），上下留白各 ≤ 10%，整页宽 ≤ 8.0
- 动画降噪（决策 #51）：emphasize 全片 3 次（S1 存储对比条 / S3「没有 D」/ S4 576 vs 32768），
  v2 动效 1 处（S3 camera_zoom_to 推近「指数吃多项式」金句，成对）；每页 1 个主视觉动效；
  数字台词全部配 counter_value / grow_bar

⚠️ 段边界修正记录（2026-11-09）：MiniMax 官方时间戳把 S3 尾句与 S4 首句并入同一粗句
  （107.459-124.124）、S4 尾句与 S5 首句并入同一粗句（163.058-173.837），tts_split 中点
  启发式切错 4-7 秒。已按 silencedetect 真实停顿（111.95 / 170.145）重切 s3/s4/s5 并重算
  sentence-boundaries.json（含跨段伪句拆分）。本文件 VOICE_DUR 与重切后 ffprobe 实测一致。

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

# 每段配音时长（重切后 ffprobe 实测），渲染时长 = 配音 + TAIL
# ⚠️ TAIL 必须等于 build 脚本的 --tail（默认 0.1）；尾卡停留用显式 self.wait()，不靠加大 TAIL
VOICE_DUR = {"S1": 22.955, "S2": 37.547, "S3": 51.590, "S4": 58.195, "S5": 49.315, "S6": 57.963}
TAIL = 0.1


def _footer(self) -> Text:
    f = t("数解AI · 数学直觉", 20, MUTED).to_edge(DOWN, buff=1.15)
    self.add(f)
    return f


def _scene_out(self, *mobs):
    """场景收尾：整页纯淡出（2026-11-09 用户拍板：滑出过渡太难看了，改淡出淡入）。

    替代 manim_helpers.transition_out（右下滑出+淡出）。传当前场景全部可见元素
    （含 head/footer），淡出后 remove，末尾仍由 pad_to_voice 兜底。
    """
    self.play(*[FadeOut(m, run_time=0.6) for m in mobs], run_time=0.6)
    self.remove(*mobs)


def _head(text: str, size: float = 38) -> Text:
    return t(text, size, YELL, "BOLD").to_edge(UP, buff=1.2)


def _img(name: str, width: float) -> ImageMobject:
    im = ImageMobject(str(IMG / name))
    im.scale_to_fit_width(width)
    return im


def _bar_row(lab_text: str, bar_w: float, track_w: float, color: str,
             val_text: str, val_color: str, lab_fs: float = 26) -> VGroup:
    """存储账对比行：左标签 + 定长轨道（左对齐生长的实心条）+ 右端数值。条按最终几何摆好。"""
    track = Rectangle(width=track_w, height=0.78, color=MUTED, stroke_width=1.5, fill_opacity=0)
    bar = Rectangle(width=bar_w, height=0.78, color=color,
                    fill_color=color, fill_opacity=0.8)
    bar.move_to(track.get_center())
    bar.align_to(track, LEFT)
    lab = t(lab_text, lab_fs, WHITE, "BOLD")
    lab.next_to(track, LEFT, buff=0.30)
    val = t(val_text, 24, val_color, "BOLD")
    val.next_to(track, RIGHT, buff=0.30)
    val.align_to(track, DOWN)
    return VGroup(lab, track, bar, val)


def _num_row(lab_text: str, slot_w: float = 1.8, lab_fs: float = 26) -> tuple[VGroup, Rectangle]:
    """纯数字行：左标签 + 透明槽位（counter_value anchor 用）。"""
    lab = t(lab_text, lab_fs, WHITE, "BOLD")
    slot = dynamic_slot(slot_w, 0.9)
    row = stable_row(lab, slot, buff=0.45)
    return row, slot


def _pipe_box(label: str, w: float = 1.55, h: float = 1.05, fs: float = 24) -> VGroup:
    """流水线/结构单步：圆角实心小卡（CARD_FILL）+ 居中限宽文字。"""
    box = RoundedRectangle(corner_radius=0.18, width=w, height=h,
                           color=CYAN, fill_color=CARD_FILL, fill_opacity=1.0,
                           stroke_width=2)
    txt = t(label, fs, WHITE, "BOLD")
    if txt.width > box.width * 0.78:
        txt.set_width(box.width * 0.78)
    txt.move_to(box.get_center())
    return VGroup(box, txt)


# ---------------- S1 开场钩子：1536 砍到 128，精度不掉 ----------------
class S1(_Base):
    def construct(self):
        self.bg()
        f = _footer(self)

        # 页1：存储账（c01-c05）
        head = _head("1536 砍到 128，精度不掉？", 36)
        note = t("以 RAG 向量检索为例", 24, MUTED)
        sub = t("潜规则：先砍维度，再建索引", 28, WHITE, "BOLD")
        row1 = _bar_row("1536 维", 3.6, 3.6, YELL, "600MB+", YELL)
        row2 = _bar_row("128 维", 0.30, 3.6, CYAN, "50MB", CYAN)
        card = _card("精度，几乎不掉", 5.6, 2.1, YELL, WHITE, 34, CARD_FILL, "BOLD")
        page1 = page_stack(note, sub, row1, row2, card, buff=0.72)
        layout_page(page1)

        self.at_clip("S1-c01")
        self.play(type_in(head, run_time=1.0), type_in(note, run_time=0.7),
                  run_time=1.0)                                   # 0.00 -> 1.00（A12 开场小字同拍）
        self.at_clip("S1-c03")
        self.grow_bar(row1[2], ValueTracker(0), 3.6, run_time=1.0, anchor="center",
                      extra_anims=[type_in(sub, run_time=0.8)])   # 7.52 -> 8.52
        self.at_clip("S1-c04")
        self.grow_bar(row2[2], ValueTracker(0), 0.30, run_time=0.8, anchor="center",
                      extra_anims=[type_in(row1[0], run_time=0.5), type_in(row1[3], run_time=0.5),
                                   type_in(row2[0], run_time=0.5), type_in(row2[3], run_time=0.5)])  # 13.07 -> 13.87
        self.at_clip("S1-c05")
        self.play_scroll_unroll(card, run_time=1.2)               # 16.31 -> 17.51
        self.emphasize(VGroup(row1[2], row2[2]), run_time=0.6)    # 17.51 -> 18.11（对比条，强调 1/3）

        # 页2：悬念（c06-c07）
        line1 = t("凭什么？", 46, WHITE, "BOLD")
        line2 = t("1984 年的一个定理", 46, YELL, "BOLD")
        page2 = page_auto(line1, line2)

        self.at_clip("S1-c06")
        self.play(FadeOut(head), FadeOut(note), FadeOut(sub), FadeOut(row1), FadeOut(row2),
                  FadeOut(card), type_in(line1, run_time=0.8), run_time=0.8)  # 18.16 -> 18.96
        self.at_clip("S1-c07")
        self.play(type_in(line2, run_time=0.9), run_time=0.9)     # 19.08 -> 19.98
        self.wait(2.48)
        _scene_out(self, line1, line2, f)                      # 22.46 -> 23.06
        self.pad_to_voice()


# ---------------- S2 随机拍扁，距离为什么还在 ----------------
class S2(_Base):
    def construct(self):
        self.bg()
        f = _footer(self)

        # 页1：一把随机矩阵就够了（c01-c04）
        head = _head("一把随机矩阵就够了", 38)
        img = _img("s2-projection-round.png", 3.0)
        card1984 = _card("1984 · Johnson 和 Lindenstrauss", 5.6, 1.3, CYAN, WHITE, 30, CARD_FILL, "BOLD")
        card3 = _card("不用挑方向\n不用看数据\n不用训练", 5.2, 2.0, GREEN, WHITE, 32, CARD_FILL, "BOLD")
        page1 = page_stack(img, card1984, card3, buff=0.72)
        layout_page(page1)

        self.at_clip("S2-c01")
        self.play(type_in(head, run_time=1.0), FadeIn(img, shift=DOWN * 0.05),
                  run_time=1.0)                                   # 0.10 -> 1.10
        self.at_clip("S2-c02")
        self.play_scroll_unroll(card1984, run_time=1.1)           # 8.59 -> 9.69
        self.at_clip("S2-c04")
        self.play_scroll_unroll(card3, run_time=1.2)              # 13.75 -> 14.95

        # 页2：大数定律（c05-c07）
        head2 = _head("凭什么？大数定律", 38)
        arrows = VGroup()
        rng = [(1.0, 0.15), (0.75, 0.66), (0.1, 1.0), (-0.6, 0.8),
               (-1.0, 0.1), (-0.7, -0.7), (0.0, -1.05), (0.65, -0.75)]
        cols = [YELL, CYAN, GREEN, YELL, CYAN, GREEN, YELL, CYAN]
        for (dx, dy), c in zip(rng, cols):
            arrows.add(Arrow(ORIGIN, np.array([dx, dy, 0]) * 1.3, color=c,
                             stroke_width=5, buff=0).set_opacity(0.85))
        arrows.move_to(ORIGIN)
        avg = Arrow(ORIGIN, RIGHT * 1.7, color=RED, stroke_width=9, buff=0)
        avg_lab = t("平均", 26, RED, "BOLD")
        avg_lab.next_to(avg, RIGHT, buff=0.22)
        avg_g = VGroup(avg, avg_lab)
        visual = VGroup(arrows, avg_g)
        card_lln = _card("每个坐标，都是大量\n独立小随机量的平均", 5.6, 2.4, YELL, WHITE, 32, CARD_FILL, "BOLD")
        note = t("平均会往一个值收敛", 26, MUTED)
        page2 = page_stack(visual, card_lln, note, buff=0.85)
        layout_page(page2)

        self.at_clip("S2-c05")
        self.play(FadeOut(head), FadeOut(img), FadeOut(card1984), FadeOut(card3),
                  type_in(head2, run_time=0.9), run_time=0.8)     # 17.29 -> 18.09
        self.at_clip("S2-c06")
        self.play(FadeIn(arrows, shift=DOWN * 0.05), run_time=1.0)  # 18.12 -> 19.12（主视觉）
        self.at_clip("S2-c07")
        self.play(GrowArrow(avg), type_in(avg_lab, run_time=0.5), type_in(note, run_time=0.7),
                  run_time=0.8)                                   # 23.31 -> 24.11
        self.play_scroll_unroll(card_lln, run_time=1.0)           # 24.11 -> 25.11

        # 页3：高维薄壳（c08）
        l1 = t("高维还有层加持：", 42, WHITE, "BOLD")
        l2 = t("能量本来就集中在薄壳上", 42, YELL, "BOLD")
        page3 = page_auto(l1, l2)

        self.at_clip("S2-c08")
        self.play(FadeOut(head2), FadeOut(arrows), FadeOut(avg_g), FadeOut(card_lln), FadeOut(note),
                  type_in(l1, run_time=0.9), run_time=0.9)        # 27.67 -> 28.57
        self.play(type_in(l2, run_time=0.9), run_time=0.9)        # 28.57 -> 29.47

        # 页4：悬念（c09-c10）
        l3 = t("可这，只是一对点的保证", 44, WHITE, "BOLD")
        l4 = t("全部数据点，怎么办？", 44, YELL, "BOLD")
        page4 = page_auto(l3, l4)

        self.at_clip("S2-c09")
        self.play(FadeOut(l1), FadeOut(l2), type_in(l3, run_time=0.9), run_time=0.9)  # 32.83 -> 33.73
        self.at_clip("S2-c10")
        self.play(type_in(l4, run_time=0.9), run_time=0.9)        # 35.31 -> 36.21
        self.wait(0.84)
        _scene_out(self, l3, l4, f)                            # 37.05 -> 37.65
        self.pad_to_voice()


# ---------------- S3 公式里没有 D ----------------
class S3(_Base):
    def construct(self):
        self.bg()
        f = _footer(self)

        # 页1：点对网 + 并集界（c01-c04）
        head = _head("把全部点对管起来", 38)
        pts = [(-2.3, 0.9), (-1.2, 1.5), (0.1, 1.1), (1.4, 1.5),
               (-2.0, -0.4), (-0.8, -0.1), (0.6, -0.5), (1.8, -0.2), (-1.5, -1.4), (0.4, -1.5)]
        dots = VGroup(*[Dot(point=[x, y, 0], radius=0.11, color=YELL) for x, y in pts])
        pairs = [(0, 4), (1, 5), (2, 5), (3, 7), (4, 8), (5, 9), (6, 9), (0, 1), (2, 6), (7, 3)]
        lines = VGroup(*[Line(dots[i].get_center(), dots[j].get_center(),
                              color=CYAN, stroke_width=2).set_opacity(0.55)
                          for i, j in pairs])
        net = VGroup(dots, lines)
        card1 = _card("点对数 = N² / 2", 5.2, 1.4, CYAN, WHITE, 34, CARD_FILL, "BOLD")
        card2 = _card("并集界：各自概率\n直接相加，永远成立", 5.6, 1.9, GREEN, WHITE, 30, CARD_FILL, "BOLD")
        page1 = page_stack(net, card1, card2, buff=0.72)
        layout_page(page1)

        self.at_clip("S3-c01")
        self.play(type_in(head, run_time=1.0))                    # 0.10 -> 1.10
        self.at_clip("S3-c02")
        self.play(FadeIn(dots, shift=DOWN * 0.05), Create(lines, lag_ratio=0.25),
                  run_time=1.4)                                   # 2.02 -> 3.42（主视觉）
        self.at_clip("S3-c03")
        self.play_scroll_unroll(card1, run_time=1.1)              # 5.23 -> 6.33
        self.at_clip("S3-c04")
        self.play_scroll_unroll(card2, run_time=1.2)              # 8.01 -> 9.21

        # 页2：指数吃多项式（c05-c06）
        head2 = _head("两个增长速度", 40)
        cardA = _card("坏事件：多项式增加", 5.8, 1.7, RED, WHITE, 30, CARD_FILL, "BOLD")
        cardB = _card("失败概率：按指数衰减", 5.8, 1.7, GREEN, WHITE, 30, CARD_FILL, "BOLD")
        punch = t("指数吃多项式", 52, YELL, "BOLD")
        note = t("所以随机够用", 26, MUTED)
        page2 = page_stack(cardA, cardB, punch, note, buff=0.90)
        layout_page(page2)

        self.at_clip("S3-c05")
        self.play(FadeOut(head), FadeOut(dots), FadeOut(lines), FadeOut(card1), FadeOut(card2),
                  type_in(head2, run_time=0.9), run_time=0.9)     # 13.45 -> 14.35
        self.play_scroll_unroll(cardA, run_time=1.0)              # 14.35 -> 15.35
        self.at_clip("S3-c06")
        self.play_scroll_unroll(cardB, run_time=1.0)              # 18.16 -> 19.16
        self.play(type_in(punch, run_time=1.0), type_in(note, run_time=0.7),
                  run_time=1.0)                                   # 19.16 -> 20.16（主视觉）
        self.camera_zoom_to(punch, run_time=0.35)                 # 20.16 -> 20.51（v2 动效 1/3：推近）
        self.camera_zoom_to(run_time=0.35)                        # 20.51 -> 20.86（拉回，成对；< c07 20.98）

        # 页3：投影维度公式（c07-c10）
        head3 = _head("投影维度 k 怎么定？", 36)
        formula = MathTex(r"k = O(\varepsilon^{-2} \ln N)",
                          tex_to_color_map={r"\varepsilon^{-2}": YELL, r"\ln N": CYAN})
        formula.set_width(5.6)
        cardD = _card("注意：这个公式里\n没有 D", 5.2, 1.9, YELL, WHITE, 34, CARD_FILL, "BOLD")
        cardE = _card("1 万维 = 100 亿维\n目标维度，一个样", 5.6, 1.9, GREEN, WHITE, 32, CARD_FILL, "BOLD")
        note3 = t("误差越小、点越多，k 越大", 26, MUTED)
        page3 = page_stack(formula, cardD, cardE, note3, buff=0.72)
        layout_page(page3)

        self.at_clip("S3-c07")
        self.play(FadeOut(head2), FadeOut(cardA), FadeOut(cardB), FadeOut(punch), FadeOut(note),
                  type_in(head3, run_time=0.9), run_time=0.9)     # 20.98 -> 21.88
        self.play(FadeIn(formula), run_time=0.9)                  # 21.88 -> 22.78（公式照写，TTS 已口语化）
        self.at_clip("S3-c09")
        self.play_scroll_unroll(cardD, run_time=1.2)              # 26.62 -> 27.82
        self.emphasize(cardD, run_time=0.7)                       # 27.82 -> 28.52（「没有 D」，强调 2/3）
        self.at_clip("S3-c10")
        self.play(type_in(cardE, run_time=0.9), type_in(note3, run_time=0.7), run_time=0.9)  # 29.43 -> 30.33

        # 页4：算账（c11-c13）
        head4 = _head("算一笔诚实的账", 38)
        rowA, slotA = _num_row("容忍一成误差")
        rowB, slotB = _num_row("放松到三成")
        cardF = _card("压缩比的上限\n被点的个数锁死，不被维度锁死", 5.8, 2.7, YELL, WHITE, 32, CARD_FILL, "BOLD")
        note4 = t("10 万个点 · 点对数 N² / 2", 26, MUTED)
        page4 = page_stack(rowA, rowB, cardF, note4, buff=0.80)
        layout_page(page4)

        self.at_clip("S3-c11")
        self.play(FadeOut(head3), FadeOut(formula), FadeOut(cardD), FadeOut(cardE), FadeOut(note3),
                  type_in(head4, run_time=0.9), type_in(note4, run_time=0.7), run_time=0.9)  # 34.57 -> 35.47
        n1 = self.counter_value(0, 5000, suffix=" 维", size=52, color=YELL, run_time=1.0,
                                anchor=slotA, extra_anims=[type_in(rowA[0], run_time=0.6)])  # 35.47 -> 36.47
        self.at_clip("S3-c12")
        n2 = self.counter_value(0, 640, suffix=" 维", size=52, color=CYAN, run_time=1.0,
                                anchor=slotB, extra_anims=[type_in(rowB[0], run_time=0.6)])   # 39.71 -> 40.71
        self.at_clip("S3-c13")
        self.play_scroll_unroll(cardF, run_time=1.3)              # 42.79 -> 44.09

        # 页5：悬念（c14）
        l1 = t("既然随机这么好，", 44, WHITE, "BOLD")
        l2 = t("DeepSeek 为什么还要费劲学投影？", 40, YELL, "BOLD")
        page5 = page_auto(l1, l2)

        self.at_clip("S3-c14")
        self.play(FadeOut(head4), FadeOut(rowA), FadeOut(rowB), FadeOut(cardF), FadeOut(note4),
                  FadeOut(n1), FadeOut(n2),
                  type_in(l1, run_time=0.9), run_time=0.9)        # 47.10 -> 48.00
        self.play(type_in(l2, run_time=0.9), run_time=0.9)        # 48.00 -> 48.90
        self.wait(2.19)
        _scene_out(self, l1, l2, f)                            # 51.09 -> 51.69
        self.pad_to_voice()


# ---------------- S4 随机 ≥ 精心设计，但学习又赢过随机 ----------------
class S4(_Base):
    def construct(self):
        self.bg()
        f = _footer(self)

        # 页1：三条路线（c01-c06）
        head = _head("随机 ≥ 精心设计？", 38)
        cPCA = _card("PCA：先看数据\n算协方差、分解矩阵", 5.8, 1.7, MUTED, WHITE, 30, CARD_FILL, "BOLD")
        cJL = _card("JL：一把随机矩阵\n最坏情况也成立", 5.8, 1.7, YELL, WHITE, 32, CARD_FILL, "BOLD")
        cMLA = _card("MLA：投影矩阵\n端到端学出来", 5.8, 1.7, CYAN, WHITE, 32, CARD_FILL, "BOLD")
        note = t("三条路线，一个目标：压维度", 26, MUTED)
        page1 = page_stack(cPCA, cJL, cMLA, note, buff=0.62)
        layout_page(page1)

        self.at_clip("S4-c01")
        self.play(type_in(head, run_time=1.0))                    # 0.00 -> 1.00
        self.at_clip("S4-c03")
        self.play_scroll_unroll(cPCA, run_time=1.1)               # 5.33 -> 6.43
        self.at_clip("S4-c05")
        self.play_scroll_unroll(cJL, run_time=1.2)                # 12.37 -> 13.57
        self.at_clip("S4-c06")
        self.play_scroll_unroll(cMLA, run_time=1.1)               # 16.54 -> 17.64

        # 页2：维度的祝福（c07-c08）
        l1 = t("人类的朴素直觉", 44, WHITE, "BOLD")
        l2 = t("对随机性错得离谱", 44, WHITE, "BOLD")
        l3 = t("高维结构，比想象中规整得多", 36, YELL, "BOLD")
        page2 = page_auto(l1, l2, l3)

        self.at_clip("S4-c07")
        self.play(FadeOut(head), FadeOut(cPCA), FadeOut(cJL), FadeOut(cMLA), FadeOut(note),
                  type_in(l1, run_time=0.9), run_time=0.9)        # 19.46 -> 20.36
        self.play(type_in(l2, run_time=0.9), run_time=0.9)        # 20.36 -> 21.26
        self.at_clip("S4-c08")
        self.play(type_in(l3, run_time=0.9), run_time=0.9)        # 23.00 -> 23.90

        # 页3a：MLA 结构（c09-c12）
        head3 = _head("但先别把随机捧上天", 36)
        card0 = _card("随机是下限，不代表最优", 5.6, 1.2, RED, WHITE, 30, CARD_FILL, "BOLD")
        card_mla = _card("投影矩阵不随机\n端到端学出来", 5.6, 1.7, CYAN, WHITE, 32, CARD_FILL, "BOLD")
        bK = _pipe_box("K", w=1.2)
        bV = _pipe_box("V", w=1.2)
        kv = VGroup(bK, bV).arrange(DOWN, buff=0.25)
        bLat = _pipe_box("512 维隐向量", w=2.6)
        bRope = _pipe_box("64 维旁路", w=2.6)
        out = VGroup(bLat, bRope).arrange(DOWN, buff=0.25)
        arr = Arrow(kv.get_right(), out.get_left(), color=YELL, stroke_width=4, buff=0.15)
        diagram = VGroup(kv, arr, out)
        note_a = t("每个 token 的 K/V，压成隐向量", 24, MUTED)
        page3 = page_stack(card0, card_mla, diagram, note_a, buff=0.80)
        layout_page(page3)

        self.at_clip("S4-c09")
        self.play(FadeOut(l1), FadeOut(l2), FadeOut(l3),
                  type_in(head3, run_time=0.9), run_time=0.9)     # 28.40 -> 29.30
        self.at_clip("S4-c10")
        self.play_scroll_unroll(card0, run_time=1.0)              # 30.31 -> 31.31
        self.at_clip("S4-c11")
        self.play(type_in(card_mla, run_time=0.9), run_time=0.9)  # 32.19 -> 33.09
        self.at_clip("S4-c12")
        self.play(FadeIn(diagram, shift=DOWN * 0.05), type_in(note_a, run_time=0.7),
                  run_time=1.0)                                   # 37.10 -> 38.10（主视觉）

        # 页3b：MLA 的账（c13-c15）
        head3b = _head("缓存里，只存多少个数？", 34)
        rowA, slotA = _num_row("MLA 缓存")
        rowB, slotB = _num_row("全量 K / V")
        card57 = _card("省了约 57 倍", 5.6, 1.6, YELL, WHITE, 36, CARD_FILL, "BOLD")
        card2 = _card("512 维就够\n还顺带做了任务相关的特征选择", 5.6, 1.9, GREEN, WHITE, 30, CARD_FILL, "BOLD")
        page4 = page_stack(rowA, rowB, card57, card2, buff=0.75)
        layout_page(page4)

        self.at_clip("S4-c13")
        self.play(FadeOut(head3), FadeOut(card0), FadeOut(card_mla), FadeOut(diagram),
                  FadeOut(note_a), type_in(head3b, run_time=0.9), run_time=0.9)  # 42.05 -> 42.95
        n1 = self.counter_value(0, 576, suffix=" 个", size=48, color=CYAN, run_time=0.9,
                                anchor=slotA, extra_anims=[type_in(rowA[0], run_time=0.5)])  # 42.95 -> 43.85
        self.at_clip("S4-c14")
        n2 = self.counter_value(0, 32768, suffix=" 个", size=48, color=RED, run_time=1.2,
                                anchor=slotB, extra_anims=[type_in(rowB[0], run_time=0.5)])   # 46.37 -> 47.57
        self.emphasize(VGroup(n1, n2), run_time=0.7)              # 47.57 -> 48.27（576 vs 32768，强调 3/3）
        self.at_clip("S4-c15")
        self.play_scroll_unroll_many(card57, card2, run_time=1.3)  # 51.11 -> 52.41（两卡同拍等宽）

        # 页4：悬念（c16）
        l4 = t("这套随机功夫，", 44, WHITE, "BOLD")
        l5 = t("工程界早就用成了日常", 44, YELL, "BOLD")
        page5 = page_auto(l4, l5)

        self.at_clip("S4-c16")
        self.play(FadeOut(head3b), FadeOut(rowA), FadeOut(rowB), FadeOut(card57), FadeOut(card2),
                  FadeOut(n1), FadeOut(n2),
                  type_in(l4, run_time=0.8), run_time=0.8)        # 55.01 -> 55.81
        self.play(type_in(l5, run_time=0.8), run_time=0.8)        # 55.81 -> 56.61
        self.wait(1.09)
        _scene_out(self, l4, l5, f)                            # 57.70 -> 58.30
        self.pad_to_voice()


# ---------------- S5 工程里干活的「随机」 ----------------
class S5(_Base):
    def construct(self):
        self.bg()
        f = _footer(self)

        # 页1：RaBitQ 流水线（c01-c05）
        head = _head("RaBitQ：随机旋转，压成 1 bit", 32)
        note = t("SIGMOD 2024 · 距离估计无偏、带误差界", 24, MUTED)
        b1 = _pipe_box("归一化")
        b2 = _pipe_box("随机旋转")
        b3 = _pipe_box("取符号")
        b4 = _pipe_box("1 bit 位串")
        boxes = VGroup(b1, b2, b3, b4).arrange(RIGHT, buff=0.55)
        a1 = Arrow(b1.get_right(), b2.get_left(), color=YELL, stroke_width=4, buff=0.15)
        a2 = Arrow(b2.get_right(), b3.get_left(), color=YELL, stroke_width=4, buff=0.15)
        a3 = Arrow(b3.get_right(), b4.get_left(), color=YELL, stroke_width=4, buff=0.15)
        arrows = VGroup(a1, a2, a3)
        pipe = VGroup(boxes, arrows)
        card_a = _card("每个向量，只剩一个位串", 5.6, 1.4, CYAN, WHITE, 32, CARD_FILL, "BOLD")
        row3, slot3 = _num_row("单条查询比 PQ 快约")
        card_b = _card("PQ：完全没有理论保证", 5.6, 1.4, RED, WHITE, 32, CARD_FILL, "BOLD")
        page1 = page_stack(pipe, card_a, row3, card_b, note, buff=0.58)
        layout_page(page1)

        self.at_clip("S5-c01")
        self.play(type_in(head, run_time=1.0), type_in(note, run_time=0.7),
                  run_time=1.0)                                   # 0.00 -> 1.00
        self.at_clip("S5-c02")
        self.play(*[DrawBorderThenFill(b, run_time=0.5) for b in boxes],
                  *[Create(a) for a in arrows], lag_ratio=0.3, run_time=2.2)  # 3.79 -> 5.99（逐步，主视觉）
        self.at_clip("S5-c03")
        self.play_scroll_unroll(card_a, run_time=1.1)             # 7.79 -> 8.89
        self.at_clip("S5-c04")
        n3 = self.counter_value(0, 3, suffix=" 倍", size=52, color=YELL, run_time=1.0,
                                anchor=slot3, extra_anims=[type_in(row3[0], run_time=0.6)])  # 12.15 -> 13.15
        self.at_clip("S5-c05")
        self.play_scroll_unroll(card_b, run_time=1.1)             # 16.52 -> 17.62

        # 页2：TurboQuant（c06-c08）
        head2 = _head("TurboQuant：同一个套路", 34)
        note2 = t("2026 年 3 月出圈 · 随机旋转 + 量化残差修正", 24, MUTED)
        img = _img("s5-turbo-round.png", 3.0)
        row4, slot4 = _num_row("全球存储股市值单日蒸发", slot_w=2.6)
        card900 = _card("一篇论文，砸掉 900 多亿美元", 5.8, 1.6, YELL, WHITE, 32, CARD_FILL, "BOLD")
        page2 = page_stack(img, row4, card900, note2, buff=0.68)
        layout_page(page2)

        self.at_clip("S5-c06")
        self.play(FadeOut(head), FadeOut(pipe), FadeOut(card_a), FadeOut(row3), FadeOut(n3),
                  FadeOut(card_b), FadeOut(note),
                  type_in(head2, run_time=0.9), type_in(note2, run_time=0.7), run_time=0.9)  # 19.08 -> 19.98
        self.play(FadeIn(img, shift=DOWN * 0.05), run_time=0.8)   # 19.98 -> 20.78（概念图）
        self.at_clip("S5-c07")
        n4 = self.counter_value(0, 900, suffix=" 多亿美元", size=48, color=YELL, run_time=1.2,
                                anchor=slot4, extra_anims=[type_in(row4[0], run_time=0.6)])  # 22.14 -> 23.34
        self.at_clip("S5-c08")
        self.play_scroll_unroll(card900, run_time=1.2)            # 25.54 -> 26.74

        # 页3：同一招跨到模型侧（c09-c11）
        head3 = _head("同一招，跨到模型侧", 36)
        note3 = t("离群值：权重里的尖刺", 24, MUTED)
        c1 = _card("QuIP 系列和 QuaRot", 5.6, 1.4, CYAN, WHITE, 32, CARD_FILL, "BOLD")
        c2 = _card("随机 Hadamard 旋转\n削平权重的离群值", 5.6, 1.9, GREEN, WHITE, 30, CARD_FILL, "BOLD")
        c3 = _card("4 bit 量化，才得以成立", 5.6, 1.4, YELL, WHITE, 32, CARD_FILL, "BOLD")
        page3 = page_stack(c1, c2, c3, note3, buff=0.70)
        layout_page(page3)

        self.at_clip("S5-c09")
        self.play(FadeOut(head2), FadeOut(img), FadeOut(row4), FadeOut(n4), FadeOut(card900),
                  FadeOut(note2),
                  type_in(head3, run_time=0.9), type_in(note3, run_time=0.7), run_time=0.9)  # 27.44 -> 28.34
        self.play_scroll_unroll(c1, run_time=1.0)                 # 28.34 -> 29.34
        self.at_clip("S5-c10")
        self.play_scroll_unroll(c2, run_time=1.1)                 # 32.10 -> 33.20
        self.at_clip("S5-c11")
        self.play_scroll_unroll(c3, run_time=1.0)                 # 36.20 -> 37.20

        # 页4：金句 + 悬念（c12-c14）
        l1 = t("从词嵌入，到向量库，再到权重量化", 36, WHITE, "BOLD")
        l2 = t("同一条数学原理，四处开花", 42, YELL, "BOLD")
        page4 = page_auto(l1, l2)

        self.at_clip("S5-c12")
        self.play(FadeOut(head3), FadeOut(c1), FadeOut(c2), FadeOut(c3), FadeOut(note3),
                  type_in(l1, run_time=0.9), run_time=0.9)        # 38.53 -> 39.43
        self.play(type_in(l2, run_time=0.9), run_time=0.9)        # 39.43 -> 40.33

        l3 = t("那 1536 砍到 128，", 44, WHITE, "BOLD")
        l4 = t("是不是砍就完了？", 44, YELL, "BOLD")
        page5 = page_auto(l3, l4)

        self.at_clip("S5-c14")
        self.play(FadeOut(l1), FadeOut(l2), type_in(l3, run_time=0.8), run_time=0.8)  # 45.07 -> 45.87
        self.play(type_in(l4, run_time=0.8), run_time=0.8)        # 45.87 -> 46.67
        self.wait(2.15)
        _scene_out(self, l3, l4, f)                            # 48.82 -> 49.42
        self.pad_to_voice()


# ---------------- S6 泼冷水 + 三层答案 + 尾卡 ----------------
class S6(_Base):
    def construct(self):
        self.bg()
        f = _footer(self)

        # 页1：128 维不是万能截断（c01-c03）
        head = _head("128 维，不是万能截断", 36)
        img = _img("s6-matryoshka-round.png", 2.9)
        card = _card("1536 砍到 128 不掉点\n不是单靠 JL", 5.8, 1.7, YELL, WHITE, 32, CARD_FILL, "BOLD")
        card2 = _card("要靠 Matryoshka 训练\n学出来的截断才友好", 5.8, 1.9, GREEN, WHITE, 30, CARD_FILL, "BOLD")
        page1 = page_stack(img, card, card2, buff=0.72)
        layout_page(page1)

        self.at_clip("S6-c01")
        self.play(type_in(head, run_time=1.0), FadeIn(img, shift=DOWN * 0.05),
                  run_time=1.0)                                   # 0.10 -> 1.10
        self.at_clip("S6-c02")
        self.play_scroll_unroll(card, run_time=1.1)               # 5.06 -> 6.16
        self.at_clip("S6-c03")
        self.play_scroll_unroll(card2, run_time=1.1)              # 9.82 -> 10.92

        # 页2：官方警告（c04-c06）
        head2 = _head("官方文档的警告", 38)
        note = t("text-embedding-3 有 dimensions 参数", 24, MUTED)
        cardA = _card("Azure：配二进制量化\n低于 1000 维，搜索质量还是会下降", 5.8, 2.4, RED, WHITE, 30, CARD_FILL, "BOLD")
        cardB = _card("OpenAI：截断后\n必须在自己数据上实测", 5.8, 2.4, CYAN, WHITE, 30, CARD_FILL, "BOLD")
        page2 = page_stack(cardA, cardB, note, buff=0.98)
        layout_page(page2)

        self.at_clip("S6-c04")
        self.play(FadeOut(head), FadeOut(img), FadeOut(card), FadeOut(card2),
                  type_in(head2, run_time=0.9), type_in(note, run_time=0.7), run_time=0.9)  # 11.93 -> 12.83
        self.play_scroll_unroll(cardA, run_time=1.2)              # 12.83 -> 14.03
        self.at_clip("S6-c06")
        self.play_scroll_unroll(cardB, run_time=1.1)              # 19.53 -> 20.63

        # 页3：三层答案（c07-c08）
        head3 = _head("完整的答案，分三层", 38)
        c1 = _card("随机：给下界", 5.6, 1.9, YELL, WHITE, 34, CARD_FILL, "BOLD")
        c2 = _card("旋转：给工程可行性", 5.6, 1.9, CYAN, WHITE, 34, CARD_FILL, "BOLD")
        c3 = _card("学习训练：给优化路径", 5.6, 1.9, GREEN, WHITE, 34, CARD_FILL, "BOLD")
        page3 = page_stack(c1, c2, c3, buff=0.85)
        layout_page(page3)

        self.at_clip("S6-c07")
        self.play(FadeOut(head2), FadeOut(cardA), FadeOut(cardB), FadeOut(note),
                  type_in(head3, run_time=0.9), run_time=0.9)     # 23.05 -> 23.95
        self.play_scroll_unroll(c1, run_time=1.0)                 # 23.95 -> 24.95
        self.at_clip("S6-c08")
        self.play_scroll_unroll_many(c2, c3, run_time=1.2)        # 26.91 -> 28.11（两层同拍）

        # 页4：回到开头的账（c09-c10）
        head4 = _head("回到开头的账", 38)
        img2 = _img("s2-projection-round.png", 3.8)
        row1 = _bar_row("1536 维", 3.6, 3.6, YELL, "600MB+", YELL)
        row2 = _bar_row("128 维", 0.30, 3.6, CYAN, "50MB", CYAN)
        line2 = t("现在每一层，都敢这么算", 36, YELL, "BOLD")
        page4 = page_stack(img2, row1, row2, line2, buff=0.65)
        layout_page(page4)

        self.at_clip("S6-c09")
        self.play(FadeOut(head3), FadeOut(c1), FadeOut(c2), FadeOut(c3),
                  type_in(head4, run_time=0.9), run_time=0.9)     # 30.98 -> 31.88
        self.grow_bar(row1[2], ValueTracker(0), 3.6, run_time=0.9, anchor="center",
                      extra_anims=[FadeIn(img2, shift=DOWN * 0.05), type_in(row1[0], run_time=0.5),
                                   type_in(row1[3], run_time=0.5)])  # 31.88 -> 32.78
        self.at_clip("S6-c10")
        self.grow_bar(row2[2], ValueTracker(0), 0.30, run_time=0.8, anchor="center",
                      extra_anims=[type_in(row2[0], run_time=0.5), type_in(row2[3], run_time=0.5),
                                   type_in(line2, run_time=0.7)])  # 35.05 -> 35.85

        # 页5：互动（c11-c13）
        l1 = t("下次你的 embedding", 42, WHITE, "BOLD")
        l2 = t("再吐出 1536 维，", 42, WHITE, "BOLD")
        l3 = t("先问自己一句：", 42, WHITE, "BOLD")
        l4 = t("这个数，是非要不可，", 42, YELL, "BOLD")
        l5 = t("还是默认值无脑拿来的？", 42, YELL, "BOLD")
        page5 = page_auto(l1, l2, l3, l4, l5)

        self.at_clip("S6-c11")
        self.play(FadeOut(head4), FadeOut(img2), FadeOut(row1), FadeOut(row2), FadeOut(line2),
                  type_in(l1, run_time=0.8), run_time=0.8)        # 37.83 -> 38.63
        self.play(type_in(l2, run_time=0.8), run_time=0.8)        # 38.63 -> 39.43
        self.at_clip("S6-c12")
        self.play(type_in(l3, run_time=0.8), run_time=0.8)        # 41.85 -> 42.65
        self.at_clip("S6-c13")
        self.play(type_in(l4, run_time=0.8), type_in(l5, run_time=0.8),
                  run_time=0.8)                                   # 44.96 -> 45.76（两行同拍）

        q1 = t("做 RAG，你在维度和存储之间怎么平衡？", 30, WHITE, "BOLD")
        q2 = t("评论区聊聊", 34, YELL, "BOLD")
        page6 = page_auto(q1, q2)

        self.at_clip("S6-c14")
        self.play(FadeOut(l1), FadeOut(l2), FadeOut(l3), FadeOut(l4), FadeOut(l5),
                  type_in(q1, run_time=0.9), run_time=0.9)        # 46.97 -> 47.87
        self.at_clip("S6-c15")
        self.play(type_in(q2, run_time=0.7), run_time=0.7)        # 50.45 -> 51.15

        # 页6：品牌尾卡（c16-c17）
        pre = t("下一篇：给 AI 看标准答案，为什么越练越差？", 26, MUTED, "BOLD")
        title = t("《向量检索为什么敢随机降维？1536 维砍到 128，精度几乎不掉》", 27, WHITE, "BOLD")
        title.set_width(6.9)
        logo = ImageMobject(str(AVATAR))
        logo.scale_to_fit_width(3.3)
        follow = t("关注「数解AI」", 38, YELL, "BOLD")
        guide = t("查看公众号文章", 30, GREEN, "BOLD")
        page7 = page_stack(pre, title, logo, follow, guide, buff=0.56)
        layout_page(page7)

        self.at_clip("S6-c16")
        self.play(FadeOut(q1), FadeOut(q2), type_in(pre, run_time=1.0), run_time=1.0)  # 51.74 -> 52.74
        self.play(FadeIn(logo, shift=DOWN * 0.05), type_in(follow, run_time=0.9),
                  run_time=0.9)                                  # 52.74 -> 53.64
        self.play(type_in(title, run_time=1.0), type_in(guide, run_time=0.6),
                  run_time=1.0)                                   # 53.64 -> 54.64
        self.wait(2.82)
        _scene_out(self, pre, title, logo, follow, guide, f)   # 57.46 -> 58.06
        self.pad_to_voice()
