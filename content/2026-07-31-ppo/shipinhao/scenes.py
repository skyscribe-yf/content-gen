#!/usr/bin/env python3
"""《PPO：被顶会拒稿，怎么成了RLHF发动机？》视频号 Manim 动画（竖屏 1080×1920）

9 个场景 S1-S9（S9 = 关注引导 CTA，2026-08-15 补录），与 storyboard.md 一一对应。
通用工具在 scripts/manim_helpers.py；本文件只放 VOICE_DUR / TAIL / 场景类。
时间轴锚点 = tts/sentence-boundaries.json 句级边界（口播实测，禁止按预估排布）。
渲染：
  python3 -m manim render -ql --disable_caching scenes.py S1 S2 S3 S4 S5 S6 S7 S8 S9
  python3 -m manim render -qm --disable_caching scenes.py S1 S2 S3 S4 S5 S6 S7 S8 S9
构建：python3 scripts/manim_video_build.py content/2026-07-31-ppo/shipinhao
"""
from __future__ import annotations

import pathlib
import sys


def _scripts_dir() -> str:
    """向上查找项目 scripts/ 目录（含 manim_helpers.py），不依赖场景文件深度。"""
    p = pathlib.Path(__file__).resolve().parent
    for _ in range(6):
        cand = p / "scripts"
        if (cand / "manim_helpers.py").exists():
            return str(cand)
        p = p.parent
    raise RuntimeError("找不到 scripts/manim_helpers.py")


sys.path.insert(0, _scripts_dir())
from manim_helpers import *

config.background_color = "#0F1A30"

# 口播实测时长（ffprobe tts/sN.wav，勿改）
VOICE_DUR = {"S1": 20.088, "S2": 34.777, "S3": 30.522, "S4": 25.679,
             "S5": 28.549, "S6": 23.473, "S7": 29.800, "S8": 29.028,
             "S9": 14.511}
TAIL = 2.5  # 渲染缓冲（build 会截到 0.1s）


# ---------------- S1 开场钩子：扔掉 Critic → 请回来 → 拒稿 → 三道机关 ----------------
class S1(_Base):
    def construct(self):
        self.bg()
        self.footer()
        head = t("PPO 凭什么翻红？", 38, YELL, "BOLD").to_edge(UP, buff=1.2)
        self.play(type_in(head, run_time=1.1))
        hint = t("本片以 GLM-5.2 为例", 20, MUTED).to_corner(UL, buff=0.6)
        self.play(type_in(hint, run_time=0.5))

        # 段1（0-6.37）：扔掉 Critic / 请回来 / 时间
        self.at(1.0)
        toss = _card("所有人都在扔掉 Critic", 5.6, 1.1, RED, WHITE, 27, CARD_FILL2, "BOLD")
        toss.next_to(head, DOWN, buff=1.6)
        self.play_scroll_unroll(toss, run_time=1.3)
        self.at(2.57)
        bring = _card("智谱却把它请了回来", 5.6, 1.1, GREEN, WHITE, 27, CARD_FILL2, "BOLD")
        bring.next_to(toss, DOWN, buff=1.1)
        self.play_scroll_unroll(bring, run_time=1.3)
        self.at(4.64)
        when = t("2026 年 6 月", 26, CYAN).next_to(bring, DOWN, buff=1.7)
        self.play(type_in(when, run_time=0.5))

        # 段2（6.37-10.68）：GLM-5.2 切回 PPO
        self.at(6.37)
        self.play(FadeOut(VGroup(toss, bring, when), shift=UP * 0.03), run_time=0.3)
        switch = t("GLM-5.2 悄悄切回了 PPO", 40, YELL, "BOLD")
        fit(switch, 0.95)
        switch.next_to(head, DOWN, buff=1.5)
        self.play(type_in(switch, run_time=1.1))

        # 段3（10.68-14.24）：被 NIPS 2017 拒稿 → 红章
        self.at(10.68)
        rej = t("一个被 NIPS 2017 拒稿的算法", 28, WHITE)
        fit(rej, 0.95)
        rej.next_to(switch, DOWN, buff=1.3)
        self.play(type_in(rej, run_time=0.9))
        stamp = VGroup(Circle(radius=1.25, color=RED, stroke_width=6),
                       t("拒稿", 40, RED, "BOLD"))
        stamp.next_to(rej, DOWN, buff=1.0)
        self.at(12.3)
        self.play(GrowFromCenter(stamp[0]), FadeIn(stamp[1], scale=1.3), run_time=0.7)

        # 段4（14.24-17.10）：凭什么成了 RLHF 的发动机
        self.at(14.24)
        self.play(FadeOut(VGroup(switch, rej, stamp), shift=UP * 0.03), run_time=0.3)
        q = t("凭什么成了 RLHF 的发动机？", 34, YELL, "BOLD")
        fit(q, 0.95)
        q.next_to(head, DOWN, buff=1.9)
        self.play(type_in(q, run_time=1.1))

        # 段5（17.10-20.09）：三道机关预告
        self.at(17.10)
        chips = VGroup(boxed("① Clip", 2.2, 1.1, CYAN, 26, fill=0.15, weight="BOLD"),
                       boxed("② Critic", 2.2, 1.1, GREEN, 26, fill=0.15, weight="BOLD"),
                       boxed("③ KL", 2.2, 1.1, MUTED, 26, fill=0.15, weight="BOLD"))
        chips.arrange(RIGHT, buff=0.5).next_to(q, DOWN, buff=1.5)
        cap = t("三道机关，给你讲透", 26, WHITE).next_to(chips, DOWN, buff=1.4)
        self.play(FadeIn(chips, shift=DOWN * 0.05), run_time=0.5)
        self.play(type_in(cap, run_time=0.8))
        self.pad_to_voice()


