#!/usr/bin/env python3
"""《FP8训练：残缺数字怎么练出顶级模型》视频号 Manim 动画（竖屏 1080×1920）

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
VOICE_DUR = {"S1": 35.79, "S2": 47.21, "S3": 58.0, "S4": 47.28, "S5": 59.04, "S6": 78.38}
TAIL = 2.5


def _footer(self) -> Text:
    f = t("数解AI · 大模型原理", 20, MUTED).to_edge(DOWN, buff=1.15)
    self.add(f)
    return f


# ---------------- S1 开场钩子：记账游戏 → FP8 8 位数字 ----------------
class S1(_Base):
    def construct(self):
        self.bg()
        f = _footer(self)

        # 页1：记账游戏概念图 + 记账例子
        head = t("只用 1 到 10 记账，你敢吗？", 38, YELL, "BOLD").to_edge(UP, buff=1.2)
        note0 = t("以 FP8 训练为例", 24, MUTED).next_to(head, DOWN, buff=0.5)
        img = ImageMobject(str(IMG / "s1-ledger-round.png"))
        img.scale_to_fit_width(4.8)
        c1 = _card("8.6 → 写成 9", 3.0, 1.6, CYAN, WHITE, 36, CARD_FILL, "BOLD")
        c2 = _card("4.2 → 写成 4", 3.0, 1.6, GREEN, WHITE, 36, CARD_FILL, "BOLD")
        cards = VGroup(c1, c2).arrange(RIGHT, buff=0.5)
        page1 = page_stack(img, cards, buff=0.9)
        layout_page(page1)

        self.at_clip("S1-c01")
        self.play_parallel(type_in(head, run_time=1.1), FadeIn(note0, shift=DOWN * 0.05),
                           FadeIn(img, shift=DOWN * 0.05), run_time=1.1)
        self.at_clip("S1-c02")
        self.play_scroll_unroll_many(c1, c2, run_time=1.2)  # 主视觉
        self.at_clip("S1-c04")
        self.play(FadeOut(head), FadeOut(note0), FadeOut(page1), run_time=0.5)

        # 页2：8 位分配图（1 符号 + 4 指数 + 3 尾数）
        head2 = t("FP8：每个数字只占 8 位", 36, YELL, "BOLD").to_edge(UP, buff=1.2)
        s_bit = boxed("符号\n1 位", 1.8, 2.0, RED, 30, weight="BOLD")
        e_bit = boxed("指数\n4 位", 1.8, 2.0, CYAN, 30, weight="BOLD")
        m_bit = boxed("尾数\n3 位", 1.8, 2.0, GREEN, 30, weight="BOLD")
        bits = VGroup(s_bit, e_bit, m_bit).arrange(RIGHT, buff=0.4)
        steps = VGroup(*[Rectangle(width=0.9, height=0.7, color=YELL,
                                   fill_color=YELL, fill_opacity=0.6) for _ in range(8)])
        steps.arrange(RIGHT, buff=0.12)
        cap = t("3 位尾数：每个区间只有 8 个台阶", 30, WHITE, "BOLD")
        concl = t("数字天生就是残缺的", 40, YELL, "BOLD")
        page2 = page_stack(bits, steps, cap, concl, buff=1.3)
        layout_page(page2)

        self.at_clip("S1-c05")
        self.play(type_in(head2, run_time=1.1))
        self.at_clip("S1-c06")
        self.play_scroll_unroll_many(s_bit, e_bit, m_bit, run_time=1.2)  # 主视觉
        self.at_clip("S1-c08")
        self.play_parallel(*[FadeIn(s, scale=0.5) for s in steps], run_time=0.9,
                           lag_ratio=0.15)
        self.at_clip("S1-c09")
        self.play(type_in(concl, run_time=0.9))
        self.emphasize(concl, run_time=0.6)  # 1/5
        self.at_clip("S1-c10")
        self.play(FadeOut(head2), FadeOut(page2), run_time=0.5)

        # 页3：1.6T 参数 + 问题（矮页）
        card = _card("DeepSeek 用残缺数字，练出 1.6T 参数的顶级模型", 7.0, 2.0, YELL, WHITE, 38, CARD_FILL, "BOLD")
        q = t("残缺数字到底有多糙？", 48, YELL, "BOLD")
        q2 = t("误差从哪来？今天拆清楚", 30, MUTED)
        page_auto(card, q, q2)

        self.play_scroll_unroll(card, run_time=1.2)
        self.at_clip("S1-c12")
        self.play(type_in(q, run_time=0.9))
        self.at_clip("S1-c13")
        self.play(type_in(q2, run_time=0.8))
        self.wait(0.3)
        self.transition_out(f, card, q, q2)
        self.pad_to_voice()


# ---------------- S2 FP8 算术：E4M3 vs E5M2 ----------------
class S2(_Base):
    def construct(self):
        self.bg()
        f = _footer(self)

        # 页1：两种格式对比卡
        head = t("8 位怎么分？两种流派", 36, YELL, "BOLD").to_edge(UP, buff=1.2)
        c1 = _card("E4M3：4 指数 + 3 尾数\n最大 448 · 8 个台阶 · 精度约 6%", 6.6, 2.2, CYAN, WHITE, 34, CARD_FILL, "BOLD")
        c2 = _card("E5M2：5 指数 + 2 尾数\n范围大 · 4 个台阶 · 更粗糙", 6.6, 2.2, GREEN, WHITE, 34, CARD_FILL, "BOLD")
        memo = t("尾数决定多准，指数决定多大", 36, YELL, "BOLD")
        page1 = page_stack(c1, c2, memo, buff=1.4)
        layout_page(page1)

        self.at_clip("S2-c01")
        self.play(type_in(head, run_time=1.1))
        self.at_clip("S2-c04")
        self.play_scroll_unroll(c1, run_time=1.2)  # 主视觉
        self.at_clip("S2-c06")
        self.play_scroll_unroll(c2, run_time=1.2)
        self.at_clip("S2-c07")
        self.play(type_in(memo, run_time=0.9))
        self.emphasize(memo, run_time=0.6)  # 2/5

        # 页2：量化示例 + 5000 爆表
        head2 = t("真实数字过一遍", 36, YELL, "BOLD").to_edge(UP, buff=1.2)
        r1 = _card("0.67 → 0.6875（误差 2.6%）", 6.4, 1.7, CYAN, WHITE, 36, CARD_FILL, "BOLD")
        r2 = _card("200 → 192", 6.4, 1.7, GREEN, WHITE, 36, CARD_FILL, "BOLD")
        r3 = _card("5000 → 448 爆表（误差 91%）", 6.4, 1.7, RED, WHITE, 36, CARD_FILL, "BOLD")
        page2 = page_stack(r1, r2, r3, buff=1.2)
        layout_page(page2)

        self.at_clip("S2-c08")
        self.play(FadeOut(head), FadeOut(page1), type_in(head2, run_time=0.8),
                  run_time=0.8)
        self.play_scroll_unroll_many(r1, r2, run_time=1.2)
        self.at_clip("S2-c10")
        self.play_scroll_unroll(r3, run_time=1.2)
        self.at_clip("S2-c11")
        cross = self.play_red_cross(r3, run_time=0.65)
        self.at_clip("S2-c12")
        self.play(FadeOut(head2), FadeOut(page2), FadeOut(cross), run_time=0.5)

        # 页3：悬念（矮页）
        card = _card("记住这个记岔了的数字", 6.4, 1.8, YELL, WHITE, 40, CARD_FILL, "BOLD")
        q = t("一个 outlier，就能毁掉整张矩阵", 40, WHITE, "BOLD")
        page_auto(card, q)

        self.play_scroll_unroll(card, run_time=1.2)
        self.at_clip("S2-c13")
        self.play(type_in(q, run_time=0.9))
        self.wait(0.4)
        self.transition_out(f, card, q)
        self.pad_to_voice()


# ---------------- S3 深潜①：一个 outlier 毁掉整张图 ----------------
class S3(_Base):
    def construct(self):
        self.bg()
        f = _footer(self)

        # 页1：per-tensor 全局 scale 被 outlier 毁掉
        head = t("per tensor：一个 scale 管整块", 34, YELL, "BOLD").to_edge(UP, buff=1.2)
        normals = VGroup(*[Rectangle(width=1.1, height=0.55, color=CYAN,
                                     fill_color=CYAN, fill_opacity=0.5) for _ in range(6)])
        normals.arrange(RIGHT, buff=0.15)
        outlier = Rectangle(width=1.1, height=0.55, color=RED,
                            fill_color=RED, fill_opacity=0.7)
        row = VGroup(normals, outlier).arrange(RIGHT, buff=0.2)
        lab1 = t("正常值 ±0.03", 28, CYAN, "BOLD")
        lab2 = t("混进一个 5000 的 outlier", 28, RED, "BOLD")
        labs = VGroup(lab1, lab2).arrange(RIGHT, buff=1.2)
        bad = _card("scale 被拉到 11.2，正常值掉进次正规区间", 6.8, 1.8, RED, WHITE, 34, CARD_FILL)
        page_auto(row, labs, bad)

        self.at_clip("S3-c01")
        self.play(type_in(head, run_time=1.1))
        self.play_parallel(*[FadeIn(b, scale=0.5) for b in normals], run_time=0.9,
                           lag_ratio=0.15)  # 主视觉
        self.at_clip("S3-c02")
        self.play(FadeIn(outlier, scale=1.5), run_time=0.6)
        self.play_parallel(type_in(lab1, run_time=0.6), type_in(lab2, run_time=0.6),
                           run_time=0.6)
        self.at_clip("S3-c03")
        self.play_scroll_unroll(bad, run_time=1.2)
        self.at_clip("S3-c05")
        self.play(FadeOut(head), FadeOut(row), FadeOut(labs), FadeOut(bad), run_time=0.5)

        # 页2：62% 误差 + 分组量化解药
        head2 = t("一个 outlier，毁掉整张矩阵", 36, YELL, "BOLD").to_edge(UP, buff=1.2)
        num_lab = t("普通行误差", 32, WHITE, "BOLD")
        slot = dynamic_slot(2.4, 0.9)
        num_row = stable_row(num_lab, slot, buff=0.4)
        c1 = _card("解药：分组量化，每组独立算 scale", 6.8, 1.8, CYAN, WHITE, 34, CARD_FILL, "BOLD")
        c2 = _card("激活 1×128 组 · 权重 128×128 块", 6.8, 1.8, GREEN, WHITE, 34, CARD_FILL, "BOLD")
        c3 = _card("outlier 只毁掉自己那一组", 6.8, 1.8, WHITE, WHITE, 34, CARD_FILL, "BOLD")
        page2 = page_stack(num_row, c1, c2, c3, buff=0.7)
        layout_page(page2)

        self.at_clip("S3-c06")
        cnt = self.counter_value(0, 62, suffix="%", size=52, color=RED, anchor=slot,
                                 run_time=1.0,
                                 extra_anims=[type_in(head2, run_time=0.8),
                                              type_in(num_lab, run_time=0.6)])  # 主视觉
        self.at_clip("S3-c07")
        self.play_scroll_unroll(c1, run_time=1.0)
        self.at_clip("S3-c08")
        self.play_scroll_unroll(c2, run_time=1.0)
        self.at_clip("S3-c10")
        self.play_scroll_unroll(c3, run_time=1.0)
        self.at_clip("S3-c12")

        # 页3：62% → 2.6% 数字对比 + 悬念
        head3 = t("改善 24 倍", 36, YELL, "BOLD").to_edge(UP, buff=1.2)
        rect1 = Rectangle(width=4.6, height=1.9, color=RED, stroke_width=2.5,
                          fill_color=RED, fill_opacity=0.15)
        b1_lab = t("per tensor", 30, WHITE, "BOLD")
        slot1 = dynamic_slot(1.8, 0.8)
        row1 = stable_row(b1_lab, slot1, buff=0.3).move_to(rect1.get_center())
        block1 = VGroup(rect1, row1)
        rect2 = Rectangle(width=4.6, height=1.9, color=GREEN, stroke_width=2.5,
                          fill_color=GREEN, fill_opacity=0.15)
        b2_lab = t("per group", 30, WHITE, "BOLD")
        slot2 = dynamic_slot(1.8, 0.8)
        row2 = stable_row(b2_lab, slot2, buff=0.3).move_to(rect2.get_center())
        block2 = VGroup(rect2, row2)
        blocks = VGroup(block1, block2).arrange(DOWN, buff=0.8)
        q = t("分组粒度还带来第二个红利：scale 实时算", 30, MUTED)
        page_auto(blocks, q)

        self.play(FadeOut(head2), FadeOut(page2), FadeOut(cnt),
                  type_in(head3, run_time=0.8), run_time=0.8)
        self.play(FadeIn(rect1, shift=DOWN * 0.05), type_in(b1_lab, run_time=0.5),
                  run_time=0.6)
        cnt1 = self.counter_value(0, 62, suffix="%", size=44, color=RED, anchor=slot1,
                                  run_time=0.9)  # 主视觉
        self.play(FadeIn(rect2, shift=DOWN * 0.05), type_in(b2_lab, run_time=0.5),
                  run_time=0.6)
        cnt2 = self.counter_value(0, 2.6, decimals=1, suffix="%", size=44, color=GREEN,
                                  anchor=slot2, run_time=0.9)
        self.at_clip("S3-c13")
        self.play(type_in(q, run_time=0.9))
        self.wait(0.3)
        self.transition_out(head3, f, blocks, cnt1, cnt2, q)
        self.pad_to_voice()


# ---------------- S4 深潜②：量化网格跟着数据走 ----------------
class S4(_Base):
    def construct(self):
        self.bg()
        f = _footer(self)

        # 页1：delayed vs online 对比
        head = t("scale 从哪来？", 36, YELL, "BOLD").to_edge(UP, buff=1.2)
        c1 = _card("延迟量化：维护历史最大值，推断当前 scale", 6.8, 1.9, RED, WHITE, 34, CARD_FILL)
        c2 = _card("分布漂移 → 历史滞后 → 误差累积", 6.8, 1.9, RED, WHITE, 34, CARD_FILL)
        c3 = _card("在线量化：当场取最大值，当场算 scale", 6.8, 1.9, GREEN, WHITE, 34, CARD_FILL, "BOLD")
        page1 = page_stack(c1, c2, c3, buff=0.9)
        layout_page(page1)

        self.at_clip("S4-c01")
        self.play(type_in(head, run_time=1.1))
        self.at_clip("S4-c02")
        self.play_scroll_unroll(c1, run_time=1.2)  # 主视觉
        self.at_clip("S4-c03")
        self.play_scroll_unroll(c2, run_time=1.2)
        self.at_clip("S4-c05")
        self.play_scroll_unroll(c3, run_time=1.2)
        self.at_clip("S4-c07")
        self.play(FadeOut(head), FadeOut(page1), run_time=0.5)

        # 页2：网格伸缩 + 相机概念图
        head2 = t("量化网格是活的", 36, YELL, "BOLD").to_edge(UP, buff=1.2)
        img = ImageMobject(str(IMG / "s4-camera-round.png"))
        img.scale_to_fit_width(4.2)
        grid1 = VGroup(*[Rectangle(width=0.5, height=0.5, color=CYAN, stroke_width=2)
                         for _ in range(5)])
        grid1.arrange(RIGHT, buff=0.1)
        grid2 = VGroup(*[Rectangle(width=0.9, height=0.5, color=GREEN, stroke_width=2)
                         for _ in range(5)])
        grid2.arrange(RIGHT, buff=0.3)
        grids = VGroup(grid1, grid2).arrange(DOWN, buff=0.5)
        cap = t("分布变宽，网格拉开；变窄，网格收紧", 30, WHITE, "BOLD")
        page2 = page_stack(img, grids, cap, buff=0.7)
        layout_page(page2)

        self.at_clip("S4-c08")
        self.play_parallel(type_in(head2, run_time=1.1), FadeIn(img, shift=DOWN * 0.05),
                           run_time=1.1)
        self.play_parallel(*[FadeIn(g, scale=0.5) for g in grid1], run_time=0.8,
                           lag_ratio=0.15)  # 主视觉
        self.at_clip("S4-c09")
        self.play_parallel(*[FadeIn(g, scale=0.5) for g in grid2], run_time=0.8,
                           lag_ratio=0.15)
        self.at_clip("S4-c10")
        self.play(type_in(cap, run_time=0.9))
        self.at_clip("S4-c11")
        self.play(FadeOut(head2), FadeOut(page2), run_time=0.5)

        # 页3：澄清 + 悬念（矮页）
        card = _card("这不是损失缩放", 6.4, 1.8, YELL, WHITE, 40, CARD_FILL, "BOLD")
        sub = t("损失缩放是梯度缩放，防下溢；在线量化不需要它", 30, WHITE)
        q = t("那格式呢？前向反传，各用各的格式行不行？", 32, MUTED)
        page_auto(card, sub, q)

        self.play_scroll_unroll(card, run_time=1.2)
        self.at_clip("S4-c12")
        self.play(type_in(sub, run_time=0.9))
        self.at_clip("S4-c14")
        self.play(type_in(q, run_time=0.9))
        self.wait(0.4)
        self.transition_out(f, card, sub, q)
        self.pad_to_voice()


# ---------------- S5 E4M3 全用 + H800 的 14 位累加陷阱 ----------------
class S5(_Base):
    def construct(self):
        self.bg()
        f = _footer(self)

        # 页1：hybrid vs 全 E4M3
        head = t("前向反传，各用各的格式？", 34, YELL, "BOLD").to_edge(UP, buff=1.2)
        c1 = _card("混合方案：前向 E4M3 + 反传 E5M2", 6.8, 1.9, RED, WHITE, 34, CARD_FILL)
        c2 = _card("DeepSeek：全链路只用 E4M3", 6.8, 1.9, GREEN, WHITE, 34, CARD_FILL, "BOLD")
        c3 = _card("分组量化补上动态范围短板，E5M2 优势多余", 6.8, 1.9, CYAN, WHITE, 32, CARD_FILL)
        page1 = page_stack(c1, c2, c3, buff=0.9)
        layout_page(page1)

        self.at_clip("S5-c01")
        self.play(type_in(head, run_time=1.1))
        self.at_clip("S5-c02")
        self.play_scroll_unroll(c1, run_time=1.2)  # 主视觉
        self.at_clip("S5-c03")
        cross = self.play_red_cross(c1, run_time=0.65)
        self.at_clip("S5-c04")
        self.play_scroll_unroll(c2, run_time=1.2)
        self.at_clip("S5-c06")
        self.play_scroll_unroll(c3, run_time=1.2)
        self.at_clip("S5-c08")

        # 页2：14 位累加陷阱 + 128 拍结算
        head2 = t("第二个陷阱：14 位累加", 36, YELL, "BOLD").to_edge(UP, buff=1.2)
        c1 = _card("想当然：FP8 乘法 + FP32 累加，精度无忧", 6.8, 1.9, RED, WHITE, 34, CARD_FILL)
        c2 = _card("实测：H800 内部累加只保留约 14 位精度", 6.8, 1.9, RED, WHITE, 34, CARD_FILL)
        c3 = _card("解法：每 128 个元素，拷到 CUDA Core 用 FP32 累加", 6.8, 1.9, GREEN, WHITE, 32, CARD_FILL, "BOLD")
        c4 = _card("Tensor Core 快，但记性差；CUDA Core 慢，但记得准", 6.8, 1.9, YELL, WHITE, 32, CARD_FILL)
        page2 = page_stack(c1, c2, c3, c4, buff=0.6)
        layout_page(page2)

        self.play(FadeOut(head), FadeOut(page1), FadeOut(cross),
                  type_in(head2, run_time=0.8), run_time=0.8)
        self.play_scroll_unroll(c1, run_time=1.0)
        self.at_clip("S5-c11")
        self.play_scroll_unroll(c2, run_time=1.0)
        self.at_clip("S5-c13")
        self.play_scroll_unroll(c3, run_time=1.2)  # 主视觉
        self.at_clip("S5-c15")
        self.play_scroll_unroll(c4, run_time=1.2)
        self.at_clip("S5-c17")
        self.play(FadeOut(head2), FadeOut(page2), run_time=0.5)

        # 页3：悬念（矮页）
        card = _card("该省的省，不该省的绝不省", 6.8, 1.9, YELL, WHITE, 40, CARD_FILL, "BOLD")
        q = t("V3 的三重保险，到底保住了什么？", 36, WHITE, "BOLD")
        page_auto(card, q)

        self.play_scroll_unroll(card, run_time=1.2)
        self.at_clip("S5-c18")
        self.play(type_in(q, run_time=0.9))
        self.wait(0.4)
        self.transition_out(f, card, q)
        self.pad_to_voice()


# ---------------- S6 三重保险 + 0.25% 实证 + 收口 + 品牌尾卡 ----------------
class S6(_Base):
    def construct(self):
        self.bg()
        f = _footer(self)

        # 页1：三层保险
        head = t("V3 的三层保险", 36, YELL, "BOLD").to_edge(UP, buff=1.2)
        c1 = _card("① 主权重：永远是 FP32", 6.6, 1.7, CYAN, WHITE, 36, CARD_FILL, "BOLD")
        c2 = _card("② 高精度累加：每 128 个元素提升到 FP32", 6.6, 1.7, GREEN, WHITE, 34, CARD_FILL, "BOLD")
        c3 = _card("③ 选择性高精度：敏感算子保持 BF16", 6.6, 1.7, YELL, WHITE, 34, CARD_FILL, "BOLD")
        c4 = _card("该省的省：线性层占 80% 计算量，全部 FP8", 6.6, 1.7, WHITE, WHITE, 34, CARD_FILL)
        page1 = page_stack(c1, c2, c3, c4, buff=0.6)
        layout_page(page1)

        self.at_clip("S6-c01")
        self.play(type_in(head, run_time=1.1))
        self.at_clip("S6-c03")
        self.play_scroll_unroll(c1, run_time=1.0)
        self.at_clip("S6-c04")
        self.play_scroll_unroll(c2, run_time=1.0)
        self.at_clip("S6-c05")
        self.play_scroll_unroll(c3, run_time=1.0)
        self.at_clip("S6-c06")
        self.play_scroll_unroll(c4, run_time=1.0)  # 主视觉
        self.at_clip("S6-c07")
        self.play(FadeOut(head), FadeOut(page1), run_time=0.5)

        # 页2：0.25% 实证（loss 曲线重合）
        head2 = t("效果：误差 < 0.25%", 36, YELL, "BOLD").to_edge(UP, buff=1.2)
        axes = Axes(x_range=[0, 6, 1], y_range=[0, 4, 1], x_length=5.6, y_length=4.0,
                    axis_config={"color": MUTED, "stroke_width": 2})
        curve1 = axes.plot(lambda x: 3.2 - 0.5 * x + 0.08 * x * x, color=CYAN, stroke_width=4)
        curve2 = axes.plot(lambda x: 3.15 - 0.48 * x + 0.07 * x * x, color=GREEN, stroke_width=4)
        lab1 = t("FP8", 26, CYAN, "BOLD").next_to(curve1.get_end(), RIGHT, buff=0.2)
        lab2 = t("BF16", 26, GREEN, "BOLD").next_to(curve2.get_end(), RIGHT, buff=0.2)
        chart = VGroup(axes, curve1, curve2, lab1, lab2)
        num_lab = t("相对误差", 32, WHITE, "BOLD")
        slot = dynamic_slot(2.4, 0.9)
        num_row = stable_row(num_lab, slot, buff=0.4)
        note = t("160 亿和 2300 亿参数两个尺度", 28, MUTED)
        page2 = page_stack(chart, num_row, note, buff=1.0)
        layout_page(page2)

        self.at_clip("S6-c08")
        self.play(type_in(head2, run_time=1.1), Create(axes), run_time=1.1)
        self.at_clip("S6-c09")
        self.play_parallel(Create(curve1), Create(curve2), run_time=0.8)  # 主视觉
        self.play_parallel(type_in(lab1, run_time=0.5), type_in(lab2, run_time=0.5),
                           run_time=0.5)
        self.play(type_in(note, run_time=0.8))
        self.at_clip("S6-c10")
        cnt = self.counter_value(0, 0.25, decimals=2, suffix="%", size=48, color=YELL,
                                 anchor=slot, run_time=1.0,
                                 extra_anims=[type_in(num_lab, run_time=0.6)])
        self.at_clip("S6-c11")
        head3 = t("为什么能守住？", 36, YELL, "BOLD").to_edge(UP, buff=1.2)
        self.play(FadeOut(head2), FadeOut(page2), FadeOut(cnt),
                  type_in(head3, run_time=0.8), run_time=0.8)

        # 页3：随机舍入 + 回扣记账游戏
        c1 = _card("四舍五入：误差恒偏向同一侧，累积成漂移", 6.8, 1.8, RED, WHITE, 34, CARD_FILL)
        c2 = _card("随机舍入：误差是零均值噪声，互相抵消", 6.8, 1.8, GREEN, WHITE, 34, CARD_FILL, "BOLD")
        concl = t("一万笔账互相抵消，只留下 0.25% 的差距", 40, YELL, "BOLD")
        page_auto(c1, c2, concl)

        self.at_clip("S6-c12")
        self.play_scroll_unroll(c1, run_time=1.2)
        self.at_clip("S6-c13")
        self.play_scroll_unroll(c2, run_time=1.2)  # 主视觉
        self.at_clip("S6-c16")
        self.play(type_in(concl, run_time=0.9))
        self.emphasize(concl, run_time=0.6)  # 3/5
        self.at_clip("S6-c17")
        self.play(FadeOut(head3), FadeOut(c1), FadeOut(c2), FadeOut(concl), run_time=0.5)

        # 页4：残缺数字的美学（矮页）
        card = _card("残缺数字的美学：不是每个数字都准，而是整体误差可控", 6.8, 2.2, YELL, WHITE, 36, CARD_FILL, "BOLD")
        page_auto(card)

        self.play_scroll_unroll(card, run_time=1.2)
        self.emphasize(card, run_time=0.6)  # 4/5
        self.at_clip("S6-c18")

        # 页5：品牌尾卡（终幕，不转场）
        avatar = ImageMobject(str(AVATAR))
        avatar.scale_to_fit_width(2.6)
        follow = t("关注「数解AI」", 40, YELL, "BOLD")
        title = t("《FP8训练：残缺数字怎么练出顶级模型》", 30, WHITE, "BOLD")
        if title.width > FW * 0.8:
            title.set_width(FW * 0.8)
        guide = t("查看公众号文章", 28, GREEN, "BOLD")
        next_lab = t("下一篇：FP4 量化——4 位数字怎么做到无损", 24, MUTED)
        aq = t("省下来的显存，你会拿去塞更大的模型，\n还是拉更长的上下文？评论区聊聊", 22, MUTED)
        page5 = page_stack(avatar, follow, title, guide, next_lab, aq, buff=0.5)
        layout_page(page5)

        self.play(FadeOut(card), FadeIn(avatar, scale=1.5), type_in(follow, run_time=0.8),
                  type_in(title, run_time=0.9), run_time=0.9)
        self.play_parallel(type_in(guide, run_time=0.7), type_in(next_lab, run_time=0.8),
                           run_time=0.8)
        self.at_clip("S6-c19")
        self.play(type_in(aq, run_time=0.9))
        self.pad_to_voice()
        self.pad_to_voice()
