#!/usr/bin/env python3
"""《位置编码怎么工作？词序一错意思全变》视频号 Manim 动画（竖屏 1080×1920）

8 个场景 S1-S8 + 封面 Cover，与 storyboard.md 一一对应。
布局规范（硬性）：VGroup 原子化 + 锚点链 + 安全区 + 比例坐标，禁止裸魔法数字定位。
内容占屏 ≥40%（最低点距底 ≤800px）、宽组 set_width 守卫、底部留字幕区（距底 ≥399px）。
用法：
  python3 -m manim render -qm --disable_caching scenes.py S1 S2 S3 S4 S5 S6 S7 S8
  python3 -m manim render -qm -s --disable_caching scenes.py Cover
"""
from __future__ import annotations

from manim import *

config.pixel_width = 1080
config.pixel_height = 1920
config.frame_width = 8.0
config.frame_height = 14.2222
config.background_color = "#16213E"

FONT = "Noto Sans CJK SC"
YELL = "#FFD54A"      # 主强调（与字幕黄一致）
CYAN = "#58C4DD"
GREEN = "#7ED7A0"
RED = "#FF8A80"
MUTED = "#AAB4C8"
WHITE = "#F0F3F8"

# 配音时长（tts_split.py 实测 2026-08-11），渲染时长 = 配音 + 缓冲
VOICE_DUR = {"S1": 24.28, "S2": 38.71, "S3": 40.25, "S4": 37.96,
             "S5": 42.85, "S6": 38.05, "S7": 42.83, "S8": 36.7}
TAIL = 2.5


def t(text: str, size: float = 34, color: str = WHITE, weight: str = "NORMAL") -> Text:
    return Text(text, font=FONT, font_size=size, color=color, weight=weight)


def boxed(label: str, w: float, h: float, color: str, fs: float = 28,
          fill: float = 0.12, wc=None, weight: str = "NORMAL") -> VGroup:
    """固定尺寸框 + 限宽文字（文字 ≤ 框宽 78%，防溢出）。"""
    txt = t(label, fs, wc or color, weight)
    txt.set_width(w * 0.78)
    box = Rectangle(width=w, height=h, color=color,
                    fill_color=color, fill_opacity=fill)
    return VGroup(box, txt)


def dot_label(label: str, col: str, fs: float = 24) -> VGroup:
    d = Dot(color=col, radius=0.09)
    lb = t(label, fs, col)
    return VGroup(d, lb).arrange(RIGHT, buff=0.18)


def fit(mob, frac: float = 0.85):
    """宽内容守卫：不超过画布宽的 frac（防越界截断）。"""
    return mob.set_width(config.frame_width * frac)


class _Base(Scene):
    scene_dur = 12.0

    def setup(self):
        self.scene_dur = VOICE_DUR[self.__class__.__name__] + TAIL

    def at(self, t: float):
        """推进到配音时间轴绝对时刻（动画动作挂到台词节点上）。"""
        if t > self.time:
            self.wait(t - self.time)

    def pad_to_voice(self):
        """末尾补齐等待，使场景总时长 = 配音时长 + TAIL 缓冲。"""
        elapsed = self.time
        target = self.scene_dur
        if target > elapsed:
            self.wait(target - elapsed)

    def footer(self, text: str = "数解AI · 大模型原理"):
        f = t(text, 20, MUTED).to_edge(DOWN, buff=1.15)
        self.add(f)


