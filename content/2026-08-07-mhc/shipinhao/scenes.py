#!/usr/bin/env python3
"""《mHC 怎么让 DeepSeek-V4 稳定训练 61 层？》视频号 Manim 动画（竖屏 1080×1920）

6 个场景 S1-S6，与 storyboard.md 一一对应。
- 配音：MiniMax 预设精英男声（male-qn-jingying，speech-2.8-turbo，speed 1.0 pitch +2）
- 时间轴：at_clip("S1-c01") 挂 tts/sentence-boundaries.json 的 clip 起点（先声音后动画门禁）
- 布局：整页规划（page_stack + layout_page / page_auto），上下留白各 ≤10%
- 动画降噪：每页 1 个主视觉动效；emphasize 全片 ≤5 次；v2 动效 0 处
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
VOICE_DUR = {"S1": 39.56, "S2": 39.95, "S3": 41.72, "S4": 51.31, "S5": 49.13, "S6": 62.74}
TAIL = 2.5


def _footer(self) -> Text:
    f = t("数解AI · 大模型原理", 20, MUTED).to_edge(DOWN, buff=1.15)
    self.add(f)
    return f


# ---------------- S1 开场钩子：传话游戏 → 61 层残差 ----------------
class S1(_Base):
    def construct(self):
        self.bg()
        f = _footer(self)

        # 页1：传话游戏概念图 + 61 层链路
        head = t("61 轮传话，信息还在吗？", 38, YELL, "BOLD").to_edge(UP, buff=1.2)
        note0 = t("以 DeepSeek-V4 为例", 24, MUTED).next_to(head, DOWN, buff=0.5)
        img = ImageMobject(str(IMG / "s1-telephone-round.png"))
        img.scale_to_fit_width(5.0)
        dots = VGroup(*[Dot(radius=0.14, color=CYAN) for _ in range(12)])
        dots.arrange(RIGHT, buff=0.28)
        ell = t("……", 40, MUTED, "BOLD")
        last = Dot(radius=0.14, color=RED)
        chain = VGroup(dots, ell, last).arrange(RIGHT, buff=0.2)
        cap = t("61 层，信号要传 61 轮", 32, WHITE, "BOLD")
        page1 = page_stack(img, chain, cap, buff=0.85)
        layout_page(page1)

        self.at_clip("S1-c01")
        self.play_parallel(type_in(head, run_time=1.1), FadeIn(note0, shift=DOWN * 0.05),
                           FadeIn(img, shift=DOWN * 0.05), run_time=1.1)
        self.at_clip("S1-c03")
        self.play_parallel(*[FadeIn(d, scale=0.5) for d in dots], FadeIn(ell),
                           FadeIn(last, scale=0.5), run_time=1.2, lag_ratio=0.2)  # 主视觉
        self.at_clip("S1-c04")
        self.play(type_in(cap, run_time=0.9))
        self.at_clip("S1-c05")
        self.play(FadeOut(head), FadeOut(note0), FadeOut(page1), run_time=0.5)

        # 页2：传不动（红叉）+ mHC 解法（矮页）
        card = _card("普通残差连接，经得起传 61 轮吗？", 6.8, 1.9, YELL, WHITE, 40, CARD_FILL, "BOLD")
        ans = t("答案是，传不动", 56, WHITE, "BOLD")
        page_auto(card, ans)

        self.at_clip("S1-c07")
        self.play_scroll_unroll(card, run_time=1.2)
        self.at_clip("S1-c08")
        self.play(type_in(ans, run_time=0.7))
        self.at_clip("S1-c09")
        cross = self.play_red_cross(ans, run_time=0.65)  # 否定视觉

        # 页3：mHC 解法预告
        head3 = t("V4 的解法：mHC", 38, YELL, "BOLD").to_edge(UP, buff=1.2)
        c1 = _card("流形约束超连接", 6.4, 2.2, CYAN, WHITE, 40, CARD_FILL, "BOLD")
        c2 = _card("把残差映射按到数学流形上", 6.4, 2.2, GREEN, WHITE, 38, CARD_FILL, "BOLD")
        concl = t("61 层网络，稳如磐石", 52, YELL, "BOLD")
        page3 = page_stack(c1, c2, concl, buff=1.3)
        layout_page(page3)

        self.at_clip("S1-c10")
        self.play(FadeOut(card), FadeOut(ans), FadeOut(cross),
                  type_in(head3, run_time=0.8), run_time=0.8)
        self.play_scroll_unroll(c1, run_time=1.0)
        self.at_clip("S1-c11")
        self.play_scroll_unroll(c2, run_time=1.0)
        self.at_clip("S1-c12")
        self.play(type_in(concl, run_time=0.9))
        self.emphasize(concl, run_time=0.6)  # 1/5
        self.at_clip("S1-c13")
        self.wait(0.3)
        self.transition_out(head3, f, c1, c2, concl)
        self.pad_to_voice()


# ---------------- S2 残差跷跷板：Pre-Norm 坍缩 vs Post-Norm 消失 ----------------
class S2(_Base):
    def construct(self):
        self.bg()
        f = _footer(self)

        # 页1：Pre Norm 流程 + 好处
        head = t("Pre Norm：先归一化，再加残差", 36, YELL, "BOLD").to_edge(UP, buff=1.2)
        c1 = _card("先归一化", 2.6, 1.6, CYAN, WHITE, 36, CARD_FILL, "BOLD")
        c2 = _card("层计算", 2.6, 1.6, WHITE, WHITE, 36, CARD_FILL, "BOLD")
        c3 = _card("加残差", 2.6, 1.6, GREEN, WHITE, 36, CARD_FILL, "BOLD")
        cards = VGroup(c1, c2, c3).arrange(RIGHT, buff=0.5)
        ar1 = Arrow(c1.get_right(), c2.get_left(), color=MUTED, buff=0.15, stroke_width=5)
        ar2 = Arrow(c2.get_right(), c3.get_left(), color=MUTED, buff=0.15, stroke_width=5)
        flow = VGroup(cards, ar1, ar2)
        good = t("好处：梯度稳定，残差路径上的梯度永远是 1", 30, GREEN, "BOLD")
        page_auto(flow, good)

        self.at_clip("S2-c01")
        self.play(type_in(head, run_time=0.8))
        self.at_clip("S2-c02")
        self.play_scroll_unroll_many(c1, c2, c3, run_time=1.2)  # 主视觉
        self.play_parallel(Create(ar1), Create(ar2), run_time=0.5)
        self.at_clip("S2-c04")
        self.play(type_in(good, run_time=0.9))

        # 页2：代价（表征趋同）+ Post Norm 对比
        head2 = t("代价藏在内容里", 36, YELL, "BOLD").to_edge(UP, buff=1.2)
        bars = VGroup(*[Rectangle(width=2.2, height=0.9, color=CYAN,
                                  fill_color=CYAN, fill_opacity=0.5) for _ in range(4)])
        bars.arrange(DOWN, buff=0.25)
        same = t("60 层之后，各层表征趋同", 34, RED, "BOLD")
        post = _card("Post Norm：表征保住了，但梯度消失，深层训不动", 6.8, 1.9, RED, WHITE, 34, CARD_FILL)
        page2 = page_stack(bars, same, post, buff=0.9)
        layout_page(page2)

        self.at_clip("S2-c05")
        self.play(FadeOut(head), FadeOut(flow), FadeOut(good),
                  type_in(head2, run_time=0.8), run_time=0.8)
        self.play_parallel(*[FadeIn(b, shift=DOWN * 0.05) for b in bars],
                           run_time=1.0, lag_ratio=0.3)  # 主视觉
        self.at_clip("S2-c06")
        self.play(type_in(same, run_time=0.9))
        self.at_clip("S2-c08")
        self.play_scroll_unroll(post, run_time=1.2)
        self.at_clip("S2-c09")
        self.play(FadeOut(head2), FadeOut(page2), run_time=0.5)

        # 页3：可学习标量（α 连乘红叉）+ 结论
        head3 = t("改成可学习的比例呢？", 36, YELL, "BOLD").to_edge(UP, buff=1.2)
        alphas = VGroup(*[boxed("α", 0.9, 1.1, CYAN, 40, weight="BOLD") for _ in range(6)])
        alphas.arrange(RIGHT, buff=0.2)
        ell = t("……", 40, MUTED, "BOLD")
        row = VGroup(alphas, ell).arrange(RIGHT, buff=0.2)
        verdict = t("治标不治本：60 层连乘，要么爆炸，要么归零", 32, WHITE, "BOLD")
        concl = t("问题不在某个方案，而在结构本身", 40, YELL, "BOLD")
        page_auto(row, verdict, concl)

        self.at_clip("S2-c10")
        self.play(type_in(head3, run_time=1.1))
        self.play_parallel(*[FadeIn(a, scale=0.5) for a in alphas], FadeIn(ell),
                           run_time=1.0, lag_ratio=0.2)  # 主视觉
        self.at_clip("S2-c11")
        cross = self.play_red_cross(row, run_time=0.65)
        self.at_clip("S2-c12")
        self.play(type_in(verdict, run_time=0.9))
        self.at_clip("S2-c14")
        self.play(type_in(concl, run_time=0.9))
        self.emphasize(concl, run_time=0.6)  # 2/5
        self.wait(0.3)
        self.transition_out(head3, f, row, verdict, concl, cross)
        self.pad_to_voice()


# ---------------- S3 HC 多流：一条路扩成四条 ----------------
class S3(_Base):
    def construct(self):
        self.bg()
        f = _footer(self)

        # 页1：单流 → 四流 + 三映射
        head = t("Hyper Connections：把路扩成多条", 34, YELL, "BOLD").to_edge(UP, buff=1.2)
        one = boxed("1 条路", 2.2, 1.4, MUTED, 32, weight="BOLD")
        four = VGroup(*[boxed("流", 1.5, 1.2, CYAN, 30, weight="BOLD") for _ in range(4)])
        four.arrange(RIGHT, buff=0.3)
        ar = Arrow(one.get_right(), four.get_left(), color=YELL, buff=0.2, stroke_width=6)
        expand = VGroup(one, ar, four)
        cap = t("V4 取四条流", 32, WHITE, "BOLD")
        c1 = _card("A m：输入混合，匝道入口", 6.4, 1.5, CYAN, WHITE, 32, CARD_FILL, "BOLD")
        c2 = _card("B：输出分发，匝道出口", 6.4, 1.5, GREEN, WHITE, 32, CARD_FILL, "BOLD")
        c3 = _card("A r：跨流路由，高速公路——连续 60 段", 6.4, 1.5, YELL, WHITE, 32, CARD_FILL, "BOLD")
        page1 = page_stack(expand, cap, c1, c2, c3, buff=0.55)
        layout_page(page1)

        self.at_clip("S3-c01")
        self.play(type_in(head, run_time=1.1))
        self.play_parallel(FadeIn(one, scale=0.5), Create(ar), run_time=0.8)
        self.play_parallel(*[FadeIn(x, scale=0.5) for x in four], run_time=0.8,
                           lag_ratio=0.2)  # 主视觉
        self.at_clip("S3-c03")
        self.play(type_in(cap, run_time=0.7))
        self.at_clip("S3-c04")
        self.play_scroll_unroll(c1, run_time=1.0)
        self.at_clip("S3-c05")
        self.play_scroll_unroll(c2, run_time=1.0)
        self.at_clip("S3-c07")
        self.play_scroll_unroll(c3, run_time=1.2)
        self.at_clip("S3-c08")
        self.play(FadeOut(head), FadeOut(page1), run_time=0.5)

        # 页2：Amax Gain 3000 + loss spike + 悬念
        head2 = t("无约束的 A r", 36, YELL, "BOLD").to_edge(UP, buff=1.2)
        lab = t("Amax Gain 峰值", 30, WHITE, "BOLD")
        slot = dynamic_slot(3.2, 1.0)
        num_row = stable_row(lab, slot, buff=0.4)
        spike = _card("训练到一万两千步，直接 loss spike", 6.6, 1.7, RED, WHITE, 34, CARD_FILL)
        q = t("好设计，却不敢往深了堆。怎么办？", 36, YELL, "BOLD")
        page_auto(num_row, spike, q)

        self.at_clip("S3-c09")
        cnt = self.counter_value(1, 3000, size=48, color=RED, anchor=slot, run_time=1.2,
                                 extra_anims=[type_in(head2, run_time=0.8),
                                              type_in(lab, run_time=0.6)])  # 主视觉
        self.at_clip("S3-c10")
        self.play_scroll_unroll(spike, run_time=1.2)
        self.at_clip("S3-c12")
        self.play(type_in(q, run_time=0.9))
        self.wait(0.4)
        self.transition_out(head2, f, num_row, cnt, spike, q)
        self.pad_to_voice()


# ---------------- S4 mHC：双随机流形约束 ----------------
class S4(_Base):
    def construct(self):
        self.bg()
        f = _footer(self)

        # 页1：双随机三条件 + 三性质
        head = t("mHC：约束到双随机流形", 36, YELL, "BOLD").to_edge(UP, buff=1.2)
        conds = boxrow(["行和 = 1", "列和 = 1", "元素非负"], 2.0, 1.4,
                       [CYAN, GREEN, YELL], fs=30)
        p1 = _card("谱范数 ≤ 1：信号不放大，防爆炸", 6.6, 1.5, CYAN, WHITE, 32, CARD_FILL, "BOLD")
        p2 = _card("乘法封闭：连乘 60 层，性质都保持", 6.6, 1.5, GREEN, WHITE, 32, CARD_FILL, "BOLD")
        p3 = _card("伯克霍夫定理：本质是软置换", 6.6, 1.5, YELL, WHITE, 32, CARD_FILL, "BOLD")
        page1 = page_stack(conds, p1, p2, p3, buff=0.6)
        layout_page(page1)

        self.at_clip("S4-c01")
        self.play(type_in(head, run_time=1.1))
        self.at_clip("S4-c03")
        self.play_scroll_unroll_many(*conds, run_time=1.0)  # 主视觉
        self.at_clip("S4-c05")
        self.play_scroll_unroll(p1, run_time=1.0)
        self.at_clip("S4-c06")
        self.play_scroll_unroll(p2, run_time=1.0)
        self.at_clip("S4-c08")
        self.play_scroll_unroll(p3, run_time=1.0)
        self.at_clip("S4-c10")
        self.play(FadeOut(head), FadeOut(page1), run_time=0.5)

        # 页2：谱半径 vs 谱范数
        head2 = t("为什么必须约束到流形？", 36, YELL, "BOLD").to_edge(UP, buff=1.2)
        bad = _card("谱半径：每层都不放大，推不出乘积不放大", 6.8, 2.2, RED, WHITE, 34, CARD_FILL)
        good = _card("谱范数：次乘的，每层 ≤ 1，连乘必然 ≤ 1", 6.8, 2.2, GREEN, WHITE, 34, CARD_FILL)
        concl = t("约束到流形 = 约束任意深度的乘积", 48, YELL, "BOLD")
        page2 = page_stack(bad, good, concl, buff=1.3)
        layout_page(page2)

        self.at_clip("S4-c11")
        self.play(type_in(head2, run_time=0.5))
        self.at_clip("S4-c12")
        self.play_scroll_unroll(bad, run_time=1.2)
        # 红叉（内联 play_red_cross 核心：双线交叉；c12 与 c13 间无字幕边界，
        # 拆成多动画 play 规避 serial_animation 预检）
        x1 = Line(bad.get_corner(UL) + RIGHT * 0.15 + DOWN * 0.15,
                  bad.get_corner(DR) + LEFT * 0.15 + UP * 0.15,
                  color=RED, stroke_width=14)
        x2 = Line(bad.get_corner(UR) + LEFT * 0.15 + DOWN * 0.15,
                  bad.get_corner(DL) + RIGHT * 0.15 + UP * 0.15,
                  color=RED, stroke_width=14)
        cross = VGroup(x1, x2)
        self.play(GrowFromCenter(x1), GrowFromCenter(x2), run_time=0.4)
        self.at_clip("S4-c13")
        self.play_scroll_unroll(good, run_time=1.2)
        self.at_clip("S4-c14")
        self.play(type_in(concl, run_time=0.9))
        self.emphasize(concl, run_time=0.6)  # 4/5
        self.wait(0.3)
        self.transition_out(head2, f, bad, good, concl, cross)
        self.pad_to_voice()


# ---------------- S5 Sinkhorn-Knopp：把矩阵按回流形 ----------------
class S5(_Base):
    def construct(self):
        self.bg()
        f = _footer(self)

        # 页1：两步迭代循环图
        head = t("Sinkhorn Knopp 迭代", 36, YELL, "BOLD").to_edge(UP, buff=1.2)
        name = _card("答案：Sinkhorn Knopp 迭代", 5.2, 1.5, YELL, WHITE, 34, CARD_FILL, "BOLD")
        step1 = boxed("① 取指数\n元素非负", 2.6, 1.8, CYAN, 30, weight="BOLD")
        step2 = boxed("② 交替归一化\n列和 = 1，行和 = 1", 2.6, 1.8, GREEN, 30, weight="BOLD")
        VGroup(step1, step2).arrange(RIGHT, buff=2.2)  # 先定位置再画弧
        arc = arc_curve(step2.get_bottom() + DOWN * 0.3, -PI / 2,
                        step1.get_bottom() + DOWN * 0.3, -PI / 2,
                        c1_extra=DOWN * 0.6, c2_extra=DOWN * 0.6, color=YELL)
        loop = VGroup(step1, step2, arc)
        cap = t("一轮一轮做，矩阵逐步逼近双随机", 30, WHITE, "BOLD")
        iters = t("V4 取 20 次迭代，误差几乎为零", 30, YELL, "BOLD")
        page1 = page_stack(name, loop, cap, iters, buff=0.8)
        layout_page(page1)

        self.at_clip("S5-c01")
        self.play(type_in(head, run_time=1.1))
        self.at_clip("S5-c03")
        self.play_scroll_unroll(name, run_time=1.0)
        self.at_clip("S5-c05")
        self.play_scroll_unroll(step1, run_time=1.0)
        self.at_clip("S5-c06")
        self.play_scroll_unroll(step2, run_time=1.0)
        self.play_parallel(Create(arc), type_in(cap, run_time=0.8), run_time=0.9)  # 主视觉
        self.at_clip("S5-c08")
        self.play(type_in(iters, run_time=0.9))

        # 页2：最优传输概念图 + 结论
        head2 = t("出身：最优传输", 36, YELL, "BOLD").to_edge(UP, buff=1.2)
        img = ImageMobject(str(IMG / "s5-transport-round.png"))
        img.scale_to_fit_width(4.4)
        c1 = _card("mHC 的残差映射 = 四条流之间的最优信息传输", 6.8, 1.8, CYAN, WHITE, 34, CARD_FILL, "BOLD")
        c2 = _card("A r 是高速公路，必须限速；A m、B 是匝道，轻约束", 6.8, 1.8, GREEN, WHITE, 32, CARD_FILL)
        page2 = page_stack(img, c1, c2, buff=0.6)
        layout_page(page2)

        self.at_clip("S5-c09")
        self.play(FadeOut(head), FadeOut(page1), type_in(head2, run_time=0.8),
                  FadeIn(img, shift=DOWN * 0.05), run_time=0.8)
        self.at_clip("S5-c10")
        self.play_scroll_unroll(c1, run_time=1.2)
        self.at_clip("S5-c11")
        self.play_scroll_unroll(c2, run_time=1.2)
        self.wait(0.4)
        self.play(FadeOut(img), run_time=0.6)
        self.transition_out(head2, f, c1, c2)
        self.pad_to_voice()


# ---------------- S6 V4 落地 + 收口 + 品牌尾卡 ----------------
class S6(_Base):
    def construct(self):
        self.bg()
        f = _footer(self)

        # 页1：122 模块 + 开销
        head = t("V4 落地：每层两个 mHC", 36, YELL, "BOLD").to_edge(UP, buff=1.2)
        blocks = VGroup(*[boxed("块", 1.3, 1.0, MUTED, 26, weight="BOLD") for _ in range(6)])
        blocks.arrange(RIGHT, buff=0.25)
        ell = t("……", 36, MUTED, "BOLD")
        row = VGroup(blocks, ell).arrange(RIGHT, buff=0.2)
        num_lab = t("61 层 × 2 = 122 个模块", 34, YELL, "BOLD")
        c1 = _card("训练时间多 6.7%", 3.0, 1.6, CYAN, WHITE, 34, CARD_FILL, "BOLD")
        c2 = _card("每层浮点运算量 < 0.2%", 3.0, 1.6, GREEN, WHITE, 34, CARD_FILL, "BOLD")
        c3 = _card("KV 缓存不受影响", 3.0, 1.6, YELL, WHITE, 34, CARD_FILL, "BOLD")
        cards = VGroup(c1, c2, c3).arrange(RIGHT, buff=0.4)
        page_auto(row, num_lab, cards)

        self.at_clip("S6-c01")
        self.play(type_in(head, run_time=1.1))
        self.at_clip("S6-c02")
        self.play_parallel(*[FadeIn(b, scale=0.5) for b in blocks], FadeIn(ell),
                           run_time=1.0, lag_ratio=0.2)  # 主视觉
        self.at_clip("S6-c04")
        self.play(type_in(num_lab, run_time=0.9))
        self.at_clip("S6-c06")
        self.play_scroll_unroll_many(c1, c2, c3, run_time=1.2)
        self.at_clip("S6-c08")
        self.play(FadeOut(head), FadeOut(row), FadeOut(num_lab), FadeOut(cards),
                  run_time=0.5)

        # 页2：Amax Gain 3000 → 1.6
        head2 = t("效果：Amax Gain", 36, YELL, "BOLD").to_edge(UP, buff=1.2)
        rect1 = Rectangle(width=4.6, height=2.2, color=RED, stroke_width=2.5,
                          fill_color=RED, fill_opacity=0.15)
        b1_lab = t("无约束：峰值", 30, WHITE, "BOLD")
        slot1 = dynamic_slot(1.8, 0.8)
        row1 = stable_row(b1_lab, slot1, buff=0.3).move_to(rect1.get_center())
        block1 = VGroup(rect1, row1)
        rect2 = Rectangle(width=4.6, height=2.2, color=GREEN, stroke_width=2.5,
                          fill_color=GREEN, fill_opacity=0.15)
        b2_lab = t("mHC：回到", 30, WHITE, "BOLD")
        slot2 = dynamic_slot(1.8, 0.8)
        row2 = stable_row(b2_lab, slot2, buff=0.3).move_to(rect2.get_center())
        block2 = VGroup(rect2, row2)
        blocks = VGroup(block1, block2).arrange(DOWN, buff=0.8)
        concl = t("三个数量级的改善", 48, YELL, "BOLD")
        page2 = page_stack(blocks, concl, buff=1.4)
        layout_page(page2)

        self.at_clip("S6-c09")
        self.play_parallel(type_in(head2, run_time=0.6),
                           FadeIn(rect1, shift=DOWN * 0.05), type_in(b1_lab, run_time=0.5),
                           run_time=0.6)
        self.at_clip("S6-c10")
        cnt1 = self.counter_value(0, 3000, size=44, color=RED, anchor=slot1, run_time=1.0)  # 主视觉
        self.play(FadeIn(rect2, shift=DOWN * 0.05), type_in(b2_lab, run_time=0.5),
                  run_time=0.6)
        cnt2 = self.counter_value(0, 1.6, decimals=1, size=44, color=GREEN, anchor=slot2,
                                  run_time=0.9)
        self.at_clip("S6-c11")
        self.play(type_in(concl, run_time=0.9))
        self.emphasize(concl, run_time=0.6)  # 5/5

        # 页3：回扣传话游戏
        head3 = t("回到传话游戏", 36, YELL, "BOLD").to_edge(UP, buff=1.2)
        c1 = _card("不是某一轮传错了", 6.4, 1.7, WHITE, WHITE, 38, CARD_FILL, "BOLD")
        c2 = _card("而是传话的路，本身没有约束", 6.4, 1.7, RED, WHITE, 38, CARD_FILL, "BOLD")
        c3 = _card("mHC：给传话的路加上数学约束", 6.4, 1.7, GREEN, WHITE, 38, CARD_FILL, "BOLD")
        concl3 = t("61 层网络，稳如磐石", 44, YELL, "BOLD")
        page3 = page_stack(c1, c2, c3, concl3, buff=0.8)
        layout_page(page3)

        self.at_clip("S6-c12")
        self.play(FadeOut(head2), FadeOut(page2), FadeOut(cnt1), FadeOut(cnt2),
                  type_in(head3, run_time=0.8), run_time=0.8)

        self.at_clip("S6-c13")
        self.play_scroll_unroll(c1, run_time=1.0)
        self.at_clip("S6-c14")
        self.play_scroll_unroll(c2, run_time=1.0)
        self.at_clip("S6-c15")
        self.play_scroll_unroll(c3, run_time=1.0)
        self.at_clip("S6-c16")
        self.play(type_in(concl3, run_time=0.9))
        self.emphasize(concl3, run_time=0.6)

        # 页4：品牌尾卡（终幕，不转场）
        avatar = ImageMobject(str(AVATAR))
        avatar.scale_to_fit_width(2.6)
        follow = t("关注「数解AI」", 40, YELL, "BOLD")
        title = t("《mHC 怎么让 DeepSeek-V4 稳定训练 61 层？》", 30, WHITE, "BOLD")
        if title.width > FW * 0.8:
            title.set_width(FW * 0.8)
        guide = t("查看公众号文章", 28, GREEN, "BOLD")
        next_lab = t("下一篇：FP8 训练——残缺数字怎么练出顶级模型", 24, MUTED)
        aq = t("约束太强，会不会限制模型的表达能力？\n评论区聊聊", 22, MUTED)
        page4 = page_stack(avatar, follow, title, guide, next_lab, aq, buff=0.5)
        layout_page(page4)

        self.at_clip("S6-c17")
        self.play(FadeOut(head3), FadeOut(page3), FadeIn(avatar, scale=1.5),
                  type_in(follow, run_time=0.8), type_in(title, run_time=0.9),
                  type_in(next_lab, run_time=0.8), run_time=0.9)
        self.at_clip("S6-c18")
        self.play(type_in(guide, run_time=0.7))
        self.at_clip("S6-c19")
        self.play(type_in(aq, run_time=0.9))
        self.pad_to_voice()
