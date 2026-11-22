#!/usr/bin/env python3
"""《国产大模型真是用禁运的GB300训练的吗？》视频号 Manim 动画（竖屏 1080×1920）

6 个场景 S1-S6，与 storyboard.md 一一对应（权重指纹取证报告技术拆解·原理篇）。
- 配音：MiniMax 精英男声（speech-2.8-turbo，speed 1.0，pitch +2），实测总长 325.94s
- 时间轴：at_clip("S1-c01") 挂 tts/sentence-boundaries.json 的 clip 起点（先声音后动画门禁；
  段界经 ASR + silencedetect 逐段验证：4 处 MiniMax 跨段并句已按真实停顿重切，
  12 项头尾 ASR 全对、段内无 ≥1.5s 静音、中段数字 clip 抽验 3/3 对齐）
- 布局：整页规划（page_stack + layout_page，页高 ≥ 显示带 80%）/ 矮页自动排版（page_auto）
- 动画降噪（决策 #51）：v2 动效 1 处（S2 morph_to 递推链→并行通道）+ breathe 2 处；
  emphasize 5 次（S1 比标题谨慎得多 / S3 硬件指纹 / S4 最高读数 / S5 24 个全对 / S6 金句）；
  每页 1 个主视觉动效；死空档用 breathe 续命
- 数字台词全配动效：5,520 亿/1,960 亿 counter + SM 表逐行点亮 + 228 倍/0.066 双 counter +
  8σ/49σ/1385σ grow_bar + 六款 σ 表逐行 + 0.999996 counter
- 概念图 1 张（yairouter 深蓝系，无数字）：s1-blackwell-fingerprint（数据中心+指纹显卡）；
  机制图（递推链/并行通道/SM 表/摆放网格/σ 阶梯）全部脚本原生绘制
- 预检器约定：段内多拍合并为一拍多动画 play（count≥2）或 at_clip 边界锚定；不用裸 at()；
  连续单动画 reveal 之间插 self.wait 断开 serial_animation

用法（shipinhao 目录内执行）：
  MANIM_STRICT_TIMELINE=1 MANIM_STRICT_WIDTH=1 python3 -m manim render -ql --disable_caching scenes.py S1 .. S6
  MANIM_STRICT_TIMELINE=1 MANIM_STRICT_WIDTH=1 python3 -m manim render -qm --disable_caching scenes.py S1 .. S6
"""
from __future__ import annotations

import pathlib
import sys

import numpy as np


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

# 每段配音时长（fix_gb300_split.py 真实段界重切 + sentence-boundaries.json 实测），渲染时长 = 配音 + TAIL
VOICE_DUR = {"S1": 34.92, "S2": 50.88, "S3": 54.05, "S4": 47.1, "S5": 69.05, "S6": 69.94}
TAIL = 0.1


def _footer(self) -> Text:
    f = t("数解AI · 大模型后训练", 20, MUTED).to_edge(DOWN, buff=1.15)
    self.add(f)
    return f


def _head(text: str, size: float = 36) -> Text:
    return t(text, size, YELL, "BOLD")


def _img(name: str, width: float) -> ImageMobject:
    im = ImageMobject(str(IMG / name))
    im.scale_to_fit_width(width)
    return im


def _tout(self, *mobs, run_time: float = 0.4):
    """场景末转场：轻微下沉淡出（位移收窄到 0.35/0.25——helper 默认右滑 0.9 会把
    宽页内容推出画布，A5 全帧扫描记越界；GRPO/OPD 篇同款位移已为先例）。"""
    grp = Group(*mobs)
    self.play(grp.animate.shift(RIGHT * 0.35 + DOWN * 0.25).set_opacity(0),
              run_time=run_time, rate_func=smooth)
    self.remove(grp)


def _fade_row(self, row: VGroup, run_time: float = 0.4):
    self.play(*[FadeOut(m) for m in row], run_time=run_time)


def _chain_nodes(n: int = 4, r: float = 0.3, gap: float = 0.95) -> VGroup:
    """线性递推链节点：x0 x1 x2 …（一个个排队产出，morph 同构 4 节点）。"""
    nodes = []
    for i in range(n):
        c = Circle(radius=r, color=MUTED, stroke_width=2.5,
                   fill_color=CARD_FILL2, fill_opacity=1)
        lab = t(f"x{i}", 22, WHITE, "BOLD")
        lab.move_to(c.get_center())
        nodes.append(VGroup(c, lab))
    return VGroup(*nodes).arrange(RIGHT, buff=gap)


def _lane_nodes(k: int = 4, r: float = 0.3, gap: float = 0.72):
    """Philox 并行通道：seed 一点 → 每位置独立产出（返回 (整组, 输出列)）。"""
    outs = []
    for i in range(k):
        c = Circle(radius=r, color=CYAN, stroke_width=2.5,
                   fill_color=CARD_FILL2, fill_opacity=1)
        lab = t(f"n={i}", 17, WHITE)
        lab.move_to(c.get_center())
        outs.append(VGroup(c, lab))
    col = VGroup(*outs).arrange(DOWN, buff=gap)
    seed = Circle(radius=r * 1.35, color=YELL, stroke_width=2.5,
                  fill_color=CARD_FILL2, fill_opacity=1)
    slab = t("seed", 19, YELL, "BOLD")
    slab.move_to(seed.get_center())
    seed_g = VGroup(seed, slab)
    seed_g.next_to(col, LEFT, buff=1.45)
    arrows = [Arrow(seed_g.get_right() + RIGHT * 0.05 + UP * (i - (k - 1) / 2) * 0.3,
                    o.get_left() + LEFT * 0.05, color=CYAN, stroke_width=2.0,
                    buff=0.03, max_tip_length=0.15)
              for i, o in enumerate(outs)]
    return VGroup(seed_g, col, *arrows), col


def _sm_row(model: str, sm: str, hi: bool = False, dim: bool = False) -> VGroup:
    """SM 数表行：型号 + SM 数（高亮行黄色，dim 行置灰）。"""
    col = YELL if hi else (MUTED if dim else WHITE)
    a = t(model, 28, col, "BOLD" if hi else "NORMAL")
    b = t(sm, 34, YELL if hi else (MUTED if dim else CYAN), "BOLD")
    return VGroup(a, b).arrange(RIGHT, buff=0.55)


