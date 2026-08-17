#!/usr/bin/env python3
"""《SFT微调：1万条数据就能让模型听话？》视频号 Manim 动画（竖屏 1080×1920）

8 个场景 S1-S8 + 封面 Cover，与 storyboard.md 一一对应（2026-08-15）。
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
VOICE_DUR = {"S1": 23.38, "S2": 32.97, "S3": 31.02, "S4": 30.11,
             "S5": 27.57, "S6": 35.23, "S7": 26.17, "S8": 37.35}
TAIL = 2.5


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


def prob_bars(n: int, heights: list, color: str) -> VGroup:
    """竖排概率条（词表候选），heights 为相对高度列表。"""
    bars = VGroup()
    for h in heights:
        bars.add(Rectangle(width=0.42, height=h, color=color,
                           fill_color=color, fill_opacity=0.55))
    bars.arrange(RIGHT, buff=0.07, aligned_edge=DOWN)
    return bars


def sub(base_str: str, sub_str: str, size: float = 30, sub_size: float = 17,
        color: str = WHITE, weight: str = "BOLD") -> VGroup:
    """主字符 + 下标（下标贴主字符右下角，顶部对齐基线下方）。"""
    base = t(base_str, size, color, weight)
    s = t(sub_str, sub_size, color, weight)
    s.next_to(base, DOWN, buff=0.02, aligned_edge=RIGHT)
    return VGroup(base, s)


def sup(base_str: str, sup_str: str, size: float = 30, sup_size: float = 17,
        color: str = WHITE, weight: str = "BOLD") -> VGroup:
    """主字符 + 上标（上标贴主字符右上角）。"""
    base = t(base_str, size, color, weight)
    s = t(sup_str, sup_size, color, weight)
    s.next_to(base, UP, buff=0.0, aligned_edge=RIGHT)
    return VGroup(base, s)


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

    def play_scroll_unroll(self, grp, run_time: float = 1.5):
        """缓慢卷轴：等高矩形从左缘向右摊开，再露出文字。grp = boxed() 的 VGroup(框, 字)。"""
        box, txt = grp[0], grp[1]
        left_x = box.get_left()[0]
        y = box.get_center()[1]
        h = box.height
        full_w = box.width
        color = box.get_stroke_color()
        fill_c = box.get_fill_color()
        fill_o = box.get_fill_opacity()
        sw = box.get_stroke_width()

        tracker = ValueTracker(0.08)
        growing = Rectangle(
            width=0.08, height=h, color=color,
            fill_color=fill_c, fill_opacity=fill_o, stroke_width=sw,
        )
        growing.move_to(np.array([left_x + 0.04, y, 0]))

        def upd(mob):
            w = max(tracker.get_value(), 0.08)
            new = Rectangle(
                width=w, height=h, color=color,
                fill_color=fill_c, fill_opacity=fill_o, stroke_width=sw,
            )
            new.move_to(np.array([left_x + w / 2.0, y, 0]))
            mob.become(new)

        growing.add_updater(upd)
        txt.set_opacity(0)
        self.add(growing)
        self.play(tracker.animate.set_value(full_w),
                  run_time=run_time * 0.78, rate_func=smooth)
        growing.clear_updaters()
        self.remove(growing)
        self.add(grp)
        self.play(txt.animate.set_opacity(1), run_time=run_time * 0.22)


if __name__ == "__main__":
    pass

# ---------------- S1 开场钩子：预训练贵到独角兽放弃 ----------------
class S1(_Base):
    def construct(self):
        self.footer()
        head = t("预训练有多贵？", 40, YELL, "BOLD").to_edge(UP, buff=1.2)
        self.play(FadeIn(head, shift=DOWN * 0.05))

        # 段1（0-1.3s）：开场钩子「贵到连独角兽都撑不住」
        self.at(0.26)
        hook = boxed("贵到连独角兽都撑不住", 5.6, 1.15, RED, 32, fill=0.2, weight="BOLD")
        hook.next_to(head, DOWN, buff=1.2)
        self.play(FadeIn(hook, scale=1.05), run_time=0.7)

        # 段2（1.9-8.9s）：36氪「六小虎」至少 2 家放弃
        self.at(2.20)
        self.play(FadeOut(hook, shift=UP * 0.03), run_time=0.3)
        six = boxed("中国 6 家大模型独角兽", 5.2, 1.1, CYAN, 30, fill=0.2, weight="BOLD")
        six.next_to(head, DOWN, buff=1.3)
        self.play(FadeIn(six, shift=DOWN * 0.05), run_time=0.7)
        self.at(4.84)
        giveup = boxed("至少 2 家已放弃预训练", 5.2, 1.1, RED, 30, fill=0.2, weight="BOLD")
        giveup.next_to(six, DOWN, buff=1.4)
        ar = Arrow(six.get_bottom() + DOWN * 0.1, giveup.get_top() + UP * 0.1,
                   color=MUTED, buff=0.1, stroke_width=6)
        self.play(Create(ar), FadeIn(giveup, shift=DOWN * 0.05), run_time=0.8)

        # 段3（9.5-21.4s）：李开复 + Character.AI
        self.at(8.81)
        self.play(FadeOut(VGroup(six, giveup, ar), shift=UP * 0.03), run_time=0.3)
        lkf = boxed("李开复：对初创公司性价比极低", 6.0, 1.1, WHITE, 28, weight="BOLD")
        lkf.next_to(head, DOWN, buff=1.3)
        self.play(FadeIn(lkf, shift=DOWN * 0.05), run_time=0.7)
        self.at(13.21)
        ca = boxed("Character.AI · 2024.08 放弃自研", 6.0, 1.1, CYAN, 28, weight="BOLD")
        ca.next_to(lkf, DOWN, buff=1.4)
        self.play(FadeIn(ca, shift=DOWN * 0.05), run_time=0.7)

        # 段4（22.0-26.5s）：问题悬念「每个公司都得从零造轮子吗？」
        self.at(19.81)
        self.play(FadeOut(VGroup(lkf, ca), shift=UP * 0.03), run_time=0.3)
        q = t("每个公司，都得从零造轮子吗？", 36, YELL, "BOLD")
        fit(q, 0.95)
        q.next_to(head, DOWN, buff=1.3)
        self.play(FadeIn(q, scale=1.1), run_time=0.7)
        self.pad_to_voice()

# ---------------- S2 账本对比：144 万倍 ----------------
class S2(_Base):
    def construct(self):
        self.footer()
        head = t("算笔账：SFT 便宜多少？", 38, YELL, "BOLD").to_edge(UP, buff=1.2)
        self.play(FadeIn(head, shift=DOWN * 0.05))

        # 段1（0-12.5s）：预训练成本（Qwen3-8B 82亿参数 + 36万亿token）
        self.at(0.49)
        model = boxed("Qwen3-8B：82 亿参数", 4.6, 1.1, CYAN, 30, fill=0.2, weight="BOLD")
        model.next_to(head, DOWN, buff=1.2)
        self.play(FadeIn(model, shift=DOWN * 0.05), run_time=0.7)
        self.at(3.93)
        pretok = boxed("预训练吃掉 36 万亿 token", 5.4, 1.1, WHITE, 28, weight="BOLD")
        pretok.next_to(model, DOWN, buff=1.3)
        self.play(FadeIn(pretok, shift=DOWN * 0.05), run_time=0.7)
        self.at(8.36)
        preflop = boxed("预训练 ≈ 1.77×10²⁴ FLOPs", 5.6, 1.2, YELL, 30, fill=0.2, weight="BOLD")
        preflop.next_to(pretok, DOWN, buff=1.3)
        self.play(FadeIn(preflop, scale=1.05), run_time=0.7)

        # 段2（13.1-26.5s）：SFT 成本（1万条×2500token）
        self.at(13.27)
        self.play(FadeOut(VGroup(model, pretok, preflop), shift=UP * 0.03), run_time=0.3)
        sftdata = boxed("SFT：1 万条指令回答对", 5.0, 1.1, CYAN, 30, fill=0.2, weight="BOLD")
        sftdata.next_to(head, DOWN, buff=1.2)
        self.play(FadeIn(sftdata, shift=DOWN * 0.05), run_time=0.7)
        self.at(17.70)
        sfttok = boxed("总共 2500 万 token", 4.6, 1.1, WHITE, 28, weight="BOLD")
        sfttok.next_to(sftdata, DOWN, buff=1.3)
        self.play(FadeIn(sfttok, shift=DOWN * 0.05), run_time=0.7)
        self.at(22.12)
        sftflop = boxed("SFT ≈ 1.23×10¹⁸ FLOPs", 5.2, 1.2, YELL, 30, fill=0.2, weight="BOLD")
        sftflop.next_to(sfttok, DOWN, buff=1.3)
        self.play(FadeIn(sftflop, scale=1.05), run_time=0.7)

        # 段3（27.1-33.5s）：144 万倍爆点
        self.at(27.04)
        self.play(FadeOut(VGroup(sftdata, sfttok, sftflop), shift=UP * 0.03), run_time=0.3)
        big = t("差多少？144 万倍", 44, YELL, "BOLD")
        fit(big, 0.95)
        big.next_to(head, DOWN, buff=1.3)
        self.play(FadeIn(big, scale=1.1), run_time=0.7)
        self.at(29.99)
        small = t("同样的参数，成本只有百万分之一", 30, GREEN, "BOLD")
        fit(small, 0.95)
        small.next_to(big, DOWN, buff=1.2)
        self.play(FadeIn(small, shift=DOWN * 0.05), run_time=0.7)
        self.pad_to_voice()

# ---------------- S3 同一模型，两种命运 ----------------
class S3(_Base):
    def construct(self):
        self.footer()
        head = t("同一个模型，同一个问题", 38, YELL, "BOLD").to_edge(UP, buff=1.2)
        self.play(FadeIn(head, shift=DOWN * 0.05))

        # 段1（0-3.3s）：两种命运
        self.at(0.54)
        fate = t("两种命运", 40, YELL, "BOLD").next_to(head, DOWN, buff=1.2)
        self.play(FadeIn(fate, scale=1.1), run_time=0.7)

        # 段2（3.9-15.2s）：base 续写「算法，并提供一个简单的 Python 实现」
        self.at(4.85)
        self.play(FadeOut(fate, shift=UP * 0.03), run_time=0.3)
        q = boxed("请解释什么是梯度下降", 5.2, 1.0, CYAN, 28, fill=0.2, weight="BOLD")
        q.next_to(head, DOWN, buff=1.2)
        self.play(FadeIn(q, shift=DOWN * 0.05), run_time=0.7)
        self.at(8.61)
        base = boxed("base：算法，并提供一个简单的 Python 实现", 6.6, 1.2, WHITE, 26, weight="BOLD")
        base.next_to(q, DOWN, buff=1.3)
        self.play(FadeIn(base, shift=DOWN * 0.05), run_time=0.7)
        self.at(12.92)
        wrong = t("知道知识，却没认出这是解释请求", 28, MUTED)
        fit(wrong, 0.95)
        wrong.next_to(base, DOWN, buff=1.0)
        self.play(FadeIn(wrong, shift=DOWN * 0.05), run_time=0.6)

        # 段3（15.3-22.5s）：post 稳定输出
        self.at(17.01)
        self.play(FadeOut(VGroup(q, base, wrong), shift=UP * 0.03), run_time=0.3)
        post = boxed("post：梯度下降是一种迭代算法", 6.2, 1.2, GREEN, 26, weight="BOLD")
        post.next_to(head, DOWN, buff=1.2)
        self.play(FadeIn(post, shift=DOWN * 0.05), run_time=0.7)
        self.at(20.46)
        struct = t("定义 · 直觉 · 举例，结构清晰", 30, GREEN, "BOLD")
        fit(struct, 0.95)
        struct.next_to(post, DOWN, buff=1.0)
        self.play(FadeIn(struct, shift=DOWN * 0.05), run_time=0.6)

        # 段4（23.1-28.8s）：参数相同，输出不同 + 悬念
        self.at(25.30)
        self.play(FadeOut(VGroup(post, struct), shift=UP * 0.03), run_time=0.3)
        same = t("参数规模相同，输出却完全不一样", 32, YELL, "BOLD")
        fit(same, 0.95)
        same.next_to(head, DOWN, buff=1.2)
        self.play(FadeIn(same, scale=1.05), run_time=0.7)
        self.at(27.99)
        q2 = t("后训练，到底改了什么？", 34, CYAN, "BOLD")
        fit(q2, 0.95)
        q2.next_to(same, DOWN, buff=1.2)
        self.play(FadeIn(q2, scale=1.1), run_time=0.7)
        self.pad_to_voice()

# ---------------- S4 实验：分布手掌→拳头 ----------------
class S4(_Base):
    def construct(self):
        self.footer()
        head = t("4090 上实测：base vs post", 38, YELL, "BOLD").to_edge(UP, buff=1.2)
        self.play(FadeIn(head, shift=DOWN * 0.05))

        # 段1（0-8.5s）：五类指令
        self.at(0.43)
        five = boxed("五类指令：解释 / 改写 / 比较 / 代码 / 情感", 6.8, 1.1, CYAN, 26, fill=0.2, weight="BOLD")
        five.next_to(head, DOWN, buff=1.2)
        self.play(FadeIn(five, shift=DOWN * 0.05), run_time=0.7)
        self.at(4.31)
        tok = t("看首个 token 的概率分布", 30, WHITE, "BOLD")
        fit(tok, 0.95)
        tok.next_to(five, DOWN, buff=1.2)
        self.play(FadeIn(tok, shift=DOWN * 0.05), run_time=0.6)

        # 段2（9.1-22.0s）：base 手掌 vs post 拳头
        self.at(8.18)
        self.play(FadeOut(VGroup(five, tok), shift=UP * 0.03), run_time=0.3)
        base_lab = t("base：摊开的手掌", 30, WHITE, "BOLD").next_to(head, DOWN, buff=1.2)
        base_lab.set_x(0)
        self.play(FadeIn(base_lab, shift=DOWN * 0.05), run_time=0.6)
        self.at(10.33)
        base_bars = prob_bars(9, [0.3, 0.5, 0.2, 0.42, 0.28, 0.55, 0.35, 0.45, 0.3], WHITE)
        base_bars.next_to(base_lab, DOWN, buff=0.8)
        self.play(FadeIn(base_bars, shift=DOWN * 0.05), run_time=0.7)
        self.at(12.92)
        post_lab = t("post：握紧的拳头", 30, GREEN, "BOLD").next_to(base_bars, DOWN, buff=1.2)
        post_lab.set_x(0)
        self.play(FadeIn(post_lab, shift=DOWN * 0.05), run_time=0.6)
        self.at(15.07)
        post_bars = prob_bars(9, [0.9, 0.15, 0.1, 0.12, 0.1, 0.1, 0.1, 0.1, 0.1], GREEN)
        post_bars.next_to(post_lab, DOWN, buff=0.8)
        self.play(FadeIn(post_bars, shift=DOWN * 0.05), run_time=0.7)

        # 段3（22.6-34.9s）：聚合指标
        self.at(19.80)
        self.play(FadeOut(VGroup(base_lab, base_bars, post_lab, post_bars), shift=UP * 0.03), run_time=0.3)
        top1 = boxed("top-1：82% → 91.6%（+12%）", 5.4, 1.1, YELL, 28, fill=0.2, weight="BOLD")
        top1.next_to(head, DOWN, buff=1.2)
        self.play(FadeIn(top1, shift=DOWN * 0.05), run_time=0.7)
        self.at(23.25)
        ent = boxed("熵：0.9 → 0.33 bits（−63%）", 5.4, 1.1, GREEN, 28, fill=0.2, weight="BOLD")
        ent.next_to(top1, DOWN, buff=1.3)
        self.play(FadeIn(ent, shift=DOWN * 0.05), run_time=0.7)
        self.at(26.69)
        concl = t("不确定性，少了近三分之二", 32, YELL, "BOLD")
        fit(concl, 0.95)
        concl.next_to(ent, DOWN, buff=1.2)
        self.play(FadeIn(concl, scale=1.05), run_time=0.7)
        self.pad_to_voice()

# ---------------- S5 入职培训比喻 ----------------
class S5(_Base):
    def construct(self):
        self.footer()
        head = t("怎么理解？SFT 是入职培训", 38, YELL, "BOLD").to_edge(UP, buff=1.2)
        self.play(FadeIn(head, shift=DOWN * 0.05))

        # 段1（0-1.4s）：怎么理解
        self.at(0.30)
        intro = t("一句话：SFT 是入职培训", 34, YELL, "BOLD").next_to(head, DOWN, buff=1.2)
        self.play(FadeIn(intro, scale=1.05), run_time=0.6)

        # 段2（2.0-13.8s）：预训练=大学四年 + 老板问策略→马尔可夫链
        self.at(2.53)
        self.play(FadeOut(intro, shift=UP * 0.03), run_time=0.3)
        college = boxed("预训练 = 大学四年", 4.6, 1.1, CYAN, 30, fill=0.2, weight="BOLD")
        college.next_to(head, DOWN, buff=1.2)
        self.play(FadeIn(college, shift=DOWN * 0.05), run_time=0.7)
        self.at(6.07)
        know = t("微积分、概率、编程，什么都懂一点", 28, WHITE)
        fit(know, 0.95)
        know.next_to(college, DOWN, buff=1.0)
        self.play(FadeIn(know, shift=DOWN * 0.05), run_time=0.6)
        self.at(9.60)
        boss = boxed("老板问增长策略 → 你讲马尔可夫链", 6.4, 1.1, RED, 26, fill=0.15, weight="BOLD")
        boss.next_to(know, DOWN, buff=1.2)
        self.play(FadeIn(boss, shift=DOWN * 0.05), run_time=0.7)

        # 段3（14.0-17.0s）：不是不懂
        self.at(14.66)
        self.play(FadeOut(VGroup(college, know, boss), shift=UP * 0.03), run_time=0.3)
        notknow = t("不是不懂，是不知道这个场景该说什么", 30, WHITE, "BOLD")
        fit(notknow, 0.95)
        notknow.next_to(head, DOWN, buff=1.2)
        self.play(FadeIn(notknow, shift=DOWN * 0.05), run_time=0.6)

        # 段4（17.6-27.2s）：入职培训规则 + 结语
        self.at(18.20)
        self.play(FadeOut(notknow, shift=UP * 0.03), run_time=0.3)
        rule1 = boxed("老板问策略，就讲策略", 4.8, 1.0, GREEN, 28, fill=0.2, weight="BOLD")
        rule1.next_to(head, DOWN, buff=1.2)
        self.play(FadeIn(rule1, shift=DOWN * 0.05), run_time=0.6)
        self.at(21.23)
        rule2 = boxed("写邮件用「尊敬的」，别用「亲爱的」", 6.0, 1.0, GREEN, 26, fill=0.2, weight="BOLD")
        rule2.next_to(rule1, DOWN, buff=1.2)
        self.play(FadeIn(rule2, shift=DOWN * 0.05), run_time=0.6)
        self.at(24.26)
        concl = t("改变的不是知识，是该说什么、怎么说", 30, YELL, "BOLD")
        fit(concl, 0.95)
        concl.next_to(rule2, DOWN, buff=1.2)
        self.play(FadeIn(concl, scale=1.05), run_time=0.7)
        self.pad_to_voice()

# ---------------- S6 数学：交叉熵收窄 ----------------
class S6(_Base):
    def construct(self):
        self.footer()
        head = t("数学上：宽分布 → 窄分布", 38, YELL, "BOLD").to_edge(UP, buff=1.2)
        self.play(FadeIn(head, shift=DOWN * 0.05))

        # 段1（0-7.1s）：交叉熵公式 + 数据变了
        self.at(0.49)
        ce = t("H(p,q) = −Σ p(x) log q(x)", 34, WHITE, "BOLD")
        fit(ce, 0.95)
        ce.next_to(head, DOWN, buff=1.2)
        self.play(FadeIn(ce, shift=DOWN * 0.05), run_time=0.7)
        self.at(3.93)
        datachg = t("公式一样，关键是数据变了：指令回答对", 28, CYAN, "BOLD")
        fit(datachg, 0.95)
        datachg.next_to(ce, DOWN, buff=1.2)
        self.play(FadeIn(datachg, shift=DOWN * 0.05), run_time=0.6)

        # 段2（7.7-19.2s）：惩罚力度表
        self.at(7.86)
        self.play(FadeOut(VGroup(ce, datachg), shift=UP * 0.03), run_time=0.3)
        p1 = boxed("概率 50% → 罚 1 bit", 4.6, 1.0, WHITE, 28, fill=0.15, weight="BOLD")
        p1.next_to(head, DOWN, buff=1.2)
        self.play(FadeIn(p1, shift=DOWN * 0.05), run_time=0.6)
        self.at(10.81)
        p2 = boxed("降到 10% → 罚 3.3 bits", 4.6, 1.0, YELL, 28, fill=0.15, weight="BOLD")
        p2.next_to(p1, DOWN, buff=1.1)
        self.play(FadeIn(p2, shift=DOWN * 0.05), run_time=0.6)
        self.at(13.76)
        p3 = boxed("再降一个数量级 → 罚 6.6 bits", 5.2, 1.0, RED, 28, fill=0.15, weight="BOLD")
        p3.next_to(p2, DOWN, buff=1.1)
        self.play(FadeIn(p3, shift=DOWN * 0.05), run_time=0.6)

        # 段3（19.9-35.8s）：梯度 + 收窄
        self.at(20.15)
        self.play(FadeOut(VGroup(p1, p2, p3), shift=UP * 0.03), run_time=0.3)
        # 梯度公式：单 Text + Unicode 下标（ⱼ=U+2C7C 在 Noto Sans CJK SC 正常渲染为下标）
        # 手动 sub()/sup() 拼装会基线错位、减号渲染成下划线——改用单文本最干净
        grad = t("∂H/∂zⱼ = qⱼ − 1[j=x*]", 32, WHITE, "BOLD")
        fit(grad, 0.95)
        grad.next_to(head, DOWN, buff=1.2)
        self.play(FadeIn(grad, shift=DOWN * 0.05), run_time=0.7)
        self.at(24.57)
        up = boxed("正确 token：负梯度，往上推", 5.2, 1.0, GREEN, 28, fill=0.2, weight="BOLD")
        up.next_to(grad, DOWN, buff=1.2)
        self.play(FadeIn(up, shift=DOWN * 0.05), run_time=0.6)
        self.at(28.50)
        down = boxed("其他 token：往下压", 4.4, 1.0, RED, 28, fill=0.15, weight="BOLD")
        down.next_to(up, DOWN, buff=1.1)
        self.play(FadeIn(down, shift=DOWN * 0.05), run_time=0.6)
        self.at(32.43)
        concl = t("收窄，就这么发生了", 34, YELL, "BOLD")
        fit(concl, 0.95)
        concl.next_to(down, DOWN, buff=1.2)
        self.play(FadeIn(concl, scale=1.1), run_time=0.7)
        self.pad_to_voice()

# ---------------- S7 chat template 考勤卡 ----------------
class S7(_Base):
    def construct(self):
        self.footer()
        head = t("被忽略的关键：chat template", 38, YELL, "BOLD").to_edge(UP, buff=1.2)
        self.play(FadeIn(head, shift=DOWN * 0.05))

        # 段1（0-3.5s）：chat template
        self.at(0.50)
        ct = boxed("chat template", 4.0, 1.1, CYAN, 30, fill=0.2, weight="BOLD")
        ct.next_to(head, DOWN, buff=1.2)
        self.play(FadeIn(ct, shift=DOWN * 0.05), run_time=0.7)

        # 段2（4.1-13.9s）：base 纯文本 vs post 特殊标记
        self.at(4.48)
        self.play(FadeOut(ct, shift=UP * 0.03), run_time=0.3)
        base = boxed("base：纯文本续写", 4.2, 1.0, WHITE, 28, fill=0.15, weight="BOLD")
        base.next_to(head, DOWN, buff=1.2)
        self.play(FadeIn(base, shift=DOWN * 0.05), run_time=0.6)
        self.at(7.96)
        post = boxed("post：被特殊标记包裹", 4.6, 1.0, GREEN, 28, fill=0.2, weight="BOLD")
        post.next_to(base, DOWN, buff=1.2)
        self.play(FadeIn(post, shift=DOWN * 0.05), run_time=0.6)
        self.at(10.94)
        roles = t("用户 · 助手 · 系统", 30, GREEN, "BOLD")
        fit(roles, 0.95)
        roles.next_to(post, DOWN, buff=1.0)
        self.play(FadeIn(roles, shift=DOWN * 0.05), run_time=0.6)

        # 段3（14.5-26.3s）：考勤卡比喻 + 概率判断变了
        self.at(14.92)
        self.play(FadeOut(VGroup(base, post, roles), shift=UP * 0.03), run_time=0.3)
        card = boxed("像入职培训的考勤卡", 4.8, 1.1, YELL, 30, fill=0.2, weight="BOLD")
        card.next_to(head, DOWN, buff=1.2)
        self.play(FadeIn(card, shift=DOWN * 0.05), run_time=0.7)
        self.at(18.90)
        tell = t("只告诉模型：什么时候该说话", 30, WHITE, "BOLD")
        fit(tell, 0.95)
        tell.next_to(card, DOWN, buff=1.2)
        self.play(FadeIn(tell, shift=DOWN * 0.05), run_time=0.6)
        self.at(22.38)
        concl = t("角色标记一进来，概率判断整个变了", 30, CYAN, "BOLD")
        fit(concl, 0.95)
        concl.next_to(tell, DOWN, buff=1.2)
        self.play(FadeIn(concl, scale=1.05), run_time=0.7)
        self.pad_to_voice()

# ---------------- S8 听话≠说得好 + 品牌尾卡 ----------------
class S8(_Base):
    def construct(self):
        self.footer()
        head = t("SFT 解决了听话，没解决说得好", 36, YELL, "BOLD").to_edge(UP, buff=1.2)
        self.play(FadeIn(head, shift=DOWN * 0.05))

        # 段1（0-4.2s）：听话 vs 说得好
        self.at(0.49)
        obey = boxed("听话 ✓", 3.0, 1.0, GREEN, 30, fill=0.2, weight="BOLD")
        obey.next_to(head, DOWN, buff=1.2)
        self.play(FadeIn(obey, shift=DOWN * 0.05), run_time=0.6)

        # 段2（4.8-13.0s）：3 个风险
        self.at(4.92)
        self.play(FadeOut(obey, shift=UP * 0.03), run_time=0.3)
        r1 = boxed("编造事实（幻觉）", 4.2, 1.0, RED, 28, fill=0.15, weight="BOLD")
        r1.next_to(head, DOWN, buff=1.2)
        self.play(FadeIn(r1, shift=DOWN * 0.05), run_time=0.6)
        self.at(7.87)
        r2 = boxed("过度迎合用户", 4.0, 1.0, RED, 28, fill=0.15, weight="BOLD")
        r2.next_to(r1, DOWN, buff=1.1)
        self.play(FadeIn(r2, shift=DOWN * 0.05), run_time=0.6)
        self.at(10.33)
        r3 = boxed("学进有害格式", 4.0, 1.0, RED, 28, fill=0.15, weight="BOLD")
        r3.next_to(r2, DOWN, buff=1.1)
        self.play(FadeIn(r3, shift=DOWN * 0.05), run_time=0.6)

        # 段3（13.6-27.8s）：必要条件 + RLHF + 关注 + 下一期
        self.at(13.78)
        self.play(FadeOut(VGroup(r1, r2, r3), shift=UP * 0.03), run_time=0.3)
        nec = t("听话，是必要条件，不是充分条件", 30, YELL, "BOLD")
        fit(nec, 0.95)
        nec.next_to(head, DOWN, buff=1.2)
        self.play(FadeIn(nec, scale=1.05), run_time=0.6)
        self.at(17.71)
        rlhf = boxed("下一道工序：RLHF", 4.6, 1.1, CYAN, 30, fill=0.2, weight="BOLD")
        rlhf.next_to(nec, DOWN, buff=1.2)
        self.play(FadeIn(rlhf, shift=DOWN * 0.05), run_time=0.7)

        # 段4（19-37.9s）：品牌尾卡 + 互动
        # 音画同步：台词「关注数解AI」~19-21s、「下一期拆 RLHF」21-27.8s、「最后问你」28.4s-
        self.at(19.19)
        self.play(FadeOut(VGroup(nec, rlhf), shift=UP * 0.03), run_time=0.3)
        logo = ImageMobject("avatar-sjai-round.png")
        logo.scale_to_fit_width(1.6)
        logo.to_edge(UP, buff=2.2)
        self.play(FadeIn(logo, shift=DOWN * 0.05), run_time=0.7)
        self.at(20.17)
        follow = t("关注「数解AI」", 34, YELL, "BOLD").next_to(logo, DOWN, buff=0.3)
        self.play(FadeIn(follow, scale=1.08), run_time=0.6)
        self.at(21.15)
        title = t("《SFT微调：1万条数据就能让模型听话？》", 21, WHITE, "BOLD")
        fit(title, 0.85)
        title.next_to(follow, DOWN, buff=0.4)
        self.play(FadeIn(title, shift=DOWN * 0.05), run_time=0.6)
        self.at(22.14)
        cta1 = boxed("👍 点赞", 2.0, 0.75, YELL, 22, fill=0.15, weight="BOLD")
        cta2 = boxed("➕ 关注", 2.0, 0.75, CYAN, 22, fill=0.15, weight="BOLD")
        cta3 = boxed("💬 评论", 2.0, 0.75, GREEN, 22, fill=0.15, weight="BOLD")
        ctas = VGroup(cta1, cta2, cta3).arrange(RIGHT, buff=0.35).next_to(title, DOWN, buff=0.5)
        fit(ctas, 0.85)
        link = t("查看公众号文章 · 系列合集", 23, GREEN, "BOLD")
        fit(link, 0.85)
        link.next_to(ctas, DOWN, buff=0.5)
        nxt = t("下一期：RLHF，怎么让模型学会说人话", 22, CYAN, "BOLD")
        fit(nxt, 0.85)
        nxt.next_to(link, DOWN, buff=0.6)
        ask = t("预算只够做一件事，你投预训练 / SFT 标注 / RAG？评论区聊聊", 21, MUTED)
        fit(ask, 0.85)
        ask.next_to(nxt, DOWN, buff=0.6)
        self.play(FadeIn(ctas, shift=DOWN * 0.05), FadeIn(link, shift=DOWN * 0.05), run_time=0.8)
        self.at(23.61)
        self.play(FadeIn(nxt, shift=DOWN * 0.05), run_time=0.6)
        self.at(28.04)
        self.play(FadeIn(ask, shift=DOWN * 0.05), run_time=0.6)
        self.pad_to_voice()

# ---------------- 封面帧 ----------------
class Cover(Scene):
    """封面帧：系列标签 + 主/副标题 + 概率分布 + 144万倍数字 + 品牌。
    渲染：python3 -m manim render -qm -s --disable_caching scenes.py Cover
    关键内容须落在 3:4 安全区（frame y ∈ [-5.33, +5.33]），上下 12.5% 只放装饰。
    """
    def construct(self):
        logo = ImageMobject("avatar-sjai-round.png")
        logo.scale_to_fit_width(1.7)
        logo.to_edge(DOWN, buff=2.15)

        series = t("大模型原理 · 第 9 篇", 26, CYAN).to_edge(UP, buff=2.2)
        title = t("SFT微调：1万条数据就能让模型听话？", 38, YELL, "BOLD")
        title.set_width(config.frame_width * 0.82)
        title.next_to(series, DOWN, buff=0.5)
        subtitle = t("预训练贵到独角兽放弃 · 144 万倍的成本差", 28, WHITE)
        fit(subtitle, 0.9)
        subtitle.next_to(title, DOWN, buff=0.45)

        # 概率分布条（base 手掌 vs post 拳头，最有记忆点视觉）
        base_lab = t("base 手掌", 24, WHITE, "BOLD")
        post_lab = t("post 拳头", 24, GREEN, "BOLD")
        base_bars = prob_bars(8, [0.3, 0.5, 0.2, 0.42, 0.28, 0.55, 0.35, 0.45], WHITE)
        post_bars = prob_bars(8, [0.9, 0.15, 0.1, 0.12, 0.1, 0.1, 0.1, 0.1], GREEN)
        base_grp = VGroup(base_lab, base_bars).arrange(DOWN, buff=0.3)
        post_grp = VGroup(post_lab, post_bars).arrange(DOWN, buff=0.3)
        dist = VGroup(base_grp, post_grp).arrange(RIGHT, buff=1.2)
        dist.next_to(subtitle, DOWN, buff=0.9)
        fit(dist, 0.92)

        # 144 万倍数字条
        nums = VGroup(boxed("144 万倍", 3.0, 1.0, YELL, 30, fill=0.2, weight="BOLD"),
                      t("SFT vs 预训练成本", 26, WHITE))
        nums.arrange(RIGHT, buff=0.5).next_to(dist, DOWN, buff=1.0)
        fit(nums, 0.92)

        j1 = t("听话 ≠ 说得好", 30, GREEN, "BOLD")
        j2 = t("下一道工序：RLHF", 30, CYAN, "BOLD")
        js = VGroup(j1, j2).arrange(DOWN, buff=0.4).next_to(nums, DOWN, buff=0.7)

        self.add(logo, series, title, subtitle, dist, nums, js)
