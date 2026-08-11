#!/usr/bin/env python3
"""《词嵌入为什么让AI懂"苹果"？5万个0变坐标》视频号 Manim 动画（竖屏 1080×1920）

8 个场景 S1-S8 + 封面 Cover，与 storyboard.md 一一对应。
布局规范（硬性）：VGroup 原子化 + 锚点链 + 安全区 + 比例坐标，禁止裸魔法数字定位。
v2：内容占屏 ≥40%（最低点距底 ≤800px）、宽组 set_width 守卫、底部留字幕区（距底 ≥399px）。
用法：
  python3 -m manim render -qm --disable_caching scenes.py S1 S2 S3 S4 S5 S6 S7 S8
  python3 -m manim render -qm -s --disable_caching scenes.py Cover
"""
from __future__ import annotations

from manim import *

# 竖屏 9:16 画布
config.pixel_width = 1080
config.pixel_height = 1920
config.frame_width = 8.0
config.frame_height = 14.2222
config.background_color = "#16213E"

FONT = "Noto Sans CJK SC"
YELL = "#FFD54A"      # 主强调（与字幕黄一致）
CYAN = "#58C4DD"
GREEN = "#7ED7A0"
RED = "#FF8A80"
MUTED = "#AAB4C8"
WHITE = "#F0F3F8"

# 每个场景的配音时长（ffprobe 实测 2026-08-12），渲染时长 = 配音 + 缓冲
VOICE_DUR = {"S1": 22.04, "S2": 23.8, "S3": 35.52, "S4": 34.0, "S5": 28.92, "S6": 32.35, "S7": 31.89, "S8": 26.3}
TAIL = 2.5  # 段尾缓冲（build 会截到 0.1s）


def t(text: str, size: float = 34, color: str = WHITE, weight: str = "NORMAL") -> Text:
    return Text(text, font=FONT, font_size=size, color=color, weight=weight)


def boxed(label: str, w: float, h: float, color: str, fs: float = 28,
          fill: float = 0.12, wc=None, weight: str = "NORMAL") -> VGroup:
    """固定尺寸框 + 限宽文字（文字 ≤ 框宽 78%，防溢出）。"""
    txt = t(label, fs, wc or color, weight)
    txt.set_width(w * 0.78)
    box = Rectangle(width=w, height=h, color=color,
                    fill_color=color, fill_opacity=fill)
    return VGroup(box, txt)


def dot_label(label: str, col: str, fs: float = 24) -> VGroup:
    d = Dot(color=col, radius=0.09)
    lb = t(label, fs, col)
    return VGroup(d, lb).arrange(RIGHT, buff=0.18)


def fit(mob, frac: float = 0.85):
    """宽内容守卫：不超过画布宽的 frac（防越界截断）。"""
    return mob.set_width(config.frame_width * frac)


class _Base(Scene):
    scene_dur = 12.0

    def setup(self):
        self.scene_dur = VOICE_DUR[self.__class__.__name__] + TAIL

    def at(self, t: float):
        """推进到配音时间轴绝对时刻（动画动作挂到台词节点上）。"""
        if t > self.time:
            self.wait(t - self.time)

    def pad_to_voice(self):
        """末尾补齐等待，使场景总时长 = 配音时长 + TAIL 缓冲。"""
        elapsed = self.time
        target = self.scene_dur
        if target > elapsed:
            self.wait(target - elapsed)

    def footer(self, text: str = "数解AI · 大模型原理"):
        f = t(text, 20, MUTED).to_edge(DOWN, buff=1.15)
        self.add(f)