# ---------------- S2 前世今生：天平 → TRPO → 二阶导数 → clip → 拒稿 ----------------
class S2(_Base):
    def construct(self):
        self.bg()
        self.footer()
        head = t("策略更新：难在平衡", 38, YELL, "BOLD").to_edge(UP, buff=1.2)
        self.play(type_in(head, run_time=1.1))

        # 段1（0-3.35）：核心矛盾
        self.at(0.6)
        core = t("PPO 要解决强化学习的核心矛盾", 28, WHITE)
        fit(core, 0.95)
        core.next_to(head, DOWN, buff=0.9)
        self.play(type_in(core, run_time=0.9))

        # 段2（3.35-6.14）：天平：太猛崩 / 太慢学不动
        self.at(3.35)
        pivot = np.array([0.0, FH * 0.218, 0.0])  # 画布比例坐标（FH=14.22）
        rig, pans, piv = self.build_balance("太猛", "崩溃", "太慢", "学不动",
                                            center=pivot, beam=4.6, pan_y=-1.0)
        self.play(FadeIn(rig, shift=DOWN * 0.05), FadeIn(pans, shift=DOWN * 0.05), run_time=0.7)

        # 段3（6.14-9.64）：TRPO 划信任域
        self.at(6.14)
        trpo = t("TRPO 说：划一个信任域", 30, CYAN, "BOLD")
        fit(trpo, 0.95)
        trpo.next_to(pans, DOWN, buff=0.8)
        self.play(type_in(trpo, run_time=0.9))
        self.at(8.05)
        trust = Circle(radius=0.9, color=CYAN, stroke_width=4)
        trust.next_to(trpo, DOWN, buff=0.8)
        inner = Dot(trust.get_center(), color=CYAN, radius=0.09)
        self.play(Create(trust), FadeIn(inner), run_time=0.6)
        self.at(9.64)
        far = t("新策略不能离旧策略太远", 26, WHITE)
        fit(far, 0.95)
        far.next_to(trust, DOWN, buff=0.5)
        self.play(type_in(far, run_time=0.8))

        # 段4（11.22-13.94）：二阶导数不可行
        self.at(11.22)
        self.play(FadeOut(VGroup(core, rig, pans, trpo, trust, inner, far),
                          shift=UP * 0.03), run_time=0.3)
        sec = boxed("但它要算二阶导数", 5.0, 1.1, WHITE, 28, fill=0.12, weight="BOLD")
        sec.next_to(head, DOWN, buff=1.7)
        self.play_scroll_unroll(sec, run_time=1.4)
        self.at(13.94)
        form = t("∂²J / ∂θ²", 40, CYAN, "BOLD")
        fit(form, 0.9)
        form.next_to(sec, DOWN, buff=1.5)
        self.play(FadeIn(form, shift=DOWN * 0.05), run_time=0.7)

        # 段5（15.0-16.07）：几乎不可行（红叉盖公式 + 白字结论）
        self.at(15.0)
        cross = self.play_red_cross(form)
        imp = t("工程上几乎不可行", 30, RED, "BOLD")
        fit(imp, 0.95)
        imp.next_to(form, DOWN, buff=1.3)
        self.play(type_in(imp, run_time=0.6))

        # 段6（16.07-19.56）：Schulman 用 clip 替代
        self.at(16.07)
        self.play(FadeOut(VGroup(sec, form, imp, cross), shift=UP * 0.03), run_time=0.3)
        who = t("2017 年 · OpenAI 的 Schulman", 28, WHITE)
        fit(who, 0.95)
        who.next_to(head, DOWN, buff=1.6)
        self.play(type_in(who, run_time=0.9))
        self.at(18.18)
        clipf = boxed("clip 替代复杂优化", 5.0, 1.1, CYAN, 28, wc=WHITE, fill=CARD_FILL, weight="BOLD")
        clipf.next_to(who, DOWN, buff=1.3)
        self.play_scroll_unroll(clipf, run_time=1.4)
        self.at(19.56)
        few = t("效果接近，实现只要几行代码", 26, GREEN, "BOLD")
        fit(few, 0.95)
        few.next_to(clipf, DOWN, buff=1.4)
        self.play(type_in(few, run_time=0.9))

        # 段7（23.41-26.72）：然后…（居中节拍页 + 三点动画）
        self.at(23.41)
        self.play(FadeOut(VGroup(who, clipf, few), shift=UP * 0.03), run_time=0.3)
        then = t("然后…", 40, MUTED).move_to(DOWN * FH * 0.0914)  # 画布比例坐标
        self.play(type_in(then, run_time=0.8))
        dots = VGroup(*[Dot(np.array([x, -FH * 0.1477, 0]), color=MUTED, radius=0.14)
                        for x in (-0.5, 0.0, 0.5)])
        for d in dots:
            self.play(FadeIn(d, scale=1.5), run_time=0.25)

        # 段8（26.72-30.05）：NIPS 2017 拒稿红章
        self.at(26.72)
        self.play(FadeOut(VGroup(then, dots), shift=UP * 0.03), run_time=0.3)
        rej = t("被 NIPS 2017 拒稿", 34, RED, "BOLD")
        fit(rej, 0.95)
        rej.next_to(head, DOWN, buff=1.3)
        self.play(type_in(rej, run_time=0.9))
        stamp = VGroup(Circle(radius=1.15, color=RED, stroke_width=6),
                       t("REJECTED", 26, RED, "BOLD"))
        stamp.next_to(rej, DOWN, buff=0.6)
        self.play(GrowFromCenter(stamp[0]), FadeIn(stamp[1], scale=1.3), run_time=0.7)

        # 段9（30.05-32.45）：审稿意见
        self.at(30.05)
        review = _card("审稿意见：创新性有限", 5.4, 1.1, MUTED, WHITE, 27, CARD_FILL2, "BOLD")
        review.next_to(stamp, DOWN, buff=0.8)
        self.play_scroll_unroll(review, run_time=1.4)

        # 段10（32.45-34.78）：时间才是评审
        self.at(32.45)
        time_l = t("时间，才是最公正的评审", 32, YELL, "BOLD")
        fit(time_l, 0.95)
        time_l.next_to(review, DOWN, buff=1.0)
        self.play(type_in(time_l, run_time=1.1))
        self.pad_to_voice()


