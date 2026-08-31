#!/usr/bin/env python3
"""《DeepEP：训练时GPU的空等怎么藏起来》视频号 Manim 动画（竖屏 1080×1920）

6 个场景 S1-S6，与 storyboard.md 一一对应。
- 配音：MiniMax 克隆作者音色（speech-2.8-turbo，speed 1.0 pitch +2）
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

# 每段配音时长（tts_split.py 实测 2026-09-03），渲染时长 = 配音 + TAIL
VOICE_DUR = {"S1": 24.01, "S2": 44.81, "S3": 64.84, "S4": 51.31, "S5": 51.16, "S6": 42.07}
TAIL = 2.5


def _footer(self) -> Text:
    f = t("数解AI · DeepSeek 技术解密", 20, MUTED).to_edge(DOWN, buff=1.15)
    self.add(f)
    return f


def _head(text: str, size: float = 38) -> Text:
    return t(text, size, YELL, "BOLD").to_edge(UP, buff=1.2)


# ---------------- S1 开场钩子：20 万的 GPU 在等 ----------------
class S1(_Base):
    def construct(self):
        self.bg()
        f = _footer(self)

        # 页1：概念图（食堂打饭）+ 利用率 60% 数字滚动
        head = _head("20 万的 GPU，真正在算的时间有多少？", 32)
        note0 = t("以 DeepSeek-V4 训练为例", 24, MUTED).next_to(head, DOWN, buff=0.5)
        img = ImageMobject(str(IMG / "s1-canteen-round.png"))
        img.scale_to_fit_width(6.0)
        lab = t("GPU 利用率", 34, WHITE, "BOLD")
        slot = dynamic_slot(2.2, 0.9)
        util_row = stable_row(lab, slot, buff=0.4)
        cap = t("只有六成多——剩下四成在等", 30, WHITE)
        page1 = page_stack(img, util_row, cap, buff=0.9)
        layout_page(page1)

        self.at_clip("S1-c01")
        self.play_parallel(type_in(head, run_time=1.1), FadeIn(note0, shift=DOWN * 0.05),
                           FadeIn(img, shift=DOWN * 0.05), run_time=1.1)
        self.at_clip("S1-c02")
        self.play(type_in(cap, run_time=0.9))
        self.at_clip("S1-c03")
        n = self.counter_value(0, 60, suffix="%", size=72, color=YELL,
                               run_time=1.2, anchor=slot,
                               extra_anims=[type_in(lab, run_time=0.6)])  # 主视觉：数字滚动
        self.at_clip("S1-c04")

        # 页2：两处等待（换页与页1 FadeOut 同拍）
        head2 = _head("模型没错——它是在等", 40)
        c1 = _card("等上游：数据传不下来", 3.6, 3.0, CYAN, WHITE, 36, CARD_FILL, "BOLD")
        c2 = _card("等网络：all-to-all 传不完", 3.6, 3.0, GREEN, WHITE, 36, CARD_FILL, "BOLD")
        cards = VGroup(c1, c2).arrange(RIGHT, buff=0.4)
        big = t("两处空等", 60, YELL, "BOLD")
        sub = t("就是最贵的浪费", 34, WHITE)
        page2 = page_stack(cards, big, sub, buff=1.4)
        layout_page(page2)

        self.play(FadeOut(head), FadeOut(note0), FadeOut(page1), FadeOut(n),
                  type_in(head2, run_time=0.9), run_time=0.9)
        self.emphasize(head2, run_time=0.6)  # 1/5
        self.at_clip("S1-c05")
        self.play_scroll_unroll_many(c1, c2, run_time=1.2)  # 主视觉：拉幕
        self.at_clip("S1-c06")
        self.play(type_in(big, run_time=0.8), type_in(sub, run_time=0.8), run_time=0.9)
        self.wait(2.03)  # 补到 c06 结束（24.06），台词讲完再转场
        self.transition_out(head2, f, c1, c2, big, sub)
        self.pad_to_voice()


# ---------------- S2 等待1：气泡 + DualPipe ----------------
class S2(_Base):
    def construct(self):
        self.bg()
        f = _footer(self)

        # 页1：流水线工件 + 气泡
        head = _head("第一处空等：气泡", 40)
        works = VGroup(*[Rectangle(width=1.1, height=1.3, color=YELL,
                                   fill_color=YELL, fill_opacity=0.25) for _ in range(4)])
        works.arrange(RIGHT, buff=0.5)
        stages = VGroup(*[Rectangle(width=1.8, height=2.2, color=CYAN,
                                    fill_color=CYAN, fill_opacity=0.15) for _ in range(4)])
        stages.arrange(RIGHT, buff=0.2)
        arrows = VGroup(*[Arrow(works[i].get_bottom(), stages[i].get_top(),
                                color=MUTED, buff=0.1, stroke_width=3) for i in range(4)])
        bubble1 = DashedVMobject(Rectangle(width=1.8, height=2.2, color=RED, stroke_width=3))
        bubble1.move_to(stages[1].get_center())
        bubble2 = DashedVMobject(Rectangle(width=1.8, height=2.2, color=RED, stroke_width=3))
        bubble2.move_to(stages[2].get_center())
        line1 = t("micro-batch 像流水线上的工件，一个接一个灌进去", 26, WHITE)
        line2 = t("工件还没到，工位先空着", 34, YELL, "BOLD")
        page1 = page_stack(works, stages, line1, line2, buff=1.0)
        layout_page(page1)

        self.at_clip("S2-c01")
        self.play(type_in(head, run_time=0.9))
        self.at_clip("S2-c02")
        self.play(*[Create(w) for w in works], *[Create(a) for a in arrows],
                  type_in(line1, run_time=0.9), run_time=1.2, lag_ratio=0.3)  # 主视觉：工件逐段
        self.at_clip("S2-c03")
        self.play(*[Create(s) for s in stages], run_time=0.8, lag_ratio=0.2)
        self.at_clip("S2-c04")
        self.play(Create(bubble1), Create(bubble2), run_time=0.5)
        # 两个红叉合并为一个 play（预检器：连续单动画 reveal 需合并）
        x1a = Line(stages[1].get_corner(UL) + RIGHT * 0.15 + DOWN * 0.15,
                   stages[1].get_corner(DR) + LEFT * 0.15 + UP * 0.15,
                   color=RED, stroke_width=14)
        x1b = Line(stages[1].get_corner(UR) + LEFT * 0.15 + DOWN * 0.15,
                   stages[1].get_corner(DL) + RIGHT * 0.15 + UP * 0.15,
                   color=RED, stroke_width=14)
        x2a = Line(stages[2].get_corner(UL) + RIGHT * 0.15 + DOWN * 0.15,
                   stages[2].get_corner(DR) + LEFT * 0.15 + UP * 0.15,
                   color=RED, stroke_width=14)
        x2b = Line(stages[2].get_corner(UR) + LEFT * 0.15 + DOWN * 0.15,
                   stages[2].get_corner(DL) + RIGHT * 0.15 + UP * 0.15,
                   color=RED, stroke_width=14)
        cross1 = VGroup(x1a, x1b)
        cross2 = VGroup(x2a, x2b)
        self.play(GrowFromCenter(x1a), GrowFromCenter(x1b),
                  GrowFromCenter(x2a), GrowFromCenter(x2b), run_time=0.5)
        self.play(cross1.animate.scale(1.1), cross2.animate.scale(1.1), run_time=0.1)
        self.play(cross1.animate.scale(1 / 1.1), cross2.animate.scale(1 / 1.1), run_time=0.1)
        self.play(type_in(line2, run_time=0.8))
        self.at_clip("S2-c05")

        # 页2：1F1B 公式 + 15 个块
        head2 = _head("1F1B 调度下的气泡账", 38)
        card0 = _card("1F1B：micro-batch 单向灌入", 5.6, 2.0, CYAN, WHITE, 32, CARD_FILL, "BOLD")
        formula = t("气泡 = (PP−1)(F+B)", 48, WHITE, "BOLD")
        lab2 = t("PP = 16 时", 34, WHITE, "BOLD")
        slot2 = dynamic_slot(2.0, 0.9)
        num_row = stable_row(lab2, slot2, buff=0.4)
        line3 = t("气泡相当于 15 个前向加反向块的时间", 30, WHITE)
        page2 = page_stack(card0, formula, num_row, line3, buff=1.0)
        layout_page(page2)

        self.play(FadeOut(head), FadeOut(page1), FadeOut(cross1), FadeOut(cross2),
                  FadeOut(bubble1), FadeOut(bubble2), FadeOut(arrows),
                  type_in(head2, run_time=0.8), run_time=0.8)
        self.play_scroll_unroll(card0, run_time=1.0)  # 主视觉：拉幕
        self.at_clip("S2-c06")
        n2 = self.counter_value(0, 15, suffix=" 个块", size=72, color=YELL,
                                run_time=1.2, anchor=slot2,
                                extra_anims=[type_in(formula, run_time=1.0),
                                             type_in(lab2, run_time=0.6),
                                             type_in(line3, run_time=0.9)])  # 主视觉：数字滚动
        self.at_clip("S2-c07")

        # 页3：DualPipe 双向调度 + chunk 四段 + 气泡减半对比
        head3 = _head("V3 的 DualPipe 怎么填？", 38)
        pipe = Rectangle(width=5.2, height=1.5, color=CYAN, fill_color=CYAN, fill_opacity=0.12)
        ar_l = Arrow(pipe.get_left() + LEFT * 0.3, pipe.get_left(), color=YELL, buff=0, stroke_width=6)
        ar_r = Arrow(pipe.get_right() + RIGHT * 0.3, pipe.get_right(), color=YELL, buff=0, stroke_width=6)
        lab_l = t("灌入", 24, YELL, "BOLD").next_to(ar_l, LEFT, buff=0.12)
        lab_r = t("灌入", 24, YELL, "BOLD").next_to(ar_r, RIGHT, buff=0.12)
        pipe_grp = VGroup(pipe, ar_l, ar_r, lab_l, lab_r)  # 箭头/标签随 pipe 一起布局
        chunks = VGroup(*[Rectangle(width=1.5, height=1.1, color=GREEN,
                                   fill_color=GREEN, fill_opacity=0.2) for _ in range(4)])
        chunks.arrange(RIGHT, buff=0.25)
        chunk_labs = [t(x, 20, WHITE, "BOLD") for x in ["attention", "dispatch", "MLP", "combine"]]
        for cl, ch in zip(chunk_labs, chunks):
            cl.set_width(1.3)
            cl.move_to(ch.get_center())
        chunk_grp = VGroup(*[VGroup(ch, cl) for ch, cl in zip(chunks, chunk_labs)])
        bar1 = Rectangle(width=2.2, height=1.4, color=RED, fill_color=RED, fill_opacity=0.5)
        bar2 = Rectangle(width=1.1, height=1.4, color=GREEN, fill_color=GREEN, fill_opacity=0.5)
        bars = VGroup(bar1, bar2).arrange(RIGHT, buff=0.8)
        lab_old = t("1F1B：15", 26, WHITE, "BOLD").next_to(bar1, UP, buff=0.2)
        lab_new = t("DualPipe：7", 26, WHITE, "BOLD").next_to(bar2, UP, buff=0.2)
        bars.add(lab_old, lab_new)  # 标签随 bars 一起布局
        line4 = t("气泡直接减半以上", 36, YELL, "BOLD")
        page3 = page_stack(pipe_grp, chunk_grp, bars, line4, buff=0.9)
        layout_page(page3)

        self.play(FadeOut(head2), FadeOut(page2), FadeOut(n2),
                  type_in(head3, run_time=0.8), run_time=0.8)
        self.at_clip("S2-c08")
        self.play(Create(pipe), run_time=0.6)
        self.play(Create(ar_l), Create(ar_r), type_in(lab_l, 0.5), type_in(lab_r, 0.5),
                  run_time=0.8)  # 主视觉：双向箭头
        self.play_scroll_unroll_many(*chunk_grp, run_time=1.2)
        self.at_clip("S2-c09")
        self.play(type_in(line4, run_time=0.8))
        self.at_clip("S2-c10")
        self.play(GrowFromEdge(bar1, LEFT), GrowFromEdge(bar2, LEFT),
                  type_in(lab_old, 0.5), type_in(lab_new, 0.5), run_time=1.0)
        self.emphasize(line4, run_time=0.6)  # 2/5
        self.at_clip("S2-c11")

        # 页4：代价 + 结论
        head4 = _head("代价与答案", 38)
        c1 = _card("代价：两份参数拷贝", 6.4, 2.2, RED, WHITE, 38, CARD_FILL, "BOLD")
        c2 = _card("但每张卡只持有一小份，不贵", 6.4, 2.2, GREEN, WHITE, 38, CARD_FILL, "BOLD")
        concl = t("V4 还在用 DualPipe", 44, YELL, "BOLD")
        page4 = page_stack(c1, c2, concl, buff=1.1)
        layout_page(page4)

        self.play(FadeOut(head3), FadeOut(page3),
                  type_in(head4, run_time=0.8), run_time=0.8)
        self.play_scroll_unroll_many(c1, c2, run_time=1.2)  # 主视觉：拉幕
        self.at_clip("S2-c12")
        self.play(type_in(concl, run_time=0.9))
        self.wait(2.58)  # 补到 c12 结束（44.88），台词讲完再转场
        self.transition_out(head4, f, c1, c2, concl)
        self.pad_to_voice()


# ---------------- S3 等待2：all-to-all + DeepEP 三件真货 ----------------
class S3(_Base):
    def construct(self):
        self.bg()
        f = _footer(self)

        # 页1：all-to-all 问题 + 16GB + 带宽对比
        head = _head("第二处空等：all-to-all", 40)
        tok = Rectangle(width=1.2, height=1.3, color=YELL, fill_color=YELL, fill_opacity=0.25)
        experts = VGroup(*[Rectangle(width=1.4, height=2.0, color=CYAN,
                                     fill_color=CYAN, fill_opacity=0.15) for _ in range(3)])
        experts.arrange(RIGHT, buff=0.3)
        exp_labs = [t("专家", 24, WHITE, "BOLD") for _ in range(3)]
        for el, ex in zip(exp_labs, experts):
            el.move_to(ex.get_center())
        exp_grp = VGroup(*[VGroup(ex, el) for ex, el in zip(experts, exp_labs)])
        tok.next_to(exp_grp, LEFT, buff=0.5)  # token 在专家左侧，不压中心专家
        tok_lab = t("token", 24, WHITE, "BOLD").move_to(tok.get_center())
        d_arrow = Arrow(tok.get_right(), experts[0].get_left(), color=YELL, buff=0.15, stroke_width=5)
        dispatch_row = VGroup(tok, tok_lab, d_arrow, exp_grp)
        lab_gb = t("每层要传约", 30, WHITE, "BOLD")
        slot_gb = dynamic_slot(2.4, 0.9)
        gb_row = stable_row(lab_gb, slot_gb, buff=0.4)
        bw1 = Rectangle(width=3.4, height=1.0, color=GREEN, fill_color=GREEN, fill_opacity=0.5)
        bw2 = Rectangle(width=0.4, height=1.0, color=RED, fill_color=RED, fill_opacity=0.5)
        bws = VGroup(bw1, bw2).arrange(RIGHT, buff=0.6)
        lab_nv = t("NVLink 900 GB/s", 24, WHITE, "BOLD").next_to(bw1, UP, buff=0.2)
        lab_ib = t("IB 50 GB/s", 24, WHITE, "BOLD").next_to(bw2, UP, buff=0.2)
        bws.add(lab_nv, lab_ib)  # 标签随 bars 一起布局
        line1 = t("跨节点带宽只有 NVLink 的约十八分之一", 30, WHITE)
        page1 = page_stack(dispatch_row, gb_row, bws, line1, buff=1.0)
        layout_page(page1)

        self.at_clip("S3-c01")
        self.play(type_in(head, run_time=0.9))
        self.at_clip("S3-c02")
        self.play(FadeIn(tok, scale=0.5), type_in(tok_lab, 0.5),
                  Create(d_arrow), run_time=0.7)
        self.play_scroll_unroll_many(*exp_grp, run_time=1.0)  # 主视觉：拉幕
        self.at_clip("S3-c03")
        self.play(type_in(line1, run_time=0.8))
        self.at_clip("S3-c04")
        n_gb = self.counter_value(0, 16, suffix=" GB", size=72, color=YELL,
                                  run_time=1.2, anchor=slot_gb,
                                  extra_anims=[type_in(lab_gb, run_time=0.6),
                                               GrowFromEdge(bw1, LEFT), GrowFromEdge(bw2, LEFT),
                                               type_in(lab_nv, 0.5), type_in(lab_ib, 0.5)])  # 主视觉：数字滚动
        self.at_clip("S3-c05")

        # 页2a：DeepEP + 三件真货之 1（专用内核）
        head2 = _head("DeepSeek 开源的 DeepEP", 38)
        deep_card = _card("DeepEP：专家并行通信库", 6.4, 1.6, CYAN, WHITE, 36, CARD_FILL, "BOLD")
        twist = t("三件真货", 56, YELL, "BOLD")
        c1 = _card("① 专用内核：形状固定，省下的开销全换成带宽", 6.6, 2.2, WHITE, WHITE, 34, CARD_FILL)
        fp8 = t("FP8 dispatch 把带宽砍半", 34, GREEN, "BOLD")
        page2a = page_stack(deep_card, twist, c1, fp8, buff=0.7)
        layout_page(page2a)

        self.play(FadeOut(head), FadeOut(page1), FadeOut(n_gb),
                  FadeOut(lab_nv), FadeOut(lab_ib),
                  type_in(head2, run_time=0.8), run_time=0.8)
        self.play_scroll_unroll(deep_card, run_time=1.0)  # 主视觉：拉幕
        self.at_clip("S3-c06")
        self.play(type_in(twist, run_time=0.5))
        self.emphasize(twist, run_time=0.5)  # 3/5
        self.at_clip("S3-c07")
        self.play_scroll_unroll(c1, run_time=1.2)
        self.at_clip("S3-c08")
        self.play(type_in(fp8, run_time=0.8))
        self.at_clip("S3-c09")

        # 页2b：三件真货之 2、3（异步重叠 + SM 占用）
        head3 = _head("三件真货（续）", 38)
        c2 = _card("② 异步重叠：通信独立流，先到先算，不等整批", 6.6, 2.2, WHITE, WHITE, 34, CARD_FILL)
        canteen = t("像食堂窗口，菜齐一碟端一碟", 32, YELL, "BOLD")
        c3 = _card("③ 极低 SM 占用：通信主要等网络，不抢算力", 6.6, 2.2, WHITE, WHITE, 34, CARD_FILL)
        lab_sm = t("SM 占用", 30, WHITE, "BOLD")
        slot_sm = dynamic_slot(2.6, 0.9)
        sm_row = stable_row(lab_sm, slot_sm, buff=0.4)
        page2b = page_stack(c2, canteen, c3, sm_row, buff=0.7)
        layout_page(page2b)

        self.play(FadeOut(head2), FadeOut(page2a), type_in(head3, run_time=0.8), run_time=0.8)
        self.play_scroll_unroll(c2, run_time=1.2)  # 主视觉：拉幕
        self.at_clip("S3-c10")
        self.play(type_in(canteen, run_time=0.8))
        self.at_clip("S3-c12")
        self.play_scroll_unroll(c3, run_time=1.2)
        self.at_clip("S3-c13")
        n_sm = self.counter_value(24, 4, suffix=" → 6 个", size=64, color=YELL,
                                  run_time=1.4, anchor=slot_sm,
                                  extra_anims=[type_in(lab_sm, run_time=0.6)])  # 主视觉：数字滚动
        self.at_clip("S3-c14")

        # 页3：藏在计算阴影里
        head4 = _head("三件真货合起来", 38)
        img = ImageMobject(str(IMG / "s3-shadow-round.png"))
        img.scale_to_fit_width(5.8)
        cap = t("all-to-all 从排队，变成藏在计算阴影里", 32, WHITE, "BOLD")
        page3 = page_stack(img, cap, buff=0.9)
        layout_page(page3)

        self.play(FadeOut(head3), FadeOut(page2b), FadeOut(n_sm),
                  type_in(head4, run_time=0.8), run_time=0.8)
        self.play(FadeIn(img, shift=DOWN * 0.05), type_in(cap, run_time=0.9), run_time=0.9)  # 主视觉：插图
        self.at_clip("S3-c15")
        self.wait(1.14)  # 补到 c15 结束（64.85），台词讲完再转场
        self.transition_out(head4, f, img, cap)
        self.pad_to_voice()


# ---------------- S4 数学判据：6144 FLOPs/Byte ----------------
class S4(_Base):
    def construct(self):
        self.bg()
        f = _footer(self)

        # 页1：不等式组装 + 算账 + 6144
        head = _head("什么时候藏得满？", 40)
        ineq = t("C/B ≤ Vcomp/Vcomm", 50, YELL, "BOLD")
        calc1 = _card("每个 token 专家对：6hd FLOPs", 3.6, 2.2, CYAN, WHITE, 32, CARD_FILL, "BOLD")
        calc2 = _card("通信只要 3h 字节", 3.6, 2.2, GREEN, WHITE, 32, CARD_FILL, "BOLD")
        calcs = VGroup(calc1, calc2).arrange(RIGHT, buff=0.4)
        result = t("= 2d = 6144", 64, YELL, "BOLD")
        unit = t("单位：FLOPs / Byte", 30, MUTED)
        page1 = page_stack(ineq, calcs, result, unit, buff=1.2)
        layout_page(page1)

        self.at_clip("S4-c01")
        self.play(type_in(head, run_time=0.9))
        self.at_clip("S4-c02")
        self.play(type_in(ineq, run_time=1.0))  # 主视觉：公式组装
        self.at_clip("S4-c03")
        self.play_scroll_unroll_many(calc1, calc2, run_time=1.2)
        self.at_clip("S4-c05")
        self.play(type_in(result, run_time=0.9))
        self.emphasize(result, run_time=0.6)  # 4/5
        self.at_clip("S4-c08")
        self.play(type_in(unit, run_time=0.7))
        self.at_clip("S4-c09")

        # 页2：代入 H800 —— NVLink 藏得满 / IB 藏不满
        head2 = _head("代入 H800", 38)
        nv = _card("节点内 NVLink：约 2200 < 6144", 6.6, 1.8, GREEN, WHITE, 36, CARD_FILL, "BOLD")
        nv_ok = t("藏得满 ✓", 40, GREEN, "BOLD")
        ib = _card("跨节点 IB：约 39600 > 6144", 6.6, 1.8, RED, WHITE, 36, CARD_FILL, "BOLD")
        ib_no = t("藏不满 ✗", 40, RED, "BOLD")
        concl = t("差一个数量级", 44, YELL, "BOLD")
        page2 = page_stack(nv, nv_ok, ib, ib_no, concl, buff=0.6)
        layout_page(page2)

        self.play(FadeOut(head), FadeOut(page1), type_in(head2, run_time=0.8), run_time=0.8)
        self.play_scroll_unroll(nv, run_time=1.0)  # 主视觉：拉幕
        self.at_clip("S4-c10")
        mk1 = t("✔", 40, GREEN, "BOLD").next_to(nv, RIGHT, buff=0.25)
        mk1.align_to(nv, UP)
        self.play(type_in(nv_ok, run_time=0.6), FadeIn(mk1, scale=1.6), run_time=0.6)
        self.play(mk1.animate.scale(0.62), run_time=0.3)
        self.at_clip("S4-c11")
        self.play_scroll_unroll(ib, run_time=1.0)
        mk2 = t("✗", 40, RED, "BOLD").next_to(ib, RIGHT, buff=0.25)
        mk2.align_to(ib, UP)
        self.play(type_in(ib_no, run_time=0.6), FadeIn(mk2, scale=1.6), run_time=0.6)
        self.play(mk2.animate.scale(0.62), run_time=0.3)
        self.at_clip("S4-c12")
        self.play(type_in(concl, run_time=0.9))
        self.wait(0.3)
        self.transition_out(head2, f, nv, nv_ok, ib, ib_no, concl, mk1, mk2)
        self.pad_to_voice()


# ---------------- S5 MegaMoE：wave 粒度摊平 ----------------
class S5(_Base):
    def construct(self):
        self.bg()
        f = _footer(self)

        # 页1：wave 概念图 + 三波 + 6144 门槛
        head = _head("藏不满，就摊平", 40)
        img = ImageMobject(str(IMG / "s5-wave-round.png"))
        img.scale_to_fit_width(5.0)
        chips = VGroup(*[t(x, 28, WHITE, "BOLD") for x in
                         ["第一波在算", "第二波在路上", "第三波待发"]])
        chips.arrange(RIGHT, buff=0.5)
        gate = t("有效比值抬过 6144 的门槛", 34, YELL, "BOLD")
        page1 = page_stack(img, chips, gate, buff=0.8)
        layout_page(page1)

        self.at_clip("S5-c01")
        self.play(type_in(head, run_time=0.8))
        self.at_clip("S5-c02")
        self.play(FadeIn(img, shift=DOWN * 0.05), run_time=0.8)  # 主视觉：插图
        self.at_clip("S5-c05")
        self.play(*[type_in(c, 0.5) for c in chips], run_time=0.8, lag_ratio=0.3)
        self.at_clip("S5-c08")
        self.play(type_in(gate, run_time=0.9))
        self.at_clip("S5-c10")

        # 页2：加速倍数（数字滚动）+ MegaMoE2 + 转折
        head2 = _head("摊平的收益", 38)
        lab_t = t("理论", 30, WHITE, "BOLD")
        slot_t = dynamic_slot(2.0, 0.9)
        col1 = VGroup(lab_t, slot_t).arrange(DOWN, buff=0.25)
        lab_m = t("实测", 30, WHITE, "BOLD")
        slot_m = dynamic_slot(2.0, 0.9)
        col2 = VGroup(lab_m, slot_m).arrange(DOWN, buff=0.25)
        lab_r = t("RL", 30, WHITE, "BOLD")
        slot_r = dynamic_slot(2.0, 0.9)
        col3 = VGroup(lab_r, slot_r).arrange(DOWN, buff=0.25)
        sps = VGroup(col1, col2, col3).arrange(RIGHT, buff=0.5)
        mega = _card("实现开源在 DeepGEMM，叫 MegaMoE2", 6.6, 1.8, WHITE, WHITE, 32, CARD_FILL)
        twist1 = t("V4 报告没提 DeepEP？", 44, YELL, "BOLD")
        twist2 = t("不是不用了——是进化了", 44, YELL, "BOLD")
        page2 = page_stack(sps, mega, twist1, twist2, buff=0.9)
        layout_page(page2)

        self.play(FadeOut(head), FadeOut(page1), type_in(head2, run_time=0.8), run_time=0.8)
        # 三个倍率数字滚动（一个 play 内并行，主视觉）
        tr1, tr2, tr3 = ValueTracker(0), ValueTracker(0), ValueTracker(0)
        n1 = DecimalNumber(0, mob_class=Text, num_decimal_places=2, font_size=56, color=CYAN)
        n1.move_to(slot_t.get_center())
        n2 = DecimalNumber(0, mob_class=Text, num_decimal_places=2, font_size=56, color=GREEN)
        n2.move_to(slot_m.get_center())
        n3 = DecimalNumber(0, mob_class=Text, num_decimal_places=2, font_size=56, color=YELL)
        n3.move_to(slot_r.get_center())
        x1 = t("×", 30, WHITE, "BOLD").next_to(n1, RIGHT, buff=0.1)
        x2 = t("×", 30, WHITE, "BOLD").next_to(n2, RIGHT, buff=0.1)
        x3 = t("×", 30, WHITE, "BOLD").next_to(n3, RIGHT, buff=0.1)
        n1.add_updater(lambda m: m.set_value(tr1.get_value()))
        n2.add_updater(lambda m: m.set_value(tr2.get_value()))
        n3.add_updater(lambda m: m.set_value(tr3.get_value()))
        self.add(n1, n2, n3, x1, x2, x3)
        self.play(tr1.animate.set_value(1.92), tr2.animate.set_value(1.73),
                  tr3.animate.set_value(1.96),
                  type_in(lab_t, run_time=0.5), type_in(lab_m, run_time=0.5),
                  type_in(lab_r, run_time=0.5), run_time=1.2)
        n1.clear_updaters()
        n2.clear_updaters()
        n3.clear_updaters()
        self.at_clip("S5-c13")
        self.play_scroll_unroll(mega, run_time=1.0)
        self.at_clip("S5-c14")
        self.play(type_in(twist1, run_time=0.9))
        self.at_clip("S5-c15")
        self.play(type_in(twist2, run_time=0.9))
        self.emphasize(twist2, run_time=0.6)  # 5/5
        self.wait(1.91)  # 补到 c15 结束（51.20），台词讲完再转场
        self.transition_out(head2, f, sps, mega, twist1, twist2, n1, n2, n3, x1, x2, x3)
        self.pad_to_voice()


# ---------------- S6 结尾：三粒度总结 + 互动 + 尾卡 ----------------
class S6(_Base):
    def construct(self):
        self.bg()
        f = _footer(self)

        # 页1：两处等待 + 三粒度 + 6144
        head = _head("回到开头：GPU 为什么空等？", 38)
        w1 = _card("等上游", 3.0, 2.2, CYAN, WHITE, 36, CARD_FILL, "BOLD")
        w2 = _card("等网络", 3.0, 2.2, GREEN, WHITE, 36, CARD_FILL, "BOLD")
        ws = VGroup(w1, w2).arrange(RIGHT, buff=0.5)
        g1 = _card("DualPipe：stage 之间藏", 2.3, 2.2, CYAN, WHITE, 26, CARD_FILL, "BOLD")
        g2 = _card("DeepEP：层内藏", 2.3, 2.2, GREEN, WHITE, 26, CARD_FILL, "BOLD")
        g3 = _card("MegaMoE：wave 内藏", 2.3, 2.2, YELL, WHITE, 26, CARD_FILL, "BOLD")
        gs = VGroup(g1, g2, g3).arrange(RIGHT, buff=0.3)
        gate = t("判据：6144 FLOPs/Byte", 36, YELL, "BOLD")
        page1 = page_stack(ws, gs, gate, buff=1.1)
        layout_page(page1)

        self.at_clip("S6-c01")
        self.play(type_in(head, run_time=0.9))
        self.at_clip("S6-c02")
        self.play_scroll_unroll_many(w1, w2, run_time=1.0)  # 主视觉：拉幕
        self.at_clip("S6-c03")
        self.play_scroll_unroll_many(g1, g2, g3, run_time=1.2)
        self.at_clip("S6-c05")
        self.play(type_in(gate, run_time=0.9))
        self.at_clip("S6-c06")

        # 页2：互动问题
        head2 = _head("一个问题留给你", 38)
        q1 = _card("NVLink 藏得满，IB 藏不满", 6.8, 2.2, YELL, WHITE, 38, CARD_FILL, "BOLD")
        q2 = _card("你会把通信往节点内搬，还是升级更宽的互连？", 6.8, 2.2, WHITE, WHITE, 34, CARD_FILL)
        line = t("评论区聊聊", 40, GREEN, "BOLD")
        page2 = page_stack(q1, q2, line, buff=1.2)
        layout_page(page2)

        self.play(FadeOut(head), FadeOut(page1), type_in(head2, run_time=0.8), run_time=0.8)
        self.play_scroll_unroll(q1, run_time=1.0)  # 主视觉：拉幕
        self.at_clip("S6-c07")
        self.play_scroll_unroll(q2, run_time=1.2)
        self.at_clip("S6-c08")
        self.play(type_in(line, run_time=0.8))
        self.at_clip("S6-c09")

        # 页3：品牌尾卡（终幕驻屏，不 transition_out）
        avatar = ImageMobject(str(AVATAR))
        avatar.scale_to_fit_width(3.6)
        follow = t("关注「数解AI」", 44, YELL, "BOLD")
        title = t("《DeepEP：训练时GPU的空等怎么藏起来》", 28, WHITE, "BOLD")
        guide = t("查看公众号文章", 32, GREEN, "BOLD")
        page3 = page_stack(avatar, follow, title, guide, buff=0.7)
        layout_page(page3)

        self.play(FadeOut(head2), FadeOut(page2), FadeIn(avatar, shift=DOWN * 0.05), run_time=0.8)  # 主视觉：品牌图
        self.play(type_in(follow, run_time=0.9), type_in(title, run_time=0.9),
                  type_in(guide, run_time=0.8), run_time=0.9)
        self.pad_to_voice()