# ---------------- S1 开场钩子：0 字匹配 ----------------
class S1(_Base):
    def construct(self):
        self.footer()
        head = t("0 字匹配，凭什么命中？", 40, YELL, "BOLD").to_edge(UP, buff=1.2)
        self.play(FadeIn(head, shift=DOWN * 0.05))

        # 页1：AI 搜索 vs Ctrl+F（锚点链，间距拉满占屏）
        self.at(0.91)
        q1 = boxed("搜索：苹果手机", 2.6, 0.9, CYAN, 26)
        ok = boxed("iPhone 16 Pro ✓", 2.5, 0.9, GREEN, 26)
        row1 = VGroup(q1, ok).arrange(RIGHT, buff=1.0).next_to(head, DOWN, buff=1.5)
        a1 = Arrow(q1.get_right(), ok.get_left(), color=GREEN, buff=0.12, stroke_width=4)
        self.play(FadeIn(q1, shift=DOWN * 0.05), run_time=0.6)
        self.play(Create(a1), FadeIn(ok, shift=DOWN * 0.05), run_time=0.7)

        self.at(7.62)
        q2 = boxed("Ctrl+F：苹果", 2.4, 0.9, RED, 26)
        bad = boxed("吃苹果 / 苹果发布会 / 苹果醋", 3.9, 0.9, RED, 22)
        row2 = VGroup(q2, bad).arrange(RIGHT, buff=1.0).next_to(row1, DOWN, buff=1.2)
        a2 = Arrow(q2.get_right(), bad.get_left(), color=RED, buff=0.12, stroke_width=4)
        self.play(FadeIn(q2, shift=DOWN * 0.05), run_time=0.5)
        self.play(Create(a2), FadeIn(bad, shift=DOWN * 0.05), run_time=0.7)

        vs = t("Ctrl+F 只认字形 · AI 认语义", 30, WHITE).next_to(row2, DOWN, buff=1.3)
        self.play(FadeIn(vs, shift=DOWN * 0.05))
        hook = boxed("0 字匹配，凭什么命中？", 4.6, 1.1, YELL, 32, fill=0.2, weight="BOLD")
        hook.next_to(vs, DOWN, buff=1.3)
        self.play(FadeIn(hook, scale=1.15), run_time=0.7)

        # 页2：高维语义空间两簇
        self.at(14.02)
        self.play(FadeOut(VGroup(row1, a1, row2, a2, vs, hook), shift=UP * 0.05), run_time=0.4)
        lab = t("高维语义空间（示意）", 26, MUTED).next_to(head, DOWN, buff=1.6)
        near = VGroup(dot_label("苹果手机", GREEN, 22), dot_label("iPhone 16 Pro", GREEN, 22),
                      dot_label("苹果", GREEN, 22)).arrange(RIGHT, buff=0.35)
        far = VGroup(dot_label("汽车", MUTED, 22), dot_label("苹果醋", MUTED, 22)).arrange(RIGHT, buff=0.35)
        stage = VGroup(near, far).arrange(RIGHT, buff=2.2)
        fit(stage, 0.85)
        stage.next_to(lab, DOWN, buff=1.6)
        ring = Ellipse(width=near.width + 0.6, height=near.height + 0.7,
                       color=GREEN, stroke_width=2).move_to(near)
        self.play(FadeIn(lab, shift=DOWN * 0.05))
        self.play(FadeIn(near, shift=UP * 0.05), FadeIn(far, shift=UP * 0.05))
        self.play(Create(ring), run_time=0.6)
        cap = t("意思近的，坐标挨得近；意思远的，各站一角", 30, WHITE)
        fit(cap, 0.85)
        cap.next_to(stage, DOWN, buff=1.5)
        self.play(FadeIn(cap, shift=DOWN * 0.05))
        self.at(19.77)
        cap2 = t("搜索，就是在空间里找邻居", 32, GREEN, "BOLD").next_to(cap, DOWN, buff=1.1)
        self.play(FadeIn(cap2, scale=0.9), run_time=0.8)
        self.pad_to_voice()


# ---------------- S2 第一步：分词 ----------------
class S2(_Base):
    def construct(self):
        self.footer()
        head = t("第一步：分词", 40, YELL, "BOLD").to_edge(UP, buff=1.2)
        self.play(FadeIn(head, shift=DOWN * 0.05))

        # 页1：输入句 → 6 token + 编号
        self.at(1.81)
        sent = boxed("今天天气真好，适合出去玩", 5.8, 1.0, CYAN, 30)
        sent.next_to(head, DOWN, buff=1.5)
        self.play(FadeIn(sent, shift=DOWN * 0.05), run_time=0.6)

        self.at(3.89)
        words = ["今天", "天气", "真好", "，", "适合", "出去玩"]
        ids = ["5237", "16652", "67261", "303", "10447", "122377"]
        blocks = VGroup()
        for wd in words:
            bw = 0.55 if wd == "，" else 1.15
            blocks.add(boxed(wd, bw, 0.8, CYAN, 26))
        blocks.arrange(RIGHT, buff=0.15).next_to(sent, DOWN, buff=1.2)
        idrow = VGroup()
        for blk, iid in zip(blocks, ids):
            idrow.add(t(iid, 20, MUTED).set_width(blk.width * 0.8).next_to(blk, DOWN, buff=0.15))
        idrow.next_to(blocks, DOWN, buff=0.25)
        self.play(*[FadeIn(b, shift=DOWN * 0.05) for b in blocks], run_time=0.9)
        self.play(*[FadeIn(i, shift=DOWN * 0.05) for i in idrow], run_time=0.7)

        self.at(6.30)
        hl = [blocks[0], blocks[5]]
        tip = t("常见词组 → 打包成单个 token", 28, GREEN).next_to(idrow, DOWN, buff=1.2)
        self.play(*[b[0].animate.set_stroke(color=GREEN, width=5) for b in hl],
                  FadeIn(tip, shift=DOWN * 0.05), run_time=0.8)

        # 页2：词表卡 + ID 无远近 + 怎么办
        self.at(7.93)
        self.play(FadeOut(VGroup(sent, blocks, idrow, tip), shift=UP * 0.05), run_time=0.4)
        vocab_head = t("DeepSeek-V4-Pro · 2026", 28, MUTED).next_to(head, DOWN, buff=1.5)
        vocab_num = t("vocab_size = 129,280", 46, YELL, "BOLD").next_to(vocab_head, DOWN, buff=0.5)
        vocab_note = t("约 13 万个 token，每个一个整数编号", 28, WHITE).next_to(vocab_num, DOWN, buff=0.6)
        self.play(FadeIn(vocab_head, shift=DOWN * 0.05), FadeIn(vocab_num, shift=DOWN * 0.05))
        self.play(FadeIn(vocab_note, shift=DOWN * 0.05))

        self.at(17.49)
        c1 = boxed("猫 → ID 11440", 2.6, 1.0, CYAN, 30)
        c2 = boxed("猫咪 → ID 54420", 2.9, 1.0, CYAN, 30)
        pair = VGroup(c1, c2).arrange(RIGHT, buff=0.8).next_to(vocab_note, DOWN, buff=1.1)
        cross = t("✗", 44, RED, "BOLD").move_to(VGroup(c1, c2).get_center())
        self.play(FadeIn(c1, shift=UP * 0.05), FadeIn(c2, shift=UP * 0.05))
        self.play(FadeIn(cross, scale=1.2), run_time=0.5)
        id_note = t("两个数字之间，毫无联系", 32, RED).next_to(pair, DOWN, buff=0.8)
        self.play(FadeIn(id_note, shift=DOWN * 0.05))

        self.at(23.08)
        why = t("怎么办？", 46, RED, "BOLD").next_to(id_note, DOWN, buff=0.8)
        self.play(FadeIn(why, scale=1.15), run_time=0.8)
        self.pad_to_voice()