# ---------------- S1 开场钩子：猫追老鼠 vs 老鼠追猫 ----------------
class S1(_Base):
    def construct(self):
        self.footer()
        head = t("词全认识，顺序却丢了", 40, YELL, "BOLD").to_edge(UP, buff=1.2)
        self.play(FadeIn(head, shift=DOWN * 0.05))

        # 页1：两张牌 + 反转箭头
        self.at(0.4)
        card1 = boxed("猫追老鼠", 2.9, 1.0, CYAN, 32, fill=0.15)
        card2 = boxed("老鼠追猫", 2.9, 1.0, RED, 32, fill=0.15)
        cards = VGroup(card1, card2).arrange(DOWN, buff=1.4).next_to(head, DOWN, buff=1.5)
        ar1 = Arrow(card1.get_bottom(), card2.get_top(), color=YELL, buff=0.15, stroke_width=5)
        self.play(FadeIn(card1, shift=DOWN * 0.05), run_time=0.6)
        self.at(2.8)
        self.play(FadeIn(card2, shift=DOWN * 0.05), run_time=0.6)
        self.play(Create(ar1), run_time=0.5)
        self.at(5.9)
        cap = t("词，一模一样；意思，完全相反", 34, YELL, "BOLD")
        fit(cap, 0.9)
        cap.next_to(cards, DOWN, buff=1.3)
        self.play(FadeIn(cap, scale=1.05), run_time=0.7)

        # 页2：词嵌入认词 vs 注意力无顺序 → 座次表
        self.at(9.6)
        self.play(FadeOut(VGroup(cards, ar1, cap), shift=UP * 0.05), run_time=0.4)
        lab = t("模型看到了什么？", 30, WHITE).next_to(head, DOWN, buff=1.2)
        good = boxed("词嵌入：认出「猫」「老鼠」", 4.6, 0.95, GREEN, 28)
        bad = boxed("注意力：分不清谁先谁后", 4.6, 0.95, RED, 28)
        rows = VGroup(good, bad).arrange(DOWN, buff=0.7).next_to(lab, DOWN, buff=1.0)
        self.play(FadeIn(lab, shift=DOWN * 0.05))
        self.at(12.2)
        self.play(FadeIn(good, shift=DOWN * 0.05), run_time=0.6)
        self.at(15.3)
        self.play(FadeIn(bad, shift=DOWN * 0.05), run_time=0.6)
        self.at(18.8)
        seat = boxed("位置编码 = 一张「座次表」", 5.2, 1.1, YELL, 32, fill=0.2, weight="BOLD")
        seat.next_to(rows, DOWN, buff=1.1)
        self.play(FadeIn(seat, scale=1.12), run_time=0.8)
        self.at(22.5)
        q = t("为什么注意力看不见顺序？", 30, CYAN, "BOLD").next_to(seat, DOWN, buff=0.9)
        self.play(FadeIn(q, shift=DOWN * 0.05), run_time=0.6)
        self.pad_to_voice()


# ---------------- S2 注意力无顺序感 + 绝对位置编码 ----------------
class S2(_Base):
    def construct(self):
        self.footer()
        head = t("注意力只看向量关系", 40, YELL, "BOLD").to_edge(UP, buff=1.2)
        self.play(FadeIn(head, shift=DOWN * 0.05))

        # 页1：x1 x2 x3 换序，集合不变
        self.at(1.0)
        lab = t("相关性表只看「谁和谁更像」", 30, WHITE).next_to(head, DOWN, buff=1.5)
        self.play(FadeIn(lab, shift=DOWN * 0.05))
        toks = VGroup(*[boxed(f"x{i}", 1.5, 1.0, CYAN, 30) for i in (1, 2, 3)])
        toks.arrange(RIGHT, buff=0.6).next_to(lab, DOWN, buff=1.5)
        self.play(FadeIn(toks, shift=DOWN * 0.05), run_time=0.6)
        self.at(5.5)
        swap = VGroup(*[boxed(f"x{i}", 1.5, 1.0, RED, 30) for i in (3, 1, 2)])
        swap.arrange(RIGHT, buff=0.6).next_to(toks, DOWN, buff=1.6)
        ar = Arrow(toks.get_bottom(), swap.get_top(), color=YELL, buff=0.15, stroke_width=5)
        self.play(Create(ar), FadeIn(swap, shift=DOWN * 0.05), run_time=0.8)
        self.at(9.5)
        same = t("集合没变，向量没变——看不出换了座次", 30, RED, "BOLD")
        fit(same, 0.92)
        same.next_to(swap, DOWN, buff=1.3)
        self.play(FadeIn(same, shift=DOWN * 0.05), run_time=0.7)
        self.at(13.5)
        none = boxed("输入里根本没有「第几个」", 4.8, 1.1, YELL, 30, fill=0.2, weight="BOLD")
        none.next_to(same, DOWN, buff=1.2)
        self.play(FadeIn(none, scale=1.08), run_time=0.7)

        # 页2：h = x + p 绝对位置编码
        self.at(17.5)
        self.play(FadeOut(VGroup(lab, toks, ar, swap, same, none), shift=UP * 0.05), run_time=0.4)
        f = t("hᵢ = xᵢ + pᵢ", 46, YELL)
        f.next_to(head, DOWN, buff=1.0)
        self.play(FadeIn(f, shift=DOWN * 0.05), run_time=0.6)
        self.at(21.5)
        row = VGroup(boxed("「猫」第 1 位", 2.6, 0.85, CYAN, 26),
                     t("=", 34, WHITE),
                     boxed("x猫 + p1", 2.4, 0.85, GREEN, 26)).arrange(RIGHT, buff=0.5)
        row2 = VGroup(boxed("「猫」第 7 位", 2.6, 0.85, CYAN, 26),
                      t("=", 34, WHITE),
                      boxed("x猫 + p7", 2.4, 0.85, GREEN, 26)).arrange(RIGHT, buff=0.5)
        rows = VGroup(row, row2).arrange(DOWN, buff=0.6).next_to(f, DOWN, buff=0.9)
        fit(rows, 0.95)
        self.play(FadeIn(rows, shift=DOWN * 0.05), run_time=0.8)
        self.at(27.5)
        absl = boxed("绝对位置编码", 3.4, 0.85, YELL, 30, fill=0.2, weight="BOLD")
        absl.next_to(rows, DOWN, buff=0.8)
        self.play(FadeIn(absl, scale=1.08), run_time=0.6)
        self.at(33.0)
        flaw = t("但 p1、p2 只是两张不同向量，相邻关系要自己学", 30, RED)
        fit(flaw, 0.95)
        flaw.next_to(absl, DOWN, buff=0.7)
        self.play(FadeIn(flaw, shift=DOWN * 0.05), run_time=0.7)
        self.at(37.0)
        q = t("怎么破？", 34, CYAN, "BOLD").next_to(flaw, DOWN, buff=0.7)
        self.play(FadeIn(q, scale=0.9), run_time=0.5)
        self.pad_to_voice()


