#!/usr/bin/env python3
"""《注意力找人，FFN存知识：跟一句话走完Transformer》视频号 Manim 动画（竖屏 1080×1920）

8 个场景 S1-S8 + 封面 Cover，与 storyboard.md 一一对应。
布局规范（硬性）：VGroup 原子化 + 锚点链 + 安全区 + 比例坐标，禁止裸魔法数字定位。
内容最低点距底 399~800px（frame y ∈ [-4.15, -1.18]）、框内文字限宽、宽组 set_width 守卫。
用法：
  python3 -m manim render -qm --disable_caching scenes.py S1 S2 S3 S4 S5 S6 S7 S8
  python3 -m manim render -qm -s --disable_caching scenes.py Cover
"""
from __future__ import annotations

import numpy as np
from manim import *

config.pixel_width = 1080
config.pixel_height = 1920
config.frame_width = 8.0
config.frame_height = 14.2222
config.background_color = "#16213E"

FONT = "Noto Sans CJK SC"
YELL = "#FFD54A"
CYAN = "#58C4DD"
GREEN = "#7ED7A0"
RED = "#FF8A80"
MUTED = "#AAB4C8"
WHITE = "#F0F3F8"

# 配音时长（tts_split.py 实测 2026-08-15），渲染时长 = 配音 + 缓冲
VOICE_DUR = {"S1": 23.35, "S2": 36.97, "S3": 33.65, "S4": 29.15,
             "S5": 33.71, "S6": 47.87, "S7": 25.88, "S8": 46.44}
TAIL = 2.5

# 7 个 token（Qwen3-1.7B 分词器输出，与 weixin.md 一致）
TOKENS = ["这篇文章", "用", "一句话", "走", "完", "Transformer", "全过程"]
TOKEN_IDS = ["113273", "11622", "105321", "99314", "46306", "46358", "109092"]


def t(text: str, size: float = 34, color: str = WHITE, weight: str = "NORMAL") -> Text:
    return Text(text, font=FONT, font_size=size, color=color, weight=weight)


def boxed(label: str, w: float, h: float, color: str, fs: float = 28,
          fill: float = 0.12, wc=None, weight: str = "NORMAL") -> VGroup:
    """固定尺寸框 + 限宽文字（文字 ≤ 框宽 78%，只缩小不放大）。"""
    txt = t(label, fs, wc or color, weight)
    if txt.width > w * 0.78:
        txt.set_width(w * 0.78)
    box = Rectangle(width=w, height=h, color=color,
                    fill_color=color, fill_opacity=fill)
    return VGroup(box, txt)


def fit(mob, frac: float = 0.85):
    """宽内容守卫：不超过画布宽的 frac（只缩小不放大）。"""
    if mob.width > config.frame_width * frac:
        return mob.set_width(config.frame_width * frac)
    return mob


def token_cards(hl: list[str] | None = None) -> VGroup:
    """7 个 token 卡片行（带 ID 小标签），hl 为要高亮的下标。"""
    widths = [1.65, 1.0, 1.65, 1.0, 1.0, 2.15, 1.65]
    row = VGroup()
    for i, (tok, w) in enumerate(zip(TOKENS, widths)):
        c = boxed(tok, w, 0.9, YELL if (hl and i in hl) else CYAN, 26)
        row.add(c)
    row.arrange(RIGHT, buff=0.18)
    fit(row, 0.92)
    return row


def token_row_with_ids() -> VGroup:
    """7 卡片 + 每张下方 Token ID。"""
    cards = token_cards()
    ids = VGroup()
    for i, c in enumerate(cards):
        lab = t(TOKEN_IDS[i], 15, MUTED).next_to(c, DOWN, buff=0.12)
        ids.add(lab)
    grp = VGroup(cards, ids)
    return grp


class _Base(Scene):
    def setup(self):
        self.scene_dur = VOICE_DUR[self.__class__.__name__] + TAIL

    def at(self, t: float):
        if t > self.time:
            self.wait(t - self.time)

    def pad_to_voice(self):
        elapsed = self.time
        target = self.scene_dur
        if target > elapsed:
            self.wait(target - elapsed)

    def footer(self, text: str = "数解AI · 大模型原理"):
        f = t(text, 20, MUTED).to_edge(DOWN, buff=1.15)
        self.add(f)

    def play_red_cross(self, target, run_time: float = 0.65):
        c1 = Line(target.get_corner(UL) + RIGHT * 0.15 + DOWN * 0.15,
                  target.get_corner(DR) + LEFT * 0.15 + UP * 0.15,
                  color=RED, stroke_width=14)
        c2 = Line(target.get_corner(UR) + LEFT * 0.15 + DOWN * 0.15,
                  target.get_corner(DL) + RIGHT * 0.15 + UP * 0.15,
                  color=RED, stroke_width=14)
        cross = VGroup(c1, c2)
        self.play(GrowFromCenter(c1), GrowFromCenter(c2), run_time=0.4)
        self.play(cross.animate.scale(1.1), run_time=0.1)
        self.play(cross.animate.scale(1 / 1.1), run_time=0.1)
        return cross


