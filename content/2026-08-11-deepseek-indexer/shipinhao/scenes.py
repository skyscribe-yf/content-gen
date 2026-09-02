#!/usr/bin/env python3
"""《稀疏注意力怎么挑重点？DeepSeek-V4 只算 1/64》视频号 Manim 动画（竖屏 1080×1920）

6 个场景 S1-S6，与 storyboard.md 一一对应。
- 配音：MiniMax 克隆作者音色（speech-2.8-turbo，speed 1.0 pitch +2，--clone-audio）
- 时间轴：at_clip("S1-c01") 挂 tts/sentence-boundaries.json 的 clip 起点（先声音后动画门禁）
- 布局：整页规划（page_stack + layout_page / page_auto），上下留白各 ≤10%
- 动画降噪：每页 1 个主视觉动效；emphasize 全片 4 次；v2 动效 0 处
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

# 每段配音时长（tts_split.py 实测 2026-09-01），渲染时长 = 配音 + TAIL
VOICE_DUR = {"S1": 36.85, "S2": 42.44, "S3": 59.37, "S4": 53.92, "S5": 50.81, "S6": 48.48}
TAIL = 2.5


def _footer(self) -> Text:
    f = t("数解AI · DeepSeek 技术解密", 20, MUTED).to_edge(DOWN, buff=1.15)
    self.add(f)
    return f


def _head(text: str, size: float = 38) -> Text:
    return t(text, size, YELL, "BOLD").to_edge(UP, buff=1.2)


# ---------------- S1 开场钩子：死结 + 图书馆类比 ----------------
class S1(_Base):
    def construct(self):
        self.bg()
        f = _footer(self)

        # 页1：死结环 + 图书馆概念图
        head = _head("先筛后算的死结", 40)
        c1 = _card("选择依赖计算", 3.4, 2.0, CYAN, WHITE, 34, CARD_FILL, "BOLD")
        c2 = _card("计算依赖选择", 3.4, 2.0, GREEN, WHITE, 34, CARD_FILL, "BOLD")
        cards = VGroup(c1, c2).arrange(RIGHT, buff=0.6)
        ar_top = Arrow(c1.get_right() + UP * 0.3, c2.get_left() + UP * 0.3,
                       color=YELL, buff=0.15, stroke_width=4)
        ar_bot = Arrow(c2.get_left() + DOWN * 0.3, c1.get_right() + DOWN * 0.3,
                       color=YELL, buff=0.15, stroke_width=4)
        loop = VGroup(cards, ar_top, ar_bot)
        img = ImageMobject(str(IMG / "s1-archive-round.png"))
        img.scale_to_fit_width(3.3)
        line1 = t("读一遍的代价，跟全量计算一样贵", 30, WHITE, "BOLD")
        cap = t("目录卡只有读了正文，才知道哪本有用", 26, MUTED)
        page1 = page_stack(loop, img, line1, cap, buff=0.55)
        layout_page(page1)

        self.at_clip("S1-c01")
        self.play(type_in(head, run_time=1.1))
        self.at_clip("S1-c02")
        self.play(FadeIn(img, shift=DOWN * 0.05), run_time=0.8)  # 主视觉：插图
        self.at_clip("S1-c03")
        self.play(type_in(line1, run_time=0.9))
        self.at_clip("S1-c04")
        self.play_scroll_unroll_many(c1, c2, run_time=1.2)
        self.play(Create(ar_top), Create(ar_bot), run_time=0.6)
        self.at_clip("S1-c05")
        self.play(type_in(cap, run_time=0.9))
        self.at_clip("S1-c06")

        # 页2：爆点 + FP4 答案 + 悬念（矮页）
        head2 = _head("V4 的答案", 40)
        b1 = t("全读，贵；赌，怕漏。", 56, YELL, "BOLD")
        b2 = t("一个只有 4 比特精度的小网络", 40, WHITE, "BOLD")
        b3 = t("它凭什么敢替大模型做决定？", 44, YELL, "BOLD")
        page2 = page_auto(b1, b2, b3, buff=0.5)

        self.play(FadeOut(head), FadeOut(page1),
                  type_in(head2, run_time=0.9), run_time=0.9)
        self.at_clip("S1-c07")
        self.play(type_in(b1, run_time=0.6))
        self.emphasize(b1, run_time=0.4)  # 1/4
        self.at_clip("S1-c08")
        self.play(type_in(b2, run_time=0.9))
        self.at_clip("S1-c09")
        self.play(type_in(b3, run_time=0.9))
        self.wait(2.09)  # 补到 c09 结束（36.86），台词讲完再转场
        self.transition_out(head2, f, page2)
        self.pad_to_voice()


# ---------------- S2 压缩块 + Indexer 登场 ----------------
class S2(_Base):
    def construct(self):
        self.bg()
        f = _footer(self)

        # 页1：token→块 压缩 + 128K→32K 数字滚动 + Indexer 卡
        head = _head("先看它怎么挑", 40)
        line1 = t("每 4 个 token 压成一个块", 30, WHITE, "BOLD")
        toks = VGroup(*[Rectangle(width=0.9, height=1.1, color=YELL,
                                  fill_color=YELL, fill_opacity=0.25) for _ in range(4)])
        toks.arrange(RIGHT, buff=0.25)
        tok_labs = [t("t", 20, WHITE, "BOLD") for _ in range(4)]
        for tl, tk in zip(tok_labs, toks):
            tl.move_to(tk.get_center())
        tok_grp = VGroup(*[VGroup(tk, tl) for tk, tl in zip(toks, tok_labs)])
        ar = Arrow(toks.get_right() + RIGHT * 0.1, toks.get_right() + RIGHT * 1.1,
                   color=YELL, buff=0, stroke_width=5)
        block = Rectangle(width=1.7, height=1.4, color=CYAN, fill_color=CYAN, fill_opacity=0.2)
        block.next_to(ar, RIGHT, buff=0.15)
        blab = t("块", 26, WHITE, "BOLD").move_to(block.get_center())
        compress = VGroup(tok_grp, ar, block, blab)
        lab_old = t("128K 上下文", 34, MUTED, "BOLD")
        slot = dynamic_slot(2.6, 0.9)
        num_row = stable_row(lab_old, slot, buff=0.4)
        idx = _card("Lightning Indexer：给全部块打分", 6.6, 1.8, CYAN, WHITE, 34, CARD_FILL, "BOLD")
        page1 = page_stack(line1, compress, num_row, idx, buff=1.0)
        layout_page(page1)

        self.at_clip("S2-c01")
        self.play(type_in(head, run_time=0.9))
        self.at_clip("S2-c02")
        self.play(type_in(line1, run_time=0.8),
                  *[Create(tk) for tk in toks], run_time=0.8, lag_ratio=0.3)  # 主视觉：token 逐段
        self.at_clip("S2-c03")
        self.play(Create(ar), Create(block), type_in(blab, 0.5), run_time=0.8)
        n = self.counter_value(0, 32, suffix="K 块", size=72, color=YELL,
                                run_time=1.2, anchor=slot,
                                extra_anims=[type_in(lab_old, run_time=0.6)])  # 主视觉：数字滚动
        self.at_clip("S2-c04")
        self.play_scroll_unroll(idx, run_time=1.2)
        self.at_clip("S2-c05")

        # 页2：打分流程链（64 头 → ReLU → Top-512）+ 512 滚动
        head2 = _head("怎么挑？三步", 38)
        p1 = _card("64 个打分头，各看各的维度", 2.2, 2.8, CYAN, WHITE, 28, CARD_FILL, "BOLD")
        p2 = _card("ReLU 淘汰负分", 2.2, 2.8, GREEN, WHITE, 28, CARD_FILL, "BOLD")
        p3 = _card("交给核心注意力", 2.2, 2.8, YELL, WHITE, 28, CARD_FILL, "BOLD")
        steps = VGroup(p1, p2, p3).arrange(RIGHT, buff=0.4)
        a1 = Arrow(p1.get_right(), p2.get_left(), color=MUTED, buff=0.15, stroke_width=4)
        a2 = Arrow(p2.get_right(), p3.get_left(), color=MUTED, buff=0.15, stroke_width=4)
        chain = VGroup(steps, a1, a2)
        cap2 = t("打分 → 淘汰 → 精选", 28, MUTED)
        lab512 = t("只留", 34, MUTED, "BOLD")
        slot512 = dynamic_slot(2.4, 1.0)
        row512 = stable_row(lab512, slot512, buff=0.4)
        page2 = page_stack(chain, cap2, row512, buff=1.5)
        layout_page(page2)

        self.play(FadeOut(head), FadeOut(page1), FadeOut(n),
                  type_in(head2, run_time=0.8), run_time=0.8)
        self.at_clip("S2-c06")
        self.play_scroll_unroll(p1, run_time=1.0)  # 主视觉：拉幕
        self.at_clip("S2-c07")
        self.play_scroll_unroll_many(p2, p3, run_time=1.2)
        self.play(Create(a1), Create(a2), run_time=0.4)
        self.at_clip("S2-c08")
        n512 = self.counter_value(0, 512, suffix=" 块", size=72, color=YELL,
                                   run_time=1.2, anchor=slot512,
                                   extra_anims=[type_in(lab512, run_time=0.6)])  # 主视觉：数字滚动
        self.at_clip("S2-c09")

        # 页3：精读 vs 速览 + 悬念
        head3 = _head("分工", 38)
        q1 = _card("主模型：精读", 3.4, 2.2, CYAN, WHITE, 34, CARD_FILL, "BOLD")
        q2 = _card("Indexer：速览", 3.4, 2.2, GREEN, WHITE, 34, CARD_FILL, "BOLD")
        qs = VGroup(q1, q2).arrange(RIGHT, buff=0.5)
        line2 = t("速览便宜到每个 token 都能跑", 30, WHITE, "BOLD")
        line3 = t("精读贵到只留给选中的块", 30, WHITE, "BOLD")
        twist = t("残缺数字的小网络，\n凭什么敢替大模型挑重点？", 36, YELL, "BOLD")
        page3 = page_stack(qs, line2, line3, twist, buff=1.3)
        layout_page(page3)

        self.play(FadeOut(head2), FadeOut(page2), FadeOut(n512),
                  type_in(head3, run_time=0.8), run_time=0.8)
        self.play_scroll_unroll_many(q1, q2, run_time=1.0)  # 主视觉：拉幕
        self.at_clip("S2-c10")
        self.play(type_in(line2, run_time=0.8))
        self.at_clip("S2-c11")
        self.play(type_in(line3, run_time=0.8))
        self.at_clip("S2-c12")
        self.play(type_in(twist, run_time=0.9))
        self.emphasize(twist, run_time=0.6)  # 2/4
        self.wait(5.29)  # 补到 c12 结束（42.50），台词讲完再转场
        self.transition_out(head3, f, page3)
        self.pad_to_voice()


# ---------------- S3 三个支柱 ----------------
class S3(_Base):
    def construct(self):
        self.bg()
        f = _footer(self)

        # 页1：支柱一 ReLU（FP4 唯一活路）
        head = _head("三个支柱", 40)
        c1 = _card("① ReLU 淘汰制：FP4 下的唯一活路", 6.6, 1.6, CYAN, WHITE, 34, CARD_FILL, "BOLD")
        fp4 = _card("FP4：只有 16 个值", 3.2, 2.0, RED, WHITE, 30, CARD_FILL, "BOLD")
        sm = _card("Softmax：指数直接溢出", 3.2, 2.0, RED, WHITE, 30, CARD_FILL, "BOLD")
        vs = VGroup(fp4, sm).arrange(RIGHT, buff=0.5)
        relu = _card("ReLU：只有比较，零精度损失", 6.6, 1.6, GREEN, WHITE, 34, CARD_FILL, "BOLD")
        twist = t("不是设计偏好，\n是软硬件协同的必然", 36, YELL, "BOLD")
        page1 = page_stack(c1, vs, relu, twist, buff=0.7)
        layout_page(page1)

        self.at_clip("S3-c01")
        self.play(type_in(head, run_time=0.9))
        self.at_clip("S3-c02")
        self.play_scroll_unroll(c1, run_time=1.0)  # 主视觉：拉幕
        self.at_clip("S3-c03")
        self.play_scroll_unroll_many(fp4, sm, run_time=1.2)
        self.at_clip("S3-c04")
        self.play_scroll_unroll(relu, run_time=1.0)
        self.at_clip("S3-c05")
        self.play(type_in(twist, run_time=0.9))
        self.at_clip("S3-c06")

        # 页2：支柱二 多头加权
        head2 = _head("② 多头加权", 40)
        m1 = _card("64 个 head，各学一套标准", 6.6, 2.8, CYAN, WHITE, 36, CARD_FILL, "BOLD")
        m2 = _card("权重由 query 动态生成，可正可负", 6.6, 2.8, GREEN, WHITE, 36, CARD_FILL, "BOLD")
        page2 = page_stack(m1, m2, buff=1.4)
        layout_page(page2)

        self.play(FadeOut(head), FadeOut(page1), type_in(head2, run_time=0.8), run_time=0.8)
        self.play_scroll_unroll(m1, run_time=1.0)  # 主视觉：拉幕
        self.at_clip("S3-c07")
        self.play_scroll_unroll(m2, run_time=1.0)
        self.at_clip("S3-c08")

        # 页3a：支柱三 选错代价 + 天平概念图
        head3 = _head("③ 选错代价有上限", 40)
        img = ImageMobject(str(IMG / "s3-balance-round.png"))
        img.scale_to_fit_width(5.2)
        g1 = _card("漏看：信息少一点，不会胡说", 3.4, 2.0, GREEN, WHITE, 28, CARD_FILL, "BOLD")
        g2 = _card("全算：刚性成本", 3.4, 2.0, RED, WHITE, 28, CARD_FILL, "BOLD")
        gs = VGroup(g1, g2).arrange(RIGHT, buff=0.5)
        page3a = page_stack(img, gs, buff=1.2)
        layout_page(page3a)

        self.play(FadeOut(head2), FadeOut(page2), type_in(head3, run_time=0.8), run_time=0.8)
        self.play(FadeIn(img, shift=DOWN * 0.05), run_time=0.8)  # 主视觉：插图
        self.at_clip("S3-c09")
        self.play_scroll_unroll_many(g1, g2, run_time=1.2)
        self.at_clip("S3-c11")

        # 页3b：64 倍 + 99.7% + 结论（矮页）
        head4 = _head("这笔账", 38)
        lab_k = t("k=512 vs 32K 块", 30, MUTED, "BOLD")
        slot1 = dynamic_slot(2.4, 0.9)
        row1 = stable_row(lab_k, slot1, buff=0.4)
        lab_r = t("召回率", 30, MUTED, "BOLD")
        slot2 = dynamic_slot(2.4, 0.9)
        row2 = stable_row(lab_r, slot2, buff=0.4)
        concl = t("漏看只是少看一点，全算才是真的贵", 36, YELL, "BOLD")
        page3b = page_auto(row1, row2, concl, buff=0.5)

        self.play(FadeOut(head3), FadeOut(page3a), type_in(head4, run_time=0.8), run_time=0.8)
        self.at_clip("S3-c12")
        n1 = self.counter_value(1, 64, suffix=" 倍", size=72, color=YELL,
                                run_time=1.2, anchor=slot1,
                                extra_anims=[type_in(lab_k, run_time=0.6)])  # 主视觉：数字滚动
        self.at_clip("S3-c13")
        n2 = self.counter_value(0, 99.7, suffix="%", decimals=1, size=72, color=GREEN,
                                run_time=1.2, anchor=slot2,
                                extra_anims=[type_in(lab_r, run_time=0.6)])
        self.emphasize(n2, run_time=0.6)  # 3/4
        self.at_clip("S3-c14")
        self.play(type_in(concl, run_time=0.9))
        self.wait(3.73)  # 补到 c14 结束（59.39），台词讲完再转场
        self.transition_out(head4, f, page3b, n1, n2)
        self.pad_to_voice()


# ---------------- S4 两阶段训练 ----------------
class S4(_Base):
    def construct(self):
        self.bg()
        f = _footer(self)

        # 页1：随机初始化直接崩
        head = _head("敢挑，还得会挑", 40)
        c1 = _card("Indexer 是随机初始化的", 6.6, 2.2, CYAN, WHITE, 36, CARD_FILL, "BOLD")
        c2 = _card("直接上稀疏训练 = 随机丢块", 6.6, 2.2, WHITE, WHITE, 36, CARD_FILL, "BOLD")
        boom = t("训练直接崩", 56, YELL, "BOLD")
        page1 = page_stack(c1, c2, boom, buff=1.3)
        layout_page(page1)

        self.at_clip("S4-c01")
        self.play(type_in(head, run_time=0.9))
        self.at_clip("S4-c02")
        self.play_scroll_unroll_many(c1, c2, run_time=1.0)  # 主视觉：拉幕
        self.at_clip("S4-c03")
        c1x = Line(c2.get_corner(UL) + RIGHT * 0.15 + DOWN * 0.15,
                   c2.get_corner(DR) + LEFT * 0.15 + UP * 0.15,
                   color=RED, stroke_width=14)
        c2x = Line(c2.get_corner(UR) + LEFT * 0.15 + DOWN * 0.15,
                   c2.get_corner(DL) + RIGHT * 0.15 + UP * 0.15,
                   color=RED, stroke_width=14)
        cross = VGroup(c1x, c2x)
        self.play(GrowFromCenter(c1x), GrowFromCenter(c2x),
                  type_in(boom, run_time=0.8), run_time=0.8)
        self.play(cross.animate.scale(1.1), run_time=0.2, rate_func=there_and_back)
        self.at_clip("S4-c04")

        # 页2a：两阶段流程
        head2 = _head("V4 用两阶段教会它", 38)
        s1 = _card("阶段一：密集预训练 1T token", 6.0, 2.2, CYAN, WHITE, 34, CARD_FILL, "BOLD")
        s2 = _card("阶段二：warmup Indexer", 6.0, 2.2, GREEN, WHITE, 34, CARD_FILL, "BOLD")
        s3 = _card("再上稀疏注意力", 6.0, 2.2, YELL, WHITE, 34, CARD_FILL, "BOLD")
        stages = VGroup(s1, s2, s3).arrange(DOWN, buff=0.7)
        a1 = Arrow(s1.get_bottom(), s2.get_top(), color=MUTED, buff=0.15, stroke_width=4)
        a2 = Arrow(s2.get_bottom(), s3.get_top(), color=MUTED, buff=0.15, stroke_width=4)
        flow = VGroup(stages, a1, a2)
        page2a = page_stack(flow, buff=0.0)
        layout_page(page2a)

        self.play(FadeOut(head), FadeOut(page1), FadeOut(cross),
                  type_in(head2, run_time=0.8), run_time=0.8)
        self.at_clip("S4-c05")
        self.play_scroll_unroll(s1, run_time=1.0)  # 主视觉：拉幕
        self.at_clip("S4-c07")
        self.play_scroll_unroll_many(s2, s3, run_time=1.2)
        self.at_clip("S4-c08")

        # 页2b：老师是谁？
        head3 = _head("老师是谁？", 40)
        q = _card("论文没写，但推理链条只有一条", 6.6, 2.2, YELL, WHITE, 34, CARD_FILL, "BOLD")
        ans = _card("密集注意力的真实权重，当老师", 6.6, 2.2, GREEN, WHITE, 34, CARD_FILL, "BOLD")
        note = t("warmup 时模型仍按密集方式跑", 28, MUTED)
        page2b = page_stack(q, ans, note, buff=1.2)
        layout_page(page2b)

        self.play(FadeOut(head2), FadeOut(page2a), type_in(head3, run_time=0.8), run_time=0.8)
        self.at_clip("S4-c09")
        self.play_scroll_unroll(q, run_time=1.0)  # 主视觉：拉幕
        self.emphasize(q, run_time=0.5)  # 4/4
        self.at_clip("S4-c10")
        self.play_scroll_unroll(ans, run_time=1.2)
        self.at_clip("S4-c11")
        self.play(type_in(note, run_time=0.8))

        # 页2c：结论（矮页）
        head4 = _head("学到的", 38)
        z1 = t("学的是真正重要的块长什么样", 52, WHITE, "BOLD")
        z2 = t("先学全量，再学偷懒", 52, YELL, "BOLD")
        z3 = t("偷懒才不至于变成瞎", 52, YELL, "BOLD")
        page2c = page_auto(z1, z2, z3, buff=0.5)

        self.play(FadeOut(head3), FadeOut(page2b), type_in(head4, run_time=0.8), run_time=0.8)
        self.play(type_in(z1, run_time=0.9))
        self.at_clip("S4-c12")
        self.play(type_in(z2, run_time=0.9), type_in(z3, run_time=0.9), run_time=0.9)
        self.wait(3.8)  # 补到 c12 结束（53.93），台词讲完再转场
        self.transition_out(head4, f, page2c)
        self.pad_to_voice()


# ---------------- S5 他山之石：GLM / Kimi ----------------
class S5(_Base):
    def construct(self):
        self.bg()
        f = _footer(self)

        # 页1：GLM-5.2 IndexShare
        head = _head("只有 DeepSeek 在走吗？不是", 36)
        g1 = _card("GLM-5.2：同一套方案", 3.4, 2.4, CYAN, WHITE, 30, CARD_FILL, "BOLD")
        g2 = _card("相邻层 top-k 重叠 70%-100%", 3.4, 2.4, WHITE, WHITE, 30, CARD_FILL, "BOLD")
        gs = VGroup(g1, g2).arrange(RIGHT, buff=0.5)
        g3 = _card("每 4 层共享 1 个 Indexer", 6.6, 2.4, GREEN, WHITE, 32, CARD_FILL, "BOLD")
        lab = t("计算量", 30, MUTED, "BOLD")
        slot = dynamic_slot(2.4, 0.9)
        row = stable_row(lab, slot, buff=0.4)
        page1 = page_stack(gs, g3, row, buff=1.1)
        layout_page(page1)

        self.at_clip("S5-c01")
        self.play(type_in(head, run_time=0.9))
        self.at_clip("S5-c03")
        self.play_scroll_unroll_many(g1, g2, run_time=1.2)  # 主视觉：拉幕
        self.at_clip("S5-c05")
        self.play_scroll_unroll(g3, run_time=1.0)
        self.at_clip("S5-c06")
        n1 = self.counter_value(0, 2.9, suffix=" 倍", decimals=1, size=72, color=YELL,
                                run_time=1.2, anchor=slot,
                                extra_anims=[type_in(lab, run_time=0.6)])  # 主视觉：数字滚动
        self.at_clip("S5-c07")

        # 页2：Kimi K3 不筛
        head2 = _head("Kimi K3：压根不筛", 38)
        k1 = _card("线性注意力：历史压成固定状态", 6.6, 2.2, CYAN, WHITE, 34, CARD_FILL, "BOLD")
        k2 = _card("没有 top-k，也没有 Indexer", 6.6, 2.2, WHITE, WHITE, 34, CARD_FILL, "BOLD")
        k3 = t("选择问题被结构消解", 40, YELL, "BOLD")
        page2 = page_stack(k1, k2, k3, buff=1.1)
        layout_page(page2)

        self.play(FadeOut(head), FadeOut(page1), FadeOut(n1),
                  type_in(head2, run_time=0.8), run_time=0.8)
        self.play_scroll_unroll(k1, run_time=1.0)  # 主视觉：拉幕
        self.at_clip("S5-c08")
        self.play_scroll_unroll(k2, run_time=1.0)
        self.at_clip("S5-c09")
        self.play(type_in(k3, run_time=0.9))
        self.at_clip("S5-c10")

        # 页3：粗筛也是瓶颈
        head3 = _head("粗筛自己也会变成瓶颈", 38)
        b1 = _card("200K 上下文，Indexer 点积消耗", 6.6, 2.2, WHITE, WHITE, 32, CARD_FILL, "BOLD")
        lab2 = t("prefill 时间", 30, MUTED, "BOLD")
        slot2 = dynamic_slot(2.4, 0.9)
        row2 = stable_row(lab2, slot2, buff=0.4)
        concl = t("三家在解同一个问题：筛选成本本身", 34, YELL, "BOLD")
        page3 = page_stack(b1, row2, concl, buff=1.8)
        layout_page(page3)

        self.play(FadeOut(head2), FadeOut(page2), type_in(head3, run_time=0.8), run_time=0.8)
        self.play_scroll_unroll(b1, run_time=1.0)  # 主视觉：拉幕
        self.at_clip("S5-c11")
        n2 = self.counter_value(0, 81, suffix="%", size=72, color=RED,
                                run_time=1.2, anchor=slot2,
                                extra_anims=[type_in(lab2, run_time=0.6)])  # 主视觉：数字滚动
        self.at_clip("S5-c12")
        self.play(type_in(concl, run_time=0.9))
        self.wait(3.8)  # 补到 c12 结束（50.86），台词讲完再转场
        self.transition_out(head3, f, page3, n2)
        self.pad_to_voice()


# ---------------- S6 回扣 + 互动 + 品牌尾卡 ----------------
class S6(_Base):
    def construct(self):
        self.bg()
        f = _footer(self)

        # 页1：回扣（速览 vs 精读概念图）
        head = _head("回到开头：它怎么知道该翻哪几卷？", 34)
        img = ImageMobject(str(IMG / "s6-scan-round.png"))
        img.scale_to_fit_width(2.6)
        c1 = _card("FP4 小网络：参数占比不到 1%", 6.6, 1.4, CYAN, WHITE, 32, CARD_FILL, "BOLD")
        lab = t("点积", 30, MUTED, "BOLD")
        slot = dynamic_slot(2.4, 0.9)
        row = stable_row(lab, slot, buff=0.4)
        l1 = t("挑出 512 卷，大模型才动手精读", 30, WHITE, "BOLD")
        concl = t("而是想清楚该用多大力气", 34, YELL, "BOLD")
        page1 = page_stack(img, c1, row, l1, concl, buff=0.7)
        layout_page(page1)

        self.at_clip("S6-c01")
        self.play(type_in(head, run_time=0.9))
        self.at_clip("S6-c02")
        self.play(FadeIn(img, shift=DOWN * 0.05), run_time=0.8)  # 主视觉：插图
        self.at_clip("S6-c03")
        self.play_scroll_unroll(c1, run_time=1.2)
        self.at_clip("S6-c04")
        n = self.counter_value(0, 200, suffix=" 万次", size=72, color=YELL,
                               run_time=1.2, anchor=slot,
                               extra_anims=[type_in(lab, run_time=0.6)])  # 主视觉：数字滚动
        self.at_clip("S6-c05")
        self.play(type_in(l1, run_time=0.9))
        self.at_clip("S6-c07")
        self.play(type_in(concl, run_time=0.9))
        self.at_clip("S6-c08")

        # 页2：互动问题
        head2 = _head("一个问题留给你", 38)
        q1 = _card("模型里还有哪些「全部算一遍」的地方？", 6.8, 2.2, YELL, WHITE, 36, CARD_FILL, "BOLD")
        q2 = _card("可以换成先筛后算？", 6.8, 2.2, WHITE, WHITE, 36, CARD_FILL, "BOLD")
        line = t("评论区聊聊", 40, GREEN, "BOLD")
        page2 = page_stack(q1, q2, line, buff=1.2)
        layout_page(page2)

        self.play(FadeOut(head), FadeOut(page1), FadeOut(n),
                  type_in(head2, run_time=0.8), run_time=0.8)
        self.play_scroll_unroll(q1, run_time=1.0)  # 主视觉：拉幕
        self.at_clip("S6-c09")
        self.play_scroll_unroll(q2, run_time=1.0)
        self.at_clip("S6-c10")
        self.play(type_in(line, run_time=0.8))
        self.at_clip("S6-c11")

        # 页3：品牌尾卡（终幕驻屏，不 transition_out）
        avatar = ImageMobject(str(AVATAR))
        avatar.scale_to_fit_width(3.0)
        follow = t("关注「数解AI」", 44, YELL, "BOLD")
        title = t("《稀疏注意力怎么挑重点？\nDeepSeek-V4 只算 1/64》", 26, WHITE, "BOLD")
        nextup = t("下一篇：MTP 一次猜两个词，推理快 1.8 倍", 26, MUTED)
        guide = t("查看公众号文章", 32, GREEN, "BOLD")
        page3 = page_stack(avatar, follow, title, nextup, guide, buff=0.7)
        layout_page(page3)

        self.play(FadeOut(head2), FadeOut(page2), FadeIn(avatar, shift=DOWN * 0.05), run_time=0.8)  # 主视觉：品牌图
        self.at_clip("S6-c12")
        self.play(type_in(follow, run_time=0.9), type_in(title, run_time=0.9), run_time=0.9)
        self.at_clip("S6-c13")
        self.play(type_in(nextup, run_time=0.8), type_in(guide, run_time=0.8), run_time=0.8)
        self.pad_to_voice()
