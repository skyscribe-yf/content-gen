#!/usr/bin/env python3
"""《多Token预测：一次猜两个词，快1.8倍》视频号 Manim 动画（竖屏 1080×1920）

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
VOICE_DUR = {"S1": 19.65, "S2": 28.1, "S3": 33.47, "S4": 33.01, "S5": 41.76, "S6": 41.19}
TAIL = 2.5


def _footer(self) -> Text:
    f = t("数解AI · DeepSeek 技术解密", 20, MUTED).to_edge(DOWN, buff=1.15)
    self.add(f)
    return f


def _head(text: str, size: float = 38) -> Text:
    return t(text, size, YELL, "BOLD").to_edge(UP, buff=1.2)


# ---------------- S1 开场钩子：一步一词的死结 ----------------
class S1(_Base):
    def construct(self):
        self.bg()
        f = _footer(self)

        # 页1：概念图（接力赛）+ token 链 + 顺序锁死
        head = _head("一步一词：GPU 在等词", 36)
        note0 = t("以 DeepSeek-V3 为例", 24, MUTED).next_to(head, DOWN, buff=0.5)
        img = ImageMobject(str(IMG / "s1-relay-round.png"))
        img.scale_to_fit_width(5.5)
        tokens = VGroup(*[Rectangle(width=1.3, height=0.9, color=CYAN,
                                    fill_color=CYAN, fill_opacity=0.2) for _ in range(3)])
        tokens.arrange(RIGHT, buff=0.3)
        tlabs = [t("第 1 个", 22, WHITE, "BOLD"), t("第 2 个", 22, WHITE, "BOLD"),
                 t("第 3 个", 22, WHITE, "BOLD")]
        for tl, tk in zip(tlabs, tokens):
            tl.move_to(tk.get_center())
        tok_grp = VGroup(*[VGroup(tk, tl) for tk, tl in zip(tokens, tlabs)])
        caption = t("第 2 个永远在等第 1 个——顺序锁死", 30, WHITE)
        page1 = page_stack(img, tok_grp, caption, buff=1.1)
        layout_page(page1)

        self.at_clip("S1-c01")
        self.play_parallel(type_in(head, run_time=1.1), FadeIn(note0, shift=DOWN * 0.05),
                           FadeIn(img, shift=DOWN * 0.05), run_time=1.1)
        self.at_clip("S1-c02")
        self.play(*[Create(tk) for tk in tokens], *[FadeIn(tl) for tl in tlabs],
                  run_time=1.0, lag_ratio=0.3)  # 主视觉：token 链
        self.at_clip("S1-c03")
        self.play(type_in(caption, run_time=0.9))
        self.at_clip("S1-c04")
        self.emphasize(caption, run_time=0.5)  # 1/5

        # 页2：问句爆点 + MTP
        head2 = _head("能不能一次猜两个词？", 44)
        ans = t("能。", 72, GREEN, "BOLD")
        line = t("DeepSeek-V3 训练时顺手造了个小模块", 32, WHITE)
        mtp = t("MTP", 60, CYAN, "BOLD")
        page2 = page_auto(ans, line, mtp)

        self.at_clip("S1-c05")
        self.play(FadeOut(head), FadeOut(note0), FadeOut(page1),
                  type_in(head2, run_time=0.9), run_time=0.9)
        self.at_clip("S1-c06")
        self.play(type_in(ans, run_time=0.35))
        self.at_clip("S1-c07")
        self.play(type_in(line, run_time=0.8))
        self.at_clip("S1-c08")
        self.play(type_in(mtp, run_time=0.6))
        self.emphasize(mtp, run_time=0.5)  # 2/5
        self.transition_out(head2, f, ans, line, mtp)
        self.pad_to_voice()


# ---------------- S2 训练时答案在手：teacher forcing + 侧头 ----------------
class S2(_Base):
    def construct(self):
        self.bg()
        f = _footer(self)

        # 页1：teacher forcing
        head = _head("训练时：答案就在手里", 38)
        card1 = _card("语料里每个位置的真实词都是已知的", 6.4, 2.2, CYAN, WHITE, 32, CARD_FILL, "BOLD")
        line1a = t("预测下一个词时，", 30, WHITE)
        line1b = t("前一个词就写在训练数据里", 30, WHITE)
        line1 = VGroup(line1a, line1b).arrange(DOWN, buff=0.15)
        card2 = _card("teacher forcing：用真实词当条件", 6.4, 2.2, GREEN, WHITE, 32, CARD_FILL, "BOLD")
        page1 = page_stack(card1, line1, card2, buff=1.1)
        layout_page(page1)

        self.at_clip("S2-c01")
        self.play(type_in(head, run_time=0.9))
        self.wait(0.1)
        self.play_scroll_unroll(card1, run_time=1.0)  # 主视觉：拉幕
        self.at_clip("S2-c02")
        self.play(type_in(line1, run_time=0.8))
        self.at_clip("S2-c03")
        self.play_scroll_unroll(card2, run_time=1.2)
        self.at_clip("S2-c04")

        # 页2：MTP 侧头结构图
        head2 = _head("MTP 侧头：多猜一个词", 38)
        main_box = _card("主干表示", 3.4, 1.5, CYAN, WHITE, 30, CARD_FILL, "BOLD")
        emb_box = _card("真实词 embedding", 3.4, 1.5, GREEN, WHITE, 30, CARD_FILL, "BOLD")
        top_row = VGroup(main_box, emb_box).arrange(RIGHT, buff=0.6)
        concat = _card("拼接", 1.6, 1.0, YELL, WHITE, 28, CARD_FILL, "BOLD")
        block = _card("Transformer block", 3.4, 1.5, CYAN, WHITE, 30, CARD_FILL, "BOLD")
        out = t("下下一个词", 40, YELL, "BOLD")
        concat.next_to(top_row, DOWN, buff=0.5)
        block.next_to(concat, DOWN, buff=0.5)
        out.next_to(block, DOWN, buff=0.5)
        a1 = Arrow(main_box.get_bottom(), concat.get_top(), color=MUTED, buff=0.1, stroke_width=3)
        a2 = Arrow(emb_box.get_bottom(), concat.get_top(), color=MUTED, buff=0.1, stroke_width=3)
        a3 = Arrow(concat.get_bottom(), block.get_top(), color=MUTED, buff=0.1, stroke_width=3)
        a4 = Arrow(block.get_bottom(), out.get_top(), color=MUTED, buff=0.1, stroke_width=3)
        diagram = VGroup(top_row, concat, block, out, a1, a2, a3, a4)
        cap = t("共享 embedding 和输出头，成本极低", 26, MUTED)
        page2 = page_stack(diagram, cap, buff=0.9)
        layout_page(page2)

        self.play(FadeOut(head), FadeOut(page1), type_in(head2, run_time=0.8), run_time=0.8)
        self.at_clip("S2-c05")
        self.play(FadeIn(main_box, shift=UP * 0.05), FadeIn(emb_box, shift=UP * 0.05),
                  FadeIn(concat, shift=UP * 0.05), run_time=0.9)
        self.at_clip("S2-c06")
        self.play(Create(a1), Create(a2), Create(a3), FadeIn(block, shift=UP * 0.05),
                  run_time=0.9)  # 主视觉：结构图组装
        self.at_clip("S2-c07")
        self.play(Create(a4), type_in(out, run_time=0.6), type_in(cap, run_time=0.7), run_time=0.9)

        # 页3：两个交叉熵 + 信号翻倍
        head3 = _head("一次前向，两个交叉熵", 40)
        card3 = _card("一次前向，两个交叉熵", 6.4, 2.8, CYAN, WHITE, 40, CARD_FILL, "BOLD")
        lab = t("学习信号", 40, WHITE, "BOLD")
        slot = dynamic_slot(2.2, 1.2)
        row = stable_row(lab, slot, buff=0.4)
        line2 = t("训练信号更密，数据效率更高", 34, WHITE)
        page3 = page_stack(card3, row, line2, buff=1.4)
        layout_page(page3)

        self.play(FadeOut(head2), FadeOut(page2), type_in(head3, run_time=0.8), run_time=0.8)
        self.at_clip("S2-c08")
        self.play_scroll_unroll(card3, run_time=1.0)
        self.wait(1.0)
        n = self.counter_value(0, 2, suffix=" 倍", size=110, color=YELL,
                               run_time=1.2, anchor=slot,
                               extra_anims=[type_in(lab, run_time=0.6),
                                            type_in(line2, run_time=0.8)])  # 主视觉：数字滚动
        self.wait(0.68)  # 补到 c08 结束（28.16），台词讲完再转场
        self.transition_out(head3, f, card3, row, n, line2)
        self.pad_to_voice()


# ---------------- S3 推理镜像：猜一串，验一串 ----------------
class S3(_Base):
    def construct(self):
        self.bg()
        f = _footer(self)

        # 页1：没有真实词 → 让侧头自己猜
        head = _head("推理时：没有真实词", 38)
        q = t("第 2 个 token 还没生成，拿什么当条件？", 34, WHITE)
        ans = t("让侧头自己猜", 48, YELL, "BOLD")
        page1 = page_auto(q, ans)

        self.at_clip("S3-c01")
        self.play(type_in(head, run_time=0.9))
        self.at_clip("S3-c02")
        self.play(type_in(q, run_time=0.8))
        self.at_clip("S3-c03")
        self.play(type_in(ans, run_time=0.7))
        self.emphasize(ans, run_time=0.5)  # 3/5

        # 页2：投机解码流程
        head2 = _head("投机解码：猜一串，验一串", 38)
        draft = VGroup(*[_card(f"候选 {i}", 1.7, 2.0, YELL, WHITE, 26, CARD_FILL, "BOLD")
                         for i in range(1, 4)]).arrange(RIGHT, buff=0.3)
        verify = _card("主模型一次前向，全部验证", 5.6, 2.4, GREEN, WHITE, 30, CARD_FILL, "BOLD")
        r1 = t("一致的候选就收下", 34, WHITE)
        r2 = t("不一致的地方，换成主模型自己的答案重来", 34, WHITE)
        verify.next_to(draft, DOWN, buff=0.8)
        r1.next_to(verify, DOWN, buff=0.7)
        r2.next_to(r1, DOWN, buff=0.5)
        a = Arrow(draft.get_bottom(), verify.get_top(), color=YELL, buff=0.1, stroke_width=4)
        diagram = VGroup(draft, verify, r1, r2, a)
        page2 = page_stack(diagram, buff=1.1)
        layout_page(page2)

        self.at_clip("S3-c04")
        self.play(FadeOut(head), FadeOut(page1), type_in(head2, run_time=0.8), run_time=0.8)
        self.play(*[Create(d) for d in draft], run_time=1.2, lag_ratio=0.3)  # 主视觉：候选块
        self.at_clip("S3-c05")
        self.play(Create(a), run_time=0.5)
        self.wait(0.1)
        self.play_scroll_unroll(verify, run_time=1.0)
        self.at_clip("S3-c06")
        self.play(type_in(r1, run_time=0.7), type_in(r2, run_time=0.8), run_time=0.9)

        # 页3：接受率 + 1.8 倍账
        head3 = _head("接受率账", 38)
        lab1 = t("第二个 token 接受率", 34, WHITE, "BOLD")
        slot1 = dynamic_slot(2.8, 1.4)
        row1 = stable_row(lab1, slot1, buff=0.4)
        lab15 = t("每步推进", 34, WHITE, "BOLD")
        slot15 = dynamic_slot(2.8, 1.4)
        row15 = stable_row(lab15, slot15, buff=0.4)
        cost = t("侧头成本只占主头 2%-3%", 34, WHITE)
        lab2 = t("生成速度", 34, WHITE, "BOLD")
        slot2 = dynamic_slot(2.8, 1.4)
        row2 = stable_row(lab2, slot2, buff=0.4)
        page3 = page_stack(row1, row15, cost, row2, buff=1.0)
        layout_page(page3)

        self.at_clip("S3-c07")
        self.play(FadeOut(head2), FadeOut(page2), type_in(head3, run_time=0.8), run_time=0.8)
        n1 = self.counter_value(0, 85, suffix="%~90%", size=56, color=YELL,
                                run_time=2.5, anchor=slot1,
                                extra_anims=[type_in(lab1, run_time=0.6)])  # 主视觉：数字滚动
        self.wait(2.12)  # 补到 c07 结束（24.98）
        self.at_clip("S3-c08")
        n15 = self.counter_value(0, 1.85, suffix=" 个词", decimals=2, size=56, color=YELL,
                                 run_time=1.2, anchor=slot15,
                                 extra_anims=[type_in(lab15, run_time=0.6)])
        self.wait(2.08)  # 补到 c08 结束（28.26）
        self.at_clip("S3-c09")
        self.play(type_in(cost, run_time=0.8))
        self.wait(1.44)
        n2 = self.counter_value(0, 1.8, suffix=" 倍", decimals=1, size=56, color=YELL,
                                run_time=1.2, anchor=slot2,
                                extra_anims=[type_in(lab2, run_time=0.6)])  # 主视觉：数字滚动
        self.wait(1.84)  # 补到 c09 结束（33.54），台词讲完再转场
        self.transition_out(head3, f, row1, n1, row15, n15, cost, row2, n2)
        self.pad_to_voice()


# ---------------- S4 侧头从哪来：训练时白赚的信号 ----------------
class S4(_Base):
    def construct(self):
        self.bg()
        f = _footer(self)

        # 页1：转折——不是为推理设计的
        head = _head("这个侧头，是为推理设计的吗？", 36)
        card = _card("为推理设计？", 5.6, 2.2, CYAN, WHITE, 40, CARD_FILL, "BOLD")
        ans = t("不是。", 64, WHITE, "BOLD")
        line1 = t("MTP 的初衷是训练", 32, WHITE)
        line2 = t("每份数据给模型两次学习信号", 32, WHITE)
        page1 = page_stack(card, ans, line1, line2, buff=1.1)
        layout_page(page1)

        self.at_clip("S4-c01")
        self.play(type_in(head, run_time=0.9))
        self.wait(0.1)
        self.play_scroll_unroll(card, run_time=1.0)  # 主视觉：拉幕
        self.at_clip("S4-c02")
        cross = self.play_red_cross(card, run_time=0.5)
        self.play(type_in(ans, run_time=0.5), type_in(line1, run_time=0.7), run_time=0.8)
        self.at_clip("S4-c04")
        self.play(type_in(line2, run_time=0.8))

        # 页2：消融数字
        head2 = _head("消融实验：不是白说", 38)
        card2 = _card("15.7B 小模型 + MTP", 6.4, 1.8, CYAN, WHITE, 34, CARD_FILL, "BOLD")
        lab1 = t("BBH", 40, WHITE, "BOLD")
        slot1 = dynamic_slot(2.6, 1.3)
        row1 = stable_row(lab1, slot1, buff=0.4)
        lab2 = t("HumanEval", 40, WHITE, "BOLD")
        slot2 = dynamic_slot(2.6, 1.3)
        row2 = stable_row(lab2, slot2, buff=0.4)
        page2 = page_stack(card2, row1, row2, buff=1.5)
        layout_page(page2)

        self.at_clip("S4-c05")
        self.play(FadeOut(head), FadeOut(page1), FadeOut(cross),
                  type_in(head2, run_time=0.8), run_time=0.8)
        self.play_scroll_unroll(card2, run_time=1.0)
        self.at_clip("S4-c06")
        n1 = self.counter_value(39.0, 41.4, decimals=1, size=80, color=YELL,
                                run_time=1.2, anchor=slot1,
                                extra_anims=[type_in(lab1, run_time=0.6)])  # 主视觉：数字滚动
        self.at_clip("S4-c07")
        n2 = self.counter_value(20.7, 26.8, decimals=1, size=80, color=YELL,
                                run_time=1.2, anchor=slot2,
                                extra_anims=[type_in(lab2, run_time=0.6)])  # 主视觉：数字滚动

        # 页3：白赚总结
        head3 = _head("推理时：成本为零", 38)
        line3 = t("直接丢弃 MTP 模块", 34, WHITE)
        concl = t("训练时白赚信号，推理时白赚速度", 44, YELL, "BOLD")
        page3 = page_auto(line3, concl)

        self.play(FadeOut(head2), FadeOut(page2), FadeOut(n1), FadeOut(n2),
                  type_in(head3, run_time=0.8), run_time=0.8)
        self.at_clip("S4-c08")
        self.play(type_in(line3, run_time=0.8))
        self.at_clip("S4-c09")
        self.play(type_in(concl, run_time=0.9))
        self.at_clip("S4-c10")
        self.emphasize(concl, run_time=0.5)  # 4/5
        self.transition_out(head3, f, line3, concl)
        self.pad_to_voice()


# ---------------- S5 同题不同解：GLM-5.2 的激进版 ----------------
class S5(_Base):
    def construct(self):
        self.bg()
        f = _footer(self)

        # 页1：保守 vs 激进
        head = _head("同题不同解", 38)
        line = t("另一家国产模型走了完全不同的路线", 30, WHITE)
        card1 = _card("DeepSeek：保守，depth=1，只多猜一个词", 6.6, 2.2, CYAN, WHITE, 32, CARD_FILL, "BOLD")
        card2 = _card("GLM-5.2：激进，一次猜 5 个草稿", 6.6, 2.2, GREEN, WHITE, 32, CARD_FILL, "BOLD")
        page1 = page_stack(line, card1, card2, buff=1.2)
        layout_page(page1)

        self.at_clip("S5-c01")
        self.play(type_in(head, run_time=0.9), type_in(line, run_time=0.8), run_time=0.9)
        self.at_clip("S5-c02")
        self.play_scroll_unroll(card1, run_time=1.0)  # 主视觉：拉幕
        self.at_clip("S5-c03")
        self.at_clip("S5-c04")
        self.play_scroll_unroll(card2, run_time=1.0)

        # 页2：训练-推理不一致
        head2 = _head("多步草稿的大坑", 38)
        c1 = _card("训练时：第 2 步起用真实词", 6.6, 2.2, GREEN, WHITE, 32, CARD_FILL, "BOLD")
        c2 = _card("推理时：用侧头自己猜的词", 6.6, 2.2, RED, WHITE, 32, CARD_FILL, "BOLD")
        line2 = t("模型从没见过这种输入分布", 30, WHITE)
        page2 = page_stack(c1, c2, line2, buff=1.2)
        layout_page(page2)

        self.play(FadeOut(head), FadeOut(page1), type_in(head2, run_time=0.8), run_time=0.8)
        self.at_clip("S5-c05")
        self.play_scroll_unroll(c1, run_time=1.0)  # 主视觉：拉幕
        self.at_clip("S5-c06")
        self.play_scroll_unroll(c2, run_time=1.0)
        self.wait(0.1)
        cross2 = self.play_red_cross(c2, run_time=0.6)
        self.wait(0.1)
        self.play(type_in(line2, run_time=0.8))

        # 页3：IndexShare 解法
        head3 = _head("GLM-5.2 的解法：IndexShare", 36)
        step1 = _card("第一步：跑索引", 5.6, 1.8, CYAN, WHITE, 32, CARD_FILL, "BOLD")
        step2 = _card("后续：复用 top-k 索引和 KV", 5.6, 1.8, GREEN, WHITE, 32, CARD_FILL, "BOLD")
        step3 = _card("条件分布终于一致", 5.6, 1.8, YELL, WHITE, 32, CARD_FILL, "BOLD")
        step2.next_to(step1, DOWN, buff=0.9)
        step3.next_to(step2, DOWN, buff=0.9)
        b1 = Arrow(step1.get_bottom(), step2.get_top(), color=MUTED, buff=0.1, stroke_width=4)
        b2 = Arrow(step2.get_bottom(), step3.get_top(), color=MUTED, buff=0.1, stroke_width=4)
        diagram = VGroup(step1, step2, step3, b1, b2)
        page3 = page_stack(diagram, buff=1.0)
        layout_page(page3)

        self.play(FadeOut(head2), FadeOut(page2), FadeOut(cross2),
                  type_in(head3, run_time=0.8), run_time=0.8)
        self.at_clip("S5-c07")
        self.play_scroll_unroll(step1, run_time=1.0)  # 主视觉：拉幕
        self.at_clip("S5-c08")
        self.play(Create(b1), run_time=0.5)
        self.wait(0.1)
        self.play_scroll_unroll(step2, run_time=1.0)
        self.at_clip("S5-c09")
        self.play(Create(b2), run_time=0.4)
        self.wait(0.1)
        self.play_scroll_unroll(step3, run_time=1.0)

        # 页4：接受长度 +20%
        head4 = _head("接受长度", 38)
        card4 = _card("GLM-5.2 草稿接受长度", 6.4, 2.0, CYAN, WHITE, 34, CARD_FILL, "BOLD")
        slot = dynamic_slot(2.6, 1.4)
        badge = t("+20%", 52, GREEN, "BOLD")
        page4 = page_stack(card4, slot, badge, buff=1.6)
        layout_page(page4)

        self.at_clip("S5-c10")
        self.play(FadeOut(head3), FadeOut(page3), type_in(head4, run_time=0.8), run_time=0.8)
        self.play_scroll_unroll(card4, run_time=1.0)
        self.wait(0.1)
        n = self.counter_value(4.56, 5.47, decimals=2, size=88, color=YELL,
                               run_time=1.2, anchor=slot,
                               extra_anims=[type_in(badge, run_time=0.6)])  # 主视觉：数字滚动
        self.transition_out(head4, f, card4, n, badge)
        self.pad_to_voice()


# ---------------- S6 接受率账 + 结尾预告 + 互动 + 尾卡 ----------------
class S6(_Base):
    def construct(self):
        self.bg()
        f = _footer(self)

        # 页1：三档接受率对比条
        head = _head("接受率 p 决定加速比", 38)
        cols = VGroup()
        for lab, h, col, val in [("p = 0.85", 4.6, GREEN, "1.8×"),
                                 ("p = 0.5", 3.6, YELL, "1.4×"),
                                 ("p ≈ 0", 2.6, RED, "1.0×")]:
            b = Rectangle(width=1.6, height=h, color=col, fill_color=col, fill_opacity=0.6)
            l = t(lab, 28, WHITE, "BOLD")
            v = t(val, 34, col, "BOLD")
            cols.add(VGroup(l, b, v).arrange(DOWN, buff=0.25))
        cols.arrange(RIGHT, buff=0.7)
        line = t("白算，还倒贴草稿成本", 30, WHITE)
        page1 = page_stack(cols, line, buff=1.2)
        layout_page(page1)

        self.at_clip("S6-c01")
        self.play(type_in(head, run_time=0.9))
        self.at_clip("S6-c02")
        self.play(GrowFromEdge(cols[0][1], DOWN), type_in(cols[0][0], 0.5),
                  type_in(cols[0][2], 0.5), run_time=1.0)  # 主视觉：柱生长
        self.at_clip("S6-c03")
        self.at_clip("S6-c04")
        self.play(GrowFromEdge(cols[1][1], DOWN), type_in(cols[1][0], 0.5),
                  type_in(cols[1][2], 0.5), run_time=1.0)
        self.at_clip("S6-c05")
        self.play(GrowFromEdge(cols[2][1], DOWN), type_in(cols[2][0], 0.5),
                  type_in(cols[2][2], 0.5), type_in(line, run_time=0.7), run_time=1.0)

        # 页2：总结句
        head2 = _head("投机解码的全部秘密", 38)
        line1 = t("草稿猜得越准，加速越猛", 44, YELL, "BOLD")
        line2 = t("猜不准，就是负优化", 44, WHITE, "BOLD")
        page2 = page_auto(line1, line2)

        self.play(FadeOut(head), FadeOut(page1), type_in(head2, run_time=0.8), run_time=0.8)
        self.at_clip("S6-c06")
        self.play(type_in(line1, run_time=0.9))
        self.at_clip("S6-c07")
        self.at_clip("S6-c08")
        self.play(type_in(line2, run_time=0.8))
        self.emphasize(line2, run_time=0.5)  # 5/5

        # 页3：下一篇预告 + 互动
        head3 = _head("下一篇", 38)
        l1 = t("单卡再快也有极限", 30, WHITE)
        l2a = t("V4 这种 1.6T 参数的模型，", 30, WHITE)
        l2b = t("一块 GPU 连装都装不下", 30, WHITE)
        l2 = VGroup(l2a, l2b).arrange(DOWN, buff=0.15)
        q = t("1000 块 GPU 怎么分活？", 44, YELL, "BOLD")
        qa = t("一个问题留给你：猜几个词最划算？", 32, WHITE)
        cm = t("评论区聊聊", 36, GREEN, "BOLD")
        page3 = page_stack(l1, l2, q, qa, cm, buff=1.2)
        layout_page(page3)

        self.play(FadeOut(head2), FadeOut(page2), type_in(head3, run_time=0.8), run_time=0.8)
        self.at_clip("S6-c09")
        self.play(type_in(l1, run_time=0.7))
        self.at_clip("S6-c10")
        self.play(type_in(l2, run_time=0.8), type_in(q, run_time=0.8), run_time=0.9)
        self.at_clip("S6-c11")
        self.play(type_in(qa, run_time=0.8))
        self.at_clip("S6-c12")
        self.play(type_in(cm, run_time=0.7))

        # 页4：品牌尾卡（终幕驻屏，不 transition_out）
        avatar = ImageMobject(str(AVATAR))
        avatar.scale_to_fit_width(3.6)
        follow = t("关注「数解AI」", 44, YELL, "BOLD")
        title = t("《多Token预测：一次猜两个词，快1.8倍》", 28, WHITE, "BOLD")
        guide = t("查看公众号文章", 32, GREEN, "BOLD")
        page4 = page_stack(avatar, follow, title, guide, buff=0.7)
        layout_page(page4)

        self.at_clip("S6-c13")
        self.play(FadeOut(head3), FadeOut(page3), FadeIn(avatar, shift=DOWN * 0.05), run_time=0.8)  # 主视觉：品牌图
        self.play(type_in(follow, run_time=0.7), type_in(title, run_time=0.7),
                  type_in(guide, run_time=0.6), run_time=0.8)
        self.pad_to_voice()