# ---------------- S1 开场钩子：一句话走完 Transformer ----------------
class S1(_Base):
    def construct(self):
        self.footer()
        # 开场说明（字幕上方，贯穿 S1，不进音轨）
        note = t("本文为演示方便，使用的是 Qwen3-1.7B 的小模型为例子", 26, MUTED)
        note.to_edge(DOWN, buff=3.0)
        fit(note, 0.95)
        self.play(FadeIn(note, shift=DOWN * 0.05), run_time=0.5)
        head = t("一句话，走完 Transformer 28 层", 40, YELL, "BOLD").to_edge(UP, buff=1.2)
        fit(head, 0.9)
        self.play(FadeIn(head, shift=DOWN * 0.05))

        self.at(0.5)
        sent = t("「这篇文章用一句话走完Transformer全过程」", 26, CYAN)
        fit(sent, 0.95)
        sent.next_to(head, DOWN, buff=0.8)
        self.play(FadeIn(sent, shift=DOWN * 0.05), run_time=0.6)

        self.at(1.4)
        cards = token_cards()
        cards.next_to(sent, DOWN, buff=0.8)
        self.play(FadeIn(cards, shift=DOWN * 0.05), run_time=0.9)

        # 数字链：7 token → 2048 维 → 28 层 → 15 万选 1
        chain = VGroup()
        for lab, col in (("7 个 token", CYAN), ("2048 维", WHITE),
                         ("28 层", WHITE), ("15 万选 1", YELL)):
            chain.add(boxed(lab, 1.45, 0.85, col, 24, weight="BOLD"))
        chain.arrange(RIGHT, buff=0.42)
        chain.next_to(cards, DOWN, buff=0.9)
        ars = VGroup()
        for i in range(3):
            ars.add(Arrow(chain[i].get_right(), chain[i + 1].get_left(),
                          color=MUTED, buff=0.12, stroke_width=4))
        for i, b in enumerate(chain):
            self.at(4.4 + 1.8 * i)
            self.play(FadeIn(b, shift=DOWN * 0.05), run_time=0.5)
            if i < 3:
                self.play(Create(ars[i]), run_time=0.3)
        self.at(12.0)
        self.play(Indicate(chain[3], color=YELL, scale_factor=1.15), run_time=1.0)

        # 两个操作 + 问句
        self.at(15.0)
        ops = VGroup(boxed("注意力", 2.6, 1.0, YELL, 32, fill=0.2, weight="BOLD"),
                     boxed("FFN", 2.6, 1.0, GREEN, 32, fill=0.2, weight="BOLD"))
        ops.arrange(RIGHT, buff=1.0).next_to(chain, DOWN, buff=0.9)
        oplab = t("全程只有两个操作", 26, MUTED).next_to(ops, UP, buff=0.4)
        self.play(FadeIn(ops, shift=DOWN * 0.05), FadeIn(oplab, shift=DOWN * 0.05), run_time=0.7)
        self.at(18.3)
        q = t("凭什么，重复 28 次，就能理解语言？", 30, CYAN, "BOLD")
        fit(q, 0.95)
        q.next_to(ops, DOWN, buff=0.7)
        self.play(FadeIn(q, shift=DOWN * 0.05), run_time=0.6)
        self.pad_to_voice()


# ---------------- S2 分词 + 嵌入表 ----------------
class S2(_Base):
    def construct(self):
        self.footer()
        head = t("先分词，再查表", 40, YELL, "BOLD").to_edge(UP, buff=1.2)
        self.play(FadeIn(head, shift=DOWN * 0.05))

        # 页1：否定两个数法 → 分词器片段 → 7 token 卡 + ID
        self.at(1.6)
        n1 = boxed("7 个汉字", 2.9, 1.15, CYAN, 28)
        n2 = boxed("7 个词", 2.9, 1.15, GREEN, 28)
        ns = VGroup(n1, n2).arrange(RIGHT, buff=1.0).next_to(head, DOWN, buff=1.2)
        self.play(FadeIn(ns, shift=DOWN * 0.05), run_time=0.7)
        self.at(4.6)
        c1 = self.play_red_cross(n1)
        self.at(5.8)
        c2 = self.play_red_cross(n2)
        self.at(7.0)
        ans = boxed("分词器输出的 7 个片段", 5.2, 1.1, YELL, 30, fill=0.2, weight="BOLD")
        ans.next_to(ns, DOWN, buff=1.4)
        self.play(FadeIn(ans, scale=1.05), run_time=0.7)
        self.at(9.0)
        toks = token_row_with_ids()
        toks.next_to(ans, DOWN, buff=1.6)
        self.play(FadeIn(toks, shift=DOWN * 0.05), run_time=0.9)
        self.at(10.6)
        self.play(Indicate(toks[0][0], color=YELL, scale_factor=1.2),
                  Indicate(toks[0][5], color=YELL, scale_factor=1.2), run_time=1.2)

        # 页2：嵌入表 + 矩阵 + 622MB + 同一张表
        self.at(12.4)
        self.play(FadeOut(VGroup(n1, n2, c1, c2, ans, toks), shift=UP * 0.05), run_time=0.4)
        tab = VGroup(Rectangle(width=6.8, height=1.3, color=CYAN,
                               fill_color=CYAN, fill_opacity=0.12),
                     t("嵌入表：151936 行 × 2048 列", 30, CYAN, "BOLD").set_width(6.8 * 0.8))
        tab.next_to(head, DOWN, buff=1.0)
        self.play(FadeIn(tab, shift=DOWN * 0.05), run_time=0.8)
        self.at(16.0)
        mlab = VGroup(t("7 个 token → 7 行向量", 26, WHITE),
                      t("[7, 2048] 矩阵", 26, YELL, "BOLD"))
        mlab.arrange(RIGHT, buff=0.5).next_to(tab, DOWN, buff=0.8)
        bars = VGroup()
        for i in range(7):
            bars.add(Rectangle(width=5.8, height=0.28, color=MUTED,
                               fill_color=MUTED, fill_opacity=0.18))
        bars.arrange(DOWN, buff=0.12).next_to(mlab, DOWN, buff=0.45)
        self.play(FadeIn(mlab, shift=DOWN * 0.05), FadeIn(bars, shift=DOWN * 0.05), run_time=0.8)
        self.at(26.0)
        badges = VGroup(boxed("622 兆字节", 2.6, 1.0, RED, 28, weight="BOLD"),
                        boxed("输入 = 输出，同一张表", 3.7, 1.0, GREEN, 22))
        badges.arrange(RIGHT, buff=0.5).next_to(bars, DOWN, buff=0.7)
        self.play(FadeIn(badges[0], scale=1.08), run_time=0.6)
        self.at(30.3)
        self.play(FadeIn(badges[1], shift=DOWN * 0.05), run_time=0.6)
        self.at(33.6)
        q = t("可这些向量没有先后——谁在第 1 位？", 29, CYAN, "BOLD")
        fit(q, 0.95)
        q.next_to(badges, DOWN, buff=0.45)
        self.play(FadeIn(q, shift=DOWN * 0.05), run_time=0.6)
        self.pad_to_voice()