def _place_grid(cols: int = 10, rows: int = 5, cell: float = 0.58):
    """摆放网格示意：列 = 线程 t，行 = 轮次 q；返回 (网格组, 高亮格)。"""
    cells = []
    for r in range(rows):
        for c in range(cols):
            sq = Rectangle(width=cell * 0.82, height=cell * 0.82,
                           color=MUTED, stroke_width=1.2, stroke_opacity=0.55,
                           fill_color=CARD_FILL2, fill_opacity=0.9)
            cells.append(sq)
    grid = VGroup(*cells)
    grid.arrange_in_grid(rows=rows, cols=cols, buff=0.06)
    hi = Rectangle(width=cell * 0.82, height=cell * 0.82, color=YELL, stroke_width=2.5,
                   fill_color=YELL, fill_opacity=0.30)
    hi.move_to(cells[2 * cols + 4])
    return VGroup(grid, hi), hi


# ---------------- S1 开场钩子：禁运的卡，指纹是哪来的 ----------------
class S1(_Base):
    def construct(self):
        self.bg()
        f = _footer(self)

        # 页1：标题 + 概念图
        head = t("国产大模型真是用禁运的\nGB300训练的吗？", 40, YELL, "BOLD")
        sub = t("一份权重取证报告的技术拆解", 24, MUTED)
        img = _img("s1-blackwell-fingerprint-round.png", 3.1)
        img.set_opacity(0.92)
        page1 = page_stack(head, sub, img, buff=0.5)
        layout_page(page1)
        self.at_clip("S1-c01")
        self.play(type_in(head, run_time=1.0), FadeIn(sub, shift=DOWN * 0.05),
                  FadeIn(img, shift=DOWN * 0.1), run_time=1.0)
        self.wait(4.3333)                                         # -> 5.43

        # 页2：报告结论 + 四厂商
        self.at_clip("S1-c02")
        self.play(FadeOut(head), FadeOut(sub), FadeOut(img), run_time=0.45)
        head2 = _head("取证报告的结论", 34)
        c1 = boxed("六款国产开源模型的初始化权重，带着 Blackwell 指纹", 6.6, 2.2, YELL, 30, weight="BOLD")
        src = t("Will DePue · 只分析公开释出的模型权重", 22, MUTED)
        v1 = boxed("DeepSeek", 2.9, 0.95, CYAN, 26)
        v2 = boxed("月之暗面", 2.9, 0.95, CYAN, 26)
        v3 = boxed("MiniMax", 2.9, 0.95, CYAN, 26)
        v4 = boxed("蚂蚁集团", 2.9, 0.95, CYAN, 26)
        rowA = VGroup(v1, v2).arrange(RIGHT, buff=0.35)
        rowB = VGroup(v3, v4).arrange(RIGHT, buff=0.35)
        vendors = VGroup(rowA, rowB).arrange(DOWN, buff=0.32)
        page2 = page_stack(head2, c1, src, vendors, buff=0.5)
        layout_page(page2)
        self.play(type_in(head2, run_time=0.6), FadeIn(c1, shift=UP * 0.08),
                  FadeIn(src, shift=UP * 0.05), run_time=0.8)
        self.wait(3.8000)                                         # -> 13.05
        self.at_clip("S1-c03")
        self.play(FadeIn(rowA, shift=UP * 0.08), FadeIn(rowB, shift=UP * 0.08), run_time=0.7)
        self.wait(6.3000)                                         # -> 17.68

        # 页3：谜题双问
        self.at_clip("S1-c05")
        self.play(FadeOut(head2), FadeOut(c1), FadeOut(src), _fade_row(vendors), run_time=0.45)
        q1 = t("GB300 明令禁运，", 38, WHITE, "BOLD")
        q1b = t("这些指纹是哪来的？", 38, YELL, "BOLD")
        g1 = VGroup(q1, q1b).arrange(DOWN, buff=0.32)
        q2 = t("这些模型，", 38, WHITE, "BOLD")
        q2b = t("真是用禁运的卡训练的吗？", 38, YELL, "BOLD")
        g2 = VGroup(q2, q2b).arrange(DOWN, buff=0.32)
        mark = t("?", 110, RED, "BOLD")
        page3 = page_stack(g1, g2, mark, buff=0.62)
        layout_page(page3)
        self.play(type_in(q1, run_time=0.7), run_time=0.7)
        self.wait(7.4667)
        self.play(type_in(q1b, run_time=0.7), run_time=0.7)
        self.wait(0.1333)
        self.at_clip("S1-c08")
        self.play(type_in(q2, run_time=0.7), run_time=0.7)
        self.wait(1.9000)
        self.play(type_in(q2b, run_time=0.7), FadeIn(mark, shift=DOWN * 0.1), run_time=0.7)
        self.wait(0.1333)                                         # -> 30.79

        # 页4：预告
        self.at_clip("S1-c09")
        self.play(FadeOut(q1), FadeOut(q1b), FadeOut(q2), FadeOut(q2b), FadeOut(mark), run_time=0.45)
        line = t("能证明的东西，比标题谨慎得多", 38, WHITE, "BOLD")
        tip = t("先看指纹是怎么留下来的", 26, MUTED)
        tip2 = t("初始化 → 摆放 → 相关性 → 证据 → 结论", 24, MUTED)
        page4 = page_stack(line, tip, tip2, buff=1.05)
        layout_page(page4)
        self.play(type_in(line, run_time=0.9), run_time=0.9)
        self.wait(0.3)
        self.emphasize(line, mode="circumscribe", run_time=0.7)
        self.wait(2.53)
        _tout(self, line, tip, tip2, f, run_time=0.4)
        self.pad_to_voice()