# ---------------- S3 正弦位置编码：多频率 ----------------
class S3(_Base):
    def construct(self):
        self.footer()
        head = t("正弦位置编码：多频率", 40, YELL, "BOLD").to_edge(UP, buff=1.2)
        self.play(FadeIn(head, shift=DOWN * 0.05))

        # 页1：三条不同频率的波（快/中/慢）
        self.at(1.0)
        lab = t("2017 Transformer 论文：用 sin/cos 生成位置", 30, WHITE)
        fit(lab, 0.95)
        lab.next_to(head, DOWN, buff=1.4)
        self.play(FadeIn(lab, shift=DOWN * 0.05))
        self.at(5.0)
        waves = VGroup()
        for freq, col, name in ((3, GREEN, "快：分清相邻位置"),
                                (1.3, CYAN, "中：中距离"),
                                (0.55, YELL, "慢：看远方")):
            fn = FunctionGraph(lambda x, f=freq: 0.55 * np.sin(f * x),
                               x_range=[-3.2, 3.2], color=col, stroke_width=4)
            cap = t(name, 24, col)
            row = VGroup(fn, cap).arrange(DOWN, buff=0.15)
            waves.add(row)
        waves.arrange(DOWN, buff=0.35).next_to(lab, DOWN, buff=1.0)
        fit(waves, 0.95)
        for row in waves:
            self.play(Create(row[0]), FadeIn(row[1], shift=DOWN * 0.05), run_time=0.8)

        # 页2：钟表隐喻 + sin/cos 坐标轴
        self.at(13.5)
        self.play(FadeOut(VGroup(lab, waves), shift=UP * 0.05), run_time=0.4)
        clk = t("像一组钟表", 34, YELL, "BOLD").next_to(head, DOWN, buff=1.1)
        hands = VGroup(dot_label("秒针 → 近处", GREEN, 26),
                       dot_label("分针 → 中距", CYAN, 26),
                       dot_label("时针 → 远方", YELL, 26)).arrange(DOWN, buff=0.5)
        hands.next_to(clk, DOWN, buff=0.9)
        self.play(FadeIn(clk, shift=DOWN * 0.05))
        self.at(16.5)
        self.play(FadeIn(hands, shift=DOWN * 0.05), run_time=0.8)
        self.at(21.0)
        axis = t("sin、cos 像垂直坐标轴，位置移动 → 向量转动", 30, CYAN)
        fit(axis, 0.95)
        axis.next_to(hands, DOWN, buff=1.0)
        self.play(FadeIn(axis, shift=DOWN * 0.05), run_time=0.7)
        self.at(27.0)
        anyp = boxed("不用存表：任意位置代入公式即得", 4.8, 1.0, GREEN, 28)
        anyp.next_to(axis, DOWN, buff=0.9)
        self.play(FadeIn(anyp, shift=DOWN * 0.05), run_time=0.6)
        self.at(33.5)
        flaw = t("但它仍是加法：位置和内容，混在一起", 30, RED)
        fit(flaw, 0.95)
        flaw.next_to(anyp, DOWN, buff=0.9)
        self.play(FadeIn(flaw, shift=DOWN * 0.05), run_time=0.7)
        self.at(38.5)
        q = t("还有别的路吗？", 32, CYAN, "BOLD").next_to(flaw, DOWN, buff=0.8)
        self.play(FadeIn(q, scale=0.9), run_time=0.5)
        self.pad_to_voice()