# ---------------- S3 RoPE 旋转位置编码 ----------------
class S3(_Base):
    def construct(self):
        self.footer()
        head = t("RoPE：旋转位置编码", 40, YELL, "BOLD").to_edge(UP, buff=1.2)
        self.play(FadeIn(head, shift=DOWN * 0.05))

        # 页1：三支箭头按位置旋转，长度不变
        self.at(2.0)
        origin = Dot(UP * 2.8, color=WHITE, radius=0.09)
        circ = DashedVMobject(Circle(radius=1.9, color=MUTED, stroke_width=2), num_dashes=48)
        circ.move_to(UP * 2.8)
        a0 = Arrow(UP * 2.8, UP * 2.8 + RIGHT * 1.9, color=CYAN, stroke_width=8, buff=0)
        l0 = t("位置 0", 22, MUTED).next_to(a0.get_end(), UP, buff=0.2)
        self.play(FadeIn(origin), Create(circ), Create(a0), FadeIn(l0), run_time=1.2)
        self.at(5.5)
        a1 = Arrow(UP * 2.8, UP * 2.8 + RIGHT * 1.9, color=GREEN, stroke_width=8, buff=0)
        l1 = t("位置 1", 22, MUTED).next_to(a1.get_end(), UP, buff=0.2)
        self.play(Create(a1), run_time=0.3)
        self.play(Rotate(a1, angle=PI / 4, about_point=UP * 2.8), run_time=1.0)
        self.add(l1.next_to(a1.get_end(), UP, buff=0.2))
        self.at(8.8)
        a2 = Arrow(UP * 2.8, UP * 2.8 + RIGHT * 1.9, color=YELL, stroke_width=8, buff=0)
        self.play(Create(a2), run_time=0.3)
        self.play(Rotate(a2, angle=PI / 2, about_point=UP * 2.8), run_time=1.0)
        l2 = t("位置 2", 22, MUTED).next_to(a2.get_end(), RIGHT, buff=0.2)
        self.add(l2)
        self.at(11.6)
        lab1 = t("每个位置，转的角度不同", 26, WHITE).next_to(circ, DOWN, buff=0.9)
        self.play(FadeIn(lab1, shift=DOWN * 0.05), run_time=0.6)
        self.at(14.3)
        keep = boxed("旋转：不改变长度，只改变方向", 5.6, 1.0, YELL, 28, fill=0.2, weight="BOLD")
        keep.next_to(lab1, DOWN, buff=0.9)
        self.play(FadeIn(keep, scale=1.05), run_time=0.7)

        # 页2：基频旋钮 + 快慢波纹
        self.at(17.8)
        self.play(FadeOut(VGroup(origin, circ, a0, a1, a2, l0, l1, l2, lab1, keep)), run_time=0.4)
        knob = boxed("基频 = 1,000,000", 4.6, 1.1, YELL, 30, fill=0.2, weight="BOLD")
        knob.next_to(head, DOWN, buff=1.1)
        self.play(FadeIn(knob, shift=DOWN * 0.05), run_time=0.7)
        self.at(21.5)
        ax = Axes(x_range=[0, 4, 1], y_range=[-1.2, 1.2, 1],
                  x_length=5.6, y_length=1.5, axis_config={"stroke_width": 1.5})
        ax.set_stroke(MUTED, 1.5)
        ax.next_to(knob, DOWN, buff=1.0)
        fast = ax.plot(lambda x: np.sin(3 * x), color=CYAN, stroke_width=5)
        slow = ax.plot(lambda x: np.sin(0.7 * x), color=GREEN, stroke_width=5)
        self.play(Create(ax), run_time=0.5)
        self.play(Create(fast), Create(slow), run_time=1.0)
        self.at(24.2)
        tags = VGroup(t("低维度：转得快 → 分清相邻", 26, CYAN),
                      t("高维度：转得慢 → 感知远方", 26, GREEN))
        tags.arrange(RIGHT, buff=0.9).next_to(ax, DOWN, buff=0.7)
        fit(tags, 0.92)
        self.play(FadeIn(tags, shift=DOWN * 0.05), run_time=0.7)
        self.at(28.7)
        q = t("位置补上了。7 个词，谁跟谁说话？", 29, YELL, "BOLD")
        fit(q, 0.95)
        q.next_to(tags, DOWN, buff=1.2)
        self.play(FadeIn(q, shift=DOWN * 0.05), run_time=0.6)
        self.pad_to_voice()


