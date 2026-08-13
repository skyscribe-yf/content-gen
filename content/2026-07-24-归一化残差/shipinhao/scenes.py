#!/usr/bin/env python3
"""《归一化为什么总在前面？61层模型靠它不崩》视频号 Manim 动画（竖屏 1080×1920）

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

# 配音时长（tts_split.py 实测 2026-08-13），渲染时长 = 配音 + 缓冲
VOICE_DUR = {"S1": 20.41, "S2": 22.34, "S3": 29.97, "S4": 26.47,
             "S5": 38.74, "S6": 30.6, "S7": 38.55, "S8": 25.99}
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


def norm_block(w: float = 3.4, h: float = 1.1, fs: float = 26) -> VGroup:
    """一个 Pre-Norm 层：黄色 Norm 小块 + 子层大块。"""
    nb = boxed("Norm", 1.5, 0.72, YELL, 22, fill=0.35, weight="BOLD")
    body = boxed("Attention / FFN", w, h, CYAN, fs)
    return VGroup(nb, body).arrange(RIGHT, buff=0.35)


# ---------------- S1 开场钩子：61 层为什么不崩 ----------------
class S1(_Base):
    def construct(self):
        self.footer()
        head = t("61 层的模型，为什么不崩？", 42, YELL, "BOLD").to_edge(UP, buff=1.2)
        self.play(FadeIn(head, shift=DOWN * 0.05))
        # 开场闪耀小字：模型架构说明（快速出现即消失，不碰字幕）
        self.at(0.5)
        dsv_note = t("本视频模型架构以 DeepSeek-V4 为例", 22, MUTED)
        dsv_note.next_to(head, DOWN, buff=0.6)
        self.play(FadeIn(dsv_note, scale=1.12), run_time=0.3)
        self.at(1.7)
        self.play(FadeOut(dsv_note, run_time=0.35))

        # 页1：3 层塔 + ×61 + Norm 高亮 + 残差直达箭头
        self.at(1.5)
        blocks = VGroup(*[norm_block() for _ in range(3)])
        blocks.arrange(DOWN, buff=0.5).next_to(head, DOWN, buff=1.1)
        self.play(FadeIn(blocks, shift=DOWN * 0.05), run_time=0.8)
        self.at(3.33)
        x61 = t("× 61", 42, YELL, "BOLD").next_to(blocks, DOWN, buff=0.8)
        self.play(FadeIn(x61, scale=1.1), run_time=0.6)
        self.at(5.0)
        # 每层开头 Norm 亮起（"答案藏在每一层开头的那一步"）
        self.play(*[b[0][0].animate.set_fill(YELL, opacity=0.55) for b in blocks],
                  run_time=1.2)
        self.at(7.4)
        # 残差直通车：左侧竖箭头绕过塔（离塔身留缝；标签竖排防左出界）
        arrow_start = blocks.get_top() + LEFT * 2.8 + UP * 0.4
        arrow_end = blocks.get_bottom() + LEFT * 2.8 + DOWN * 0.4
        bypass = Arrow(arrow_start, arrow_end, color=GREEN, stroke_width=8, buff=0.1)
        bl = t("直通车", 28, GREEN, "BOLD").rotate(PI / 2).next_to(bypass, LEFT, buff=0.3)
        self.play(Create(bypass), FadeIn(bl, shift=UP * 0.05), run_time=1.0)
        self.at(11.9)
        stab = t("还缺一个稳压器", 32, WHITE).next_to(x61, DOWN, buff=1.0)
        self.play(FadeIn(stab, shift=DOWN * 0.05), run_time=0.6)
        self.at(15.4)
        self.play(FadeOut(VGroup(blocks, x61, bypass, bl, stab), shift=UP * 0.05),
                  run_time=0.4)
        # 页2：核心问题大字 + 装饰块
        q = t("归一化，为什么总放在前面？", 44, YELL, "BOLD")
        fit(q, 0.95)
        q.next_to(head, DOWN, buff=3.4)
        self.play(FadeIn(q, scale=1.08), run_time=0.8)
        self.at(17.6)
        icon = norm_block(3.6, 1.0)
        icon.next_to(q, DOWN, buff=1.9)
        self.play(FadeIn(icon, shift=DOWN * 0.05), run_time=0.6)
        self.at(18.6)
        self.play(q.animate.set_color(YELL).scale(1.04), run_time=0.5)
        self.pad_to_voice()


# ---------------- S2 捷径保真 ≠ 相加后尺度不变 ----------------
class S2(_Base):
    def construct(self):
        self.footer()
        head = t("捷径保真，相加之后呢？", 40, YELL, "BOLD").to_edge(UP, buff=1.2)
        self.play(FadeIn(head, shift=DOWN * 0.05))

        # 页1：残差块 x + F(x)（横向链 + 顶部捷径弧）
        self.at(0.8)
        x0 = boxed("x", 1.6, 1.6, CYAN, 46, fill=0.2, weight="BOLD")
        f0 = boxed("F(x)", 2.0, 1.6, MUTED, 34)
        plus = t("+", 52, YELL, "BOLD")
        y0 = boxed("x + F(x)", 2.8, 1.6, GREEN, 30, fill=0.2, weight="BOLD")
        chain = VGroup(x0, f0, plus, y0).arrange(RIGHT, buff=0.35)
        chain.next_to(head, DOWN, buff=2.3)
        fit(chain, 0.98)
        branch = Arrow(x0.get_right(), f0.get_left(), color=MUTED, stroke_width=7, buff=0.06)
        self.play(FadeIn(x0, shift=DOWN * 0.05), run_time=0.6)
        self.at(2.4)
        self.play(FadeIn(VGroup(f0, plus, y0, branch), shift=DOWN * 0.05), run_time=0.8)
        self.at(4.3)
        # 捷径：x 上方折线直通到 y（原样通过，长度不变）
        lift = UP * 1.15
        bypass = VGroup(
            Line(x0.get_top() + UP * 0.1, x0.get_top() + lift),
            Line(y0.get_top() + UP * 0.1, y0.get_top() + lift),
            Arrow(x0.get_top() + lift, y0.get_top() + lift, color=GREEN, stroke_width=9, buff=0.05),
        )
        bl = t("捷径：原样通过，长度不变", 28, GREEN, "BOLD").next_to(bypass, UP, buff=0.25)
        self.play(Create(bypass), FadeIn(bl, shift=UP * 0.05), run_time=1.0)
        # 相加送进下一层：三行承接文案（撑起页1占屏）
        self.at(4.8)
        c1 = t("真正送进下一层的，是 x + F(x)", 34, WHITE, "BOLD").next_to(chain, DOWN, buff=0.8)
        self.play(FadeIn(c1, shift=DOWN * 0.05), run_time=0.5)
        self.at(6.0)
        self.play(FadeOut(VGroup(bypass, bl)), run_time=0.3)
        self.at(6.6)
        c2 = t("同向最长翻倍 · 反向可能抵消", 26, MUTED).next_to(c1, DOWN, buff=0.6)
        c3 = t("长度由 F(x) 的方向决定", 26, MUTED).next_to(c2, DOWN, buff=0.6)
        self.play(FadeIn(VGroup(c2, c3), shift=DOWN * 0.05), run_time=0.6)
        # 同向 / 反向长度对比条（预告文案退场，c1 保留承接）
        self.at(9.1)
        self.play(FadeOut(VGroup(c2, c3), run_time=0.3))
        bars = VGroup()
        for lab, wdt, col in (("同向 → 最长", 5.4, RED), ("反向 → 抵消", 1.5, CYAN)):
            bar = Rectangle(width=wdt, height=0.7, color=col, fill_color=col, fill_opacity=0.75)
            l = t(lab, 28, col, "BOLD").next_to(bar, DOWN, buff=0.3)
            bars.add(VGroup(bar, l))
        bars.arrange(DOWN, buff=1.0, aligned_edge=LEFT)
        bars.next_to(chain, DOWN, buff=1.4).set_x(0)
        self.play(FadeIn(bars, shift=DOWN * 0.05), run_time=0.8)
        self.at(13.7)
        self.play(FadeOut(VGroup(chain, c1, bars), shift=UP * 0.05), run_time=0.4)
        # 页2：文档比喻
        keep = boxed("原件存档", 3.2, 1.2, GREEN, 32, fill=0.2, weight="BOLD")
        keep_l = t("永不丢失", 26, MUTED).next_to(keep, DOWN, buff=0.4)
        edit = boxed("修改意见", 3.2, 1.2, YELL, 32, weight="BOLD")
        edit_l = t("越并越多", 26, MUTED).next_to(edit, DOWN, buff=0.4)
        pair = VGroup(VGroup(keep, keep_l), VGroup(edit, edit_l)).arrange(RIGHT, buff=1.4)
        pair.next_to(head, DOWN, buff=2.2)
        self.play(FadeIn(pair, shift=DOWN * 0.05), run_time=0.8)
        self.at(16.4)
        out = t("几十层后：稿子失控", 40, RED, "BOLD").next_to(pair, DOWN, buff=1.8)
        self.play(FadeIn(out, scale=1.08), run_time=0.6)
        self.at(17.2)
        cap = t("原件不丢 ≠ 尺度不变", 26, MUTED).next_to(out, DOWN, buff=0.7)
        self.play(FadeIn(cap, shift=DOWN * 0.05), run_time=0.5)
        self.at(19.3)
        self.play(FadeOut(VGroup(pair, out, cap), shift=UP * 0.05), run_time=0.4)
        ask = t("整体尺度，谁说了算？", 44, YELL, "BOLD")
        ask.next_to(head, DOWN, buff=2.6)
        self.play(FadeIn(ask, scale=1.08), run_time=0.8)
        self.at(20.3)
        mini = VGroup(boxed("x", 1.2, 0.8, CYAN, 26),
                      t("→", 30, YELL, "BOLD"),
                      boxed("y", 1.2, 0.8, GREEN, 26)).arrange(RIGHT, buff=0.4)
        mini.next_to(ask, DOWN, buff=1.6)
        self.play(FadeIn(mini, shift=DOWN * 0.05), run_time=0.6)
        self.at(21.0)
        stab = boxed("稳压器？", 3.0, 1.2, YELL, 40, fill=0.3, weight="BOLD")
        stab.next_to(mini, DOWN, buff=1.4)
        self.play(FadeIn(stab, scale=1.06), run_time=0.6)
        self.pad_to_voice()


# ---------------- S3 LayerNorm：每个 token 自己算 ----------------
class S3(_Base):
    def construct(self):
        self.footer()
        head = t("归一化：管尺度，不擦信息", 40, YELL, "BOLD").to_edge(UP, buff=1.2)
        self.play(FadeIn(head, shift=DOWN * 0.05))

        # 页1：token 向量条 → 计算链
        self.at(1.0)
        tok = boxed("一个 token 的向量（7168 个数字）", 6.4, 0.95, CYAN, 24)
        tok.next_to(head, DOWN, buff=1.1)
        self.play(FadeIn(tok, shift=DOWN * 0.05), run_time=0.7)
        self.at(3.96)
        steps = VGroup(boxed("算均值 μ", 2.2, 0.9, WHITE, 24),
                       boxed("算方差 σ", 2.2, 0.9, WHITE, 24),
                       boxed("减均值", 2.2, 0.9, YELL, 24),
                       boxed("除标准差", 2.2, 0.9, YELL, 24))
        steps.arrange(RIGHT, buff=0.4).next_to(tok, DOWN, buff=1.1)
        fit(steps, 0.98)
        self.play(FadeIn(steps, shift=DOWN * 0.05), run_time=0.8)
        self.at(6.0)
        self.play(*[s[0].animate.set_fill(YELL, opacity=0.4) for s in steps[2:]],
                  run_time=0.8)
        self.at(8.5)
        out = t("拉到零附近、单位方差", 28, GREEN, "BOLD").next_to(steps, DOWN, buff=1.0)
        self.play(FadeIn(out, shift=DOWN * 0.05), run_time=0.6)
        self.at(10.5)
        gamma = t("γ 缩放 · β 平移：模型自己定", 24, MUTED).next_to(out, DOWN, buff=0.7)
        self.play(FadeIn(gamma, shift=DOWN * 0.05), run_time=0.6)
        self.at(11.3)
        eps_note = t("ε = 1e-5：防止方差为零", 22, MUTED).next_to(gamma, DOWN, buff=0.7)
        self.play(FadeIn(eps_note, shift=DOWN * 0.05), run_time=0.5)
        self.at(11.6)
        # 快速闪公式（不碰音轨，纯视觉）
        self.play(FadeOut(VGroup(out, gamma, eps_note), run_time=0.3))
        f1 = t("μ = (1/d) Σ xi", 30, WHITE)
        f2 = t("σ² = (1/d) Σ (xi − μ)²", 30, WHITE)
        f3 = t("LN(x) = γ · (x − μ) / σ + β", 30, WHITE)
        formula = VGroup(f1, f2, f3).arrange(DOWN, buff=0.35, aligned_edge=LEFT)
        formula.next_to(steps, DOWN, buff=0.9)
        self.play(FadeIn(formula, shift=DOWN * 0.05), run_time=0.5)
        self.at(13.6)
        self.play(FadeOut(VGroup(tok, steps, formula), shift=UP * 0.05), run_time=0.4)
        # 页2：短句强调 + 三个 token 各自算 μ σ（撑起占屏）
        note = t("注意。每个 token，自己算。", 46, YELL, "BOLD")
        fit(note, 0.95)
        note.next_to(head, DOWN, buff=2.0)
        self.play(FadeIn(note, scale=1.1), run_time=0.7)
        self.at(14.6)
        rows = VGroup()
        for i, col in enumerate((CYAN, YELL, GREEN)):
            strip = Rectangle(width=4.6, height=0.7, color=col, fill_color=col, fill_opacity=0.35)
            row = VGroup(t(f"token {i + 1}", 24, MUTED), strip,
                         t("μ σ", 22, WHITE)).arrange(RIGHT, buff=0.45)
            rows.add(row)
        rows.arrange(DOWN, buff=0.45).next_to(note, DOWN, buff=1.4)
        self.play(FadeIn(rows, shift=DOWN * 0.05), run_time=0.6)
        self.at(15.2)
        indep = t("互不影响，各自调曝光", 26, MUTED).next_to(rows, DOWN, buff=0.6)
        self.play(FadeIn(indep, shift=DOWN * 0.05), run_time=0.5)
        self.at(16.0)
        self.play(FadeOut(VGroup(note, rows, indep), shift=UP * 0.05), run_time=0.4)
        # 页3：银行 vs 贷款
        bank = boxed("“银行” ±50", 3.2, 1.3, RED, 32, fill=0.25, weight="BOLD")
        loan = boxed("“贷款” ±2", 3.2, 1.3, CYAN, 32, fill=0.2, weight="BOLD")
        cards = VGroup(bank, loan).arrange(RIGHT, buff=1.2).next_to(head, DOWN, buff=2.4)
        self.play(FadeIn(cards, shift=DOWN * 0.05), run_time=0.8)
        self.at(18.4)
        self.play(bank.animate.scale(1.15), run_time=0.5)   # 一起算：大值压倒小值
        self.at(19.4)
        together = t("一起算 → 小数字被吞掉", 28, WHITE).next_to(cards, DOWN, buff=1.2)
        self.play(FadeIn(together, shift=DOWN * 0.05), run_time=0.6)
        self.at(21.1)
        self.play(bank.animate.scale(1 / 1.15), run_time=0.4)
        self.at(21.9)
        cross = self.play_red_cross(together)
        self.at(23.0)
        apart = t("分开算：谁都不被洗掉", 30, GREEN, "BOLD").next_to(together, DOWN, buff=1.0)
        self.play(FadeIn(apart, shift=DOWN * 0.05), run_time=0.6)
        self.at(24.4)
        sem = t("语义差异，完整保留", 24, MUTED).next_to(apart, DOWN, buff=0.8)
        self.play(FadeIn(sem, shift=DOWN * 0.05), run_time=0.5)
        self.at(26.3)
        self.play(FadeOut(VGroup(cards, together, cross, apart, sem), shift=UP * 0.05), run_time=0.4)
        ask = t("减均值，真的非做不可吗？", 38, YELL, "BOLD")
        fit(ask, 0.95)
        ask.next_to(head, DOWN, buff=2.8)
        self.play(FadeIn(ask, scale=1.08), run_time=0.7)
        self.at(28.0)
        mini = VGroup(boxed("“银行” ±50", 2.6, 0.8, RED, 22),
                      boxed("“贷款” ±2", 2.6, 0.8, CYAN, 22)).arrange(RIGHT, buff=0.8)
        mini.next_to(ask, DOWN, buff=1.8)
        self.play(FadeIn(mini, shift=DOWN * 0.05), run_time=0.6)
        self.at(28.8)
        tease = boxed("RMSNorm？", 3.2, 1.2, GREEN, 36, fill=0.2, weight="BOLD")
        tease.next_to(mini, DOWN, buff=1.4)
        self.play(FadeIn(tease, scale=1.06), run_time=0.6)
        self.pad_to_voice()


# ---------------- S4 RMSNorm：省掉减均值 ----------------
class S4(_Base):
    def construct(self):
        self.footer()
        head = t("RMSNorm：省掉减均值", 40, YELL, "BOLD").to_edge(UP, buff=1.2)
        self.play(FadeIn(head, shift=DOWN * 0.05))

        # 页1：LayerNorm 两步 vs RMSNorm 一步
        self.at(1.0)
        ln_l = t("LayerNorm", 30, MUTED)
        ln_steps = VGroup(boxed("减均值", 2.0, 0.85, WHITE, 24),
                          boxed("除标准差", 2.2, 0.85, WHITE, 24),
                          boxed("γ 缩放", 2.0, 0.85, WHITE, 24))
        ln_steps.arrange(RIGHT, buff=0.35)
        ln = VGroup(ln_l, ln_steps).arrange(DOWN, buff=0.5)
        ln.next_to(head, DOWN, buff=1.0)
        self.play(FadeIn(ln, shift=DOWN * 0.05), run_time=0.7)
        self.at(3.2)
        cross = self.play_red_cross(ln_steps[0])   # 减均值被划掉
        self.at(5.2)
        rm_l = t("RMSNorm", 30, GREEN, "BOLD")
        rm_steps = VGroup(boxed("除均方根", 2.4, 0.85, YELL, 24, fill=0.3),
                          boxed("γ 缩放", 2.0, 0.85, YELL, 24, fill=0.3))
        rm_steps.arrange(RIGHT, buff=0.35)
        rm = VGroup(rm_l, rm_steps).arrange(DOWN, buff=0.5)
        rm.next_to(ln, DOWN, buff=1.0)
        self.play(FadeIn(rm, shift=DOWN * 0.05), run_time=0.8)
        self.at(7.6)
        keep = t("尺度控制，还在", 30, YELL, "BOLD").next_to(rm, DOWN, buff=0.7)
        self.play(FadeIn(keep, scale=1.05), run_time=0.5)
        self.at(10.0)
        fear = t("子层真正怕的：", 26, MUTED).next_to(keep, DOWN, buff=0.5)
        self.play(FadeIn(fear, shift=DOWN * 0.05), run_time=0.5)
        self.at(11.5)
        boom = t("数值过大 → 梯度爆炸", 30, RED, "BOLD").next_to(fear, DOWN, buff=0.4)
        self.play(FadeIn(boom, scale=1.08), run_time=0.6)
        self.at(14.0)
        notbias = t("不是“偏正偏负”", 24, MUTED).next_to(boom, DOWN, buff=0.45)
        self.play(FadeIn(notbias, shift=DOWN * 0.05), run_time=0.5)
        self.at(16.0)
        self.play(FadeOut(VGroup(ln, cross, rm, keep, fear, boom, notbias),
                          shift=UP * 0.05), run_time=0.4)
        # 页2：转折 + 低精度警告
        self.at(18.6)
        warn = boxed("低精度下：归一化决定计算会不会崩", 6.6, 1.2, RED, 28, fill=0.25, weight="BOLD")
        warn.next_to(head, DOWN, buff=3.0)
        self.play(FadeIn(warn, scale=1.06), run_time=0.8)
        self.at(23.5)
        q = t("怎么个崩法？", 42, YELL, "BOLD").next_to(warn, DOWN, buff=2.0)
        self.play(FadeIn(q, scale=1.1), run_time=0.7)
        self.pad_to_voice()


# ---------------- S5 BF16：数值刚性需求 ----------------
class S5(_Base):
    def construct(self):
        self.footer()
        head = t("低精度下，归一化是安全网", 40, YELL, "BOLD").to_edge(UP, buff=1.2)
        self.play(FadeIn(head, shift=DOWN * 0.05))

        # 页1：BF16 尾数对比
        self.at(0.8)
        fp = t("FP32：23 位尾数", 26, MUTED)
        fp_bar = Rectangle(width=6.4, height=1.0, color=MUTED, fill_color=MUTED, fill_opacity=0.7)
        bf = t("BF16：8 位尾数", 26, CYAN, "BOLD")
        bf_bar = Rectangle(width=2.3, height=1.0, color=CYAN, fill_color=CYAN, fill_opacity=0.8)
        g1 = VGroup(fp, fp_bar).arrange(DOWN, buff=0.35)
        g2 = VGroup(bf, bf_bar).arrange(DOWN, buff=0.35)
        cmp = VGroup(g1, g2).arrange(DOWN, buff=0.8, aligned_edge=LEFT).set_x(0)
        cmp.next_to(head, DOWN, buff=1.2)
        prec = t("最小精度 ≈ 1e-8", 30, YELL, "BOLD").next_to(cmp, DOWN, buff=0.8)
        ticks = VGroup()
        for i, lab in enumerate(("1e0", "1e-2", "1e-4", "1e-6", "1e-8")):
            x = LEFT * 3.2 + RIGHT * (i * 1.6)
            ticks.add(Line(x + UP * 0.12, x + DOWN * 0.12, color=MUTED, stroke_width=3))
            ticks.add(t(lab, 22, YELL if lab == "1e-8" else MUTED,
                        "BOLD" if lab == "1e-8" else "NORMAL").next_to(x, DOWN, buff=0.25))
        mags = VGroup(Line(LEFT * 3.2, RIGHT * 3.2, color=MUTED, stroke_width=4), ticks)
        mags.next_to(prec, DOWN, buff=0.8)
        fp8 = t("超大模型甚至用更低精度：FP8 / MXFP4", 24, MUTED).next_to(mags, DOWN, buff=0.5)
        self.play(FadeIn(cmp, shift=DOWN * 0.05), run_time=0.9)
        self.at(3.2)
        self.play(FadeIn(fp8, shift=DOWN * 0.05), run_time=0.5)
        self.at(5.0)
        self.play(FadeIn(prec, scale=1.06), run_time=0.6)
        self.at(6.6)
        # 精度量级标尺：1e0 → 1e-8（撑起页1占屏）
        self.play(FadeIn(mags, shift=DOWN * 0.05), run_time=0.7)
        self.at(8.4)
        self.play(FadeOut(VGroup(cmp, prec, mags, fp8), shift=UP * 0.05), run_time=0.4)
        # 页2：logits 误差网格 80%
        cells = VGroup()
        for i in range(25):
            col = RED if i < 20 else GREEN
            cells.add(Rectangle(width=0.85, height=0.85, color=col,
                                fill_color=col, fill_opacity=0.85))
        cells.arrange_in_grid(5, 5, buff=0.28).next_to(head, DOWN, buff=1.3)
        self.play(FadeIn(cells, shift=DOWN * 0.05), run_time=0.8)
        self.at(12.5)
        big = t("80% 元素误差 > 0.01", 40, RED, "BOLD").next_to(cells, DOWN, buff=0.9)
        self.play(FadeIn(big, scale=1.1), run_time=0.8)
        self.at(15.6)
        src = t("BF16 跑 logits，同一份代码", 24, MUTED).next_to(big, DOWN, buff=0.55)
        self.play(FadeIn(src, shift=DOWN * 0.05), run_time=0.5)
        self.at(18.4)
        self.play(FadeOut(VGroup(cells, big, src), shift=UP * 0.05), run_time=0.4)
        # 页3：根源 + eps 安全网
        root = boxed("根源：归一化附近的低精度乘加", 6.4, 1.1, YELL, 26, fill=0.25, weight="BOLD")
        root.next_to(head, DOWN, buff=1.5)
        self.play(FadeIn(root, scale=1.06), run_time=0.7)
        self.at(20.8)
        div = t("分母：mean(x²) + ε", 28, WHITE).next_to(root, DOWN, buff=1.0)
        self.play(FadeIn(div, shift=DOWN * 0.05), run_time=0.5)
        self.at(22.6)
        eps = t("ε = 1e-6", 36, YELL, "BOLD").next_to(div, DOWN, buff=0.7)
        self.play(FadeIn(eps, scale=1.1), run_time=0.6)
        self.at(24.6)
        net = t("BF16 下的刚性安全网", 30, GREEN, "BOLD").next_to(eps, DOWN, buff=0.8)
        self.play(FadeIn(net, shift=DOWN * 0.05), run_time=0.5)
        self.at(26.8)
        dsv = boxed("DeepSeek-V4-Pro：rms_norm_eps = 1e-6", 6.4, 0.95, CYAN, 24)
        dsv.next_to(net, DOWN, buff=0.8)
        self.play(FadeIn(dsv, shift=DOWN * 0.05), run_time=0.6)
        self.at(32.0)
        self.play(FadeOut(VGroup(root, div, eps, net, dsv), shift=UP * 0.05), run_time=0.4)
        # 页4：位置转折
        pos = t("归一化放哪个位置，差别巨大", 34, WHITE, "BOLD")
        fit(pos, 0.95)
        pos.next_to(head, DOWN, buff=3.4)
        self.play(FadeIn(pos, scale=1.06), run_time=0.7)
        self.at(34.2)
        diff = t("差别巨大", 28, WHITE, "BOLD").next_to(pos, DOWN, buff=1.0)
        self.play(FadeIn(diff, shift=DOWN * 0.05), run_time=0.5)
        self.at(34.9)
        bar_g = Rectangle(width=4.0, height=0.75, color=GREEN, fill_color=GREEN, fill_opacity=0.8)
        bar_r = Rectangle(width=1.6, height=0.75, color=RED, fill_color=RED, fill_opacity=0.8)
        gl = t("放在前面", 24, GREEN, "BOLD").next_to(bar_g, DOWN, buff=0.3)
        rl = t("放在后面", 24, RED, "BOLD").next_to(bar_r, DOWN, buff=0.3)
        bars2 = VGroup(VGroup(bar_g, gl), VGroup(bar_r, rl)).arrange(RIGHT, buff=0.8, aligned_edge=UP)
        bars2.next_to(diff, DOWN, buff=0.9)
        self.play(FadeIn(bars2, shift=DOWN * 0.05), run_time=0.7)
        self.at(36.0)
        q = t("放后面，会怎样？", 44, YELL, "BOLD").next_to(bars2, DOWN, buff=1.0)
        self.play(FadeIn(q, scale=1.1), run_time=0.7)
        self.pad_to_voice()


# ---------------- S6 Pre-Norm vs Post-Norm（核心段） ----------------
class S6(_Base):
    def construct(self):
        self.footer()
        head = t("放前面，还是放后面？", 40, YELL, "BOLD").to_edge(UP, buff=1.2)
        self.play(FadeIn(head, shift=DOWN * 0.05))

        # 页1：Post-Norm 链 + 梯度回传衰减
        self.at(0.9)
        x0 = boxed("x", 1.4, 0.9, CYAN, 30, fill=0.2)
        f0 = boxed("子层 F", 2.6, 0.9, MUTED, 26)
        plus0 = t("+", 36, WHITE, "BOLD")
        norm0 = boxed("Norm", 2.2, 0.9, RED, 26, fill=0.3)
        y0 = boxed("y", 1.4, 0.9, GREEN, 30, fill=0.2)
        chain = VGroup(x0, f0, plus0, norm0, y0).arrange(RIGHT, buff=0.3)
        chain.next_to(head, DOWN, buff=1.1)
        fit(chain, 0.98)
        lab0 = t("Post-Norm：先算子层，加残差，再归一化", 24, MUTED).next_to(chain, DOWN, buff=0.6)
        self.play(FadeIn(VGroup(chain, lab0), shift=DOWN * 0.05), run_time=0.8)
        self.at(4.4)
        # 梯度回传：穿 Norm 逐层衰减（三支递减箭头）
        grad_lab = t("梯度回传，逐层穿过 Norm", 26, RED, "BOLD").next_to(lab0, DOWN, buff=0.9)
        self.play(FadeIn(grad_lab, shift=DOWN * 0.05), run_time=0.5)
        self.at(6.3)
        arrows = VGroup()
        for i, (wd, op) in enumerate(((12, 1.0), (7, 0.7), (3.5, 0.45))):
            ar = Arrow(RIGHT * 3.2, LEFT * 3.2, color=RED, stroke_width=wd,
                       stroke_opacity=op, buff=0.0)
            ar.shift(DOWN * (1.6 + i * 0.75))
            arrows.add(ar)
        arrows.next_to(grad_lab, DOWN, buff=0.6)
        self.play(Create(arrows[0]), run_time=0.5)
        self.play(Create(arrows[1]), run_time=0.5)
        self.play(Create(arrows[2]), run_time=0.5)
        self.at(10.5)
        exp = t("多层连乘 → 指数级放大或衰减", 28, RED).next_to(arrows, DOWN, buff=0.8)
        self.play(FadeIn(exp, shift=DOWN * 0.05), run_time=0.6)
        self.at(12.6)
        warm = t("早期训练尤其危险", 26, MUTED).next_to(exp, DOWN, buff=0.5)
        self.play(FadeIn(warm, shift=DOWN * 0.05), run_time=0.5)
        self.at(15.1)
        self.play(FadeOut(VGroup(chain, lab0, grad_lab, arrows, exp, warm),
                          shift=UP * 0.05), run_time=0.4)
        # 页2：Pre-Norm 竖排链 + 右侧主路直达（竖屏上下读，撑起占屏）
        x1 = boxed("x", 3.4, 1.2, CYAN, 34, fill=0.2)
        norm1 = boxed("Norm", 3.4, 1.2, YELL, 32, fill=0.45, weight="BOLD")
        f1 = boxed("子层 F", 3.4, 1.2, CYAN, 30)
        y1 = boxed("y", 3.4, 1.2, GREEN, 34, fill=0.2)
        chain2 = VGroup(x1, norm1, f1, y1).arrange(DOWN, buff=0.65)
        ar1 = Arrow(x1.get_bottom(), norm1.get_top(), color=WHITE, buff=0.15, stroke_width=6)
        ar2 = Arrow(norm1.get_bottom(), f1.get_top(), color=WHITE, buff=0.15, stroke_width=6)
        ar3 = Arrow(f1.get_bottom(), y1.get_top(), color=WHITE, buff=0.15, stroke_width=6)
        chain2.add(ar1, ar2, ar3)
        chain2.next_to(head, DOWN, buff=2.6)
        lab2 = t("Pre-Norm：先稳住输入，再做增量", 26, YELL, "BOLD").rotate(PI / 2) \
            .next_to(chain2, LEFT, buff=0.5)
        self.play(FadeIn(VGroup(chain2, lab2), shift=DOWN * 0.05), run_time=0.8)
        self.at(17.8)
        self.play(norm1[0].animate.set_fill(YELL, opacity=0.7), run_time=0.5)
        self.at(19.5)
        # 残差主路直达箭头（右侧竖箭头 + 竖排标签）
        bypass2 = Arrow(x1.get_right() + RIGHT * 0.6, y1.get_right() + RIGHT * 0.6,
                        color=GREEN, stroke_width=9, buff=0.1)
        straight_l = t("主路直达，梯度几乎不衰减", 24, GREEN, "BOLD").rotate(PI / 2) \
            .next_to(bypass2, RIGHT, buff=0.3)
        self.play(Create(bypass2), FadeIn(straight_l, shift=UP * 0.05), run_time=1.0)
        self.at(24.6)
        self.play(FadeOut(VGroup(chain2, lab2, bypass2, straight_l), shift=UP * 0.05),
                  run_time=0.4)
        # 页3：立规矩
        rule = t("放在前面，不是装饰，是立规矩", 36, YELL, "BOLD")
        fit(rule, 0.95)
        rule.next_to(head, DOWN, buff=3.4)
        self.play(FadeIn(rule, scale=1.1), run_time=0.8)
        self.at(27.0)
        q = t("那代码，长什么样？", 40, WHITE, "BOLD").next_to(rule, DOWN, buff=2.4)
        self.play(FadeIn(q, scale=1.06), run_time=0.6)
        self.pad_to_voice()


# ---------------- S7 四行代码 + DeepSeek-V4-Pro ----------------
class S7(_Base):
    def construct(self):
        self.footer()
        head = t("四行代码", 42, YELL, "BOLD").to_edge(UP, buff=1.2)
        self.play(FadeIn(head, shift=DOWN * 0.05))

        # 页1：4 行伪代码
        self.at(0.8)
        code_frame = Rectangle(width=7.0, height=4.1, color=MUTED, fill_color=BLACK,
                               fill_opacity=0.35)
        lines = VGroup(
            t("a = rms_norm(x)", 28, YELL),
            t("x = x + attention(a)", 28, GREEN),
            t("f = rms_norm(x)", 28, YELL),
            t("x = x + ffn(f)", 28, GREEN),
        ).arrange(DOWN, buff=0.5, aligned_edge=LEFT)
        lines.move_to(code_frame.get_center())
        code = VGroup(code_frame, lines).next_to(head, DOWN, buff=2.6)
        self.play(FadeIn(code_frame, shift=DOWN * 0.05), run_time=0.4)
        self.at(1.4)
        self.play(FadeIn(lines[0], shift=DOWN * 0.05), run_time=0.6)
        self.at(3.6)
        self.play(FadeIn(lines[1], shift=DOWN * 0.05), run_time=0.6)
        self.at(6.0)
        self.play(FadeIn(lines[2], shift=DOWN * 0.05), run_time=0.6)
        self.at(7.8)
        self.play(FadeIn(lines[3], shift=DOWN * 0.05), run_time=0.6)
        self.at(10.0)
        nope = t("没有一行是“把残差归一化”", 28, WHITE).next_to(code, DOWN, buff=0.7)
        self.play(FadeIn(nope, shift=DOWN * 0.05), run_time=0.6)
        self.at(13.2)
        self.play(FadeOut(VGroup(code, nope), shift=UP * 0.05), run_time=0.4)
        # 页2：节奏循环（竖排三步 + 循环标 + 八字口诀，撑起占屏）
        r1 = boxed("先稳住", 4.6, 1.2, YELL, 34, fill=0.3, weight="BOLD")
        r2 = boxed("做增量", 4.6, 1.2, CYAN, 34)
        r3 = boxed("再加回", 4.6, 1.2, GREEN, 34)
        loop = VGroup(r1, r2, r3).arrange(DOWN, buff=1.3)
        ar12 = Arrow(r1.get_bottom(), r2.get_top(), color=WHITE, buff=0.2, stroke_width=6)
        ar23 = Arrow(r2.get_bottom(), r3.get_top(), color=WHITE, buff=0.2, stroke_width=6)
        loop.add(ar12, ar23)
        loop.next_to(head, DOWN, buff=1.4)
        self.play(FadeIn(loop, shift=DOWN * 0.05), run_time=0.8)
        self.at(13.8)
        self.play(Create(ar12), Create(ar23), run_time=0.5)
        self.at(14.6)
        badge = t("循环 ×61", 26, YELL, "BOLD").rotate(PI / 2).next_to(loop, RIGHT, buff=0.4)
        self.play(FadeIn(badge, shift=UP * 0.05), run_time=0.5)
        self.at(15.2)
        eight = t("先稳住，做增量，再加回", 34, WHITE, "BOLD").next_to(loop, DOWN, buff=0.7)
        self.play(FadeIn(eight, scale=1.06), run_time=0.6)
        # 八字口诀画面延到「DeepSeek-V4-Pro 就是这么写的」台词结束，避免空屏等语音
        self.at(18.6)
        self.play(FadeOut(VGroup(loop, ar12, ar23, badge, eight), shift=UP * 0.05), run_time=0.4)
        # 页3：DeepSeek-V4-Pro 参数卡 + Hyper-Connections 4 车道（合成一页，车道视觉贯穿到最后）
        dsv_t = t("DeepSeek-V4-Pro", 40, CYAN, "BOLD")
        dsv_s = t("61 层 · 宽度 7168 · eps 1e-6", 30, WHITE)
        dsv = VGroup(dsv_t, dsv_s).arrange(DOWN, buff=0.4).next_to(head, DOWN, buff=1.3)
        self.play(FadeIn(dsv_t, shift=DOWN * 0.05), run_time=0.6)
        self.at(21.2)
        self.play(FadeIn(dsv_s, shift=DOWN * 0.05), run_time=0.5)
        self.at(22.2)
        self.play(dsv_s.animate.scale(1.07), run_time=0.3)
        self.play(dsv_s.animate.scale(1 / 1.07), run_time=0.3)
        # Attn / FFN 前各一个 RMSNorm：双行小图填充参数卡到 HC 的窗口（台词 [20] 的视觉）
        self.at(23.0)
        arow = VGroup(boxed("Norm", 1.6, 0.9, YELL, 28, fill=0.4, weight="BOLD"),
                      Arrow(LEFT * 0.3, RIGHT * 0.3, color=WHITE, buff=0.15),
                      boxed("Attn", 2.6, 0.9, CYAN, 28)).arrange(RIGHT, buff=0.4)
        frow = VGroup(boxed("Norm", 1.6, 0.9, YELL, 28, fill=0.4, weight="BOLD"),
                      Arrow(LEFT * 0.3, RIGHT * 0.3, color=WHITE, buff=0.15),
                      boxed("FFN", 2.6, 0.9, CYAN, 28)).arrange(RIGHT, buff=0.4)
        pre_rms = VGroup(arow, frow).arrange(DOWN, buff=0.7)
        pre_cap = t("Attn / FFN 前各一个 RMSNorm", 24, MUTED)
        pre = VGroup(pre_rms, pre_cap).arrange(DOWN, buff=0.35).next_to(dsv, DOWN, buff=0.9)
        self.play(FadeIn(pre, shift=DOWN * 0.05), run_time=0.7)
        self.at(26.5)
        self.play(FadeOut(pre, run_time=0.35))
        self.at(26.9)
        hc = t("Hyper-Connections：残差升级成多车道", 26, GREEN, "BOLD")
        fit(hc, 0.95)
        hc.next_to(dsv, DOWN, buff=0.35)
        lanes = VGroup()
        for i in range(4):
            nb = boxed("Norm", 1.15, 0.5, YELL, 18, fill=0.4)
            ln = Line(nb.get_bottom() + DOWN * 0.05, nb.get_bottom() + DOWN * 0.95,
                      color=CYAN, stroke_width=5)
            lanes.add(VGroup(nb, ln))
        lanes.arrange(RIGHT, buff=0.6).next_to(hc, DOWN, buff=0.4)
        self.play(FadeIn(hc, shift=DOWN * 0.05), run_time=0.6)
        self.at(27.7)
        self.play(FadeIn(lanes, shift=DOWN * 0.05), run_time=0.8)
        self.at(30.2)
        # 混合容器：大框包住 4 条 Norm 车道，标题挂在框下
        mix_box = Rectangle(width=lanes.width + 0.9, height=lanes.height + 0.4,
                            color=YELL, stroke_width=4, fill_color=YELL, fill_opacity=0.07)
        mix_box.move_to(lanes.get_center())
        mix_lab = t("混合 4 份状态", 24, YELL, "BOLD").next_to(mix_box, DOWN, buff=0.25)
        mix = VGroup(mix_box, mix_lab)
        self.play(FadeIn(mix, shift=DOWN * 0.05), run_time=0.5)
        self.at(31.0)
        # 字幕上方小字：mHC 留到后续系列展开（不碰音轨）
        mhc_note = t("mHC 的内容，后续 DeepSeek 技术解密系列会解释，这里不展开", 22, MUTED)
        mhc_note.to_edge(DOWN, buff=3.2)
        self.play(FadeIn(mhc_note, shift=DOWN * 0.05), run_time=0.5)
        self.at(33.5)
        guard = t("归一化依然守在每条车道入口", 26, WHITE).next_to(mix, DOWN, buff=0.7)
        self.play(FadeIn(guard, shift=DOWN * 0.05), run_time=0.5)
        self.at(35.8)
        q = t("四份状态怎么混？", 38, YELL, "BOLD").next_to(guard, DOWN, buff=0.9)
        self.play(FadeIn(q, scale=1.08), run_time=0.7)
        self.pad_to_voice()


# ---------------- S8 总结 + 品牌尾卡 ----------------
class S8(_Base):
    def construct(self):
        self.footer()
        head = t("分工 + 正确的顺序", 40, YELL, "BOLD").to_edge(UP, buff=1.2)
        self.play(FadeIn(head, shift=DOWN * 0.05))

        # 页1：三职责卡
        self.at(0.9)
        c1 = VGroup(boxed("捷径保通路", 2.8, 1.0, GREEN, 28, fill=0.25, weight="BOLD"),
                    t("残差：信号有路走", 22, MUTED)).arrange(DOWN, buff=0.35)
        c2 = VGroup(boxed("归一化管尺度", 2.8, 1.0, YELL, 28, fill=0.3, weight="BOLD"),
                    t("每次加工前稳压", 22, MUTED)).arrange(DOWN, buff=0.35)
        c3 = VGroup(boxed("Pre-Norm 排顺序", 3.2, 1.0, CYAN, 26, fill=0.2, weight="BOLD"),
                    t("先稳住，再加回", 22, MUTED)).arrange(DOWN, buff=0.35)
        cards = VGroup(c1, c2, c3).arrange(RIGHT, buff=0.7).next_to(head, DOWN, buff=2.2)
        fit(cards, 0.98)
        self.play(FadeIn(cards, shift=DOWN * 0.05), run_time=0.9)
        self.at(4.6)
        x61 = t("61 层不崩 = 分工 × 顺序", 30, WHITE, "BOLD").next_to(cards, DOWN, buff=1.1)
        self.play(FadeIn(x61, scale=1.05), run_time=0.6)
        self.at(6.4)
        noshot = t("不是哪一个“神招”", 26, MUTED).next_to(x61, DOWN, buff=1.0)
        self.play(FadeIn(noshot, shift=DOWN * 0.05), run_time=0.5)
        self.at(10.8)
        self.play(FadeOut(VGroup(cards, x61, noshot), shift=UP * 0.05), run_time=0.4)
        # 页2：互动问题 + 双选项 + 61 层 mini 视觉（撑起占屏，台词没说完不切页）
        ask = VGroup(t("残差主路：保持纯粹直通，", 34, WHITE, "BOLD"),
                     t("还是学会混合多份状态？", 34, WHITE, "BOLD")).arrange(DOWN, buff=0.5)
        ask.next_to(head, DOWN, buff=2.2)
        self.play(FadeIn(ask, shift=DOWN * 0.05), run_time=0.7)
        self.at(12.6)
        choice = VGroup(boxed("纯直通", 2.6, 1.0, GREEN, 28, fill=0.2, weight="BOLD"),
                        boxed("混合多份状态", 3.2, 1.0, YELL, 26, fill=0.25, weight="BOLD")) \
            .arrange(RIGHT, buff=1.2).next_to(ask, DOWN, buff=1.4)
        self.play(FadeIn(choice, shift=DOWN * 0.05), run_time=0.6)
        self.at(14.0)
        minis = VGroup()
        for _ in range(3):
            minis.add(VGroup(boxed("N", 0.5, 0.7, YELL, 16, fill=0.4),
                             boxed("层", 0.7, 0.7, CYAN, 14)).arrange(RIGHT, buff=0.12))
        minis.arrange(RIGHT, buff=0.4)
        minigrp = VGroup(minis, t("× 61", 26, YELL, "BOLD")).arrange(RIGHT, buff=0.5) \
            .next_to(choice, DOWN, buff=1.0)
        self.play(FadeIn(minigrp, shift=DOWN * 0.05), run_time=0.5)
        self.at(18.1)
        cmt = t("评论区聊聊", 28, YELL, "BOLD").next_to(minigrp, DOWN, buff=0.7)
        self.play(FadeIn(cmt, scale=1.05), run_time=0.5)
        self.at(20.2)
        self.play(FadeOut(VGroup(ask, choice, minigrp, cmt), shift=UP * 0.05), run_time=0.4)
        # 页3：品牌尾卡
        logo = ImageMobject("avatar-sjai-round.png")
        logo.scale_to_fit_width(3.0)
        logo.next_to(head, DOWN, buff=1.0)
        self.play(FadeIn(logo, shift=DOWN * 0.05), run_time=0.6)
        self.at(21.2)
        follow = t("关注「数解AI」", 40, YELL, "BOLD").next_to(logo, DOWN, buff=0.6)
        self.play(FadeIn(follow, scale=1.08), run_time=0.6)
        self.at(21.8)
        title = t("《归一化为什么总在前面？61层模型靠它不崩》", 27, WHITE, "BOLD")
        fit(title, 0.95)
        title.next_to(follow, DOWN, buff=0.7)
        self.play(FadeIn(title, shift=DOWN * 0.05), run_time=0.6)
        self.at(22.4)
        link = t("查看公众号文章", 30, GREEN, "BOLD").next_to(title, DOWN, buff=0.55)
        self.play(FadeIn(link, scale=0.95), run_time=0.6)
        self.at(23.0)
        nxt = t("下一篇：跟一句话走完 Transformer 全景", 27, CYAN, "BOLD")
        fit(nxt, 0.95)
        nxt.next_to(link, DOWN, buff=0.7)
        self.play(FadeIn(nxt, shift=DOWN * 0.05), run_time=0.6)
        self.pad_to_voice()


# ---------------- 封面帧 ----------------
class Cover(Scene):
    """封面帧：系列标签 + 主/副标题 + Pre-Norm block 视觉 + 底部公众号 logo。
    渲染：python3 -m manim render -qm -s --disable_caching scenes.py Cover
    关键内容须落在 3:4 安全区（frame y ∈ [-5.33, +5.33]）。
    """
    def construct(self):
        series = t("大模型原理 · 第 6 篇", 26, CYAN).to_edge(UP, buff=2.2)
        title = t("归一化为什么总在前面？61层模型靠它不崩", 44, YELL, "BOLD")
        title.set_width(config.frame_width * 0.8)
        title.next_to(series, DOWN, buff=0.5)
        subtitle = t("残差开直通车，归一化当稳压器", 32, WHITE).next_to(title, DOWN, buff=0.4)

        # 关键视觉：Pre-Norm block（Norm 在前的黄色高亮块）
        x0 = boxed("x", 1.5, 1.0, CYAN, 34, fill=0.2)
        nb = boxed("Norm", 2.4, 1.0, YELL, 30, fill=0.45, weight="BOLD")
        f0 = boxed("子层", 2.4, 1.0, CYAN, 30)
        plus0 = t("+", 40, WHITE, "BOLD")
        y0 = boxed("x + 增量", 2.9, 1.0, GREEN, 26, fill=0.2)
        chain = VGroup(x0, nb, f0, plus0, y0).arrange(RIGHT, buff=0.35)
        chain.next_to(subtitle, DOWN, buff=1.3)
        fit(chain, 0.98)
        lift = UP * 0.6
        straight = VGroup(
            Line(x0.get_top() + UP * 0.1, x0.get_top() + lift),
            Line(y0.get_top() + UP * 0.1, y0.get_top() + lift),
            Arrow(x0.get_top() + lift, y0.get_top() + lift, color=GREEN, stroke_width=8, buff=0.05),
        )
        tag = t("先稳住 · 做增量 · 再加回", 28, GREEN, "BOLD").next_to(chain, DOWN, buff=1.0)

        logo = ImageMobject("avatar-sjai-round.png")
        logo.scale_to_fit_width(2.2)
        logo.to_edge(DOWN, buff=1.9)

        self.add(series, title, subtitle, chain, straight, tag, logo)


if __name__ == "__main__":
    pass
