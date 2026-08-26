#!/usr/bin/env python3
"""《Kimi K3 架构怎么撑住 2.8T 参数？三轴拆给你看》视频号 Manim 动画（竖屏 1080×1920）

6 个场景 S1-S6，与 storyboard.md 一一对应。
配音：MiniMax 预设精英男声 male-qn-jingying（2026-08-26 用户拍板为默认），speed 1.0 pitch +2。
时间轴契约：at() 只落在 tts/full.subtitle.json 句级边界（check_manim_scene.py --strict 校验）；
窗口内节奏用 wait() 控制（wait 不要求边界对齐）。
通用工具在 scripts/manim_helpers.py；本文件只放 VOICE_DUR / TAIL / 场景类。

2026-08-26 重优化（helper 布局版）：
- 矮页（1-4 行文字/结论页）改 page_auto：S1p1、S2p4、S6p2、S6p3a（语义标点拆行 + 字号放大 + 垂直居中，无中间空洞）
- 所有 grow_bar 改 anchor="center"（柱底/标签居中对齐，2026-08-25 左缘锚定偏右修复）
- S5p1 柱状图重做：柱宽统一 1.5，高度按分值 3.0/3.35/3.7 编码，柱底对齐（原目标 2.8/3.1/3.4 宽度会柱体重叠）
- S6p2 下期预告改为 DeepSeek CSA（V4 为何不用 MLA？）——声音/音轨未动，字幕文本经 tts/manual-boundaries.json 覆盖
  （tts.txt 第 6 行改写为预告+互动句；句子 17 仍由 S5 跨段分支烧录，防重复；全片时长/at() 锚点不变）

渲染：
  python3 -m manim render -ql --disable_caching scenes.py S1 S2 S3 S4 S5 S6
  python3 -m manim render -qm --disable_caching scenes.py S1 S2 S3 S4 S5 S6
构建：python3 scripts/manim_video_build.py content/2026-07-28-kimi-k3-architecture/shipinhao
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

config.background_color = "#16213E"

# TTS 实测时长（tts_split.py 输出 VOICE_DUR，勿改）
VOICE_DUR = {"S1": 27.56, "S2": 34.65, "S3": 36.44, "S4": 43.55,
             "S5": 37.68, "S6": 27.4}
TAIL = 2.5  # 渲染缓冲（build 会截到 0.1s）


# ================= S1 开场钩子：2.8T 怎么跑得动 → 三轴预告 =================
# 句边界: [0.0, 12.6]
class S1(_Base):
    def construct(self):
        self.bg()
        ftr = t("数解AI · 大模型原理", 20, MUTED).to_edge(DOWN, buff=1.15)
        self.add(ftr)
        head = t("2.8 万亿参数，凭什么跑得动？", 36, YELL, "BOLD")
        fit(head, 0.92)
        head.to_edge(UP, buff=1.0)
        hint = t("本片拆解 Kimi K3 三轴架构", 20, MUTED).to_corner(UL, buff=0.6)

        # ---- 页1：Agent 故事 + 50 万 token + 第 37 轮死命令（0-10.6）----
        lineA = t("一个 Agent，连续改了 3 小时", 30, WHITE)
        fit(lineA, 0.9)
        cnt_ph = Rectangle(width=3.6, height=1.7, fill_opacity=0.0, stroke_opacity=0.0)
        cardB = _card("第 37 轮 · 支付接口，绝对不能改", 5.8, 2.6, CYAN, WHITE, 30, CARD_FILL, "BOLD")
        page_auto(lineA, cnt_ph, cardB)  # 矮页：紧凑行距 + 垂直居中（无上下空洞）

        self.play(type_in(head, run_time=1.1), type_in(hint, run_time=0.5),
                  run_time=1.6, lag_ratio=1.0)          # 0.0-1.6（标题+小字，串行）
        self.wait(0.6)                                  # -> 2.2
        cnt50 = self.counter_value(0, 50, suffix=" 万 token", size=52, color=YELL,
                                   anchor=cnt_ph, run_time=2.0)   # 2.2-4.2
        self.wait(0.4)
        self.play(type_in(lineA, run_time=1.1))        # 4.6-5.7
        self.wait(0.4)
        self.play_scroll_unroll(cardB, run_time=1.6)   # 6.1-7.7
        self.wait(0.5)
        self.emphasize(cardB, mode="indicate", run_time=0.9)  # 8.2-9.1
        self.wait(0.4)
        self.play(FadeOut(Group(lineA, cnt50, cardB), shift=UP * 0.03), run_time=1.0)  # 9.5-10.5
        self.wait(2.1)                                  # -> 12.6
        self.at(12.6)

        # ---- 页2：还记得吗 + 三轴预告（12.6-26.2）----
        q = t("三小时后问它：还记得吗？", 40, YELL, "BOLD")
        fit(q, 0.92)
        c_nofull = _card("不能从头翻", 2.7, 1.4, CYAN, WHITE, 26, CARD_FILL, "BOLD")
        c_noquick = _card("也不能为快忘掉", 2.7, 1.4, CYAN, WHITE, 26, CARD_FILL, "BOLD")
        row2 = VGroup(c_nofull, c_noquick).arrange(RIGHT, buff=0.45)
        ans = t("答案：不是更大的窗口", 30, WHITE)
        fit(ans, 0.9)
        t1 = boxed("KDA\n省序列", 2.4, 2.4, YELL, 28, weight="BOLD")
        t2 = boxed("AttnRes\n救深度", 2.4, 2.4, CYAN, 28, weight="BOLD")
        t3 = boxed("Latent MoE\n控规模", 2.4, 2.4, GREEN, 28, weight="BOLD")
        trios = VGroup(t1, t2, t3).arrange(RIGHT, buff=0.3)
        layout_page(page_stack(q, row2, ans, trios, buff=1.0))

        self.play(type_in(q, run_time=1.4))            # 12.6-14.0
        self.wait(0.5)
        self.play_scroll_unroll(c_nofull, run_time=1.3)  # 14.5-15.8
        self.wait(0.4)
        self.play_scroll_unroll(c_noquick, run_time=1.3)    # 16.2-17.5
        self.wait(0.5)
        self.play(type_in(ans, run_time=1.2))          # 18.0-19.2
        self.wait(0.7)
        self.play_scroll_unroll(t1, run_time=1.1)      # 19.9-21.0
        self.wait(0.4)
        self.play_scroll_unroll(t2, run_time=1.1)      # 21.4-22.5
        self.wait(0.4)
        self.play_scroll_unroll(t3, run_time=1.1)      # 22.9-24.0
        self.wait(0.7)
        self.emphasize(trios, mode="wiggle", run_time=1.1)     # 24.7-25.8（wiggle 不放大，防贴边裁切）
        self.breathe(head, scale=1.03, run_time=1.0, loops=1)  # 25.8-26.8
        self.wait(0.4)
        self.transition_out(head, ftr, hint, q, row2, ans, trios, run_time=0.8)  # 27.2-28.0
        self.pad_to_voice()


# ================= S2 KDA 轴：序列方向 =================
# 句边界: [0.0, 9.7, 21.96, 29.83, 34.6]
class S2(_Base):
    def construct(self):
        self.bg()
        ftr = t("数解AI · 大模型原理", 20, MUTED).to_edge(DOWN, buff=1.15)
        self.add(ftr)
        head = t("第一轴 · KDA 序列方向", 36, YELL, "BOLD")
        fit(head, 0.92)
        head.to_edge(UP, buff=1.0)

        # ---- 页1：普通注意力逐词配对 → 100 万次（0-9.7）----
        toks = VGroup(*[cnode(f"x{i}", CYAN, radius=0.45, fs=20) for i in range(1, 5)])
        dots = VGroup(*[cnode("", MUTED, 0.17, fs=10) for _ in range(16)]).arrange_in_grid(4, 4, buff=0.62)
        lab_cnt = t("历史 100 万，配对", 28, WHITE)
        cnt_ph = Rectangle(width=2.6, height=1.4, fill_opacity=0.0, stroke_opacity=0.0)
        cnt_row = VGroup(lab_cnt, cnt_ph).arrange(RIGHT, buff=0.3)
        page1 = page_stack(toks, dots, cnt_row, buff=1.05)
        layout_page(page1)

        self.play(type_in(head, run_time=0.9))           # 0.0-0.9
        self.wait(0.6)
        self.play(FadeIn(toks, shift=DOWN * 0.05), run_time=0.7)  # 1.5-2.2
        self.wait(0.3)
        self.play(FadeIn(dots, shift=DOWN * 0.05), run_time=0.7)  # 2.5-3.2
        self.wait(0.3)
        conns = VGroup(*[Line(dots[0].get_center(), c.get_center(), color=CYAN, stroke_width=2)
                         for c in dots[1:]])
        self.play(*[Create(ln) for ln in conns], run_time=1.6, lag_ratio=0.15)  # 3.5-5.1 主视觉
        self.wait(0.4)
        cnt = self.counter_value(0, 100, suffix=" 万次", size=52, color=YELL,
                                 anchor=cnt_ph, run_time=1.8,
                                 extra_anims=[type_in(lab_cnt, 0.5)])    # 5.5-7.3
        self.wait(1.0)
        self.play(FadeOut(Group(page1, cnt, conns), shift=UP * 0.03), run_time=1.0)  # 8.3-9.3
        self.wait(0.4)
        self.at(9.7)

        # ---- 页2：会议速记概念图 + T²→T（9.7-21.96）----
        cardK = _card("KDA：维护一份「会议速记」", 5.8, 1.2, CYAN, WHITE, 28, CARD_FILL, "BOLD")
        img = ImageMobject("img/kda-speednote-round.png")
        img.scale_to_fit_width(3.1)
        cap = t("新信息写入 · 旧信息衰减", 24, WHITE)
        fit(cap, 0.9)
        cost_lab = t("处理量", 24, MUTED)
        t2card = _card("T 的平方", 2.6, 1.2, MUTED, WHITE, 24, CARD_FILL, "BOLD")
        tcard = _card("T", 2.0, 1.2, GREEN, WHITE, 28, CARD_FILL, "BOLD")
        cost_row = VGroup(t2card, tcard).arrange(RIGHT, buff=0.8)
        page2 = page_stack(cardK, img, cap, cost_lab, cost_row, buff=0.6)
        layout_page(page2)

        self.play_scroll_unroll(cardK, run_time=1.2)     # 9.7-10.9
        self.wait(0.6)
        self.play(FadeIn(img, shift=DOWN * 0.05), run_time=1.0)  # 11.5-12.5
        self.wait(0.5)
        self.play(type_in(cap, run_time=1.0))            # 13.0-14.0
        self.wait(0.7)
        self.play(type_in(cost_lab, run_time=0.7))       # 14.7-15.4
        self.wait(0.4)
        self.play_scroll_unroll(t2card, run_time=1.1)    # 15.8-16.9
        self.wait(0.3)
        cross = self.play_red_cross(t2card)              # 17.2-17.7
        self.wait(0.25)
        self.play(FadeOut(cross, run_time=0.3))          # 17.95-18.25
        self.wait(0.15)
        self.morph_to(t2card, tcard, run_time=1.0)       # 18.4-19.4
        self.wait(0.5)
        self.play(FadeOut(Group(cardK, img, cap, cost_lab, cost_row), shift=UP * 0.03),
                  run_time=0.9)                          # 19.9-20.8
        self.wait(0.66)                                  # -> 21.96
        self.at(21.96)

        # ---- 页3：69 + 24 = 93 层（21.96-29.83）----
        lab93 = t("落到 K3 的层配置", 28, WHITE)
        bar69 = Rectangle(width=4.4, height=1.9, color=CYAN, fill_color=CYAN, fill_opacity=0.85)
        lab69 = t("69 层 KDA", 26, CYAN, "BOLD")
        bar24 = Rectangle(width=1.6, height=1.9, color=YELL, fill_color=YELL, fill_opacity=0.85)
        lab24 = t("24 层 Gated MLA", 26, YELL, "BOLD")
        bars_row = VGroup(VGroup(bar69, lab69).arrange(DOWN, buff=0.3),
                          VGroup(bar24, lab24).arrange(DOWN, buff=0.3)).arrange(RIGHT, buff=0.5)
        tot_lab = t("一共", 30, WHITE)
        tot_ph = Rectangle(width=2.8, height=1.8, fill_opacity=0.0, stroke_opacity=0.0)
        tot_row = VGroup(tot_lab, tot_ph).arrange(RIGHT, buff=0.3)
        page3 = page_stack(lab93, bars_row, tot_row, buff=1.4)
        layout_page(page3)

        self.play(type_in(lab93, run_time=0.8))          # 21.96-22.76
        self.wait(0.4)
        tr69 = ValueTracker(0)
        self.grow_bar(bar69, tr69, 4.4, run_time=1.2, anchor="center", extra_anims=[type_in(lab69, 0.5)])  # 23.16-24.36
        self.wait(0.2)
        tr24 = ValueTracker(0)
        self.grow_bar(bar24, tr24, 1.6, run_time=1.1, anchor="center", extra_anims=[type_in(lab24, 0.5)])  # 24.56-25.66
        self.wait(0.3)
        cnt93 = self.counter_value(0, 93, suffix=" 层", size=56, color=YELL,
                                   anchor=tot_ph, run_time=1.5,
                                   extra_anims=[type_in(tot_lab, 0.5)])   # 25.96-27.46
        self.wait(0.3)
        self.emphasize(cnt93, mode="indicate", run_time=0.9)      # 27.76-28.66
        self.wait(0.17)
        self.play(FadeOut(Group(page3, cnt93), shift=UP * 0.03), run_time=0.5)  # 29.33-29.83
        self.at(29.83)

        # ---- 页4：93 层太深，信号走样（29.83-34.4）----
        big = t("93 层，太深了", 52, WHITE, "BOLD")
        fit(big, 0.92)
        card4 = _card("信号传着传着，就走样了", 5.8, 2.0, MUTED, WHITE, 28, CARD_FILL, "BOLD")
        q4 = t("这个坑，怎么填？", 52, YELL, "BOLD")
        fit(q4, 0.92)
        page_auto(big, card4, q4)  # 矮页：放大 + 居中（无中间空洞）

        self.play(type_in(big, run_time=1.1))            # 29.83-30.93
        self.wait(0.4)
        self.play_scroll_unroll(card4, run_time=1.4)     # 31.33-32.73
        self.wait(0.3)
        self.play(type_in(q4, run_time=1.1))             # 33.03-34.13
        self.wait(0.6)
        self.transition_out(head, ftr, big, card4, q4, run_time=0.5)  # 34.73-35.23
        self.pad_to_voice()


# ================= S3 AttnRes 轴：深度方向 =================
# 句边界: [0.0, 12.77, 22.91, 36.22]
class S3(_Base):
    def construct(self):
        self.bg()
        ftr = t("数解AI · 大模型原理", 20, MUTED).to_edge(DOWN, buff=1.15)
        self.add(ftr)
        head = t("第二轴 · AttnRes 深度救援", 36, YELL, "BOLD")
        fit(head, 0.92)
        head.to_edge(UP, buff=1.0)

        # ---- 页1：传话游戏概念图 + 层层稀释（0-12.77）----
        img = ImageMobject("img/telephone-game-round.png")
        img.scale_to_fit_width(3.8)
        cap = t("第 100 个人听到的，不是原话", 28, WHITE)
        fit(cap, 0.9)
        card = _card("93 层里，早期特征被层层稀释", 5.8, 1.7, CYAN, WHITE, 26, CARD_FILL, "BOLD")
        page1 = page_stack(img, cap, card, buff=0.9)
        layout_page(page1)

        self.play(type_in(head, run_time=0.9))           # 0.0-0.9
        self.wait(0.4)
        self.play(FadeIn(img, shift=DOWN * 0.05), run_time=1.6)  # 1.3-2.9
        self.wait(0.4)
        self.play(type_in(cap, run_time=1.2))            # 3.3-4.5
        self.wait(0.5)
        self.play_scroll_unroll(card, run_time=1.8)      # 5.0-6.8
        self.wait(5.2)                                   # 卡驻屏，对应台词「早期特征被层层稀释」
        self.play(FadeOut(Group(img, cap, card), shift=UP * 0.03), run_time=0.6)  # 12.0-12.6
        self.wait(0.17)
        self.at(12.77)

        # ---- 页2：AttnRes 翻任意层（12.77-22.91）----
        card2 = _card("AttnRes：能翻任意一层", 5.8, 1.5, CYAN, WHITE, 28, CARD_FILL, "BOLD")
        n93 = cnode("第 93 层", YELL, radius=1.25, fs=24)
        n3 = cnode("第 3 层", GREEN, radius=1.25, fs=24)
        node_row = VGroup(n93, n3).arrange(RIGHT, buff=2.6)
        ar = Arrow(n93.get_right(), n3.get_left(), color=YELL, buff=0.15, stroke_width=6)
        sub2 = t("不再只能问上一层", 26, MUTED)
        fit(sub2, 0.9)
        page2 = page_stack(card2, node_row, sub2, buff=1.55)
        layout_page(page2)

        self.play_scroll_unroll(card2, run_time=1.2)     # 12.77-13.97
        self.wait(0.6)
        self.play(FadeIn(n93, shift=DOWN * 0.05), run_time=0.6)  # 14.57-15.17
        self.wait(0.5)
        self.play(FadeIn(n3, shift=DOWN * 0.05), run_time=0.6)   # 15.67-16.27
        self.wait(0.3)
        self.play(Create(ar), run_time=1.0)              # 16.57-17.57 主视觉
        self.wait(0.6)
        self.play(type_in(sub2, run_time=1.0))           # 18.17-19.17
        self.wait(0.5)
        self.play(FadeOut(Group(card2, n93, n3, ar, sub2), shift=UP * 0.03), run_time=0.8)  # 19.67-20.47
        self.wait(2.44)                                  # -> 22.91
        self.at(22.91)

        # ---- 页3：分块 12 层一组，存储 93→8（22.91-35.3）----
        cMem = _card("每层输出都存 → 内存扛不住", 5.8, 1.3, MUTED, WHITE, 24, CARD_FILL, "BOLD")
        cBlock = _card("K3 分块：每 12 层一组", 5.8, 1.3, CYAN, WHITE, 26, CARD_FILL, "BOLD")
        blocks = VGroup(*[RoundedRectangle(width=1.15, height=0.75, corner_radius=0.15,
                                           color=CYAN, fill_color=CARD_FILL, fill_opacity=1.0)
                          for _ in range(8)])
        blocks.arrange_in_grid(2, 4, buff=0.35)
        blab = t("块间才做注意力检索", 22, MUTED)
        fit(blab, 0.9)
        s_ph = Rectangle(width=2.2, height=1.2, fill_opacity=0.0, stroke_opacity=0.0)
        lab_s = t("存储：93 份 → ", 24, WHITE)
        s_row = VGroup(lab_s, s_ph).arrange(RIGHT, buff=0.2)
        cQ = _card("还剩最后一轴：唤醒多少参数？", 5.8, 1.5, YELL, WHITE, 24, CARD_FILL, "BOLD")
        page3 = page_stack(cMem, cBlock, blocks, blab, s_row, cQ, buff=0.6)
        layout_page(page3)

        self.play_scroll_unroll(cMem, run_time=1.0)      # 22.91-23.91
        self.wait(0.3)
        xMem = self.play_red_cross(cMem)                 # 24.21-24.91
        self.wait(0.4)
        self.play_scroll_unroll(cBlock, run_time=1.1)    # 25.31-26.41
        self.wait(0.5)
        self.play(FadeIn(blocks, shift=DOWN * 0.05), run_time=1.0)  # 26.91-27.91
        self.wait(0.4)
        self.play(type_in(blab, run_time=0.8))           # 28.31-29.11
        self.wait(0.5)
        cnt8 = self.counter_value(0, 8, suffix=" 份", size=52, color=YELL,
                                  anchor=s_ph, run_time=1.5,
                                  extra_anims=[type_in(lab_s, 0.5)])    # 29.61-31.11
        self.wait(0.6)
        self.play_scroll_unroll(cQ, run_time=1.3)        # 31.71-33.01
        self.wait(0.5)
        self.play(FadeOut(Group(cMem, xMem, cBlock, blocks, blab, s_row, cnt8, cQ),
                          shift=UP * 0.03), run_time=0.7)  # 33.51-34.21
        self.wait(0.5)
        self.transition_out(head, ftr, run_time=0.5)     # 34.71-35.21
        self.pad_to_voice()


# ================= S4 Latent MoE 轴：通道方向 =================
# 句边界: [0.0, 14.64, 26.21, 32.48, 43.14]
class S4(_Base):
    def construct(self):
        self.bg()
        ftr = t("数解AI · 大模型原理", 20, MUTED).to_edge(DOWN, buff=1.15)
        self.add(ftr)
        head = t("第三轴 · Latent MoE 通道", 36, YELL, "BOLD")
        fit(head, 0.92)
        head.to_edge(UP, buff=1.0)

        # ---- 页1：896 挑 16 · 1.8% · 1040 亿（0-14.64）----
        lineA = t("2.8 万亿全醒 → 算力直接爆", 28, WHITE)
        fit(lineA, 0.9)
        c896 = _card("896 个路由专家", 2.9, 1.4, CYAN, WHITE, 24, CARD_FILL, "BOLD")
        c16 = _card("每 token 挑 16 个", 2.9, 1.4, CYAN, WHITE, 24, CARD_FILL, "BOLD")
        row16 = VGroup(c896, c16).arrange(RIGHT, buff=0.35)
        pct_lab = t("被激活", 26, WHITE)
        pct_ph = Rectangle(width=2.6, height=1.4, fill_opacity=0.0, stroke_opacity=0.0)
        pct_row = VGroup(pct_lab, pct_ph).arrange(RIGHT, buff=0.3)
        cShared = _card("+ 2 个共享专家 · 常驻兜底", 5.8, 1.1, GREEN, WHITE, 24, CARD_FILL, "BOLD")
        tot_lab2 = t("激活参数一共", 24, WHITE)
        tot_ph = Rectangle(width=3.0, height=1.4, fill_opacity=0.0, stroke_opacity=0.0)
        tot_row = VGroup(tot_lab2, tot_ph).arrange(RIGHT, buff=0.25)
        page1 = page_stack(lineA, row16, pct_row, cShared, tot_row, buff=0.55)
        layout_page(page1)

        self.play(type_in(head, run_time=0.9))           # 0.0-0.9
        self.wait(0.5)
        self.play(type_in(lineA, run_time=1.0))          # 1.4-2.4
        self.wait(0.5)
        self.play_scroll_unroll(c896, run_time=1.0)      # 2.9-3.9
        self.wait(0.5)
        self.play_scroll_unroll(c16, run_time=1.0)       # 4.4-5.4
        self.wait(0.6)
        cnt18 = self.counter_value(0, 1.8, suffix="%", decimals=1, size=48, color=YELL,
                                    anchor=pct_ph, run_time=1.6,
                                    extra_anims=[type_in(pct_lab, 0.5)])  # 6.0-7.6
        self.wait(0.6)
        self.play_scroll_unroll(cShared, run_time=1.2)   # 8.2-9.4
        self.wait(0.6)
        cnt1040 = self.counter_value(0, 1040, suffix=" 亿", size=50, color=YELL,
                                     anchor=tot_ph, run_time=1.8,
                                     extra_anims=[type_in(tot_lab2, 0.5)])  # 10.0-11.8
        self.wait(0.6)
        self.play(FadeOut(Group(page1, cnt1040, cnt18), shift=UP * 0.03), run_time=1.0)  # 12.4-13.4
        self.wait(1.24)                                  # -> 14.64
        self.at(14.64)

        # ---- 页2：草图批改概念图 + 维度条（14.64-26.21）----
        img = ImageMobject("img/blueprint-sketch-round.png")
        img.scale_to_fit_width(3.6)
        cap = t("先缩成草图批改 · 再升回原尺寸", 24, WHITE)
        fit(cap, 0.9)
        bar7 = Rectangle(width=4.4, height=0.9, color=CYAN, fill_color=CYAN, fill_opacity=0.85)
        lab7 = t("7168 维", 22, CYAN, "BOLD")
        bar3 = Rectangle(width=2.2, height=0.9, color=YELL, fill_color=YELL, fill_opacity=0.85)
        lab3 = t("3584 维", 22, YELL, "BOLD")
        dim_row = VGroup(VGroup(bar7, lab7).arrange(DOWN, buff=0.2),
                         VGroup(bar3, lab3).arrange(DOWN, buff=0.2)).arrange(RIGHT, buff=0.5)
        cHalf = _card("搬运量减半", 5.8, 1.2, GREEN, WHITE, 26, CARD_FILL, "BOLD")
        page2 = page_stack(img, cap, dim_row, cHalf, buff=0.7)
        layout_page(page2)

        self.play(FadeIn(img, shift=DOWN * 0.05), run_time=1.2)  # 14.64-15.84
        self.wait(0.6)
        self.play(type_in(cap, run_time=1.0))            # 16.44-17.44
        self.wait(0.7)
        tr7 = ValueTracker(0)
        self.grow_bar(bar7, tr7, 4.4, run_time=1.3, anchor="center", extra_anims=[type_in(lab7, 0.5)])  # 18.14-19.44
        self.wait(0.5)
        tr3 = ValueTracker(0)
        self.grow_bar(bar3, tr3, 2.2, run_time=1.1, anchor="center", extra_anims=[type_in(lab3, 0.5)])  # 19.94-21.04
        self.wait(0.9)
        self.play_scroll_unroll(cHalf, run_time=1.3)     # 21.94-23.24
        self.wait(0.7)
        self.play(FadeOut(Group(img, cap, dim_row, cHalf), shift=UP * 0.03), run_time=0.9)  # 23.94-24.84
        self.wait(1.37)                                  # -> 26.21
        self.at(26.21)

        # ---- 页3：忙死闲死（26.21-32.48）----
        lab3p = t("忙的忙死 · 闲的闲死", 30, WHITE)
        fit(lab3p, 0.92)
        b_hi = Rectangle(width=1.2, height=3.4, color=RED, fill_color=RED, fill_opacity=0.85)
        b_lo = Rectangle(width=1.2, height=0.9, color=MUTED, fill_color=MUTED, fill_opacity=0.85)
        lab_hi = t("过载", 22, RED, "BOLD")
        lab_lo = t("闲置", 22, MUTED, "BOLD")
        bars2 = VGroup(VGroup(b_hi, lab_hi).arrange(DOWN, buff=0.25),
                       VGroup(b_lo, lab_lo).arrange(DOWN, buff=0.25)
                       ).arrange(RIGHT, buff=1.6)
        for m in bars2:
            m.align_to(ORIGIN, DOWN)
        card3p = _card("白占显存 · 浪费", 5.8, 1.2, MUTED, WHITE, 26, CARD_FILL, "BOLD")
        page3 = page_stack(lab3p, bars2, card3p, buff=1.0)
        layout_page(page3)

        self.play(type_in(lab3p, run_time=0.9))          # 26.21-27.11
        self.wait(0.4)
        trH = ValueTracker(0)
        self.grow_bar(b_hi, trH, 3.4, run_time=1.0, anchor="center",
                      extra_anims=[type_in(lab_hi, 0.5)])      # 27.51-28.51
        self.wait(0.3)
        trL = ValueTracker(0)
        self.grow_bar(b_lo, trL, 0.9, run_time=0.9, anchor="center",
                      extra_anims=[type_in(lab_lo, 0.5)])      # 28.81-29.71
        self.wait(0.4)
        self.play_scroll_unroll(card3p, run_time=1.1)    # 30.11-31.21
        self.wait(0.3)
        self.play(FadeOut(Group(lab3p, bars2, card3p), shift=UP * 0.03), run_time=0.7)  # 31.51-32.21
        self.wait(0.27)                                  # -> 32.48
        self.at(32.48)

        # ---- 页4：Quantile Balancing 天平（32.48-41.3）----
        cardQ = _card("Quantile Balancing", 5.8, 1.3, CYAN, WHITE, 28, CARD_FILL, "BOLD")
        rig, pans, pivot = self.build_balance("选太多", "压下去", "选太少", "抬上来", beam=4.6)
        sub4 = t("偏置只定选不选 · 不掺和加权", 26, MUTED)
        fit(sub4, 0.9)
        cardE = _card("负载自动拉平", 5.8, 1.3, GREEN, WHITE, 26, CARD_FILL, "BOLD")
        page4 = page_stack(cardQ, VGroup(rig, pans), sub4, cardE, buff=0.9)
        layout_page(page4)

        self.play_scroll_unroll(cardQ, run_time=1.1)     # 32.48-33.58
        self.wait(0.4)
        self.play(FadeIn(VGroup(rig, pans), shift=DOWN * 0.05), run_time=0.7)  # 33.98-34.68
        self.wait(0.3)
        self.tilt_balance(rig, pans, pivot, 0.15, run_time=1.0)   # 34.98-35.98 左盘重（选太多）
        self.wait(0.5)
        self.tilt_balance(rig, pans, pivot, -0.15, run_time=1.0)   # 36.48-37.48 回平
        self.wait(0.4)
        self.play(type_in(sub4, run_time=0.9))           # 37.88-38.78
        self.wait(0.5)
        self.play_scroll_unroll(cardE, run_time=1.0)     # 39.28-40.28
        self.wait(0.4)
        self.transition_out(head, ftr, cardQ, rig, pans, sub4, cardE, run_time=0.6)  # 40.68-41.28
        self.pad_to_voice()


# ================= S5 Benchmark 段：跑分见真章 =================
# 句边界: [0.0, 11.4, 19.77, 30.21, 37.12]
class S5(_Base):
    def construct(self):
        self.bg()
        ftr = t("数解AI · 大模型原理", 20, MUTED).to_edge(DOWN, buff=1.15)
        self.add(ftr)
        head = t("跑分见真章", 36, YELL, "BOLD")
        fit(head, 0.92)
        head.to_edge(UP, buff=1.0)

        # ---- 页1：SWE Marathon 三柱对比（0-11.4）----
        lab1 = t("SWE Marathon · 长程编程", 30, WHITE)
        fit(lab1, 0.92)
        b_f = Rectangle(width=1.5, height=3.0, color=MUTED, fill_color=MUTED, fill_opacity=0.85)
        v_f = t("35", 28, MUTED, "BOLD")
        b_g = Rectangle(width=1.5, height=3.35, color=CYAN, fill_color=CYAN, fill_opacity=0.85)
        v_g = t("39", 28, CYAN, "BOLD")
        b_k = Rectangle(width=1.5, height=3.7, color=YELL, fill_color=YELL, fill_opacity=0.85)
        v_k = t("42", 28, YELL, "BOLD")
        n_f = t("Fable 5", 24, MUTED)
        n_g = t("GPT-5.6 Sol", 24, CYAN)
        n_k = t("K3", 24, YELL, "BOLD")
        # 柱高按分值编码 3.0/3.35/3.7（35/39/42 线性），柱宽统一 1.5，柱底对齐——不重叠
        c_f = VGroup(b_f, v_f, n_f).arrange(DOWN, buff=0.3)
        c_g = VGroup(b_g, v_g, n_g).arrange(DOWN, buff=0.3)
        c_k = VGroup(b_k, v_k, n_k).arrange(DOWN, buff=0.3)
        rows = VGroup(c_f, c_g, c_k).arrange(RIGHT, buff=0.5)
        for m in rows:
            m.align_to(ORIGIN, DOWN)   # 柱底对齐（名字同字号，柱底等高）
        names = VGroup(n_f, n_g, n_k)
        page1 = page_stack(lab1, rows, buff=1.8)
        layout_page(page1)

        self.play(type_in(head, run_time=0.9))           # 0.0-0.9
        self.wait(0.5)
        self.play(type_in(lab1, run_time=0.9))           # 1.4-2.3
        self.wait(0.4)
        trF = ValueTracker(0)
        self.grow_bar(b_f, trF, 1.5, run_time=1.2, anchor="center", extra_anims=[type_in(v_f, 0.5)])  # 2.7-3.9
        self.wait(0.4)
        trG = ValueTracker(0)
        self.grow_bar(b_g, trG, 1.5, run_time=1.2, anchor="center", extra_anims=[type_in(v_g, 0.5)])  # 4.3-5.5
        self.wait(0.6)
        trK = ValueTracker(0)
        self.grow_bar(b_k, trK, 1.5, run_time=1.4, anchor="center", extra_anims=[type_in(v_k, 0.6)])  # 6.1-7.5
        self.wait(0.5)
        self.play(FadeIn(names, shift=DOWN * 0.05), run_time=0.7)   # 8.0-8.7
        self.wait(0.8)
        self.emphasize(v_k, mode="indicate", run_time=0.8)      # 9.5-10.3
        self.wait(0.4)
        self.play(FadeOut(Group(lab1, rows, names), shift=UP * 0.03), run_time=0.7)  # 10.7-11.4
        self.at(11.4)

        # ---- 页2：BrowseComp 91.2 第一（11.4-19.77）----
        lab2 = t("BrowseComp · Agent 浏览", 30, WHITE)
        fit(lab2, 0.92)
        bph = Rectangle(width=3.0, height=2.1, fill_opacity=0.0, stroke_opacity=0.0)
        badge = cnode("第一", GREEN, radius=1.05, fs=30)
        num_badge = VGroup(bph, badge).arrange(RIGHT, buff=0.7)
        sub = t("Fable 5: 88.0 · GPT-5.6 Sol: 90.4", 24, MUTED)
        fit(sub, 0.92)
        card = _card("最吃长上下文的任务 = 三轴目标", 5.8, 1.5, CYAN, WHITE, 26, CARD_FILL, "BOLD")
        page2 = page_stack(lab2, num_badge, sub, card, buff=1.2)
        layout_page(page2)

        self.play(type_in(lab2, run_time=0.8))           # 11.4-12.2
        self.wait(0.5)
        cnt = self.counter_value(0, 91.2, decimals=1, size=60, color=YELL,
                                 anchor=bph, run_time=1.8)        # 12.7-14.5
        self.wait(0.5)
        self.play(FadeIn(badge, shift=DOWN * 0.05), run_time=0.7) # 15.0-15.7
        self.wait(0.6)
        self.play(type_in(sub, run_time=0.9))            # 16.3-17.2
        self.wait(0.4)
        self.play(type_in(card, run_time=1.2))           # 17.6-18.8
        self.wait(0.3)
        self.play(FadeOut(Group(lab2, num_badge, sub, card, cnt), shift=UP * 0.03),
                  run_time=0.6)                          # 19.1-19.7
        self.wait(0.07)
        self.at(19.77)

        # ---- 页3：1.6T → 2.8T（19.77-30.21）----
        lab3 = t("上一代开源天花板", 28, MUTED)
        fit(lab3, 0.9)
        b_v = Rectangle(width=1.6, height=2.1, color=MUTED, fill_color=MUTED, fill_opacity=0.85)
        v_v = t("1.6 万亿", 26, MUTED, "BOLD")
        b_k3 = Rectangle(width=2.8, height=3.6, color=YELL, fill_color=YELL, fill_opacity=0.85)
        v_k3 = t("2.8 万亿", 26, YELL, "BOLD")
        rows = VGroup(VGroup(b_v, v_v).arrange(DOWN, buff=0.3),
                      VGroup(b_k3, v_k3).arrange(DOWN, buff=0.3)).arrange(RIGHT, buff=0.9)
        for m in rows:
            m.align_to(ORIGIN, DOWN)
        n_ds = t("DeepSeek-V4-Pro", 22, MUTED)
        n_k = t("Kimi K3", 22, YELL, "BOLD")
        nrow = VGroup(n_ds, n_k).arrange(RIGHT, buff=1.1)
        card7 = _card("多了七成", 5.8, 1.3, YELL, YELL, 30, CARD_FILL, "BOLD")
        page3 = page_stack(lab3, rows, nrow, card7, buff=1.1)
        layout_page(page3)

        self.play(type_in(lab3, run_time=0.8))           # 19.77-20.57
        self.wait(0.5)
        trV = ValueTracker(0)
        self.grow_bar(b_v, trV, 1.7, run_time=1.3, anchor="center", extra_anims=[type_in(v_v, 0.5)])  # 21.07-22.37
        self.wait(0.5)
        trK = ValueTracker(0)
        self.grow_bar(b_k3, trK, 3.0, run_time=1.5, anchor="center", extra_anims=[type_in(v_k3, 0.6)])  # 22.87-24.37
        self.wait(0.5)
        self.play(type_in(nrow, run_time=1.0))           # 24.87-25.87
        self.wait(0.6)
        self.play_scroll_unroll(card7, run_time=1.2)     # 26.47-27.67
        self.wait(0.6)
        self.play(FadeOut(Group(lab3, rows, nrow, card7), shift=UP * 0.03), run_time=0.8)  # 28.27-29.07
        self.wait(1.14)                                  # -> 30.21
        self.at(30.21)

        # ---- 页4：回到第 37 轮（30.21-37.6）----
        cBack = _card("回到第 37 轮的约束", 5.8, 1.3, CYAN, WHITE, 28, CARD_FILL, "BOLD")
        b1 = boxed("KDA\n省序列", 1.7, 1.6, YELL, 22, weight="BOLD")
        b2 = boxed("AttnRes\n救信号", 1.7, 1.6, CYAN, 22, weight="BOLD")
        b3 = boxed("Latent\n控规模", 1.7, 1.6, GREEN, 22, weight="BOLD")
        badges = VGroup(b1, b2, b3).arrange(RIGHT, buff=0.3)
        big1 = t("三轴合力", 46, WHITE, "BOLD")
        fit(big1, 0.92)
        big2 = t("不但跑得动，还跑得赢", 42, YELL, "BOLD")
        fit(big2, 0.92)
        page4 = page_stack(cBack, badges, big1, big2, buff=1.2)
        layout_page(page4)

        self.play_scroll_unroll(cBack, run_time=1.1)     # 30.21-31.31
        self.wait(0.5)
        self.play(FadeIn(badges, shift=DOWN * 0.05), run_time=0.8)  # 31.81-32.61
        self.wait(0.5)
        self.play(type_in(big1, run_time=1.0))           # 33.11-34.11
        self.wait(0.5)
        self.play(type_in(big2, run_time=1.1))           # 34.61-35.71
        self.wait(0.5)
        self.emphasize(big2, mode="indicate", run_time=0.9)      # 36.21-37.11
        self.transition_out(head, ftr, cBack, badges, big1, big2, run_time=0.5)  # 37.11-37.61
        self.pad_to_voice()


# ================= S6 总结 + 预告 + 互动 + 品牌尾卡 =================
# 句边界: [0.0, 12.75, 20.17]
class S6(_Base):
    def construct(self):
        self.bg()
        ftr = t("数解AI · 大模型原理", 20, MUTED).to_edge(DOWN, buff=1.15)
        self.add(ftr)
        head = t("总结 · 三轴合力", 36, YELL, "BOLD")
        fit(head, 0.92)
        head.to_edge(UP, buff=1.0)

        # ---- 页1：三轴总结 + 上限 ≠ 听话（0-12.75）----
        line = t("所以秘密不在堆料", 28, WHITE)
        fit(line, 0.9)
        t1 = boxed("KDA\n压序列", 2.3, 1.8, YELL, 24, weight="BOLD")
        t2 = boxed("AttnRes\n救信号", 2.3, 1.8, CYAN, 24, weight="BOLD")
        t3 = boxed("Latent MoE\n控规模", 2.3, 1.8, GREEN, 24, weight="BOLD")
        trios = VGroup(t1, t2, t3).arrange(RIGHT, buff=0.35)
        cCap = _card("能跑 1M 上下文 ≠ 天生会听话", 5.8, 1.5, MUTED, WHITE, 24, CARD_FILL, "BOLD")
        sub = t("它，还是语言底座", 26, MUTED)
        page1 = page_stack(line, trios, cCap, sub, buff=1.0)
        layout_page(page1)

        self.play(type_in(head, run_time=0.9))           # 0.0-0.9
        self.wait(0.4)
        self.play(type_in(line, run_time=0.9))           # 1.3-2.2
        self.wait(0.5)
        self.play_scroll_unroll(t1, run_time=1.0)        # 2.7-3.7
        self.wait(0.4)
        self.play_scroll_unroll(t2, run_time=1.0)        # 4.1-5.1
        self.wait(0.4)
        self.play_scroll_unroll(t3, run_time=1.0)        # 5.5-6.5
        self.wait(0.6)
        self.play_scroll_unroll(cCap, run_time=1.2)      # 7.1-8.3
        self.wait(0.4)
        xCap = self.play_red_cross(cCap)                 # 8.7-9.4
        self.wait(0.7)
        self.play(type_in(sub, run_time=0.9))            # 10.1-11.0
        self.wait(0.7)
        self.play(FadeOut(Group(line, trios, cCap, xCap, sub), shift=UP * 0.03), run_time=0.55)  # 12.0-12.55
        self.wait(0.2)                                   # -> 12.75
        self.at(12.75)

        # ---- 页2：DeepSeek CSA 预告（12.75-20.17）----
        # 2026-08-27 用户拍板：预告改为 DeepSeek CSA（音轨未改，字幕经 manual-boundaries.json 覆盖）
        lab = t("下期预告", 30, MUTED)
        fit(lab, 0.9)
        cCsa = _card("DeepSeek CSA", 5.8, 2.6, YELL, WHITE, 44, CARD_FILL, "BOLD")
        sub2 = t("V4 为何不用 MLA？", 32, WHITE)
        fit(sub2, 0.92)
        page_auto(lab, cCsa, sub2)  # 矮页：紧凑 + 放大 + 居中

        self.play(type_in(lab, run_time=0.7))            # 12.75-13.45
        self.wait(0.5)
        self.play_scroll_unroll(cCsa, run_time=1.6)      # 13.95-15.55
        self.wait(0.6)
        self.play(type_in(sub2, run_time=1.0))           # 16.15-17.15
        self.wait(0.6)
        self.play(FadeOut(Group(lab, cCsa, sub2), shift=UP * 0.03), run_time=0.8)  # 17.75-18.55
        self.wait(1.62)                                  # -> 20.17
        self.at(20.17)

        # ---- 页3a：互动问题（20.17-25.1）----
        q1 = t("假如你来设计 2.8 万亿模型", 34, WHITE)
        fit(q1, 0.92)
        cQ = _card("更多层给 KDA，还是 Gated MLA？", 6.0, 2.6, YELL, WHITE, 28, CARD_FILL, "BOLD")
        q2 = t("评论区聊聊", 30, MUTED)
        page_auto(q1, cQ, q2)  # 矮页：紧凑 + 居中

        self.play(type_in(q1, run_time=0.9))             # 20.17-21.07
        self.wait(0.5)
        self.play_scroll_unroll(cQ, run_time=1.2)        # 21.57-22.77
        self.wait(0.5)
        self.play(type_in(q2, run_time=0.8))             # 23.27-24.07
        self.wait(0.4)
        self.play(FadeOut(Group(q1, cQ, q2), shift=UP * 0.03), run_time=0.7)  # 24.47-25.17
        self.wait(0.4)

        # ---- 页3b：品牌尾卡（25.6-27.5，停留到结尾）----
        logo = ImageMobject("avatar-sjai-round.png")
        logo.scale_to_fit_width(3.4)
        follow = t("关注「数解AI」", 36, YELL, "BOLD")
        fit(follow, 0.9)
        title = t("《Kimi K3 架构怎么撑住 2.8T 参数？三轴拆给你看》", 26, WHITE, "BOLD")
        fit(title, 0.94)
        wc = t("查看公众号文章", 28, GREEN, "BOLD")
        fit(wc, 0.9)
        more = t("想获得更多细节解读", 24, MUTED)
        tail = Group(more, logo, follow, title, wc).arrange(DOWN, buff=0.55)
        layout_page(tail)

        self.play(FadeIn(logo, shift=UP * 0.05), run_time=0.4)   # 25.6-26.0
        self.play(type_in(more, run_time=0.4),
                  type_in(follow, run_time=0.4),
                  type_in(title, run_time=0.4),
                  type_in(wc, run_time=0.4),
                  run_time=1.5, lag_ratio=1.0)           # 26.0-27.5 尾卡串行
        self.pad_to_voice()