# ---------------- S4 注意力 + GQA ----------------
class S4(_Base):
    def construct(self):
        self.footer()
        head = t("注意力：谁跟谁说话", 40, YELL, "BOLD").to_edge(UP, buff=1.2)
        self.play(FadeIn(head, shift=DOWN * 0.05))

        # 页1：Q 问所有 token + 16 Q 头 / 8 KV 头
        self.at(1.4)
        qc = boxed("Q：你跟我有关系吗？", 4.2, 0.95, YELL, 26, fill=0.2, weight="BOLD")
        qc.next_to(head, DOWN, buff=0.8)
        cards = token_cards()
        cards.next_to(qc, DOWN, buff=0.7)
        ars = VGroup()
        for c in cards:
            ars.add(Arrow(qc.get_bottom() + DOWN * 0.05, c.get_top() + UP * 0.05,
                          color=MUTED, buff=0.05, stroke_width=2.5))
        self.play(FadeIn(qc, shift=DOWN * 0.05), FadeIn(cards, shift=DOWN * 0.05),
                  Create(ars), run_time=1.2)
        self.at(6.5)
        qlab = t("Qwen3 一层里：16 个 Q 头", 26, CYAN).next_to(cards, DOWN, buff=0.8)
        qgrid = VGroup()
        for _ in range(16):
            qgrid.add(Square(side_length=0.42, color=CYAN, fill_color=CYAN, fill_opacity=0.35))
        qgrid.arrange_in_grid(2, 8, buff=0.08).next_to(qlab, DOWN, buff=0.4)
        self.play(FadeIn(qlab, shift=DOWN * 0.05), FadeIn(qgrid, shift=DOWN * 0.05), run_time=0.8)
        self.at(10.2)
        kvlab = t("只有 8 个 KV 头", 26, GREEN).next_to(qgrid, DOWN, buff=0.5)
        kvgrid = VGroup()
        for _ in range(8):
            kvgrid.add(Square(side_length=0.5, color=GREEN, fill_color=GREEN, fill_opacity=0.4))
        kvgrid.arrange(RIGHT, buff=0.14).next_to(kvlab, DOWN, buff=0.4)
        self.play(FadeIn(kvlab, shift=DOWN * 0.05), FadeIn(kvgrid, shift=DOWN * 0.05), run_time=0.8)
        self.at(12.2)
        merges = VGroup()
        for i in range(8):
            top_x = qgrid[i * 2].get_center()[0]
            pair_c = (qgrid[i * 2].get_center() + qgrid[i * 2 + 1].get_center()) / 2
            merges.add(Line(pair_c + DOWN * 0.23, kvgrid[i].get_top() + UP * 0.06,
                            color=MUTED, stroke_width=2.5))
        merges.add(t("每 2 个 Q 头，共享 1 组答案", 24, WHITE)
                   .next_to(kvgrid, DOWN, buff=0.55))
        self.play(Create(merges[0:8]), FadeIn(merges[8], shift=DOWN * 0.05), run_time=1.0)

        # 页2：KV 缓存减半 + 问句
        self.at(15.2)
        self.play(FadeOut(VGroup(qc, cards, ars, qlab, qgrid, kvlab, kvgrid, merges),
                          shift=UP * 0.05), run_time=0.4)
        kvlab2 = t("KV 缓存太吃显存", 30, WHITE, "BOLD").next_to(head, DOWN, buff=1.1)
        self.play(FadeIn(kvlab2, shift=DOWN * 0.05), run_time=0.6)
        self.at(19.0)
        bar16 = Rectangle(width=4.8, height=0.6, color=CYAN, fill_color=CYAN, fill_opacity=0.3)
        l16 = t("16 组独立缓存", 26, CYAN).next_to(bar16, UP, buff=0.3)
        g16 = VGroup(bar16, l16).next_to(kvlab2, DOWN, buff=1.1)
        self.play(FadeIn(g16, shift=DOWN * 0.05), run_time=0.6)
        self.at(22.5)
        bar8 = Rectangle(width=2.4, height=0.6, color=GREEN, fill_color=GREEN, fill_opacity=0.5)
        l8 = t("8 组", 26, GREEN).next_to(bar8, UP, buff=0.3)
        g8 = VGroup(bar8, l8).next_to(kvlab2, DOWN, buff=2.7)
        g8.align_to(g16, LEFT)
        half = t("直接减半", 32, RED, "BOLD").next_to(bar8, RIGHT, buff=0.8)
        self.play(FadeIn(g8, shift=DOWN * 0.05), FadeIn(half, scale=1.08), run_time=0.8)
        self.at(25.5)
        q = t("同一句话，第 1 层和第 28 层看到的，是同一个世界吗？", 27, CYAN, "BOLD")
        fit(q, 0.95)
        q.next_to(bar8, DOWN, buff=1.0)
        q.set_x(0)
        self.play(FadeIn(q, shift=DOWN * 0.05), run_time=0.7)
        self.pad_to_voice()


# ---------------- S5 层间对比：从到处看到盯住关键 ----------------
def heatmap_squares(n: int = 7, side: float = 0.45, buff: float = 0.05) -> VGroup:
    sq = VGroup()
    for _ in range(n * n):
        sq.add(Square(side_length=side, color=WHITE, stroke_width=1,
                      fill_color=YELL, fill_opacity=0.06))
    sq.arrange_in_grid(n, n, buff=buff)
    return sq


def fill_l1(sq: VGroup):
    ops = [0.06] * 49
    for i in range(7):
        ops[i * 7 + i] = 0.85
        if i > 0:
            ops[i * 7 + i - 1] = 0.5
    for i in range(7):
        for j in range(i + 1, 7):
            ops[i * 7 + j] = 0.03  # 因果掩码：看不到后面
    return ops


def fill_l14(sq: VGroup):
    ops = [0.05] * 49
    for i in range(7):
        ops[i * 7] = 0.8          # 首列：主题锚点
        ops[i * 7 + i] = 0.3
    for i in range(7):
        for j in range(i + 1, 7):
            ops[i * 7 + j] = 0.03
    return ops


def fill_l28(sq: VGroup):
    ops = [0.05] * 49
    for i in range(7):
        ops[i * 7] = 0.95         # 首列吸走注意力
        ops[i * 7 + i] = 0.12
    for i in range(7):
        for j in range(i + 1, 7):
            ops[i * 7 + j] = 0.03
    return ops