# ---------------- S2 机制一：伪随机与 Philox ----------------
class S2(_Base):
    def construct(self):
        self.bg()
        f = _footer(self)

        # 页1：初始化需求 + 参数规模（c01-c05）
        head = _head("指纹从哪来？先从初始化说起", 34)
        l1 = t("训练大模型，第一件事", 30, WHITE)
        l2 = t("是给海量参数填随机数", 30, WHITE, "BOLD")
        labA = t("DeepSeek-V4.1-Flash 总参数", 26, WHITE)
        labB = t("外加 Engram 记忆", 26, WHITE)
        slotA = dynamic_slot(2.6, 1.0)
        slotB = dynamic_slot(2.6, 1.0)
        labA.next_to(slotA, UP, buff=0.26).align_to(slotA, LEFT)
        labB.next_to(slotB, UP, buff=0.26).align_to(slotB, LEFT)
        tail = t("一个数都躲不掉，全得排队出来", 26, MUTED)
        page1 = page_stack(head, VGroup(l1, l2).arrange(DOWN, buff=0.3),
                           VGroup(labA, slotA), VGroup(labB, slotB), tail, buff=0.45)
        layout_page(page1)
        self.at_clip("S2-c01")
        self.play(type_in(head, run_time=0.6), type_in(l1, run_time=0.6), run_time=0.7)
        self.wait(5.2000)
        self.play(type_in(l2, run_time=0.6), run_time=0.6)
        self.wait(1.2333)                                         # -> 7.87
        self.at_clip("S2-c03")
        n1 = self.counter_value(0, 5520, suffix=" 亿", size=58, run_time=1.2,
                                anchor=slotA, extra_anims=[type_in(labA, run_time=0.5)])
        self.wait(4.3333)                                         # -> 13.52
        self.at_clip("S2-c04")
        n2 = self.counter_value(0, 1960, suffix=" 亿", size=58, run_time=1.2,
                                anchor=slotB, extra_anims=[type_in(labB, run_time=0.5)])
        self.wait(2.9333)                                         # -> 17.75
        self.at_clip("S2-c05")
        self.play(FadeIn(tail, shift=UP * 0.06), run_time=0.5)
        self.wait(5.9667)                                         # -> 24.30

        # 页2：伪随机（c06-c08）
        self.at_clip("S2-c06")
        self.play(FadeOut(head), FadeOut(VGroup(l1, l2)), FadeOut(VGroup(labA, n1)),
                  FadeOut(VGroup(labB, n2)), FadeOut(tail), run_time=0.45)
        c1 = boxed("计算机不擅长产生真随机，用的都是伪随机", 6.6, 2.6, CYAN, 32)
        c2 = boxed("同一个 seed 加同一个位置，数值完全固定", 6.6, 2.3, CYAN, 30)
        why = t("科学计算需要稳定可复现", 26, MUTED)
        why2 = t("同样的输入和硬件，结果完全一样", 26, MUTED)
        page2 = page_stack(c1, c2, why, why2, buff=0.72)
        layout_page(page2)
        self.play(FadeIn(c1, shift=UP * 0.08), run_time=0.7)
        self.wait(2.8000)                                         # -> 28.38
        self.at_clip("S2-c07")
        self.play(FadeIn(c2, shift=UP * 0.08), FadeIn(why, shift=UP * 0.05), run_time=0.7)
        self.wait(2.8333)
        self.at_clip("S2-c08")
        self.play(FadeIn(why2, shift=UP * 0.05), run_time=0.5)
        self.wait(3.3667)                                         # -> 32.00

        # 页3：递推链 →（v2 morph）→ 并行通道（c09-c11）
        self.at_clip("S2-c09")
        self.play(FadeOut(c1), FadeOut(c2), FadeOut(why), FadeOut(why2), run_time=0.45)
        head3 = _head("传统递推太慢，Philox 换成并行", 32)
        rec = VGroup(sub("x", "n+1"), t(" = ", 26, WHITE), t("a·x", 26, WHITE), sub("x", "n"),
                     t(" + c  mod  m", 26, WHITE)).arrange(RIGHT, buff=0.12)
        slow = t("前一个出来，才算下一个", 24, MUTED)
        philox = VGroup(t("r", 30, WHITE), sub("r", "n"),
                        t(" = Mix(seed, n)", 30, YELL, "BOLD")).arrange(RIGHT, buff=0.1)
        tag2011 = t("2011 · Random123 论文", 22, MUTED)
        good1 = boxed("可跳转", 2.0, 0.85, GREEN, 24)
        good2 = boxed("天然并行", 2.0, 0.85, GREEN, 24)
        good3 = boxed("可复现", 2.0, 0.85, GREEN, 24)
        goods = VGroup(good1, good2, good3).arrange(RIGHT, buff=0.3)
        slotM = dynamic_slot(3.4, 2.9)   # morph 区占位（链→通道都在此）
        page3 = page_stack(head3, rec, slotM, slow, philox, tag2011, goods, buff=0.4)
        layout_page(page3)
        chain = _chain_nodes(4)
        chain.move_to(slotM.get_center())
        chain.align_to(slotM, DOWN)
        self.play(type_in(head3, run_time=0.5), type_in(rec, run_time=0.7),
                  FadeIn(chain, shift=RIGHT * 0.2), type_in(slow, run_time=0.5), run_time=0.8)
        self.wait(0.1333)                                         # -> 35.95

        # v2 morph：链 → 并行通道（目标在 layout 之后创建，同构 4 节点）
        fan, lanes = _lane_nodes(4)
        lanes.move_to(slotM.get_center())
        lanes.align_to(slotM, DOWN)
        seed_arrows = VGroup(fan[0], *fan[2:])
        seed_arrows.move_to(lanes.get_center())
        self.play(FadeOut(slow), ReplacementTransform(chain, lanes), run_time=1.0667)
        self.play(FadeIn(seed_arrows, shift=RIGHT * 0.15), run_time=0.5)
        self.play(type_in(philox, run_time=0.6), FadeIn(tag2011, shift=UP * 0.05), run_time=0.7)
        self.wait(2.7000)                                         # -> 42.44
        self.at_clip("S2-c10")
        self.play(FadeIn(goods, shift=UP * 0.1), run_time=0.7)
        self.breathe(lanes, loops=2, run_time=1.0)
        self.wait(2.140)
        _tout(self, head3, rec, lanes, seed_arrows, philox, tag2011, goods, f, run_time=0.4)
        self.pad_to_voice()