# ---------------- S3 GRPO：简化 → 组内平均 → 矮子里拔将军 → 悬念 ----------------
class S3(_Base):
    def construct(self):
        self.bg()
        self.footer()
        head = t("开源社区开始简化 PPO", 36, YELL, "BOLD").to_edge(UP, buff=1.2)
        self.play(type_in(head, run_time=1.1))

        # 段1（1.78-5.75）：RLHF 时代 · 2024
        self.at(1.2)
        era = t("RLHF 时代", 26, WHITE).next_to(head, DOWN, buff=1.2)
        self.play(type_in(era, run_time=0.6))
        self.at(4.32)
        y24 = t("2024 年", 26, CYAN).next_to(era, DOWN, buff=0.7)
        self.play(type_in(y24, run_time=0.5))

        # 段2（5.75-7.99）：DeepSeek 提出 GRPO
        self.at(5.75)
        grpo = boxed("DeepSeek 提出 GRPO", 5.2, 1.1, GREEN, 30, wc=WHITE, fill=0.2, weight="BOLD")
        grpo.next_to(y24, DOWN, buff=1.2)
        self.play_scroll_unroll(grpo, run_time=1.5)

        # 段3（7.99-9.95）：不训练价值网络
        self.at(7.99)
        no_critic = boxed("不训练价值网络", 4.4, 1.0, RED, 27, wc=WHITE, fill=CARD_FILL2, weight="BOLD")
        no_critic.next_to(grpo, DOWN, buff=1.1)
        self.play_scroll_unroll(no_critic, run_time=1.3)
        self.at(9.0)
        xc = self.play_red_cross(no_critic)

        # 段4（9.95-13.04）：同一道题 → 一组回答
        self.at(9.95)
        self.play(FadeOut(VGroup(era, y24, grpo, no_critic, xc), shift=UP * 0.03), run_time=0.3)
        prompt = boxed("同一道题", 3.2, 1.0, WHITE, 28, fill=0.12, weight="BOLD")
        prompt.next_to(head, DOWN, buff=1.2)
        self.play_scroll_unroll(prompt, run_time=1.3)
        self.at(11.0)
        ans = VGroup(*[boxed(f"回答 {i}", 2.6, 1.0, CYAN, 24, fill=0.12, weight="BOLD")
                       for i in range(1, 5)])
        ans.arrange(RIGHT, buff=0.45).next_to(prompt, DOWN, buff=1.0)
        fit(ans, 0.95)
        self.play(*[FadeIn(a, shift=DOWN * 0.05) for a in ans], run_time=0.6)

        # 段5（13.04-15.45）：组内平均分当基线
        self.at(13.04)
        avg = DashedLine(LEFT * 2.9, RIGHT * 2.9, color=YELL, dash_length=0.14)
        avg.next_to(ans, DOWN, buff=0.8)
        avglab = t("组内平均分 = 基线", 26, YELL, "BOLD").next_to(avg, DOWN, buff=0.35)
        self.play(Create(avg), run_time=0.5)
        self.play(type_in(avglab, run_time=0.8))

        # 段6（15.45-18.04）：几十个学生同时交卷
        self.at(15.45)
        stu = t("就像几十个学生同时交卷", 24, MUTED).next_to(avglab, DOWN, buff=0.9)
        self.play(type_in(stu, run_time=0.8))

        # 段7（18.04-22.13）：矮子里也能拔将军
        self.at(18.04)
        self.play(FadeOut(VGroup(prompt, ans, avg, avglab, stu), shift=UP * 0.03), run_time=0.3)
        bars = VGroup()
        for h, v, col in ((2.2, "59", RED), (3.0, "78", CYAN), (2.6, "66", GREEN), (1.8, "53", MUTED)):
            bar = Rectangle(width=1.05, height=h, color=col, fill_color=col, fill_opacity=0.7)
            val = t(v, 26, col, "BOLD").next_to(bar, DOWN, buff=0.2)
            bars.add(VGroup(bar, val))
        bars.arrange(RIGHT, buff=0.8, aligned_edge=DOWN).next_to(head, DOWN, buff=1.3)
        self.play(*[GrowFromEdge(bg[0], DOWN, run_time=0.5) for bg in bars],
                  *[type_in(bg[1], run_time=0.5) for bg in bars], run_time=0.5)
        self.at(20.0)
        gen = t("互相比较打分——矮子里也能拔将军", 28, GREEN, "BOLD")
        fit(gen, 0.95)
        gen.next_to(bars, DOWN, buff=1.0)
        self.play(type_in(gen, run_time=1.0))

        # 段8（22.13-24.56）：省显存又稳定
        self.at(22.13)
        cheap = t("省显存、又稳定", 30, GREEN, "BOLD")
        fit(cheap, 0.95)
        cheap.next_to(gen, DOWN, buff=0.9)
        self.play(type_in(cheap, run_time=0.8))

        # 段9（24.56-27.39）：GLM-5.1 用的就是这套
        self.at(24.56)
        glm51 = _card("GLM-5.1 用的就是这套", 5.0, 1.0, CYAN, CYAN, 26, CARD_FILL, "BOLD")
        glm51.next_to(cheap, DOWN, buff=0.9)
        self.play_scroll_unroll(glm51, run_time=1.3)

        # 段10（27.39-30.52）：那 GLM-5.2 为什么放弃
        self.at(27.39)
        self.play(FadeOut(VGroup(bars, gen, cheap, glm51), shift=UP * 0.03), run_time=0.3)
        q1 = t("那 GLM-5.2，", 32, WHITE)
        fit(q1, 0.95)
        q1.next_to(head, DOWN, buff=1.3)
        self.play(type_in(q1, run_time=0.9))
        self.at(29.09)
        q2 = t("为什么又放弃了它？", 36, YELL, "BOLD")
        fit(q2, 0.95)
        q2.next_to(q1, DOWN, buff=0.9)
        self.play(type_in(q2, run_time=1.1))
        self.at(30.2)
        qm = t("？", 150, YELL, "BOLD").next_to(q2, DOWN, buff=2.0)
        self.play(FadeIn(qm, scale=1.2), run_time=0.6)
        self.pad_to_voice()