class S5(_Base):
    def construct(self):
        self.footer()
        head = t("同一句话，三层看得不一样", 40, YELL, "BOLD").to_edge(UP, buff=1.2)
        self.play(FadeIn(head, shift=DOWN * 0.05))

        # 实测声明 + 7×7 热力图（三层依次变换）
        self.at(1.0)
        decl = VGroup(boxed("Qwen3-1.7B 实测", 3.0, 0.85, CYAN, 26, weight="BOLD"),
                      t("「这篇文章用一句话走完Transformer全过程」", 20, MUTED))
        decl.arrange(RIGHT, buff=0.6).next_to(head, DOWN, buff=0.8)
        fit(decl, 0.95)
        self.play(FadeIn(decl, shift=DOWN * 0.05), run_time=0.8)

        self.at(6.6)
        lyr = t("第 1 层", 30, WHITE, "BOLD").next_to(decl, DOWN, buff=0.8)
        hm = heatmap_squares().next_to(lyr, DOWN, buff=0.35)
        cap = t("只盯自己和前一个 token", 24, MUTED).next_to(hm, DOWN, buff=0.4)
        self.play(FadeIn(lyr, shift=DOWN * 0.05), FadeIn(hm, shift=DOWN * 0.05),
                  FadeIn(cap, shift=DOWN * 0.05), run_time=1.0)
        self.play(*[s.animate.set_fill(color=YELL, opacity=o)
                    for s, o in zip(hm, fill_l1(hm))], run_time=1.2)

        self.at(12.6)
        newlab = t("第 14 层", 30, WHITE, "BOLD").move_to(lyr)
        newcap = t("「用」把 86% 注意力给首 token", 24, YELL, "BOLD").move_to(cap)
        badge86 = t("86%", 34, YELL, "BOLD").next_to(hm, RIGHT, buff=0.55)
        self.play(FadeOut(lyr), FadeOut(cap), run_time=0.3)
        self.play(FadeIn(newlab), FadeIn(newcap), run_time=0.4)
        self.play(*[s.animate.set_fill(color=YELL, opacity=o)
                    for s, o in zip(hm, fill_l14(hm))], run_time=1.2)
        self.play(FadeIn(badge86, scale=1.2), run_time=0.5)
        lyr, cap = newlab, newcap

        self.at(19.5)
        newlab = t("第 28 层", 30, WHITE, "BOLD").move_to(lyr)
        newcap = t("所有位置都盯首 token：79%-87%", 24, YELL, "BOLD").move_to(cap)
        badge = t("79%-87%", 30, YELL, "BOLD").move_to(badge86)
        self.play(FadeOut(lyr), FadeOut(cap), run_time=0.3)
        self.play(FadeIn(newlab), FadeIn(newcap), FadeOut(badge86), FadeIn(badge), run_time=0.4)
        self.play(*[s.animate.set_fill(color=YELL, opacity=o)
                    for s, o in zip(hm, fill_l28(hm))], run_time=1.2)
        lyr, cap = newlab, newcap

        # 反常识：不是看更广，是盯得更准
        self.at(26.8)
        wide = boxed("看更广", 2.6, 0.95, WHITE, 28)
        sharp = boxed("盯得更准", 3.0, 0.95, YELL, 28, fill=0.2, weight="BOLD")
        vs = VGroup(wide, sharp).arrange(RIGHT, buff=1.0).next_to(hm, DOWN, buff=0.9)
        self.play(FadeIn(vs, shift=DOWN * 0.05), run_time=0.6)
        self.at(27.8)
        cr = self.play_red_cross(wide)
        self.at(29.6)
        note = t('深层不是「看更广」，而是「盯得更准」', 26, WHITE).next_to(vs, DOWN, buff=0.5)
        fit(note, 0.95)
        self.play(FadeIn(note, shift=DOWN * 0.05), run_time=0.5)
        self.at(30.9)
        self.play(FadeOut(VGroup(vs, note, cr)), run_time=0.3)
        q = t('注意力决定跟谁说话。那「说了什么」呢？', 29, CYAN, "BOLD")
        fit(q, 0.95)
        q.next_to(hm, DOWN, buff=0.9)
        self.play(FadeIn(q, shift=DOWN * 0.05), run_time=0.6)
        self.pad_to_voice()


