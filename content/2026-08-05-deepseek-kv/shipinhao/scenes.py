#!/usr/bin/env python3
"""《K=V：一份KV缓存怎么干两份活？》视频号 Manim 动画（竖屏 1080×1920）

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

# 每段配音时长（tts_split.py 实测 2026-08-26 重配音去段首 breath），渲染时长 = 配音 + TAIL
VOICE_DUR = {"S1": 20.8, "S2": 24.65, "S3": 31.0, "S4": 37.81, "S5": 31.24, "S6": 56.01}
TAIL = 2.5


def _footer(self) -> Text:
    f = t("数解AI · 大模型原理", 20, MUTED).to_edge(DOWN, buff=1.15)
    self.add(f)
    return f


# ---------------- S1 开场钩子：K 是索引，V 是正文 ----------------
class S1(_Base):
    def construct(self):
        self.bg()
        f = _footer(self)

        # 页1：概念图 + K/V 分工
        head = t("K 是索引，V 是正文", 38, YELL, "BOLD").to_edge(UP, buff=1.2)
        note0 = t("以 DeepSeek-V4 为例", 24, MUTED).next_to(head, DOWN, buff=0.5)
        img = ImageMobject(str(IMG / "s1-index-card-round.png"))
        img.scale_to_fit_width(5.5)
        line1 = t("K：负责匹配，必须知道位置", 34, CYAN, "BOLD")
        line2 = t("V：负责取出，内容必须干净", 34, GREEN, "BOLD")
        labels = VGroup(line1, line2).arrange(DOWN, buff=0.4)
        page1 = page_stack(img, labels, buff=0.7)
        layout_page(page1)

        self.at_clip("S1-c01")
        self.play_parallel(type_in(head, run_time=1.1), FadeIn(note0, shift=DOWN * 0.05),
                           FadeIn(img, shift=DOWN * 0.05), run_time=1.1)
        self.at_clip("S1-c02")
        self.play_parallel(type_in(line1, run_time=0.9), type_in(line2, run_time=0.9),
                           run_time=0.9)
        self.at_clip("S1-c03")
        self.play(FadeOut(head), FadeOut(note0), FadeOut(page1), run_time=0.5)

        # 页2：K=V 反直觉（矮页）
        card = _card("同一个向量，又当 K 又当 V", 6.4, 1.8, YELL, WHITE, 40, CARD_FILL, "BOLD")
        q = t("这不串味吗？", 60, YELL, "BOLD")
        ans = t("答案，藏在两个机制里", 30, MUTED)
        page_auto(card, q, ans)

        self.at_clip("S1-c04")
        self.play_scroll_unroll(card, run_time=1.2)
        self.at_clip("S1-c05")
        self.play(type_in(q, run_time=0.9))
        self.at_clip("S1-c06")
        self.play(type_in(ans, run_time=0.8))
        self.wait(0.4)
        self.transition_out(f, card, q, ans)
        self.pad_to_voice()


# ---------------- S2 双流重叠压缩：一份 entry 诞生 ----------------
class S2(_Base):
    def construct(self):
        self.bg()
        f = _footer(self)

        # 页1：双流结构图（4 token → 1 entry）
        head = t("双流重叠压缩", 38, YELL, "BOLD").to_edge(UP, buff=1.2)
        a_lab = t("a 流：当前块", 32, CYAN, "BOLD")
        b_lab = t("b 流：前一块", 32, GREEN, "BOLD")
        tokens = VGroup(*[boxed("token", 1.4, 1.1, CYAN, 24) for _ in range(4)])
        tokens.arrange_in_grid(2, 2, buff=0.3)
        tokens_grp = VGroup(a_lab, tokens, b_lab).arrange(DOWN, buff=0.35)
        entry = boxed("entry", 2.0, 1.5, YELL, 32, weight="BOLD")
        VGroup(tokens_grp, entry).arrange(RIGHT, buff=2.0)  # 先定位置再画箭头
        arrow = Arrow(tokens.get_right(), entry.get_left(), color=YELL,
                      buff=0.2, stroke_width=6)
        flow = VGroup(tokens_grp, arrow, entry)
        cap = t("每 4 个 token 合成 1 个 entry", 30, WHITE)
        note = t("相邻摘要共享范围，有效压缩比仍是 m", 26, MUTED)
        page1 = page_stack(flow, cap, note, buff=1.2)
        layout_page(page1)

        self.at_clip("S2-c01")
        self.play_parallel(type_in(head, run_time=1.1), type_in(a_lab, run_time=0.5),
                           run_time=1.1)
        self.at_clip("S2-c02")
        self.play_parallel(type_in(b_lab, run_time=0.5),
                           *[Create(tk) for tk in tokens], run_time=1.2, lag_ratio=0.3)  # 主视觉
        self.at_clip("S2-c03")
        self.play(Create(arrow), run_time=0.5)

        # 页2：关键一步 K=V + 冲突
        head2 = t("关键一步：K=V", 38, YELL, "BOLD").to_edge(UP, buff=1.2)
        card1 = _card("压缩后的 entry，不再拆成 K 和 V", 6.6, 1.7, YELL, WHITE, 38, CARD_FILL, "BOLD")
        entry_box = boxed("entry", 2.2, 1.2, CYAN, 30, weight="BOLD")
        k_lab = t("K", 44, YELL, "BOLD")
        v_lab = t("V", 44, GREEN, "BOLD")
        VGroup(k_lab, entry_box, v_lab).arrange(RIGHT, buff=1.6)  # 定位置
        k_ar = Arrow(k_lab.get_right(), entry_box.get_left(), color=YELL,
                     buff=0.15, stroke_width=5)
        v_ar = Arrow(entry_box.get_right(), v_lab.get_left(), color=GREEN,
                     buff=0.15, stroke_width=5)
        kv_row = VGroup(k_lab, k_ar, entry_box, v_ar, v_lab)
        card2 = _card("同一个向量：既要被匹配，又要被取出", 6.6, 1.7, RED, WHITE, 36, CARD_FILL)
        q = t("怎么破？按维度分工", 44, YELL, "BOLD")
        page2 = page_stack(card1, kv_row, card2, q, buff=0.8)
        layout_page(page2)

        self.at_clip("S2-c04")
        self.play(FadeOut(head), FadeOut(page1), type_in(head2), run_time=0.8)
        self.play_scroll_unroll_many(entry_box, card1, run_time=1.2)
        self.at_clip("S2-c05")
        self.play_parallel(type_in(k_lab, run_time=0.5), Create(k_ar),
                           type_in(v_lab, run_time=0.5), Create(v_ar), run_time=0.6)
        self.at_clip("S2-c06")
        self.play_scroll_unroll(card2, run_time=1.2)
        self.at_clip("S2-c07")
        self.play(type_in(q, run_time=0.8))
        self.wait(0.5)
        self.transition_out(head2, f, card1, kv_row, card2, q)
        self.pad_to_voice()


# ---------------- S3 Partial RoPE：只转最后 64 维 ----------------
class S3(_Base):
    def construct(self):
        self.bg()
        f = _footer(self)

        # 页1：512 维向量条（448 内容 + 64 位置）
        head = t("Partial RoPE：只转最后 64 维", 36, YELL, "BOLD").to_edge(UP, buff=1.2)
        total_lab = t("512 维", 40, WHITE, "BOLD")
        content_bar = Rectangle(width=5.2, height=3.0, color=CYAN,
                                fill_color=CYAN, fill_opacity=0.7)
        pos_bar = Rectangle(width=1.2, height=3.0, color=YELL,
                           fill_color=YELL, fill_opacity=0.7)
        bars = VGroup(content_bar, pos_bar).arrange(RIGHT, buff=0.15)
        lab1 = t("448 维：我是什么内容", 32, CYAN, "BOLD")
        lab2 = t("64 维：我在哪个位置", 32, YELL, "BOLD")
        labs = VGroup(lab1, lab2).arrange(RIGHT, buff=1.2)
        concl = t("位置和内容，在维度上物理分离", 30, MUTED)
        page1 = page_stack(total_lab, bars, labs, concl, buff=0.95)
        layout_page(page1)

        self.at_clip("S3-c01")
        self.play_parallel(type_in(head, run_time=1.1), type_in(total_lab, run_time=0.6),
                           run_time=1.1)
        self.at_clip("S3-c02")
        self.grow_bar(content_bar, ValueTracker(0), 5.2, run_time=1.0, anchor="center")  # 主视觉
        self.at_clip("S3-c03")
        self.grow_bar(pos_bar, ValueTracker(0), 1.2, run_time=0.8, anchor="center")
        self.play_parallel(type_in(lab1, run_time=0.8), type_in(lab2, run_time=0.8),
                           type_in(concl, run_time=0.8), run_time=0.8)

        # 页2：混合存储（BF16/FP8，体积近乎减半）
        head2 = t("混合存储", 36, YELL, "BOLD").to_edge(UP, buff=1.2)
        c1 = _card("64 维 BF16", 3.0, 1.8, YELL, WHITE, 40, CARD_FILL, "BOLD")
        c2 = _card("448 维 FP8", 3.0, 1.8, CYAN, WHITE, 40, CARD_FILL, "BOLD")
        cards = VGroup(c1, c2).arrange(RIGHT, buff=0.8)
        num_lab = t("缓存体积", 36, WHITE, "BOLD")
        slot = dynamic_slot(2.2, 0.9)
        num_row = stable_row(num_lab, slot, buff=0.4)
        note = t("只有 64 维需要精确位置，KV 混合存储", 28, MUTED)
        page_auto(cards, num_row, note)

        self.at_clip("S3-c04")
        self.play(FadeOut(head), FadeOut(page1), type_in(head2), run_time=0.8)
        self.play_scroll_unroll_many(c1, c2, run_time=1.2)
        self.at_clip("S3-c05")
        cnt = self.counter_value(100, 50, suffix="%", size=52, color=YELL, anchor=slot,
                                 run_time=0.9, extra_anims=[type_in(num_lab, run_time=0.6)])  # 主视觉
        self.at_clip("S3-c06")
        self.play(FadeOut(head2), FadeOut(VGroup(cards, num_row, note)), FadeOut(cnt),
                  run_time=0.5)

        # 页3：悬念问句（矮页）
        card = _card("带着旋转被加权求和", 6.4, 1.8, YELL, WHITE, 40, CARD_FILL, "BOLD")
        q = t("位置不就渗进输出了吗？", 52, YELL, "BOLD")
        page_auto(card, q)

        self.play_scroll_unroll(card, run_time=1.2)
        self.at_clip("S3-c07")
        self.play(type_in(q, run_time=0.9))
        self.wait(0.9)
        self.transition_out(f, card, q)
        self.pad_to_voice()


# ---------------- S4 de-RoPE：输出端解旋 ----------------
class S4(_Base):
    def construct(self):
        self.bg()
        f = _footer(self)

        # 页1：问题（带旋转的 V 加权求和 → 坐标漂移）
        head = t("de-RoPE：输出端解旋", 36, YELL, "BOLD").to_edge(UP, buff=1.2)
        img = ImageMobject(str(IMG / "s4-derope-gear-round.png"))
        img.scale_to_fit_width(4.8)
        lab1 = t("第 3 块的旋转 vs 第 300 块的旋转", 32, WHITE)
        lab2 = t("同一内容换个位置，坐标就漂了", 34, RED, "BOLD")
        page1 = page_stack(img, lab1, lab2, buff=0.75)
        layout_page(page1)

        self.at_clip("S4-c01")
        self.play_parallel(type_in(head, run_time=1.1), FadeIn(img, shift=DOWN * 0.05),
                           run_time=1.1)
        self.at_clip("S4-c02")
        self.play(type_in(lab1, run_time=0.9))
        self.at_clip("S4-c03")
        self.play(type_in(lab2, run_time=0.9))
        self.at_clip("S4-c04")
        self.emphasize(lab2, run_time=0.6)  # 1/5

        # 页2：解法（反向旋转，R₋ᵢRⱼ = Rⱼ₋ᵢ）
        head2 = t("反向旋转一次", 36, YELL, "BOLD").to_edge(UP, buff=1.2)
        f1 = sup("R", "-i", 64, 32, YELL)
        f2 = sup("R", "j", 64, 32, YELL)
        eq = t("=", 64, WHITE, "BOLD")
        f3 = sup("R", "j-i", 64, 32, YELL)
        formula = VGroup(f1, f2, eq, f3).arrange(RIGHT, buff=0.5)
        card = _card("角度可以相加：负 i 乘 j，等于 j 减 i", 6.4, 1.8, CYAN, WHITE, 36, CARD_FILL)
        lab = t("绝对位置消掉，只剩相对距离", 38, GREEN, "BOLD")
        page2 = page_stack(formula, card, lab, buff=1.8)
        layout_page(page2)

        self.at_clip("S4-c05")
        self.play(FadeOut(head), FadeOut(page1), type_in(head2), FadeIn(formula, scale=1.05),
                  run_time=0.8)  # 公式用 FadeIn 合规
        self.at_clip("S4-c06")
        self.play_scroll_unroll(card, run_time=1.2)
        self.at_clip("S4-c07")
        self.play(type_in(lab, run_time=0.9))
        self.emphasize(lab, run_time=0.6)  # 2/5
        self.at_clip("S4-c08")
        self.play(FadeOut(head2), FadeOut(page2), run_time=0.5)

        # 页3：爆点（de 是 undo，不是 delete）+ 悬念（矮页）
        card3 = _card("de-RoPE 不是去掉位置，是解旋", 6.8, 1.9, YELL, WHITE, 42, CARD_FILL, "BOLD")
        sub_lab = t("de 是 undo，不是 delete", 34, WHITE)
        q = t("这套设计，真的经得起验证吗？", 30, MUTED)
        page_auto(card3, sub_lab, q)

        self.play_scroll_unroll(card3, run_time=1.2)
        self.at_clip("S4-c09")
        self.play_parallel(type_in(sub_lab, run_time=0.8), type_in(q, run_time=0.8),
                           run_time=0.8)
        self.wait(2.8)
        self.transition_out(f, card3, sub_lab, q)
        self.pad_to_voice()


# ---------------- S5 机制验证 + Kimi K3 对照 ----------------
class S5(_Base):
    def construct(self):
        self.bg()
        f = _footer(self)

        # 页1：实验三行卡
        head = t("机制验证：NumPy 实验", 36, YELL, "BOLD").to_edge(UP, buff=1.2)
        c1 = _card("K=V 路径成立", 6.6, 1.7, GREEN, WHITE, 38, CARD_FILL, "BOLD")
        c2 = _card("QK 内积只依赖相对距离", 6.6, 1.7, CYAN, WHITE, 38, CARD_FILL, "BOLD")
        c3 = _card("绝对位置 5,8 → 105,108，内积一模一样", 6.6, 1.7, WHITE, WHITE, 36, CARD_FILL)
        page1 = page_stack(c1, c2, c3, buff=1.0)
        layout_page(page1)

        self.at_clip("S5-c01")
        self.play(type_in(head, run_time=1.1))
        self.wait(0.2)
        self.play_scroll_unroll(c1, run_time=1.0)
        self.at_clip("S5-c02")
        self.play_scroll_unroll(c2, run_time=1.0)
        self.at_clip("S5-c03")
        self.play_scroll_unroll(c3, run_time=1.0)

        # 页2：数字对比（0.28 → 1e-16）
        head2 = t("de-RoPE 还原了吗？", 36, YELL, "BOLD").to_edge(UP, buff=1.2)
        rect1 = Rectangle(width=4.6, height=1.7, color=RED, stroke_width=2.5,
                          fill_color=RED, fill_opacity=0.15)
        b1_lab = t("无 de-RoPE：漂移", 30, WHITE, "BOLD")
        slot1 = dynamic_slot(1.8, 0.8)
        row1 = stable_row(b1_lab, slot1, buff=0.3).move_to(rect1.get_center())
        block1 = VGroup(rect1, row1)
        rect2 = Rectangle(width=4.6, height=1.7, color=GREEN, stroke_width=2.5,
                          fill_color=GREEN, fill_opacity=0.15)
        b2_lab = t("有 de-RoPE：漂移", 30, WHITE, "BOLD")
        slot2 = dynamic_slot(1.8, 0.8)
        row2 = stable_row(b2_lab, slot2, buff=0.3).move_to(rect2.get_center())
        block2 = VGroup(rect2, row2)
        blocks = VGroup(block1, block2).arrange(DOWN, buff=0.8)
        page_auto(blocks)

        self.at_clip("S5-c04")
        self.play(FadeOut(head), FadeOut(page1), type_in(head2), run_time=0.8)
        self.play(FadeIn(rect1, shift=DOWN * 0.05), type_in(b1_lab, run_time=0.5),
                  run_time=0.6)
        cnt1 = self.counter_value(0, 0.28, decimals=2, size=44, color=RED, anchor=slot1,
                                  run_time=0.8)  # 主视觉
        self.at_clip("S5-c05")
        self.play(FadeIn(rect2, shift=DOWN * 0.05), type_in(b2_lab, run_time=0.5),
                  run_time=0.6)
        n16 = t("1e-16", 44, GREEN, "BOLD").move_to(slot2.get_center())
        self.play(type_in(n16, run_time=0.4))
        self.emphasize(n16, run_time=0.5)  # 3/5

        # 页3：Kimi K3 完全不旋转
        head3 = t("另一条路：完全不旋转", 36, YELL, "BOLD").to_edge(UP, buff=1.2)
        card = _card("Kimi K3：注意力干脆完全不旋转", 6.8, 1.9, YELL, WHITE, 40, CARD_FILL, "BOLD")
        code = boxed("rotary_emb = None", 5.0, 1.4, GREEN, 34, weight="BOLD")
        q = t("这笔账，到底省了多少？", 30, MUTED)
        page3 = page_stack(card, code, q, buff=1.7)
        layout_page(page3)

        self.at_clip("S5-c06")
        self.play(FadeOut(head2), FadeOut(blocks), FadeOut(cnt1), FadeOut(n16),
                  type_in(head3), run_time=0.8)
        self.play_scroll_unroll(card, run_time=1.2)
        self.at_clip("S5-c07")
        self.play_scroll_unroll(code, run_time=1.0)
        self.at_clip("S5-c08")
        self.play(type_in(q, run_time=0.8))
        self.wait(0.2)
        self.transition_out(head3, f, card, code, q)
        self.pad_to_voice()


# ---------------- S6 效率收口 + 回扣 + 品牌尾卡 ----------------
class S6(_Base):
    def construct(self):
        self.bg()
        f = _footer(self)

        # 页1：三根对比条（27% / 10% / 2%）
        head = t("效率收口：1M 上下文", 36, YELL, "BOLD").to_edge(UP, buff=1.2)
        r1_lab = t("推理 FLOPs", 32, WHITE, "BOLD")
        bar1 = Rectangle(width=1.73, height=1.1, color=CYAN, fill_color=CYAN, fill_opacity=0.7)
        slot1 = dynamic_slot(1.6, 0.8)
        row1 = stable_row(r1_lab, bar1, slot1, buff=0.5)
        r2_lab = t("KV 缓存", 32, WHITE, "BOLD")
        bar2 = Rectangle(width=0.64, height=1.1, color=GREEN, fill_color=GREEN, fill_opacity=0.7)
        slot2 = dynamic_slot(1.6, 0.8)
        row2 = stable_row(r2_lab, bar2, slot2, buff=0.5)
        r3_lab = t("BF16 基线", 32, WHITE, "BOLD")
        bar3 = Rectangle(width=0.13, height=1.1, color=YELL, fill_color=YELL, fill_opacity=0.7)
        slot3 = dynamic_slot(1.6, 0.8)
        row3 = stable_row(r3_lab, bar3, slot3, buff=0.5)
        note = t("对比 DeepSeek-V3.2 · 官方口径", 28, MUTED)
        page1 = page_stack(row1, row2, row3, note, buff=1.1)
        layout_page(page1)

        self.at_clip("S6-c01")
        self.play_parallel(type_in(head, run_time=1.1), type_in(r1_lab, run_time=0.6),
                           run_time=1.1)
        self.at_clip("S6-c02")
        self.grow_bar(bar1, ValueTracker(0), 1.73, run_time=1.0, anchor="center")  # 主视觉
        self.wait(0.1)
        cnt1 = self.counter_value(0, 27, suffix="%", size=44, color=CYAN, anchor=slot1, run_time=0.9)
        self.at_clip("S6-c03")
        self.grow_bar(bar2, ValueTracker(0), 0.64, run_time=1.0, anchor="center",
                      extra_anims=[type_in(r2_lab, run_time=0.6)])
        self.wait(0.1)
        cnt2 = self.counter_value(0, 10, suffix="%", size=44, color=GREEN, anchor=slot2, run_time=0.9)
        self.wait(0.1)
        self.grow_bar(bar3, ValueTracker(0), 0.13, run_time=1.0, anchor="center",
                      extra_anims=[type_in(r3_lab, run_time=0.6)])
        self.wait(0.1)
        cnt3 = self.counter_value(0, 2, suffix="%", size=44, color=YELL, anchor=slot3, run_time=0.9,
                                  extra_anims=[type_in(note, run_time=0.8)])

        # 页2：四件事
        head2 = t("省在哪？四件事", 36, YELL, "BOLD").to_edge(UP, buff=1.2)
        cards = boxrow(["压缩", "K=V 单份缓存", "混合存储", "索引器 FP8"],
                       6.6, 1.4, [CYAN, YELL, GREEN, CYAN], fs=34)
        page2 = page_stack(cards, buff=0.8)
        layout_page(page2)

        self.at_clip("S6-c04")
        self.play(FadeOut(head), FadeOut(page1), FadeOut(cnt1), FadeOut(cnt2), FadeOut(cnt3),
                  type_in(head2), run_time=0.8)
        self.play_scroll_unroll_many(*cards, run_time=1.2)  # 主视觉

        # 页3：回扣（各归其位）
        head3 = t("K=V 为什么没串味？", 36, YELL, "BOLD").to_edge(UP, buff=1.2)
        c1 = _card("Partial RoPE：位置锁进最后 64 维", 6.8, 1.9, CYAN, WHITE, 36, CARD_FILL, "BOLD")
        c2 = _card("de-RoPE：绝对位置 → 相对距离", 6.8, 1.9, GREEN, WHITE, 36, CARD_FILL, "BOLD")
        concl = t("各用各的维度——更精细的分工", 44, YELL, "BOLD")
        page3 = page_stack(c1, c2, concl, buff=1.3)
        layout_page(page3)

        self.at_clip("S6-c05")
        self.play(FadeOut(head2), FadeOut(page2), type_in(head3), run_time=0.8)
        self.play_scroll_unroll(c1, run_time=1.0)
        self.at_clip("S6-c06")
        self.play_scroll_unroll(c2, run_time=1.0)
        self.at_clip("S6-c07")
        self.play(type_in(concl, run_time=0.9))
        self.emphasize(concl, run_time=0.6)  # 4/5
        self.at_clip("S6-c08")
        self.play(FadeOut(head3), FadeOut(page3), run_time=0.5)

        # 页4：品牌尾卡（终幕，不转场）
        avatar = ImageMobject(str(AVATAR))
        avatar.scale_to_fit_width(2.6)
        follow = t("关注「数解AI」", 40, YELL, "BOLD")
        title = t("《K=V：一份KV缓存怎么干两份活？》", 30, WHITE, "BOLD")
        if title.width > FW * 0.8:
            title.set_width(FW * 0.8)
        guide = t("查看公众号文章", 28, GREEN, "BOLD")
        next_lab = t("下一篇：mHC——60 层以上为什么「传话传没」", 24, MUTED)
        aq = t("你会把位置放在少数维度，还是干脆不旋转？\n评论区聊聊", 22, MUTED)
        page4 = page_stack(avatar, follow, title, guide, next_lab, aq, buff=0.5)
        layout_page(page4)

        self.at_clip("S6-c09")
        self.play_parallel(FadeIn(avatar, scale=1.5), type_in(follow, run_time=0.8),
                           type_in(title, run_time=0.9), run_time=0.9)
        self.at_clip("S6-c10")
        self.play_parallel(type_in(guide, run_time=0.7), type_in(next_lab, run_time=0.8),
                           run_time=0.8)
        self.at_clip("S6-c11")
        self.play(type_in(aq, run_time=0.9))
        self.pad_to_voice()
