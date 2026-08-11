#!/usr/bin/env python3
"""《注意力机制是什么？别再当数据库查询》视频号 Manim 动画（竖屏 1080×1920）

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

# 配音时长（tts_split.py 实测 2026-08-14），渲染时长 = 配音 + 缓冲
VOICE_DUR = {'S1': 16.22, 'S2': 25.16, 'S3': 26.29, 'S4': 21.5, 'S5': 25.36, 'S6': 24.96, 'S7': 21.24, 'S8': 34.77}
TAIL = 2.5


def t(text: str, size: float = 34, color: str = WHITE, weight: str = "NORMAL") -> Text:
    return Text(text, font=FONT, font_size=size, color=color, weight=weight)


def boxed(label: str, w: float, h: float, color: str, fs: float = 28,
          fill: float = 0.12, wc=None, weight: str = "NORMAL") -> VGroup:
    """固定尺寸框 + 限宽文字（文字 ≤ 框宽 78%，只缩小不放大——短字符保持原大小防溢出）。"""
    txt = t(label, fs, wc or color, weight)
    if txt.width > w * 0.78:
        txt.set_width(w * 0.78)
    box = Rectangle(width=w, height=h, color=color,
                    fill_color=color, fill_opacity=fill)
    return VGroup(box, txt)


def sqrt_group(d_size: float = 52, color: str = YELL, weight: str = "BOLD") -> VGroup:
    """手绘 √d。结构仿 LaTeX \\sqrt{d}：斜线从横线左端连到 d 左下（斜率≈2），d 顶紧贴横线（2026-08-11 两轮返工定稿）。"""
    d = Text("d", font=FONT, font_size=d_size, color=color, weight=weight)
    w, h = d.width, d.height
    sw = max(3, int(d_size / 5))
    bar = Line(np.array([-0.8 * w, 0.62 * h, 0]), np.array([1.08 * w, 0.62 * h, 0]),
               color=color, stroke_width=sw)
    diag = Line(np.array([-0.68 * w, 0.62 * h, 0]), np.array([0.28 * w, -0.55 * h, 0]),
                color=color, stroke_width=sw)
    d.shift(RIGHT * 0.55 * w + UP * 0.10 * h)  # d 顶 0.60h，横线 0.62h → 空隙 0.02h
    return VGroup(bar, diag, d)


def fit(mob, frac: float = 0.85):
    """宽内容守卫：不超过画布宽的 frac（只缩小不放大——短文字保持原大小）。"""
    if mob.width > config.frame_width * frac:
        return mob.set_width(config.frame_width * frac)
    return mob


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

    def play_red_cross(self, target, run_time: float = 0.65):
        """大红叉动态盖在 target 上：两笔从中心生长成交叉 + 弹跳强调（2026-08-11 用户要求动态效果）。"""
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


# ---------------- S1 开场钩子：注意力 ≠ 数据库查询 ----------------
class S1(_Base):
    def construct(self):
        self.footer()
        head = t("注意力 ≠ 数据库查询", 40, YELL, "BOLD").to_edge(UP, buff=1.2)
        self.play(FadeIn(head, shift=DOWN * 0.05))

        # 页1：数据库类比三卡 + 划掉
        self.at(1.11)
        lab = t("有人说：像数据库一样", 28, MUTED).next_to(head, DOWN, buff=1.3)
        self.play(FadeIn(lab, shift=DOWN * 0.05))
        self.at(2.89)
        cards = VGroup(boxed("Q = 查询", 3.4, 1.0, CYAN, 30),
                       boxed("K = 键", 3.4, 1.0, CYAN, 30),
                       boxed("V = 值", 3.4, 1.0, CYAN, 30))
        cards.arrange(DOWN, buff=0.55).next_to(lab, DOWN, buff=0.9)
        self.play(FadeIn(cards, shift=DOWN * 0.05), run_time=0.8)
        self.at(7.78)
        bad = t("这个说法，帮倒忙", 36, RED, "BOLD").next_to(cards, DOWN, buff=1.1)
        self.play(FadeIn(bad, scale=1.05), run_time=0.6)
        self.at(8.6)
        cross = self.play_red_cross(cards)

        # 页2：真正的问题
        self.at(10.3)
        self.play(FadeOut(VGroup(lab, cards, bad, cross), shift=UP * 0.05), run_time=0.4)
        q = t("注意力到底是什么？", 38, CYAN, "BOLD").next_to(head, DOWN, buff=1.85)
        self.play(FadeIn(q, shift=DOWN * 0.05), run_time=0.6)
        self.at(12.0)
        steps = VGroup(boxed("内积", 1.5, 0.9, GREEN, 26),
                       boxed("缩放", 1.5, 0.9, CYAN, 26),
                       boxed("归一化", 1.5, 0.9, YELL, 26),
                       boxed("求和", 1.5, 0.9, WHITE, 26))
        steps.arrange(RIGHT, buff=0.5).next_to(q, DOWN, buff=1.15)
        self.play(FadeIn(steps, shift=DOWN * 0.05), run_time=0.7)
        self.at(13.8)
        ans = boxed("先看它怎么算", 4.2, 1.2, YELL, 34, fill=0.2, weight="BOLD")
        ans.next_to(steps, DOWN, buff=1.1)
        ar = Arrow(steps.get_bottom(), ans.get_top(), color=YELL, buff=0.15, stroke_width=5)
        self.play(Create(ar), FadeIn(ans, shift=DOWN * 0.05), run_time=0.8)
        self.pad_to_voice()


# ---------------- S2 四步计算：内积→缩放→softmax→加权求和 ----------------
class S2(_Base):
    def construct(self):
        self.footer()
        head = t("注意力四步算法", 40, YELL, "BOLD").to_edge(UP, buff=1.2)
        self.play(FadeIn(head, shift=DOWN * 0.05))

        # 页1：token 生成 QKV + 四步链路
        self.at(1.03)
        tok = boxed("追", 1.6, 1.0, CYAN, 34)
        qkv = VGroup(boxed("Q", 1.2, 0.9, YELL, 30),
                     boxed("K", 1.2, 0.9, GREEN, 30),
                     boxed("V", 1.2, 0.9, CYAN, 30))
        qkv.arrange(RIGHT, buff=0.4)
        row = VGroup(tok, qkv).arrange(RIGHT, buff=1.0).next_to(head, DOWN, buff=1.2)
        lab = t("每个 token 生成三个向量", 28, MUTED).next_to(row, DOWN, buff=0.6)
        self.play(FadeIn(row, shift=DOWN * 0.05), FadeIn(lab, shift=DOWN * 0.05), run_time=0.8)
        self.at(5.33)
        s1 = boxed("① Q·K 内积 → 分数", 3.6, 1.05, GREEN, 26)
        s2 = VGroup(Rectangle(width=3.6, height=1.05, color=CYAN, fill_color=CYAN, fill_opacity=0.12),
                    VGroup(t("② 分数 ÷ ", 26, CYAN), sqrt_group(26, CYAN),
                           t(" 缩放", 26, CYAN)).arrange(RIGHT, buff=0.1).set_width(3.6 * 0.78))
        s3 = boxed("③ softmax → 权重", 3.6, 1.05, YELL, 26)
        s4 = boxed("④ 权重 × V 加权求和", 3.6, 1.05, WHITE, 26)
        grid = VGroup(s1, s2, s3, s4).arrange_in_grid(2, 2, buff=0.45)
        grid.next_to(lab, DOWN, buff=1.6)
        self.play(FadeIn(s1, shift=DOWN * 0.05), run_time=0.6)
        self.at(9.03)
        self.play(FadeIn(s2, shift=DOWN * 0.05), run_time=0.6)
        self.at(11.49)
        self.play(FadeIn(s3, shift=DOWN * 0.05), run_time=0.6)
        self.at(14.15)
        self.play(FadeIn(s4, shift=DOWN * 0.05), run_time=0.6)

        # 页2：四步而已 + 问句
        self.at(17.23)
        self.play(FadeOut(VGroup(row, lab, s1, s2, s3, s4), shift=UP * 0.05), run_time=0.4)
        words = VGroup(t("内积", 40, GREEN), t("缩放", 40, CYAN),
                       t("归一化", 40, YELL), t("求和", 40, WHITE))
        words.arrange(RIGHT, buff=0.8).next_to(head, DOWN, buff=2.2)
        self.play(FadeIn(words, shift=DOWN * 0.05), run_time=0.8)
        self.at(18.67)
        only = t("四步而已", 44, YELL, "BOLD").next_to(words, DOWN, buff=1.2)
        self.play(FadeIn(only, scale=1.1), run_time=0.6)
        self.at(20.51)
        q = t("可它和数据库查询，差在哪？", 32, CYAN, "BOLD")
        fit(q, 0.95)
        q.next_to(only, DOWN, buff=1.65)
        self.play(FadeIn(q, shift=DOWN * 0.05), run_time=0.6)
        self.pad_to_voice()


# ---------------- S3 数据库 vs 圆桌 ----------------
class S3(_Base):
    def construct(self):
        self.footer()
        head = t("数据库 vs 注意力", 40, YELL, "BOLD").to_edge(UP, buff=1.2)
        self.play(FadeIn(head, shift=DOWN * 0.05))

        # 页1：一方查 vs 双方互问
        self.at(0.8)
        dbl = boxed("查询方", 2.6, 1.0, CYAN, 28)
        dbr = boxed("被查方", 2.6, 1.0, MUTED, 28)
        dbside = VGroup(dbl, dbr).arrange(RIGHT, buff=1.1).next_to(head, DOWN, buff=1.5)
        ar1 = Arrow(dbl.get_right(), dbr.get_left(), color=CYAN, buff=0.15, stroke_width=5)
        cap1 = t("数据库：一方查、一方被查", 26, MUTED).next_to(dbside, DOWN, buff=0.6)
        self.play(FadeIn(dbside, shift=DOWN * 0.05), run_time=0.6)
        self.play(Create(ar1), run_time=0.4)
        self.play(FadeIn(cap1, shift=DOWN * 0.05), run_time=0.5)
        self.at(4.08)
        att = VGroup(boxed("Q", 1.1, 0.85, YELL, 28),
                     boxed("K", 1.1, 0.85, GREEN, 28),
                     boxed("V", 1.1, 0.85, CYAN, 28))
        att.arrange(RIGHT, buff=0.35)
        attside = VGroup(t("每个 token", 30, WHITE), att).arrange(DOWN, buff=0.4)
        attside.next_to(cap1, DOWN, buff=1.2)
        cap2 = t("注意力：同时生成 Q、K、V", 26, YELL, "BOLD").next_to(attside, DOWN, buff=0.8)
        self.play(FadeIn(attside, shift=DOWN * 0.05), run_time=0.7)
        self.play(FadeIn(cap2, shift=DOWN * 0.05), run_time=0.6)
        self.at(7.98)
        both = t("既是提问者，也是被提问者", 32, GREEN, "BOLD")
        fit(both, 0.95)
        both.next_to(cap2, DOWN, buff=1.2)
        self.play(FadeIn(both, scale=1.05), run_time=0.7)

        # 页2：token1 ↔ token2 双向打分
        self.at(10.91)
        self.play(FadeOut(VGroup(dbside, ar1, cap1, attside, cap2, both), shift=UP * 0.05), run_time=0.4)
        t1 = boxed("token 1", 2.6, 1.1, CYAN, 30)
        t2 = boxed("token 2", 2.6, 1.1, GREEN, 30)
        pair = VGroup(t1, t2).arrange(RIGHT, buff=2.2).next_to(head, DOWN, buff=2.0)
        self.play(FadeIn(pair, shift=DOWN * 0.05), run_time=0.6)
        self.at(12.6)
        up = Arrow(t1.get_top() + UP * 0.4, t2.get_top() + UP * 0.4,
                   color=YELL, buff=0, stroke_width=5)
        lup = t("Q1 × K2", 26, YELL, "BOLD").next_to(up, UP, buff=0.15)
        self.play(Create(up), FadeIn(lup, shift=DOWN * 0.05), run_time=0.6)
        self.at(14.9)
        dn = Arrow(t2.get_bottom() + DOWN * 0.4, t1.get_bottom() + DOWN * 0.4,
                   color=GREEN, buff=0, stroke_width=5)
        ldn = t("Q2 × K1", 26, GREEN, "BOLD").next_to(dn, DOWN, buff=0.15)
        self.play(Create(dn), FadeIn(ldn, shift=DOWN * 0.05), run_time=0.6)
        self.at(16.5)
        both2 = t("每个 token 同时在问、也在被问", 30, WHITE)
        fit(both2, 0.95)
        both2.next_to(pair, DOWN, buff=2.0)
        self.play(FadeIn(both2, shift=DOWN * 0.05), run_time=0.6)

        # 页3：圆桌讨论
        self.at(18.63)
        self.play(FadeOut(VGroup(pair, up, lup, dn, ldn, both2), shift=UP * 0.05), run_time=0.4)
        table = Circle(radius=1.0, color=YELL, stroke_width=4)
        tl = t("圆桌讨论", 30, YELL, "BOLD").move_to(table.get_center())
        ring = VGroup(table, tl)
        toks = VGroup()
        for i, (s, col) in enumerate((("猫", CYAN), ("追", YELL), ("老", GREEN), ("鼠", WHITE))):
            ang = i * np.pi / 2 + np.pi / 4
            tok = boxed(s, 1.3, 0.9, col, 28)
            tok.shift(np.array([np.cos(ang), np.sin(ang), 0]) * 1.9)
            toks.add(tok)
        ring = VGroup(ring, toks)
        ring.next_to(head, DOWN, buff=1.3)
        self.play(FadeIn(ring, shift=DOWN * 0.05), run_time=0.8)
        self.at(21.82)
        tags = t("名片 K · 提问 Q · 信息 V", 30, GREEN, "BOLD")
        fit(tags, 0.95)
        tags.next_to(ring, DOWN, buff=1.2)
        self.play(FadeIn(tags, shift=DOWN * 0.05), run_time=0.6)
        self.at(23.95)
        q = t("那它会只挑一条记录吗？", 32, CYAN, "BOLD")
        fit(q, 0.95)
        q.next_to(tags, DOWN, buff=1.0)
        self.play(FadeIn(q, shift=DOWN * 0.05), run_time=0.6)
        self.pad_to_voice()


# ---------------- S4 权重分配：不是只取一个 ----------------
class S4(_Base):
    def construct(self):
        self.footer()
        head = t("softmax：分配，不是选择", 40, YELL, "BOLD").to_edge(UP, buff=1.2)
        self.play(FadeIn(head, shift=DOWN * 0.05))

        # 页1：权重条 0.7 / 0.2 / 0.1
        self.at(1.4)
        lab = t("对每个允许的位置，softmax 给一个权重", 28, WHITE)
        fit(lab, 0.95)
        lab.next_to(head, DOWN, buff=1.45)
        self.play(FadeIn(lab, shift=DOWN * 0.05))
        self.at(2.8)
        bars = VGroup()
        for w, v, col in ((2.9, "0.7", CYAN), (1.0, "0.2", GREEN), (0.5, "0.1", MUTED)):
            bar = Rectangle(width=w, height=0.62, color=col, fill_color=col, fill_opacity=0.7)
            val = t(v, 28, col, "BOLD").next_to(bar, DOWN, buff=0.2)
            bars.add(VGroup(bar, val))
        bars.arrange(RIGHT, buff=0.9, aligned_edge=DOWN).next_to(lab, DOWN, buff=1.55)
        tok2 = t("token 2", 24, CYAN).next_to(bars[0], UP, buff=0.35)
        tok3 = t("token 3", 24, GREEN).next_to(bars[1], UP, buff=0.35)
        tok4 = t("token 4", 24, MUTED).next_to(bars[2], UP, buff=0.35)
        toks = VGroup(tok2, tok3, tok4)
        self.play(FadeIn(toks, shift=DOWN * 0.05), FadeIn(bars, shift=DOWN * 0.05), run_time=0.9)
        self.at(5.79)
        notone = t("不是只取一个", 36, RED, "BOLD").next_to(bars, DOWN, buff=1.65)
        self.play(FadeIn(notone, scale=1.05), run_time=0.6)

        # 页2：e^x 永远为正 → 无零权重
        self.at(9.15)
        self.play(FadeOut(VGroup(lab, toks, bars, notone), shift=UP * 0.05), run_time=0.4)
        lab2 = t("指数函数永远为正", 32, WHITE).next_to(head, DOWN, buff=1.6)
        self.play(FadeIn(lab2, shift=DOWN * 0.05))
        self.at(10.08)
        axes = Axes(x_range=[-1, 3], y_range=[0, 4], x_length=6.4, y_length=3.2,
                    axis_config={"color": MUTED, "stroke_width": 3,
                                 "include_ticks": False, "include_tip": True})
        axes.next_to(lab2, DOWN, buff=0.9)
        curve = axes.plot(lambda x: 0.55 * np.exp(0.55 * x), x_range=[-0.8, 2.4],
                          color=GREEN, stroke_width=5)
        self.play(Create(axes), run_time=0.6)
        self.play(Create(curve), run_time=0.9)
        self.at(11.95)
        zero = t("softmax 之后，没有零权重", 34, YELL, "BOLD")
        fit(zero, 0.95)
        zero.next_to(curve, DOWN, buff=1.4)
        zero.set_x(0)  # 水平居中（next_to 对齐到 curve 偏移中心会超界）
        self.play(FadeIn(zero, scale=1.05), run_time=0.7)

        # 页3：关注 ≠ 只看一个
        self.at(15.4)
        self.play(FadeOut(VGroup(lab2, curve, zero), shift=UP * 0.05), run_time=0.4)
        look = t("「关注」= 只看一个", 36, WHITE)
        fit(look, 0.95)
        look.next_to(head, DOWN, buff=1.75)
        self.play(FadeIn(look, shift=DOWN * 0.05), run_time=0.6)
        self.at(16.6)
        self.play_red_cross(look)
        self.at(17.5)
        dist = t("「关注」= 权重分配", 36, GREEN, "BOLD").next_to(look, DOWN, buff=1.5)
        self.play(FadeIn(dist, scale=1.05), run_time=0.6)
        self.at(19.42)
        q = t("那公式里的矩阵，又是怎么回事？", 32, CYAN, "BOLD")
        fit(q, 0.95)
        q.next_to(dist, DOWN, buff=1.95)
        self.play(FadeIn(q, shift=DOWN * 0.05), run_time=0.6)
        self.pad_to_voice()


# ---------------- S5 矩阵只是并行打包 ----------------
class S5(_Base):
    def construct(self):
        self.footer()
        head = t("矩阵只是打包", 40, YELL, "BOLD").to_edge(UP, buff=1.2)
        self.play(FadeIn(head, shift=DOWN * 0.05))

        # 页1：公式卡 + 别被吓住
        self.at(1.05)
        f = VGroup(t("Attention(Q,K,V) = softmax(QKᵀ/", 30, WHITE),
                    sqrt_group(30, WHITE),
                    t(")V", 30, WHITE)).arrange(RIGHT, buff=0.06)
        f.set_width(config.frame_width * 0.9)
        f.next_to(head, DOWN, buff=1.6)
        self.play(FadeIn(f, shift=DOWN * 0.05), run_time=0.7)
        self.at(3.36)
        calm = t("别被矩阵吓住", 36, YELL, "BOLD").next_to(f, DOWN, buff=1.3)
        self.play(FadeIn(calm, scale=1.05), run_time=0.6)

        # 页2：第 i 行展开
        self.at(5.88)
        self.play(FadeOut(VGroup(f, calm), shift=UP * 0.05), run_time=0.4)
        lab = t("QKᵀ 的第 i 行，是什么？", 30, WHITE).next_to(head, DOWN, buff=1.4)
        self.play(FadeIn(lab, shift=DOWN * 0.05))
        self.at(7.13)
        qi = boxed("qᵢ", 1.4, 1.0, YELL, 30)
        ks = VGroup(*[boxed(f"k{j}", 1.4, 1.0, GREEN, 26) for j in (1, 2, 3)])
        ks.arrange(DOWN, buff=0.5)
        row = VGroup(qi, ks).arrange(RIGHT, buff=1.4).next_to(lab, DOWN, buff=1.3)
        ell = t("…之前所有 K", 24, MUTED).next_to(ks, DOWN, buff=0.4)
        self.play(FadeIn(row, shift=DOWN * 0.05), FadeIn(ell, shift=DOWN * 0.05), run_time=0.8)
        self.at(9.97)
        scores = VGroup()
        for k in ks:
            ar = Arrow(qi.get_right(), k.get_left(), color=CYAN, buff=0.15, stroke_width=4)
            scores.add(ar)
        self.play(*[Create(a) for a in scores], run_time=0.9)
        self.at(12.59)
        rowlab = t("第 i 个 token 拿自己的 Q，和每个 K 打分", 28, CYAN)
        fit(rowlab, 0.75)
        rowlab.next_to(ell, DOWN, buff=1.0)
        rowlab.set_x(0)  # next_to 对齐到 ell 偏移中心会超界，强制水平居中
        self.play(FadeIn(rowlab, shift=DOWN * 0.05), run_time=0.6)

        # 页3：N 行打包 → GPU
        self.at(15.74)
        self.play(FadeOut(VGroup(lab, row, ell, scores, rowlab), shift=UP * 0.05), run_time=0.4)
        lab2 = t("N 个 token，各算各的", 30, WHITE).next_to(head, DOWN, buff=1.5)
        self.play(FadeIn(lab2, shift=DOWN * 0.05))
        self.at(16.79)
        rows = VGroup(*[boxed(f"token {j}", 3.0, 0.85, CYAN, 24) for j in range(1, 5)])
        rows.arrange_in_grid(2, 2, buff=0.4).next_to(lab2, DOWN, buff=1.0)
        self.play(FadeIn(rows, shift=DOWN * 0.05), run_time=0.9)
        self.at(19.41)
        pack = t("打包成矩阵 → GPU 一次算完", 32, YELL, "BOLD")
        fit(pack, 0.95)
        pack.next_to(rows, DOWN, buff=1.1)
        self.play(FadeIn(pack, scale=1.05), run_time=0.7)
        self.at(22.45)
        q = t("那凭什么内积能当匹配分数？", 32, CYAN, "BOLD")
        fit(q, 0.95)
        q.next_to(pack, DOWN, buff=1.1)
        self.play(FadeIn(q, shift=DOWN * 0.05), run_time=0.6)
        self.pad_to_voice()


# ---------------- S6 内积几何 + 除以 √d ----------------
class S6(_Base):
    def construct(self):
        self.footer()
        head = t("内积为什么能打分？", 40, YELL, "BOLD").to_edge(UP, buff=1.2)
        self.play(FadeIn(head, shift=DOWN * 0.05))

        # 页1：二维向量图 q / k1 / k2
        self.at(1.09)
        lab = t("⟨Q,K⟩ = ‖Q‖ ‖K‖ cosθ", 34, WHITE).next_to(head, DOWN, buff=1.3)
        self.play(FadeIn(lab, shift=DOWN * 0.05))
        self.at(2.72)
        origin = np.array([0.0, -0.4, 0.0])
        axes = VGroup(
            Arrow(origin + LEFT * 3.1, origin + RIGHT * 3.1, color=MUTED, buff=0, stroke_width=3),
            Arrow(origin + DOWN * 2.2, origin + UP * 2.2, color=MUTED, buff=0, stroke_width=3),
        )
        axes.next_to(lab, DOWN, buff=1.2)
        origin = axes.get_center() + DOWN * 0.0
        self.play(Create(axes[0]), Create(axes[1]), run_time=0.7)
        self.at(3.8)
        qv = Arrow(origin, origin + np.array([1.9, 0.5, 0]) * 0.62, color=YELL, buff=0, stroke_width=7)
        k1v = Arrow(origin, origin + np.array([2.2, 1.35, 0]) * 0.62, color=GREEN, buff=0, stroke_width=7)
        k2v = Arrow(origin, origin + np.array([0.3, -2.0, 0]) * 0.62, color=RED, buff=0, stroke_width=7)
        lq = t("q", 26, YELL, "BOLD").next_to(qv.get_end(), UP * 0.3 + RIGHT * 0.3)
        lk1 = t("k₁", 26, GREEN, "BOLD").next_to(k1v.get_end(), UP * 0.4)
        lk2 = t("k₂", 26, RED, "BOLD").next_to(k2v.get_end(), DOWN * 0.4 + RIGHT * 0.4)
        self.play(Create(qv), FadeIn(lq, shift=DOWN * 0.05), run_time=0.6)
        self.play(Create(k1v), FadeIn(lk1, shift=DOWN * 0.05), Create(k2v), FadeIn(lk2, shift=DOWN * 0.05), run_time=0.8)
        self.at(6.16)
        q_ang = np.arctan2(0.5, 1.9)
        k1_ang = np.arctan2(1.35, 2.2)
        arc = Arc(radius=0.85, start_angle=q_ang, angle=k1_ang - q_ang,
                  color=YELL, stroke_width=4, arc_center=origin)
        self.play(Create(arc), run_time=0.5)
        self.at(7.43)
        align = t("方向越对齐 → 分数越高", 30, GREEN, "BOLD")
        fit(align, 0.95)
        align.next_to(axes, DOWN, buff=1.3)
        orth = t("正交 → 分数为零", 30, RED).next_to(align, DOWN, buff=0.55)
        self.play(FadeIn(align, shift=DOWN * 0.05), run_time=0.6)
        self.play(FadeIn(orth, shift=DOWN * 0.05), run_time=0.6)

        # 页2：维度膨胀
        self.at(10.42)
        self.play(FadeOut(VGroup(lab, axes, qv, lq, k1v, lk1, k2v, lk2, arc, align, orth), shift=UP * 0.05), run_time=0.4)
        lab2 = t("但分数会随维度膨胀", 32, WHITE).next_to(head, DOWN, buff=1.6)
        self.play(FadeIn(lab2, shift=DOWN * 0.05))
        self.at(11.32)
        ok = boxed("d = 64 → 内积 ±10", 4.4, 1.1, GREEN, 28)
        boom = boxed("d = 4096 → 内积 ±100", 4.4, 1.1, RED, 28)
        rows = VGroup(ok, boom).arrange(DOWN, buff=0.9).next_to(lab2, DOWN, buff=1.4)
        self.play(FadeIn(ok, shift=DOWN * 0.05), run_time=0.6)
        self.at(13.58)
        self.play(FadeIn(boom, shift=DOWN * 0.05), run_time=0.6)
        self.at(15.85)
        hot = t("softmax 退化成 one-hot", 34, RED, "BOLD")
        fit(hot, 0.95)
        hot.next_to(rows, DOWN, buff=1.25)
        self.play(FadeIn(hot, scale=1.05), run_time=0.7)

        # 页3：除以 √d
        self.at(20.11)
        self.play(FadeOut(VGroup(lab2, ok, boom, hot), shift=UP * 0.05), run_time=0.4)
        div = VGroup(t("除以 ", 52, YELL, "BOLD"), sqrt_group(52, YELL, "BOLD")).arrange(RIGHT, buff=0.15)
        div.next_to(head, DOWN, buff=1.6)
        self.play(FadeIn(div, scale=0.9), run_time=0.6)
        self.at(21.92)
        fix = t("把内积方差压回可控范围", 32, GREEN, "BOLD")
        fit(fix, 0.95)
        fix.next_to(div, DOWN, buff=1.5)
        self.play(FadeIn(fix, shift=DOWN * 0.05), run_time=0.6)
        self.at(23.18)
        q = t("一个头，只学一种问法吗？", 32, CYAN, "BOLD")
        fit(q, 0.95)
        q.next_to(fix, DOWN, buff=1.95)
        self.play(FadeIn(q, shift=DOWN * 0.05), run_time=0.6)
        self.pad_to_voice()


# ---------------- S7 多头注意力 ----------------
class S7(_Base):
    def construct(self):
        self.footer()
        head = t("多头注意力：多套问法", 40, YELL, "BOLD").to_edge(UP, buff=1.2)
        self.play(FadeIn(head, shift=DOWN * 0.05))

        # 页1：单头 → 多头 + Qwen3-8B 参数
        self.at(1.31)
        single = boxed("一个头：一套 QKV 投影", 4.6, 1.1, CYAN, 28)
        single.next_to(head, DOWN, buff=1.5)
        self.play(FadeIn(single, shift=DOWN * 0.05), run_time=0.5)
        self.at(2.22)
        self.play(FadeOut(single, shift=UP * 0.05), run_time=0.3)
        heads = VGroup()
        for col in (GREEN, CYAN, YELL):
            h = VGroup(t("头", 26, col, "BOLD"),
                       boxed("Q", 0.85, 0.7, col, 24),
                       boxed("K", 0.85, 0.7, col, 24),
                       boxed("V", 0.85, 0.7, col, 24)).arrange(DOWN, buff=0.3)
            heads.add(h)
        heads.arrange(RIGHT, buff=0.7).next_to(head, DOWN, buff=1.4)
        self.play(FadeIn(heads, shift=DOWN * 0.05), run_time=0.8)
        self.at(4.04)
        qw = boxed("Qwen3-8B：4096 维 / 32 头 / 每头 128 维", 5.6, 1.2, YELL, 28, fill=0.2)
        qw.next_to(heads, DOWN, buff=1.4)
        self.play(FadeIn(qw, scale=1.06), run_time=0.7)

        # 页2：头分工
        self.at(10.41)
        self.play(FadeOut(VGroup(heads, qw), shift=UP * 0.05), run_time=0.4)
        lab = t("每个头学不同的「问法」", 30, WHITE).next_to(head, DOWN, buff=1.3)
        self.play(FadeIn(lab, shift=DOWN * 0.05))
        self.at(11.63)
        near = boxed("头 A：重视附近的词", 4.6, 1.1, GREEN, 28)
        ref = boxed("头 B：追踪指代对象", 4.6, 1.1, CYAN, 28)
        rows = VGroup(near, ref).arrange(DOWN, buff=0.7).next_to(lab, DOWN, buff=1.1)
        self.play(FadeIn(near, shift=DOWN * 0.05), run_time=0.6)
        self.at(13.65)
        self.play(FadeIn(ref, shift=DOWN * 0.05), run_time=0.6)
        self.at(15.16)
        key = t("多套独立投影，不是一副更大的眼镜", 32, YELL, "BOLD")
        fit(key, 0.95)
        key.next_to(rows, DOWN, buff=1.1)
        self.play(FadeIn(key, scale=1.05), run_time=0.7)
        self.at(18.8)
        q = t("这场加权汇总，代价是什么？", 32, CYAN, "BOLD")
        fit(q, 0.95)
        q.next_to(key, DOWN, buff=1.0)
        self.play(FadeIn(q, shift=DOWN * 0.05), run_time=0.6)
        self.pad_to_voice()


# ---------------- S8 代价 + 总结 + 品牌尾卡 ----------------
class S8(_Base):
    def construct(self):
        self.footer()
        head = t("注意力：加权汇总，不是检索", 40, YELL, "BOLD").to_edge(UP, buff=1.2)
        self.play(FadeIn(head, shift=DOWN * 0.05))

        # 页1：O(N²) + 64 倍 + GQA/MLA
        self.at(1.09)
        f = t("O(N²)", 52, YELL, "BOLD").next_to(head, DOWN, buff=1.2)
        self.play(FadeIn(f, scale=0.9), run_time=0.6)
        self.at(3.16)
        c1 = boxed("上下文 4K", 3.2, 1.0, CYAN, 28)
        c2 = boxed("上下文 32K", 3.2, 1.0, RED, 28)
        cs = VGroup(c1, c2).arrange(RIGHT, buff=1.2).next_to(f, DOWN, buff=1.3)
        ar = Arrow(c1.get_right(), c2.get_left(), color=YELL, buff=0.15, stroke_width=5)
        self.play(FadeIn(cs, shift=DOWN * 0.05), run_time=0.7)
        self.play(Create(ar), run_time=0.4)
        self.at(5.99)
        x64 = t("配对数量 × 64", 40, RED, "BOLD").next_to(cs, DOWN, buff=1.2)
        self.play(FadeIn(x64, scale=1.1), run_time=0.6)
        self.at(8.16)
        save = VGroup(boxed("GQA", 2.2, 0.9, GREEN, 26),
                      boxed("MLA", 2.2, 0.9, CYAN, 26)).arrange(RIGHT, buff=0.8)
        save.next_to(x64, DOWN, buff=1.4)
        sl = t("这些省法，只改开销，不改主线", 26, MUTED).next_to(save, DOWN, buff=0.55)
        self.play(FadeIn(save, shift=DOWN * 0.05), FadeIn(sl, shift=DOWN * 0.05), run_time=0.7)

        # 页2：总结定义
        self.at(11.97)
        self.play(FadeOut(VGroup(f, cs, ar, x64, save, sl), shift=UP * 0.05), run_time=0.4)
        lab = t("回到开头：注意力到底是什么？", 30, WHITE).next_to(head, DOWN, buff=1.5)
        self.play(FadeIn(lab, shift=DOWN * 0.05))
        self.at(13.28)
        summ = boxed("每个 token 按自己的需要，从上下文里做加权汇总", 6.0, 1.4, YELL, 30, fill=0.2, weight="BOLD")
        summ.next_to(lab, DOWN, buff=1.4)
        self.play(FadeIn(summ, scale=1.06), run_time=0.8)
        self.at(16.32)
        notdb = t("不是数据库查询", 36, WHITE)
        fit(notdb, 0.95)
        notdb.next_to(summ, DOWN, buff=1.4)
        self.play(FadeIn(notdb, shift=DOWN * 0.05), run_time=0.6)
        self.at(18.5)
        cross = self.play_red_cross(notdb)

        # 页3：品牌尾卡
        self.at(21.33)
        self.play(FadeOut(VGroup(lab, summ, notdb, cross), shift=UP * 0.05), run_time=0.4)
        logo = ImageMobject("avatar-sjai-round.png")
        logo.scale_to_fit_width(3.0)
        logo.next_to(head, DOWN, buff=1.0)
        self.play(FadeIn(logo, shift=DOWN * 0.05), run_time=0.7)
        self.at(23.07)
        follow = t("关注「数解AI」", 40, YELL, "BOLD").next_to(logo, DOWN, buff=0.6)
        self.play(FadeIn(follow, scale=1.08), run_time=0.6)
        self.at(24.81)
        title = t("《注意力机制是什么？别再当数据库查询》", 27, WHITE, "BOLD")
        fit(title, 0.95)
        title.next_to(follow, DOWN, buff=0.7)
        self.play(FadeIn(title, shift=DOWN * 0.05), run_time=0.6)
        self.at(26.99)
        link = t("查看公众号文章", 30, GREEN, "BOLD").next_to(title, DOWN, buff=0.55)
        self.play(FadeIn(link, scale=0.95), run_time=0.6)
        self.at(28.73)
        nxt = t("下一篇：拆 FFN，看知识存在哪", 27, CYAN, "BOLD")
        fit(nxt, 0.95)
        nxt.next_to(link, DOWN, buff=0.7)
        self.play(FadeIn(nxt, shift=DOWN * 0.05), run_time=0.6)
        self.at(31.12)
        ask = t("模型该更看重近的词，还是更相关但更远的词？评论区聊聊", 24, MUTED)
        fit(ask, 0.95)
        ask.next_to(nxt, DOWN, buff=0.6)
        self.play(FadeIn(ask, shift=DOWN * 0.05), run_time=0.6)
        self.pad_to_voice()


# ---------------- 封面帧 ----------------
class Cover(Scene):
    """封面帧：系列标签 + 主/副标题 + 权重分配视觉 + 底部公众号 logo。
    渲染：python3 -m manim render -qm -s --disable_caching scenes.py Cover
    关键内容须落在 3:4 安全区（frame y ∈ [-5.33, +5.33]）。
    """
    def construct(self):
        logo = ImageMobject("avatar-sjai-round.png")
        logo.scale_to_fit_width(2.2)
        logo.to_edge(DOWN, buff=1.9)

        series = t("大模型原理 · 第 4 篇", 26, CYAN).to_edge(UP, buff=2.5)
        title = t("注意力机制是什么？别再当数据库查询", 44, YELL, "BOLD")
        title.set_width(config.frame_width * 0.8)
        title.next_to(series, DOWN, buff=0.5)
        subtitle = t("不是数据库查询，是加权汇总", 32, WHITE).next_to(title, DOWN, buff=0.4)

        # 关键视觉：token 行 + 权重条 0.7 / 0.2 / 0.1
        toks = VGroup(*[t(s, 30, c) for s, c in (("猫", CYAN), ("追", YELL),
                                                  ("老", GREEN), ("鼠", WHITE))])
        toks.arrange(RIGHT, buff=0.8).next_to(subtitle, DOWN, buff=1.4)
        bars = VGroup()
        for w, v, col in ((2.7, "0.7", CYAN), (0.9, "0.2", GREEN), (0.45, "0.1", MUTED)):
            bar = Rectangle(width=w, height=0.6, color=col, fill_color=col, fill_opacity=0.7)
            val = t(v, 26, col, "BOLD").next_to(bar, DOWN, buff=0.18)
            bars.add(VGroup(bar, val))
        bars.arrange(RIGHT, buff=0.95, aligned_edge=DOWN)
        bars.next_to(toks, DOWN, buff=1.1)
        ar = Arrow(toks[1].get_bottom() + DOWN * 0.3, bars.get_top() + UP * 0.1,
                   color=YELL, buff=0.1, stroke_width=5)
        qkv = t("Q 提问 · K 名片 · V 信息", 26, GREEN, "BOLD").next_to(bars, DOWN, buff=1.0)

        self.add(logo, series, title, subtitle, toks, bars, ar, qkv)


if __name__ == "__main__":
    pass