# ---------------- S6 FFN + LoRA ----------------
class S6(_Base):
    def construct(self):
        self.footer()
        head = t("FFN：说了什么", 40, YELL, "BOLD").to_edge(UP, buff=1.2)
        self.play(FadeIn(head, shift=DOWN * 0.05))

        # 页1：SwiGLU 流程：双路 ×3 投影 → SiLU 门控 ⊙ 信息 → 压回 2048
        self.at(3.0)
        d2048 = boxed("2048 维", 2.6, 1.0, CYAN, 28, weight="BOLD").next_to(head, DOWN, buff=0.9)
        self.play(FadeIn(d2048, shift=DOWN * 0.05), run_time=0.6)
        self.at(6.0)
        gate = boxed("门控投影\n6144 维", 3.3, 1.25, GREEN, 26, fill=0.2, weight="BOLD")
        info = boxed("信息投影\n6144 维", 3.3, 1.25, CYAN, 26, fill=0.2, weight="BOLD")
        two = VGroup(gate, info).arrange(RIGHT, buff=1.0).next_to(d2048, DOWN, buff=1.1)
        split = VGroup(Arrow(d2048.get_bottom(), gate.get_top(), color=MUTED, buff=0.1, stroke_width=5),
                       Arrow(d2048.get_bottom(), info.get_top(), color=MUTED, buff=0.1, stroke_width=5))
        self.play(FadeIn(two, shift=DOWN * 0.05), Create(split), run_time=1.0)
        self.at(9.5)
        x3s = VGroup(t("×3", 30, RED, "BOLD").next_to(split[0], LEFT, buff=0.1),
                     t("×3", 30, RED, "BOLD").next_to(split[1], RIGHT, buff=0.1))
        self.play(FadeIn(x3s, shift=DOWN * 0.05), run_time=0.5)
        self.at(15.7)
        silu = boxed("SiLU 激活", 2.6, 0.8, GREEN, 26, fill=0.15)
        silu.next_to(gate, DOWN, buff=0.45)
        ag = Arrow(gate.get_bottom(), silu.get_top(), color=GREEN, buff=0.1, stroke_width=5)
        self.play(FadeIn(silu, shift=DOWN * 0.05), Create(ag),
                  Indicate(gate, color=GREEN, scale_factor=1.1), run_time=0.9)
        self.at(18.2)
        mul = t("⊙", 52, YELL, "BOLD")
        mul.next_to(silu, DOWN, buff=0.7)
        mul.set_x(0)
        am = VGroup(Arrow(silu.get_bottom(), mul.get_top(), color=MUTED, buff=0.12, stroke_width=5),
                    Arrow(info.get_bottom(), mul.get_top(), color=MUTED, buff=0.12, stroke_width=5))
        self.play(Create(am), Indicate(info, color=CYAN, scale_factor=1.1), run_time=0.9)
        self.at(19.6)
        self.play(FadeIn(mul, scale=1.2), run_time=0.5)
        self.at(21.0)
        down = boxed("压回 2048 维", 3.6, 0.95, WHITE, 26)
        down.next_to(mul, DOWN, buff=0.6)
        ad = Arrow(mul.get_bottom(), down.get_top(), color=YELL, buff=0.12, stroke_width=5)
        self.play(Create(ad), FadeIn(down, shift=DOWN * 0.05), run_time=0.7)

        # 页2：一层 75% + 知识重路由轻 + 全量微调太贵
        self.at(22.4)
        self.play(FadeOut(VGroup(d2048, two, split, x3s, silu, ag, am, mul, down, ad)),
                  run_time=0.4)
        f375 = boxed("一层 FFN：3774 万个参数", 6.4, 1.2, YELL, 30, fill=0.2, weight="BOLD")
        f375.next_to(head, DOWN, buff=1.1)
        self.play(FadeIn(f375, scale=1.05), run_time=0.7)
        self.at(25.5)
        bar = Rectangle(width=6.4, height=0.7, color=MUTED, fill_color=MUTED, fill_opacity=0.15)
        fill75 = Rectangle(width=6.4 * 0.75, height=0.7, color=YELL,
                           fill_color=YELL, fill_opacity=0.6).align_to(bar, LEFT)
        blab = t("占一层参数的 75%", 26, YELL, "BOLD").next_to(bar, DOWN, buff=0.35)
        bg = VGroup(bar, fill75, blab).next_to(f375, DOWN, buff=0.9)
        self.play(FadeIn(bar), run_time=0.3)
        self.play(GrowFromEdge(fill75, LEFT), FadeIn(blab, shift=DOWN * 0.05), run_time=0.8)
        self.at(27.6)
        heavy = t("知识是重的，路由是轻的", 30, WHITE, "BOLD").next_to(bg, DOWN, buff=0.9)
        self.play(FadeIn(heavy, shift=DOWN * 0.05), run_time=0.6)
        self.at(30.4)
        full = boxed("全量微调 = 全改？", 4.6, 0.95, RED, 28)
        full.next_to(heavy, DOWN, buff=0.9)
        self.play(FadeIn(full, shift=DOWN * 0.05), run_time=0.6)

        # 页3：LoRA 旁边插两个小矩阵
        self.at(33.4)
        self.play(FadeOut(VGroup(f375, bg, heavy, full)), run_time=0.4)
        W = Rectangle(width=2.6, height=2.6, color=CYAN, fill_color=CYAN, fill_opacity=0.15)
        wl = t("原矩阵\n1258 万", 24, CYAN, "BOLD").move_to(W)
        Wg = VGroup(W, wl).next_to(head, DOWN, buff=1.3).shift(LEFT * 1.35)
        A = Rectangle(width=0.5, height=2.6, color=GREEN, fill_color=GREEN, fill_opacity=0.3)
        B = Rectangle(width=2.6, height=0.5, color=GREEN, fill_color=GREEN, fill_opacity=0.3)
        A.next_to(W, RIGHT, buff=0.4).align_to(W, UP)
        B.next_to(W, DOWN, buff=0.35).align_to(W, LEFT)
        Al = t("2048×r", 20, GREEN).next_to(A, UP, buff=0.25)
        Bl = t("r×6144", 20, GREEN).next_to(B, DOWN, buff=0.2)
        loral = t("LoRA：不碰原矩阵，旁边插两个小矩阵", 26, WHITE, "BOLD")
        fit(loral, 0.95)
        loral.next_to(Wg, UP, buff=0.9)
        loral.set_x(0)  # Wg 偏移中心后必须回中，否则左缘被裁（规则 #18）
        self.play(FadeIn(loral, shift=DOWN * 0.05), FadeIn(Wg, shift=DOWN * 0.05), run_time=0.8)
        self.at(36.0)
        self.play(FadeIn(A), FadeIn(B), FadeIn(Al), FadeIn(Bl), run_time=0.8)
        self.at(37.6)
        rnote = t("r 通常取 8 或 16", 22, MUTED).next_to(B, DOWN, buff=0.55).align_to(B, LEFT)
        self.play(FadeIn(rnote, shift=DOWN * 0.05), run_time=0.5)
        self.at(39.4)
        cmp = t("1258 万 → 10 万", 42, YELL, "BOLD").next_to(B, DOWN, buff=1.5)
        cmp.align_to(B, LEFT)
        self.play(FadeIn(cmp, scale=1.1), run_time=0.7)
        self.at(43.5)
        q = t("向量里已经装满答案。怎么变回一个字？", 29, CYAN, "BOLD")
        fit(q, 0.95)
        q.next_to(cmp, DOWN, buff=1.0)
        self.play(FadeIn(q, shift=DOWN * 0.05), run_time=0.6)
        self.pad_to_voice()