# ---------------- S4 机关 1：Clip ----------------
class S4(_Base):
    def construct(self):
        self.bg()
        self.footer()
        head = t("机关 ①：Clip，管微观稳定", 36, YELL, "BOLD").to_edge(UP, buff=1.2)
        self.play(type_in(head, run_time=1.1))

        # 段1（0-2.08）：第一道机关
        self.at(1.2)
        lab = t("第一道机关", 26, CYAN, "BOLD").next_to(head, DOWN, buff=1.2)
        self.play(type_in(lab, run_time=0.5))

        # 段2（2.08-3.56）：不能更新太快
        self.at(2.08)
        fast = t("策略不能更新太快", 30, WHITE, "BOLD")
        fit(fast, 0.95)
        fast.next_to(lab, DOWN, buff=0.8)
        self.play(type_in(fast, run_time=0.9))

        # 段3（3.56-7.65）：骑自行车摆动（摆锤，枢轴在上）
        self.at(3.56)
        bike = t("就像学骑自行车：左倾就往右摆", 26, WHITE)
        fit(bike, 0.95)
        bike.next_to(fast, DOWN, buff=0.9)
        self.play(type_in(bike, run_time=0.9))
        self.at(5.70)
        pivot = np.array([-FW * 0.325, FH * 0.0281, 0.0])  # 画布比例坐标（FW=8, FH=14.22）
        pend = VGroup(Line(ORIGIN, DOWN * 1.3, color=CYAN, stroke_width=5),
                      Dot(DOWN * 1.3, color=CYAN, radius=0.16))
        pend.move_to(pivot + DOWN * 0.65)
        self.play(FadeIn(pend, shift=DOWN * 0.05), run_time=0.5)
        self.play(pend.animate.rotate(-0.35, about_point=pivot), run_time=0.5)
        self.play(pend.animate.rotate(0.7, about_point=pivot), run_time=0.7)
        self.play(pend.animate.rotate(-0.35, about_point=pivot), run_time=0.5)

        # 段4（7.65-9.25）：摆猛了
        self.at(7.65)
        hard = t("但摆猛了，", 28, RED, "BOLD")
        hard.next_to(bike, DOWN, buff=1.5)
        self.play(type_in(hard, run_time=0.7))

        # 段5（9.25-10.40）：反而摔向另一边
        self.at(9.25)
        fall = t("反而摔向另一边", 28, RED, "BOLD")
        fit(fall, 0.95)
        fall.next_to(hard, DOWN, buff=0.5)
        self.play(type_in(fall, run_time=0.7))
        self.play(pend.animate.rotate(1.0, about_point=pivot), run_time=0.5)

        # 段6（10.40-12.20）：概率比
        self.at(10.40)
        self.play(FadeOut(VGroup(lab, fast, bike, hard, fall, pend), shift=UP * 0.03), run_time=0.3)
        ratio = t("PPO 把新旧策略的概率比", 28, WHITE)
        fit(ratio, 0.95)
        ratio.next_to(head, DOWN, buff=1.5)
        self.play(type_in(ratio, run_time=0.9))

        # 段7（12.20-14.96）：1±ε 区间
        self.at(12.20)
        axis = Line(LEFT * 3.1, RIGHT * 3.1, color=MUTED, stroke_width=4)
        axis.next_to(ratio, DOWN, buff=1.3)
        band = Rectangle(width=3.2, height=0.85, color=GREEN, fill_color=GREEN, fill_opacity=0.25)
        band.move_to(axis.get_center())
        e1 = t("1 − ε", 24, GREEN, "BOLD").next_to(band.get_left(), DOWN, buff=0.5)
        e2 = t("1 + ε", 24, GREEN, "BOLD").next_to(band.get_right(), DOWN, buff=0.5)
        ctr = t("1", 26, WHITE, "BOLD").next_to(band, UP, buff=0.25)
        self.play(Create(axis), run_time=0.5)
        self.play(GrowFromEdge(band, LEFT), run_time=0.6)
        self.play(type_in(e1, run_time=0.5), type_in(e2, run_time=0.5), type_in(ctr, run_time=0.5))

        # 段8（14.96-18.45）：超出就截断
        self.at(14.96)
        cut = t("超出就截断", 30, RED, "BOLD")
        fit(cut, 0.95)
        cut.next_to(axis, DOWN, buff=1.6)
        self.play(type_in(cut, run_time=0.8))
        lx = Line(band.get_left() + LEFT * 0.9 + UP * 0.45, band.get_left() + LEFT * 0.9 + DOWN * 0.45,
                  color=RED, stroke_width=10)
        rx = Line(band.get_right() + RIGHT * 0.9 + UP * 0.45, band.get_right() + RIGHT * 0.9 + DOWN * 0.45,
                  color=RED, stroke_width=10)
        self.play(GrowFromCenter(lx), GrowFromCenter(rx), run_time=0.4)

        # 段9（18.45-19.91）：不给它贡献梯度
        self.at(18.45)
        no_grad = t("不给它贡献梯度", 24, MUTED).next_to(cut, DOWN, buff=0.7)
        self.play(type_in(no_grad, run_time=0.6))

        # 段10（19.91-23.12）：一次截断替代整套二阶优化
        self.at(19.91)
        once = t("一次截断，替代了 TRPO 的整套二阶优化", 28, GREEN, "BOLD")
        fit(once, 0.95)
        once.next_to(no_grad, DOWN, buff=0.9)
        self.play(type_in(once, run_time=1.0))
        self.pad_to_voice()


