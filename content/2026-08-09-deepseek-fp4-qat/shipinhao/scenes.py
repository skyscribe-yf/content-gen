#!/usr/bin/env python3
"""《FP4量化：4位数字怎么做到无损》视频号 Manim 动画（竖屏 1080×1920，精英男声重做版）

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
VOICE_DUR = {"S1": 33.5, "S2": 38.32, "S3": 40.43, "S4": 45.61, "S5": 64.65, "S6": 79.83}
TAIL = 2.5


def _footer(self) -> Text:
    f = t("数解AI · 大模型原理", 20, MUTED).to_edge(DOWN, buff=1.15)
    self.add(f)
    return f


# ---------------- S1 开场钩子：账本游戏 ----------------
class S1(_Base):
    def construct(self):
        self.bg()
        f = _footer(self)

        # 页1：账本概念图 + 数字行 + 误差卡
        head = t("账本上只能写 7 个数", 38, YELL, "BOLD").to_edge(UP, buff=1.2)
        note0 = t("以 FP4 量化为例", 24, MUTED).next_to(head, DOWN, buff=0.5)
        img = ImageMobject(str(IMG / "s1-ledger-round.png"))
        img.scale_to_fit_width(4.4)
        nums = VGroup(*[boxed(n, 1.1, 1.0, CYAN, 30, weight="BOLD")
                        for n in ["0.5", "1", "1.5", "2", "3", "4", "6"]])
        nums.arrange(RIGHT, buff=0.15)
        c1 = _card("0.8 → 写成 1", 3.0, 1.5, RED, WHITE, 34, CARD_FILL, "BOLD")
        c2 = _card("3.7 → 写成 4", 3.0, 1.5, RED, WHITE, 34, CARD_FILL, "BOLD")
        cards = VGroup(c1, c2).arrange(RIGHT, buff=0.5)
        cap = t("每个数字，最多带 25% 的误差", 30, WHITE, "BOLD")
        page1 = page_stack(img, nums, cards, cap, buff=0.6)
        layout_page(page1)

        self.at_clip("S1-c01")
        self.play_parallel(type_in(head, run_time=1.1), FadeIn(note0, shift=DOWN * 0.05),
                           FadeIn(img, shift=DOWN * 0.05), run_time=1.1)
        self.at_clip("S1-c02")
        self.play_parallel(*[FadeIn(n, scale=0.5) for n in nums], run_time=1.0,
                           lag_ratio=0.12)  # 主视觉
        self.at_clip("S1-c04")
        self.play_scroll_unroll_many(c1, c2, run_time=1.2)
        self.at_clip("S1-c05")
        self.play(type_in(cap, run_time=0.9))
        self.at_clip("S1-c06")
        self.wait(0.3)
        self.at_clip("S1-c07")
        self.play(FadeOut(head), FadeOut(note0), FadeOut(page1), run_time=0.5)

        # 页2：16 个可选值 + 无损疑问（矮页）
        card = _card("DeepSeek 干了：专家权重全用 4 位数字", 6.8, 1.9, YELL, WHITE, 36, CARD_FILL, "BOLD")
        q = t("16 个可选值，你跟我说无损？", 48, YELL, "BOLD")
        page_auto(card, q)

        self.at_clip("S1-c09")
        self.play_scroll_unroll(card, run_time=1.2)
        self.at_clip("S1-c11")
        self.play(type_in(q, run_time=0.9))
        self.emphasize(q, run_time=0.6)  # 1/5
        self.wait(0.3)
        self.transition_out(f, card, q)
        self.pad_to_voice()


# ---------------- S2 E2M1 格式解剖 ----------------
class S2(_Base):
    def construct(self):
        self.bg()
        f = _footer(self)

        # 页1：4 位结构 + 7 个正数
        head = t("E2M1：1 符号 + 2 指数 + 1 尾数", 34, YELL, "BOLD").to_edge(UP, buff=1.2)
        s_bit = boxed("符号\n1 位", 1.8, 1.8, RED, 30, weight="BOLD")
        e_bit = boxed("指数\n2 位", 1.8, 1.8, CYAN, 30, weight="BOLD")
        m_bit = boxed("尾数\n1 位", 1.8, 1.8, GREEN, 30, weight="BOLD")
        bits = VGroup(s_bit, e_bit, m_bit).arrange(RIGHT, buff=0.4)
        nums = VGroup(*[boxed(n, 1.1, 1.0, CYAN, 30, weight="BOLD")
                        for n in ["0.5", "1", "1.5", "2", "3", "4", "6"]])
        nums.arrange(RIGHT, buff=0.15)
        cap = t("正数就 7 个，加上负号共 16 个组合", 30, WHITE, "BOLD")
        page_auto(bits, nums, cap)

        self.at_clip("S2-c01")
        self.play(type_in(head, run_time=1.1))
        self.at_clip("S2-c02")
        self.play_scroll_unroll_many(s_bit, e_bit, m_bit, run_time=1.2)  # 主视觉
        self.at_clip("S2-c03")
        self.play_parallel(*[FadeIn(n, scale=0.5) for n in nums], run_time=1.0,
                           lag_ratio=0.12)
        self.at_clip("S2-c05")
        self.play(type_in(cap, run_time=0.9))
        self.at_clip("S2-c06")
        self.wait(0.3)
        self.at_clip("S2-c08")

        # 页2：动态范围 + 32 元素共享 scale
        head2 = t("动态范围 12 倍", 36, YELL, "BOLD").to_edge(UP, buff=1.2)
        ruler = Rectangle(width=6.4, height=0.5, color=MUTED, fill_color=MUTED, fill_opacity=0.3)
        tick1 = t("0.5", 26, CYAN, "BOLD").next_to(ruler.get_left(), DOWN, buff=0.3)
        tick2 = t("6", 26, YELL, "BOLD").next_to(ruler.get_right(), DOWN, buff=0.3)
        ruler_grp = VGroup(ruler, tick1, tick2)
        c1 = _card("精度比 FP8 糙 4 倍，比 BF16 糙约 60 倍", 6.6, 1.7, RED, WHITE, 34, CARD_FILL)
        c2 = _card("32 个元素，共享一个 2 的幂的 scale", 6.6, 1.7, GREEN, WHITE, 34, CARD_FILL, "BOLD")
        concl = t("这个结构，是无损成立的前提", 36, YELL, "BOLD")
        page2 = page_stack(ruler_grp, c1, c2, concl, buff=0.9)
        layout_page(page2)

        self.play(FadeOut(head), FadeOut(bits), FadeOut(nums), FadeOut(cap),
                  type_in(head2, run_time=0.8), run_time=0.8)
        self.play(FadeIn(ruler, shift=DOWN * 0.05), type_in(tick1, run_time=0.5),
                  type_in(tick2, run_time=0.5), run_time=0.7)  # 主视觉
        self.at_clip("S2-c10")
        self.play_scroll_unroll(c1, run_time=1.2)
        self.at_clip("S2-c11")
        self.play_scroll_unroll(c2, run_time=1.2)
        self.at_clip("S2-c13")
        self.play(type_in(concl, run_time=0.9))
        self.emphasize(concl, run_time=0.6)  # 2/5
        self.wait(0.3)
        self.transition_out(head2, f, ruler_grp, c1, c2, concl)
        self.pad_to_voice()


# ---------------- S3 STE 直通梯度 ----------------
class S3(_Base):
    def construct(self):
        self.bg()
        f = _footer(self)

        # 页1：阶梯函数 + 梯度归零
        head = t("量化不可微，怎么训练？", 36, YELL, "BOLD").to_edge(UP, buff=1.2)
        axes = Axes(x_range=[0, 6, 1], y_range=[0, 4, 1], x_length=5.4, y_length=3.6,
                    axis_config={"color": MUTED, "stroke_width": 2})
        steps = VGroup(*[Rectangle(width=0.9, height=0.5, color=CYAN, stroke_width=2)
                         for _ in range(5)])
        steps.arrange(RIGHT, buff=0.0)
        steps.next_to(axes.c2p(0.5, 0.5), UP, buff=0.1)
        chart = VGroup(axes, steps)
        bad = _card("导数处处是 0 → 梯度归零 → 训练死给你看", 6.8, 2.4, RED, WHITE, 34, CARD_FILL)
        page1 = page_stack(chart, bad, buff=1.4)
        layout_page(page1)

        self.at_clip("S3-c01")
        self.play(type_in(head, run_time=1.1), Create(axes), run_time=1.1)
        self.play_parallel(*[FadeIn(s, scale=0.5) for s in steps], run_time=0.9,
                           lag_ratio=0.15)  # 主视觉
        self.at_clip("S3-c04")
        self.play_scroll_unroll(bad, run_time=1.2)
        self.at_clip("S3-c05")
        self.wait(0.3)
        self.at_clip("S3-c06")

        # 页2：STE 双路径 + 实验对比
        head2 = t("STE：梯度原样穿墙", 36, YELL, "BOLD").to_edge(UP, buff=1.2)
        c1 = _card("前向：照常用量化后的权重", 6.6, 1.7, CYAN, WHITE, 34, CARD_FILL, "BOLD")
        c2 = _card("反传：假装量化器不存在，梯度穿墙", 6.6, 1.7, GREEN, WHITE, 34, CARD_FILL, "BOLD")
        c3 = _card("严格说这是错的，但它是 QAT 的事实标准", 6.6, 1.7, WHITE, WHITE, 34, CARD_FILL)
        page2 = page_stack(c1, c2, c3, buff=1.2)
        layout_page(page2)

        self.play(FadeOut(head), FadeOut(page1), type_in(head2, run_time=0.8),
                  run_time=0.8)
        self.at_clip("S3-c07")
        self.play_scroll_unroll(c1, run_time=1.0)
        self.at_clip("S3-c08")
        self.play_scroll_unroll(c2, run_time=1.0)  # 主视觉
        self.at_clip("S3-c09")
        self.play_scroll_unroll(c3, run_time=1.0)
        self.at_clip("S3-c11")

        # 页3：实验对比（矮页）
        head3 = t("实验：300 个 epoch", 36, YELL, "BOLD").to_edge(UP, buff=1.2)
        r1 = _card("截断：6.866 纹丝不动", 6.4, 1.6, RED, WHITE, 34, CARD_FILL)
        r2 = _card("STE：降到 0.993，离基线只差 4%", 6.4, 1.6, GREEN, WHITE, 34, CARD_FILL, "BOLD")
        page_auto(r1, r2)

        self.play(FadeOut(head2), FadeOut(page2), type_in(head3, run_time=0.8),
                  run_time=0.8)
        self.play_scroll_unroll(r1, run_time=1.0)
        self.at_clip("S3-c12")
        self.play_scroll_unroll(r2, run_time=1.2)
        self.emphasize(r2, run_time=0.6)  # 3/5
        self.wait(0.3)
        self.transition_out(head3, f, r1, r2)
        self.pad_to_voice()


# ---------------- S4 无损藏在回程 ----------------
class S4(_Base):
    def construct(self):
        self.bg()
        f = _footer(self)

        # 页1：有损 vs 回程零损失
        head = t("无损藏在回程", 36, YELL, "BOLD").to_edge(UP, buff=1.2)
        c1 = _card("主权重 → FP4：有损，25% 精度丢得明明白白", 6.8, 2.6, RED, WHITE, 34, CARD_FILL)
        c2 = _card("FP4 → FP8 回程：零信息损失", 6.8, 2.6, GREEN, WHITE, 34, CARD_FILL, "BOLD")
        page1 = page_stack(c1, c2, buff=2.4)
        layout_page(page1)

        self.at_clip("S4-c01")
        self.play(type_in(head, run_time=1.1))
        self.at_clip("S4-c03")
        self.play_scroll_unroll(c1, run_time=1.2)  # 主视觉
        self.at_clip("S4-c04")
        self.play_scroll_unroll(c2, run_time=1.2)
        self.at_clip("S4-c05")
        self.play(FadeOut(head), FadeOut(page1), run_time=0.5)

        # 页2：两个算术事实
        head2 = t("两个算术事实", 36, YELL, "BOLD").to_edge(UP, buff=1.2)
        f1 = _card("事实一：FP4 能表示的数，FP8 全能精确表示", 6.8, 1.8, CYAN, WHITE, 34, CARD_FILL, "BOLD")
        f2 = _card("E2M1 只会说半个、一个、一个半", 6.8, 1.6, WHITE, WHITE, 32, CARD_FILL)
        f3 = _card("事实二：scale 是 2 的幂，只移指数位", 6.8, 1.8, GREEN, WHITE, 34, CARD_FILL, "BOLD")
        page2 = page_stack(f1, f2, f3, buff=1.1)
        layout_page(page2)

        self.at_clip("S4-c06")
        self.play(type_in(head2, run_time=1.1))
        self.at_clip("S4-c07")
        self.play_scroll_unroll(f1, run_time=1.2)
        self.at_clip("S4-c08")
        self.play_scroll_unroll(f2, run_time=1.0)
        self.at_clip("S4-c11")
        self.play_scroll_unroll(f3, run_time=1.2)  # 主视觉
        self.at_clip("S4-c12")
        self.play(FadeOut(head2), FadeOut(page2), run_time=0.5)

        # 页3：就这？爆点（矮页）
        card = _card("就这？", 4.6, 1.8, YELL, WHITE, 56, CARD_FILL, "BOLD")
        sub = t("卡了两天没想通的无损，一句话就完了", 34, WHITE, "BOLD")
        page_auto(card, sub)

        self.play_scroll_unroll(card, run_time=1.2)
        self.at_clip("S4-c13")
        self.play(type_in(sub, run_time=0.9))
        self.emphasize(sub, run_time=0.6)  # 4/5
        self.wait(0.4)
        self.transition_out(f, card, sub)
        self.pad_to_voice()


# ---------------- S5 边界两千倍 + 显存账 ----------------
class S5(_Base):
    def construct(self):
        self.bg()
        f = _footer(self)

        # 页1：边界条件
        head = t("但有个边界", 36, YELL, "BOLD").to_edge(UP, buff=1.2)
        c1 = _card("E4M3 范围：最大 448，最小约 0.016", 6.6, 1.7, CYAN, WHITE, 34, CARD_FILL, "BOLD")
        c2 = _card("子块 scale 比值 ≤ 约两千倍", 6.6, 1.7, GREEN, WHITE, 34, CARD_FILL, "BOLD")
        c3 = _card("两千以内误差为 0；超过三千，溢出饱和", 6.6, 1.7, RED, WHITE, 34, CARD_FILL)
        page1 = page_stack(c1, c2, c3, buff=1.2)
        layout_page(page1)

        self.at_clip("S5-c01")
        self.play(type_in(head, run_time=1.1))
        self.at_clip("S5-c02")
        self.play_scroll_unroll(c1, run_time=1.0)
        self.at_clip("S5-c04")
        self.play_scroll_unroll(c2, run_time=1.0)  # 主视觉
        self.at_clip("S5-c06")
        self.play_scroll_unroll(c3, run_time=1.0)
        self.at_clip("S5-c08")

        # 页2：搬家比喻概念图
        head2 = t("打个比方：搬家", 36, YELL, "BOLD").to_edge(UP, buff=1.2)
        img = ImageMobject(str(IMG / "s5-move-round.png"))
        img.scale_to_fit_width(4.6)
        c1 = _card("4 位小箱子 → 8 位大箱子，格子更密放得下", 6.8, 1.8, CYAN, WHITE, 34, CARD_FILL, "BOLD")
        c2 = _card("但容量有上限，塞不下就扁了", 6.8, 1.8, RED, WHITE, 34, CARD_FILL)
        page2 = page_stack(img, c1, c2, buff=0.7)
        layout_page(page2)

        self.play(FadeOut(head), FadeOut(page1), type_in(head2, run_time=0.8),
                  FadeIn(img, shift=DOWN * 0.05), run_time=0.8)
        self.play_scroll_unroll(c1, run_time=1.2)
        self.at_clip("S5-c10")
        self.play_scroll_unroll(c2, run_time=1.2)  # 主视觉
        self.at_clip("S5-c11")
        self.wait(0.3)
        self.at_clip("S5-c13")

        # 页3：显存账
        head3 = t("算笔账：专家权重", 36, YELL, "BOLD").to_edge(UP, buff=1.2)
        r1_lab = t("FP8 存", 32, WHITE, "BOLD")
        bar1 = Rectangle(width=5.2, height=1.2, color=CYAN, fill_color=CYAN, fill_opacity=0.7)
        slot1 = dynamic_slot(2.0, 0.8)
        row1 = stable_row(r1_lab, bar1, slot1, buff=0.5)
        num1 = t("1.55 TB", 44, CYAN, "BOLD").move_to(slot1.get_center())
        r2_lab = t("FP4 存", 32, WHITE, "BOLD")
        bar2 = Rectangle(width=2.6, height=1.2, color=GREEN, fill_color=GREEN, fill_opacity=0.7)
        slot2 = dynamic_slot(2.0, 0.8)
        row2 = stable_row(r2_lab, bar2, slot2, buff=0.5)
        num2 = t("776 GB", 44, GREEN, "BOLD").move_to(slot2.get_center())
        note = t("1.55T 专家权重 · 占总参数 97% · H800 才 80 GB", 28, MUTED)
        page_auto(row1, row2, note)

        self.play(FadeOut(head2), FadeOut(page2), run_time=0.5)
        self.grow_bar(bar1, ValueTracker(0), 5.2, run_time=1.0, anchor="center",
                      extra_anims=[type_in(head3, run_time=0.8), type_in(r1_lab, run_time=0.6),
                                   type_in(num1, run_time=0.6)])  # 主视觉
        self.at_clip("S5-c14")
        self.grow_bar(bar2, ValueTracker(0), 2.6, run_time=1.0, anchor="center",
                      extra_anims=[type_in(r2_lab, run_time=0.6), type_in(num2, run_time=0.6)])
        self.at_clip("S5-c16")
        self.play(type_in(note, run_time=0.9))
        self.at_clip("S5-c18")
        self.play(FadeOut(head3), FadeOut(row1), FadeOut(row2), FadeOut(note),
                  FadeOut(num1), FadeOut(num2), run_time=0.5)

        # 页4：省下的显存（矮页）
        card = _card("省下 776 GB，够再装一个 7000 亿参数的模型", 7.0, 2.0, YELL, WHITE, 36, CARD_FILL, "BOLD")
        page_auto(card)

        self.play_scroll_unroll(card, run_time=1.2)
        self.emphasize(card, run_time=0.6)  # 5/5
        self.wait(0.4)
        self.transition_out(f, card)
        self.pad_to_voice()


# ---------------- S6 indexer 99.7% + 后训练 + 收尾 + 品牌尾卡 ----------------
class S6(_Base):
    def construct(self):
        self.bg()
        f = _footer(self)

        # 页1：indexer 两处量化
        head = t("indexer：99.7% 召回怎么保住", 34, YELL, "BOLD").to_edge(UP, buff=1.2)
        c1 = _card("① QK 路径全 FP4——连激活都量化，比权重更狠", 6.8, 1.8, CYAN, WHITE, 32, CARD_FILL, "BOLD")
        c2 = _card("② 分数 FP32 → BF16，选择器提速 2 倍", 6.8, 1.8, GREEN, WHITE, 32, CARD_FILL, "BOLD")
        c3 = _card("召回还停在 99.7%", 6.8, 1.8, YELL, WHITE, 36, CARD_FILL, "BOLD")
        page1 = page_stack(c1, c2, c3, buff=1.2)
        layout_page(page1)

        self.at_clip("S6-c01")
        self.play(type_in(head, run_time=1.1))
        self.at_clip("S6-c03")
        self.play_scroll_unroll(c1, run_time=1.2)  # 主视觉
        self.at_clip("S6-c05")
        self.play_scroll_unroll(c2, run_time=1.2)
        self.at_clip("S6-c06")
        self.play_scroll_unroll(c3, run_time=1.2)
        self.emphasize(c3, run_time=0.6)
        self.at_clip("S6-c07")

        # 页2：top-k 排序直觉（排名榜）
        head2 = t("top k 选的是排序，不是绝对值", 34, YELL, "BOLD").to_edge(UP, buff=1.2)
        rows = VGroup(*[boxed(f"第 {i} 名", 2.6, 0.9, MUTED, 26, weight="BOLD")
                        for i in [1, 2, 3, 1000]])
        rows.arrange(DOWN, buff=0.2)
        edge1 = boxed("第 1024 名", 2.6, 0.9, YELL, 26, weight="BOLD")
        edge2 = boxed("第 1025 名", 2.6, 0.9, YELL, 26, weight="BOLD")
        edges = VGroup(edge1, edge2).arrange(DOWN, buff=0.2)
        VGroup(rows, edges).arrange(RIGHT, buff=1.2)
        cap = t("BF16 扰动 0.4%：只有压线的名次可能互换", 30, WHITE, "BOLD")
        page2 = page_stack(rows, edges, cap, buff=0.9)
        layout_page(page2)

        self.play(FadeOut(head), FadeOut(page1), type_in(head2, run_time=0.8),
                  run_time=0.8)
        self.play_parallel(*[FadeIn(r, scale=0.5) for r in rows], run_time=0.9,
                           lag_ratio=0.15)  # 主视觉
        self.at_clip("S6-c09")
        self.play_parallel(*[FadeIn(e, scale=0.5) for e in edges], run_time=0.8,
                           lag_ratio=0.15)
        self.at_clip("S6-c10")
        self.play(type_in(cap, run_time=0.9))
        self.at_clip("S6-c12")

        # 页3：后训练 QAT + 金句
        head3 = t("为什么留到后训练？", 36, YELL, "BOLD").to_edge(UP, buff=1.2)
        c1 = _card("33 万亿 tokens 预训练全用 FP8", 6.6, 1.7, CYAN, WHITE, 34, CARD_FILL, "BOLD")
        c2 = _card("FP4 QAT 留到后训练：临门一脚，部署侧全链路受益", 6.6, 1.7, GREEN, WHITE, 32, CARD_FILL)
        concl = t("先学会知识，再学会在 16 个台阶上表达", 40, YELL, "BOLD")
        page_auto(c1, c2, concl)

        self.play(FadeOut(head2), FadeOut(page2), type_in(head3, run_time=0.8),
                  run_time=0.8)
        self.play_scroll_unroll(c1, run_time=1.0)
        self.at_clip("S6-c15")
        self.play_scroll_unroll(c2, run_time=1.0)  # 主视觉
        self.at_clip("S6-c17")
        self.play(type_in(concl, run_time=0.9))
        self.emphasize(concl, run_time=0.6)
        self.at_clip("S6-c18")
        self.play(FadeOut(head3), FadeOut(c1), FadeOut(c2), FadeOut(concl), run_time=0.5)

        # 页4：FP4 美学（矮页）
        card = _card("FP4 的美学：把有损量化放进训练里适应，把回程压缩做成无损", 7.0, 2.2, YELL, WHITE, 34, CARD_FILL, "BOLD")
        page_auto(card)

        self.play_scroll_unroll(card, run_time=1.2)
        self.at_clip("S6-c19")

        # 页5：品牌尾卡（终幕，不转场）
        avatar = ImageMobject(str(AVATAR))
        avatar.scale_to_fit_width(2.6)
        follow = t("关注「数解AI」", 40, YELL, "BOLD")
        title = t("《FP4量化：4位数字怎么做到无损》", 30, WHITE, "BOLD")
        if title.width > FW * 0.8:
            title.set_width(FW * 0.8)
        guide = t("查看公众号文章", 28, GREEN, "BOLD")
        next_lab = t("下一篇：KV 缓存存进 SSD——1M 上下文为什么能秒开", 24, MUTED)
        aq = t("你跑模型时，有没有被显存不够卡过？\n评论区聊聊", 22, MUTED)
        page5 = page_stack(avatar, follow, title, guide, next_lab, aq, buff=0.5)
        layout_page(page5)

        self.at_clip("S6-c19")
        self.play(FadeOut(card), FadeIn(avatar, scale=1.5), type_in(follow, run_time=0.8),
                  type_in(title, run_time=0.9), run_time=0.9)
        self.at_clip("S6-c20")
        self.play_parallel(type_in(guide, run_time=0.7), type_in(next_lab, run_time=0.8),
                           run_time=0.8)
        self.at_clip("S6-c21")
        self.play(type_in(aq, run_time=0.9))
        self.pad_to_voice()