# ---------------- S3 One-hot：距离全等 ----------------
class S3(_Base):
    def construct(self):
        self.footer()
        head = t("方案一：One-hot", 40, YELL, "BOLD").to_edge(UP, buff=1.2)
        self.play(FadeIn(head, shift=DOWN * 0.05))

        # 页1：三词词表 → 垂直箭头 → cos=0 → 语义为零
        self.at(5.67)
        rows = VGroup()
        for wd, vec in [("猫", [1, 0, 0]), ("狗", [0, 1, 0]), ("汽车", [0, 0, 1])]:
            wb = boxed(wd, 1.2, 0.7, CYAN, 28)
            cells = VGroup(*[boxed(str(v), 0.62, 0.7, GREEN if v else MUTED, 24)
                             for v in vec]).arrange(RIGHT, buff=0.08)
            eq = t("=", 30, WHITE)
            row = VGroup(wb, eq, cells).arrange(RIGHT, buff=0.25)
            rows.add(row)
        rows.arrange(DOWN, buff=0.3).next_to(head, DOWN, buff=0.9)
        self.play(*[FadeIn(r, shift=DOWN * 0.05) for r in rows], run_time=1.0)

        self.at(16.13)
        origin = Dot(color=WHITE, radius=0.08)
        a_up = Arrow(ORIGIN, UP * 0.8 + RIGHT * 0.3, color=GREEN, stroke_width=5, buff=0.1)
        a_lf = Arrow(ORIGIN, UP * 0.8 - RIGHT * 0.3, color=CYAN, stroke_width=5, buff=0.1)
        a_dn = Arrow(ORIGIN, DOWN * 0.8, color=MUTED, stroke_width=5, buff=0.1)
        trio = VGroup(origin, a_up, a_lf, a_dn).next_to(rows, DOWN, buff=0.5)
        perp = t("三个向量，互相垂直", 30, WHITE).next_to(trio, DOWN, buff=0.4)
        self.play(FadeIn(trio, shift=UP * 0.05), run_time=0.6)
        self.play(FadeIn(perp, shift=DOWN * 0.05), run_time=0.6)

        self.at(18.09)
        self.play(FadeOut(VGroup(rows, trio, perp), shift=UP * 0.05), run_time=0.4)
        c1 = t("cos(猫, 狗) = 0", 32, RED, "BOLD")
        c2 = t("cos(猫, 汽车) = 0", 32, RED, "BOLD")
        cosg = VGroup(c1, c2).arrange(DOWN, buff=0.3).next_to(head, DOWN, buff=1.8)
        eq_note = t("猫和狗的距离 = 猫和汽车的距离", 30, WHITE).next_to(cosg, DOWN, buff=0.9)
        self.play(FadeIn(c1, shift=DOWN * 0.05), FadeIn(c2, shift=DOWN * 0.05), run_time=0.7)
        self.play(FadeIn(eq_note, shift=DOWN * 0.05), run_time=0.6)

        self.at(24.62)
        zero = t("语义？为零。", 46, RED, "BOLD").next_to(eq_note, DOWN, buff=1.5)
        self.play(FadeIn(zero, scale=1.15), run_time=0.8)

        # 页2：13 万维膨胀 + 判死刑
        self.at(25.93)
        self.play(FadeOut(VGroup(rows, trio, perp, cosg, eq_note, zero), shift=UP * 0.05), run_time=0.4)
        big = t("13 万 token → 13 万维", 44, YELL, "BOLD").next_to(head, DOWN, buff=1.5)
        cells = VGroup(*[Rectangle(width=0.5, height=0.95, color=MUTED,
                                   fill_color=MUTED, fill_opacity=0.18) for _ in range(8)])
        cells.arrange(RIGHT, buff=0.08).next_to(big, DOWN, buff=1.1)
        lit = boxed("1", 0.5, 0.95, YELL, 30).move_to(cells[3])
        many = t("… × 13 万位，几乎全是 0", 28, WHITE).next_to(cells, DOWN, buff=0.8)
        self.play(FadeIn(big, shift=DOWN * 0.05))
        self.play(*[FadeIn(c, shift=DOWN * 0.05) for c in cells], FadeIn(many, shift=DOWN * 0.05), run_time=0.9)
        self.play(FadeIn(lit, scale=1.2), run_time=0.5)

        self.at(32.25)
        charge = t("维度灾难 + 语义为零", 34, RED).next_to(many, DOWN, buff=1.1)
        stamp = boxed("判死刑", 2.6, 1.2, RED, 40, fill=0.25, weight="BOLD")
        stamp.next_to(charge, DOWN, buff=1.0)
        self.play(FadeIn(charge, shift=DOWN * 0.05))
        self.play(FadeIn(stamp, scale=1.6), run_time=0.7)
        self.pad_to_voice()