# ---------------- S5 机关 2：Critic ----------------
class S5(_Base):
    def construct(self):
        self.bg()
        self.footer()
        head = t("机关 ②：Critic", 36, YELL, "BOLD").to_edge(UP, buff=1.2)
        self.play(type_in(head, run_time=1.1))

        # 段1（2.71-5.09）：优势函数回答一个问题
        self.at(2.71)
        q = t("优势函数回答一个问题：", 28, WHITE)
        fit(q, 0.95)
        q.next_to(head, DOWN, buff=1.6)
        self.play(type_in(q, run_time=0.8))

        # 段2（5.09-8.09）：比平均水平好多少
        self.at(5.09)
        better = t("这个动作比平均水平好多少？", 30, CYAN, "BOLD")
        fit(better, 0.95)
        better.next_to(q, DOWN, buff=1.8)
        self.play(type_in(better, run_time=0.9))

        # 段3（8.09-10.91 前）：组装公式（上标锚 UR）
        self.at(6.5)
        formula = VGroup(t("A(s,a) = ", 42, WHITE, "BOLD"),
                         sub("Q", "动作得分", 42, 20, WHITE, "BOLD"),
                         t(" − ", 42, WHITE, "BOLD"),
                         sub("V", "平均水平", 42, 20, WHITE, "BOLD"),
                         ).arrange(RIGHT, buff=0.15)
        fit(formula, 0.95)
        formula.next_to(better, DOWN, buff=2.0)
        self.play(FadeIn(formula, shift=DOWN * 0.05), run_time=0.8)

        # 段4（8.09-10.91）：GRPO 组内均值
        self.at(8.09)
        self.play(FadeOut(VGroup(q, better, formula), shift=UP * 0.03), run_time=0.3)
        grpo = boxed("GRPO：拿同组均值当基线", 5.4, 1.1, GREEN, 27, wc=WHITE, fill=0.2, weight="BOLD")
        grpo.next_to(head, DOWN, buff=1.5)
        self.play_scroll_unroll(grpo, run_time=1.4)

        # 段5（10.91-14.83）：两条轨迹 5 步 vs 50 步
        self.at(10.91)
        t5 = Rectangle(width=1.6, height=0.8, color=CYAN, fill_color=CYAN, fill_opacity=0.5)
        t50 = Rectangle(width=5.2, height=0.8, color=YELL, fill_color=YELL, fill_opacity=0.5)
        l5 = t("5 步", 22, CYAN, "BOLD").next_to(t5, DOWN, buff=0.2)
        l50 = t("50 步", 22, YELL, "BOLD").next_to(t50, DOWN, buff=0.2)
        pair = VGroup(VGroup(t5, l5), VGroup(t50, l50)).arrange(RIGHT, buff=1.2, aligned_edge=DOWN)
        pair.next_to(grpo, DOWN, buff=1.3)
        fit(pair, 0.95)
        self.play(FadeIn(t5), type_in(l5, run_time=0.5), run_time=0.5)
        self.play(FadeIn(t50), type_in(l50, run_time=0.5), run_time=0.5)

        # 段6（14.83-17.18）：怎么放一起算平均 → 红叉
        self.at(14.83)
        how = t("怎么放在一起算平均？", 28, RED, "BOLD")
        fit(how, 0.95)
        how.next_to(pair, DOWN, buff=1.2)
        self.play(type_in(how, run_time=0.8))
        self.at(16.5)
        xc = self.play_red_cross(pair)

        # 段7（17.18-18.17）：Critic 独立打分
        self.at(17.18)
        self.play(FadeOut(VGroup(grpo, pair, how, xc), shift=UP * 0.03), run_time=0.3)
        crit = t("Critic 呢：每条轨迹独立打分", 28, GREEN, "BOLD")
        fit(crit, 0.95)
        crit.next_to(head, DOWN, buff=1.6)
        self.play(type_in(crit, run_time=0.9))

        # 段8（18.17-20.88）：长度不影响估值
        self.at(18.17)
        s5b = Rectangle(width=1.6, height=0.8, color=CYAN, fill_color=CYAN, fill_opacity=0.5)
        s50b = Rectangle(width=5.2, height=0.8, color=YELL, fill_color=YELL, fill_opacity=0.5)
        sc5 = t("+0.8", 24, GREEN, "BOLD").next_to(s5b, UP, buff=0.2)
        sc50 = t("+1.2", 24, GREEN, "BOLD").next_to(s50b, UP, buff=0.2)
        spair = VGroup(VGroup(s5b, sc5), VGroup(s50b, sc50)).arrange(RIGHT, buff=1.2, aligned_edge=DOWN)
        spair.next_to(crit, DOWN, buff=1.5)
        fit(spair, 0.95)
        self.play(FadeIn(s5b), type_in(sc5, run_time=0.5), run_time=0.5)
        self.play(FadeIn(s50b), type_in(sc50, run_time=0.5), run_time=0.5)
        self.at(20.0)
        lens = t("长度不影响估值", 26, WHITE).next_to(spair, DOWN, buff=1.0)
        self.play(type_in(lens, run_time=0.8))

        # 段9（23.14-24.44）：长程任务里
        self.at(23.14)
        long = t("长程任务里，", 28, WHITE).next_to(lens, DOWN, buff=0.8)
        self.play(type_in(long, run_time=0.6))

        # 段10（24.44-26.19）：这就是胜负手
        self.at(24.44)
        dec = t("这就是胜负手", 36, YELL, "BOLD")
        fit(dec, 0.95)
        dec.next_to(long, DOWN, buff=0.8)
        self.play(type_in(dec, run_time=1.0))

        # 段11（26.19-28.55）：可光有它，模型会不会走偏
        self.at(26.19)
        self.play(FadeOut(VGroup(crit, spair, lens, long, dec, xc), shift=UP * 0.03), run_time=0.3)
        doubt = t("可光有它，模型会不会走偏？", 30, WHITE, "BOLD")
        fit(doubt, 0.95)
        doubt.next_to(head, DOWN, buff=2.2)
        self.play(type_in(doubt, run_time=1.0))
        qm = t("？", 150, YELL, "BOLD").next_to(doubt, DOWN, buff=2.8)
        self.play(FadeIn(qm, scale=1.2), run_time=0.6)
        self.pad_to_voice()