# ---------------- S3 机制二：SM 数就是指纹 ----------------
class S3(_Base):
    def construct(self):
        self.bg()
        f = _footer(self)

        # 页1：并行层级
        head = _head("随机数怎么摆，才是指纹的关键", 32)
        bars = VGroup(*[Rectangle(width=6.2 - 0.7 * i, height=0.85, color=MUTED,
                                  stroke_width=1.5, fill_color=CARD_FILL2, fill_opacity=0.9)
                        for i in range(4)])
        bars.arrange(DOWN, buff=0.42)
        labs = [t("整张显卡", 28, WHITE, "BOLD"), t("SM 流处理器", 28, CYAN, "BOLD"),
                t("Warp（32 线程）", 26, CYAN), t("线程", 26, MUTED)]
        for b, lb in zip(bars, labs):
            lb.move_to(b.get_center())
        lv = VGroup(bars, *labs)
        note = t("一个 SM 同时驻留很多 Warp，靠飞速切换掩盖等待", 24, MUTED)
        page1 = page_stack(head, lv, note, buff=0.5)
        layout_page(page1)
        self.at_clip("S3-c01")
        self.play(type_in(head, run_time=0.6), FadeIn(bars, shift=UP * 0.08), run_time=0.8)
        self.wait(1.8667)
        self.play(FadeIn(note, shift=UP * 0.05), run_time=0.5)
        self.wait(1.0333)                                           # -> 4.29

        # 页2：SM 表逐行点亮
        self.at_clip("S3-c02")
        self.play(FadeOut(head), FadeOut(lv), FadeOut(note), run_time=0.45)
        head2 = _head("不同型号，SM 数不一样", 32)
        r0 = _sm_row("A100 / A800", "108", dim=True)
        r1 = _sm_row("H100 / H800", "132")
        r2 = _sm_row("B200 / B300", "148")
        r3 = _sm_row("GB200 / GB300", "152", hi=True)
        rows = VGroup(r0, r1, r2, r3).arrange(DOWN, buff=1.05, aligned_edge=LEFT)
        rows.set_x(0)
        note2 = t("同一款硬件，SM 数是个固定整数", 32, MUTED)
        page2 = page_stack(head2, rows, note2, buff=0.8)
        layout_page(page2)
        self.play(type_in(head2, run_time=0.5), FadeIn(r0, shift=RIGHT * 0.15), run_time=0.6)
        self.wait(3.0667)
        self.play(FadeIn(r1, shift=RIGHT * 0.15), run_time=0.6)
        self.wait(0.4333)
        self.at_clip("S3-c03")
        self.play(FadeIn(r2, shift=RIGHT * 0.15), run_time=0.6)
        self.wait(3.8667)
        self.at_clip("S3-c04")
        self.play(FadeIn(r3, shift=RIGHT * 0.15), FadeIn(note2, shift=UP * 0.05), run_time=0.6)
        self.wait(0.1667)                                         # -> 14.10

        # 页3：G = 2048 × SM
        self.play(FadeOut(head2), FadeOut(rows), FadeOut(note2), run_time=0.45)
        head3 = _head("PyTorch 按每个 SM 2,048 个线程塞满整卡", 30)
        gform = t("G = 2,048 × SM 数", 44, YELL, "BOLD")
        gH = t("H100：G = 270,336", 30, MUTED)
        gA = t("B200：G = 303,104", 32, WHITE)
        gB = t("GB300：G = 311,296", 32, YELL, "BOLD")
        tip = t("整卡型号，最后压缩成 G 这一个整数", 26, MUTED)
        page3 = page_stack(head3, gform, gH, gA, gB, tip, buff=0.9)
        layout_page(page3)
        self.play(type_in(head3, run_time=0.6), type_in(gform, run_time=0.6), run_time=0.7667)
        self.wait(1.3000)
        self.play(FadeIn(gH, shift=UP * 0.05), run_time=0.5)
        self.wait(0.4333)
        self.play(FadeIn(gA, shift=UP * 0.05), run_time=0.5)
        self.wait(0.7333)
        self.at_clip("S3-c05")
        self.play(FadeIn(gB, shift=UP * 0.08), FadeIn(tip, shift=UP * 0.05), run_time=0.6)
        self.wait(3.3333)                                         # -> 23.74

        # 页4：摆放网格
        self.at_clip("S3-c06")
        self.play(FadeOut(head3), FadeOut(gform), FadeOut(gH), FadeOut(gA), FadeOut(gB),
                  FadeOut(tip), run_time=0.45)
        head4 = _head("第 i 个数，落在哪个格子", 32)
        tform = VGroup(t("t = i mod G", 30, CYAN, "BOLD"),
                       t("q = ⌊i / G⌋", 30, CYAN, "BOLD")).arrange(RIGHT, buff=0.5)
        grid, hi = _place_grid(10, 5, 0.62)
        xlab = t("线程 t →", 22, MUTED)
        ylab = t("轮次 q →", 22, MUTED)
        xlab.next_to(grid, UP, buff=0.16)
        ylab.next_to(grid, LEFT, buff=0.16).rotate(PI / 2)
        hit = t("第 i 个随机数", 22, YELL, "BOLD")
        hit.next_to(grid, DOWN, buff=0.3)
        cap = t("不同的卡 G 不同，同一个 i 落在不同的格子", 26, MUTED)
        page4 = page_stack(head4, tform, VGroup(grid, hi, xlab, ylab), hit, cap, buff=0.52)
        layout_page(page4)
        self.play(type_in(head4, run_time=0.5), type_in(tform, run_time=0.6), run_time=0.7)
        self.wait(2.8333)
        self.play(FadeIn(grid, shift=UP * 0.1), FadeIn(xlab), FadeIn(ylab), run_time=0.7)
        self.wait(2.3333)
        self.at_clip("S3-c08")
        self.play(FadeIn(hi), type_in(hit, run_time=0.5), run_time=0.6)
        self.wait(3.3000)                                         # -> 34.88

        # 页5：比对反推卡型（纵向流程）
        self.at_clip("S3-c09")
        self.play(FadeOut(head4), FadeOut(tform), FadeOut(VGroup(grid, hi, xlab, ylab)),
                  FadeOut(hit), FadeOut(cap), run_time=0.45)
        head5 = _head("对得上哪个 G，就是哪张卡", 32)
        s1 = boxed("发布权重 W", 5.6, 1.5, WHITE, 30)
        ar1 = Arrow(DOWN * 0.2, DOWN * 0.9, color=MUTED, stroke_width=2.2, buff=0.05)
        s2 = boxed("候选 (seed, G) 重新生成 W₀", 5.6, 1.5, CYAN, 28)
        ar2 = Arrow(DOWN * 0.2, DOWN * 0.9, color=MUTED, stroke_width=2.2, buff=0.05)
        s3 = boxed("相关性显著 → 锁定卡的型号", 5.6, 1.5, GREEN, 28)
        flow = VGroup(s1, ar1, s2, ar2, s3).arrange(DOWN, buff=0.5)
        note5 = t("比对前先跳过前 270,336 个公共位置", 24, MUTED)
        page5 = page_stack(head5, flow, note5, buff=0.6)
        layout_page(page5)
        self.play(type_in(head5, run_time=0.5), FadeIn(flow, shift=UP * 0.08), run_time=0.8)
        self.wait(5.1000)
        self.play(FadeIn(note5, shift=UP * 0.05), run_time=0.5)
        self.wait(0.6333)                                           # -> 42.47

        # 页6：硬件指纹 + 严谨性
        self.at_clip("S3-c11")
        self.play(FadeOut(head5), FadeOut(flow), FadeOut(note5), run_time=0.45)
        line = t("这就是硬件指纹", 52, YELL, "BOLD")
        c1 = boxed("GB200 与 GB300 共享 152，B200 与 B300 共享 148", 6.6, 2.1, MUTED, 28)
        c2 = boxed("读数只能精确到斜杠两边那一档", 6.6, 1.8, MUTED, 28)
        c3 = t("这套方法读到的是软件可见层", 28, MUTED)
        page6 = page_stack(line, c1, c2, c3, buff=0.75)
        layout_page(page6)
        self.play(type_in(line, run_time=0.7), run_time=0.7)
        self.wait(0.0333)
        self.emphasize(line, mode="circumscribe", run_time=0.4000)
        self.wait(0.0333)
        self.at_clip("S3-c12")
        self.play(FadeIn(c1, shift=UP * 0.08), run_time=0.6)
        self.wait(3.6333)
        self.at_clip("S3-c13")
        self.play(FadeIn(c2, shift=UP * 0.08), FadeIn(c3, shift=UP * 0.05), run_time=0.6)
        self.wait(1.840)
        _tout(self, line, c1, c2, c3, f, run_time=0.4)
        self.pad_to_voice()


