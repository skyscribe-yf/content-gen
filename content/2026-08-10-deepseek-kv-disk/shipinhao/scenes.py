#!/usr/bin/env python3
"""《KV缓存存进SSD：慢50倍的硬盘，为什么反而更快？》视频号 Manim 动画（竖屏 1080×1920）

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
VOICE_DUR = {"S1": 27.61, "S2": 49.99, "S3": 68.34, "S4": 50.66, "S5": 56.41, "S6": 73.07}
TAIL = 2.5


def _footer(self) -> Text:
    f = t("数解AI · 大模型原理", 20, MUTED).to_edge(DOWN, buff=1.15)
    self.add(f)
    return f


# ---------------- S1 开场钩子：同事秒回 vs 你等十几秒 ----------------
class S1(_Base):
    def construct(self):
        self.bg()
        f = _footer(self)

        # 页1：对话框概念图 + 秒回对比
        head = t("同一个问题，凭什么他秒回？", 36, YELL, "BOLD").to_edge(UP, buff=1.2)
        note0 = t("以 DeepSeek-V4 为例", 24, MUTED).next_to(head, DOWN, buff=0.5)
        img = ImageMobject(str(IMG / "s1-chat-round.png"))
        img.scale_to_fit_width(4.8)
        c1 = _card("你：等了十几秒", 3.4, 1.6, RED, WHITE, 34, CARD_FILL, "BOLD")
        c2 = _card("同事：秒回", 3.4, 1.6, GREEN, WHITE, 34, CARD_FILL, "BOLD")
        cards = VGroup(c1, c2).arrange(RIGHT, buff=0.5)
        page1 = page_stack(img, cards, buff=0.9)
        layout_page(page1)

        self.at_clip("S1-c01")
        self.play_parallel(type_in(head, run_time=1.1), FadeIn(note0, shift=DOWN * 0.05),
                           FadeIn(img, shift=DOWN * 0.05), run_time=1.1)
        self.at_clip("S1-c03")
        self.play_scroll_unroll_many(c1, c2, run_time=1.2)  # 主视觉
        self.at_clip("S1-c05")
        self.play(FadeOut(head), FadeOut(note0), FadeOut(page1), run_time=0.5)

        # 页2：答案在硬盘里（矮页）
        card = _card("答案不在显存里，在慢 50 倍的硬盘里", 6.8, 2.0, YELL, WHITE, 38, CARD_FILL, "BOLD")
        q = t("KV 缓存怎么进硬盘？", 44, YELL, "BOLD")
        q2 = t("进了硬盘，为什么反而快？", 30, MUTED)
        page_auto(card, q, q2)

        self.at_clip("S1-c06")
        self.play_scroll_unroll(card, run_time=1.2)
        self.at_clip("S1-c07")
        self.play_parallel(type_in(q, run_time=0.9), type_in(q2, run_time=0.8),
                           run_time=0.9)
        self.wait(0.3)
        self.transition_out(f, card, q, q2)
        self.pad_to_voice()


# ---------------- S2 prefill 为什么慢 ----------------
class S2(_Base):
    def construct(self):
        self.bg()
        f = _footer(self)

        # 页1：n² 增长 + 重复 prefill
        head = t("prefill：先读完才能回答", 34, YELL, "BOLD").to_edge(UP, buff=1.2)
        axes = Axes(x_range=[0, 6, 1], y_range=[0, 5, 1], x_length=5.4, y_length=3.8,
                    axis_config={"color": MUTED, "stroke_width": 2})
        curve = axes.plot(lambda x: 0.12 * x * x, color=RED, stroke_width=4)
        lab = t("序列长一倍，计算量涨四倍", 30, RED, "BOLD").next_to(curve.get_end(), RIGHT, buff=0.2)
        chart = VGroup(axes, curve, lab)
        c1 = _card("同一个文档被问 100 次，前 99 次都在算同一段前缀", 6.8, 2.2, RED, WHITE, 32, CARD_FILL)
        page1 = page_stack(chart, c1, buff=1.2)
        layout_page(page1)

        self.at_clip("S2-c01")
        self.play(type_in(head, run_time=1.1), Create(axes), run_time=1.1)
        self.play(Create(curve), run_time=1.0)  # 主视觉
        self.at_clip("S2-c05")
        self.play(type_in(lab, run_time=0.8))
        self.at_clip("S2-c06")
        self.play_scroll_unroll(c1, run_time=1.2)
        self.at_clip("S2-c08")
        self.play(FadeOut(head), FadeOut(page1), run_time=0.5)

        # 页2：KV 复用 + 存哪？→ SSD
        head2 = t("算过的结果，存起来复用", 34, YELL, "BOLD").to_edge(UP, buff=1.2)
        c1 = _card("算过的中间结果 = KV 缓存", 6.6, 1.7, CYAN, WHITE, 34, CARD_FILL, "BOLD")
        c2 = _card("把「读文档」变成「查档案」", 6.6, 1.7, GREEN, WHITE, 34, CARD_FILL, "BOLD")
        c3 = _card("一百万 token 的 KV 缓存占几十 GB 显存，一张卡放不下", 6.8, 1.8, RED, WHITE, 32, CARD_FILL)
        c4 = _card("DeepSeek-V4 的决定：把 KV 缓存存进 SSD", 6.8, 1.8, YELL, WHITE, 34, CARD_FILL, "BOLD")
        page2 = page_stack(c1, c2, c3, c4, buff=0.6)
        layout_page(page2)

        self.at_clip("S2-c09")
        self.play(type_in(head2, run_time=1.1))
        self.at_clip("S2-c11")
        self.play_scroll_unroll_many(c1, c2, run_time=1.2)  # 主视觉
        self.at_clip("S2-c12")
        self.play_scroll_unroll(c3, run_time=1.2)
        self.at_clip("S2-c15")
        self.play_scroll_unroll(c4, run_time=1.2)
        self.emphasize(c4, run_time=0.6)  # 1/5
        self.wait(0.3)
        self.transition_out(head2, f, c1, c2, c3, c4)
        self.pad_to_voice()


# ---------------- S3 慢 50 倍为什么反而划算 ----------------
class S3(_Base):
    def construct(self):
        self.bg()
        f = _footer(self)

        # 页1：带宽对比 + 反直觉
        head = t("慢 50 倍的硬盘，为什么划算？", 34, YELL, "BOLD").to_edge(UP, buff=1.2)
        r1_lab = t("显存带宽", 32, WHITE, "BOLD")
        bar1 = Rectangle(width=5.4, height=1.6, color=CYAN, fill_color=CYAN, fill_opacity=0.7)
        slot1 = dynamic_slot(2.6, 0.8)
        row1 = stable_row(r1_lab, bar1, slot1, buff=0.5)
        num1 = t("1-3 TB/s", 40, CYAN, "BOLD").move_to(slot1.get_center())
        r2_lab = t("SSD 顺序读", 32, WHITE, "BOLD")
        bar2 = Rectangle(width=1.1, height=1.6, color=GREEN, fill_color=GREEN, fill_opacity=0.7)
        slot2 = dynamic_slot(2.6, 0.8)
        row2 = stable_row(r2_lab, bar2, slot2, buff=0.5)
        num2 = t("3-7 GB/s", 40, GREEN, "BOLD").move_to(slot2.get_center())
        c1 = _card("反直觉：prefill 的瓶颈不是带宽，是计算", 6.8, 2.2, YELL, WHITE, 34, CARD_FILL, "BOLD")
        page1 = page_stack(row1, row2, c1, buff=1.2)
        layout_page(page1)

        self.at_clip("S3-c01")
        self.grow_bar(bar1, ValueTracker(0), 5.4, run_time=1.0, anchor="center",
                      extra_anims=[type_in(head, run_time=0.8), type_in(r1_lab, run_time=0.6),
                                   type_in(num1, run_time=0.6)])  # 主视觉
        self.at_clip("S3-c04")
        self.grow_bar(bar2, ValueTracker(0), 1.1, run_time=1.0, anchor="center",
                      extra_anims=[type_in(r2_lab, run_time=0.6), type_in(num2, run_time=0.6)])
        self.at_clip("S3-c06")
        self.play_scroll_unroll(c1, run_time=1.2)
        self.at_clip("S3-c07")
        self.play(FadeOut(head), FadeOut(page1), run_time=0.5)

        # 页2：读盘 vs 重算账
        head2 = t("算一笔账", 36, YELL, "BOLD").to_edge(UP, buff=1.2)
        c1 = _card("100 万 token 的文档，KV 缓存约 10 GB", 6.6, 1.7, CYAN, WHITE, 34, CARD_FILL, "BOLD")
        c2 = _card("从 SSD 读回来：约 2 秒", 6.6, 1.7, GREEN, WHITE, 34, CARD_FILL, "BOLD")
        c3 = _card("重新 prefill：要几十秒", 6.6, 1.7, RED, WHITE, 34, CARD_FILL, "BOLD")
        concl = t("2 秒读盘，换掉几十秒的计算", 40, YELL, "BOLD")
        page2 = page_stack(c1, c2, c3, concl, buff=0.8)
        layout_page(page2)

        self.at_clip("S3-c12")
        self.play(type_in(head2, run_time=1.1))
        self.at_clip("S3-c13")
        self.play_scroll_unroll(c1, run_time=1.0)
        self.at_clip("S3-c14")
        self.play_scroll_unroll(c2, run_time=1.0)  # 主视觉
        self.at_clip("S3-c15")
        self.play_scroll_unroll(c3, run_time=1.0)
        self.at_clip("S3-c16")
        self.play(type_in(concl, run_time=0.9))
        self.emphasize(concl, run_time=0.6)  # 2/5
        self.at_clip("S3-c17")

        # 页3：线性 vs 二次交叉曲线
        head3 = t("线性 vs 平方：必然相交", 34, YELL, "BOLD").to_edge(UP, buff=1.2)
        axes = Axes(x_range=[0, 6, 1], y_range=[0, 5, 1], x_length=5.4, y_length=3.4,
                    axis_config={"color": MUTED, "stroke_width": 2})
        lin = axes.plot(lambda x: 0.5 * x, color=GREEN, stroke_width=4)
        quad = axes.plot(lambda x: 0.12 * x * x, color=RED, stroke_width=4)
        lab1 = t("读盘：线性", 26, GREEN, "BOLD").next_to(lin.get_end(), RIGHT, buff=0.2)
        lab2 = t("重算：平方", 26, RED, "BOLD").next_to(quad.get_end(), RIGHT, buff=0.2)
        chart = VGroup(axes, lin, quad, lab1, lab2)
        c1 = _card("交点 ≈ 三万六千 token：之后读盘通吃", 6.8, 1.8, YELL, WHITE, 34, CARD_FILL, "BOLD")
        c2 = _card("一百万 token：读盘 2 秒 vs 重算 60 秒，快 30 倍", 6.8, 1.8, GREEN, WHITE, 32, CARD_FILL, "BOLD")
        page3 = page_stack(chart, c1, c2, buff=0.7)
        layout_page(page3)

        self.play(FadeOut(head2), FadeOut(page2), type_in(head3, run_time=0.8),
                  run_time=0.8)
        self.play_parallel(Create(lin), Create(quad), run_time=1.0)  # 主视觉
        self.play_parallel(type_in(lab1, run_time=0.5), type_in(lab2, run_time=0.5),
                           run_time=0.5)
        self.at_clip("S3-c19")
        self.play_scroll_unroll(c1, run_time=1.2)
        self.at_clip("S3-c23")
        self.play_scroll_unroll(c2, run_time=1.2)
        self.emphasize(c2, run_time=0.6)  # 3/5
        self.wait(0.3)
        self.transition_out(head3, f, chart, c1, c2)
        self.pad_to_voice()


# ---------------- S4 KV 不是一种东西 ----------------
class S4(_Base):
    def construct(self):
        self.bg()
        f = _footer(self)

        # 页1：档案 vs 状态分类
        head = t("KV 不是一种东西", 36, YELL, "BOLD").to_edge(UP, buff=1.2)
        c1 = _card("档案：压缩后的长期 KV，跨请求复用价值高", 6.8, 1.8, CYAN, WHITE, 32, CARD_FILL, "BOLD")
        c2 = _card("状态：滑动窗口缓存，只随窗口滚动", 6.8, 1.8, GREEN, WHITE, 32, CARD_FILL)
        c3 = _card("状态：没凑够压缩块的半成品", 6.8, 1.8, WHITE, WHITE, 32, CARD_FILL)
        concl = t("档案进硬盘，状态留显存", 40, YELL, "BOLD")
        page1 = page_stack(c1, c2, c3, concl, buff=0.8)
        layout_page(page1)

        self.at_clip("S4-c01")
        self.play(type_in(head, run_time=1.1))
        self.at_clip("S4-c04")
        self.play_scroll_unroll(c1, run_time=1.2)  # 主视觉
        self.at_clip("S4-c05")
        self.play_scroll_unroll(c2, run_time=1.0)
        self.at_clip("S4-c06")
        self.play_scroll_unroll(c3, run_time=1.0)
        self.at_clip("S4-c07")
        self.play(FadeOut(head), FadeOut(page1), run_time=0.5)

        # 页2：两套缓存 + 结论
        head2 = t("两套缓存系统", 36, YELL, "BOLD").to_edge(UP, buff=1.2)
        c1 = _card("状态缓存：装滑动窗口和半成品，固定大小块", 6.8, 1.8, GREEN, WHITE, 32, CARD_FILL, "BOLD")
        c2 = _card("经典 KV 缓存：装压缩条目，按块覆盖 token 区间", 6.8, 1.8, CYAN, WHITE, 32, CARD_FILL, "BOLD")
        concl = t("档案库 + 状态机，不是统一的历史仓库", 38, YELL, "BOLD")
        page2 = page_stack(c1, c2, concl, buff=1.6)
        layout_page(page2)

        self.at_clip("S4-c09")
        self.play(type_in(head2, run_time=1.1))
        self.at_clip("S4-c10")
        self.play_scroll_unroll(c1, run_time=1.2)  # 主视觉
        self.at_clip("S4-c11")
        self.play_scroll_unroll(c2, run_time=1.2)
        self.at_clip("S4-c12")
        self.play(type_in(concl, run_time=0.9))
        self.emphasize(concl, run_time=0.6)  # 4/5
        self.at_clip("S4-c14")
        self.wait(0.3)
        self.transition_out(head2, f, c1, c2, concl)
        self.pad_to_voice()


# ---------------- S5 lcm 对齐 + 半成品不落盘 ----------------
class S5(_Base):
    def construct(self):
        self.bg()
        f = _footer(self)

        # 页1：块边界错位 → lcm 对齐
        head = t("档案怎么对齐：lcm", 36, YELL, "BOLD").to_edge(UP, buff=1.2)
        c1 = _card("CSA 每 4 个 token 产 1 个条目 · HCA 每 128 个产 1 个", 6.8, 1.8, CYAN, WHITE, 32, CARD_FILL, "BOLD")
        c2 = _card("两个分支的块边界对不上，按块检索就乱套", 6.8, 1.8, RED, WHITE, 34, CARD_FILL)
        c3 = _card("每个缓存块覆盖 lcm(4,128) = 128 个原始 token", 6.8, 1.8, GREEN, WHITE, 32, CARD_FILL, "BOLD")
        c4 = _card("lcm 是最小的对齐块——块越小，检索粒度越细", 6.8, 1.8, YELL, WHITE, 32, CARD_FILL)
        page1 = page_stack(c1, c2, c3, c4, buff=0.6)
        layout_page(page1)

        self.at_clip("S5-c01")
        self.play(type_in(head, run_time=1.1))
        self.at_clip("S5-c02")
        self.play_scroll_unroll(c1, run_time=1.0)
        self.at_clip("S5-c04")
        self.play_scroll_unroll(c2, run_time=1.0)  # 主视觉
        self.at_clip("S5-c06")
        self.play_scroll_unroll(c3, run_time=1.2)
        self.at_clip("S5-c08")
        self.play_scroll_unroll(c4, run_time=1.2)
        self.at_clip("S5-c11")

        # 页2：半成品不落盘 + 档案柜概念图
        head2 = t("什么能落盘，什么只能重算", 34, YELL, "BOLD").to_edge(UP, buff=1.2)
        img = ImageMobject(str(IMG / "s5-archive-round.png"))
        img.scale_to_fit_width(4.2)
        c1 = _card("压缩 KV 全部落盘，但只复用到最后一个完整块", 6.8, 1.8, CYAN, WHITE, 32, CARD_FILL, "BOLD")
        c2 = _card("半成品不落盘——下次命中，最后几个 token 重新 prefill", 6.8, 1.8, RED, WHITE, 32, CARD_FILL)
        c3 = _card("档案柜只收整理好的文件；半成品留在桌面", 6.8, 1.8, GREEN, WHITE, 32, CARD_FILL, "BOLD")
        page2 = page_stack(img, c1, c2, c3, buff=0.6)
        layout_page(page2)

        self.play(FadeOut(head), FadeOut(page1), type_in(head2, run_time=0.8),
                  FadeIn(img, shift=DOWN * 0.05), run_time=0.8)
        self.play_scroll_unroll(c1, run_time=1.0)
        self.at_clip("S5-c13")
        self.play_scroll_unroll(c2, run_time=1.2)  # 主视觉
        self.at_clip("S5-c15")
        self.play_scroll_unroll(c3, run_time=1.2)
        self.wait(0.3)
        self.play(FadeOut(img), run_time=0.6)
        self.transition_out(head2, f, c1, c2, c3)
        self.pad_to_voice()


# ---------------- S6 SWA 三策略 + 秒回链路 + 品牌尾卡 ----------------
class S6(_Base):
    def construct(self):
        self.bg()
        f = _footer(self)

        # 页1：SWA 8 倍 + 三策略
        head = t("最难伺候的：滑动窗口缓存", 34, YELL, "BOLD").to_edge(UP, buff=1.2)
        c1 = _card("不压缩、每一层都有，体积约是压缩档案的 8 倍", 6.8, 1.8, RED, WHITE, 32, CARD_FILL)
        c2 = _card("全量缓存：几乎零重算，但存储压力最大", 6.8, 1.7, CYAN, WHITE, 32, CARD_FILL)
        c3 = _card("周期检查点：两头各付一半", 6.8, 1.7, GREEN, WHITE, 32, CARD_FILL)
        c4 = _card("零缓存：重算量有界，约 7800 token，零点几秒", 6.8, 1.7, YELL, WHITE, 32, CARD_FILL, "BOLD")
        page1 = page_stack(c1, c2, c3, c4, buff=0.6)
        layout_page(page1)

        self.at_clip("S6-c01")
        self.play(type_in(head, run_time=1.1))
        self.at_clip("S6-c02")
        self.play_scroll_unroll(c1, run_time=1.2)  # 主视觉
        self.at_clip("S6-c05")
        self.play_scroll_unroll(c2, run_time=1.0)
        self.at_clip("S6-c07")
        self.play_scroll_unroll(c3, run_time=1.0)
        self.at_clip("S6-c08")
        self.play_scroll_unroll(c4, run_time=1.2)
        self.at_clip("S6-c10")
        self.play(FadeOut(head), FadeOut(page1), run_time=0.5)

        # 页2：秒回链路
        head2 = t("同事的秒回 = 一条链路", 34, YELL, "BOLD").to_edge(UP, buff=1.2)
        c1 = _card("共享前缀命中 → 跳过 prefill", 6.6, 1.6, CYAN, WHITE, 34, CARD_FILL, "BOLD")
        c2 = _card("压缩 KV 落盘可复用", 6.6, 1.6, GREEN, WHITE, 34, CARD_FILL, "BOLD")
        c3 = _card("分层让落盘可行 · lcm 对齐让检索高效", 6.6, 1.6, YELL, WHITE, 34, CARD_FILL, "BOLD")
        concl = t("2 秒读盘，换掉十几秒重算", 40, YELL, "BOLD")
        page2 = page_stack(c1, c2, c3, concl, buff=0.8)
        layout_page(page2)

        self.at_clip("S6-c11")
        self.play(type_in(head2, run_time=1.1))
        self.at_clip("S6-c12")
        self.play_scroll_unroll_many(c1, c2, run_time=1.2)  # 主视觉
        self.at_clip("S6-c13")
        self.play_scroll_unroll(c3, run_time=1.0)
        self.at_clip("S6-c16")
        self.play(type_in(concl, run_time=0.9))
        self.emphasize(concl, run_time=0.6)  # 5/5
        self.at_clip("S6-c17")
        self.play(FadeOut(head2), FadeOut(page2), run_time=0.5)

        # 页3：金句（矮页）
        card = _card("慢 50 倍的硬盘，赢在把最贵的算力省了下来", 7.0, 2.0, YELL, WHITE, 36, CARD_FILL, "BOLD")
        page_auto(card)

        self.play_scroll_unroll(card, run_time=1.2)
        self.at_clip("S6-c18")

        # 页4：品牌尾卡（终幕，不转场）
        avatar = ImageMobject(str(AVATAR))
        avatar.scale_to_fit_width(2.6)
        follow = t("关注「数解AI」", 40, YELL, "BOLD")
        title = t("《KV缓存存进SSD：慢50倍的硬盘，为什么反而更快？》", 28, WHITE, "BOLD")
        if title.width > FW * 0.8:
            title.set_width(FW * 0.8)
        guide = t("查看公众号文章", 28, GREEN, "BOLD")
        next_lab = t("下一篇：Lightning Indexer——注意力怎么学会只看重点", 24, MUTED)
        aq = t("如果 KV 能存进 SSD，下一步该把什么存进硬盘？\n评论区聊聊", 22, MUTED)
        page4 = page_stack(avatar, follow, title, guide, next_lab, aq, buff=0.5)
        layout_page(page4)

        self.play(FadeOut(card), FadeIn(avatar, scale=1.5), type_in(follow, run_time=0.8),
                  type_in(title, run_time=0.9), run_time=0.9)
        self.at_clip("S6-c19")
        self.play_parallel(type_in(guide, run_time=0.7), type_in(next_lab, run_time=0.8),
                           run_time=0.8)
        self.at_clip("S6-c20")
        self.play(type_in(aq, run_time=0.9))
        self.pad_to_voice()