# ---------------- S4 嵌入矩阵 ----------------
class S4(_Base):
    def construct(self):
        self.footer()
        head = t("答案：嵌入矩阵", 40, YELL, "BOLD").to_edge(UP, buff=1.2)
        self.play(FadeIn(head, shift=DOWN * 0.05))

        # 页1：矩阵示意 + 真实规模
        self.at(0.81)
        cells = VGroup()
        for r in range(3):
            for c in range(4):
                cells.add(Rectangle(width=0.72, height=0.56, color=CYAN,
                                    fill_color=CYAN, fill_opacity=0.12))
        cells.arrange_in_grid(rows=3, cols=4, buff=0.06)
        rlab = VGroup(t("猫", 24, WHITE), t("狗", 24, WHITE), t("汽车", 24, WHITE)).arrange(DOWN, buff=0.62)
        rlab.next_to(cells, LEFT, buff=0.3)
        col_lab = t("… 7168 列", 22, MUTED).next_to(cells, RIGHT, buff=0.3)
        row_lab = t("129,280 行 …", 22, MUTED).rotate(PI / 2).next_to(rlab, LEFT, buff=0.25)
        mat = VGroup(cells, rlab, col_lab, row_lab).next_to(head, DOWN, buff=1.5)
        mat_cap = t("行 = 词表大小 · 列 = 嵌入维度", 28, WHITE).next_to(mat, DOWN, buff=1.1)
        self.play(FadeIn(cells, shift=DOWN * 0.05), FadeIn(rlab, shift=DOWN * 0.05), run_time=0.8)
        self.play(FadeIn(col_lab, shift=DOWN * 0.05), FadeIn(row_lab, shift=DOWN * 0.05))
        self.play(FadeIn(mat_cap, shift=DOWN * 0.05))

        self.at(5.74)
        n1 = boxed("vocab_size 129,280", 3.2, 1.0, YELL, 30)
        n2 = boxed("hidden_size 7,168", 3.2, 1.0, YELL, 30)
        nums = VGroup(n1, n2).arrange(RIGHT, buff=0.5).next_to(mat_cap, DOWN, buff=1.3)
        per = t("每个 token，用 7168 个数字表示", 28, WHITE).next_to(nums, DOWN, buff=1.0)
        self.play(FadeIn(n1, shift=DOWN * 0.05), FadeIn(n2, shift=DOWN * 0.05), run_time=0.7)
        self.play(FadeIn(per, shift=DOWN * 0.05))

        # 页2：参数账 → 不是人填的 → 查表
        self.at(19.25)
        self.play(FadeOut(VGroup(cells, rlab, col_lab, row_lab, mat_cap, nums, per), shift=UP * 0.05), run_time=0.4)
        eq = t("129,280 × 7,168 ≈ 9.27 亿", 44, YELL, "BOLD").next_to(head, DOWN, buff=2.0)
        note = t("光嵌入矩阵，占了一个中等模型的体量", 30, WHITE).next_to(eq, DOWN, buff=0.9)
        self.play(FadeIn(eq, shift=DOWN * 0.05))
        self.play(FadeIn(note, shift=DOWN * 0.05))

        self.at(26.21)
        n2a = t("这些数不是人填的", 34, RED).next_to(note, DOWN, buff=1.4)
        n2b = t("是反向传播一步步调出来的", 34, GREEN, "BOLD").next_to(n2a, DOWN, buff=0.5)
        self.play(FadeIn(n2a, shift=DOWN * 0.05))
        self.play(FadeIn(n2b, shift=DOWN * 0.05))

        self.at(30.11)
        oh = boxed("one-hot 向量", 1.9, 1.0, CYAN, 24)
        mt = boxed("嵌入矩阵", 1.9, 1.0, CYAN, 24)
        row_out = boxed("抽出一行 = 向量", 2.6, 1.0, GREEN, 24)
        chain = VGroup(oh, mt, row_out).arrange(RIGHT, buff=0.4)
        fit(chain, 0.88)
        chain.next_to(n2b, DOWN, buff=1.3)
        a1 = Arrow(oh.get_right(), mt.get_left(), color=WHITE, buff=0.12, stroke_width=4)
        a2 = Arrow(mt.get_right(), row_out.get_left(), color=WHITE, buff=0.12, stroke_width=4)
        self.play(FadeIn(oh, shift=UP * 0.05), FadeIn(mt, shift=UP * 0.05))
        self.play(Create(a1), Create(a2), FadeIn(row_out, shift=UP * 0.05), run_time=0.8)
        self.pad_to_voice()


