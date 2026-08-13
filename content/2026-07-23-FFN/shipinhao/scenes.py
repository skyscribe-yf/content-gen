#!/usr/bin/env python3
"""《Attention都够了，为什么还要前馈网络？》视频号 Manim 动画（竖屏 1080×1920）

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

# 配音时长（tts_split.py 实测 2026-08-18），渲染时长 = 配音 + 缓冲
VOICE_DUR = {'S1': 15.75, 'S2': 21.75, 'S3': 21.44, 'S4': 22.38, 'S5': 25.97, 'S6': 21.97, 'S7': 25.6, 'S8': 42.28}
TAIL = 2.5


def t(text: str, size: float = 34, color: str = WHITE, weight: str = "NORMAL") -> Text:
    return Text(text, font=FONT, font_size=size, color=color, weight=weight)


def mt(markup: str, size: float = 34, color: str = WHITE,
       weight: str = "NORMAL") -> MarkupText:
    return MarkupText(markup, font=FONT, font_size=size, color=color, weight=weight)


def sub_t(base: str, sub: str, size: float = 28, color: str = WHITE,
          weight: str = "NORMAL") -> MarkupText:
    """Render a compact, readable subscript label with Pango markup."""
    return MarkupText(
        f"{base}<sub><small>{sub}</small></sub>",
        font=FONT,
        font_size=size,
        color=color,
        weight=weight,
    )


def boxed_mob(label_mob, w: float, h: float, color: str,
              fill: float = 0.12) -> VGroup:
    """Put an already-rendered label in a fixed-size box, shrinking only."""
    if label_mob.width > w * 0.78:
        label_mob.set_width(w * 0.78)
    box = Rectangle(width=w, height=h, color=color,
                    fill_color=color, fill_opacity=fill)
    label_mob.move_to(box.get_center())
    return VGroup(box, label_mob)


def boxed_sub(base: str, sub: str, w: float, h: float, color: str,
              fs: float = 28, fill: float = 0.12,
              weight: str = "NORMAL") -> VGroup:
    return boxed_mob(sub_t(base, sub, fs, color, weight), w, h, color, fill)


def boxed(label: str, w: float, h: float, color: str, fs: float = 28,
          fill: float = 0.12, wc=None, weight: str = "NORMAL") -> VGroup:
    """固定尺寸框 + 限宽文字（文字 ≤ 框宽 78%，只缩小不放大——短字符保持原大小防溢出）。"""
    txt = t(label, fs, wc or color, weight)
    if txt.width > w * 0.78:
        txt.set_width(w * 0.78)
    box = Rectangle(width=w, height=h, color=color,
                    fill_color=color, fill_opacity=fill)
    return VGroup(box, txt)


def fit(mob, frac: float = 0.85):
    """宽内容守卫：不超过画布宽的 frac（只缩小不放大——短文字保持原大小）。"""
    if mob.width > config.frame_width * frac:
        return mob.set_width(config.frame_width * frac)
    return mob


def room(w: float, h: float, color: str = MUTED, sw: float = 4) -> VGroup:
    """无门思考室：三面墙（顶 + 左右），底边开放（无门）。"""
    top = Line(LEFT * w / 2, RIGHT * w / 2, color=color, stroke_width=sw)
    lft = Line(LEFT * w / 2, LEFT * w / 2 + DOWN * h, color=color, stroke_width=sw)
    rgt = Line(RIGHT * w / 2, RIGHT * w / 2 + DOWN * h, color=color, stroke_width=sw)
    return VGroup(top, lft, rgt)


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
        """大红叉动态盖在 target 上：两笔从中心生长成交叉 + 弹跳强调。"""
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


# ---------------- S1 开场钩子：Attention 都够了，为什么还要 FFN？ ----------------
class S1(_Base):
    def construct(self):
        self.footer()
        head = t("Attention 都够了？", 40, YELL, "BOLD").to_edge(UP, buff=1.2)
        self.play(FadeIn(head, shift=DOWN * 0.05))

        # 页1：上下文已汇入 token
        self.at(1.2)
        lab = t("注意力已把上下文汇入每个 token", 28, WHITE).next_to(head, DOWN, buff=2.2)
        self.play(FadeIn(lab, shift=DOWN * 0.05))
        self.at(2.3)
        toks = VGroup(*[boxed(s, 1.5, 1.0, c, 28) for s, c in (("猫", CYAN), ("追", YELL), ("老", GREEN))])
        toks.arrange(RIGHT, buff=0.7).next_to(lab, DOWN, buff=0.8)
        in_ar = Arrow(toks[1].get_top() + UP * 0.5, toks[1].get_top(),
                      color=GREEN, buff=0.1, stroke_width=5)
        in_lab = t("上下文", 24, GREEN, "BOLD").next_to(in_ar, UP, buff=0.12)
        self.play(FadeIn(toks, shift=DOWN * 0.05), run_time=0.8)
        self.play(Create(in_ar), FadeIn(in_lab, shift=DOWN * 0.05), run_time=0.6)
        self.at(3.6)
        qmark = t("？", 64, YELL, "BOLD").next_to(toks, DOWN, buff=2.8)
        self.play(FadeIn(qmark, scale=1.1), run_time=0.6)

        # 页2：为什么还要 FFN？参数占比对比
        self.at(5.2)
        self.play(FadeOut(VGroup(lab, toks, in_ar, in_lab, qmark), shift=UP * 0.05), run_time=0.4)
        why = t("为什么还要一块 FFN？", 34, WHITE, "BOLD").next_to(head, DOWN, buff=1.5)
        self.play(FadeIn(why, shift=DOWN * 0.05), run_time=0.6)
        self.at(6.6)
        att_bar = Rectangle(width=1.4, height=1.0, color=CYAN, fill_color=CYAN, fill_opacity=0.7)
        att_lab = t("注意力", 24, CYAN).next_to(att_bar, DOWN, buff=0.25)
        ffn_bar = Rectangle(width=3.2, height=1.0, color=YELL, fill_color=YELL, fill_opacity=0.7)
        ffn_lab = t("FFN", 24, YELL).next_to(ffn_bar, DOWN, buff=0.25)
        bars = VGroup(VGroup(att_bar, att_lab), VGroup(ffn_bar, ffn_lab))
        bars.arrange(RIGHT, buff=1.4, aligned_edge=DOWN).next_to(why, DOWN, buff=1.2)
        self.play(FadeIn(VGroup(att_bar, att_lab), shift=DOWN * 0.05), run_time=0.5)
        self.at(7.9)
        self.play(FadeIn(VGroup(ffn_bar, ffn_lab), shift=DOWN * 0.05), run_time=0.6)
        self.at(9.3)
        maxp = t("却占掉最多的参数", 30, YELL, "BOLD").next_to(bars, DOWN, buff=1.1)
        self.play(FadeIn(maxp, scale=1.05), run_time=0.6)
        self.at(10.3)
        no_talk = t("它还不让 token 交流", 30, WHITE).next_to(maxp, DOWN, buff=0.5)
        self.play(FadeIn(no_talk, shift=DOWN * 0.05), run_time=0.6)

        # 停顿 <#0.5#>：10.69-11.29 静止

        # 页3：这不矛盾吗？→ FFN 到底在干什么
        self.at(11.3)
        self.play(FadeOut(VGroup(why, att_bar, att_lab, ffn_bar, ffn_lab, maxp, no_talk), shift=UP * 0.05), run_time=0.4)
        q = t("这不矛盾吗？", 42, RED, "BOLD").next_to(head, DOWN, buff=1.6)
        self.play(FadeIn(q, scale=1.08), run_time=0.6)
        self.at(12.6)
        q2 = t("FFN，到底在干什么？", 34, CYAN, "BOLD").next_to(q, DOWN, buff=1.2)
        self.play(FadeIn(q2, shift=DOWN * 0.05), run_time=0.6)
        self.at(13.8)
        r = room(2.2, 1.5, YELL, 5)
        r.next_to(q2, DOWN, buff=1.1)
        rl = t("一间没有门的思考室？", 26, MUTED).next_to(r, DOWN, buff=0.5)
        self.play(FadeIn(r, shift=DOWN * 0.05), FadeIn(rl, shift=DOWN * 0.05), run_time=0.7)
        self.pad_to_voice()


# ---------------- S2 圆桌 vs 思考室 ----------------
class S2(_Base):
    def construct(self):
        self.footer()
        head = t("一层 Transformer 的工作流程", 36, YELL, "BOLD").to_edge(UP, buff=1.2)
        fit(head, 0.85)
        self.play(FadeIn(head, shift=DOWN * 0.05))

        # 页1：圆桌互相看
        self.at(1.2)
        lab = t("先围坐圆桌，听取彼此线索", 28, WHITE).next_to(head, DOWN, buff=1.3)
        self.play(FadeIn(lab, shift=DOWN * 0.05))
        self.at(2.4)
        table = Circle(radius=1.05, color=YELL, stroke_width=4)
        tl = t("注意力", 30, YELL, "BOLD").move_to(table.get_center())
        ring = VGroup(table, tl)
        toks = VGroup()
        for i, (s, col) in enumerate((("猫", CYAN), ("追", YELL), ("老", GREEN), ("鼠", WHITE))):
            ang = i * np.pi / 2 + np.pi / 4
            tok = boxed(s, 1.3, 0.9, col, 28)
            tok.shift(np.array([np.cos(ang), np.sin(ang), 0]) * 2.0)
            toks.add(tok)
        ring = VGroup(ring, toks)
        ring.next_to(lab, DOWN, buff=1.0)
        self.play(FadeIn(ring, shift=DOWN * 0.05), run_time=0.8)
        self.at(5.0)
        arcs = VGroup()
        for i in range(4):
            a1 = np.pi / 4 + i * np.pi / 2
            a2 = a1 + np.pi / 2
            arc = Arc(radius=1.28, start_angle=a1 + 0.2, angle=a2 - a1 - 0.4,
                      color=CYAN, stroke_width=3, arc_center=table.get_center())
            arcs.add(arc)
        self.play(*[Create(a) for a in arcs], run_time=0.8)
        self.at(6.9)
        look = t("互相看：跨 token 混合信息", 30, GREEN, "BOLD")
        fit(look, 0.95)
        look.next_to(ring, DOWN, buff=1.1)
        self.play(FadeIn(look, shift=DOWN * 0.05), run_time=0.6)

        # 页2：散会 → 思考室
        self.at(9.7)
        self.play(FadeOut(VGroup(lab, ring, arcs, look), shift=UP * 0.05), run_time=0.4)
        lab2 = t("散会后，回到没有门的思考室", 30, WHITE).next_to(head, DOWN, buff=1.0)
        self.play(FadeIn(lab2, shift=DOWN * 0.05), run_time=0.6)
        self.at(11.5)
        rooms = VGroup()
        for j, (s, col) in enumerate((("猫", CYAN), ("追", YELL), ("老", GREEN), ("鼠", WHITE))):
            r = room(1.7, 1.05, col, 4)
            tok = boxed(s, 1.1, 0.65, col, 24)
            grp = VGroup(tok, r).arrange(DOWN, buff=0.2)
            rooms.add(grp)
        rooms.arrange_in_grid(2, 2, buff=0.6).next_to(lab2, DOWN, buff=0.9)
        self.play(FadeIn(rooms, shift=DOWN * 0.05), run_time=0.9)
        self.at(13.6)
        note = t("各用各的设备，处理自己的笔记", 27, MUTED).next_to(rooms, DOWN, buff=0.5)
        self.play(FadeIn(note, shift=DOWN * 0.05), run_time=0.6)

        # 页3：FFN 标签
        self.at(15.6)
        self.play(FadeOut(VGroup(lab2, rooms, note), shift=UP * 0.05), run_time=0.4)
        lab3 = t("这间思考室，就是 FFN", 32, YELL, "BOLD").next_to(head, DOWN, buff=2.6)
        self.play(FadeIn(lab3, scale=1.06), run_time=0.6)
        self.at(17.6)
        d1 = t("注意力：互相看", 32, CYAN, "BOLD")
        d2 = t("FFN：各自想", 32, GREEN, "BOLD")
        divs = VGroup(d1, d2).arrange(DOWN, buff=0.9).next_to(lab3, DOWN, buff=1.6)
        self.play(FadeIn(d1, shift=DOWN * 0.05), run_time=0.6)
        self.at(19.2)
        self.play(FadeIn(d2, shift=DOWN * 0.05), run_time=0.6)
        self.at(20.2)
        sep = t("各干各的，互不打扰", 25, MUTED).next_to(divs, DOWN, buff=0.6)
        self.play(FadeIn(sep, shift=DOWN * 0.05), run_time=0.5)
        self.pad_to_voice()


# ---------------- S3 独立性：yᵢ = f(xᵢ) ----------------
class S3(_Base):
    def construct(self):
        self.footer()
        head = t("各自想，怎么个算法？", 40, YELL, "BOLD").to_edge(UP, buff=1.2)
        self.play(FadeIn(head, shift=DOWN * 0.05))

        # 页1：公式 yᵢ = f(xᵢ)
        self.at(1.2)
        lab = t("对每一行只做一件事", 28, WHITE).next_to(head, DOWN, buff=2.4)
        self.play(FadeIn(lab, shift=DOWN * 0.05))
        self.at(2.4)
        yi = t("yᵢ", 44, YELL, "BOLD")
        eq = t("=", 40, WHITE, "BOLD")
        fbox = Rectangle(width=1.6, height=1.2, color=GREEN, fill_color=GREEN, fill_opacity=0.12)
        f_txt = t("f", 40, GREEN, "BOLD").move_to(fbox.get_center())
        xi = t("xᵢ", 44, CYAN, "BOLD")
        fpart = VGroup(fbox, f_txt)
        fx = VGroup(fpart, xi).arrange(RIGHT, buff=0.25)
        formula = VGroup(yi, eq, fx).arrange(RIGHT, buff=0.35)
        formula.next_to(lab, DOWN, buff=1.0)
        self.play(FadeIn(formula, shift=DOWN * 0.05), run_time=0.8)
        self.at(4.4)
        in_ar = Arrow(xi.get_bottom() + DOWN * 0.4, xi.get_bottom(), color=CYAN, buff=0.1, stroke_width=4)
        in_lab = t("输入第 i 行", 22, CYAN).next_to(in_ar, DOWN, buff=0.12)
        self.play(Create(in_ar), FadeIn(in_lab, shift=DOWN * 0.05), run_time=0.6)
        self.at(6.0)
        out_ar = Arrow(yi.get_top(), yi.get_top() + UP * 0.4, color=YELL, buff=0.1, stroke_width=4)
        out_lab = t("输出第 i 行", 22, YELL).next_to(out_ar, UP, buff=0.12)
        self.play(Create(out_ar), FadeIn(out_lab, shift=DOWN * 0.05), run_time=0.6)
        self.at(6.8)
        same = t("每一行，都走同一个 f", 24, MUTED).next_to(in_lab, DOWN, buff=1.3)
        self.play(FadeIn(same, shift=DOWN * 0.05), run_time=0.5)

        # 页2：同一函数 f 复用给每行；不读 xⱼ
        self.at(7.6)
        self.play(FadeOut(VGroup(lab, formula, in_ar, in_lab, out_ar, out_lab, same), shift=UP * 0.05), run_time=0.4)
        lab2 = t("同一个 f，复用给每个 token", 30, WHITE).next_to(head, DOWN, buff=1.4)
        self.play(FadeIn(lab2, shift=DOWN * 0.05))
        self.at(9.0)
        rows = VGroup()
        for j, (s, col) in enumerate((("token 1", CYAN), ("token 2", YELL), ("token 3", GREEN), ("token 4", WHITE))):
            tok = boxed(s, 2.4, 0.85, col, 24)
            fmini = t("f", 26, GREEN, "BOLD").next_to(tok, RIGHT, buff=0.5)
            rows.add(VGroup(tok, fmini))
        rows.arrange_in_grid(2, 2, buff=0.5).next_to(lab2, DOWN, buff=1.1)
        self.play(FadeIn(rows, shift=DOWN * 0.05), run_time=0.9)
        self.at(11.0)
        no_talk = t("算 token 1 时，绝不去读 token 2", 29, RED, "BOLD")
        fit(no_talk, 0.95)
        no_talk.next_to(rows, DOWN, buff=1.2)
        self.play(FadeIn(no_talk, shift=DOWN * 0.05), run_time=0.7)
        self.at(13.6)
        cross = self.play_red_cross(rows[1])
        self.at(15.6)

        # 页3：共享参数 ≠ 互相影响 + 悬念
        self.play(FadeOut(VGroup(lab2, rows, no_talk, cross), shift=UP * 0.05), run_time=0.4)
        share = t("共享参数", 34, WHITE, "BOLD").next_to(head, DOWN, buff=1.7)
        neq = t("≠", 44, YELL, "BOLD").next_to(share, DOWN, buff=0.7)
        infl = t("互相影响", 34, WHITE, "BOLD").next_to(neq, DOWN, buff=0.7)
        stack = VGroup(share, neq, infl)
        self.play(FadeIn(stack, shift=DOWN * 0.05), run_time=0.7)
        self.at(17.8)
        q = t("它真的完全不知道上下文吗？", 31, CYAN, "BOLD")
        fit(q, 0.95)
        q.next_to(stack, DOWN, buff=1.9)
        self.play(FadeIn(q, shift=DOWN * 0.05), run_time=0.6)
        self.pad_to_voice()


# ---------------- S4 SwiGLU 四步：扩张 ----------------
class S4(_Base):
    def construct(self):
        self.footer()
        head = t("SwiGLU 版 FFN：四步", 40, YELL, "BOLD").to_edge(UP, buff=1.2)
        self.play(FadeIn(head, shift=DOWN * 0.05))

        # 页1：四步总览
        self.at(1.2)
        steps = VGroup(boxed("① 扩张", 1.5, 1.0, CYAN, 25),
                       boxed("② 门控", 1.5, 1.0, GREEN, 25),
                       boxed("③ 相乘", 1.5, 1.0, YELL, 25),
                       boxed("④ 投影", 1.5, 1.0, WHITE, 25))
        steps.arrange(RIGHT, buff=0.35).next_to(head, DOWN, buff=1.6)
        self.play(FadeIn(steps, shift=DOWN * 0.05), run_time=0.8)
        self.at(3.2)
        s1lab = mt("第一步：x 分乘 W<sub><small>gate</small></sub> 与 "
                    "W<sub><small>up</small></sub>", 28, CYAN, "BOLD")
        s1lab.next_to(steps, DOWN, buff=1.2)
        fit(s1lab, 0.95)
        self.play(FadeIn(s1lab, shift=DOWN * 0.05), run_time=0.6)

        # 页2：扩张动画 d_model → d_ff
        self.at(5.0)
        self.play(FadeOut(VGroup(steps, s1lab), shift=UP * 0.05), run_time=0.4)
        xbar = Rectangle(width=1.3, height=1.6, color=CYAN, fill_color=CYAN, fill_opacity=0.7)
        xlab = t("x·7168 维", 19, CYAN).next_to(xbar, DOWN, buff=0.3)
        xg = VGroup(xbar, xlab)
        wg = boxed_sub("W", "gate", 1.8, 0.9, GREEN, 23)
        wu = boxed_sub("W", "up", 1.8, 0.9, YELL, 23)
        wcol = VGroup(wg, wu).arrange(DOWN, buff=0.6)
        dff = Rectangle(width=2.6, height=2.0, color=MUTED, fill_color=MUTED, fill_opacity=0.15)
        dff_lab = t("d_ff 维空间", 22, MUTED).next_to(dff, DOWN, buff=0.3)
        dffg = VGroup(dff, dff_lab)
        chain = VGroup(xg, wcol, dffg).arrange(RIGHT, buff=0.7).next_to(head, DOWN, buff=2.4)
        self.play(FadeIn(xg, shift=DOWN * 0.05), run_time=0.5)
        self.at(6.2)
        self.play(FadeIn(wcol, shift=DOWN * 0.05), run_time=0.6)
        self.at(7.4)
        # Use one centered junction and two straight branches.  The old
        # horizontal-plus-vertical elbow made the yellow branch look broken
        # and left it glued to the lower box's left edge.
        split = Dot(point=(xg.get_right() + wcol.get_left()) / 2,
                    radius=0.06, color=YELL)
        split_link = Line(xg.get_right(), split.get_center(),
                          color=MUTED, stroke_width=4)
        ar_gate = Arrow(split.get_center(), wg.get_left(),
                        color=GREEN, buff=0.08, stroke_width=5)
        ar_up = Arrow(split.get_center(), wu.get_left(),
                      color=YELL, buff=0.08, stroke_width=5)
        self.play(Create(split_link), FadeIn(split), Create(ar_gate), Create(ar_up),
                  run_time=0.7)
        self.at(8.7)
        self.play(FadeIn(dffg, shift=DOWN * 0.05), run_time=0.6)
        self.at(10.0)
        x4 = t("×4：通常是 d_model 的四倍", 30, YELL, "BOLD")
        fit(x4, 0.95)
        x4.next_to(chain, DOWN, buff=1.2)
        self.play(FadeIn(x4, scale=1.05), run_time=0.6)

        # 页3：DeepSeek 数字对比
        self.at(13.5)
        self.play(FadeOut(VGroup(xg, wcol, dffg, split, split_link, ar_gate, ar_up, x4),
                          shift=UP * 0.05), run_time=0.4)
        lab3 = t("比如 DeepSeek V4 Pro", 30, WHITE).next_to(head, DOWN, buff=1.5)
        self.play(FadeIn(lab3, shift=DOWN * 0.05))
        self.at(15.0)
        n1 = boxed("输入 7168 维", 3.6, 1.1, CYAN, 28)
        n2 = boxed("中间 28672 维", 3.6, 1.1, YELL, 28)
        nums = VGroup(n1, n2).arrange(DOWN, buff=0.9).next_to(lab3, DOWN, buff=1.2)
        ar = Arrow(n1.get_bottom(), n2.get_top(), color=YELL, buff=0.12, stroke_width=5)
        self.play(FadeIn(n1, shift=DOWN * 0.05), run_time=0.6)
        self.at(16.6)
        self.play(FadeIn(n2, shift=DOWN * 0.05), Create(ar), run_time=0.7)
        self.at(18.5)
        dirs = t("先铺开足够多的方向，才有得选", 30, GREEN, "BOLD")
        fit(dirs, 0.95)
        dirs.next_to(nums, DOWN, buff=1.3)
        self.play(FadeIn(dirs, scale=1.05), run_time=0.7)
        self.pad_to_voice()


# ---------------- S5 门控 + 投影 ----------------
class S5(_Base):
    def construct(self):
        self.footer()
        head = t("第二步：门控", 40, YELL, "BOLD").to_edge(UP, buff=1.2)
        self.play(FadeIn(head, shift=DOWN * 0.05))

        # 页1：SiLU 连续曲线
        self.at(1.2)
        lab = t("SiLU 生成一排阀门", 30, WHITE).next_to(head, DOWN, buff=1.4)
        self.play(FadeIn(lab, shift=DOWN * 0.05))
        self.at(2.4)
        axes = Axes(x_range=[-3, 3], y_range=[-0.2, 1.2], x_length=6.0, y_length=3.0,
                    axis_config={"color": MUTED, "stroke_width": 3,
                                 "include_ticks": False, "include_tip": True})
        axes.next_to(lab, DOWN, buff=0.9)
        curve = axes.plot(lambda x: x / (1 + np.exp(-x)), x_range=[-2.8, 2.8],
                          color=GREEN, stroke_width=5)
        self.play(Create(axes), run_time=0.5)
        self.play(Create(curve), run_time=0.9)
        self.at(4.6)
        cont = t("连续调节，不是简单的开或关", 28, GREEN, "BOLD")
        fit(cont, 0.95)
        cont.next_to(curve, DOWN, buff=1.2)
        cont.set_x(0)
        self.play(FadeIn(cont, shift=DOWN * 0.05), run_time=0.6)
        self.at(6.4)
        gates = VGroup()
        for i in range(5):
            hgt = 0.25 + 0.15 * i
            g = Rectangle(width=0.5, height=hgt, color=YELL, fill_color=YELL, fill_opacity=0.7)
            gates.add(g)
        gates.arrange(RIGHT, buff=0.35, aligned_edge=DOWN).next_to(cont, DOWN, buff=1.0)
        gl = t("一排随输入而变的阀门", 25, MUTED).next_to(gates, DOWN, buff=0.4)
        self.play(FadeIn(gates, shift=DOWN * 0.05), FadeIn(gl, shift=DOWN * 0.05), run_time=0.7)

        # 页2：gate ⊙ up = hidden 逐元素相乘（竖式三行 + 行间符号）
        self.at(8.4)
        self.play(FadeOut(VGroup(lab, axes, curve, cont, gates, gl), shift=UP * 0.05), run_time=0.4)
        lab2 = t("第三步：gate 与 up 逐元素相乘", 28, WHITE).next_to(head, DOWN, buff=1.4)
        self.play(FadeIn(lab2, shift=DOWN * 0.05))
        self.at(9.8)
        gv = VGroup(*[boxed(str(v), 0.72, 0.85, GREEN, 22) for v in ("0.9", "0.5", "0.1", "1.0", "0.3")])
        gv.arrange(RIGHT, buff=0.18)
        uv = VGroup(*[boxed(str(v), 0.72, 0.85, YELL, 22) for v in ("0.8", "0.4", "1.2", "0.6", "0.9")])
        uv.arrange(RIGHT, buff=0.18)
        hv = VGroup(*[boxed(str(v), 0.72, 0.85, MUTED, 22) for v in ("0.72", "0.20", "0.12", "0.60", "0.27")])
        hv.arrange(RIGHT, buff=0.18)
        rows = VGroup(gv, uv, hv).arrange(DOWN, buff=1.35, aligned_edge=LEFT)
        rows.next_to(lab2, DOWN, buff=1.8)
        dot_y = (gv.get_bottom()[1] + uv.get_top()[1]) / 2
        eq_y = (uv.get_bottom()[1] + hv.get_top()[1]) / 2
        dot = t("⊙", 40, WHITE, "BOLD").move_to([gv.get_center()[0], dot_y, 0])
        eqm = t("=", 40, WHITE, "BOLD").move_to([uv.get_center()[0], eq_y, 0])
        gl2 = t("gate", 22, GREEN, "BOLD").next_to(gv, UP, buff=0.15)
        ul2 = t("up", 22, YELL, "BOLD").next_to(uv, UP, buff=0.15)
        hl2 = t("hidden", 22, MUTED, "BOLD").next_to(hv, UP, buff=0.15)
        self.play(FadeIn(gv, shift=DOWN * 0.05), FadeIn(gl2, shift=DOWN * 0.05), run_time=0.6)
        self.at(11.0)
        self.play(FadeIn(dot, scale=0.9), FadeIn(uv, shift=DOWN * 0.05), FadeIn(ul2, shift=DOWN * 0.05), run_time=0.7)
        self.at(12.6)
        self.play(FadeIn(eqm, scale=0.9), FadeIn(hv, shift=DOWN * 0.05), FadeIn(hl2, shift=DOWN * 0.05), run_time=0.7)
        self.at(14.2)
        each = t("每个维度独立控制", 28, GREEN, "BOLD").next_to(rows, DOWN, buff=0.6)
        self.play(FadeIn(each, shift=DOWN * 0.05), run_time=0.6)

        # 页3：独立控制：放行 / 截断
        self.at(15.5)
        self.play(FadeOut(VGroup(lab2, gv, gl2, dot, uv, ul2, eqm, hv, hl2, each), shift=UP * 0.05), run_time=0.4)
        lab3 = t("每个维度独立控制", 30, WHITE).next_to(head, DOWN, buff=1.5)
        self.play(FadeIn(lab3, shift=DOWN * 0.05))
        self.at(16.8)
        open_g = boxed("开到最大 → 放行", 3.8, 1.1, GREEN, 28)
        close_g = boxed("关到接近零 → 截断", 3.8, 1.1, RED, 28)
        gates2 = VGroup(open_g, close_g).arrange(DOWN, buff=0.6).next_to(lab3, DOWN, buff=1.9)
        self.play(FadeIn(open_g, shift=DOWN * 0.05), run_time=0.6)
        self.at(18.3)
        self.play(FadeIn(close_g, shift=DOWN * 0.05), run_time=0.6)

        # 页4：第四步 W_down 投影
        self.at(21.6)
        self.play(FadeOut(VGroup(lab3, open_g, close_g), shift=UP * 0.05), run_time=0.4)
        lab4 = mt("第四步：W<sub><small>down</small></sub> 投影回原维度", 28, WHITE)
        lab4.next_to(head, DOWN, buff=1.4)
        fit(lab4, 0.95)
        self.play(FadeIn(lab4, shift=DOWN * 0.05))
        self.at(22.8)
        wide = Rectangle(width=3.4, height=1.6, color=MUTED, fill_color=MUTED, fill_opacity=0.15)
        wl = t("hidden（宽）", 22, MUTED).next_to(wide, DOWN, buff=0.25)
        narrow = Rectangle(width=1.6, height=1.6, color=YELL, fill_color=YELL, fill_opacity=0.7)
        nl = t("y（原维度）", 22, YELL).next_to(narrow, DOWN, buff=0.25)
        proj = VGroup(VGroup(wide, wl), VGroup(narrow, nl)).arrange(RIGHT, buff=1.6).next_to(lab4, DOWN, buff=1.4)
        ar = Arrow(wide.get_right(), narrow.get_left(), color=YELL, buff=0.15, stroke_width=5)
        arl = sub_t("W", "down", 24, YELL, "BOLD").next_to(ar, UP, buff=0.15)
        self.play(FadeIn(VGroup(wide, wl), shift=DOWN * 0.05), run_time=0.5)
        self.play(Create(ar), FadeIn(arl, shift=DOWN * 0.05), run_time=0.6)
        self.play(FadeIn(VGroup(narrow, nl), shift=DOWN * 0.05), run_time=0.6)
        self.at(24.3)
        recap = VGroup(t("扩张", 30, CYAN, "BOLD"), t("筛选", 30, GREEN, "BOLD"), t("归位", 30, YELL, "BOLD"))
        recap.arrange(RIGHT, buff=0.8).next_to(proj, DOWN, buff=1.1)
        self.play(FadeIn(recap, shift=DOWN * 0.05), run_time=0.7)
        self.pad_to_voice()


# ---------------- S6 实验：扰动不跨行 ----------------
class S6(_Base):
    def construct(self):
        self.footer()
        head = t("两行真的互不干扰吗？", 40, YELL, "BOLD").to_edge(UP, buff=1.2)
        self.play(FadeIn(head, shift=DOWN * 0.05))

        # 页1：实验台（x 矩阵 → SwiGLU，固定权重）
        self.at(1.2)
        lab = t("一个 2 维 SwiGLU，两个 token", 28, WHITE).next_to(head, DOWN, buff=1.3)
        self.play(FadeIn(lab, shift=DOWN * 0.05))
        self.at(2.6)
        xrow1 = VGroup(boxed("1.0", 0.78, 0.6, CYAN, 22), boxed("-0.5", 0.78, 0.6, CYAN, 22)).arrange(RIGHT, buff=0.2)
        xrow2 = VGroup(boxed("0.2", 0.78, 0.6, CYAN, 22), boxed("1.0", 0.78, 0.6, CYAN, 22)).arrange(RIGHT, buff=0.2)
        xl1 = t("token 1", 20, CYAN).next_to(xrow1, LEFT, buff=0.5)
        xl2 = t("token 2", 20, CYAN).next_to(xrow2, LEFT, buff=0.5)
        xmat = VGroup(VGroup(xl1, xrow1), VGroup(xl2, xrow2)).arrange(DOWN, buff=0.3, aligned_edge=LEFT)
        xg = VGroup(xmat, t("输入 x", 20, CYAN, "BOLD").next_to(xmat, DOWN, buff=0.3))
        ffn = boxed("SwiGLU", 2.2, 1.0, GREEN, 30, fill=0.2)
        chain = VGroup(xg, ffn).arrange(DOWN, buff=0.6).next_to(lab, DOWN, buff=0.8)
        self.play(FadeIn(xg, shift=DOWN * 0.05), run_time=0.8)
        self.play(FadeIn(ffn, shift=DOWN * 0.05), run_time=0.5)
        self.at(4.6)
        ax1 = Arrow(xg.get_bottom(), ffn.get_top(), color=MUTED, buff=0.12, stroke_width=4)
        self.play(Create(ax1), run_time=0.5)
        self.at(5.8)
        ws = VGroup(boxed_sub("W", "gate", 1.7, 0.7, GREEN, 22),
                    boxed_sub("W", "up", 1.7, 0.7, YELL, 22),
                    boxed_sub("W", "down", 1.7, 0.7, MUTED, 22)).arrange(RIGHT, buff=0.5)
        ws.next_to(chain, DOWN, buff=0.6)
        wl = t("权重固定，不许改", 25, MUTED).next_to(ws, DOWN, buff=0.35)
        self.play(FadeIn(ws, shift=DOWN * 0.05), FadeIn(wl, shift=DOWN * 0.05), run_time=0.7)

        # 页2：扰动 token1 → y2 不变
        self.at(8.5)
        self.play(FadeOut(VGroup(lab, xg, ffn, ax1, ws, wl), shift=UP * 0.05), run_time=0.4)
        lab2 = t("改动第 1 个 token", 30, RED, "BOLD").next_to(head, DOWN, buff=1.4)
        self.play(FadeIn(lab2, shift=DOWN * 0.05))
        self.at(9.6)
        xrow1p = VGroup(boxed("1.0", 0.78, 0.6, CYAN, 22), boxed("-0.5", 0.78, 0.6, CYAN, 22)).arrange(RIGHT, buff=0.2)
        p1 = t("+0.3", 22, RED, "BOLD").next_to(xrow1p[0], UP, buff=0.1)
        p2 = t("−0.4", 22, RED, "BOLD").next_to(xrow1p[1], UP, buff=0.1)
        xrow2p = VGroup(boxed("0.2", 0.78, 0.6, CYAN, 22), boxed("1.0", 0.78, 0.6, CYAN, 22)).arrange(RIGHT, buff=0.2)
        xlab1 = t("token 1", 20, CYAN).next_to(xrow1p, LEFT, buff=0.5)
        xlab2 = t("token 2", 20, CYAN).next_to(xrow2p, LEFT, buff=0.5)
        xmat2 = VGroup(VGroup(xlab1, xrow1p), VGroup(xlab2, xrow2p)).arrange(DOWN, buff=0.3, aligned_edge=LEFT)
        xg2 = VGroup(xmat2, t("输入 x", 20, CYAN, "BOLD").next_to(xmat2, DOWN, buff=0.3))
        ffn2 = boxed("SwiGLU", 2.2, 1.0, GREEN, 30, fill=0.2)
        chain2 = VGroup(xg2, ffn2).arrange(DOWN, buff=0.6).next_to(lab2, DOWN, buff=0.8)
        self.play(FadeIn(xrow1p, shift=DOWN * 0.05), FadeIn(p1, shift=DOWN * 0.05), FadeIn(p2, shift=DOWN * 0.05), run_time=0.7)
        self.play(FadeIn(xrow2p, shift=DOWN * 0.05), FadeIn(xlab1, shift=DOWN * 0.05), FadeIn(xlab2, shift=DOWN * 0.05), run_time=0.5)
        self.play(FadeIn(ffn2, shift=DOWN * 0.05), run_time=0.4)
        self.at(11.0)
        y2row = VGroup(boxed("-0.042", 0.78, 0.6, YELL, 21), boxed("0.357", 0.78, 0.6, YELL, 21)).arrange(RIGHT, buff=0.2)
        y2g = VGroup(t("y₂", 20, YELL, "BOLD").next_to(y2row, LEFT, buff=0.5), y2row,
                     t("输出", 20, YELL, "BOLD").next_to(y2row, DOWN, buff=0.3))
        y2g.next_to(ffn2, DOWN, buff=0.4)
        ay = Arrow(ffn2.get_bottom(), y2row.get_top(), color=MUTED, buff=0.12, stroke_width=4)
        self.play(Create(ay), FadeIn(y2g, shift=DOWN * 0.05), run_time=0.6)
        self.at(12.0)
        guess = t("token 2 的输出，变不变？", 32, CYAN, "BOLD")
        fit(guess, 0.95)
        guess.next_to(y2g, DOWN, buff=0.35)
        self.play(FadeIn(guess, shift=DOWN * 0.05), run_time=0.6)
        self.at(13.2)
        same = boxed("逐元素，纹丝不动", 4.0, 0.9, GREEN, 32, fill=0.2, weight="BOLD")
        same.next_to(guess, DOWN, buff=0.4)
        self.play(FadeIn(same, scale=1.06), run_time=0.7)

        # 页3：反过来 + 批量 = 单独 + 结论
        self.at(15.0)
        self.play(FadeOut(VGroup(lab2, chain2, ay, y2g, guess, same), shift=UP * 0.05), run_time=0.4)
        lab3 = t("反过来：改动第 2 个 token", 30, RED, "BOLD").next_to(head, DOWN, buff=2.5)
        self.play(FadeIn(lab3, shift=DOWN * 0.05))
        self.at(15.9)
        xrow2r = VGroup(boxed("0.2", 0.78, 0.6, CYAN, 22), boxed("1.0", 0.78, 0.6, CYAN, 22)).arrange(RIGHT, buff=0.2)
        rp1 = t("−0.4", 22, RED, "BOLD").next_to(xrow2r[0], UP, buff=0.1)
        rp2 = t("+0.3", 22, RED, "BOLD").next_to(xrow2r[1], UP, buff=0.1)
        token2_label = t("token 2", 20, CYAN).next_to(xrow2r, LEFT, buff=0.5)
        rev_vis = VGroup(token2_label, xrow2r, rp1, rp2)
        rev1 = t("y₁ 也逐元素不变", 30, GREEN, "BOLD")
        fit(rev1, 0.95)
        rev_vis2 = VGroup(rev_vis, rev1).arrange(DOWN, buff=0.9).next_to(lab3, DOWN, buff=0.7)
        self.play(FadeIn(xrow2r, shift=DOWN * 0.05), FadeIn(rp1, shift=DOWN * 0.05), FadeIn(rp2, shift=DOWN * 0.05), run_time=0.7)
        self.play(FadeIn(rev1, shift=DOWN * 0.05), run_time=0.5)
        self.at(16.8)
        batch = VGroup(boxed("批量算", 2.2, 0.8, YELL, 27),
                       t("=", 34, WHITE, "BOLD"),
                       boxed("单独算", 2.2, 0.8, YELL, 27)).arrange(RIGHT, buff=0.5)
        batch.next_to(rev_vis2, DOWN, buff=0.7)
        self.play(FadeIn(batch, shift=DOWN * 0.05), run_time=0.6)
        self.at(19.2)
        concl = t("独立性不是定义，是算出来的", 30, GREEN, "BOLD")
        fit(concl, 0.95)
        concl.next_to(batch, DOWN, buff=0.7)
        self.play(FadeIn(concl, shift=DOWN * 0.05), run_time=0.7)
        self.pad_to_voice()


# ---------------- S7 真实模型 + MoE ----------------
class S7(_Base):
    def construct(self):
        self.footer()
        head = t("真实模型也这么搭？", 40, YELL, "BOLD").to_edge(UP, buff=1.2)
        self.play(FadeIn(head, shift=DOWN * 0.05))

        # 页1：DeepSeek V4 Pro 配置核对
        self.at(1.2)
        lab = t("DeepSeek V4 Pro 的 config.json", 28, WHITE).next_to(head, DOWN, buff=1.3)
        self.play(FadeIn(lab, shift=DOWN * 0.05))
        self.at(2.4)
        cfg1 = boxed('hidden_size: 7168', 3.2, 1.1, CYAN, 27)
        cfg2 = boxed('hidden_act: "silu"', 3.2, 1.1, GREEN, 27)
        cfgs = VGroup(cfg1, cfg2).arrange(DOWN, buff=0.6).next_to(lab, DOWN, buff=1.2)
        self.play(FadeIn(cfg1, shift=DOWN * 0.05), run_time=0.6)
        self.at(4.0)
        self.play(FadeIn(cfg2, shift=DOWN * 0.05), run_time=0.6)
        self.at(5.6)
        chk1 = t("✓ 7168", 20, GREEN, "BOLD").next_to(cfg1, RIGHT, buff=0.4)
        chk2 = t("✓ silu", 20, GREEN, "BOLD").next_to(cfg2, RIGHT, buff=0.4)
        self.play(FadeIn(chk1, scale=1.1), FadeIn(chk2, scale=1.1), run_time=0.6)
        self.at(7.4)
        match = t("和上面讲的，完全对得上", 30, YELL, "BOLD")
        fit(match, 0.95)
        match.next_to(cfgs, DOWN, buff=0.8)
        self.play(FadeIn(match, scale=1.05), run_time=0.6)
        self.at(9.4)
        four = VGroup(boxed("扩张", 1.3, 0.9, CYAN, 24),
                      boxed("门控", 1.3, 0.9, GREEN, 24),
                      boxed("相乘", 1.3, 0.9, YELL, 24),
                      boxed("投影", 1.3, 0.9, WHITE, 24))
        four.arrange(RIGHT, buff=0.35).next_to(match, DOWN, buff=0.7)
        self.play(FadeIn(four, shift=DOWN * 0.05), run_time=0.7)

        # 页2：Dense vs MoE
        self.at(13.2)
        self.play(FadeOut(VGroup(lab, cfg1, cfg2, chk1, chk2, match, four), shift=UP * 0.05), run_time=0.4)
        lab2 = t("Dense FFN：同一间思考室", 30, WHITE).next_to(head, DOWN, buff=1.4)
        self.play(FadeIn(lab2, shift=DOWN * 0.05))
        self.at(14.8)
        toks_in = VGroup(*[boxed(s, 0.95, 0.75, c, 24) for s, c in (("A", CYAN), ("B", YELL), ("C", WHITE))])
        toks_in.arrange(RIGHT, buff=0.5).next_to(lab2, DOWN, buff=0.9)
        big_room = room(4.6, 2.4, GREEN, 5)
        big_room.next_to(toks_in, DOWN, buff=1.0)
        big_lab = t("FFN（全体 token 共用）", 24, GREEN).next_to(big_room, DOWN, buff=0.35)
        tars = [Arrow(tok.get_bottom(), big_room.get_top() + LEFT * (0.9 - i * 0.9), color=MUTED, buff=0.12, stroke_width=4)
                for i, tok in enumerate(toks_in)]
        self.play(FadeIn(toks_in, shift=DOWN * 0.05), run_time=0.6)
        self.play(Create(big_room), FadeIn(big_lab, shift=DOWN * 0.05), run_time=0.6)
        self.play(*[Create(a) for a in tars], run_time=0.7)
        self.at(17.6)
        self.play(FadeOut(VGroup(lab2, toks_in, big_room, big_lab, *tars), shift=UP * 0.05), run_time=0.4)
        lab3 = t("MoE：路由器分流到专科思考室", 30, WHITE).next_to(head, DOWN, buff=1.4)
        self.play(FadeIn(lab3, shift=DOWN * 0.05))
        self.at(19.0)
        router = Circle(radius=0.7, color=YELL, stroke_width=4)
        rl = t("路由器", 24, YELL, "BOLD").move_to(router.get_center())
        router_g = VGroup(router, rl)
        experts = VGroup()
        for j, col in enumerate((GREEN, CYAN, YELL)):
            e = room(1.6, 1.2, col, 4)
            el = t(f"专家 {j + 1}", 20, col).next_to(e, DOWN, buff=0.2)
            experts.add(VGroup(e, el))
        experts.arrange(RIGHT, buff=0.7)
        moe = VGroup(router_g, experts).arrange(DOWN, buff=1.4).next_to(lab3, DOWN, buff=1.2)
        self.play(FadeIn(moe, shift=DOWN * 0.05), run_time=0.8)
        self.at(21.0)
        links = VGroup()
        for e in experts:
            target = e.get_top()
            direction = target - router.get_center()
            start = router.get_center() + direction / np.linalg.norm(direction) * router.radius
            a = Arrow(start, target, color=YELL, buff=0, stroke_width=4)
            links.add(a)
        self.play(*[Create(a) for a in links], run_time=0.7)
        self.at(22.6)
        inside = t("专家内部，还是 FFN", 30, GREEN, "BOLD")
        fit(inside, 0.95)
        inside.next_to(moe, DOWN, buff=1.2)
        self.play(FadeIn(inside, scale=1.05), run_time=0.7)
        self.pad_to_voice()


# ---------------- S8 残差 + 总结 + 品牌尾卡 ----------------
class S8(_Base):
    def construct(self):
        self.footer()
        head = t("思考室不是终点", 40, YELL, "BOLD").to_edge(UP, buff=1.2)
        self.play(FadeIn(head, shift=DOWN * 0.05))

        # 页1：残差回路
        self.at(2.0)
        lab = t("输出 = 输入 + FFN(输入)", 34, WHITE, "BOLD").next_to(head, DOWN, buff=2.2)
        self.play(FadeIn(lab, shift=DOWN * 0.05))
        self.at(3.6)
        xbox = boxed("输入 x", 1.6, 1.0, CYAN, 25)
        fbox = boxed("FFN", 1.5, 1.0, GREEN, 25)
        plus = t("+", 40, WHITE, "BOLD")
        ybox = boxed("输出 y", 1.6, 1.0, YELL, 25)
        chain = VGroup(xbox, fbox, plus, ybox).arrange(RIGHT, buff=0.45).next_to(lab, DOWN, buff=0.8)
        self.play(FadeIn(xbox, shift=DOWN * 0.05), run_time=0.5)
        self.play(FadeIn(fbox, shift=DOWN * 0.05), run_time=0.5)
        self.play(FadeIn(plus, scale=0.9), FadeIn(ybox, shift=DOWN * 0.05), run_time=0.6)
        self.at(6.0)
        ar1 = Arrow(xbox.get_right(), fbox.get_left(), color=GREEN, buff=0.15, stroke_width=5)
        ar2 = Arrow(fbox.get_right(), plus.get_left(), color=GREEN, buff=0.15, stroke_width=5)
        ar3 = Arrow(plus.get_right(), ybox.get_left(), color=WHITE, buff=0.15, stroke_width=5)
        self.play(Create(ar1), Create(ar2), Create(ar3), run_time=0.8)
        self.at(8.0)
        direct = Arrow(xbox.get_bottom() + DOWN * 0.5, ybox.get_bottom() + DOWN * 0.5,
                       color=GREEN, buff=0, stroke_width=6)
        dlab = t("残差直通路", 24, GREEN, "BOLD").next_to(direct, DOWN, buff=0.15)
        self.play(Create(direct), FadeIn(dlab, shift=DOWN * 0.05), run_time=0.7)
        self.at(10.6)
        safe = t("即使 FFN 没学到有用变换，原信息仍有直通路", 27, GREEN, "BOLD")
        fit(safe, 0.9)
        safe.next_to(dlab, DOWN, buff=0.8)
        self.play(FadeIn(safe, shift=DOWN * 0.05), run_time=0.6)

        # 页2：一层节奏
        self.at(13.0)
        self.play(FadeOut(VGroup(lab, xbox, fbox, plus, ybox, ar1, ar2, ar3, direct, dlab, safe), shift=UP * 0.05), run_time=0.4)
        lab2 = t("一层 Transformer 的节奏", 32, WHITE).next_to(head, DOWN, buff=1.5)
        self.play(FadeIn(lab2, shift=DOWN * 0.05))
        self.at(15.9)
        r1 = boxed("注意力：把上下文写进 token", 4.8, 1.1, CYAN, 27)
        r2 = boxed("FFN：各自加工", 4.8, 1.1, GREEN, 27)
        r3 = boxed("残差：把结果接回去", 4.8, 1.1, YELL, 27)
        steps = VGroup(r1, r2, r3).arrange(DOWN, buff=0.8).next_to(lab2, DOWN, buff=1.2)
        self.play(FadeIn(r1, shift=DOWN * 0.05), run_time=0.6)
        self.at(18.0)
        self.play(FadeIn(r2, shift=DOWN * 0.05), run_time=0.6)
        self.at(20.0)
        self.play(FadeIn(r3, shift=DOWN * 0.05), run_time=0.6)

        # 页3：浪费还是不可或缺 + 互动
        self.at(25.5)
        self.play(FadeOut(VGroup(lab2, r1, r2, r3), shift=UP * 0.05), run_time=0.4)
        lab3 = t("FFN：不让交流，却占大部分参数", 30, WHITE).next_to(head, DOWN, buff=1.4)
        self.play(FadeIn(lab3, shift=DOWN * 0.05))
        self.at(27.0)
        pbar = Rectangle(width=4.6, height=1.2, color=YELL, fill_color=YELL, fill_opacity=0.75)
        pbar.next_to(lab3, DOWN, buff=1.0)
        pl = t("大部分参数", 26, YELL, "BOLD").next_to(pbar, DOWN, buff=0.3)
        self.play(FadeIn(VGroup(pbar, pl), shift=DOWN * 0.05), run_time=0.6)
        self.at(28.6)
        q = t("这种「各自思考」，是浪费，还是不可或缺？", 30, CYAN, "BOLD")
        fit(q, 0.9)
        q.next_to(pbar, DOWN, buff=1.3)
        self.play(FadeIn(q, shift=DOWN * 0.05), run_time=0.7)
        self.at(30.2)
        ask = t("评论区聊聊你的答案", 28, MUTED).next_to(q, DOWN, buff=0.8)
        self.play(FadeIn(ask, shift=DOWN * 0.05), run_time=0.6)

        # 页4：品牌尾卡
        self.at(31.6)
        self.play(FadeOut(VGroup(lab3, pbar, pl, q, ask), shift=UP * 0.05), run_time=0.4)
        logo = ImageMobject("avatar-sjai-round.png")
        logo.scale_to_fit_width(3.0)
        logo.next_to(head, DOWN, buff=1.0)
        self.play(FadeIn(logo, shift=DOWN * 0.05), run_time=0.7)
        self.at(33.0)
        follow = t("关注「数解AI」", 40, YELL, "BOLD").next_to(logo, DOWN, buff=0.6)
        self.play(FadeIn(follow, scale=1.08), run_time=0.6)
        self.at(34.2)
        title = t("《Attention都够了，为什么还要前馈网络？》", 25, WHITE, "BOLD")
        fit(title, 0.95)
        title.next_to(follow, DOWN, buff=0.7)
        self.play(FadeIn(title, shift=DOWN * 0.05), run_time=0.6)
        self.at(35.6)
        link = t("查看公众号文章", 30, GREEN, "BOLD").next_to(title, DOWN, buff=0.55)
        self.play(FadeIn(link, scale=0.95), run_time=0.6)
        self.at(37.0)
        nxt = t("下一篇：归一化怎么稳住 61 层不崩", 27, CYAN, "BOLD")
        fit(nxt, 0.95)
        nxt.next_to(link, DOWN, buff=0.7)
        self.play(FadeIn(nxt, shift=DOWN * 0.05), run_time=0.6)
        self.at(39.8)
        bye = t("不迷路", 26, MUTED).next_to(nxt, DOWN, buff=0.6)
        self.play(FadeIn(bye, shift=DOWN * 0.05), run_time=0.5)
        self.pad_to_voice()


# ---------------- 封面帧 ----------------
class Cover(Scene):
    """封面帧：系列标签 + 主/副标题 + 思考室/SwiGLU 视觉 + 底部公众号 logo。
    渲染：python3 -m manim render -qm -s --disable_caching scenes.py Cover
    关键内容须落在 3:4 安全区（frame y ∈ [-5.33, +5.33]）。
    """
    def construct(self):
        logo = ImageMobject("avatar-sjai-round.png")
        logo.scale_to_fit_width(2.2)
        logo.to_edge(DOWN, buff=1.9)

        series = t("大模型原理 · 第 5 篇", 26, CYAN).to_edge(UP, buff=2.5)
        title = t("Attention都够了，为什么还要前馈网络？", 42, YELL, "BOLD")
        title.set_width(config.frame_width * 0.8)
        title.next_to(series, DOWN, buff=0.5)
        subtitle = t("注意力互相看，FFN 各自想", 32, WHITE).next_to(title, DOWN, buff=0.4)

        # 关键视觉：圆桌 token + 思考室 + 公式 y=f(x)
        toks = VGroup(*[t(s, 28, c) for s, c in (("猫", CYAN), ("追", YELL),
                                                  ("老", GREEN), ("鼠", WHITE))])
        toks.arrange(RIGHT, buff=0.9).next_to(subtitle, DOWN, buff=1.3)
        table = Circle(radius=0.75, color=YELL, stroke_width=4).move_to(toks.get_center())
        ar = Arrow(toks.get_right() + RIGHT * 0.3, table.get_center(),
                   color=YELL, buff=0.1, stroke_width=5)
        r = room(2.6, 1.5, GREEN, 5)
        r.next_to(table, DOWN, buff=1.2)
        rl = t("FFN 思考室", 26, GREEN, "BOLD").next_to(r, DOWN, buff=0.4)

        self.add(logo, series, title, subtitle, toks, table, ar, r, rl)


if __name__ == "__main__":
    pass