# ---------------- S4 机制三：训练改得掉权重，改不掉相关性 ----------------
class S4(_Base):
    def construct(self):
        self.bg()
        f = _footer(self)

        # 页1：问句 + 分解
        head = _head("训练更新权重，痕迹还在吗？", 34)
        wcard = VGroup(t("W = W", 40, WHITE), sub("W", "0"),
                       t(" + Δ", 40, YELL, "BOLD")).arrange(RIGHT, buff=0.14)
        ans = t("在", 96, GREEN, "BOLD")
        sub2 = t("发布权重 = 初始值 + 训练累计增量", 30, MUTED)
        note1 = t("这就是全部线索的来源", 24, MUTED)
        page1 = page_stack(head, wcard, ans, sub2, note1, buff=1.02)
        layout_page(page1)
        self.at_clip("S4-c01")
        self.play(type_in(head, run_time=0.6), type_in(wcard, run_time=0.6), run_time=0.8)
        self.wait(4.3333)
        self.at_clip("S4-c02")
        self.play(FadeIn(ans, shift=DOWN * 0.1), FadeIn(sub2, shift=UP * 0.05),
                  FadeIn(note1, shift=UP * 0.05), run_time=0.6)
        self.play(FadeOut(head), FadeOut(wcard), FadeOut(ans), FadeOut(sub2),
                  FadeOut(note1), run_time=0.45)

        # 页2：假设 + 公式（c04 台词「增量和初始值近似无关」）
        head2 = _head("近似无关假设", 34)
        assume = VGroup(t("Δ ⊥ W", 32, CYAN, "BOLD"), sub("Δ ⊥ W", "0"),
                        t("（更新量与初始化近似无关）", 26, MUTED)).arrange(RIGHT, buff=0.14)
        formula = MathTex(r"\mathrm{Corr}(W,W_0)=\frac{1}{\sqrt{1+\mathrm{Var}(\Delta)/\mathrm{Var}(W_0)}}",
                          font_size=38).set_color(WHITE)
        noteF = t("训练往矩阵里加的增量，几乎不带初始化的信息", 26, MUTED)
        cardC = boxed("协方差项 C ≈ 0：改动与初始化近似无关，结论才稳", 6.6, 1.7, MUTED, 26)
        page2 = page_stack(head2, assume, formula, cardC, noteF, buff=0.9)
        layout_page(page2)
        self.wait(2.0000)
        self.at_clip("S4-c04")
        self.play(type_in(head2, run_time=0.5), type_in(assume, run_time=0.6), run_time=0.7)
        self.wait(0.1000)
        self.play(Write(formula), run_time=1.0)
        self.wait(0.0333)
        self.play(FadeIn(cardC, shift=UP * 0.08), FadeIn(noteF, shift=UP * 0.05), run_time=0.6)
        self.wait(4.3667)                                         # -> 15.30

        # 页3：双 counter 228 倍 / 0.066
        self.at_clip("S4-c05")
        self.play(FadeOut(head2), FadeOut(assume), FadeOut(formula), FadeOut(noteF), run_time=0.45)
        head3 = _head("改得天翻地覆，仍剩一点相关性", 30)
        labA = t("训练改动方差 / 初始化方差", 24, WHITE)
        labB = t("剩余相关系数", 24, WHITE)
        slotA = dynamic_slot(2.2, 1.0)
        slotB = dynamic_slot(2.2, 1.0)
        labA.next_to(slotA, UP, buff=0.26).align_to(slotA, LEFT)
        labB.next_to(slotB, UP, buff=0.26).align_to(slotB, LEFT)
        page3 = page_stack(head3, VGroup(labA, slotA), VGroup(labB, slotB), buff=0.6)
        layout_page(page3)
        n1 = self.counter_value(0, 228, suffix=" 倍", size=54, run_time=1.2,
                                anchor=slotA, extra_anims=[type_in(labA, run_time=0.5)])
        self.wait(4.5000)                                         # -> 21.57
        self.at_clip("S4-c07")
        n2 = self.counter_value(0.99, 0.066, suffix="", decimals=3, size=54, run_time=1.2,
                                anchor=slotB, extra_anims=[type_in(labB, run_time=0.5)])
        self.wait(0.8000)                                         # -> 23.64

        # 页4：57 西格玛
        self.at_clip("S4-c08")
        self.play(FadeOut(head3), FadeOut(VGroup(labA, n1)), FadeOut(VGroup(labB, n2)), run_time=0.45)
        head4 = _head("大样本假设检验", 32)
        zform = VGroup(t("z = r √n", 38, WHITE, "BOLD"),
                       t("n = 745,472 权重 × 42 层", 28, MUTED)).arrange(DOWN, buff=0.3)
        sig = t("57 σ", 96, YELL, "BOLD")
        cap = t("单次 5σ 已极罕见，57σ 不可能是噪声", 26, MUTED)
        page4 = page_stack(head4, zform, sig, cap, buff=0.5)
        layout_page(page4)
        self.play(type_in(head4, run_time=0.5), type_in(zform, run_time=0.6), run_time=0.7)
        self.wait(1.5667)
        self.at_clip("S4-c09")
        self.play(FadeIn(sig, shift=UP * 0.12), type_in(cap, run_time=0.6), run_time=0.8)
        self.wait(1.6333)                                         # -> 32.20

        # 页5：多重比较
        self.at_clip("S4-c10")
        self.play(FadeOut(head4), FadeOut(zform), FadeOut(sig), FadeOut(cap), run_time=0.45)
        head5 = _head("也要排除碰巧", 32)
        m1 = t("seed 共 2³² ≈ 43 亿种", 30, WHITE)
        m2 = t("候选 SM 档位两百多种", 30, WHITE)
        m3 = t("六个模型合计 ≈ 6 万亿次比较", 30, WHITE)
        ms = VGroup(m1, m2, m3).arrange(DOWN, buff=0.55, aligned_edge=LEFT)
        ms.set_x(0)
        cap5 = t("纯靠运气，最高也就 8 σ", 30, MUTED)
        page5 = page_stack(head5, ms, cap5, buff=0.55)
        layout_page(page5)
        self.play(type_in(head5, run_time=0.5), FadeIn(ms, shift=RIGHT * 0.12), run_time=0.7)
        self.wait(10.8333)                                         # -> 41.12

        # 页6：观测 49–1385σ 对比条
        self.at_clip("S4-c13")
        self.play(FadeOut(head5), FadeOut(ms), FadeOut(cap5), run_time=0.45)
        head6 = _head("实际观测：49 到 1385 σ", 32)
        tr = ValueTracker(0)
        b1 = Rectangle(width=0.02, height=0.75, color=MUTED, fill_color=MUTED, fill_opacity=0.6)
        b2 = Rectangle(width=0.02, height=0.75, color=CYAN, fill_color=CYAN, fill_opacity=0.8)
        b3 = Rectangle(width=0.02, height=0.75, color=YELL, fill_color=YELL, fill_opacity=0.9)
        bars = VGroup(b1, b2, b3).arrange(DOWN, buff=0.85, aligned_edge=LEFT)
        bars.set_x(-2.4)
        l1 = t("偶然上限 8σ", 26, MUTED)
        l2 = t("最低读数 49σ", 26, CYAN)
        l3 = t("最高读数 1385σ", 26, YELL, "BOLD")
        for lb, b in zip([l1, l2, l3], [b1, b2, b3]):
            lb.next_to(b, RIGHT, buff=0.25).align_to(b, DOWN)
        cap6 = t("远超偶然上限：极值模型假设成立", 26, MUTED)
        page6 = page_stack(head6, VGroup(bars, l1, l2, l3), cap6, buff=0.6)
        layout_page(page6)
        self.play(type_in(head6, run_time=0.5), FadeIn(l1), FadeIn(l2), FadeIn(l3), run_time=0.6)
        self.wait(0.3)
        self.grow_bar(b1, tr, 0.5, run_time=0.5)
        self.wait(0.0)
        self.grow_bar(b2, tr, 2.2, run_time=0.6)
        self.wait(0.0)
        self.grow_bar(b3, tr, 5.9, run_time=0.8)
        self.wait(0.4)
        self.emphasize(l3, mode="circumscribe", run_time=0.7)
        self.wait(1.1)
        _tout(self, head6, bars, l1, l2, l3, cap6, f, run_time=0.4)
        self.pad_to_voice()