# ---------------- S6 机关 3：KL + 三机关各管一层 ----------------
class S6(_Base):
    def construct(self):
        self.bg()
        self.footer()
        head = t("机关 ③：KL 约束", 36, YELL, "BOLD").to_edge(UP, buff=1.2)
        self.play(type_in(head, run_time=1.1))

        # 段1（0.95-1.50）：骗奖励
        self.at(0.95)
        cheat = boxed("为了骗奖励，模型突然改掉语言能力", 6.4, 1.1, RED, 26, wc=WHITE, fill=CARD_FILL2, weight="BOLD")
        cheat.next_to(head, DOWN, buff=1.5)
        self.play_scroll_unroll(cheat, run_time=1.5)
        self.play(Flash(cheat, color=RED), run_time=0.4)

        # 段2（1.50-4.28）：所以第三道机关
        self.at(1.50)
        third = t("所以第三道机关", 28, WHITE).next_to(cheat, DOWN, buff=1.3)
        self.play(type_in(third, run_time=0.7))

        # 段3（4.28-6.95）：KL 约束
        self.at(4.28)
        kl = boxed("KL 约束", 3.6, 1.1, CYAN, 32, wc=WHITE, fill=0.2, weight="BOLD")
        kl.next_to(third, DOWN, buff=1.2)
        self.play_scroll_unroll(kl, run_time=1.4)

        # 段4（6.95-9.62）：防止走偏
        self.at(6.95)
        guard = t("防止它走偏", 28, GREEN, "BOLD")
        fit(guard, 0.95)
        guard.next_to(kl, DOWN, buff=1.1)
        self.play(type_in(guard, run_time=0.7))

        # 段5（9.62-11.26）：三道机关各管一层
        self.at(9.62)
        self.play(FadeOut(VGroup(cheat, third, kl, guard), shift=UP * 0.03), run_time=0.3)
        layer = t("三道机关各管一层", 30, WHITE, "BOLD")
        fit(layer, 0.95)
        layer.next_to(head, DOWN, buff=1.2)
        self.play(type_in(layer, run_time=0.9))

        # 段6（11.26-13.21）：三卡
        self.at(11.26)
        c1 = _card("Clip：限制单步幅度", 5.2, 1.0, CYAN, CYAN, 27, CARD_FILL, "BOLD")
        c2 = _card("Critic：提供 token 级信号", 5.2, 1.0, GREEN, GREEN, 27, CARD_FILL, "BOLD")
        c3 = _card("KL：锚定整体方向", 5.2, 1.0, MUTED, MUTED, 27, CARD_FILL, "BOLD")
        trio = VGroup(c1, c2, c3).arrange(DOWN, buff=0.6, aligned_edge=LEFT)
        trio.next_to(layer, DOWN, buff=1.0)
        trio.align_to(layer, LEFT)
        self.play_scroll_unroll(c1, run_time=1.2)
        self.at(13.21)
        self.play_scroll_unroll(c2, run_time=1.2)
        self.at(15.22)
        self.play_scroll_unroll(c3, run_time=1.2)

        # 段7（17.74-21.83）：微观 / 中观 / 宏观 —— 逐个对准对应卡
        self.at(17.74)
        m1 = t("微观", 24, CYAN, "BOLD").next_to(c1, LEFT, buff=0.35)
        m1.align_to(c1, UP)
        self.play(type_in(m1, run_time=0.5))
        self.at(20.23)
        m2 = t("中观", 24, GREEN, "BOLD").next_to(c2, LEFT, buff=0.35)
        m2.align_to(c2, UP)
        self.play(type_in(m2, run_time=0.5))
        self.at(21.83)
        m3 = t("宏观", 24, MUTED, "BOLD").next_to(c3, LEFT, buff=0.35)
        m3.align_to(c3, UP)
        self.play(type_in(m3, run_time=0.5))

        # 段8（22.71-23.47）：各司其职
        self.at(22.71)
        duty = t("各司其职", 34, YELL, "BOLD")
        fit(duty, 0.95)
        duty.next_to(trio, DOWN, buff=1.1)
        self.play(type_in(duty, run_time=0.9))
        self.pad_to_voice()