# ---------------- S4 可学习位置编码 + 长度外推 ----------------
class S4(_Base):
    def construct(self):
        self.footer()
        head = t("可学习位置编码", 40, YELL, "BOLD").to_edge(UP, buff=1.2)
        self.play(FadeIn(head, shift=DOWN * 0.05))

        # 页1：可训练参数表
        self.at(1.0)
        lab = t("位置向量 = 可训练参数，反向传播来调", 30, WHITE)
        fit(lab, 0.95)
        lab.next_to(head, DOWN, buff=1.4)
        self.play(FadeIn(lab, shift=DOWN * 0.05))
        self.at(5.0)
        ps = VGroup(*[boxed(f"p{i}", 1.4, 0.9, CYAN, 26) for i in (1, 2, 3)])
        ps.arrange(RIGHT, buff=0.5).next_to(lab, DOWN, buff=1.4)
        rand = t("一开始：随机数", 28, MUTED).next_to(ps, DOWN, buff=0.8)
        self.play(FadeIn(ps, shift=DOWN * 0.05), FadeIn(rand, shift=DOWN * 0.05), run_time=0.8)
        self.at(11.0)
        ar = Arrow(rand.get_bottom(), rand.get_bottom() + DOWN * 1.2,
                   color=YELL, buff=0.1, stroke_width=5, max_tip_length_to_length_ratio=0.3)
        loop = t("每猜错一次 → 反向传播调一次", 28, YELL, "BOLD").next_to(ar, DOWN, buff=0.4)
        self.play(Create(ar), FadeIn(loop, shift=DOWN * 0.05), run_time=0.7)
        self.at(17.0)
        learned = VGroup(dot_label("p1 学会「句首的特点」", GREEN, 26),
                         dot_label("p100 学会「中段的特点」", GREEN, 26)).arrange(DOWN, buff=0.6)
        learned.next_to(loop, DOWN, buff=1.2)
        self.play(FadeIn(learned, shift=DOWN * 0.05), run_time=0.8)

        # 页2：长度外推断层
        self.at(22.5)
        self.play(FadeOut(VGroup(lab, ps, rand, ar, loop, learned), shift=UP * 0.05), run_time=0.4)
        ok = boxed("训练见过 2048 个位置", 4.6, 1.1, GREEN, 28)
        bad = boxed("推理给 8192 个 token？", 4.6, 1.1, RED, 28)
        rows = VGroup(ok, bad).arrange(DOWN, buff=1.0).next_to(head, DOWN, buff=1.6)
        self.play(FadeIn(ok, shift=DOWN * 0.05), run_time=0.6)
        self.at(27.5)
        self.play(FadeIn(bad, shift=DOWN * 0.05), run_time=0.6)
        self.at(31.5)
        gap = t("p2049 到 p8192——根本没学过", 32, RED, "BOLD")
        fit(gap, 0.95)
        gap.next_to(rows, DOWN, buff=1.4)
        self.play(FadeIn(gap, scale=1.05), run_time=0.7)
        self.at(35.0)
        ext = boxed("长度外推问题", 3.6, 1.1, YELL, 32, fill=0.2, weight="BOLD")
        ext.next_to(gap, DOWN, buff=1.3)
        self.play(FadeIn(ext, scale=1.1), run_time=0.7)
        self.at(37.0)
        q = t("能不能把「相隔多远」直接送进注意力？", 30, CYAN, "BOLD")
        fit(q, 0.95)
        q.next_to(ext, DOWN, buff=1.2)
        self.play(FadeIn(q, shift=DOWN * 0.05), run_time=0.6)
        self.pad_to_voice()