# ---------------- S5 中药柜隐喻 ----------------
class S5(_Base):
    def construct(self):
        self.footer()
        head = t("中药柜隐喻", 40, YELL, "BOLD").to_edge(UP, buff=1.2)
        self.play(FadeIn(head, shift=DOWN * 0.05))

        # 药柜
        self.at(2.73)
        drawers = VGroup()
        for i in range(12):
            d = Rectangle(width=0.95, height=0.7, color=MUTED,
                          fill_color=MUTED, fill_opacity=0.12)
            drawers.add(d)
        drawers.arrange_in_grid(rows=3, cols=4, buff=0.15)
        dg = boxed("当归", 0.95, 0.7, GREEN, 24).move_to(drawers[1])
        cx = boxed("川芎", 0.95, 0.7, GREEN, 24).move_to(drawers[2])
        cabinet = VGroup(drawers, dg, cx).next_to(head, DOWN, buff=1.4)
        cab_cap = t("13 万个抽屉，每个抽屉一个 token", 28, WHITE)
        fit(cab_cap, 0.85)
        cab_cap.next_to(cabinet, DOWN, buff=1.0)
        self.play(FadeIn(cabinet, shift=DOWN * 0.05))
        self.play(FadeIn(cab_cap, shift=DOWN * 0.05))

        # 拉开抽屉 = 粉末（向量）
        self.at(7.82)
        def powder(col=CYAN):
            return VGroup(*[Dot(color=col, radius=0.07) for _ in range(5)]).arrange(RIGHT, buff=0.2)
        p1 = powder().next_to(dg, DOWN, buff=1.3)
        p2 = powder().next_to(cx, DOWN, buff=1.3)
        pcap = t("拉开抽屉 → 一包粉末 = 7168 个数字的向量", 28, WHITE)
        fit(pcap, 0.85)
        pcap.next_to(p1, DOWN, buff=0.9)
        self.play(FadeIn(p1, shift=DOWN * 0.05), FadeIn(p2, shift=DOWN * 0.05))
        self.play(FadeIn(pcap, shift=DOWN * 0.05))

        # 粉末越来越像
        self.at(12.12)
        self.play(p1.animate.shift(RIGHT * 1.4 + UP * 0.2),
                  p2.animate.shift(LEFT * 1.4 + UP * 0.2), run_time=0.9)
        like = t("同一张方子 → 粉末越来越像 → 近义词挤在一起", 30, GREEN)
        fit(like, 0.85)
        like.next_to(pcap, DOWN, buff=0.9)
        self.play(FadeIn(like, shift=DOWN * 0.05), run_time=0.6)

        # 药柜是机器
        self.at(18.18)
        m1 = t("倒药 = 前向传播", 30, CYAN)
        m2 = t("按「配得好不好」调配方 = 反向传播", 30, GREEN, "BOLD")
        mach = VGroup(m1, m2).arrange(DOWN, buff=0.4).next_to(like, DOWN, buff=0.8)
        self.play(FadeIn(m1, shift=DOWN * 0.05), FadeIn(m2, shift=DOWN * 0.05))

        # 金句
        self.at(24.81)
        gold = t("语义不是规则，是几百万张方子「用」出来的", 32, YELL, "BOLD")
        fit(gold, 0.85)
        gold.next_to(mach, DOWN, buff=0.75)
        self.play(FadeIn(gold, scale=0.9), run_time=0.8)
        self.pad_to_voice()