# ---------------- S5 证据：六款模型读数 + 真卡复现 ----------------
class S5(_Base):
    def construct(self):
        self.bg()
        f = _footer(self)

        # 页1：六款模型 σ 表
        head = _head("六款模型的指纹读数", 32)
        rows = [
            ("DeepSeek-V4-Flash", "B200 档", "1385σ"),
            ("DeepSeek-V4-Pro", "GB200 档", "49σ"),
            ("Kimi K3 / K3.1-Pro", "GB200 档", "305σ"),
            ("MiniMax-M3", "B200 档", "323σ"),
            ("Ling-3.1-flash", "GB200 档", "244σ"),
        ]
        rowmobs = []
        for name, tier, sig in rows:
            a = t(name, 26, WHITE, "BOLD")
            b = t(tier, 22, MUTED)
            c = t(sig, 32, YELL, "BOLD")
            rowmobs.append(VGroup(a, b, c).arrange(RIGHT, buff=0.55))
        tbl = VGroup(*rowmobs).arrange(DOWN, buff=0.8, aligned_edge=LEFT)
        tbl.set_x(0)
        note = t("2026-04 至 2026-10 发布，全带 Blackwell 指纹", 24, MUTED)
        page1 = page_stack(head, tbl, note, buff=0.6)
        layout_page(page1)
        self.at_clip("S5-c01")
        self.play(type_in(head, run_time=0.5), FadeIn(rowmobs[0], shift=RIGHT * 0.12), run_time=0.6)
        self.wait(7.8333)                                         # -> 8.50
        self.at_clip("S5-c03")
        self.play(FadeIn(rowmobs[1], shift=RIGHT * 0.12), run_time=0.5)
        self.wait(4.2667)                                         # -> 13.37
        self.at_clip("S5-c05")
        self.play(FadeIn(rowmobs[2], shift=RIGHT * 0.12), run_time=0.5)
        self.wait(4.3333)                                         # -> 22.04
        self.at_clip("S5-c07")
        self.play(FadeIn(rowmobs[3], shift=RIGHT * 0.12), run_time=0.5)
        self.wait(8.1667)                                         # -> 27.10

        # 页2：物理复现
        self.at_clip("S5-c10")
        self.play(FadeOut(head), FadeOut(tbl), FadeOut(note), run_time=0.45)
        head2 = _head("作者租了真卡复现", 32)
        c1 = boxed("GB200 上重放 Kimi K3 保留的 13 行", 6.6, 1.7, CYAN, 28)
        slotR = dynamic_slot(2.6, 1.1)
        lab1 = t("相关系数", 22, MUTED)
        lab1.next_to(slotR, UP, buff=0.2).align_to(slotR, LEFT)
        c2 = boxed("B300 上重放 V4-Flash 的 469 行", 6.6, 1.7, CYAN, 28)
        hit = t("461 行命中 · 445 行逐比特一致", 34, GREEN, "BOLD")
        page2 = page_stack(head2, VGroup(c1, VGroup(lab1, slotR)), c2, hit, buff=0.95)
        layout_page(page2)
        self.play(type_in(head2, run_time=0.5), FadeIn(c1, shift=UP * 0.08), run_time=0.7)
        self.wait(3.9000)                                         # -> 32.90
        r = self.counter_value(0.9, 0.999996, suffix="", decimals=6, size=48, run_time=1.4,
                               anchor=slotR, extra_anims=[type_in(lab1, run_time=0.5)])
        self.wait(1.5333)                                         # -> 35.17
        self.at_clip("S5-c12")
        self.play(FadeIn(c2, shift=UP * 0.08), run_time=0.6)
        self.wait(3.2333)
        self.at_clip("S5-c13")
        self.play(FadeIn(hit, shift=UP * 0.08), run_time=0.6)
        self.wait(2.9000)                                         # -> 45.38

        # 页3：种子 + 对照组
        self.at_clip("S5-c14")
        self.play(FadeOut(head2), FadeOut(VGroup(c1, lab1, r)), FadeOut(c2), FadeOut(hit), run_time=0.45)
        head3 = _head("种子只改 1，匹配全部消失", 32)
        s1 = t("953,049,583", 64, YELL, "BOLD")
        s2 = t("DeepSeek 用的种子，与 V3 是同一个", 28, WHITE)
        ctrl = boxed("对照组 24 个公开过硬件的模型，24 个全对", 6.6, 2.0, GREEN, 30)
        src = t("Llama 3.1 的 H100 → Nemotron 的 GB200", 22, MUTED)
        page3 = page_stack(head3, s1, s2, ctrl, src, buff=0.72)
        layout_page(page3)
        self.play(type_in(head3, run_time=0.5), FadeIn(s1, shift=UP * 0.1), run_time=0.7)
        self.wait(6.4667)
        self.at_clip("S5-c16")
        self.play(FadeIn(s2, shift=UP * 0.06), run_time=0.6)
        self.wait(1.1667)                                         # -> 58.66

        # 页4：对照组 + 代际
        self.at_clip("S5-c17")
        self.play(FadeOut(head3), FadeOut(s1), FadeOut(s2), run_time=0.45)
        head4 = _head("一致性检查：24 个全对", 32)
        ctrl2 = boxed("Llama 3.1 的 H100 → Nemotron 的 GB200", 6.2, 1.7, GREEN, 26)
        ok = t("24 / 24", 72, GREEN, "BOLD")
        old = t("上一代 V3/K2.5/M2.7 全是 Hopper", 24, MUTED)
        new = t("V4 与 K3 这一代，换成 Blackwell", 30, YELL, "BOLD")
        page4 = page_stack(head4, ctrl2, ok, old, new, buff=0.78)
        layout_page(page4)
        self.play(type_in(head4, run_time=0.5), FadeIn(ctrl2, shift=UP * 0.08), run_time=0.7)
        self.wait(5.0667)
        self.at_clip("S5-c19")
        self.play(FadeIn(ok, shift=UP * 0.1), run_time=0.6)
        self.emphasize(ok, mode="circumscribe", run_time=0.2000)
        self.wait(0.0667)
        self.at_clip("S5-c20")
        self.play(FadeIn(old, shift=UP * 0.06), FadeIn(new, shift=UP * 0.06), run_time=0.6)
        self.breathe(new, loops=2, run_time=1.0)
        self.wait(3.400)
        _tout(self, head4, ctrl2, ok, old, new, f, run_time=0.4)
        self.pad_to_voice()