# ---------------- S5 RoPE：旋转 Q 和 K ----------------
class S5(_Base):
    def construct(self):
        self.footer()
        head = t("RoPE：旋转 Q 和 K", 40, YELL, "BOLD").to_edge(UP, buff=1.2)
        self.play(FadeIn(head, shift=DOWN * 0.05))

        # 页1：位置 0/1/2 旋转箭头
        self.at(1.0)
        lab = t("不把位置加进向量，而是旋转 Q / K", 30, WHITE)
        fit(lab, 0.95)
        lab.next_to(head, DOWN, buff=1.4)
        self.play(FadeIn(lab, shift=DOWN * 0.05))
        self.at(8.5)
        arrows = VGroup()
        for ang, pos, col in ((0, 0, GREEN), (0.9, 1, CYAN), (1.9, 2, YELL)):
            a = Arrow(ORIGIN, np.array([np.cos(ang), np.sin(ang), 0]) * 1.2,
                      color=col, stroke_width=6, buff=0)
            cap = t(f"位置 {pos}", 24, col).next_to(a, DOWN * 0.8 + RIGHT * 0.6)
            arrows.add(VGroup(a, cap))
        arrows.arrange(RIGHT, buff=2.1).next_to(lab, DOWN, buff=1.6)
        fit(arrows, 0.95)
        for g in arrows:
            self.play(Create(g[0]), FadeIn(g[1], shift=DOWN * 0.05), run_time=0.7)
        self.at(16.0)
        note = t("旋转只改变方向，不改变长度", 30, GREEN, "BOLD")
        fit(note, 0.95)
        note.next_to(arrows, DOWN, buff=1.4)
        self.play(FadeIn(note, shift=DOWN * 0.05), run_time=0.7)

        # 页2：j−i 相对距离
        self.at(18.5)
        self.play(FadeOut(VGroup(lab, arrows, note), shift=UP * 0.05), run_time=0.4)
        f1 = t("qᵢ′ = R(iθ) qᵢ", 46, GREEN)
        f2 = t("kⱼ′ = R(jθ) kⱼ", 46, CYAN)
        fs = VGroup(f1, f2).arrange(DOWN, buff=0.6).next_to(head, DOWN, buff=1.2)
        self.play(FadeIn(fs, shift=DOWN * 0.05), run_time=0.8)
        self.at(24.5)
        f3 = t("qᵢ′·kⱼ′ = qᵢᵀ R((j−i)θ) kⱼ", 50, YELL)
        f3.next_to(fs, DOWN, buff=1.1)
        self.play(FadeIn(f3, shift=DOWN * 0.05), run_time=0.8)
        self.at(30.5)
        rel = boxed("关键：j − i，只和「相隔多远」有关", 5.0, 1.0, YELL, 30, fill=0.2, weight="BOLD")
        rel.next_to(f3, DOWN, buff=1.0)
        self.play(FadeIn(rel, scale=1.1), run_time=0.7)
        self.at(36.5)
        pair = VGroup(dot_label("第 3 看第 4：间隔 1", CYAN, 26),
                      dot_label("第 100 看第 101：间隔 1", CYAN, 26)).arrange(DOWN, buff=0.5)
        pair.next_to(rel, DOWN, buff=1.0)
        self.play(FadeIn(pair, shift=DOWN * 0.05), run_time=0.8)
        self.at(41.0)
        fin = t("绝对位置参与，留下的是相对距离", 30, GREEN, "BOLD")
        fit(fin, 0.95)
        fin.next_to(pair, DOWN, buff=0.8)
        self.play(FadeIn(fin, scale=0.95), run_time=0.7)
        self.pad_to_voice()