# ---------------- S6 余弦相似度 ----------------
class S6(_Base):
    def construct(self):
        self.footer()
        head = t("余弦相似度", 40, YELL, "BOLD").to_edge(UP, buff=1.2)
        self.play(FadeIn(head, shift=DOWN * 0.05))

        # 页1：三个场景箭头对
        self.at(4.20)
        g1 = VGroup(Arrow(ORIGIN, RIGHT * 1.4, color=GREEN, stroke_width=5, buff=0.1),
                    Arrow(UP * 0.25, RIGHT * 1.4 + UP * 0.25, color=GREEN, stroke_width=5, buff=0.1))
        g2 = VGroup(Arrow(ORIGIN, RIGHT * 1.4, color=MUTED, stroke_width=5, buff=0.1),
                    Arrow(ORIGIN, UP * 1.4, color=MUTED, stroke_width=5, buff=0.1))
        g3 = VGroup(Arrow(ORIGIN, RIGHT * 1.4, color=RED, stroke_width=5, buff=0.1),
                    Arrow(ORIGIN, LEFT * 1.4, color=RED, stroke_width=5, buff=0.1))
        labs = [VGroup(t("方向一致 · cos=1", 24, GREEN), t("猫 & 猫咪", 22, MUTED)).arrange(DOWN, buff=0.2),
                VGroup(t("互相垂直 · cos=0", 24, MUTED), t("猫 & 汽车", 22, MUTED)).arrange(DOWN, buff=0.2),
                VGroup(t("完全相反 · cos=−1", 24, RED), t("", 22, MUTED)).arrange(DOWN, buff=0.2)]
        trio = VGroup()
        for g, lb in zip([g1, g2, g3], labs):
            trio.add(VGroup(g, lb).arrange(DOWN, buff=0.35))
        trio.arrange(RIGHT, buff=0.8)
        fit(trio, 0.85)
        trio.next_to(head, DOWN, buff=1.6)
        trio_cap = t("夹角越小 → 意思越近", 26, WHITE).next_to(trio, DOWN, buff=1.2)
        self.play(*[FadeIn(g, shift=DOWN * 0.05) for g in trio], run_time=0.9)
        self.play(FadeIn(trio_cap, shift=DOWN * 0.05), run_time=0.6)

        # 页2：欧式距离问题
        self.at(13.78)
        self.play(FadeOut(VGroup(trio, trio_cap), shift=UP * 0.05), run_time=0.4)
        q = t("为什么不用欧式距离？", 36, WHITE).next_to(head, DOWN, buff=0.9)
        self.play(FadeIn(q, shift=DOWN * 0.05))
        long_a = Arrow(ORIGIN, RIGHT * 2.0, color=RED, stroke_width=8, buff=0.1)
        short_a = Arrow(ORIGIN, RIGHT * 0.9, color=GREEN, stroke_width=8, buff=0.1)
        rows_v = VGroup(long_a, short_a).arrange(DOWN, buff=0.6).next_to(q, DOWN, buff=0.5)
        l1 = t("「的」· 高频 → 模长偏大", 26, RED).next_to(long_a, UP, buff=0.15)
        l2 = t("「开心」· 低频 → 模长短", 26, GREEN).next_to(short_a, UP, buff=0.15)
        self.play(Create(long_a), FadeIn(l1), run_time=0.7)
        self.play(Create(short_a), FadeIn(l2), run_time=0.7)
        dnote = t("欧式距离下，「的」和谁都远", 30, WHITE).next_to(rows_v, DOWN, buff=0.5)
        self.play(FadeIn(dnote, shift=DOWN * 0.05))

        # cos 对比
        self.at(21.05)
        bar1 = Rectangle(width=1.1, height=2.4, color=GREEN, fill_color=GREEN, fill_opacity=0.6)
        bar2 = Rectangle(width=1.1, height=0.7, color=RED, fill_color=RED, fill_opacity=0.6)
        bg = VGroup(bar1, bar2).arrange(RIGHT, buff=1.4).next_to(dnote, DOWN, buff=0.5)
        lb1 = t("cos(开心, 高兴)", 26, GREEN).next_to(bar1, UP, buff=0.15)
        lb2 = t("cos(开心, 汽车)", 26, RED).next_to(bar2, UP, buff=0.15)
        cmp = t("明显更高 → 语义更近", 30, WHITE).next_to(bg, DOWN, buff=0.5)
        self.play(GrowFromEdge(bar1, DOWN), FadeIn(lb1), run_time=0.6)
        self.play(GrowFromEdge(bar2, DOWN), FadeIn(lb2), run_time=0.6)
        self.play(FadeIn(cmp, shift=DOWN * 0.05))

        # 邻居
        self.at(27.37)
        nb = VGroup(dot_label("苹果手机", GREEN, 26), dot_label("iPhone 16 Pro", GREEN, 26)).arrange(RIGHT, buff=0.6)
        nb.next_to(cmp, DOWN, buff=0.4)
        nbcap = t("嵌入空间里，它们是邻居", 30, GREEN, "BOLD").next_to(nb, DOWN, buff=0.3)
        self.play(FadeIn(nb, shift=DOWN * 0.05))
        self.play(FadeIn(nbcap, scale=0.9), run_time=0.7)
        self.pad_to_voice()


