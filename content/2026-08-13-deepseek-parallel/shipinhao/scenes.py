#!/usr/bin/env python3
"""《1.6T参数怎么塞进GPU？V4五维并行策略》视频号 Manim 动画（竖屏 1080×1920）

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

# 每段配音时长（tts_split.py 实测），渲染时长 = 配音 + TAIL
VOICE_DUR = {"S1": 20.65, "S2": 34.99, "S3": 45.55, "S4": 45.22, "S5": 49.11, "S6": 51.23}
TAIL = 2.5


def _footer(self) -> Text:
    f = t("数解AI · DeepSeek 技术解密", 20, MUTED).to_edge(DOWN, buff=1.15)
    self.add(f)
    return f


def _head(text: str, size: float = 38) -> Text:
    return t(text, size, YELL, "BOLD").to_edge(UP, buff=1.2)


# ---------------- S1 开场钩子：1.6T 塞不进 80GB ----------------
class S1(_Base):
    def construct(self):
        self.bg()
        f = _footer(self)

        # 页1：概念图（塞行李箱）+ 20 倍
        head = _head("1.6T 参数 vs 80G 显存", 36)
        note0 = t("以 DeepSeek-V4-Pro 为例", 24, MUTED).next_to(head, DOWN, buff=0.5)
        img = ImageMobject(str(IMG / "s1-squeeze-round.png"))
        img.scale_to_fit_width(5.2)
        lab = t("差距", 34, WHITE, "BOLD")
        slot = dynamic_slot(2.2, 1.0)
        row = stable_row(lab, slot, buff=0.4)
        page1 = page_stack(img, row, buff=1.0)
        layout_page(page1)

        self.at_clip("S1-c01")
        self.play_parallel(type_in(head, run_time=1.1), FadeIn(note0, shift=DOWN * 0.05),
                           FadeIn(img, shift=DOWN * 0.05), run_time=1.1)
        self.at_clip("S1-c02")
        n = self.counter_value(0, 20, suffix=" 倍", size=88, color=YELL,
                               run_time=1.2, anchor=slot,
                               extra_anims=[type_in(lab, run_time=0.6)])  # 主视觉：数字滚动

        # 页2：问句 + 五把刀
        head2 = _head("怎么塞进去，还让它跑得动？", 40)
        line = t("答案是切", 34, WHITE)
        chips_top = VGroup(*[_card(x, 1.8, 1.8, CYAN, WHITE, 28, CARD_FILL, "BOLD")
                           for x in ["按层切", "按矩阵切", "按数据切"]]).arrange(RIGHT, buff=0.2)
        chips_bot = VGroup(*[_card(x, 1.8, 1.8, CYAN, WHITE, 28, CARD_FILL, "BOLD")
                           for x in ["按专家切", "按序列切"]]).arrange(RIGHT, buff=0.2)
        chips = VGroup(chips_top, chips_bot).arrange(DOWN, buff=0.2)
        concl = t("五把刀，各切一刀", 40, YELL, "BOLD")
        page2 = page_stack(line, chips, concl, buff=1.4)
        layout_page(page2)

        self.at_clip("S1-c03")
        self.play(FadeOut(head), FadeOut(note0), FadeOut(page1), FadeOut(n),
                  type_in(head2, run_time=0.9), run_time=0.9)
        self.emphasize(head2, run_time=0.5)  # 1/5
        self.at_clip("S1-c04")
        self.play(type_in(line, run_time=0.6))
        self.wait(0.1)
        self.play(*[FadeIn(c, shift=UP * 0.05) for c in chips_top], run_time=0.8)  # 主视觉：五刀
        self.at_clip("S1-c05")
        self.play(*[FadeIn(c, shift=UP * 0.05) for c in chips_bot], run_time=0.6)
        self.at_clip("S1-c06")
        self.play(type_in(concl, run_time=0.8))
        self.wait(0.7)  # 补到 c06 结束（20.65），台词讲完再转场
        self.transition_out(head2, f, line, chips, concl)
        self.pad_to_voice()


# ---------------- S2 先算账：显存不是瓶颈 ----------------
class S2(_Base):
    def construct(self):
        self.bg()
        f = _footer(self)

        # 页1：推理账
        head = _head("先算账：推理", 38)
        lab1 = t("1.6T 参数", 34, WHITE, "BOLD")
        slot1 = dynamic_slot(2.4, 1.2)
        row1 = stable_row(lab1, slot1, buff=0.4)
        lab2 = t("推理至少", 34, WHITE, "BOLD")
        slot2 = dynamic_slot(2.4, 1.2)
        row2 = stable_row(lab2, slot2, buff=0.4)
        lab3 = t("FP4 后", 34, WHITE, "BOLD")
        slot3 = dynamic_slot(2.4, 1.2)
        row3 = stable_row(lab3, slot3, buff=0.4)
        note = t("11 块卡就够", 30, GREEN, "BOLD")
        page1 = page_stack(row1, row2, row3, note, buff=1.0)
        layout_page(page1)

        self.at_clip("S2-c01")
        self.play(type_in(head, run_time=0.6))
        self.at_clip("S2-c02")
        n1 = self.counter_value(0, 1600, suffix=" GB", size=72, color=YELL,
                                run_time=2.0, anchor=slot1,
                                extra_anims=[type_in(lab1, run_time=0.6)])  # 主视觉：数字滚动
        self.at_clip("S2-c03")
        n2 = self.counter_value(0, 20, suffix=" 块卡", size=72, color=YELL,
                                run_time=1.2, anchor=slot2,
                                extra_anims=[type_in(lab2, run_time=0.6)])
        self.at_clip("S2-c04")
        n3 = self.counter_value(0, 826, suffix=" GB", size=72, color=YELL,
                                run_time=1.8, anchor=slot3,
                                extra_anims=[type_in(lab3, run_time=0.6),
                                             type_in(note, run_time=0.6)])

        # 页2：训练账
        head2 = _head("训练：账完全不一样", 38)
        line = t("要存权重、梯度、优化器状态", 30, WHITE)
        card = _card("16 路 PP × 64 路 EP", 6.4, 1.8, CYAN, WHITE, 36, CARD_FILL, "BOLD")
        lab4 = t("每张卡只管", 34, WHITE, "BOLD")
        slot4 = dynamic_slot(2.4, 1.2)
        row4 = stable_row(lab4, slot4, buff=0.4)
        lab5 = t("合计", 34, WHITE, "BOLD")
        slot5 = dynamic_slot(2.4, 1.2)
        row5 = stable_row(lab5, slot5, buff=0.4)
        page2 = page_stack(line, card, row4, row5, buff=1.0)
        layout_page(page2)

        self.play(FadeOut(head), FadeOut(page1), FadeOut(n1), FadeOut(n2), FadeOut(n3),
                  type_in(head2, run_time=0.8), run_time=0.8)
        self.at_clip("S2-c05")
        self.play(type_in(line, run_time=0.8))
        self.at_clip("S2-c06")
        self.play_scroll_unroll(card, run_time=1.0)  # 主视觉：拉幕
        self.at_clip("S2-c07")
        n4 = self.counter_value(0, 15.6, suffix=" 亿参数", decimals=1, size=72, color=YELL,
                                run_time=1.5, anchor=slot4,
                                extra_anims=[type_in(lab4, run_time=0.6)])
        self.wait(0.2)
        n5 = self.counter_value(0, 16, suffix=" GB", size=72, color=YELL,
                                run_time=1.2, anchor=slot5,
                                extra_anims=[type_in(lab5, run_time=0.6)])

        # 页3：转折爆点
        head3 = _head("第一个反直觉的转折", 38)
        concl = t("显存不是瓶颈", 60, YELL, "BOLD")
        page3 = page_auto(concl)

        self.play(FadeOut(head2), FadeOut(page2), FadeOut(n4), FadeOut(n5),
                  type_in(head3, run_time=0.8), run_time=0.8)
        self.at_clip("S2-c08")
        self.play(type_in(concl, run_time=0.9))
        self.emphasize(concl, run_time=0.5)  # 2/5
        self.wait(3.6)  # 补到 c08 结束（35.07），台词讲完再转场
        self.transition_out(head3, f, concl)
        self.pad_to_voice()


# ---------------- S3 五维地图 + PP/TP ----------------
class S3(_Base):
    def construct(self):
        self.bg()
        f = _footer(self)

        # 页1：为什么 2048 张卡
        head = _head("那为什么要 2048 张卡？", 38)
        ans = t("因为算力。", 48, YELL, "BOLD")
        card = _card("最大 batch：94.4M tokens/step", 6.4, 1.8, CYAN, WHITE, 34, CARD_FILL, "BOLD")
        line1 = t("矩阵乘法量巨大", 32, WHITE)
        line2 = t("协同干活，就躲不开通信", 32, WHITE)
        page1 = page_stack(ans, card, line1, line2, buff=1.3)
        layout_page(page1)

        self.at_clip("S3-c01")
        self.play(type_in(head, run_time=0.8))
        self.at_clip("S3-c02")
        self.play(type_in(ans, run_time=0.6))
        self.emphasize(ans, run_time=0.4)  # 3/5
        self.at_clip("S3-c03")
        self.play_scroll_unroll(card, run_time=1.0)  # 主视觉：拉幕
        self.at_clip("S3-c04")
        self.play(type_in(line1, run_time=0.7), type_in(line2, run_time=0.7), run_time=0.8)

        # 页2：PP 流水线
        head2 = _head("按层切：流水线并行", 38)
        img = ImageMobject(str(IMG / "s3-factory-round.png"))
        img.scale_to_fit_width(4.8)
        line3 = t("61 层 → 16 个 stage", 32, WHITE)
        stages = VGroup(*[Rectangle(width=1.5, height=1.2, color=CYAN,
                                    fill_color=CYAN, fill_opacity=0.15) for _ in range(4)])
        stages.arrange(RIGHT, buff=0.3)
        bubble = DashedVMobject(Rectangle(width=1.5, height=1.2, color=RED, stroke_width=3))
        bubble.move_to(stages[1].get_center())
        stages.add(bubble)
        line4 = t("代价：流水线气泡", 32, RED, "BOLD")
        page2 = page_stack(img, line3, stages, line4, buff=1.2)
        layout_page(page2)

        self.play(FadeOut(head), FadeOut(page1), type_in(head2, run_time=0.8), run_time=0.8)
        self.at_clip("S3-c05")
        self.play(FadeIn(img, shift=DOWN * 0.05), run_time=0.8)  # 主视觉：插图
        self.at_clip("S3-c06")
        self.play(type_in(line3, run_time=0.7))
        self.wait(0.1)
        self.play(*[Create(s) for s in stages], run_time=1.0, lag_ratio=0.3)
        self.at_clip("S3-c07")
        self.play(Create(bubble), type_in(line4, run_time=0.6), run_time=0.8)

        # 页3：TP 张量并行
        head3 = _head("按矩阵切：张量并行", 38)
        card = _card("hidden 7168 → 8 片", 6.4, 1.6, GREEN, WHITE, 36, CARD_FILL, "BOLD")
        slices = VGroup(*[Rectangle(width=0.8, height=2.4, color=GREEN,
                                   fill_color=GREEN, fill_opacity=0.15) for _ in range(8)])
        slices.arrange(RIGHT, buff=0.1)
        line6 = t("每层两次 all-reduce · 必须走 NVLink", 32, WHITE)
        page3 = page_stack(card, slices, line6, buff=1.3)
        layout_page(page3)

        self.play(FadeOut(head2), FadeOut(page2), type_in(head3, run_time=0.8), run_time=0.8)
        self.at_clip("S3-c08")
        self.play_scroll_unroll(card, run_time=1.0)  # 主视觉：拉幕
        self.wait(0.1)
        self.play(*[Create(s) for s in slices], run_time=1.2, lag_ratio=0.2)
        self.at_clip("S3-c09")
        self.play(type_in(line6, run_time=0.8))

        # 页4：转折爆点——TP 关了
        head4 = _head("直觉 vs 现实", 38)
        q = t("1.6T 这么大，TP 肯定拉满了吧？", 36, WHITE)
        twist = t("V4 反手把 TP 关了", 56, YELL, "BOLD")
        why = t("注意力被 CSA 压得极扁，通信税不值了", 32, WHITE)
        page4 = page_auto(q, twist, why)

        self.play(FadeOut(head3), FadeOut(page3), type_in(head4, run_time=0.8), run_time=0.8)
        self.at_clip("S3-c10")
        self.play(type_in(q, run_time=0.8))
        self.at_clip("S3-c11")
        self.play(type_in(twist, run_time=0.8))
        self.at_clip("S3-c12")
        self.play(type_in(why, run_time=0.8))
        self.wait(2.6)  # 补到 c12 结束（45.57），台词讲完再转场
        self.transition_out(head4, f, q, twist, why)
        self.pad_to_voice()


# ---------------- S4 DP + ZeRO-1 免费午餐 ----------------
class S4(_Base):
    def construct(self):
        self.bg()
        f = _footer(self)

        # 页1：数据并行
        head = _head("模型装下了，怎么算得快？", 36)
        line0 = t("最朴素的想法", 30, WHITE)
        card1 = _card("数据并行：每张卡一份完整模型", 6.4, 2.2, CYAN, WHITE, 34, CARD_FILL, "BOLD")
        card2 = _card("各算各的 batch，反向结束同步梯度", 6.4, 2.2, GREEN, WHITE, 34, CARD_FILL, "BOLD")
        page1 = page_stack(line0, card1, card2, buff=1.2)
        layout_page(page1)

        self.at_clip("S4-c01")
        self.play(type_in(head, run_time=0.8))
        self.at_clip("S4-c02")
        self.play(type_in(line0, run_time=0.6))
        self.wait(0.1)
        self.play_scroll_unroll(card1, run_time=1.0)  # 主视觉：拉幕
        self.at_clip("S4-c03")
        self.play_scroll_unroll(card2, run_time=1.0)

        # 页2：优化器状态账
        head2 = _head("隐形成本：优化器状态", 38)
        line = t("每张卡要存一份完整的优化器状态", 30, WHITE)
        lab1 = t("10B 模型里优化器占", 28, WHITE, "BOLD")
        slot1 = dynamic_slot(2.2, 1.2)
        row1 = stable_row(lab1, slot1, buff=0.4)
        lab2 = t("是参数的", 32, WHITE, "BOLD")
        slot2 = dynamic_slot(2.2, 1.2)
        row2 = stable_row(lab2, slot2, buff=0.4)
        lab3 = t("1.6T 的模型", 32, WHITE, "BOLD")
        slot3 = dynamic_slot(2.2, 1.2)
        row3 = stable_row(lab3, slot3, buff=0.4)
        page2 = page_stack(line, row1, row2, row3, buff=1.0)
        layout_page(page2)

        self.play(FadeOut(head), FadeOut(page1), type_in(head2, run_time=0.8), run_time=0.8)
        self.at_clip("S4-c04")
        self.play(type_in(line, run_time=0.8))
        self.at_clip("S4-c05")
        n1 = self.counter_value(0, 80, suffix=" GB", size=72, color=YELL,
                                run_time=1.5, anchor=slot1,
                                extra_anims=[type_in(lab1, run_time=0.6)])  # 主视觉：数字滚动
        self.at_clip("S4-c06")
        n2 = self.counter_value(0, 4, suffix=" 倍", size=72, color=YELL,
                                run_time=1.0, anchor=slot2,
                                extra_anims=[type_in(lab2, run_time=0.6)])
        self.at_clip("S4-c07")
        n3 = self.counter_value(0, 12, suffix=" TB 级", size=72, color=YELL,
                                run_time=1.2, anchor=slot3,
                                extra_anims=[type_in(lab3, run_time=0.6)])

        # 页3：ZeRO-1
        head3 = _head("ZeRO-1：只切优化器状态", 38)
        card3 = _card("只切优化器状态，梯度照常全量同步", 6.4, 1.8, CYAN, WHITE, 32, CARD_FILL, "BOLD")
        line2 = t("通信量和普通 DP 一模一样", 32, WHITE)
        rs = _card("reduce-scatter", 2.8, 1.2, GREEN, WHITE, 26, CARD_FILL, "BOLD")
        ag = _card("all-gather", 2.8, 1.2, GREEN, WHITE, 26, CARD_FILL, "BOLD")
        flow = VGroup(rs, ag).arrange(RIGHT, buff=1.2)
        fa = Arrow(rs.get_right(), ag.get_left(), color=MUTED, buff=0.1, stroke_width=4)
        flow.add(fa)
        line3 = t("只是把更新参数插在中间", 30, WHITE)
        concl = t("近乎免费", 44, GREEN, "BOLD")
        page3 = page_stack(card3, line2, flow, line3, concl, buff=0.8)
        layout_page(page3)

        self.play(FadeOut(head2), FadeOut(page2), FadeOut(n1), FadeOut(n2), FadeOut(n3),
                  type_in(head3, run_time=0.8), run_time=0.8)
        self.at_clip("S4-c08")
        self.play_scroll_unroll(card3, run_time=1.0)  # 主视觉：拉幕
        self.at_clip("S4-c09")
        self.at_clip("S4-c10")
        self.play(type_in(line2, run_time=0.8))
        self.at_clip("S4-c11")
        self.play(Create(rs), Create(ag), Create(fa), run_time=1.2, lag_ratio=0.3)
        self.at_clip("S4-c12")
        self.play(type_in(line3, run_time=0.8))
        self.at_clip("S4-c13")
        self.play(type_in(concl, run_time=0.8))
        self.wait(3.0)  # 补到 c13 结束（45.23），台词讲完再转场
        self.transition_out(head3, f, card3, line2, flow, line3, concl)
        self.pad_to_voice()


# ---------------- S5 EP 通信账：1800 倍 ----------------
class S5(_Base):
    def construct(self):
        self.bg()
        f = _footer(self)

        # 页1：token 找专家
        head = _head("真正的主角：专家并行", 38)
        lab1 = t("路由专家", 34, WHITE, "BOLD")
        slot1 = dynamic_slot(2.2, 1.2)
        row1 = stable_row(lab1, slot1, buff=0.4)
        lab2 = t("每 token 激活", 34, WHITE, "BOLD")
        slot2 = dynamic_slot(2.2, 1.2)
        row2 = stable_row(lab2, slot2, buff=0.4)
        img = ImageMobject(str(IMG / "s5-courier-round.png"))
        img.scale_to_fit_width(3.0)
        line = t("token 上门找专家，算完带回来", 30, WHITE)
        page1 = page_stack(row1, row2, img, line, buff=1.2)
        layout_page(page1)

        self.at_clip("S5-c01")
        self.play(type_in(head, run_time=0.8))
        self.at_clip("S5-c02")
        n1 = self.counter_value(0, 384, suffix=" 个", size=72, color=YELL,
                                run_time=1.5, anchor=slot1,
                                extra_anims=[type_in(lab1, run_time=0.6)])  # 主视觉：数字滚动
        self.at_clip("S5-c03")
        n2 = self.counter_value(0, 6, suffix=" 个", size=72, color=YELL,
                                run_time=1.0, anchor=slot2,
                                extra_anims=[type_in(lab2, run_time=0.6)])
        self.at_clip("S5-c04")
        self.play(FadeIn(img, shift=DOWN * 0.05), type_in(line, run_time=0.8), run_time=0.9)
        self.at_clip("S5-c05")

        # 页2：单层账
        head2 = _head("这笔账有多大？", 38)
        card = _card("每 token 每层：6 专家对 × 7168 维", 6.4, 1.6, CYAN, WHITE, 32, CARD_FILL, "BOLD")
        formula = t("6 × 7168 × 3 字节", 40, WHITE, "BOLD")
        lab3 = t("≈", 40, WHITE, "BOLD")
        slot3 = dynamic_slot(2.4, 1.2)
        row3 = stable_row(lab3, slot3, buff=0.4)
        note = t("FP8 发过去，BF16 收回来", 26, MUTED)
        page2 = page_stack(card, formula, row3, note, buff=1.2)
        layout_page(page2)

        self.play(FadeOut(head), FadeOut(page1), FadeOut(n1), FadeOut(n2),
                  type_in(head2, run_time=0.8), run_time=0.8)
        self.at_clip("S5-c06")
        self.at_clip("S5-c07")
        self.play_scroll_unroll(card, run_time=1.0)  # 主视觉：拉幕
        self.wait(0.1)
        self.play(type_in(formula, run_time=0.8))
        self.at_clip("S5-c08")
        n3 = self.counter_value(0, 129, suffix=" KB", size=72, color=YELL,
                                run_time=1.2, anchor=slot3,
                                extra_anims=[type_in(note, run_time=0.6)])

        # 页3：16GB vs 9MB
        head3 = _head("1M 上下文场景", 38)
        b1 = Rectangle(width=1.6, height=4.0, color=RED, fill_color=RED, fill_opacity=0.6)
        l1 = t("EP 单层 16GB", 28, RED, "BOLD")
        col1 = VGroup(l1, b1).arrange(DOWN, buff=0.25)
        b2 = Rectangle(width=1.6, height=0.6, color=GREEN, fill_color=GREEN, fill_opacity=0.6)
        l2 = t("CP 每层 9MB", 28, GREEN, "BOLD")
        col2 = VGroup(l2, b2).arrange(DOWN, buff=0.25)
        cols = VGroup(col1, col2).arrange(RIGHT, buff=1.2)
        lab4 = t("差了近", 34, WHITE, "BOLD")
        slot4 = dynamic_slot(2.4, 1.2)
        row4 = stable_row(lab4, slot4, buff=0.4)
        page3 = page_stack(cols, row4, buff=1.2)
        layout_page(page3)

        self.at_clip("S5-c09")
        self.play(FadeOut(head2), FadeOut(page2), FadeOut(n3),
                  type_in(head3, run_time=0.8), run_time=0.8)
        self.play(GrowFromEdge(b1, DOWN), type_in(l1, 0.5), run_time=1.0)  # 主视觉：柱生长
        self.at_clip("S5-c10")
        self.play(GrowFromEdge(b2, DOWN), type_in(l2, 0.5), run_time=1.0)
        self.at_clip("S5-c11")
        n4 = self.counter_value(0, 1800, suffix=" 倍", size=72, color=YELL,
                                run_time=1.2, anchor=slot4,
                                extra_anims=[type_in(lab4, run_time=0.6)])
        self.emphasize(n4, run_time=0.5)  # 4/5

        # 页4：1TB + 20 秒
        head4 = _head("61 层加起来", 38)
        card4 = _card("一次前向 EP 通信", 6.4, 1.6, CYAN, WHITE, 36, CARD_FILL, "BOLD")
        lab5 = t("接近", 34, WHITE, "BOLD")
        slot5 = dynamic_slot(2.2, 1.3)
        row5 = stable_row(lab5, slot5, buff=0.4)
        lab6 = t("IB 50GB/s 光传", 34, WHITE, "BOLD")
        slot6 = dynamic_slot(2.2, 1.3)
        row6 = stable_row(lab6, slot6, buff=0.4)
        concl = t("IB 带宽是训练系统的命脉", 40, YELL, "BOLD")
        page4 = page_stack(card4, row5, row6, concl, buff=1.0)
        layout_page(page4)

        self.at_clip("S5-c12")
        self.play(FadeOut(head3), FadeOut(page3), FadeOut(n4),
                  type_in(head4, run_time=0.8), run_time=0.8)
        self.play_scroll_unroll(card4, run_time=1.0)  # 主视觉：拉幕
        self.wait(0.1)
        n5 = self.counter_value(0, 1, suffix=" TB", size=72, color=YELL,
                                run_time=1.2, anchor=slot5,
                                extra_anims=[type_in(lab5, run_time=0.6)])
        self.at_clip("S5-c13")
        n6 = self.counter_value(0, 20, suffix=" 秒", size=72, color=YELL,
                                run_time=1.2, anchor=slot6,
                                extra_anims=[type_in(lab6, run_time=0.6)])
        self.at_clip("S5-c14")
        self.play(type_in(concl, run_time=0.8))
        self.wait(2.2)  # 补到 c14 结束（49.15），台词讲完再转场
        self.transition_out(head4, f, card4, row5, n5, row6, n6, concl)
        self.pad_to_voice()


# ---------------- S6 CP + 四重身份 + 结尾 + 尾卡 ----------------
class S6(_Base):
    def construct(self):
        self.bg()
        f = _footer(self)

        # 页1：上下文并行
        head = _head("最后一个维度：序列", 38)
        card = _card("上下文并行：序列切成 8 段", 6.4, 2.0, CYAN, WHITE, 34, CARD_FILL, "BOLD")
        seq = VGroup(*[Rectangle(width=0.8, height=1.6, color=CYAN,
                                 fill_color=CYAN, fill_opacity=0.2) for _ in range(8)])
        seq.arrange(RIGHT, buff=0.1)
        lab = t("每层只要", 34, WHITE, "BOLD")
        slot = dynamic_slot(2.2, 1.4)
        row = stable_row(lab, slot, buff=0.4)
        page1 = page_stack(card, seq, row, buff=1.4)
        layout_page(page1)

        self.at_clip("S6-c01")
        self.play(type_in(head, run_time=0.8))
        self.at_clip("S6-c02")
        self.play_scroll_unroll(card, run_time=1.0)  # 主视觉：拉幕
        self.at_clip("S6-c03")
        self.play(*[Create(s) for s in seq], run_time=1.2, lag_ratio=0.2)
        self.at_clip("S6-c04")
        n = self.counter_value(0, 9, suffix=" MB/层", size=72, color=YELL,
                               run_time=1.2, anchor=slot,
                               extra_anims=[type_in(lab, run_time=0.6)])

        # 页2：四重身份
        head2 = _head("一块 GPU 的四重身份", 38)
        line2 = t("2048 张卡里随便抽一张", 30, WHITE)
        c1 = _card("DP 副本", 3.0, 1.8, CYAN, WHITE, 34, CARD_FILL, "BOLD")
        c2 = _card("PP stage", 3.0, 1.8, GREEN, WHITE, 34, CARD_FILL, "BOLD")
        c3 = _card("CP rank", 3.0, 1.8, YELL, WHITE, 34, CARD_FILL, "BOLD")
        c4 = _card("EP 专家组", 3.0, 1.8, RED, WHITE, 34, CARD_FILL, "BOLD")
        grid = VGroup(c1, c2, c3, c4).arrange_in_grid(2, 2, buff=0.4)
        line3 = t("四个正交的切割轴", 32, WHITE)
        page2 = page_stack(line2, grid, line3, buff=1.1)
        layout_page(page2)

        self.play(FadeOut(head), FadeOut(page1), FadeOut(n),
                  type_in(head2, run_time=0.8), run_time=0.8)
        self.at_clip("S6-c05")
        self.play(type_in(line2, run_time=0.7))
        self.at_clip("S6-c06")
        self.play_scroll_unroll_many(c1, c2, run_time=1.0)  # 主视觉：拉幕
        self.at_clip("S6-c07")
        self.play_scroll_unroll_many(c3, c4, run_time=1.0)
        self.at_clip("S6-c08")
        self.play(type_in(line3, run_time=0.7))

        # 页3：总结
        head3 = _head("装下只是第一步", 40)
        concl = t("协同干活、通信不打架，才是真正的战场", 44, YELL, "BOLD")
        page3 = page_auto(concl)

        self.play(FadeOut(head2), FadeOut(page2), type_in(head3, run_time=0.8), run_time=0.8)
        self.at_clip("S6-c09")
        self.at_clip("S6-c10")
        self.play(type_in(concl, run_time=0.9))
        self.emphasize(concl, run_time=0.5)  # 5/5

        # 页4：预告 + 互动
        head4 = _head("下一篇", 38)
        q1 = t("1M 序列为什么切了会坏？", 40, YELL, "BOLD")
        q2 = t("一个问题留给你", 34, WHITE)
        q3a = t("1T 参数的 MoE，", 32, WHITE)
        q3b = t("你会抄 DeepSeek 的作业，", 32, WHITE)
        q3 = VGroup(q3a, q3b).arrange(DOWN, buff=0.15)
        q4 = t("还是给 TP 留位置？", 32, WHITE)
        cm = t("评论区聊聊", 36, GREEN, "BOLD")
        page4 = page_stack(q1, q2, q3, q4, cm, buff=1.2)
        layout_page(page4)

        self.play(FadeOut(head3), FadeOut(page3), type_in(head4, run_time=0.8), run_time=0.8)
        self.at_clip("S6-c11")
        self.play(type_in(q1, run_time=0.9))
        self.at_clip("S6-c12")
        self.play(type_in(q2, run_time=0.7), type_in(q3, run_time=0.8), run_time=0.9)
        self.at_clip("S6-c13")
        self.play(type_in(q4, run_time=0.8))
        self.at_clip("S6-c14")
        self.play(type_in(cm, run_time=0.7))

        # 页5：品牌尾卡（终幕驻屏，不 transition_out）
        avatar = ImageMobject(str(AVATAR))
        avatar.scale_to_fit_width(3.6)
        follow = t("关注「数解AI」", 44, YELL, "BOLD")
        title = t("《1.6T参数怎么塞进GPU？V4五维并行策略》", 28, WHITE, "BOLD")
        guide = t("查看公众号文章", 32, GREEN, "BOLD")
        page5 = page_stack(avatar, follow, title, guide, buff=0.7)
        layout_page(page5)

        self.at_clip("S6-c15")
        self.play(FadeOut(head4), FadeOut(page4), FadeIn(avatar, shift=DOWN * 0.05), run_time=0.8)  # 主视觉：品牌图
        self.play(type_in(follow, run_time=0.7), type_in(title, run_time=0.7),
                  type_in(guide, run_time=0.6), run_time=0.8)
        self.pad_to_voice()