# ---------------- S6 二维小实验 ----------------
class S6(_Base):
    def construct(self):
        self.footer()
        head = t("二维小实验：旋转 60°", 40, YELL, "BOLD").to_edge(UP, buff=1.2)
        self.play(FadeIn(head, shift=DOWN * 0.05))

        # 页1：q=(1,0) 旋转 60° / 120°
        self.at(1.0)
        axes = VGroup(
            Arrow(LEFT * 3.2, RIGHT * 3.2, color=MUTED, buff=0, stroke_width=3),
            Arrow(DOWN * 1.9, UP * 1.9, color=MUTED, buff=0, stroke_width=3),
        ).next_to(head, DOWN, buff=1.6)
        self.play(Create(axes[0]), Create(axes[1]), run_time=0.7)
        origin = axes.get_center()  # 坐标轴交叉点（对称 VGroup 中心）——箭头/弧必须以此为起点
        self.at(4.5)
        q0 = Arrow(origin, origin + RIGHT * 1.6, color=GREEN, buff=0, stroke_width=6)
        l0 = t("q0 = (1, 0)", 22, GREEN).next_to(q0.get_end(), DOWN * 0.7 + RIGHT * 0.6)
        self.play(Create(q0), FadeIn(l0, shift=DOWN * 0.05), run_time=0.7)
        self.at(9.5)
        ang60 = 60 * np.pi / 180
        q1 = Arrow(origin, origin + np.array([np.cos(ang60), np.sin(ang60), 0]) * 1.6,
                   color=CYAN, buff=0, stroke_width=6)
        l1 = t("q1 = (0.5, 0.866)", 22, CYAN).next_to(q1.get_end(), UP * 0.5 + RIGHT * 0.5)
        self.play(Create(q1), FadeIn(l1, shift=DOWN * 0.05), run_time=0.7)
        self.at(15.0)
        ang120 = 120 * np.pi / 180
        q2 = Arrow(origin, origin + np.array([np.cos(ang120), np.sin(ang120), 0]) * 1.6,
                   color=YELL, buff=0, stroke_width=6)
        l2 = t("q2 = (−0.5, 0.866)", 22, YELL).next_to(q2.get_end(), UP * 0.5 + LEFT * 0.5)
        self.play(Create(q2), FadeIn(l2, shift=DOWN * 0.05), run_time=0.7)
        self.at(20.5)
        arc = Arc(radius=1.9, start_angle=0, angle=ang60, color=YELL, stroke_width=3).move_to(origin)
        al = t("60°", 24, YELL, "BOLD").move_to(origin + np.array([np.cos(np.pi / 6), np.sin(np.pi / 6), 0]) * 1.25)
        self.play(Create(arc), FadeIn(al, shift=DOWN * 0.05), run_time=0.6)

        # 页2：位置 7-8 夹角不变
        self.at(25.5)
        self.play(FadeOut(VGroup(axes, q0, l0, q1, l1, q2, l2, arc, al), shift=UP * 0.05), run_time=0.4)
        lab = t("换成位置 7 和 8，每步仍转 60°", 32, WHITE).next_to(head, DOWN, buff=1.5)
        self.play(FadeIn(lab, shift=DOWN * 0.05))
        self.at(29.5)
        a7 = Arrow(ORIGIN, RIGHT * 1.5, color=CYAN, buff=0, stroke_width=6).next_to(lab, DOWN, buff=2.0)
        a8 = Arrow(ORIGIN, np.array([np.cos(ang60), np.sin(ang60), 0]) * 1.5,
                   color=YELL, buff=0, stroke_width=6).next_to(lab, DOWN, buff=2.0)
        pair = VGroup(a7, a8).arrange(RIGHT, buff=1.6).next_to(lab, DOWN, buff=1.6)
        l7 = t("位置 7", 24, CYAN).next_to(a7, UP * 0.5)
        l8 = t("位置 8", 24, YELL).next_to(a8, UP * 0.5)
        self.play(Create(a7), FadeIn(l7, shift=DOWN * 0.05), Create(a8), FadeIn(l8, shift=DOWN * 0.05), run_time=0.9)
        self.at(34.0)
        same = t("夹角还是 60°——相邻位置的旋转差，恒定", 30, GREEN, "BOLD")
        fit(same, 0.95)
        same.next_to(pair, DOWN, buff=1.5)
        self.play(FadeIn(same, scale=1.05), run_time=0.7)
        self.at(37.0)
        q = t("那真实模型里，旋转速度由谁决定？", 30, CYAN, "BOLD")
        fit(q, 0.95)
        q.next_to(same, DOWN, buff=1.1)
        self.play(FadeIn(q, shift=DOWN * 0.05), run_time=0.6)
        self.pad_to_voice()