# ---------------- S7 Word2Vec ----------------
class S7(_Base):
    def construct(self):
        self.footer()
        head = t("2013 · Word2Vec", 40, YELL, "BOLD").to_edge(UP, buff=1.2)
        self.play(FadeIn(head, shift=DOWN * 0.05))

        # 页1：提出者 + 完形填空
        self.at(1.99)
        card = boxed("Tomas Mikolov · Google · 2013", 4.2, 0.9, CYAN, 26)
        card.next_to(head, DOWN, buff=1.5)
        w2v = t("Word2Vec", 44, YELL, "BOLD").next_to(card, DOWN, buff=0.7)
        self.play(FadeIn(card, shift=DOWN * 0.05))
        self.play(FadeIn(w2v, shift=DOWN * 0.05))

        blank_words = ["今天", "天气", "？", "适合", "出去玩"]
        blanks = VGroup()
        for wd in blank_words:
            blanks.add(boxed(wd, 1.0 if wd != "？" else 0.7, 0.8, YELL if wd == "？" else CYAN, 24))
        blanks.arrange(RIGHT, buff=0.15).next_to(w2v, DOWN, buff=1.2)
        blank_cap = t("完形填空：遮掉中间的词，用上下文猜", 28, WHITE)
        fit(blank_cap, 0.85)
        blank_cap.next_to(blanks, DOWN, buff=1.0)
        self.play(*[FadeIn(b, shift=DOWN * 0.05) for b in blanks], run_time=0.8)
        self.play(FadeIn(blank_cap, shift=DOWN * 0.05))

        # 猜着猜着就学会了
        self.at(12.29)
        learned = t("猜着猜着，就学会了语义", 36, GREEN, "BOLD").next_to(blank_cap, DOWN, buff=1.3)
        self.play(FadeIn(learned, scale=0.9), run_time=0.7)

        # 页2：语义算术
        self.at(13.95)
        self.play(FadeOut(VGroup(card, w2v, blanks, blank_cap, learned), shift=UP * 0.05), run_time=0.4)
        arith_head = t("最轰动的：语义算术", 32, WHITE).next_to(head, DOWN, buff=1.5)
        eq1 = VGroup(t("vec(国王) − vec(男人) + vec(女人) ≈ ", 30, WHITE),
                     t("vec(女王)", 30, YELL, "BOLD")).arrange(RIGHT, buff=0)
        fit(eq1, 0.9)
        eq1.next_to(arith_head, DOWN, buff=0.8)
        eq2 = t("不是人工规则，是模型从海量文本自动学到的", 26, MUTED)
        fit(eq2, 0.85)
        eq2.next_to(eq1, DOWN, buff=0.9)
        self.play(FadeIn(arith_head, shift=DOWN * 0.05))
        self.play(FadeIn(eq1, shift=DOWN * 0.05), run_time=0.8)
        self.play(FadeIn(eq2, shift=DOWN * 0.05))

        # 页3：一词一向量 vs 上下文
        self.at(22.25)
        self.play(FadeOut(VGroup(arith_head, eq1, eq2), shift=UP * 0.05), run_time=0.4)
        left_head = t("Word2Vec：一词一向量", 28, RED)
        apple = boxed("苹果", 1.6, 1.0, RED, 32)
        fix = t("固定身份证", 24, MUTED).next_to(apple, DOWN, buff=0.5)
        left = VGroup(left_head, apple, fix).arrange(DOWN, buff=0.6)
        right_head = t("大模型：上下文嵌入", 28, GREEN)
        ctx1 = boxed("吃苹果 → 向量 A", 2.6, 0.9, GREEN, 24)
        ctx2 = boxed("苹果发布会 → 向量 B", 3.2, 0.9, CYAN, 24)
        right = VGroup(right_head, ctx1, ctx2).arrange(DOWN, buff=0.5)
        split = VGroup(left, right).arrange(RIGHT, buff=0.7)
        fit(split, 0.88)
        split.next_to(head, DOWN, buff=1.5)
        self.play(FadeIn(left, shift=DOWN * 0.05), run_time=0.7)
        self.play(FadeIn(right, shift=DOWN * 0.05), run_time=0.7)
        clothes = t("同一个词，不同场合，穿不同的衣服", 30, WHITE)
        fit(clothes, 0.85)
        clothes.next_to(split, DOWN, buff=1.4)
        self.play(FadeIn(clothes, shift=DOWN * 0.05), run_time=0.7)
        self.pad_to_voice()