# ---------------- S7 GLM-5.2 实战：长轨迹压缩 → GRPO 失效 → Critic 通吃 → 作弊拦截 ----------------
class S7(_Base):
    def construct(self):
        self.bg()
        self.footer()
        head = t("GLM-5.2：长程任务实战", 36, YELL, "BOLD").to_edge(UP, buff=1.2)
        self.play(type_in(head, run_time=1.1))

        # 段1（2.84-5.46）：瞄准长程任务
        self.at(2.84)
        aim = t("GLM-5.2 瞄准长程任务", 28, WHITE)
        fit(aim, 0.95)
        aim.next_to(head, DOWN, buff=1.5)
        self.play(type_in(aim, run_time=0.9))

        # 段2（5.46-7.77）：coding agent 几十步
        self.at(5.46)
        agent = t("coding agent 执行几十步工具调用", 26, WHITE)
        fit(agent, 0.95)
        agent.next_to(aim, DOWN, buff=1.0)
        self.play(type_in(agent, run_time=0.8))

        # 段3（7.77-8.71）：轨迹远超上下文窗口
        self.at(7.77)
        win = Rectangle(width=5.6, height=1.1, color=MUTED, fill_color=MUTED, fill_opacity=0.12)
        win.next_to(agent, DOWN, buff=1.2)
        over = Rectangle(width=7.0, height=0.55, color=YELL, fill_color=YELL, fill_opacity=0.8)
        over.move_to(win.get_center())
        wlab = t("上下文窗口", 20, MUTED).next_to(win, UP, buff=0.2)
        self.play(Create(win), type_in(wlab, run_time=0.5), run_time=0.5)
        self.play(FadeIn(over, shift=LEFT * 0.3), run_time=0.5)

        # 段4（8.71-10.46）：压缩后
        self.at(8.71)
        comp = t("压缩后，", 26, WHITE).next_to(win, DOWN, buff=1.1)
        self.play(type_in(comp, run_time=0.6))

        # 段5（10.46-13.45）：200 步 → 3 条子轨迹
        self.at(10.46)
        self.play(FadeOut(VGroup(aim, agent, win, over, wlab, comp), shift=UP * 0.03), run_time=0.3)
        big = Rectangle(width=6.6, height=1.1, color=YELL, fill_color=YELL, fill_opacity=0.7)
        big.next_to(head, DOWN, buff=1.8)
        bl = t("一条 200 步的轨迹", 26, WHITE).next_to(big, DOWN, buff=0.3)
        self.play(FadeIn(big, shift=DOWN * 0.05), run_time=0.5)
        self.play(type_in(bl, run_time=0.7))
        self.at(12.3)
        segs = VGroup(Rectangle(width=1.65, height=1.1, color=CYAN, fill_color=CYAN, fill_opacity=0.7),
                      Rectangle(width=0.99, height=1.1, color=GREEN, fill_color=GREEN, fill_opacity=0.7),
                      Rectangle(width=3.96, height=1.1, color=MUTED, fill_color=MUTED, fill_opacity=0.7))
        segs.arrange(RIGHT, buff=0.15).move_to(big.get_center())
        seglab = VGroup(t("50 步", 20, CYAN, "BOLD"), t("30 步", 20, GREEN, "BOLD"),
                        t("120 步", 20, MUTED, "BOLD"))
        for s, lb in zip(segs, seglab):
            lb.next_to(s, DOWN, buff=0.15)
        self.play(FadeOut(VGroup(big, bl), shift=UP * 0.03), FadeIn(segs, shift=DOWN * 0.05), run_time=0.4)
        self.play(*[type_in(lb, run_time=0.4) for lb in seglab], run_time=0.4)
        sub = t("3 条长短不一的子轨迹", 24, WHITE).next_to(segs, DOWN, buff=0.8)
        self.play(type_in(sub, run_time=0.6))

        # 段6（13.45-15.24）：GRPO 组内比较直接失效
        self.at(13.8)
        fail = t("GRPO 的组内比较，直接失效", 28, RED, "BOLD")
        fit(fail, 0.95)
        fail.next_to(segs, DOWN, buff=1.6)
        self.play(type_in(fail, run_time=0.8))
        self.at(14.8)
        xc = self.play_red_cross(segs)

        # 段7（15.24-16.64）：Critic 却无所谓
        self.at(15.24)
        self.play(FadeOut(VGroup(segs, seglab, sub, fail, xc), shift=UP * 0.03), run_time=0.3)
        fine = t("Critic 却无所谓：独立估值", 28, GREEN, "BOLD")
        fit(fine, 0.95)
        fine.next_to(head, DOWN, buff=1.4)
        self.play(type_in(fine, run_time=0.9))

        # 段8（16.64-18.52）：三段独立打分
        self.at(16.64)
        p1 = Rectangle(width=1.65, height=1.4, color=CYAN, fill_color=CYAN, fill_opacity=0.6)
        p2 = Rectangle(width=0.99, height=1.7, color=GREEN, fill_color=GREEN, fill_opacity=0.6)
        p3 = Rectangle(width=3.96, height=1.5, color=MUTED, fill_color=MUTED, fill_opacity=0.6)
        s1 = t("+0.9", 22, GREEN, "BOLD").next_to(p1, UP, buff=0.2)
        s2 = t("+1.4", 22, GREEN, "BOLD").next_to(p2, UP, buff=0.2)
        s3 = t("+1.1", 22, GREEN, "BOLD").next_to(p3, UP, buff=0.2)
        scored = VGroup(VGroup(p1, s1), VGroup(p2, s2), VGroup(p3, s3))
        scored.arrange(RIGHT, buff=0.6, aligned_edge=DOWN).next_to(fine, DOWN, buff=1.5)
        fit(scored, 0.95)
        self.play(FadeIn(p1), type_in(s1, run_time=0.4), run_time=0.4)
        self.play(FadeIn(p2), type_in(s2, run_time=0.4), run_time=0.4)
        self.play(FadeIn(p3), type_in(s3, run_time=0.4), run_time=0.4)

        # 段9（18.52-21.19）：长短通吃
        self.at(18.52)
        all_ok = t("长短通吃", 34, YELL, "BOLD")
        fit(all_ok, 0.95)
        all_ok.next_to(scored, DOWN, buff=1.3)
        self.play(type_in(all_ok, run_time=0.9))

        # 段10（21.19-22.81）：模型作弊呢
        self.at(21.19)
        self.play(FadeOut(VGroup(fine, scored, all_ok, xc), shift=UP * 0.03), run_time=0.3)
        cheat = t("模型作弊呢？", 32, WHITE, "BOLD")
        fit(cheat, 0.95)
        cheat.next_to(head, DOWN, buff=1.8)
        self.play(type_in(cheat, run_time=0.9))

        # 段11（22.81-25.78）：拦截返回假信息
        self.at(22.81)
        block = boxed("GLM-5.2 拦截，返回假信息", 5.6, 1.1, RED, 27, wc=WHITE, fill=CARD_FILL2, weight="BOLD")
        block.next_to(cheat, DOWN, buff=1.2)
        self.play_scroll_unroll(block, run_time=1.4)

        # 段12（25.78-27.55）：让轨迹继续
        self.at(25.78)
        cont = t("让轨迹继续", 26, WHITE).next_to(block, DOWN, buff=0.9)
        self.play(type_in(cont, run_time=0.6))

        # 段13（27.55-29.80）：作弊没用
        self.at(27.55)
        useless = t("作弊没用", 34, GREEN, "BOLD")
        fit(useless, 0.95)
        useless.next_to(cont, DOWN, buff=0.9)
        self.play(type_in(useless, run_time=0.9))
        self.pad_to_voice()


