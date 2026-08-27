#!/usr/bin/env python3
"""《Muon 怎么省一半显存？优化器只记一份账》视频号 Manim 动画（竖屏 1080×1920）

6 个场景 S1-S6，与 storyboard.md 一一对应。
- 配音：MiniMax 预设精英男声（male-qn-jingying，speech-2.8-turbo，speed 1.0 pitch +2）
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

# 每段配音时长（tts_split.py 实测 2026-08-26），渲染时长 = 配音 + TAIL
VOICE_DUR = {"S1": 29.67, "S2": 35.54, "S3": 47.85, "S4": 31.88, "S5": 38.63, "S6": 42.43}
TAIL = 2.5


def _footer(self) -> Text:
    f = t("数解AI · 大模型原理", 20, MUTED).to_edge(DOWN, buff=1.15)
    self.add(f)
    return f


# ---------------- S1 开场钩子：6.4TB 的账 ----------------
class S1(_Base):
    def construct(self):
        self.bg()
        f = _footer(self)

        # 页1：概念图 + 6.4TB 数字
        head = t("第一笔显存开销", 38, YELL, "BOLD").to_edge(UP, buff=1.2)
        note0 = t("以 DeepSeek-V4-Pro 为例", 24, MUTED).next_to(head, DOWN, buff=0.5)
        img = ImageMobject(str(IMG / "s1-ledger-round.png"))
        img.scale_to_fit_width(5.4)
        lab = t("1.6 万亿参数 × 2 份账", 34, WHITE, "BOLD")
        slot = dynamic_slot(2.6, 0.9)
        num_row = stable_row(lab, slot, buff=0.5)
        lab2 = t("光优化器状态", 30, MUTED)
        page1 = page_stack(img, num_row, lab2, buff=0.9)
        layout_page(page1)

        self.at_clip("S1-c01")
        self.play_parallel(type_in(head, run_time=1.1), FadeIn(note0, shift=DOWN * 0.05),
                           FadeIn(img, shift=DOWN * 0.05), run_time=1.1)
        self.at_clip("S1-c02")
        self.play(type_in(lab, run_time=0.9))
        self.at_clip("S1-c03")
        cnt = self.counter_value(0, 6.4, decimals=1, suffix=" TB", size=56, color=YELL,
                                 anchor=slot, run_time=1.0)  # 主视觉
        self.at_clip("S1-c04")
        self.emphasize(cnt, run_time=0.6)  # 1/5
        self.at_clip("S1-c05")
        self.play(type_in(lab2, run_time=0.8))

        # 页2：四块账（优化器状态常驻）
        head2 = t("训练时显存的四块账", 38, YELL, "BOLD").to_edge(UP, buff=1.2)
        c1 = _card("参数", 3.3, 2.2, CYAN, WHITE, 44, CARD_FILL, "BOLD")
        c2 = _card("梯度", 3.3, 2.2, CYAN, WHITE, 44, CARD_FILL, "BOLD")
        c3 = _card("激活值", 3.3, 2.2, CYAN, WHITE, 44, CARD_FILL, "BOLD")
        c4 = _card("优化器状态", 3.3, 2.2, YELL, WHITE, 44, CARD_FILL, "BOLD")
        grid = VGroup(c1, c2, c3, c4).arrange_in_grid(2, 2, buff=0.5)
        note = t("只有它全程常驻", 34, GREEN, "BOLD")
        page2 = page_stack(grid, note, buff=1.7)
        layout_page(page2)

        self.play(FadeOut(head), FadeOut(note0), FadeOut(page1), FadeOut(cnt),
                  type_in(head2), run_time=1.1)
        self.play_scroll_unroll_many(c1, c2, c3, c4, run_time=1.2)  # 主视觉
        self.at_clip("S1-c06")
        self.play(type_in(note, run_time=0.9))
        self.at_clip("S1-c07")
        self.play(FadeOut(head2), FadeOut(page2), run_time=0.5)

        # 页3：Muon 答案
        head3 = t("DeepSeek-V4 的答案", 38, YELL, "BOLD").to_edge(UP, buff=1.2)
        muon = t("Muon", 72, YELL, "BOLD")
        card = _card("换掉优化器本身", 6.6, 2.2, GREEN, WHITE, 44, CARD_FILL, "BOLD")
        slot3 = dynamic_slot(2.2, 0.9)
        lab3 = t("直接省下", 34, WHITE, "BOLD")
        row3 = stable_row(lab3, slot3, buff=0.4)
        page3 = page_stack(muon, card, row3, buff=1.8)
        layout_page(page3)

        self.play_parallel(type_in(head3, run_time=1.1), type_in(muon, run_time=1.1),
                           run_time=1.1)
        self.at_clip("S1-c08")
        self.play_scroll_unroll(card, run_time=1.2)
        self.wait(0.1)
        cnt3 = self.counter_value(0, 3, suffix=" TB", size=56, color=GREEN,
                                  anchor=slot3, run_time=1.0,
                                  extra_anims=[type_in(lab3, run_time=0.6)])  # 主视觉
        self.at_clip("S1-c09")
        q = t("它怎么做到的？", 60, YELL, "BOLD")
        page_auto(q)
        self.play(FadeOut(head3), FadeOut(page3), FadeOut(cnt3), type_in(q), run_time=0.9)
        self.wait(0.3)
        self.transition_out(f, q)
        self.pad_to_voice()


# ---------------- S2 AdamW 两份账 + v 的本质 ----------------
class S2(_Base):
    def construct(self):
        self.bg()
        f = _footer(self)

        # 页1：m/v 两张账本卡
        head = t("AdamW 的账本", 38, YELL, "BOLD").to_edge(UP, buff=1.2)
        m_card = _card("m 一阶矩 · 动量", 6.6, 1.9, CYAN, WHITE, 40, CARD_FILL, "BOLD")
        m_sub = t("梯度的滑动平均", 30, WHITE)
        v_card = _card("v 二阶矩", 6.6, 1.9, YELL, WHITE, 40, CARD_FILL, "BOLD")
        v_sub = t("梯度平方的滑动平均", 30, WHITE)
        concl = t("两个数组，各占一份显存", 36, WHITE, "BOLD")
        page1 = page_stack(m_card, m_sub, v_card, v_sub, concl, buff=0.7)
        layout_page(page1)

        self.at_clip("S2-c01")
        self.play(type_in(head, run_time=0.9))
        self.wait(0.1)
        self.play_scroll_unroll_many(m_card, v_card, run_time=1.0)  # 主视觉
        self.at_clip("S2-c02")
        self.play(type_in(m_sub, run_time=0.8))
        self.at_clip("S2-c03")
        self.play(type_in(v_sub, run_time=0.8))
        self.at_clip("S2-c04")
        self.play(type_in(concl, run_time=0.9))
        self.at_clip("S2-c05")
        self.play(FadeOut(head), FadeOut(page1), run_time=0.5)

        # 页2：v 的归一化
        head2 = t("v 到底在做什么？", 38, YELL, "BOLD").to_edge(UP, buff=1.2)
        big_lab = t("大梯度", 36, WHITE, "BOLD")
        big_ar = Arrow(ORIGIN, RIGHT * 2.2, color=RED, buff=0.1, stroke_width=8)
        big_txt = t("自动减速", 32, RED, "BOLD")
        big_row = VGroup(big_lab, big_ar, big_txt).arrange(RIGHT, buff=0.5)
        small_lab = t("小梯度", 36, WHITE, "BOLD")
        small_ar = Arrow(ORIGIN, RIGHT * 2.2, color=GREEN, buff=0.1, stroke_width=8)
        small_txt = t("自动加速", 32, GREEN, "BOLD")
        small_row = VGroup(small_lab, small_ar, small_txt).arrange(RIGHT, buff=0.5)
        concl2 = _card("本质：粗糙的、对角的正交化", 6.8, 2.0, YELL, WHITE, 38, CARD_FILL, "BOLD")
        note = t("每个维度一套自适应学习率", 28, MUTED)
        page2 = page_stack(big_row, small_row, concl2, note, buff=1.3)
        layout_page(page2)

        self.play(type_in(head2, run_time=1.1))
        self.at_clip("S2-c06")
        self.play_parallel(type_in(big_lab, run_time=0.6), Create(big_ar),
                           type_in(big_txt, run_time=0.6), run_time=0.8)  # 主视觉
        self.at_clip("S2-c07")
        self.play_parallel(type_in(small_lab, run_time=0.6), Create(small_ar),
                           type_in(small_txt, run_time=0.6), run_time=0.8)
        self.at_clip("S2-c08")
        self.play_scroll_unroll(concl2, run_time=1.2)
        self.wait(0.1)
        self.play(type_in(note, run_time=0.8))
        self.at_clip("S2-c09")
        self.play(FadeOut(head2), FadeOut(page2), run_time=0.5)

        # 页3：核心冲突
        head3 = t("核心冲突", 38, YELL, "BOLD").to_edge(UP, buff=1.2)
        a_card = _card("AdamW：M×N 个标量\n对角近似", 6.6, 2.0, CYAN, WHITE, 36, CARD_FILL, "BOLD")
        m_card2 = _card("Muon：矩阵级正交化", 6.6, 2.0, YELL, WHITE, 36, CARD_FILL, "BOLD")
        m_sub2 = t("更新幅度在所有方向完全相等", 30, GREEN, "BOLD")
        save_lab = t("顺便把 v 整份省掉", 34, WHITE, "BOLD")
        q = t("怎么省？", 56, YELL, "BOLD")
        page3 = page_stack(a_card, m_card2, m_sub2, save_lab, q, buff=0.6)
        layout_page(page3)

        self.play(type_in(head3, run_time=1.1))
        self.wait(0.1)
        self.play_scroll_unroll_many(a_card, m_card2, run_time=1.2)  # 主视觉
        self.at_clip("S2-c10")
        self.play(type_in(m_sub2, run_time=0.8))
        self.at_clip("S2-c11")
        self.play(type_in(save_lab, run_time=0.8))
        self.at_clip("S2-c12")
        self.play(type_in(q, run_time=0.8))
        self.wait(0.3)
        self.transition_out(f, head3, a_card, m_card2, m_sub2, save_lab, q)
        self.pad_to_voice()


# ---------------- S3 Muon 三步 + Newton-Schulz ----------------
class S3(_Base):
    def construct(self):
        self.bg()
        f = _footer(self)

        # 页1：三步卡
        head = t("Muon 每步只做三件事", 38, YELL, "BOLD").to_edge(UP, buff=1.2)
        c1 = _card("① 动量平滑", 6.6, 1.7, CYAN, WHITE, 38, CARD_FILL, "BOLD")
        c2 = _card("② 拧成正交矩阵", 6.6, 1.7, YELL, WHITE, 38, CARD_FILL, "BOLD")
        c2_sub = t("所有方向更新幅度相等", 30, GREEN, "BOLD")
        c3 = _card("③ 缩放更新", 6.6, 1.7, CYAN, WHITE, 38, CARD_FILL, "BOLD")
        core = t("核心是第二步", 36, YELL, "BOLD")
        page1 = page_stack(c1, c2, c2_sub, c3, core, buff=0.6)
        layout_page(page1)

        self.at_clip("S3-c01")
        self.play(type_in(head, run_time=1.1))
        self.wait(0.1)
        self.play_scroll_unroll_many(c1, c2, c3, run_time=1.2)  # 主视觉
        self.at_clip("S3-c02")
        sub1 = t("和 Adam 一样", 28, MUTED).move_to((c1.get_bottom() + c2.get_top()) / 2)
        self.play(type_in(sub1, run_time=0.6))
        self.at_clip("S3-c03")
        self.play(type_in(c2_sub, run_time=0.8))
        self.at_clip("S3-c04")
        self.emphasize(c2, run_time=0.6)  # 2/5
        self.at_clip("S3-c05")
        sub3 = t("按固定系数缩放", 28, MUTED).move_to((c3.get_bottom() + core.get_top()) / 2)
        self.play(type_in(sub3, run_time=0.6))
        self.at_clip("S3-c06")
        self.play(type_in(core, run_time=0.8))
        self.at_clip("S3-c07")
        self.play(FadeOut(head), FadeOut(page1), FadeOut(sub1), FadeOut(sub3), run_time=0.5)

        # 页2：SVD 不可行 → NS 迭代公式 + 调音师图
        head2 = t("精确解：SVD", 38, YELL, "BOLD").to_edge(UP, buff=1.2)
        svd_card = _card("每步做 SVD 不可行", 6.6, 1.9, WHITE, WHITE, 40, CARD_FILL, "BOLD")
        img = ImageMobject(str(IMG / "s3-tuner-round.png"))
        img.scale_to_fit_width(4.6)
        f1 = t("X", 56, YELL, "BOLD")
        f2 = t("←", 44, WHITE, "BOLD")
        f3 = t("½X(3 - ", 44, WHITE, "BOLD")
        x2 = sup("X", "2", 44, 24, YELL)
        f4 = t(")", 44, WHITE, "BOLD")
        formula = VGroup(f1, f2, f3, x2, f4).arrange(RIGHT, buff=0.25)
        cap = t("Newton-Schulz 迭代", 30, GREEN, "BOLD")
        page2 = page_stack(svd_card, img, formula, cap, buff=0.7)
        layout_page(page2)

        self.play(type_in(head2, run_time=1.1))
        self.wait(0.1)
        self.play_scroll_unroll(svd_card, run_time=1.2)
        self.at_clip("S3-c08")
        cross = self.play_red_cross(svd_card, run_time=0.65)  # 主视觉
        self.play(FadeOut(head2), FadeOut(svd_card), FadeOut(cross),
                  FadeIn(img, shift=DOWN * 0.05), run_time=0.6)
        self.play(FadeIn(formula, scale=1.05), run_time=0.6)  # 公式用 FadeIn 合规
        self.at_clip("S3-c09")
        self.play(type_in(cap, run_time=0.8))
        self.at_clip("S3-c10")
        self.play(FadeOut(img), FadeOut(formula), FadeOut(cap), run_time=0.5)

        # 页3：奇异值条带对齐（矮页自动排版）
        head3 = t("奇异值被拧向 1", 38, YELL, "BOLD").to_edge(UP, buff=1.2)
        widths = [0.9, 1.3, 1.7, 2.1, 2.5]
        bars = VGroup(*[Rectangle(width=w, height=0.9, color=CYAN,
                                  fill_color=CYAN, fill_opacity=0.7) for w in widths])
        bars.arrange(RIGHT, buff=0.35)
        lab_small = t("小于 1：放大", 30, GREEN, "BOLD")
        lab_big = t("大于 1：压缩", 30, RED, "BOLD")
        labs = VGroup(lab_small, lab_big).arrange(RIGHT, buff=1.4)
        done = t("全部拧向 1", 40, YELL, "BOLD")
        page3 = page_auto(bars, labs, done)

        self.play(type_in(head3, run_time=1.1))
        self.play_parallel(*[Create(b) for b in bars], run_time=1.0, lag_ratio=0.2)  # 主视觉
        self.play_parallel(type_in(lab_small, run_time=0.6), type_in(lab_big, run_time=0.6),
                           run_time=0.6)
        self.at_clip("S3-c11")
        targets = VGroup(*[Rectangle(width=1.7, height=0.9, color=YELL,
                                     fill_color=YELL, fill_opacity=0.7) for _ in bars])
        targets.arrange(RIGHT, buff=0.35)
        self.play(*[Transform(b, tg) for b, tg in zip(bars, targets)], run_time=1.0)
        self.wait(0.1)
        self.play(type_in(done, run_time=0.8))
        self.at_clip("S3-c12")
        self.play(FadeOut(head3), FadeOut(page3), run_time=0.5)

        # 页4：二阶收敛数字链（矮页自动排版）
        head4 = t("误差平方衰减", 38, YELL, "BOLD").to_edge(UP, buff=1.2)
        n1 = t("0.1", 40, WHITE, "BOLD")
        n2 = t("0.01", 40, WHITE, "BOLD")
        n3 = t("0.0001", 40, WHITE, "BOLD")
        n4 = t("1e-8", 40, YELL, "BOLD")
        nums = VGroup(n1, n2, n3, n4).arrange(RIGHT, buff=0.7)
        ar1 = Arrow(n1.get_right(), n2.get_left(), color=MUTED, buff=0.12, stroke_width=5)
        ar2 = Arrow(n2.get_right(), n3.get_left(), color=MUTED, buff=0.12, stroke_width=5)
        ar3 = Arrow(n3.get_right(), n4.get_left(), color=MUTED, buff=0.12, stroke_width=5)
        chain = VGroup(nums, ar1, ar2, ar3)
        note1 = t("误差平方衰减", 32, WHITE, "BOLD")
        note2 = t("前慢后快，第四步到机器精度", 30, MUTED)
        page4 = page_auto(chain, note1, note2)

        self.play(type_in(head4, run_time=1.1))
        self.wait(0.1)
        self.play(type_in(n1, run_time=0.5))
        self.at_clip("S3-c13")
        self.play(type_in(n2, run_time=0.5), Create(ar1), run_time=0.6)
        self.play(type_in(n3, run_time=0.5), Create(ar2), run_time=0.6)
        self.play(type_in(n4, run_time=0.5), Create(ar3), run_time=0.6)  # 主视觉
        self.emphasize(n4, run_time=0.6)  # 3/5
        self.play(type_in(note1, run_time=0.8))
        self.wait(0.1)
        self.play(type_in(note2, run_time=0.8))
        self.at_clip("S3-c14")
        self.play(FadeOut(head4), FadeOut(page4), run_time=0.5)

        # 页5：爆点 + 悬念（矮页）
        card = _card("所以只要 5 次迭代", 6.8, 1.9, YELL, WHITE, 44, CARD_FILL, "BOLD")
        q = t("这 5 次，够吗？", 56, YELL, "BOLD")
        page_auto(card, q)
        self.play_scroll_unroll(card, run_time=1.2)
        self.at_clip("S3-c15")
        self.play(type_in(q, run_time=0.9))
        self.wait(0.4)
        self.transition_out(f, card, q)
        self.pad_to_voice()


# ---------------- S4 双实验验证 ----------------
class S4(_Base):
    def construct(self):
        self.bg()
        f = _footer(self)

        # 页1：实验一
        head = t("实验一：NS 收敛性", 38, YELL, "BOLD").to_edge(UP, buff=1.2)
        c1 = _card("条件数 κ = 3 的矩阵", 6.6, 1.8, CYAN, WHITE, 40, CARD_FILL, "BOLD")
        lab = t("5 次迭代后偏离", 34, WHITE, "BOLD")
        slot = dynamic_slot(2.4, 0.9)
        row = stable_row(lab, slot, buff=0.4)
        note1 = t("κ < 10 只需 5 次迭代", 28, MUTED)
        note2 = t("κ > 200 要 11 步", 28, MUTED)
        page1 = page_stack(c1, row, note1, note2, buff=1.2)
        layout_page(page1)

        self.at_clip("S4-c01")
        self.play(type_in(head, run_time=1.1))
        self.wait(0.1)
        self.play_scroll_unroll(c1, run_time=1.2)  # 主视觉
        self.at_clip("S4-c02")
        self.play(type_in(lab, run_time=0.8))
        self.at_clip("S4-c03")
        n8 = t("1e-8", 56, GREEN, "BOLD").move_to(slot.get_center())
        self.play(type_in(n8, run_time=0.5))
        self.wait(0.1)
        self.play(type_in(note1, run_time=0.8))
        self.wait(0.1)
        self.play(type_in(note2, run_time=0.8))
        self.at_clip("S4-c04")
        self.play(FadeOut(head), FadeOut(page1), FadeOut(n8), run_time=0.5)

        # 页2：实验二 窄谷轨迹
        head2 = t("实验二：窄谷走 60 步", 38, YELL, "BOLD").to_edge(UP, buff=1.2)
        img = ImageMobject(str(IMG / "s4-valley-round.png"))
        img.scale_to_fit_width(3.2)
        a_lab = t("Adam 首步偏 47.4°", 34, RED, "BOLD")
        m_lab = t("Muon 只偏 0.6°", 34, GREEN, "BOLD")
        m_sub = t("几乎正对最优点", 30, WHITE)
        page2 = page_stack(img, a_lab, m_lab, m_sub, buff=0.6)
        layout_page(page2)

        self.play(type_in(head2, run_time=1.1), FadeIn(img, shift=DOWN * 0.05), run_time=1.1)
        self.at_clip("S4-c05")
        self.play(type_in(a_lab, run_time=0.8))  # 主视觉
        self.at_clip("S4-c06")
        self.play(type_in(m_lab, run_time=0.8))
        self.wait(0.1)
        self.play(type_in(m_sub, run_time=0.8))
        self.at_clip("S4-c07")
        self.play(FadeOut(head2), FadeOut(page2), run_time=0.5)

        # 页3：诚实说明 + 悬念
        head3 = t("说句实话", 38, YELL, "BOLD").to_edge(UP, buff=1.2)
        c2 = _card("机制演示，不是性能基准", 6.8, 1.9, WHITE, WHITE, 40, CARD_FILL, "BOLD")
        c3 = _card("真实收益以 Moonlight / Kimi K2 论文为准", 6.8, 1.9, CYAN, WHITE, 36, CARD_FILL)
        q = t("那 V4 自己，怎么落地？", 48, YELL, "BOLD")
        page3 = page_stack(c2, c3, q, buff=1.35)
        layout_page(page3)

        self.play(type_in(head3, run_time=1.1))
        self.wait(0.1)
        self.play_scroll_unroll(c2, run_time=1.2)  # 主视觉
        self.at_clip("S4-c08")
        self.play_scroll_unroll(c3, run_time=1.2)
        self.at_clip("S4-c09")
        self.play(type_in(q, run_time=0.9))
        self.wait(0.4)
        self.transition_out(f, head3, c2, c3, q)
        self.pad_to_voice()


# ---------------- S5 V4 落地：分组 + 0.18 + expert collapse ----------------
class S5(_Base):
    def construct(self):
        self.bg()
        f = _footer(self)

        # 页1：分组表
        head = t("V4 怎么落地？", 38, YELL, "BOLD").to_edge(UP, buff=1.2)
        big = _card("绝大多数参数 → Muon", 6.8, 2.2, YELL, WHITE, 42, CARD_FILL, "BOLD")
        c1 = _card("embedding → AdamW", 2.1, 1.8, CYAN, WHITE, 28, CARD_FILL, "BOLD")
        c2 = _card("输出层 → AdamW", 2.1, 1.8, CYAN, WHITE, 28, CARD_FILL, "BOLD")
        c3 = _card("RMSNorm → AdamW", 2.1, 1.8, CYAN, WHITE, 28, CARD_FILL, "BOLD")
        smalls = VGroup(c1, c2, c3).arrange(RIGHT, buff=0.4)
        note = t("正交化对象是矩阵", 32, WHITE, "BOLD")
        note2 = t("查表和一维向量用不上", 28, MUTED)
        page1 = page_stack(big, smalls, note, note2, buff=0.9)
        layout_page(page1)

        self.at_clip("S5-c01")
        self.play(type_in(head, run_time=1.1))
        self.at_clip("S5-c02")
        self.play_scroll_unroll(big, run_time=1.2)  # 主视觉
        self.at_clip("S5-c03")
        self.play_scroll_unroll_many(c1, c2, c3, run_time=1.2)
        self.at_clip("S5-c04")
        self.play(type_in(note, run_time=0.8))
        self.at_clip("S5-c05")
        self.play(type_in(note2, run_time=0.8))
        self.play(FadeOut(head), FadeOut(page1), run_time=0.5)

        # 页2：RMS 0.18（矮页自动排版）
        head2 = t("复用 AdamW 学习率", 38, YELL, "BOLD").to_edge(UP, buff=1.2)
        lab2 = t("每个更新矩阵 RMS 缩放到", 34, WHITE, "BOLD")
        slot2 = dynamic_slot(2.0, 0.9)
        row2 = stable_row(lab2, slot2, buff=0.4)
        note3 = t("对齐 AdamW 更新幅度（Kimi K2 取 0.2）", 28, MUTED)
        note4 = t("momentum 0.95 · weight decay 0.1", 28, MUTED)
        page2 = page_auto(row2, note3, note4)

        self.play(type_in(head2, run_time=1.1))
        self.at_clip("S5-c06")
        self.play(type_in(lab2, run_time=0.8))
        self.wait(0.1)
        cnt = self.counter_value(0, 0.18, decimals=2, size=56, color=YELL,
                                 anchor=slot2, run_time=1.0)  # 主视觉
        self.at_clip("S5-c07")
        self.play(type_in(note3, run_time=0.8))
        self.wait(0.1)
        self.play(type_in(note4, run_time=0.8))
        self.at_clip("S5-c08")
        self.play(FadeOut(head2), FadeOut(page2), FadeOut(cnt), run_time=0.5)

        # 页3：256 专家网格
        head3 = t("按 expert 分块", 38, YELL, "BOLD").to_edge(UP, buff=1.2)
        cells = VGroup(*[Rectangle(width=0.42, height=0.42, color=CYAN,
                                   fill_color=CYAN, fill_opacity=0.55) for _ in range(64)])
        cells.arrange_in_grid(8, 8, buff=0.12)
        lab3 = t("256 个专家矩阵各自独立 NS", 34, WHITE, "BOLD")
        lab3b = t("完美并行 · 条件数天然可控", 30, GREEN, "BOLD")
        page3 = page_stack(cells, lab3, lab3b, buff=1.05)
        layout_page(page3)

        self.play(type_in(head3, run_time=1.1))
        self.wait(0.1)
        self.play(*[FadeIn(c, scale=0.5) for c in cells], run_time=1.0, lag_ratio=0.05)  # 主视觉
        self.at_clip("S5-c09")
        self.play(type_in(lab3, run_time=0.8))
        self.wait(0.1)
        self.play(type_in(lab3b, run_time=0.8))
        self.play(FadeOut(head3), FadeOut(page3), run_time=0.5)

        # 页4：expert collapse 压制
        head4 = t("漂亮的副作用", 38, YELL, "BOLD").to_edge(UP, buff=1.2)
        hot_lab = t("热门专家", 32, WHITE, "BOLD")
        hot_bar = Rectangle(width=3.4, height=1.0, color=RED, fill_color=RED, fill_opacity=0.6)
        cold_lab = t("冷门专家", 32, WHITE, "BOLD")
        cold_bar = Rectangle(width=3.4, height=1.0, color=GREEN, fill_color=GREEN, fill_opacity=0.6)
        row_h = stable_row(hot_lab, hot_bar, buff=0.5)
        row_c = stable_row(cold_lab, cold_bar, buff=0.5)
        eq = t("更新范数完全相等", 40, YELL, "BOLD")
        concl = _card("从优化器层面压制 expert collapse", 6.8, 1.8, GREEN, WHITE, 36, CARD_FILL, "BOLD")
        page4 = page_stack(row_h, row_c, eq, concl, buff=0.95)
        layout_page(page4)

        self.play(type_in(head4, run_time=1.1))
        self.play_parallel(type_in(hot_lab, run_time=0.6), FadeIn(hot_bar, shift=DOWN * 0.05),
                           type_in(cold_lab, run_time=0.6), FadeIn(cold_bar, shift=DOWN * 0.05),
                           run_time=0.8)  # 主视觉
        self.at_clip("S5-c10")
        self.play(type_in(eq, run_time=0.8))
        self.emphasize(eq, run_time=0.6)  # 4/5
        self.at_clip("S5-c11")
        self.play_scroll_unroll(concl, run_time=1.2)
        self.at_clip("S5-c12")
        q = t("可这套激进设计，真能训稳吗？", 48, YELL, "BOLD")
        page_auto(q)
        self.play(FadeOut(head4), FadeOut(page4), type_in(q), run_time=0.9)
        self.wait(0.3)
        self.transition_out(f, q)
        self.pad_to_voice()


# ---------------- S6 回扣 + MuonClip + 品牌尾卡 ----------------
class S6(_Base):
    def construct(self):
        self.bg()
        f = _footer(self)

        # 页1：3TB vs 3.2TB
        head = t("省下的 3TB 去哪了", 38, YELL, "BOLD").to_edge(UP, buff=1.2)
        lab1 = t("省下的优化器状态", 28, WHITE, "BOLD")
        bar1 = Rectangle(width=2.2, height=1.4, color=YELL, fill_color=YELL, fill_opacity=0.7)
        slot1 = dynamic_slot(1.6, 0.8)
        row1 = stable_row(lab1, bar1, slot1, buff=0.35)
        lab2 = t("V4-Pro 全部权重", 28, WHITE, "BOLD")
        bar2 = Rectangle(width=2.4, height=1.4, color=CYAN, fill_color=CYAN, fill_opacity=0.7)
        slot2 = dynamic_slot(1.6, 0.8)
        row2 = stable_row(lab2, bar2, slot2, buff=0.35)
        concl = t("够再放一套完整模型", 40, GREEN, "BOLD")
        note = t("BF16 单份存储", 28, MUTED)
        page1 = page_stack(row1, row2, concl, note, buff=1.2)
        layout_page(page1)

        self.at_clip("S6-c01")
        self.play_parallel(type_in(head, run_time=1.0), type_in(lab1, run_time=0.6),
                           run_time=1.0)
        self.at_clip("S6-c02")
        self.grow_bar(bar1, ValueTracker(0), 2.2, run_time=1.0, anchor="center")  # 主视觉
        self.wait(0.1)
        cnt1 = self.counter_value(0, 3, suffix=" TB", size=36, color=YELL, anchor=slot1, run_time=0.9)
        self.at_clip("S6-c03")
        self.grow_bar(bar2, ValueTracker(0), 2.4, run_time=1.0, anchor="center",
                      extra_anims=[type_in(lab2, run_time=0.6)])
        self.wait(0.1)
        cnt2 = self.counter_value(0, 3.2, decimals=1, suffix=" TB", size=36, color=CYAN,
                                  anchor=slot2, run_time=0.9)
        self.at_clip("S6-c04")
        self.play(type_in(concl, run_time=0.9))
        self.wait(0.1)
        self.play(type_in(note, run_time=0.8))
        self.at_clip("S6-c05")
        self.play(FadeOut(head), FadeOut(page1), FadeOut(cnt1), FadeOut(cnt2), run_time=0.5)

        # 页2：Kimi K2 + QK-Clip
        head2 = t("Kimi K2：推到极致", 38, YELL, "BOLD").to_edge(UP, buff=1.2)
        c1 = _card("1 万亿参数 · 15.5 万亿 token", 6.8, 1.8, CYAN, WHITE, 38, CARD_FILL, "BOLD")
        c2 = _card("零 loss spike", 6.8, 1.6, GREEN, WHITE, 40, CARD_FILL, "BOLD")
        c3 = _card("QK-Clip：锁住注意力 logits", 6.8, 1.8, YELL, WHITE, 36, CARD_FILL, "BOLD")
        c3_sub = t("超过阈值 100 就按比例缩放", 28, MUTED)
        page2 = page_stack(c1, c2, c3, c3_sub, buff=0.6)
        layout_page(page2)

        self.play(type_in(head2, run_time=1.1))
        self.wait(0.1)
        self.play_scroll_unroll_many(c1, c2, run_time=1.2)  # 主视觉
        self.at_clip("S6-c06")
        self.play_scroll_unroll(c3, run_time=1.2)
        self.at_clip("S6-c07")
        self.play(type_in(c3_sub, run_time=0.8))
        self.at_clip("S6-c08")
        red_lab = t("防止满秩更新让 logits 爆炸", 30, RED, "BOLD")
        self.play(type_in(red_lab, run_time=0.8))
        self.at_clip("S6-c09")
        concl2 = t("收敛更快，训练更稳", 44, YELL, "BOLD")
        page_auto(concl2)
        self.play(FadeOut(head2), FadeOut(page2), FadeOut(red_lab), type_in(concl2), run_time=0.9)
        self.emphasize(concl2, run_time=0.6)  # 5/5
        self.at_clip("S6-c10")
        self.play(FadeOut(concl2), run_time=0.4)

        # 页3：品牌尾卡（终幕，不转场）
        avatar = ImageMobject(str(AVATAR))
        avatar.scale_to_fit_width(2.4)
        follow = t("关注「数解AI」", 40, YELL, "BOLD")
        title = t("《Muon 怎么省一半显存？优化器只记一份账》", 30, WHITE, "BOLD")
        if title.width > FW * 0.8:
            title.set_width(FW * 0.8)
        guide = t("查看公众号文章", 28, GREEN, "BOLD")
        next_lab = t("下一篇：mHC——61 层网络为什么「传话传没」", 24, MUTED)
        aq = t("省下的算力，你希望 DeepSeek 拿去干嘛？\n回复更快，还是上下文更长？评论区聊聊", 22, MUTED)
        page3 = page_stack(avatar, follow, title, guide, next_lab, aq, buff=0.6)
        layout_page(page3)

        self.play_parallel(FadeIn(avatar, scale=1.5), type_in(follow, run_time=0.8),
                           type_in(title, run_time=0.9), run_time=0.9)
        self.at_clip("S6-c11")
        self.play_parallel(type_in(guide, run_time=0.7), type_in(next_lab, run_time=0.8),
                           run_time=0.8)
        self.at_clip("S6-c12")
        self.play(type_in(aq, run_time=0.9))
        self.pad_to_voice()