# ---------------- S7 输出：变回下一个 token ----------------
class S7(_Base):
    def construct(self):
        self.footer()
        head = t("最后一步：变回一个字", 40, YELL, "BOLD").to_edge(UP, buff=1.2)
        self.play(FadeIn(head, shift=DOWN * 0.05))

        # 页1：取最后一行
        self.at(0.8)
        mlab = t("输入矩阵 [7, 2048]", 26, WHITE).next_to(head, DOWN, buff=0.9)
        bars = VGroup()
        for i in range(7):
            bars.add(Rectangle(width=5.8, height=0.36, color=MUTED,
                               fill_color=MUTED, fill_opacity=0.18))
        bars.arrange(DOWN, buff=0.16).next_to(mlab, DOWN, buff=0.45)
        self.play(FadeIn(mlab, shift=DOWN * 0.05), FadeIn(bars, shift=DOWN * 0.05), run_time=0.8)
        self.at(2.7)
        bars[6].set_fill(color=YELL, opacity=0.8)
        self.play(bars[6].animate.set_fill(color=YELL, opacity=0.8), run_time=0.6)
        lastl = t("取最后一行", 26, YELL, "BOLD").next_to(bars[6], DOWN, buff=0.25).align_to(bars[6], RIGHT)
        self.play(FadeIn(lastl, shift=DOWN * 0.05), run_time=0.5)
        self.at(3.4)
        nxt = boxed("我们只关心下一个 token", 5.4, 0.95, CYAN, 26)
        nxt.next_to(bars, DOWN, buff=1.2)
        self.play(FadeIn(nxt, shift=DOWN * 0.05), run_time=0.6)

        # 页2：同一张表倒过来用
        self.at(4.6)
        self.play(FadeOut(VGroup(mlab, bars, lastl, nxt)), run_time=0.4)
        same = boxed("输入 = 输出：同一张嵌入表", 6.6, 1.0, GREEN, 28, fill=0.2, weight="BOLD")
        same.next_to(head, DOWN, buff=0.9)
        self.play(FadeIn(same, shift=DOWN * 0.05), run_time=0.7)
        self.at(7.8)
        tr = t("倒过来用：乘上它的转置", 26, WHITE).next_to(same, DOWN, buff=0.9)
        dar = Arrow(tr.get_bottom(), tr.get_bottom() + DOWN * 1.2, color=MUTED, stroke_width=5, buff=0.1)
        cand = VGroup()
        for _ in range(18):
            cand.add(Square(side_length=0.5, color=CYAN, fill_color=CYAN, fill_opacity=0.3))
        cand.arrange_in_grid(3, 6, buff=0.09).next_to(dar, DOWN, buff=0.2)
        clab = t("151936 个候选", 26, CYAN, "BOLD").next_to(cand, DOWN, buff=0.6)
        self.play(FadeIn(tr, shift=DOWN * 0.05), Create(dar), FadeIn(cand, shift=DOWN * 0.05),
                  FadeIn(clab, shift=DOWN * 0.05), run_time=1.0)

        # 页3：softmax 概率条 + 选最高 + 过程/的
        self.at(14.7)
        self.play(FadeOut(VGroup(tr, dar, cand, clab)), run_time=0.4)
        plab = t("softmax → 151936 个概率", 26, WHITE).next_to(same, DOWN, buff=1.2)
        bars2 = VGroup()
        heights = [0.35, 0.45, 0.55, 0.7, 1.15, 0.6, 0.5, 0.42, 0.38, 0.35]
        for h in heights:
            bars2.add(Rectangle(width=0.5, height=h, color=MUTED,
                                fill_color=MUTED, fill_opacity=0.3))
        bars2.arrange(RIGHT, buff=0.09, aligned_edge=DOWN).next_to(plab, DOWN, buff=0.4)
        bars2[4].set_fill(color=YELL, opacity=0.9)
        self.play(FadeIn(plab, shift=DOWN * 0.05), FadeIn(bars2, shift=DOWN * 0.05), run_time=0.9)
        self.at(17.5)
        self.play(Indicate(bars2[4], color=YELL, scale_factor=1.25), run_time=1.0)
        self.at(19.0)
        pick = t("最高的那个 = 猜的下一个字", 28, YELL, "BOLD").next_to(bars2, DOWN, buff=0.6)
        self.play(FadeIn(pick, shift=DOWN * 0.05), run_time=0.6)
        self.at(21.0)
        words = VGroup(boxed("过程", 1.5, 0.9, GREEN, 26),
                       boxed("的", 1.5, 0.9, CYAN, 26))
        words.arrange(RIGHT, buff=0.6).next_to(pick, DOWN, buff=0.8)
        wlab = t("训练得好，后面可能接……", 24, MUTED).next_to(words, UP, buff=0.35)
        self.play(FadeIn(words, shift=DOWN * 0.05), FadeIn(wlab, shift=DOWN * 0.05), run_time=0.7)
        self.pad_to_voice()