# ---------------- S8 总结：任务分栏 → 预告 GRPO 数学 → 留题 ----------------
class S8(_Base):
    def construct(self):
        self.bg()
        self.footer()
        head = t("PPO 不是万能，但目前最稳", 36, YELL, "BOLD").to_edge(UP, buff=1.2)
        self.play(type_in(head, run_time=1.1))

        # 段1（1.70-3.45）：不是万能
        self.at(1.70)
        notall = t("不是万能", 28, MUTED)
        fit(notall, 0.95)
        notall.next_to(head, DOWN, buff=1.5)
        self.play(type_in(notall, run_time=0.6))

        # 段2（3.45-4.37）：两栏
        self.at(3.45)
        short = boxed("短任务", 3.0, 1.0, GREEN, 28, wc=WHITE, fill=0.15, weight="BOLD")
        long = boxed("长任务", 3.0, 1.0, YELL, 28, wc=WHITE, fill=0.15, weight="BOLD")
        cols = VGroup(short, long).arrange(RIGHT, buff=1.2).next_to(notall, DOWN, buff=1.1)
        self.play_scroll_unroll(short, run_time=1.2)
        self.play_scroll_unroll(long, run_time=1.2)

        # 段3（4.37-6.19）：短任务 GRPO 便宜
        self.at(4.37)
        g = t("GRPO 便宜够用", 26, GREEN, "BOLD").next_to(short, DOWN, buff=0.7)
        self.play(type_in(g, run_time=0.7))

        # 段4（6.19-8.80）：长任务 PPO 鲁棒
        self.at(6.19)
        p = t("PPO 更鲁棒", 26, YELL, "BOLD").next_to(long, DOWN, buff=0.7)
        self.play(type_in(p, run_time=0.7))

        # 段5（8.80-11.77）：算法选择任务相关
        self.at(8.80)
        rel = t("算法选择，正在变得任务相关", 28, WHITE, "BOLD")
        fit(rel, 0.95)
        rel.next_to(cols, DOWN, buff=1.6)
        self.play(type_in(rel, run_time=0.9))

        # 段6（11.77-14.77）：下一条拆 GRPO 数学
        self.at(11.77)
        self.play(FadeOut(VGroup(notall, cols, g, p, rel), shift=UP * 0.03), run_time=0.3)
        nxt = t("下一条，拆 GRPO 的数学", 30, WHITE)
        fit(nxt, 0.95)
        nxt.next_to(head, DOWN, buff=1.6)
        self.play(type_in(nxt, run_time=0.9))
        self.at(13.5)
        size32 = boxed("组大小 32", 3.6, 1.1, CYAN, 32, wc=WHITE, fill=0.2, weight="BOLD")
        size32.next_to(nxt, DOWN, buff=1.4)
        self.play_scroll_unroll(size32, run_time=1.3)

        # 段7（14.77-16.35）：为什么是甜点
        self.at(14.77)
        sweet = t("为什么是甜点？", 32, YELL, "BOLD")
        fit(sweet, 0.95)
        sweet.next_to(size32, DOWN, buff=1.3)
        self.play(type_in(sweet, run_time=0.9))

        # 段8（16.35-18.13）：最后留道题（换页：先带走页2 全部元素）
        self.at(16.35)
        self.play(FadeOut(VGroup(nxt, size32, sweet), shift=UP * 0.03), run_time=0.3)
        quiz = t("最后留道题：", 28, WHITE)
        fit(quiz, 0.95)
        quiz.next_to(head, DOWN, buff=1.2)
        self.play(type_in(quiz, run_time=0.7))

        # 段9（18.13-19.66）：agent 50 步修 bug
        self.at(18.13)
        qcard = _card("一个 agent 花 50 步修 bug", 5.6, 1.1, CYAN, WHITE, 27, CARD_FILL2, "BOLD")
        qcard.next_to(quiz, DOWN, buff=1.0)
        self.play_scroll_unroll(qcard, run_time=1.3)
        self.at(19.66)
        subq = t("压缩成 3 条长短不一的子轨迹", 26, WHITE)
        fit(subq, 0.95)
        subq.next_to(qcard, DOWN, buff=0.8)
        self.play(type_in(subq, run_time=0.8))

        # 段10（22.35-25.42）：GRPO 和 PPO 会怎么处理
        self.at(22.35)
        qend = t("GRPO 和 PPO 会怎么处理？", 30, YELL, "BOLD")
        fit(qend, 0.95)
        qend.next_to(subq, DOWN, buff=0.9)
        self.play(type_in(qend, run_time=0.9))

        # 段11（25.42-28.26）：评论区聊聊
        self.at(25.42)
        chat = t("评论区聊聊", 28, GREEN, "BOLD")
        fit(chat, 0.95)
        chat.next_to(qend, DOWN, buff=0.8)
        self.play(type_in(chat, run_time=0.7))
        self.pad_to_voice()


# ---------------- S9 关注引导 CTA + 品牌尾卡 ----------------
class S9(_Base):
    def construct(self):
        self.bg()
        self.footer()
        # 品牌图 + 关注引导 + 当期标题 + 公众号引导（决策 3 尾卡四要素）
        logo = ImageMobject("avatar-sjai-round.png")
        logo.scale_to_fit_width(3.6)
        logo.move_to(UP * config.frame_height * 0.26)  # 画布比例坐标
        self.at(0.3)
        self.play(FadeIn(logo, scale=0.9), run_time=0.7)

        # 段1（0.52-2.73）：点赞
        self.at(0.52)
        like = boxed("👍 点赞", 2.3, 0.9, YELL, 24, wc=WHITE, fill=0.15, weight="BOLD")
        share = boxed("↗ 转发", 2.3, 0.9, CYAN, 24, wc=WHITE, fill=0.15, weight="BOLD")
        cta = VGroup(like, share).arrange(RIGHT, buff=0.5).next_to(logo, DOWN, buff=0.6)
        self.play(FadeIn(like, shift=DOWN * 0.05), run_time=0.4)
        self.at(2.73)
        self.play(FadeIn(share, shift=DOWN * 0.05), run_time=0.4)

        # 段2（4.57-6.60）：关注
        self.at(4.57)
        follow = t("关注「数解AI」", 44, YELL, "BOLD")
        fit(follow, 0.95)
        follow.next_to(cta, DOWN, buff=0.6)
        self.play(type_in(follow, run_time=1.1))

        # 段3（6.60-9.11）：继续往下拆
        self.at(6.60)
        cont = t("后面我们继续往下拆", 28, WHITE)
        fit(cont, 0.95)
        cont.next_to(follow, DOWN, buff=0.45)
        self.play(type_in(cont, run_time=0.8))

        # 段4（9.11-11.27）：更多细节解读
        self.at(9.11)
        more = t("想获得更多细节解读", 26, MUTED).next_to(cont, DOWN, buff=0.35)
        self.play(type_in(more, run_time=0.7))

        # 段5（11.27-14.51）：公众号同名文章 + 当期标题（more 换下）
        self.at(11.27)
        self.play(FadeOut(more, shift=UP * 0.03), run_time=0.3)
        wc = t("公众号查看同名文章", 30, GREEN, "BOLD")
        fit(wc, 0.95)
        wc.next_to(cont, DOWN, buff=0.4)
        self.play(type_in(wc, run_time=0.9))
        self.at(12.6)
        title = t("《PPO：被顶会拒稿，怎么成了RLHF发动机？》", 24, WHITE, "BOLD")
        fit(title, 0.92)
        title.next_to(wc, DOWN, buff=0.4)
        self.play(type_in(title, run_time=1.1))
        self.pad_to_voice()


if __name__ == "__main__":
    pass