# ---------------- S6 结论：证明了什么，没证明什么 ----------------
class S6(_Base):
    def construct(self):
        self.bg()
        f = _footer(self)

        # 页1：铁证 + 红叉否定（c01-c05）
        head = _head("所以到底证明了什么？", 34)
        proof = boxed("铁证：初始化权重在 Blackwell 这一档硬件上生成", 6.6, 3.0, GREEN, 34, weight="BOLD")
        wrong = t("训练也在 GB300 上", 40, RED, "BOLD")
        right = t("初始化只是起点，不是全程", 32, WHITE)
        page1 = page_stack(head, proof, VGroup(wrong, right).arrange(DOWN, buff=0.55), buff=0.95)
        layout_page(page1)
        self.at_clip("S6-c01")
        self.play(type_in(head, run_time=0.6), FadeIn(proof, shift=UP * 0.1), run_time=0.8)
        self.wait(7.9667)                                         # -> 8.86
        self.at_clip("S6-c04")
        self.play(type_in(wrong, run_time=0.6), run_time=0.6)
        self.wait(0.3000)
        cross = self.play_red_cross(wrong, run_time=0.6)
        self.wait(0.2333)
        self.play(type_in(right, run_time=0.6), run_time=0.6)
        self.wait(2.8000)                                         # -> 23.86 前的 c06 由下页锚定

        # 页2：报告自列无法确认（c06-c09）
        self.at_clip("S6-c06")
        self.play(FadeOut(head), FadeOut(proof), FadeOut(wrong), FadeOut(right), FadeOut(cross),
                  run_time=0.45)
        head3 = _head("报告自己列了一串无法确认", 32)
        u1 = boxed("每家的算力利用率 MFU", 6.6, 1.35, MUTED, 26)
        u2 = boxed("训练 token 数与每轮时长", 6.6, 1.35, MUTED, 26)
        u3 = boxed("训练是否留在创建初始权重的硬件上", 6.6, 1.35, MUTED, 26)
        us = VGroup(u1, u2, u3).arrange(DOWN, buff=0.5)
        note3 = t("所以「初始化在 Blackwell」推不出「训练在 Blackwell」", 26, YELL, "BOLD")
        caveat = boxed("报告原话：无法排除在一个系统上生成权重，再搬到另一个系统", 6.6, 1.6, MUTED, 24)
        page2 = page_stack(head3, us, caveat, note3, buff=0.72)
        layout_page(page2)
        self.play(type_in(head3, run_time=0.5), FadeIn(us, shift=RIGHT * 0.12), run_time=0.7)
        self.wait(4.8667)
        self.play(FadeIn(caveat, shift=UP * 0.08), run_time=0.6)
        self.wait(1.4333)
        self.play(FadeIn(note3, shift=UP * 0.06), run_time=0.5)
        self.wait(1.1000)                                         # -> 34.06

        # 页3： loophole + 规模（c09-c11）
        self.at_clip("S6-c09")
        self.play(FadeOut(head3), FadeOut(us), FadeOut(caveat), FadeOut(note3), run_time=0.45)
        head4 = _head("算力从哪来？两条明路", 32)
        c1 = boxed("Blackwell 在中国以外的数据中心租得到", 6.6, 1.6, CYAN, 28)
        c2 = boxed("权重生成之后，再搬到别的系统", 6.6, 1.6, CYAN, 28)
        scale = VGroup(t("12,000 张 Blackwell", 30, WHITE),
                       t("每张约 7 万美元", 26, WHITE),
                       t("五次训练合计超 5 亿美元", 34, YELL, "BOLD")).arrange(DOWN, buff=0.34)
        page4 = page_stack(head4, c1, c2, scale, buff=0.65)
        layout_page(page4)
        self.play(type_in(head4, run_time=0.5), FadeIn(c1, shift=UP * 0.08), run_time=0.7)
        self.wait(3.1667)
        self.at_clip("S6-c10")
        self.play(FadeIn(c2, shift=UP * 0.08), run_time=0.6)
        self.wait(1.8000)
        self.at_clip("S6-c11")
        self.play(FadeIn(scale, shift=UP * 0.08), run_time=0.6)
        self.wait(2.5667)                                         # -> 50.41

        # 页4：社区反驳
        self.at_clip("S6-c12")
        self.play(FadeOut(head4), FadeOut(c1), FadeOut(c2), FadeOut(scale), run_time=0.45)
        head5 = _head("社区还有两头反驳", 32)
        c1 = boxed("迪伦·帕特尔：不是新闻，DeepSeek 早开源了只支持 SM100 和昇腾 950 的推理引擎", 6.6, 2.2, CYAN, 26)
        c2 = boxed("功耗账：3,000 张卡约 6 兆瓦，做最终训练远远不够", 6.6, 1.8, CYAN, 26)
        note5 = t("两边都承认芯片到过中国，争的是算力够不够", 26, MUTED)
        page5 = page_stack(head5, c1, c2, note5, buff=0.72)
        layout_page(page5)
        self.play(type_in(head5, run_time=0.5), FadeIn(c1, shift=UP * 0.08), run_time=0.7)
        self.wait(9.4000)
        self.at_clip("S6-c14")
        self.play(FadeIn(c2, shift=UP * 0.08), FadeIn(note5, shift=UP * 0.05), run_time=0.6)
        self.wait(5.0000)                                         # -> 58.90

        # 页5：金句 + 收尾
        self.at_clip("S6-c16")
        self.play(FadeOut(head5), FadeOut(c1), FadeOut(c2), FadeOut(note5), run_time=0.45)
        line = t("指纹能证明芯片存在，", 38, WHITE, "BOLD")
        line2 = t("证明不了算力充裕", 38, YELL, "BOLD")
        g = VGroup(line, line2).arrange(DOWN, buff=0.34)
        note = t("方法已经公开，任何实验室都可以抹掉痕迹", 26, MUTED)
        ask = t("你觉得哪种可能性更大？", 32, WHITE, "BOLD")
        echo = t("禁运卡的指纹，藏在权重里", 24, MUTED)
        page6 = page_stack(g, note, ask, echo, buff=0.72)
        layout_page(page6)
        self.play(type_in(g, run_time=0.8), run_time=0.8)
        self.wait(0.4333)
        self.emphasize(line2, mode="circumscribe", run_time=0.7)
        self.wait(1.1333)
        self.at_clip("S6-c17")
        self.play(FadeIn(note, shift=UP * 0.06), run_time=0.6)
        self.wait(4.1667)
        self.at_clip("S6-c18")
        self.play(FadeIn(ask, shift=UP * 0.06), FadeIn(echo, shift=UP * 0.06), run_time=0.6)
        self.wait(5.7333)                                         # -> 65.32

        # 页6：品牌尾卡
        self.at_clip("S6-c21")
        self.play(FadeOut(g), FadeOut(note), FadeOut(ask), FadeOut(echo), run_time=0.4)
        avatar = _img(str(AVATAR.name), 3.0)
        lFollow = t("关注「数解AI」", 32, YELL, "BOLD")
        lTitle = t("国产大模型真是用禁运的GB300训练的吗？", 28, WHITE)
        lGuide = t("查看公众号文章", 28, GREEN, "BOLD")
        lNext = t("下一篇：量一次起始距离，四两拨千斤", 22, MUTED)
        tail_card = VGroup(avatar, lFollow, lTitle, lGuide, lNext).arrange(DOWN, buff=0.45)
        page7 = page_stack(tail_card, buff=0.6)
        layout_page(page7)
        self.play(FadeIn(avatar, shift=DOWN * 0.1), FadeIn(lFollow, shift=UP * 0.08), run_time=0.6)
        self.wait(0.5)
        self.play(FadeIn(lTitle, shift=UP * 0.06), run_time=0.6)
        self.wait(0.4)
        self.play(FadeIn(lGuide, shift=UP * 0.06), FadeIn(lNext, shift=UP * 0.06), run_time=0.6)
        self.wait(2.9)
        _tout(self, avatar, lFollow, lTitle, lGuide, lNext, f, run_time=0.4)
        self.pad_to_voice()