# ---------------- S7 真实模型 rope_theta 对比 ----------------
class S7(_Base):
    def construct(self):
        self.footer()
        head = t("真实模型：rope_theta 旋钮", 40, YELL, "BOLD").to_edge(UP, buff=1.2)
        self.play(FadeIn(head, shift=DOWN * 0.05))

        # 页1：三模型对比卡片（网格）
        self.at(0.5)
        lab = t("三个国产模型的 config.json", 30, WHITE).next_to(head, DOWN, buff=1.4)
        self.play(FadeIn(lab, shift=DOWN * 0.05))
        self.at(4.5)
        m1 = VGroup(boxed("DeepSeek-V4 Pro", 4.6, 0.9, GREEN, 26),
                    t("θ = 10000 · 旋转最快", 26, GREEN),
                    t("YaRN：64K → 1M", 24, MUTED)).arrange(DOWN, buff=0.4)
        m2 = VGroup(boxed("Qwen3-235B", 4.6, 0.9, CYAN, 26),
                    t("θ = 100 万 · 中间值", 26, CYAN),
                    t("原生 32K", 24, MUTED)).arrange(DOWN, buff=0.4)
        m3 = VGroup(boxed("GLM-5.2", 4.6, 0.9, YELL, 26),
                    t("θ = 800 万 · 极慢", 26, YELL),
                    t("原生覆盖 1M", 24, MUTED)).arrange(DOWN, buff=0.4)
        grid = VGroup(m1, m2, m3).arrange(RIGHT, buff=0.8).next_to(lab, DOWN, buff=1.4)
        fit(grid, 0.95)
        self.play(FadeIn(m1, shift=DOWN * 0.05), run_time=0.8)  # 配音 4.2s 讲 DeepSeek
        self.at(19.5)
        self.play(FadeIn(m2, shift=DOWN * 0.05), run_time=0.8)  # 配音 19.4s 讲 Qwen3
        self.at(25.5)
        self.play(FadeIn(m3, shift=DOWN * 0.05), run_time=0.8)  # 配音 ~25s 讲 GLM
        self.at(31.5)
        note = t("θ 越大，旋转越慢，覆盖越远", 30, YELL, "BOLD")
        fit(note, 0.95)
        note.next_to(grid, DOWN, buff=1.4)
        self.play(FadeIn(note, shift=DOWN * 0.05), run_time=0.7)

        # 页2：拧快 vs 拧慢 取舍（配音 32.7s 讲“所以 θ 不是越大越好”）
        self.at(33.0)
        self.play(FadeOut(VGroup(lab, grid, note), shift=UP * 0.05), run_time=0.4)
        knob = t("θ 不是越大越好，它是一个旋钮", 34, YELL, "BOLD")
        fit(knob, 0.95)
        knob.next_to(head, DOWN, buff=1.5)
        self.play(FadeIn(knob, shift=DOWN * 0.05), run_time=0.7)
        self.at(34.5)
        fast = boxed("拧快：近处清，远处糊", 4.6, 1.1, GREEN, 28)
        slow = boxed("拧慢：看得远，近处靠训练补", 4.6, 1.1, CYAN, 28)
        rows = VGroup(fast, slow).arrange(DOWN, buff=0.9).next_to(knob, DOWN, buff=1.4)
        self.play(FadeIn(fast, shift=DOWN * 0.05), run_time=0.6)
        self.at(38.5)
        self.play(FadeIn(slow, shift=DOWN * 0.05), run_time=0.6)
        self.at(41.5)
        q = t("取舍，没有标准答案", 30, MUTED).next_to(rows, DOWN, buff=1.3)
        self.play(FadeIn(q, shift=DOWN * 0.05), run_time=0.6)
        self.pad_to_voice()


