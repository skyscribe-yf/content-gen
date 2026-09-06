#!/usr/bin/env python3
"""《上下文并行：1M序列为什么切了会坏？》视频号 Manim 动画（竖屏 1080×1920）

6 个场景 S1-S6，与 storyboard-v2.md 一一对应（2026-09-03 重做）。
- 配音：MiniMax 预设精英男声（male-qn-jingying，speech-2.8-turbo，speed 1.0 pitch +2；S6 结尾降速 0.85）
- 时间轴：at_clip("S1-c01") 挂 tts/sentence-boundaries.json 的 clip 起点（先声音后动画门禁）
- 布局：整页规划（page_stack + layout_page / page_auto），上下留白各 ≤10%
- 动画降噪：每页 1 个主视觉动效；emphasize 全片 5 次；v2 动效 0 处
- 段末统一 transition_out（S6 尾卡除外，终幕驻屏）
用法（项目根目录执行）：
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
VOICE_DUR = {"S1": 17.34, "S2": 33.22, "S3": 30.66, "S4": 43.1, "S5": 57.61, "S6": 58.74}
TAIL = 2.5


def _footer(self) -> Text:
    f = t("数解AI · DeepSeek 技术解密", 20, MUTED).to_edge(DOWN, buff=1.15)
    self.add(f)
    return f


def _head(text: str, size: float = 38) -> Text:
    return t(text, size, YELL, "BOLD").to_edge(UP, buff=1.2)


# ---------------- S1 开场钩子：切蛋糕 → 一切就坏 ----------------
class S1(_Base):
    def construct(self):
        self.bg()
        f = _footer(self)

        # 页1：概念图 + 8 段序列条 + 问句
        head = _head("1M 序列，切成 8 段", 36)
        img = ImageMobject(str(IMG / "s1-cake-round.png"))
        img.scale_to_fit_width(5.0)
        seq = VGroup(*[Rectangle(width=0.72, height=1.5, color=CYAN,
                                 fill_color=CYAN, fill_opacity=0.2) for _ in range(8)])
        seq.arrange(RIGHT, buff=0.08)
        q = t("每人一块，有什么难的？", 36, WHITE, "BOLD")
        page1 = page_stack(img, seq, q, buff=0.9)
        layout_page(page1)

        self.at_clip("S1-c01")
        self.play_parallel(type_in(head, run_time=1.0),
                           FadeIn(img, shift=DOWN * 0.05), run_time=1.0)  # 主视觉：概念图
        self.at_clip("S1-c02")
        self.play(*[Create(s) for s in seq], run_time=1.2, lag_ratio=0.15)
        self.at_clip("S1-c03")
        self.play(type_in(q, run_time=0.8))

        # 页2：转折爆点
        head2 = _head("DeepSeek-V4 的回答", 36)
        punch = t("一切就坏", 88, YELL, "BOLD")
        line = t("为什么切了会坏？两阶段通信怎么修好？", 34, WHITE, "BOLD")
        page2 = page_auto(punch, line)

        self.at_clip("S1-c04")
        self.play(FadeOut(head), FadeOut(page1), type_in(head2, run_time=0.8), run_time=0.8)
        self.play(type_in(punch, run_time=0.9))
        self.emphasize(punch, run_time=0.5)  # 1/5
        self.at_clip("S1-c05")
        self.play(type_in(line, run_time=1.3))
        self.wait(3.45)  # 补到 c05 结束（17.41），台词讲完再转场
        self.transition_out(head2, f, page2)
        self.pad_to_voice()


# ---------------- S2 为什么必须切：1.3TB 显存账 ----------------
class S2(_Base):
    def construct(self):
        self.bg()
        f = _footer(self)

        # 页1：显存账
        head = _head("先看为什么要切", 36)
        card1 = _card("单层注意力：Q、K、V 三份张量", 6.6, 1.7, CYAN, WHITE, 32, CARD_FILL, "BOLD")
        lab1 = t("约", 34, WHITE, "BOLD")
        slot1 = dynamic_slot(2.6, 1.2)
        row1 = stable_row(lab1, slot1, buff=0.35)
        lab2 = t("61 层 × 单层", 30, WHITE)
        slot2 = dynamic_slot(2.6, 1.2)
        row2 = stable_row(lab2, slot2, buff=0.35)
        lab3 = t("一块 H800 只有", 30, WHITE)
        slot3 = dynamic_slot(2.6, 1.2)
        row3 = stable_row(lab3, slot3, buff=0.35)
        lab4 = t("差距", 34, WHITE, "BOLD")
        slot4 = dynamic_slot(2.2, 1.0)
        row4 = stable_row(lab4, slot4, buff=0.35)
        page1 = page_stack(card1, row1, row2, row3, row4, buff=0.75)
        layout_page(page1)

        self.at_clip("S2-c01")
        self.play(type_in(head, run_time=0.8))
        self.at_clip("S2-c02")
        self.play_scroll_unroll(card1, run_time=1.0)  # 主视觉：拉幕
        self.at_clip("S2-c03")
        n1 = self.counter_value(0, 21.5, suffix=" GB", decimals=1, size=64, color=YELL,
                                run_time=1.0, anchor=slot1,
                                extra_anims=[type_in(lab1, run_time=0.5)])
        self.at_clip("S2-c04")
        n2 = self.counter_value(0, 1.3, suffix=" TB", decimals=1, size=64, color=YELL,
                                run_time=1.0, anchor=slot2,
                                extra_anims=[type_in(lab2, run_time=0.5)])
        self.at_clip("S2-c05")
        n3 = self.counter_value(0, 80, suffix=" GB", size=64, color=YELL,
                                run_time=1.0, anchor=slot3,
                                extra_anims=[type_in(lab3, run_time=0.5)])
        self.wait(0.2)
        n4 = self.counter_value(0, 16, suffix=" 倍", size=72, color=YELL,
                                run_time=1.0, anchor=slot4,
                                extra_anims=[type_in(lab4, run_time=0.5)])  # 主视觉：数字滚动
        self.emphasize(n4, run_time=0.5)  # 2/5

        # 页2：Flash Attention 转折
        head2 = _head("Flash Attention 不是解决了吗？", 34)
        card2 = _card("只压掉了分数矩阵", 5.6, 3.0, GREEN, WHITE, 34, CARD_FILL, "BOLD")
        card3 = _card("Q、K、V 一分没少", 5.6, 3.0, CYAN, WHITE, 34, CARD_FILL, "BOLD")
        page2 = page_stack(card2, card3, buff=1.2)
        layout_page(page2)

        self.play(FadeOut(head), FadeOut(page1), FadeOut(n1), FadeOut(n2),
                  FadeOut(n3), FadeOut(n4), type_in(head2, run_time=0.8), run_time=0.8)
        self.at_clip("S2-c06")
        self.play(type_in(head2, run_time=0.6))
        self.at_clip("S2-c07")
        self.play_scroll_unroll_many(card2, card3, run_time=1.0)  # 主视觉：拉幕

        # 页3：结论
        head3 = _head("结论", 36)
        concl = t("CP 不是优化，是必须", 52, YELL, "BOLD")
        line = t("1M 上下文训练，没有 CP 根本跑不起来", 34, WHITE, "BOLD")
        page3 = page_auto(concl, line)

        self.play(FadeOut(head2), FadeOut(page2),
                  type_in(head3, run_time=0.8), run_time=0.8)
        self.at_clip("S2-c08")
        self.play(type_in(concl, run_time=0.9))
        self.at_clip("S2-c09")
        self.play(type_in(line, run_time=0.9))
        self.wait(2.92)  # 补到 c09 结束（33.28），台词讲完再转场
        self.transition_out(head3, f, page3)
        self.pad_to_voice()


# ---------------- S3 普通 CP 两个假设 + Ring-Attention ----------------
class S3(_Base):
    def construct(self):
        self.bg()
        f = _footer(self)

        # 页1：普通 CP + 两个假设
        head = _head("普通 CP 怎么切？", 36)
        seq = VGroup(*[Rectangle(width=1.5, height=1.4, color=CYAN,
                                 fill_color=CYAN, fill_opacity=0.2) for _ in range(4)])
        seq.arrange(RIGHT, buff=0.15)
        lab = t("每张卡持有一段连续 token", 28, WHITE)
        h1 = _card("假设 1：本地 token 数 ≈ 本地 KV 数", 6.8, 1.6, CYAN, WHITE, 30, CARD_FILL, "BOLD")
        h2 = _card("假设 2：边界好处理，跨段补一补就行", 6.8, 1.6, GREEN, WHITE, 30, CARD_FILL, "BOLD")
        page1 = page_stack(seq, lab, h1, h2, buff=0.7)
        layout_page(page1)

        self.at_clip("S3-c01")
        self.play(type_in(head, run_time=0.8))
        self.at_clip("S3-c02")
        self.play(*[Create(s) for s in seq], run_time=1.0, lag_ratio=0.2)  # 主视觉：轨迹
        self.at_clip("S3-c03")
        self.play(type_in(lab, run_time=0.6))
        self.at_clip("S3-c04")
        self.play_scroll_unroll(h1, run_time=1.0)  # 主视觉：拉幕
        self.at_clip("S3-c05")
        self.play_scroll_unroll(h2, run_time=1.0)

        # 页2：Ring-Attention
        head2 = _head("Ring-Attention", 36)
        img = ImageMobject(str(IMG / "s3-relay-round.png"))
        img.scale_to_fit_width(5.5)
        cap = t("KV 块击鼓传花，轮流传着算", 34, WHITE, "BOLD")
        page2 = page_stack(img, cap, buff=1.1)
        layout_page(page2)

        self.play(FadeOut(head), FadeOut(page1), type_in(head2, run_time=0.8), run_time=0.8)
        self.at_clip("S3-c06")
        self.play(FadeIn(img, shift=DOWN * 0.05), run_time=0.8)  # 主视觉：概念图
        self.at_clip("S3-c07")
        self.play(type_in(cap, run_time=0.7))

        # 页3：转折
        head3 = _head("但 V4 的压缩注意力", 36)
        punch = t("两个假设，同时打破", 52, YELL, "BOLD")
        q = t("怎么破的？", 40, WHITE, "BOLD")
        page3 = page_auto(punch, q)

        self.play(FadeOut(head2), FadeOut(page2), type_in(head3, run_time=0.8), run_time=0.8)
        self.at_clip("S3-c08")
        self.play(type_in(punch, run_time=0.9))
        self.emphasize(punch, run_time=0.5)  # 3/5
        self.at_clip("S3-c09")
        self.play(type_in(q, run_time=0.7))
        self.wait(0.35)  # 补到 c09 结束（30.72），台词讲完再转场
        self.transition_out(head3, f, page3)
        self.pad_to_voice()


# ---------------- S4 两个坏因：长度不齐 + 窗口跨边界 ----------------
class S4(_Base):
    def construct(self):
        self.bg()
        f = _footer(self)

        # 页1：坏因一 长度不齐
        head = _head("坏因一：压缩后 KV 长度不齐", 34)
        long_bar = Rectangle(width=6.4, height=0.9, color=CYAN, fill_color=CYAN, fill_opacity=0.25)
        short_bar = Rectangle(width=0.9, height=0.9, color=GREEN, fill_color=GREEN, fill_opacity=0.25)
        bars = VGroup(long_bar, short_bar).arrange(RIGHT, buff=0.3)
        card0 = _card("packed 序列，按序列边界独立压缩", 6.4, 1.8, CYAN, WHITE, 30, CARD_FILL, "BOLD")
        lab1 = t("两条序列打包：1000 token + 7 token", 28, WHITE)
        blocks = VGroup(*[Rectangle(width=1.2, height=1.3, color=YELL, fill_color=YELL, fill_opacity=0.2) for _ in range(4)])
        blocks.arrange(RIGHT, buff=0.1)
        drop = VGroup(*[Rectangle(width=0.28, height=1.3, color=MUTED, fill_color=MUTED, fill_opacity=0.3) for _ in range(3)])
        drop.arrange(RIGHT, buff=0.05)
        row2 = stable_row(blocks, drop, buff=0.3)
        lab2 = t("7 个凑不出 2 个完整块，尾部 3 个被丢弃", 28, WHITE)
        page1 = page_stack(card0, lab1, bars, lab2, row2, buff=0.7)
        layout_page(page1)

        self.at_clip("S4-c01")
        self.play(type_in(head, run_time=0.8))
        self.at_clip("S4-c02")
        self.play(FadeIn(bars, shift=DOWN * 0.05), type_in(lab1, run_time=0.7), run_time=0.9)  # 主视觉：序列条
        self.at_clip("S4-c03")
        self.play(type_in(lab2, run_time=0.7))
        self.at_clip("S4-c04")
        self.play(*[Create(b) for b in blocks], run_time=1.0, lag_ratio=0.2)
        self.at_clip("S4-c05")
        self.play(*[Create(d) for d in drop], run_time=0.8, lag_ratio=0.2)
        self.wait(0.2)
        cross = self.play_red_cross(drop)
        self.wait(0.2)

        # 页2：rank 产出不等
        head2 = _head("每个 rank 产出数量不等", 34)
        r1 = _card("rank A：全是完整块", 4.6, 2.2, CYAN, WHITE, 30, CARD_FILL, "BOLD")
        r2 = _card("rank B：段尾正好是残块", 4.6, 2.2, RED, WHITE, 30, CARD_FILL, "BOLD")
        punch = t("all-gather 第一步就卡住", 44, YELL, "BOLD")
        page2 = page_stack(r1, r2, punch, buff=1.0)
        layout_page(page2)

        self.play(FadeOut(head), FadeOut(page1), FadeOut(cross),
                  type_in(head2, run_time=0.8), run_time=0.8)
        self.at_clip("S4-c06")
        self.play_scroll_unroll_many(r1, r2, run_time=1.0)  # 主视觉：拉幕
        self.at_clip("S4-c07")
        self.play(type_in(punch, run_time=0.8))
        self.wait(0.2)

        # 页3：坏因二 窗口跨边界
        head3 = _head("坏因二：压缩窗口跨边界", 34)
        left = Rectangle(width=2.6, height=2.2, color=CYAN, fill_color=CYAN, fill_opacity=0.2)
        right = Rectangle(width=2.6, height=2.2, color=GREEN, fill_color=GREEN, fill_opacity=0.2)
        pair = VGroup(left, right).arrange(RIGHT, buff=0.0)
        div = Line(pair.get_center() + UP * 0.8, pair.get_center() + DOWN * 0.8, color=RED, stroke_width=5)
        half_l = Rectangle(width=0.6, height=0.9, color=YELL, fill_color=YELL, fill_opacity=0.35)
        half_r = Rectangle(width=0.6, height=0.9, color=YELL, fill_color=YELL, fill_opacity=0.35)
        half_l.move_to(left.get_right() + LEFT * 0.3)
        half_r.move_to(right.get_left() + RIGHT * 0.3)
        card3a = _card("压缩要 m 个连续的 KV entry", 6.4, 1.6, CYAN, WHITE, 30, CARD_FILL, "BOLD")
        lab3 = t("m 个 token 横跨分界线：左半块 + 右半块", 28, WHITE)
        punch2 = t("谁都没法压", 44, YELL, "BOLD")
        page3 = page_stack(card3a, lab3, pair, punch2, buff=0.8)
        layout_page(page3)

        self.play(FadeOut(head2), FadeOut(page2), type_in(head3, run_time=0.8), run_time=0.8)
        self.at_clip("S4-c08")
        self.play(type_in(head3, run_time=0.6))
        self.at_clip("S4-c09")
        self.play(FadeIn(pair, shift=DOWN * 0.05), type_in(lab3, run_time=0.7), run_time=0.9)  # 主视觉：跨边界块
        self.at_clip("S4-c10")
        self.play(FadeIn(half_l), FadeIn(half_r), run_time=0.6)
        self.at_clip("S4-c11")
        self.play(Create(div), run_time=0.5)
        self.at_clip("S4-c12")
        self.play(type_in(punch2, run_time=0.4))
        self.wait(0.1)
        cross2 = self.play_red_cross(pair, run_time=0.5)

        # 页4：照片比喻
        head4 = _head("照片 4 张一组", 34)
        img = ImageMobject(str(IMG / "s4-album-round.png"))
        img.scale_to_fit_width(5.0)
        cap = t("相册切给两个人，边界切在两张照片中间", 28, WHITE)
        punch3 = t("这组照片，丢了。", 48, YELL, "BOLD")
        page4 = page_stack(img, cap, punch3, buff=0.7)
        layout_page(page4)

        self.at_clip("S4-c13")
        self.play(FadeOut(head3), FadeOut(page3), FadeOut(cross2),
                  type_in(head4, run_time=0.8), FadeIn(img, shift=DOWN * 0.05), run_time=0.9)  # 主视觉：概念图
        self.at_clip("S4-c14")
        self.play(type_in(cap, run_time=0.7))
        self.at_clip("S4-c15")
        self.play(type_in(punch3, run_time=0.8))
        self.emphasize(punch3, run_time=0.5)  # 4/5
        self.wait(0.32)  # 补到 c15 结束（43.18），台词讲完再转场
        self.transition_out(head4, f, page4)
        self.pad_to_voice()


# ---------------- S5 两阶段修复：原料交换 + select-and-pad ----------------
class S5(_Base):
    def construct(self):
        self.bg()
        f = _footer(self)

        # 页1：阶段一 边界原料交换
        head = _head("V4 的修法分两步", 36)
        card0 = _card("阶段 1：交换边界原料", 6.4, 1.6, CYAN, WHITE, 30, CARD_FILL, "BOLD")
        r0 = _card("rank r", 2.4, 2.4, CYAN, WHITE, 34, CARD_FILL, "BOLD")
        r1 = _card("rank r+1", 2.4, 2.4, GREEN, WHITE, 34, CARD_FILL, "BOLD")
        pair = VGroup(r0, r1).arrange(RIGHT, buff=2.2)
        arrow = Arrow(pair[0].get_right(), pair[1].get_left(), color=YELL, stroke_width=6)
        lab = t("末尾 m 个未压缩 KV → 右邻居拼完整块", 28, WHITE)
        page1 = page_stack(card0, pair, arrow, lab, buff=0.8)
        layout_page(page1)

        self.at_clip("S5-c01")
        self.play(type_in(head, run_time=0.8))
        self.at_clip("S5-c02")
        self.play_scroll_unroll_many(r0, r1, run_time=1.0)  # 主视觉：拉幕
        self.wait(0.2)
        self.play(Create(arrow), run_time=0.7)
        self.at_clip("S5-c03")
        self.play(type_in(lab, run_time=0.7))

        # 页2：传原料不是半成品
        head2 = _head("传的是原料，不是半成品", 34)
        raw = _card("原料：未压缩 KV", 4.8, 3.0, GREEN, WHITE, 32, CARD_FILL, "BOLD")
        semi = _card("半成品：不存在的中间表示", 4.8, 3.0, RED, WHITE, 32, CARD_FILL, "BOLD")
        page2 = page_stack(raw, semi, buff=1.2)
        layout_page(page2)

        self.play(FadeOut(head), FadeOut(page1), type_in(head2, run_time=0.8), run_time=0.8)
        self.at_clip("S5-c04")
        self.play_scroll_unroll(raw, run_time=1.0)  # 主视觉：拉幕
        self.at_clip("S5-c05")
        self.play_scroll_unroll(semi, run_time=1.0)
        self.wait(0.2)
        cross = self.play_red_cross(semi)
        self.wait(0.2)

        # 页3：通信量 2KB
        head3 = _head("通信量与序列长度无关", 34)
        lab3 = t("CSA 层每 rank 每层只要", 30, WHITE)
        slot = dynamic_slot(2.4, 1.2)
        row = stable_row(lab3, slot, buff=0.35)
        note = t("几乎可以忽略", 34, WHITE, "BOLD")
        page3 = page_auto(row, note)

        self.play(FadeOut(head2), FadeOut(page2), FadeOut(cross),
                  type_in(head3, run_time=0.8), run_time=0.8)
        self.at_clip("S5-c06")
        n = self.counter_value(0, 2.3, suffix=" KB", decimals=1, size=72, color=YELL,
                               run_time=1.0, anchor=slot,
                               extra_anims=[type_in(lab3, run_time=0.5)])  # 主视觉：数字滚动
        self.at_clip("S5-c07")
        self.play(type_in(note, run_time=0.6))
        self.wait(0.2)

        # 页4：阶段二 all-gather
        head4 = _head("第二步：all-gather + select-and-pad", 32)
        c0 = _card("Rank 0: [C0, PAD, PAD, PAD]", 5.4, 2.4, CYAN, WHITE, 28, CARD_FILL, "BOLD")
        c1 = _card("Rank 1: [C1, C2, C3, PAD]", 5.4, 2.4, GREEN, WHITE, 28, CARD_FILL, "BOLD")
        lab4 = t("先 pad 到统一上界，再 all-gather", 28, WHITE)
        page4 = page_stack(c0, c1, lab4, buff=0.9)
        layout_page(page4)

        self.play(FadeOut(head3), FadeOut(page3), FadeOut(n), FadeOut(note),
                  type_in(head4, run_time=0.7), run_time=0.7)
        self.at_clip("S5-c08")
        self.play(type_in(head4, run_time=0.6))
        self.at_clip("S5-c09")
        self.play_scroll_unroll_many(c0, c1, run_time=1.0)  # 主视觉：拉幕
        self.at_clip("S5-c10")
        self.play(type_in(lab4, run_time=0.7))
        self.at_clip("S5-c11")
        self.play(type_in(lab4, run_time=0.5))

        # 页5：blob 有洞
        head5 = _head("gather 出来的数据里有洞", 34)
        blob = _card("blob: [C0, PAD, PAD, PAD, C1, C2, C3, PAD]", 6.6, 1.8, YELL, WHITE, 28, CARD_FILL, "BOLD")
        punch = t("padding 会污染注意力", 40, YELL, "BOLD")
        page5 = page_auto(blob, punch)

        self.play(FadeOut(head4), FadeOut(page4), type_in(head5, run_time=0.8), run_time=0.8)
        self.at_clip("S5-c12")
        self.play_scroll_unroll(blob, run_time=1.0)  # 主视觉：拉幕
        self.at_clip("S5-c13")
        self.play(type_in(punch, run_time=0.8))
        self.emphasize(punch, run_time=0.5)  # 5/5

        # 页6：select-and-pad 三步
        head6 = _head("select-and-pad：一个 kernel 三步合一", 30)
        s1 = _card("① 去 padding", 2.4, 2.6, CYAN, WHITE, 26, CARD_FILL, "BOLD")
        s2 = _card("② 尾对齐", 2.4, 2.6, GREEN, WHITE, 26, CARD_FILL, "BOLD")
        s3 = _card("③ 稀疏重排", 2.4, 2.6, YELL, WHITE, 26, CARD_FILL, "BOLD")
        grid = VGroup(s1, s2, s3).arrange_in_grid(1, 3, buff=0.3)
        line6 = t("合并成一个 kernel，把 padding 全部滤掉", 30, WHITE)
        result = _card("结果: [C0, C1, C2, C3]", 5.4, 2.2, GREEN, WHITE, 30, CARD_FILL, "BOLD")
        page6 = page_stack(grid, line6, result, buff=0.9)
        layout_page(page6)

        self.play(FadeOut(head5), FadeOut(page5), type_in(head6, run_time=0.8), run_time=0.8)
        self.at_clip("S5-c14")
        self.play_scroll_unroll_many(s1, s2, s3, run_time=1.0)  # 主视觉：拉幕
        self.at_clip("S5-c15")
        self.play(type_in(head6, run_time=0.6))
        self.at_clip("S5-c16")
        self.play_scroll_unroll(result, run_time=1.0)  # 主视觉：拉幕

        # 页7：悬念
        head7 = _head("那这笔账", 36)
        q = t("到底省了多少？", 48, YELL, "BOLD")
        page7 = page_auto(q)
        self.play(FadeOut(head6), FadeOut(page6), type_in(head7, run_time=0.8), run_time=0.8)
        self.at_clip("S5-c17")
        self.play(type_in(q, run_time=0.8))
        self.wait(1.36)  # 补到 c17 结束（57.69），台词讲完再转场
        self.transition_out(head7, f, page7)
        self.pad_to_voice()


# ---------------- S6 账 + 实验 + 总结 + 尾卡 ----------------
class S6(_Base):
    def construct(self):
        self.bg()
        f = _footer(self)

        # 页1：通信账 9MB vs 72MB
        head = _head("算笔账", 36)
        lab1 = t("压缩后每层平均", 30, WHITE)
        slot1 = dynamic_slot(2.4, 1.2)
        row1 = stable_row(lab1, slot1, buff=0.35)
        lab2 = t("NVLink 上只要", 30, WHITE)
        slot2 = dynamic_slot(2.4, 1.2)
        row2 = stable_row(lab2, slot2, buff=0.35)
        lab3 = t("不压缩直接 gather", 30, WHITE)
        slot3 = dynamic_slot(2.4, 1.2)
        row3 = stable_row(lab3, slot3, buff=0.35)
        lab4 = t("省了", 34, WHITE, "BOLD")
        slot4 = dynamic_slot(2.2, 1.0)
        row4 = stable_row(lab4, slot4, buff=0.35)
        page1 = page_stack(row1, row2, row3, row4, buff=0.8)
        layout_page(page1)

        self.at_clip("S6-c01")
        self.play(type_in(head, run_time=0.8))
        self.at_clip("S6-c02")
        n1 = self.counter_value(0, 9, suffix=" MB", size=64, color=YELL,
                                run_time=1.0, anchor=slot1,
                                extra_anims=[type_in(lab1, run_time=0.5)])  # 主视觉：数字滚动
        self.wait(0.2)
        n2 = self.counter_value(0, 0.02, suffix=" 毫秒", decimals=2, size=64, color=YELL,
                                run_time=1.0, anchor=slot2,
                                extra_anims=[type_in(lab2, run_time=0.5)])
        self.at_clip("S6-c03")
        n3 = self.counter_value(0, 72, suffix=" MB", size=64, color=YELL,
                                run_time=1.0, anchor=slot3,
                                extra_anims=[type_in(lab3, run_time=0.5)])
        self.wait(0.2)
        n4 = self.counter_value(0, 8, suffix=" 倍", size=72, color=YELL,
                                run_time=1.0, anchor=slot4,
                                extra_anims=[type_in(lab4, run_time=0.5)])  # 主视觉：数字滚动

        # 页2：实验 277/276/277
        head2 = _head("模拟器跑出来", 36)
        b1 = _card("单卡基准", 2.4, 3.4, CYAN, WHITE, 28, CARD_FILL, "BOLD")
        b2 = _card("朴素 CP", 2.4, 3.4, RED, WHITE, 28, CARD_FILL, "BOLD")
        b3 = _card("两阶段 CP", 2.4, 3.4, GREEN, WHITE, 28, CARD_FILL, "BOLD")
        grid = VGroup(b1, b2, b3).arrange(RIGHT, buff=0.3)
        lab2b = t("压缩 KV 数", 30, WHITE)
        slot_a = dynamic_slot(1.8, 1.4)
        slot_b = dynamic_slot(1.8, 1.4)
        slot_c = dynamic_slot(1.8, 1.4)
        nums = VGroup(slot_a, slot_b, slot_c).arrange(RIGHT, buff=0.35)
        page2 = page_stack(grid, lab2b, nums, buff=1.0)
        layout_page(page2)

        self.play(FadeOut(head), FadeOut(page1), FadeOut(n1), FadeOut(n2),
                  FadeOut(n3), FadeOut(n4), type_in(head2, run_time=0.8), run_time=0.8)
        self.at_clip("S6-c04")
        self.play_scroll_unroll_many(b1, b2, b3, run_time=1.0)  # 主视觉：拉幕
        self.wait(0.2)
        na = self.counter_value(0, 277, size=64, color=YELL, run_time=1.0, anchor=slot_a)
        self.at_clip("S6-c05")
        nb = self.counter_value(0, 276, size=64, color=YELL, run_time=1.0, anchor=slot_b)
        self.wait(0.2)
        cross = self.play_red_cross(b2)
        self.at_clip("S6-c06")
        nc = self.counter_value(0, 277, size=64, color=YELL, run_time=1.0, anchor=slot_c)
        self.wait(0.2)
        mk = self.play_mark("✔", b3)

        # 页3：总结
        head3 = _head("结论", 36)
        concl = t("注意力公式变了，并行策略不能原封不动", 40, YELL, "BOLD")
        c1 = _card("rank 间怎么通信", 2.4, 3.6, CYAN, WHITE, 24, CARD_FILL, "BOLD")
        c2 = _card("张量怎么对齐", 2.4, 3.6, GREEN, WHITE, 24, CARD_FILL, "BOLD")
        c3 = _card("kernel 要什么布局", 2.4, 3.6, YELL, WHITE, 24, CARD_FILL, "BOLD")
        grid2 = VGroup(c1, c2, c3).arrange_in_grid(1, 3, buff=0.3)
        line3 = t("全都改了", 40, YELL, "BOLD")
        page3 = page_stack(concl, grid2, line3, buff=1.2)
        layout_page(page3)

        self.play(FadeOut(head2), FadeOut(page2), FadeOut(na), FadeOut(nb),
                  FadeOut(nc), FadeOut(cross), FadeOut(mk),
                  type_in(head3, run_time=0.8), run_time=0.8)
        self.at_clip("S6-c07")
        self.play(type_in(concl, run_time=0.9))
        self.at_clip("S6-c08")
        self.play_scroll_unroll_many(c1, c2, c3, run_time=1.0)  # 主视觉：拉幕
        self.at_clip("S6-c09")
        self.play(type_in(line3, run_time=0.7))

        # 页4：预告 + 问题
        head4 = _head("下一篇", 36)
        nxt = t("DualPipe 与 DeepEP：训练时 GPU 在等什么", 36, YELL, "BOLD")
        q1 = t("一个问题留给你", 32, WHITE)
        q2 = t("压缩省通信 vs 流水线藏通信，", 32, WHITE)
        q3 = t("你更看好哪条路？", 32, WHITE)
        page4 = page_auto(nxt, q1, q2, q3)

        self.at_clip("S6-c10")
        self.play(FadeOut(head3), FadeOut(page3), type_in(head4, run_time=0.8), run_time=0.8)
        self.at_clip("S6-c11")
        self.play(type_in(nxt, run_time=0.9))
        self.at_clip("S6-c12")
        self.play(type_in(q1, run_time=0.6), type_in(q2, run_time=0.7), run_time=0.8)
        self.at_clip("S6-c13")
        self.play(type_in(q3, run_time=0.7))

        # 页5：品牌尾卡（终幕驻屏，不 transition_out）
        # 2026-09-03 用户反馈：前两期结尾太短 → 尾卡提前到 c14 组装，
        # 全部元素露出后驻屏 ≥1.5s（S6 配音已降速 0.85 拉长结尾）
        avatar = ImageMobject(str(AVATAR))
        avatar.scale_to_fit_width(3.6)
        follow = t("关注「数解AI」", 44, YELL, "BOLD")
        title = t("《上下文并行：1M序列为什么切了会坏？》", 28, WHITE, "BOLD")
        guide = t("查看公众号文章", 32, GREEN, "BOLD")
        page5 = page_stack(avatar, follow, title, guide, buff=0.7)
        layout_page(page5)

        self.at_clip("S6-c14")
        self.play(FadeOut(head4), FadeOut(page4), FadeIn(avatar, shift=DOWN * 0.05), run_time=0.6)  # 主视觉：品牌图
        self.play(type_in(follow, run_time=0.5), type_in(title, run_time=0.5),
                  type_in(guide, run_time=0.5), run_time=0.6)
        self.pad_to_voice()
