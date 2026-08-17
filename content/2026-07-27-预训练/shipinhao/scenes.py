#!/usr/bin/env python3
"""《预训练：只会猜下一个词，模型怎么学会了写文章？》视频号 Manim 动画（竖屏 1080×1920）

8 个场景 S1-S8 + 封面 Cover，与 storyboard.md 一一对应（2026-08-14）。
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

# 配音时长（tts_split.py 实测 2026-08-14），渲染时长 = 配音 + 缓冲
VOICE_DUR = {"S1": 36.73, "S2": 30.9, "S3": 31.79, "S4": 35.84,
             "S5": 35.5, "S6": 36.17, "S7": 27.99, "S8": 42.01}
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

# ---------------- S1 开场钩子：只猜词，却写文章 ----------------
class S1(_Base):
    def construct(self):
        self.footer()
        head = t("只让它猜下一个词", 38, YELL, "BOLD").to_edge(UP, buff=1.2)
        self.play(FadeIn(head, shift=DOWN * 0.05))

        # 段1（0-9s）：猜词 → 写出文章
        self.at(0.3)
        act = boxed("猜下一个词", 3.6, 1.15, CYAN, 32, fill=0.2, weight="BOLD")
        act.next_to(head, DOWN, buff=1.2)
        self.play(FadeIn(act, shift=DOWN * 0.05), run_time=0.7)
        self.at(3.2)
        res = boxed("写出了像文章的东西", 5.3, 1.15, YELL, 32, fill=0.2, weight="BOLD")
        res.next_to(act, DOWN, buff=1.5)
        ar = Arrow(act.get_bottom() + DOWN * 0.1, res.get_top() + UP * 0.1,
                   color=MUTED, buff=0.1, stroke_width=6)
        self.play(Create(ar), FadeIn(res, shift=DOWN * 0.05), run_time=0.9)

        # 段2（10-18s）：2019 GPT-2 → 今天写代码
        self.at(10.5)
        self.play(FadeOut(VGroup(act, res, ar), shift=UP * 0.03), run_time=0.4)
        gpt = boxed("2019 · GPT-2：15 亿参数", 5.6, 1.1, WHITE, 30, weight="BOLD")
        gpt.next_to(head, DOWN, buff=1.4)
        self.play(FadeIn(gpt, shift=DOWN * 0.05), run_time=0.7)
        self.at(14.0)
        today = boxed("今天：能续写、能写代码", 5.6, 1.1, CYAN, 30, weight="BOLD")
        today.next_to(gpt, DOWN, buff=1.4)
        self.play(FadeIn(today, shift=DOWN * 0.05), run_time=0.7)

        # 段3（18-28s）：凭什么会写文章 + 先给结论（台词「先给结论」~23.5-24.5s）
        # 布局修复（2026-08-14 打磨）：gpt/today 框随段 3 淡出——原保留导致 q2/concl/lines
        # 逐层下堆溢出到 footer（00:19 起显示不下，用户反馈），q2 改挂 head 下方
        self.at(18.5)
        self.play(FadeOut(VGroup(gpt, today), shift=UP * 0.03), run_time=0.3)
        q2 = t("一个只会猜词的系统，凭什么会写文章？", 32, CYAN, "BOLD")
        fit(q2, 0.95)
        q2.next_to(head, DOWN, buff=1.3)
        self.play(FadeIn(q2, shift=DOWN * 0.05), run_time=0.7)
        self.at(25.0)
        concl = boxed("先给结论", 4.0, 0.95, YELL, 32, fill=0.2, weight="BOLD")
        concl.next_to(q2, DOWN, buff=1.2)
        self.play(FadeIn(concl, scale=1.05), run_time=0.6)

        # 段4（28-34s）：把规律压进参数（台词「从没被显式教过」~24.5-27s、「把规律压进去」28-30s）
        self.at(26.2)
        line1 = t("从没被显式教过语法，还是故事", 28, WHITE)
        line2 = t("为了猜得更准，把规律一层层压进参数", 28, WHITE)
        lines = VGroup(line1, line2).arrange(DOWN, buff=0.5).next_to(concl, DOWN, buff=1.0)
        fit(lines, 0.95)
        self.play(FadeIn(lines[0], shift=DOWN * 0.05), run_time=0.6)
        self.at(29.6)
        self.play(FadeIn(lines[1], shift=DOWN * 0.05), run_time=0.6)

        # 段5（34.2-36.7）：但写得像，就是真的懂吗？（台词「猜得准，就能写得像」~31.5-33.5s）
        # 布局修复（2026-08-14 打磨）：gpt/today 框一并淡出——原保留两框导致 squeeze/doubt
        # 挤在框间（00:35 画面混乱，用户反馈未改掉），结尾三行独占画面
        self.at(33.2)
        self.play(FadeOut(VGroup(q2, concl, lines), shift=UP * 0.03), run_time=0.3)
        squeeze = t("猜得准，就能写得像", 34, GREEN, "BOLD").next_to(head, DOWN, buff=1.2)
        squeeze.set_x(0)
        self.play(FadeIn(squeeze, scale=1.05), run_time=0.6)
        self.at(34.6)
        doubt = t("但写得像，就是真的懂吗？", 40, YELL, "BOLD")
        fit(doubt, 0.95)
        doubt.next_to(squeeze, DOWN, buff=1.2)
        self.play(FadeIn(doubt, scale=1.1), run_time=0.7)
        self.at(35.0)
        s1bottom = t("猜得准，写得像——不等于真的懂。", 28, CYAN, "BOLD")
        s1bottom.to_edge(DOWN, buff=3.0)
        self.play(FadeIn(s1bottom, shift=DOWN * 0.05), run_time=0.6)
        self.pad_to_voice()

# ---------------- S2 猜的不是词，是概率分布 ----------------
class S2(_Base):
    def construct(self):
        self.footer()
        head = t("猜的不是词，是概率分布", 38, YELL, "BOLD").to_edge(UP, buff=1.2)
        self.play(FadeIn(head, shift=DOWN * 0.05))

        # 段1（0-14s）：前文 c → 词表候选概率 → one-hot
        self.at(1.2)
        ctx = boxed("前文 c", 2.5, 1.0, CYAN, 30, weight="BOLD").next_to(head, DOWN, buff=1.0)
        self.play(FadeIn(ctx, shift=DOWN * 0.05), run_time=0.6)
        self.at(5.5)
        bars = prob_bars(12, [0.3,0.42,0.28,0.55,0.38,0.48,0.32,0.6,0.35,0.45,0.3,0.4], MUTED)
        bars.next_to(ctx, DOWN, buff=1.0)
        ar = Arrow(ctx.get_bottom(), bars.get_top(), color=MUTED, buff=0.1, stroke_width=5)
        blab = t("词表里每个候选 token 一个概率", 26, WHITE)
        fit(blab, 0.9)
        blab.next_to(bars, DOWN, buff=0.55)   # 标签放条下方，避开箭头
        self.play(Create(ar), FadeIn(bars, shift=DOWN * 0.05), FadeIn(blab, shift=DOWN * 0.05), run_time=0.9)
        self.at(10.5)
        onehot = boxed("正确 1，其余全 0（one-hot）", 5.6, 1.0, GREEN, 28, fill=0.2, weight="BOLD")
        onehot.next_to(bars, DOWN, buff=1.4)
        self.play(FadeIn(onehot, scale=1.05), run_time=0.7)

        # 段2（14-21s）：交叉熵 = -log p + 1%→10%
        self.at(14.5)
        self.play(FadeOut(VGroup(ctx, bars, blab, ar, onehot), shift=UP * 0.03), run_time=0.35)
        ce = t("交叉熵 =  −log q(正确那个词)", 34, YELL, "BOLD")
        fit(ce, 0.95)
        ce.next_to(head, DOWN, buff=1.2)
        self.play(FadeIn(ce, shift=DOWN * 0.05), run_time=0.7)
        self.at(18.2)
        p1 = t("从 1% 提到 10%，损失立刻下降", 30, WHITE)
        fit(p1, 0.95)
        p1.next_to(ce, DOWN, buff=1.0)
        self.play(FadeIn(p1, shift=DOWN * 0.05), run_time=0.6)
        # 概率条 1% → 10%
        self.at(20.0)
        b3 = Rectangle(width=0.7, height=0.5, color=WHITE, fill_color=WHITE, fill_opacity=0.4)
        b10 = Rectangle(width=0.7, height=2.2, color=GREEN, fill_color=GREEN, fill_opacity=0.7)
        grp = VGroup(b3, b10).arrange(RIGHT, buff=1.4).next_to(p1, DOWN, buff=0.8)
        lab3 = t("1%", 24, MUTED).next_to(b3, UP, buff=0.25)
        lab10 = t("10%", 24, GREEN, "BOLD").next_to(b10, UP, buff=0.25)
        self.play(FadeIn(b3, shift=DOWN * 0.05), FadeIn(lab3, shift=DOWN * 0.05), run_time=0.5)
        self.play(GrowFromEdge(b10, DOWN), FadeIn(lab10, shift=DOWN * 0.05), run_time=0.9)

        # 段3（24-28s）：注意——预测准 ≠ 懂
        # 2026-08-14 打磨：画面只留「注意」二字 + 一次 Flash
        self.at(24.5)
        self.play(FadeOut(VGroup(ce, p1, b3, b10, lab3, lab10), shift=UP * 0.03), run_time=0.35)
        but = t("注意", 56, YELL, "BOLD")
        but.next_to(head, DOWN, buff=1.2)
        self.play(FadeIn(but, scale=1.08), run_time=0.45)
        self.play(Flash(but.get_center(), color=YELL, line_length=1.5,
                        num_lines=12, flash_radius=1.7), run_time=0.7)
        self.at(26.5)
        warns = VGroup(t("预测得更准 ≠ 因果正确", 30, WHITE),
                       t("更不等于「知道自己在说什么」", 30, WHITE))
        warns.arrange(DOWN, buff=0.55).next_to(but, DOWN, buff=0.8)
        fit(warns, 0.95)
        self.play(FadeIn(warns, shift=DOWN * 0.05), run_time=0.8)
        self.at(28.0)
        bottom = t("概率分布，不等于懂。", 30, CYAN, "BOLD")
        bottom.to_edge(DOWN, buff=3.2)
        self.play(FadeIn(bottom, shift=DOWN * 0.05), run_time=0.6)
        self.pad_to_voice()

# ---------------- S3 PPL：看趋势的尺子 ----------------
class S3(_Base):
    def construct(self):
        self.footer()
        head = t("怎么读这个下降？", 38, YELL, "BOLD").to_edge(UP, buff=1.2)
        self.play(FadeIn(head, shift=DOWN * 0.05))

        # 段1（0-12s）：PPL 公式 + 困惑度标注 + 规则
        # 2026-08-14 打磨：NLL 必须贴在字母 e 的右上角（拆出 e，按 UR 锚点放上标）
        self.at(0.5)
        ppl_pre = t("PPL = ", 36, YELL, "BOLD")
        e_char = t("e", 40, YELL, "BOLD")
        f1_sup = t("NLL", 20, YELL, "BOLD")
        e_char.next_to(ppl_pre, RIGHT, buff=0.06, aligned_edge=DOWN)
        f1_sup.move_to(e_char.get_corner(UR) + RIGHT * 0.28 + UP * 0.08)
        f1 = VGroup(ppl_pre, e_char, f1_sup)
        f1.next_to(head, DOWN, buff=1.4)
        f1_note = t("PPL 常被译作「困惑度」", 24, MUTED).next_to(f1, DOWN, buff=0.4)
        self.play(FadeIn(f1, shift=DOWN * 0.05), FadeIn(f1_note, shift=DOWN * 0.05), run_time=0.7)
        self.at(4.5)
        f2 = t("NLL = −log p(x)", 32, WHITE, "BOLD")
        fit(f2, 0.9)
        f2.next_to(f1_note, DOWN, buff=0.9)
        f2_note = t("负对数似然", 24, MUTED).next_to(f2, DOWN, buff=0.3)
        self.play(FadeIn(f2, shift=DOWN * 0.05), FadeIn(f2_note, shift=DOWN * 0.05), run_time=0.7)
        self.at(7.5)
        rule = VGroup(t("模型越确定 → PPL 越低", 30, GREEN),
                      t("越意外 → 数字越大", 30, WHITE))
        rule.arrange(DOWN, buff=0.55).next_to(f2_note, DOWN, buff=0.9)
        self.play(FadeIn(rule[0], shift=DOWN * 0.05), run_time=0.6)
        self.at(10.0)
        self.play(FadeIn(rule[1], shift=DOWN * 0.05), run_time=0.6)

        # 段2（12-21s）：换语料/语言/词表不能比 → 不是智力分数
        # 音画同步（2026-08-14 打磨）：红叉节奏对齐台词（12.2「换语料」/13.5「换语言」/15「换词表」/19-20.5「不是智力分数」）
        self.at(12.5)
        self.play(FadeOut(VGroup(f1, f1_note, f2, f2_note, rule), shift=UP * 0.03), run_time=0.3)
        three = VGroup(boxed("换语料", 2.2, 1.0, WHITE, 26),
                       boxed("换语言", 2.2, 1.0, WHITE, 26),
                       boxed("换词表", 2.2, 1.0, WHITE, 26))
        three.arrange(RIGHT, buff=0.4).next_to(head, DOWN, buff=1.5)
        crosses = VGroup()
        for i, b in enumerate(three):
            self.at(12.8 + 1.5 * i)
            self.play(FadeIn(b, shift=DOWN * 0.05), run_time=0.5)
            crosses.add(self.play_red_cross(b))
        self.at(20.0)
        notiq = boxed("不是智力分数", 4.3, 1.0, RED, 32, fill=0.2, weight="BOLD")
        notiq.next_to(three, DOWN, buff=1.3)
        self.play(FadeIn(notiq, scale=1.05), run_time=0.6)

        # 段3（22-32s）：DeepSeek config
        self.at(22.5)
        self.play(FadeOut(VGroup(three, notiq, crosses), shift=UP * 0.03), run_time=0.3)
        cfg = VGroup(boxed("词表 129280", 2.5, 1.1, CYAN, 25, weight="BOLD"),
                     boxed("隐藏 7168", 2.5, 1.1, CYAN, 25, weight="BOLD"),
                     boxed("61 层", 2.0, 1.1, CYAN, 25, weight="BOLD"))
        cfg.arrange(RIGHT, buff=0.25).next_to(head, DOWN, buff=1.2)
        fit(cfg, 0.92)
        head2 = t("2026 · DeepSeek-V4-Pro config", 26, MUTED).next_to(cfg, UP, buff=0.45)
        self.play(FadeIn(head2, shift=DOWN * 0.05), run_time=0.5)
        self.play(FadeIn(cfg, shift=DOWN * 0.05), run_time=0.7)
        self.at(26.5)
        big = t("数字，大得吓人。", 40, YELL, "BOLD").next_to(cfg, DOWN, buff=1.2)
        self.play(FadeIn(big, scale=1.1), run_time=0.5)
        self.at(29.5)
        nope = t("可单凭它，证明不了模型有什么能力", 30, WHITE)
        fit(nope, 0.95)
        nope.next_to(big, DOWN, buff=0.9)
        self.play(FadeIn(nope, shift=DOWN * 0.05), run_time=0.6)
        self.at(30.4)
        bottom = t("参数大，不等于它知道自己在说什么。", 30, RED, "BOLD")
        bottom.to_edge(DOWN, buff=3.2)
        self.play(FadeIn(bottom, shift=DOWN * 0.05), run_time=0.6)
        self.pad_to_voice()

# ---------------- S4 把 4090 的 90 分钟摊开 ----------------
class S4(_Base):
    def construct(self):
        self.footer()
        head = t("数字够吓人，可我不信", 38, YELL, "BOLD").to_edge(UP, buff=1.2)
        self.play(FadeIn(head, shift=DOWN * 0.05))

        # 段1（0-16s）：硬件 + 模型 + 数据
        self.at(3.5)
        hardware = VGroup(boxed("RTX 4090", 2.0, 1.1, WHITE, 26, weight="BOLD"),
                          boxed("8 层", 1.7, 1.1, CYAN, 26, weight="BOLD"),
                          boxed("33M 参数", 1.9, 1.1, GREEN, 26, weight="BOLD"))
        hardware.arrange(RIGHT, buff=0.28).next_to(head, DOWN, buff=1.3)
        fit(hardware, 0.92)
        self.play(FadeIn(hardware, shift=DOWN * 0.05), run_time=0.9)
        self.at(7.5)
        ds = boxed("50 万篇中文短故事", 5.6, 1.0, CYAN, 30, weight="BOLD")
        ds.next_to(hardware, DOWN, buff=1.1)
        self.play(FadeIn(ds, shift=DOWN * 0.05), run_time=0.6)
        self.at(11.5)
        val = boxed("验证集 9989 篇，训练中一篇没见过", 6.4, 1.0, YELL, 28, fill=0.2, weight="BOLD")
        val.next_to(ds, DOWN, buff=0.9)
        self.play(FadeIn(val, scale=1.05), run_time=0.7)
        # 2026-08-14 打磨：RTX 4090 性价比小字说明（用户要求 01:56 附近）
        self.at(14.5)
        gpu_note = t("RTX 4090：性价比极高的常见 Nvidia 显卡，适合小实验", 22, MUTED)
        fit(gpu_note, 0.9)
        gpu_note.next_to(val, DOWN, buff=0.8)
        self.play(FadeIn(gpu_note, shift=DOWN * 0.05), run_time=0.6)

        # 段2（16-25s）：PPL 柱状图 + 趋势线（带 X 轴时间刻度 + 轴箭头）
        # 2026-08-14 打磨：head 换「小模型实验实测：童话故事续写」（用户要求 01:50 起页面标题）
        self.at(16.5)
        self.play(FadeOut(VGroup(hardware, ds, val, gpu_note, head), shift=UP * 0.03), run_time=0.3)
        head2 = t("小模型实验实测：童话故事续写", 34, YELL, "BOLD").to_edge(UP, buff=1.2)
        fit(head2, 0.95)
        self.play(FadeIn(head2, shift=DOWN * 0.05), run_time=0.5)
        sub = t("90 分钟 · 24112 步 · PPL 走势", 28, WHITE, "BOLD").next_to(head2, DOWN, buff=1.0)
        self.play(FadeIn(sub, shift=DOWN * 0.05), run_time=0.5)
        specs = [("18.6 分", 103.9), ("60 分", 60.54), ("74.5 分", 54.82), ("90 分", 50.73)]

        # 坐标系：原点在左下，X 轴→右（时间），Y 轴→上（PPL）
        ORIG = np.array([0, 0, 0])
        XLEN, YLEN = 5.6, 3.3
        x_axis = Arrow(ORIG, RIGHT*XLEN, color=MUTED, stroke_width=3, buff=0, max_tip_length_to_length_ratio=0.08)
        y_axis = Arrow(ORIG, UP*YLEN, color=MUTED, stroke_width=3, buff=0, max_tip_length_to_length_ratio=0.08)
        axes = VGroup(x_axis, y_axis)
        axes.next_to(sub, DOWN, buff=0.9)
        axes.move_to(np.array([-2.6 + XLEN/2, axes.get_center()[1], 0]))   # 左缘 x≈-2.6，留出 y 刻度空间
        origin = x_axis.get_start()   # 图表原点 = X 轴起点（真左下角）
        # 轴名（2026-08-14 打磨：原在 move_to 前定义，xlab 落在画布外、ylab 不随轴 → 移到 origin 确定后）
        xlab = t("训练时间", 18, MUTED).next_to(np.array([origin[0] + XLEN/2, origin[1], 0]), DOWN, buff=0.3)
        ylab = t("PPL", 18, MUTED).next_to(y_axis.get_end(), RIGHT, buff=0.15)
        # X 轴四个刻度标签（时间点）——柱 1 与 Y 轴间隔 0.4、柱 4 不贴箭头（2026-08-14 打磨）
        bar_w, x0, spacing = 0.7, origin[0] + 0.4, (XLEN - 0.8) / 3
        x_tick_labs = VGroup()
        for i,(mins,_) in enumerate(specs):
            bx = x0 + spacing*i
            lab = t(mins, 18, MUTED).next_to(np.array([bx, origin[1], 0]), DOWN, buff=0.15)
            x_tick_labs.add(lab)
        # Y 轴刻度标签
        y_tick_labs = VGroup()
        for yy,ltxt in [(0,"0"),(40,"40"),(80,"80"),(120,"120")]:
            lab = t(ltxt, 16, MUTED).next_to(np.array([origin[0]-0.1, origin[1]+yy/120*YLEN, 0]), LEFT, buff=0.15)
            y_tick_labs.add(lab)
        # 四根柱（基线 = origin y = X 轴，柱向上生长）
        bars = VGroup(); bar_labels = VGroup()
        for i,(mins,pval) in enumerate(specs):
            bx = x0 + spacing*i
            bh = pval/120 * YLEN
            rec = Rectangle(width=bar_w, height=bh, color=CYAN, fill_color=CYAN, fill_opacity=0.5)
            rec.move_to(np.array([bx, origin[1] + 0.08 + bh/2, 0]))
            bars.add(rec)
            vlab = t(f"{pval}", 20, YELL if i==len(specs)-1 else WHITE, "BOLD")
            vlab.next_to(rec.get_top(), UP, buff=0.1)
            if i == 0:   # 柱 1 标签右移，避开 Y 轴「120」刻度（2026-08-14 打磨）
                vlab.shift(RIGHT * 0.45)
            bar_labels.add(vlab)
        self.play(FadeIn(axes, shift=DOWN*0.05), FadeIn(xlab, shift=DOWN*0.05),
                  FadeIn(ylab, shift=DOWN*0.05), run_time=0.6)
        self.play(FadeIn(x_tick_labs, shift=DOWN*0.05), FadeIn(y_tick_labs, shift=DOWN*0.05), run_time=0.5)
        # 柱逐根生长
        for i,rec in enumerate(bars):
            self.at(18.5 + 1.7*i)
            self.play(GrowFromEdge(rec, DOWN), run_time=0.7)
            self.play(FadeIn(bar_labels[i], shift=DOWN*0.05), run_time=0.35)
        # 趋势线：弧线拟合 4 根柱顶（2026-08-14 打磨：原直线连接首尾柱顶 → 平滑弧线过全部柱顶）
        self.at(25.3)
        top_pts = [bars[i].get_top() for i in range(4)]
        trend = VMobject().set_points_smoothly(top_pts).set_stroke(RED, 5)
        tlab = t("PPL 一路下降", 26, GREEN, "BOLD").next_to(trend, UP, buff=0.35)
        tlab.align_to(trend, LEFT)
        self.play(Create(trend), FadeIn(tlab, shift=DOWN*0.05), run_time=0.9)
        group_chart = VGroup(axes, xlab, ylab, x_tick_labs, y_tick_labs, bars, bar_labels, trend, tlab)

        # 段3（25-36s）：关键点——没背过（台词 25.49「关键：这些故事，它一篇都没背过」）
        self.at(26.3)
        self.play(FadeOut(VGroup(sub, group_chart), shift=UP*0.03), run_time=0.35)
        key = t("关键点：这些故事，它一篇都没背过。", 34, YELL, "BOLD")
        fit(key, 0.95)
        key.next_to(head, DOWN, buff=0.9)
        self.play(FadeIn(key, scale=1.05), run_time=0.7)
        self.at(32.5)
        concl = t("只背原文，遇到新故事早该崩了。", 30, WHITE)
        fit(concl, 0.95)
        concl.next_to(key, DOWN, buff=1.1)
        self.play(FadeIn(concl, shift=DOWN * 0.05), run_time=0.6)
        self.at(34.5)
        notc = t("没崩！", 56, GREEN, "BOLD")
        notc.next_to(concl, DOWN, buff=1.2)
        bottom = t("它在没见过的故事上，也「猜得更准」了。", 28, CYAN, "BOLD")
        bottom.to_edge(DOWN, buff=3.2)
        self.play(FadeIn(notc, scale=1.12), FadeIn(bottom, shift=DOWN * 0.05), run_time=0.4)
        self.play(notc.animate.set_opacity(0.15), run_time=0.15)
        self.play(notc.animate.set_opacity(1), run_time=0.15)
        self.play(notc.animate.set_opacity(0.15), run_time=0.15)
        self.play(notc.animate.set_opacity(1), run_time=0.15)
        self.pad_to_voice()

# ---------------- S5 四个 checkpoint，四次续写 ----------------
class S5(_Base):
    def construct(self):
        self.footer()
        head = t("同一个前缀，四次续写", 38, YELL, "BOLD").to_edge(UP, buff=1.2)
        self.play(FadeIn(head, shift=DOWN * 0.05))
        prefix = boxed("前缀：从前有个叫 Lily 的小女孩", 6.6, 1.0, CYAN, 28, weight="BOLD")
        prefix.next_to(head, DOWN, buff=0.9)
        self.play(FadeIn(prefix, shift=DOWN * 0.05), run_time=0.7)

        # 段1（1.5-15s）：三个 checkpoint 续写（错开，避免重叠）
        self.at(4.5)
        st0 = boxed("step 0：一堆乱码", 4.4, 1.0, MUTED, 26)
        st0.next_to(prefix, DOWN, buff=1.2)
        self.play(FadeIn(st0, shift=DOWN * 0.05), run_time=0.6)
        self.at(8.3)
        st5 = boxed("step 5000：复读机", 4.4, 1.0, WHITE, 26)
        st5.next_to(st0, DOWN, buff=1.2)
        rep = t("（重复、重复、再重复）", 24, MUTED).next_to(st5, DOWN, buff=0.5)
        self.play(FadeIn(st5, shift=DOWN * 0.05), FadeIn(rep, shift=DOWN * 0.05), run_time=0.7)
        self.at(11.0)
        st24 = boxed("step 24000：冒出「寓意」", 5.4, 1.15, YELL, 27, fill=0.2, weight="BOLD")
        st24.next_to(rep, DOWN, buff=1.2)
        self.play(FadeIn(st24, scale=1.05), run_time=0.7)
        self.at(14.0)
        moral = t("「这个故事的寓意是：朋友」", 30, GREEN, "BOLD")
        fit(moral, 0.95)
        moral.next_to(st24, DOWN, buff=1.0)
        self.play(FadeIn(moral, scale=1.05), run_time=0.6)

        # 段2（15.5-24s）：局部变好（红叉）+ 写不出稳定故事（分两行，拉开不重叠）
        # 音画同步（2026-08-14 打磨）：台词 15.49「局部结构，确实在变好」→ 15.8 切换
        # 布局修复（2026-08-14 打磨）：better 原 next_to(head, DOWN, buff=1.2) 与 prefix 框
        # （head 下方 0.9-1.9）重叠 → 改挂到 prefix 框下方
        self.at(15.8)
        self.play(FadeOut(VGroup(st0, st5, rep, st24, moral), shift=UP * 0.03), run_time=0.3)
        better = t("局部结构，确实在变好。", 32, GREEN, "BOLD")
        better.next_to(prefix, DOWN, buff=1.0)
        better.set_x(0)
        self.play(FadeIn(better, shift=DOWN * 0.05), run_time=0.6)
        self.at(18.5)
        cr = self.play_red_cross(better)
        self.at(20.5)
        limit1 = t("可直到训练结束，也写不出", 30, WHITE)
        limit2 = t("人物一致、有因果的故事", 30, WHITE)
        limit = VGroup(limit1, limit2).arrange(DOWN, buff=0.15)
        limit.next_to(better, DOWN, buff=2.6)
        limit.set_x(0)
        self.play(FadeIn(limit, shift=DOWN * 0.05), run_time=0.7)

        # 段3（24-35.5s）：曲线直觉 vs 输出（干净居中下滑曲线）
        # 2026-08-14 打磨：FadeOut 组补入 prefix——原漏掉导致前缀框残留到曲线页（02:43 遮挡，用户反馈）
        self.at(24.5)
        self.play(FadeOut(VGroup(better, limit, cr, prefix), shift=UP * 0.03), run_time=0.3)
        curve = t("光看曲线：104 → 50，好像「稳步变好」", 28, WHITE, "BOLD")
        fit(curve, 0.95)
        curve.next_to(head, DOWN, buff=1.0)
        self.play(FadeIn(curve, shift=DOWN * 0.05), run_time=0.6)
        # 手绘坐标轴（带箭头）：X=时间，Y=PPL；chart 左下贴 x=-3.2，右端至 +2.4（安全期内）
        XLEN, YLEN = 5.6, 3.0
        x_axis = Arrow(ORIGIN, RIGHT*XLEN, color=MUTED, stroke_width=3, buff=0, max_tip_length_to_length_ratio=0.06)
        y_axis = Arrow(ORIGIN, UP*YLEN, color=MUTED, stroke_width=3, buff=0, max_tip_length_to_length_ratio=0.06)
        chart = VGroup(x_axis, y_axis)
        chart.next_to(curve, DOWN, buff=0.8)
        chart.move_to(np.array([-3.2 + XLEN/2, chart.get_center()[1], 0]))
        origin = x_axis.get_start()   # 图表原点 = X 轴起点（x≈-3.2）
        # 平滑指数下滑曲线（104→50）
        xs = np.linspace(0, 10, 20)
        ys = 45 + 62*np.exp(-0.28*xs)
        pts = [origin + RIGHT*(x/10)*XLEN + UP*(ys[i]/107)*YLEN for i,x in enumerate(xs)]
        downc = VMobject().set_points_smoothly(pts).set_stroke(CYAN, 6)
        # 起点=104（高），终点=50（低）
        s_dot = Dot(origin + UP*YLEN, color=WHITE, radius=0.09)
        e_dot = Dot(origin + RIGHT*XLEN, color=YELL, radius=0.11)
        s_lab = t("104", 22, WHITE, "BOLD").next_to(s_dot, UP, buff=0.2)
        e_lab = t("50", 22, YELL, "BOLD").next_to(e_dot, RIGHT, buff=0.2)
        tl = t("PPL", 18, MUTED).next_to(chart.get_top(), RIGHT, buff=0.2)
        self.play(FadeIn(chart, shift=DOWN*0.05), run_time=0.5)
        self.play(Create(downc), run_time=1.2)
        self.play(FadeIn(s_dot), FadeIn(e_dot), FadeIn(s_lab), FadeIn(e_lab), FadeIn(tl), run_time=0.5)
        # 下方结论（错开曲线，居中）
        self.at(31.5)
        switch = t("可把输出摊开？", 32, YELL, "BOLD")
        fit(switch, 0.8)
        switch.next_to(chart, DOWN, buff=1.0)
        switch.set_x(0)
        self.play(FadeIn(switch, scale=1.05), run_time=0.5)
        self.at(33.5)
        punch = t("预测更准，不等于输出更好", 34, WHITE, "BOLD")
        fit(punch, 0.8)
        punch.next_to(switch, DOWN, buff=0.7)
        punch.set_x(0)
        self.play(FadeIn(punch, shift=DOWN * 0.05), run_time=0.6)
        self.pad_to_voice()

# ---------------- S6 三层证据 + 随机鹦鹉 ----------------
class S6(_Base):
    def construct(self):
        self.footer()
        head = t("放回证据框架，就三层", 38, YELL, "BOLD").to_edge(UP, buff=1.2)
        self.play(FadeIn(head, shift=DOWN * 0.05))
        # 固定左边缘（贴画布左留 0.35），三层统一左对齐
        LV = -config.frame_width/2 + 0.35
        # 段1（0-19s）：三层等宽，从左缘向右缓慢卷轴摊开
        BOX_W = 6.9
        self.at(2.5)
        l1 = boxed("一 · 训练损失下降：更会拟合见过的序列", BOX_W, 1.05, GREEN, 26, fill=0.2)
        l1.next_to(head, DOWN, buff=1.3)
        l1.align_to(np.array([LV, 0, 0]), LEFT)
        self.play_scroll_unroll(l1, run_time=1.5)

        self.at(9.0)
        l2 = boxed("二 · 未见验证集 PPL 也降：有了可迁移结构", BOX_W, 1.05, GREEN, 26, fill=0.2)
        l2.next_to(l1, DOWN, buff=0.7)
        l2.align_to(np.array([LV, 0, 0]), LEFT)
        self.play_scroll_unroll(l2, run_time=1.5)

        self.at(13.5)
        l3 = boxed("三 · 理解/因果/体验：要额外证据", BOX_W, 1.05, MUTED, 26)
        l3.next_to(l2, DOWN, buff=0.7)
        l3.align_to(np.array([LV, 0, 0]), LEFT)
        self.play_scroll_unroll(l3, run_time=1.5)

        # 段2（19-24.5s）：前两层值钱
        self.at(21.5)
        front = t("前两层，已经很值钱。", 34, GREEN, "BOLD")
        front.next_to(l3, DOWN, buff=1.3, aligned_edge=LEFT)
        self.play(FadeIn(front, scale=1.05), run_time=0.6)
        self.at(23.0)
        nwm = boxed("「抽取规律」≠ 拥有世界模型", 5.6, 1.1, RED, 30, fill=0.15, weight="BOLD")
        nwm.next_to(front, DOWN, buff=1.0, aligned_edge=LEFT)
        self.play(FadeIn(nwm, scale=1.05), run_time=0.6)

        # 段3（24.5-36s）：随机鹦鹉
        self.at(25.5)
        self.play(FadeOut(VGroup(l1, l2, l3, front, nwm), shift=UP * 0.03), run_time=0.3)
        view = t("语言行为像人，不代表能看见第一人称视角", 28, WHITE)
        fit(view, 0.95)
        view.next_to(head, DOWN, buff=1.3)
        self.play(FadeIn(view, shift=DOWN * 0.05), run_time=0.6)
        self.at(28.5)
        parrot = boxed("随机鹦鹉", 3.4, 1.1, YELL, 34, fill=0.2, weight="BOLD")
        parrot.next_to(view, DOWN, buff=1.0)
        self.play(FadeIn(parrot, scale=1.1), run_time=0.7)
        self.at(32.0)
        remind = t("复现语言模式，不等于理解自己在说什么", 30, WHITE)
        fit(remind, 0.95)
        remind.next_to(parrot, DOWN, buff=1.0)
        self.play(FadeIn(remind, shift=DOWN * 0.05), run_time=0.6)
        self.at(34.0)
        bottom = t("像人说话 ≠ 有人格。", 34, YELL, "BOLD")
        bottom.to_edge(DOWN, buff=3.2)
        self.play(FadeIn(bottom, shift=DOWN * 0.05), run_time=0.6)
        self.pad_to_voice()

# ---------------- S7 涌现收窄 + 像≠理解 ----------------
class S7(_Base):
    def construct(self):
        self.footer()
        head = t("「涌现」要说得更窄", 38, YELL, "BOLD").to_edge(UP, buff=1.2)
        self.play(FadeIn(head, shift=DOWN * 0.05))

        # 段1（0-11s）：涌现定义 + 无跃迁（台词 0s 起说「尺度变化后的非线性提升」→ 1.8 显示）
        self.at(1.8)
        defi = t("尺度变化后的非线性提升", 30, WHITE).next_to(head, DOWN, buff=1.4)
        self.play(FadeIn(defi, shift=DOWN * 0.05), run_time=0.6)
        self.at(5.0)
        nojump = t("可这 90 分钟，我没看到神秘跃迁", 32, WHITE, "BOLD").next_to(defi, DOWN, buff=1.2)
        self.play(FadeIn(nojump, shift=DOWN * 0.05), run_time=0.6)
        self.at(7.5)
        ax = Axes(x_range=[0, 6, 1], y_range=[0, 1, 0.5], x_length=6.2, y_length=2.4,
                  x_axis_config={"include_numbers": False},
                  y_axis_config={"include_numbers": False},
                  axis_config={"stroke_width": 1.4}).set_stroke(MUTED, 1.4)
        ax.next_to(nojump, DOWN, buff=0.8)
        grad = ax.plot(lambda x: 0.95 - 0.14*x + 0.015*np.sin(4*x),
                       color=CYAN, stroke_width=5)
        self.play(Create(ax), run_time=0.4)
        self.play(Create(grad), run_time=1.0)

        # 段2（11-18s）：只有局部渐进，无相变证据
        self.at(12.0)
        self.play(FadeOut(VGroup(defi, nojump, ax, grad), shift=UP * 0.03), run_time=0.3)
        accurate = t("说得最准：只有局部的、渐进的能力变化", 30, WHITE, "BOLD")
        fit(accurate, 0.95)
        accurate.next_to(head, DOWN, buff=1.4)
        self.play(FadeIn(accurate, shift=DOWN * 0.05), run_time=0.6)
        self.at(14.5)
        nophase = boxed("没有相变的证据", 4.4, 1.1, RED, 32, fill=0.18, weight="BOLD")
        nophase.next_to(accurate, DOWN, buff=1.2)
        self.play(FadeIn(nophase, scale=1.05), run_time=0.6)

        # 段3（18-28s）：对仗金句 + 补充说明（不改音轨）
        self.at(19.0)
        self.play(FadeOut(VGroup(accurate, nophase), shift=UP * 0.03), run_time=0.3)
        j1 = t("会预测，不等于会解释", 40, YELL, "BOLD")
        j2 = t("会模仿，不等于有体验", 40, YELL, "BOLD")
        js = VGroup(j1, j2).arrange(DOWN, buff=0.6).next_to(head, DOWN, buff=1.2)
        fit(js, 0.95)
        self.play(FadeIn(js[0], scale=1.05), run_time=0.6)
        self.at(21.5)
        self.play(FadeIn(js[1], scale=1.05), run_time=0.6)
        self.at(24.0)
        # 补充说明：仅本次小模型实验；原始涌现来自更大模型实验（屏幕文字，无音频）
        note_box = VGroup(
            Rectangle(width=7.2, height=1.5, color=YELL, fill_color=YELL, fill_opacity=0.08),
        )
        note_txt = VGroup(
            t("补充：本次为小模型实验，未观察到涌现", 25, WHITE),
            t("原始「涌现」现象，来自更大规模模型实验", 25, WHITE,),
        )
        note_txt.arrange(DOWN, buff=0.35)
        note_txt.move_to(note_box)
        note_grp = VGroup(note_box, note_txt)
        note_grp.next_to(js, DOWN, buff=1.4)
        s7bottom = t("涌现是能力变化，不是意识证据。", 30, GREEN, "BOLD")
        s7bottom.to_edge(DOWN, buff=3.2)
        self.play(FadeIn(note_grp, scale=0.95), FadeIn(s7bottom, shift=DOWN * 0.05), run_time=0.8)
        self.wait(2.0)   # 停留 2s 供观众阅读（不改音轨，纯画面延长由 pad 承接）
        self.pad_to_voice()

# ---------------- S8 预训练之后 + 品牌尾卡 ----------------
class S8(_Base):
    def construct(self):
        self.footer()
        head = t("预训练之后", 38, YELL, "BOLD").to_edge(UP, buff=1.2)
        self.play(FadeIn(head, shift=DOWN * 0.05))

        # 页1（0-10s）：条件概率模型
        self.at(1.5)
        cm = boxed("条件概率模型：给定上文，往下写", 6.6, 1.2, CYAN, 28, fill=0.2, weight="BOLD")
        cm.next_to(head, DOWN, buff=1.1)
        self.play(FadeIn(cm, scale=1.05), run_time=0.7)
        self.at(7.0)
        notgoal = boxed("不会天然「帮人、守边界」", 5.4, 1.0, RED, 28, fill=0.15)
        notgoal.next_to(cm, DOWN, buff=1.2)
        self.play(FadeIn(notgoal, shift=DOWN * 0.05), run_time=0.6)

        # 页2（10-21s）：后训练 → 更可靠助手
        self.at(12.5)
        self.play(FadeOut(VGroup(cm, notgoal), shift=UP * 0.03), run_time=0.3)
        post = boxed("后训练 · 指令微调", 4.6, 1.1, YELL, 30, fill=0.2, weight="BOLD")
        post.next_to(head, DOWN, buff=1.3)
        self.play(FadeIn(post, shift=DOWN * 0.05), run_time=0.7)
        self.at(17.0)
        helper = boxed("更可靠的助手", 4.2, 1.1, GREEN, 32, fill=0.2, weight="BOLD")
        helper.next_to(post, DOWN, buff=1.5)
        ar1 = Arrow(post.get_bottom(), helper.get_top(), color=GREEN,
                    buff=0.1, stroke_width=6)
        self.play(Create(ar1), FadeIn(helper, shift=DOWN * 0.05), run_time=0.7)
        self.at(19.5)
        nosense = boxed("更好用，可不是「补上意识」", 6.2, 1.1, RED, 28, weight="BOLD")
        nosense.next_to(helper, DOWN, buff=1.2)
        self.play(FadeIn(nosense, scale=1.05), run_time=0.6)

        # 页3（21-27s）：金句收束（台词 18.16「可不是补上意识…会预测…会模仿」）
        self.at(21.0)
        self.play(FadeOut(VGroup(post, helper, ar1, nosense), shift=UP * 0.03), run_time=0.3)
        j1 = t("会预测，不等于会解释", 40, YELL, "BOLD")
        j2 = t("会模仿，不等于有体验", 40, YELL, "BOLD")
        js = VGroup(j1, j2).arrange(DOWN, buff=0.6).next_to(head, DOWN, buff=1.3)
        fit(js, 0.95)
        self.play(FadeIn(js[0], scale=1.05), run_time=0.6)
        self.at(22.8)
        self.play(FadeIn(js[1], scale=1.05), run_time=0.6)

        # 页4（25-42s）：品牌尾卡 + 点赞/关注/评论 CTA
        # 音画同步（2026-08-14 打磨）：台词「关注数解AI」~24.5-26.5、「下一期」27.0-33.7、「最后问你」33.7-
        # 原节点滞后 4-8s（关注 29.0/预告 35.0/提问 38.5），全部前移至台词对应时刻
        self.at(25.2)
        self.play(FadeOut(VGroup(js), shift=UP * 0.03), run_time=0.3)
        logo = ImageMobject("avatar-sjai-round.png")
        logo.scale_to_fit_width(2.0)
        logo.to_edge(UP, buff=2.6)
        self.play(FadeIn(logo, shift=DOWN * 0.05), run_time=0.7)
        self.at(26.6)
        follow = t("关注「数解AI」", 36, YELL, "BOLD").next_to(logo, DOWN, buff=0.4)
        self.play(FadeIn(follow, scale=1.08), run_time=0.6)
        self.at(28.0)
        title = t("《预训练：只会猜下一个词，模型怎么学会了写文章？》", 22, WHITE, "BOLD")
        fit(title, 0.85)
        title.next_to(follow, DOWN, buff=0.5)
        self.play(FadeIn(title, shift=DOWN * 0.05), run_time=0.6)
        self.at(29.6)
        cta1 = boxed("👍 点赞", 2.1, 0.8, YELL, 23, fill=0.15, weight="BOLD")
        cta2 = boxed("➕ 关注", 2.1, 0.8, CYAN, 23, fill=0.15, weight="BOLD")
        cta3 = boxed("💬 评论", 2.1, 0.8, GREEN, 23, fill=0.15, weight="BOLD")
        ctas = VGroup(cta1, cta2, cta3).arrange(RIGHT, buff=0.4).next_to(title, DOWN, buff=0.6)
        fit(ctas, 0.85)
        link = t("查看公众号文章 · 系列合集", 24, GREEN, "BOLD")
        fit(link, 0.85)
        link.next_to(ctas, DOWN, buff=0.7)
        nxt = t("下一期：1 万条数据，怎么让模型听话", 23, CYAN, "BOLD")
        fit(nxt, 0.85)
        nxt.next_to(link, DOWN, buff=1.0)
        ask = t("长期稳定解释理由，算「理解」吗？评论区聊聊", 22, MUTED)
        fit(ask, 0.85)
        ask.next_to(nxt, DOWN, buff=0.8)
        self.play(FadeIn(ctas, shift=DOWN * 0.05), FadeIn(link, shift=DOWN * 0.05), run_time=0.8)
        self.at(31.6)
        self.play(FadeIn(nxt, shift=DOWN * 0.05), run_time=0.6)
        self.at(34.4)
        self.play(FadeIn(ask, shift=DOWN * 0.05), run_time=0.6)
        self.pad_to_voice()

# ---------------- 封面帧 ----------------
class Cover(Scene):
    """封面帧：系列标签 + 主/副标题 + 概率分布 + PPL 数字 + 品牌。
    渲染：python3 -m manim render -qm -s --disable_caching scenes.py Cover
    关键内容须落在 3:4 安全区（frame y ∈ [-5.33, +5.33]），上下 12.5% 只放装饰。
    """
    def construct(self):
        logo = ImageMobject("avatar-sjai-round.png")
        logo.scale_to_fit_width(1.7)
        logo.to_edge(DOWN, buff=2.15)

        series = t("大模型原理 · 第 8 篇", 26, CYAN).to_edge(UP, buff=2.2)
        title = t("预训练：只会猜下一个词，模型怎么学会了写文章？", 38, YELL, "BOLD")
        title.set_width(config.frame_width * 0.82)
        title.next_to(series, DOWN, buff=0.5)
        subtitle = t("猜的不是词，是概率分布 · 4090 上 90 分钟的真相", 28, WHITE)
        fit(subtitle, 0.9)
        subtitle.next_to(title, DOWN, buff=0.45)

        # 概率分布条（最有记忆点视觉）
        bars = prob_bars(12, [0.3,0.42,0.28,0.55,0.38,0.48,0.32,0.6,0.35,0.45,0.3,0.4], CYAN)
        bars.next_to(subtitle, DOWN, buff=1.0)
        # PPL 数字条
        nums = VGroup(boxed("103.9 → 50.73", 3.3, 1.0, YELL, 28, fill=0.2, weight="BOLD"),
                      t("90 分钟 RTX 4090 实测", 26, WHITE))
        nums.arrange(RIGHT, buff=0.5).next_to(bars, DOWN, buff=1.1)
        fit(nums, 0.92)

        j1 = t("会预测 ≠ 会解释", 30, GREEN, "BOLD")
        j2 = t("会模仿 ≠ 有体验", 30, GREEN, "BOLD")
        js = VGroup(j1, j2).arrange(DOWN, buff=0.4).next_to(nums, DOWN, buff=0.7)

        self.add(logo, series, title, subtitle, bars, nums, js)
        # （2026-08-14 打磨：删除误粘贴的 S8 尾卡动画代码——Cover 继承 Scene 无 at()/pad_to_voice()，
        #   保留会 AttributeError；封面为单帧静态布局，self.add 即完成。）