# ---------------- S8 三步总结 + 品牌尾卡 ----------------
class S8(_Base):
    def construct(self):
        self.footer()
        head = t("三步总结", 40, YELL, "BOLD").to_edge(UP, buff=1.2)
        self.play(FadeIn(head, shift=DOWN * 0.05))

        # ① 分词
        self.at(3.88)
        s1 = VGroup(t("①", 40, YELL, "BOLD"), boxed("分词器切 token，给编号", 4.0, 0.9, CYAN, 28)
                    ).arrange(RIGHT, buff=0.4)
        s1.next_to(head, DOWN, buff=1.5)
        self.play(FadeIn(s1, shift=DOWN * 0.05), run_time=0.6)

        # ② 嵌入矩阵
        self.at(7.78)
        s2 = VGroup(t("②", 40, YELL, "BOLD"), boxed("嵌入矩阵：129,280 × 7,168", 4.6, 0.9, CYAN, 28)
                    ).arrange(RIGHT, buff=0.4)
        s2.next_to(s1, DOWN, buff=1.2)
        self.play(FadeIn(s2, shift=DOWN * 0.05), run_time=0.6)

        # ③ 反向传播
        self.at(12.59)
        s3 = VGroup(t("③", 40, YELL, "BOLD"), boxed("反向传播调整坐标", 3.4, 0.9, CYAN, 28)
                    ).arrange(RIGHT, buff=0.4)
        s3.next_to(s2, DOWN, buff=1.2)
        d_near = VGroup(*[Dot(color=GREEN, radius=0.09) for _ in range(3)]).arrange(RIGHT, buff=0.15)
        d_far = Dot(color=RED, radius=0.09)
        dots = VGroup(d_near, d_far).arrange(RIGHT, buff=1.6).next_to(s3, DOWN, buff=1.1)
        self.play(FadeIn(s3, shift=DOWN * 0.05), run_time=0.6)
        self.play(FadeIn(d_near, shift=DOWN * 0.05), FadeIn(d_far, shift=DOWN * 0.05), run_time=0.7)
        dot_cap = t("意思近的靠拢 · 无关的拉远", 28, WHITE).next_to(dots, DOWN, buff=0.9)
        self.play(FadeIn(dot_cap, shift=DOWN * 0.05))

        # 金句 + 三步速览
        self.at(16.91)
        self.play(FadeOut(VGroup(s1, s2, s3, dots, dot_cap), shift=UP * 0.05), run_time=0.4)
        gold = t("这不是人设计的，是「用」出来的", 36, YELL, "BOLD").next_to(head, DOWN, buff=1.8)
        recap = t("① 分词 → ② 嵌入矩阵 → ③ 反向传播", 26, MUTED).next_to(gold, DOWN, buff=1.4)
        self.play(FadeIn(gold, scale=0.9), run_time=0.8)
        self.play(FadeIn(recap, shift=DOWN * 0.05), run_time=0.6)

        # 品牌尾卡
        self.at(20.59)
        self.play(FadeOut(VGroup(head, gold, recap), shift=UP * 0.05), run_time=0.4)
        logo = ImageMobject("avatar-sjai-round.png")
        logo.scale_to_fit_width(2.9)
        logo.move_to(UP * config.frame_height * 0.12)
        follow = VGroup(
            t("关注「数解AI」", 44, YELL, "BOLD"),
            t("《词嵌入为什么让AI懂\u201c苹果\u201d？\n5万个0变坐标》", 24, WHITE, "BOLD"),
            t("查看公众号文章 · 图文全解", 24, GREEN),
            t("下一篇：位置编码——词序一错，意思全变", 22, MUTED),
        ).arrange(DOWN, buff=0.35)
        follow.next_to(logo, DOWN, buff=0.7)
        self.play(FadeIn(logo, scale=0.9), run_time=0.9)
        self.play(FadeIn(follow, scale=0.85), run_time=0.8)
        self.wait(1.2)
        self.pad_to_voice()


# ---------------- 封面（无配音，底部放公众号 logo） ----------------
class Cover(Scene):
    """封面帧：系列标签 + 主/副标题 + 语义空间视觉 + 底部公众号 logo。
    渲染：python3 -m manim render -qm -s --disable_caching scenes.py Cover
    """
    def construct(self):
        # 底部：公众号 logo（用户要求放封面下方）
        logo = ImageMobject("avatar-sjai-round.png")
        logo.scale_to_fit_width(2.5)
        logo.to_edge(DOWN, buff=0.8)

        # 系列标签 → 主标题 → 副标题（锚点链）
        series = t("大模型原理 · 第 2 篇", 26, CYAN).to_edge(UP, buff=1.4)
        title = t("词嵌入：5万个0变坐标", 54, YELL, "BOLD").next_to(series, DOWN, buff=0.55)
        subtitle = t("AI 凭什么懂「苹果」？", 34, WHITE).next_to(title, DOWN, buff=0.35)

        # 关键视觉：语义空间两簇（本片最有记忆点的元素）
        near = VGroup(dot_label("苹果手机", GREEN), dot_label("iPhone 16 Pro", GREEN),
                      dot_label("苹果", GREEN)).arrange(RIGHT, buff=0.5)
        far = VGroup(dot_label("汽车", MUTED), dot_label("苹果醋", MUTED)).arrange(RIGHT, buff=0.5)
        stage = VGroup(near, far).arrange(RIGHT, buff=2.2)
        fit(stage, 0.88)
        stage.next_to(subtitle, DOWN, buff=1.4)
        ring = Ellipse(width=near.width + 0.9, height=near.height + 0.7,
                       color=GREEN, stroke_width=2).move_to(near)
        cap = t("意思近的，坐标挨得近", 26, GREEN).next_to(stage, DOWN, buff=0.8)

        self.add(logo, series, title, subtitle, stage, ring, cap)


if __name__ == "__main__":
    pass