# ---------------- S8 收官 + 品牌尾卡 ----------------
class S8(_Base):
    def construct(self):
        self.footer()
        head = t("六站，拼成一条流水线", 40, YELL, "BOLD").to_edge(UP, buff=1.2)
        self.play(FadeIn(head, shift=DOWN * 0.05))

        # 页1：六站纵向流水线（垂直链，内容铺满屏幕）
        stations = [("分词", "7 个 ID", CYAN), ("嵌入", "2048 维", CYAN),
                    ("位置", "旋转", CYAN), ("注意力", "找人", YELL),
                    ("FFN", "存知识", GREEN), ("输出", "选 1 个", CYAN)]
        rows = VGroup()
        for name, cap, col in stations:
            nd = VGroup(boxed(name, 1.7, 0.8, col, 28, weight="BOLD"),
                        t(cap, 22, MUTED))
            nd.arrange(RIGHT, buff=0.6)
            rows.add(nd)
        rows.arrange(DOWN, buff=0.42, aligned_edge=LEFT).next_to(head, DOWN, buff=0.9)
        ars = VGroup()
        for i in range(5):
            # 箭头以左侧框列为中心（rows[i][0] 是框，行组含右侧注释、中心偏右）
            ars.add(Arrow(rows[i][0].get_bottom(), rows[i + 1][0].get_top(),
                          color=MUTED, buff=0.08, stroke_width=4))
        for i, nd in enumerate(rows):
            self.at(1.0 + 1.15 * i)
            self.play(FadeIn(nd, shift=DOWN * 0.05), run_time=0.4)
            if i > 0:
                self.play(Create(ars[i - 1]), run_time=0.3)

        # 页2：路由器 / 存储器
        self.at(10.6)
        self.play(FadeOut(VGroup(rows, ars)), run_time=0.4)
        router = boxed("注意力 = 路由器", 3.3, 1.55, YELL, 28, fill=0.2, weight="BOLD")
        memory = boxed("FFN = 存储器", 3.3, 1.55, GREEN, 28, fill=0.2, weight="BOLD")
        duo = VGroup(router, memory).arrange(RIGHT, buff=0.5).next_to(head, DOWN, buff=1.3)
        self.play(FadeIn(duo, scale=1.06), run_time=0.8)
        self.at(14.6)
        rlab = t("信息怎么流 / 每个位置知道了什么", 24, MUTED).next_to(duo, DOWN, buff=0.9)
        self.play(FadeIn(rlab, shift=DOWN * 0.05), run_time=0.5)
        self.at(16.2)
        x28 = t("重复 28 次，语义一层层压进向量", 28, WHITE, "BOLD").next_to(rlab, DOWN, buff=1.3)
        ticks = VGroup()
        for _ in range(28):
            ticks.add(Rectangle(width=0.055, height=0.28, color=MUTED,
                                fill_color=MUTED, fill_opacity=0.5))
        ticks.arrange(RIGHT, buff=0.05).next_to(x28, DOWN, buff=1.0)
        self.play(FadeIn(x28, shift=DOWN * 0.05), FadeIn(ticks, shift=DOWN * 0.05), run_time=0.6)

        # 页3：标准 Transformer = 骨架，V4 = 改装
        self.at(19.3)
        self.play(FadeOut(VGroup(duo, rlab, x28, ticks)), run_time=0.4)
        std = boxed("这就是标准 Transformer", 5.8, 1.1, YELL, 30, fill=0.2, weight="BOLD")
        std.next_to(head, DOWN, buff=1.1)
        self.play(FadeIn(std, scale=1.05), run_time=0.7)
        self.at(22.2)
        v4lab = t("DeepSeek V4：不是另起炉灶，是改装这个骨架", 26, WHITE)
        fit(v4lab, 0.95)
        v4lab.next_to(std, DOWN, buff=1.0)
        self.play(FadeIn(v4lab, shift=DOWN * 0.05), run_time=0.6)
        self.at(25.5)
        chassis = Rectangle(width=6.8, height=0.95, color=WHITE,
                            fill_color=WHITE, fill_opacity=0.06)
        badges = VGroup(boxed("MLA", 1.9, 0.68, GREEN, 26, weight="BOLD"),
                        boxed("CSA", 1.9, 0.68, CYAN, 26, weight="BOLD"))
        badges.arrange(RIGHT, buff=1.2)
        chassis.next_to(v4lab, DOWN, buff=0.8)
        badges.move_to(chassis)
        self.play(FadeIn(chassis, shift=DOWN * 0.05), FadeIn(badges, shift=DOWN * 0.05), run_time=0.8)
        self.at(31.7)
        piston = boxed("改装前，先认识活塞和曲轴", 5.6, 1.0, CYAN, 28)
        piston.next_to(chassis, DOWN, buff=0.9)
        self.play(FadeIn(piston, shift=DOWN * 0.05), run_time=0.6)

        # 页4：品牌尾卡
        self.at(34.2)
        self.play(FadeOut(VGroup(std, v4lab, chassis, badges, piston)), run_time=0.4)
        logo = ImageMobject("avatar-sjai-round.png")
        logo.scale_to_fit_width(3.0)
        logo.next_to(head, DOWN, buff=0.9)
        self.play(FadeIn(logo, shift=DOWN * 0.05), run_time=0.7)
        self.at(35.2)
        follow = t("关注「数解AI」", 40, YELL, "BOLD").next_to(logo, DOWN, buff=0.55)
        self.play(FadeIn(follow, scale=1.08), run_time=0.6)
        self.at(37.3)
        title = t("《注意力找人，FFN存知识：跟一句话走完Transformer》", 25, WHITE, "BOLD")
        fit(title, 0.95)
        title.next_to(follow, DOWN, buff=0.7)
        self.play(FadeIn(title, shift=DOWN * 0.05), run_time=0.6)
        self.at(38.4)
        link = t("查看公众号文章", 30, GREEN, "BOLD").next_to(title, DOWN, buff=0.55)
        self.play(FadeIn(link, scale=0.95), run_time=0.6)
        self.at(39.4)
        nxt = t("下一篇：17 亿参数，怎么从零学出来？", 26, CYAN, "BOLD")
        fit(nxt, 0.95)
        nxt.next_to(link, DOWN, buff=0.7)
        self.play(FadeIn(nxt, shift=DOWN * 0.05), run_time=0.6)
        self.at(41.6)
        ask = t('更深的层，会「看」得更广，还是「看」得更准？评论区聊聊', 24, MUTED)
        fit(ask, 0.95)
        ask.next_to(nxt, DOWN, buff=0.7)
        self.play(FadeIn(ask, shift=DOWN * 0.05), run_time=0.6)
        self.pad_to_voice()


# ---------------- 封面帧 ----------------
class Cover(Scene):
    """封面帧：系列标签 + 主/副标题 + 7 token + 数字链 + 底部品牌。
    渲染：python3 -m manim render -qm -s --disable_caching scenes.py Cover
    关键内容须落在 3:4 安全区（frame y ∈ [-5.33, +5.33]）。
    """
    def construct(self):
        logo = ImageMobject("avatar-sjai-round.png")
        logo.scale_to_fit_width(1.8)
        logo.to_edge(DOWN, buff=2.1)

        series = t("大模型原理 · 第 7 篇", 26, CYAN).to_edge(UP, buff=2.2)
        title = t("注意力找人，FFN存知识：跟一句话走完Transformer", 42, YELL, "BOLD")
        title.set_width(config.frame_width * 0.8)
        title.next_to(series, DOWN, buff=0.5)
        subtitle = t("7 个 token 走完 28 层，真实数据全记录", 30, WHITE)
        fit(subtitle, 0.9)
        subtitle.next_to(title, DOWN, buff=0.45)

        cards = token_cards()
        cards.next_to(subtitle, DOWN, buff=1.2)
        chain = VGroup()
        for lab, col in (("7 个 token", CYAN), ("2048 维", WHITE),
                         ("28 层", WHITE), ("15 万选 1", YELL)):
            chain.add(boxed(lab, 1.4, 0.85, col, 24, weight="BOLD"))
        chain.arrange(RIGHT, buff=0.5).next_to(cards, DOWN, buff=1.3)
        ars = VGroup()
        for i in range(3):
            ars.add(Arrow(chain[i].get_right(), chain[i + 1].get_left(),
                          color=MUTED, buff=0.12, stroke_width=4))
        duo = VGroup(t("注意力 = 路由器", 26, YELL, "BOLD"),
                     t("FFN = 存储器", 26, GREEN, "BOLD"))
        duo.arrange(RIGHT, buff=1.2).next_to(chain, DOWN, buff=1.15)

        self.add(logo, series, title, subtitle, cards, chain, ars, duo)


if __name__ == "__main__":
    pass