# ---------------- S8 总结 + 品牌尾卡 ----------------
class S8(_Base):
    def construct(self):
        self.footer()
        head = t("位置编码补上了什么？", 40, YELL, "BOLD").to_edge(UP, buff=1.2)
        self.play(FadeIn(head, shift=DOWN * 0.05))

        # 页1：分工 + 方案链
        self.at(1.0)
        w1 = boxed("词嵌入：这是猫", 3.4, 1.0, GREEN, 28)
        w2 = boxed("位置编码：猫排第 1", 3.4, 1.0, YELL, 28)
        pair = VGroup(w1, w2).arrange(RIGHT, buff=0.9).next_to(head, DOWN, buff=1.5)
        self.play(FadeIn(pair, shift=DOWN * 0.05), run_time=0.7)
        self.at(6.5)
        chain = VGroup(boxed("绝对位置", 2.2, 0.9, CYAN, 24),
                       boxed("正弦", 1.6, 0.9, CYAN, 24),
                       boxed("可学习", 2.0, 0.9, CYAN, 24),
                       boxed("RoPE", 1.8, 0.9, YELL, 24, fill=0.25, weight="BOLD"))
        chain.arrange(RIGHT, buff=0.45).next_to(pair, DOWN, buff=1.4)
        fit(chain, 0.95)
        self.play(FadeIn(chain, shift=DOWN * 0.05), run_time=0.8)
        self.at(20.5)
        key = boxed("词是谁重要，隔多远同样重要", 5.4, 1.2, YELL, 32, fill=0.2, weight="BOLD")
        key.next_to(chain, DOWN, buff=1.4)
        self.play(FadeIn(key, scale=1.1), run_time=0.8)
        self.at(25.0)
        nxt = t("下一篇：拆开 Q、K、V，看注意力怎么算「该看谁」", 28, CYAN)
        fit(nxt, 0.95)
        nxt.next_to(key, DOWN, buff=1.2)
        self.play(FadeIn(nxt, shift=DOWN * 0.05), run_time=0.6)

        # 页2：品牌尾卡（配音 29.2s 才讲关注句，切页跟到其后）
        self.at(28.5)
        self.play(FadeOut(VGroup(pair, chain, key, nxt), shift=UP * 0.05), run_time=0.4)
        logo = ImageMobject("avatar-sjai-round.png")
        logo.scale_to_fit_width(3.6)
        logo.next_to(head, DOWN, buff=1.6)
        self.play(FadeIn(logo, shift=DOWN * 0.05), run_time=0.7)
        self.at(29.8)
        follow = t("关注「数解AI」", 40, YELL, "BOLD").next_to(logo, DOWN, buff=0.9)
        self.play(FadeIn(follow, scale=1.08), run_time=0.6)
        self.at(31.5)
        title = t("《位置编码怎么工作？词序一错意思全变》", 28, WHITE, "BOLD")
        fit(title, 0.95)
        title.next_to(follow, DOWN, buff=1.0)
        self.play(FadeIn(title, shift=DOWN * 0.05), run_time=0.6)
        self.at(34.0)
        link = t("查看公众号文章", 30, GREEN, "BOLD").next_to(title, DOWN, buff=0.8)
        self.play(FadeIn(link, scale=0.95), run_time=0.6)
        self.pad_to_voice()


# ---------------- 封面帧 ----------------
class Cover(Scene):
    """封面帧：系列标签 + 主/副标题 + RoPE 旋转箭头视觉 + 底部公众号 logo。
    渲染：python3 -m manim render -qm -s --disable_caching scenes.py Cover
    """
    def construct(self):
        logo = ImageMobject("avatar-sjai-round.png")
        logo.scale_to_fit_width(2.5)
        logo.to_edge(DOWN, buff=0.8)

        series = t("大模型原理 · 第 3 篇", 26, CYAN).to_edge(UP, buff=1.4)
        title = t("位置编码：词序一错意思全变", 48, YELL, "BOLD").next_to(series, DOWN, buff=0.55)
        subtitle = t("注意力怎么知道谁先谁后？", 34, WHITE).next_to(title, DOWN, buff=0.35)

        # 关键视觉：RoPE 旋转箭头（共原点扇形，禁止 arrange 破坏共点）
        arrows = [Arrow(ORIGIN, np.array([np.cos(ang), np.sin(ang), 0]) * 1.3,
                        color=col, stroke_width=7, buff=0)
                  for ang, col in ((0, GREEN), (0.9, CYAN), (1.9, YELL))]
        stage = VGroup(*arrows)
        stage.next_to(subtitle, DOWN, buff=1.5)
        fit(stage, 0.9)
        arc = Arc(radius=1.7, start_angle=0, angle=0.9, color=YELL, stroke_width=3)
        arc.move_to(stage[0].get_start())  # 弧心 = 扇形公共起点
        cap = t("位置不同 → 角度不同", 26, GREEN).next_to(stage, DOWN, buff=0.9)

        self.add(logo, series, title, subtitle, stage, arc, cap)


if __name__ == "__main__":
    pass
