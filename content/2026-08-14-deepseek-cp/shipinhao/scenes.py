#!/usr/bin/env python3
"""《上下文并行：1M序列为什么切了会坏？》视频号 Manim 动画（竖屏 1080×1920）

8 个场景 S1-S8，与 storyboard.md 一一对应。
布局规范（硬性）：VGroup 原子化 + 锚点链 + 安全区 + 比例坐标，禁止裸魔法数字定位。
用法：
  python3 -m manim -qm scenes.py S1 S2 S3 S4 S5 S6 S7 S8
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

# 每个场景的配音时长（ffprobe 实测），渲染时长 = 配音 + 缓冲
VOICE_DUR = {"S1": 16.64, "S2": 27.36, "S3": 22.08, "S4": 22.56,
             "S5": 25.76, "S6": 22.24, "S7": 27.36, "S8": 27.36}
TAIL = 2.5  # 段尾缓冲（build 会截到 0.1s）

# 安全区（画布比例坐标）：上避标题、下避 footer/字幕、左右避边
SAFE_TOP = config.frame_height / 2 - 1.5
SAFE_BOTTOM = -config.frame_height / 2 + 1.6
SAFE_X = config.frame_width / 2 - 0.4


def t(text: str, size: float = 34, color: str = WHITE, weight: str = "NORMAL") -> Text:
    return Text(text, font=FONT, font_size=size, color=color, weight=weight)


class _Base(Scene):
    scene_dur = 12.0

    def setup(self):
        self.scene_dur = VOICE_DUR[self.__class__.__name__] + TAIL

    def pad_to_voice(self):
        """末尾补齐等待，使场景总时长 = 配音时长 + TAIL 缓冲。"""
        elapsed = self.time
        target = self.scene_dur
        if target > elapsed:
            self.wait(target - elapsed)

    def footer(self, text: str = "数解AI · DeepSeek 技术解密"):
        f = t(text, 20, MUTED).to_edge(DOWN, buff=1.15)
        self.add(f)

    def fit_width(self, mob, frac: float = 0.8):
        """长内容限宽：不超过画布宽的 frac，防越界截断。"""
        return mob.set_width(config.frame_width * frac)


def seq_bar(n_seg: int = 8, color: str = CYAN) -> VGroup:
    """一条序列长条，切成 n_seg 段。返回 VGroup（seg0..segN-1）。"""
    segs = VGroup()
    for _ in range(n_seg):
        segs.add(Rectangle(height=0.6, width=1.0, color=color,
                           fill_color=color, fill_opacity=0.18))
    segs.arrange(RIGHT, buff=0)
    return segs


def gpu_rack(n: int = 8) -> VGroup:
    """一排 GPU 方块（网格）。"""
    gpus = VGroup(*[Rectangle(height=0.8, width=0.66, color=GREEN,
                              fill_color=GREEN, fill_opacity=0.15) for _ in range(n)])
    gpus.arrange(RIGHT, buff=0.1)
    return gpus


# ---------------- S1 开场钩子 ----------------
class S1(_Base):
    def construct(self):
        self.footer()
        title = t("上下文并行 · CP", 42, YELL, "BOLD").to_edge(UP, buff=1.2)
        sub = t("1M token 的序列，切给 8 张 GPU", 28, WHITE).next_to(title, DOWN, buff=0.35)
        self.play(FadeIn(title, shift=DOWN * 0.3), FadeIn(sub))

        # 序列条 + 指向 GPU 的箭头 + GPU 排：整体组一个 stage
        bar = seq_bar().set_width(config.frame_width * 0.75)
        gpus = gpu_rack().set_width(config.frame_width * 0.75)
        gpus.next_to(bar, DOWN, buff=0.5)
        arrows = VGroup(*[Arrow(bar[i].get_bottom(), gpus[i].get_top(),
                                color=MUTED, buff=0.08, stroke_width=3) for i in range(8)])
        stage = VGroup(bar, gpus, arrows)
        stage.next_to(sub, DOWN, buff=0.8)
        self.play(Create(bar), run_time=1.0)
        self.play(FadeIn(gpus, shift=UP * 0.3), run_time=0.9)
        self.play(*[Create(a) for a in arrows], run_time=0.8)

        # 切蛋糕隐喻 → 回答
        cake = t("听起来像切蛋糕：切 8 块，每人一块", 30, WHITE).next_to(stage, DOWN, buff=0.7)
        ans = t("V4 技术报告：一切就坏", 40, RED, "BOLD").next_to(cake, DOWN, buff=0.6)
        self.play(FadeIn(cake, shift=UP * 0.2))
        self.play(FadeIn(ans, scale=0.9), run_time=0.9)
        self.wait(1.0)
        self.pad_to_voice()


# ---------------- S2 显存账 ----------------
class S2(_Base):
    def construct(self):
        self.footer()
        head = t("为什么必须切：3.5TB 的显存账", 36, YELL, "BOLD").to_edge(UP, buff=1.2)
        self.play(FadeIn(head, shift=DOWN * 0.3))

        # 公式三行
        f1 = t("Q = 10⁶ × 7168 × 2B ≈ 14.3 GB", 30, WHITE)
        f2 = t("单层注意力留 Q、K、V：≈ 57 GB", 30, WHITE)
        f3 = t("V4 共 61 层：57 × 61 ≈ 3.5 TB", 34, RED, "BOLD")
        block = VGroup(f1, f2, f3).arrange(DOWN, buff=0.5).next_to(head, DOWN, buff=0.9)
        for f in block:
            self.play(FadeIn(f, shift=UP * 0.2), run_time=0.8)

        # H800 对比
        gpu = Rectangle(height=0.7, width=3.2, color=GREEN, fill_color=GREEN, fill_opacity=0.15)
        gl = t("一块 H800：80 GB", 28, GREEN)
        ggroup = VGroup(gpu, gl).next_to(block, DOWN, buff=0.8)
        self.play(FadeIn(ggroup))

        vs = t("差了约 44 倍", 40, RED, "BOLD").next_to(ggroup, DOWN, buff=0.7)
        self.play(FadeIn(vs, scale=0.9), run_time=0.8)

        # Flash Attention 澄清
        fa1 = t("Flash Attention 只压 T×T 分数矩阵", 26, MUTED)
        fa2 = t("Q、K、V 本身是 O(T)，一分没少", 26, MUTED)
        fa = VGroup(fa1, fa2).arrange(DOWN, buff=0.3).next_to(vs, DOWN, buff=0.7)
        self.play(FadeIn(fa))

        concl = t("CP 不是优化，是必须", 40, YELL, "BOLD").next_to(fa, DOWN, buff=0.8)
        self.play(FadeIn(concl, shift=UP * 0.2), run_time=0.8)
        self.wait(1.2)
        self.pad_to_voice()


# ---------------- S3 普通 CP 的两个假设 ----------------
class S3(_Base):
    def construct(self):
        self.footer()
        head = t("普通 CP 的切法：朴素成立", 36, YELL, "BOLD").to_edge(UP, buff=1.2)
        self.play(FadeIn(head, shift=DOWN * 0.3))

        bar = seq_bar(n_seg=4).set_width(config.frame_width * 0.6)
        bar.next_to(head, DOWN, buff=0.9)
        self.play(Create(bar))

        h1 = VGroup(
            t("假设 1", 26, CYAN, "BOLD"),
            t("本地 token 数 ≈ 本地 KV 数", 28, WHITE),
        ).arrange(RIGHT, buff=0.5)
        h2 = VGroup(
            t("假设 2", 26, CYAN, "BOLD"),
            t("边界好处理，补一补就行", 28, WHITE),
        ).arrange(RIGHT, buff=0.5)
        ring = t("Ring-Attention：KV 块击鼓传花", 28, GREEN)
        brk = t("但 V4 的压缩注意力：两个假设同时打破", 30, RED, "BOLD")
        content = VGroup(h1, h2, ring, brk).arrange(DOWN, buff=0.6).next_to(bar, DOWN, buff=0.8)
        for mob in (h1, h2):
            self.play(FadeIn(mob, shift=UP * 0.2))
        self.play(FadeIn(ring, shift=UP * 0.2))
        self.wait(0.4)
        self.play(FadeIn(brk, scale=0.9), run_time=0.9)
        self.wait(1.0)
        self.pad_to_voice()


# ---------------- S4 坏因 1：压缩后长度不齐 ----------------
class S4(_Base):
    def construct(self):
        self.footer()
        head = t("坏因 1：压缩后 KV 长度不齐", 36, RED, "BOLD").to_edge(UP, buff=1.2)
        self.play(FadeIn(head, shift=DOWN * 0.3))

        # packed 序列 A + B
        sa = Rectangle(height=0.6, width=4.6, color=CYAN, fill_color=CYAN, fill_opacity=0.18)
        sa_g = VGroup(sa, t("序列 A：1000 token", 22, CYAN)).arrange(DOWN, buff=0.15)
        sb = Rectangle(height=0.6, width=0.55, color=GREEN, fill_color=GREEN, fill_opacity=0.18)
        sb_g = VGroup(sb, t("序列 B：7 token", 22, GREEN)).arrange(DOWN, buff=0.15)
        seqs = VGroup(sa_g, sb_g).arrange(RIGHT, buff=1.0).next_to(head, DOWN, buff=0.8)
        self.fit_width(seqs, 0.8)  # 限宽防溢出
        self.play(FadeIn(seqs))

        note = t("每个序列按自己的边界独立压缩（m=4）", 26, WHITE).next_to(seqs, DOWN, buff=0.6)
        drop = self.fit_width(t("7 个凑不出 2 个完整块，尾部 3 个丢弃 → 只出 1 个压缩 KV", 26, RED))
        drop.next_to(note, DOWN, buff=0.5)
        self.play(FadeIn(note))
        self.play(FadeIn(drop, shift=UP * 0.2))

        # 8 个 rank 产出不齐
        heights = [0.9, 0.9, 0.55, 0.9, 0.7, 0.9, 0.45, 0.9]
        ranks = VGroup(*[Rectangle(height=h, width=0.42, color=YELL,
                                   fill_color=YELL, fill_opacity=0.55) for h in heights])
        ranks.arrange(RIGHT, buff=0.22).next_to(drop, DOWN, buff=0.6)
        cap = t("8 张卡产出的压缩 KV 数，彼此不等", 28, YELL, "BOLD").next_to(ranks, DOWN, buff=0.45)
        self.play(*[GrowFromEdge(b, DOWN) for b in ranks], run_time=1.2)
        self.play(FadeIn(cap))

        stuck = t("形状不齐 → all-gather 第一步就卡住", 30, RED, "BOLD").next_to(cap, DOWN, buff=0.6)
        self.play(FadeIn(stuck, scale=0.9))
        self.wait(1.0)
        self.pad_to_voice()


# ---------------- S5 坏因 2：窗口跨边界 ----------------
class S5(_Base):
    def construct(self):
        self.footer()
        head = t("坏因 2：压缩窗口跨边界", 36, RED, "BOLD").to_edge(UP, buff=1.2)
        self.play(FadeIn(head, shift=DOWN * 0.3))

        # m=4 的压缩块（k0..k3），红色虚线穿过
        blocks = VGroup(*[VGroup(Rectangle(height=0.55, width=0.7, color=WHITE,
                                           fill_color=WHITE, fill_opacity=0.15),
                                 t(f"k{i}", 20, WHITE)) for i in range(4)])
        blocks.arrange(RIGHT, buff=0.12)
        grp = Rectangle(height=1.0, width=blocks.width + 0.5, color=YELL,
                        fill_color=YELL, fill_opacity=0.05)
        block_grp = VGroup(grp, blocks)
        block_grp.next_to(head, DOWN, buff=0.9)
        self.play(FadeIn(grp), FadeIn(blocks))
        grp_l = t("一个压缩块：m=4 个连续 KV", 24, YELL).next_to(block_grp, DOWN, buff=0.4)
        self.play(FadeIn(grp_l))

        # rank 边界竖线（缩短到画布内，避免穿出顶部）
        bl = DashedLine(UP * 1.0, DOWN * 2.0, color=RED, dash_length=0.15)
        bl.move_to(blocks[1].get_center() + UP * 1.0)
        self.play(Create(bl), run_time=0.6)
        self.wait(0.3)

        sides = VGroup(
            t("左 rank：只有前半块", 24, CYAN),
            t("右 rank：只有后半块", 24, GREEN),
        ).arrange(RIGHT, buff=0.8)
        sides.next_to(grp_l, DOWN, buff=0.7)
        self.fit_width(sides, 0.75)  # 总宽 6.9→6.0 单位，防溢出画布被裁
        self.play(FadeIn(sides))
        none = t("任何一边都无法完成压缩", 30, RED, "BOLD").next_to(sides, DOWN, buff=0.7)
        self.play(FadeIn(none, scale=0.9))

        # 照片比喻
        photo = VGroup(
            t("照片 4 张一组进相册，边界切在两张中间", 24, WHITE),
            t("——谁都没拿到完整的一组", 24, WHITE),
        ).arrange(DOWN, buff=0.15).next_to(none, DOWN, buff=0.7)
        self.play(FadeIn(photo))
        self.wait(1.0)
        self.pad_to_voice()


# ---------------- S6 阶段 1：边界原料交换 ----------------
class S6(_Base):
    def construct(self):
        self.footer()
        head = t("阶段 1：先交换边界原料", 38, YELL, "BOLD").to_edge(UP, buff=1.2)
        self.play(FadeIn(head, shift=DOWN * 0.3))

        # rank r 与 rank r+1，r 末尾 m 个原料传给右邻居
        r0 = Rectangle(height=1.6, width=2.2, color=CYAN, fill_color=CYAN, fill_opacity=0.10)
        r0l = t("rank r", 26, CYAN, "BOLD")
        r0g = VGroup(r0, r0l).arrange(DOWN, buff=0.2)
        r1 = Rectangle(height=1.6, width=2.2, color=GREEN, fill_color=GREEN, fill_opacity=0.10)
        r1l = t("rank r+1", 26, GREEN, "BOLD")
        r1g = VGroup(r1, r1l).arrange(DOWN, buff=0.2)
        diagram = VGroup(r0g, r1g).arrange(RIGHT, buff=3.4)
        diagram.next_to(head, DOWN, buff=0.9)
        self.fit_width(diagram, 0.9)  # 限宽防溢出
        self.play(FadeIn(r0g), FadeIn(r1g))

        # 原料块：r0 右下角 → 箭头 → r1
        mat = VGroup(*[Rectangle(height=0.32, width=0.3, color=YELL,
                                 fill_color=YELL, fill_opacity=0.8) for _ in range(4)])
        mat.arrange(RIGHT, buff=0.06)
        mat.move_to(r0.get_bottom() + UP * 0.45)
        a = Arrow(r0.get_right() + DOWN * 0.4, r1.get_left() + DOWN * 0.4,
                  color=YELL, buff=0.15, stroke_width=5)
        self.play(FadeIn(mat, shift=DOWN * 0.2))
        self.play(Create(a), run_time=0.6)
        p1 = t("发原料", 24, YELL, "BOLD").next_to(a, UP, buff=0.3)
        self.play(FadeIn(p1))
        self.wait(0.4)

        p2 = t("右邻居拼成完整块 → 压一次", 28, WHITE).next_to(diagram, DOWN, buff=0.7)
        why = t("不传半成品：跨边界块在左边压不出合法输出", 26, MUTED).next_to(p2, DOWN, buff=0.5)
        kb = t("通信量：与序列长度无关，CSA 层仅约 2 KB", 28, GREEN, "BOLD").next_to(why, DOWN, buff=0.5)
        self.fit_width(kb, 0.9)  # 限宽防溢出
        self.play(FadeIn(p2))
        self.play(FadeIn(why))
        self.play(FadeIn(kb, shift=UP * 0.2), run_time=0.8)
        self.wait(1.0)
        self.pad_to_voice()


# ---------------- S7 阶段 2：all-gather + select-and-pad ----------------
class S7(_Base):
    def construct(self):
        self.footer()
        head = t("阶段 2：all-gather + select-and-pad", 34, YELL, "BOLD").to_edge(UP, buff=1.2)
        self.fit_width(head, 0.85)  # 标题含长英文，限宽防溢出
        self.play(FadeIn(head, shift=DOWN * 0.3))

        def row(entries, col):
            boxes = VGroup()
            for e in entries:
                is_pad = e == "PAD"
                color = col if not is_pad else MUTED
                b = Rectangle(height=0.62, width=0.72, color=color, fill_color=color,
                              fill_opacity=0.75 if not is_pad else 0.35)
                lab = t(e, 20, "#16213E" if not is_pad else WHITE, "BOLD")
                boxes.add(VGroup(b, lab))
            boxes.arrange(RIGHT, buff=0.12)
            return boxes

        r0row = row(["C0", "PAD", "PAD", "PAD"], YELL)
        r0g = VGroup(t("rank 0：valid_count = 1", 22, YELL), r0row).arrange(RIGHT, buff=0.5)
        r1row = row(["C1", "C2", "C3", "PAD"], GREEN)
        r1g = VGroup(t("rank 1：valid_count = 3", 22, GREEN), r1row).arrange(RIGHT, buff=0.5)
        diagram = VGroup(r0g, r1g).arrange(DOWN, buff=0.55).next_to(head, DOWN, buff=0.8)
        self.fit_width(diagram, 0.9)  # 限宽防溢出
        self.play(FadeIn(r0g, shift=UP * 0.2), FadeIn(r1g, shift=UP * 0.2))
        self.wait(0.3)

        pad_note = t("每卡先 pad 到统一上界，再 all-gather", 28, WHITE).next_to(diagram, DOWN, buff=0.6)
        hole = t("gather 出来的 blob 有洞——padding 会污染注意力", 26, RED).next_to(pad_note, DOWN, buff=0.5)
        self.fit_width(hole, 0.9)  # 限宽防溢出
        self.play(FadeIn(pad_note))
        self.wait(0.4)
        self.play(FadeIn(hole, shift=UP * 0.2))

        steps = VGroup(
            t("① 去 padding（按 valid_count）", 26, CYAN),
            t("② 尾对齐（padding 集中到尾部）", 26, GREEN),
            t("③ 稀疏重排（CSA sparse 按 top-k）", 26, MUTED),
        ).arrange(DOWN, buff=0.35).next_to(hole, DOWN, buff=0.6)
        for s in steps:
            self.play(FadeIn(s, shift=UP * 0.15), run_time=0.5)

        outrow = row(["C0", "C1", "C2", "C3"], YELL)
        outg = VGroup(t("select-and-pad 后", 22, WHITE), outrow).arrange(RIGHT, buff=0.5)
        outg.next_to(steps, DOWN, buff=0.6)
        self.fit_width(outg, 0.9)  # 限宽防溢出
        self.play(FadeOut(r0g, r1g, shift=DOWN * 0.2), FadeIn(outg, shift=UP * 0.2))
        ok = t("一个 kernel 合并，数据只过一次内存总线", 24, GREEN).next_to(outg, DOWN, buff=0.45)
        self.play(FadeIn(ok))
        self.wait(1.0)
        self.pad_to_voice()


# ---------------- S8 通信账 + 实验 + 品牌尾卡 ----------------
class S8(_Base):
    def construct(self):
        self.footer("数解AI · DeepSeek 技术解密")
        head = t("压缩比直接兑换成通信节省", 34, YELL, "BOLD").to_edge(UP, buff=1.2)
        self.play(FadeIn(head, shift=DOWN * 0.3))

        # 9MB vs 72MB 条形
        bars = VGroup()
        for lab, v, col in [("压缩后 9 MB", 9, GREEN), ("不压缩 72 MB", 72, RED)]:
            b = Rectangle(height=v / 72 * 4.0, width=0.9, color=col,
                          fill_color=col, fill_opacity=0.6)
            bars.add(VGroup(b, t(lab, 24, col, "BOLD").next_to(b, UP, buff=0.15)))
        bars.arrange(RIGHT, buff=1.6).next_to(head, DOWN, buff=1.1)
        self.play(*[GrowFromEdge(b[0], DOWN) for b in bars], run_time=1.2)
        self.play(*[FadeIn(b[1]) for b in bars])
        save = t("省约 8 倍 · NVLink 上仅 0.02 ms，可被计算藏住", 26, WHITE).next_to(bars, DOWN, buff=0.7)
        self.play(FadeIn(save))

        # 实验结论
        exp = VGroup(
            t("模拟器（8 ranks × packed 序列）：", 26, MUTED),
            t("单卡基准 277 · 朴素 CP 276（缺 1）· 两阶段 277 ✅", 28, GREEN, "BOLD"),
        ).arrange(DOWN, buff=0.3).next_to(save, DOWN, buff=0.6)
        self.play(FadeIn(exp, shift=UP * 0.2))
        self.wait(0.4)

        concl = t("注意力公式变了，并行策略不能原封不动", 30, YELL, "BOLD").next_to(exp, DOWN, buff=0.6)
        self.play(FadeIn(concl, scale=0.9), run_time=0.8)
        self.wait(0.6)

        # 切品牌卡：建议淡出
        self.play(*[FadeOut(m, shift=DOWN * 0.25) for m in (head, bars, save, exp, concl)], run_time=0.7)

        logo = ImageMobject("avatar-sjai-round.png")
        logo.scale_to_fit_width(3.6)
        logo.move_to(UP * config.frame_height * 0.06)  # 画布比例坐标（锚点）
        follow = VGroup(
            t("关注「数解AI」", 44, YELL, "BOLD"),
            t("《上下文并行：1M序列为什么切了会坏？》", 26, WHITE, "BOLD"),
            t("查看公众号文章 · 图文全解", 24, GREEN),
            t("下一篇拆 DualPipe 与 DeepEP", 22, MUTED),
        ).arrange(DOWN, buff=0.4)
        follow.next_to(logo, DOWN, buff=0.8)  # 锚点链：跟随 logo
        self.play(FadeIn(logo, scale=0.9), run_time=0.9)
        self.play(FadeIn(follow, scale=0.85), run_time=0.8)
        self.wait(1.0)
        self.pad_to_voice()


# ---------------- 封面（视频号竖屏封面，-s 渲染单帧） ----------------
class Cover(Scene):
    """封面帧：品牌条 + 系列标签 + 主/副标题 + 关键视觉。
    渲染：python3 -m manim render -qm -s scenes.py Cover
    输出：media/images/scenes/Cover.png（1080×1920）
    """
    def construct(self):
        # 底部品牌条（锚点）
        brand = t("数解AI · DeepSeek 技术解密", 20, MUTED).to_edge(DOWN, buff=1.15)

        # 系列标签 → 主标题 → 副标题（锚点链）
        series = t("DeepSeek 技术解密 · 解密篇", 26, CYAN).to_edge(UP, buff=1.4)
        title = t("上下文并行", 54, YELL, "BOLD").next_to(series, DOWN, buff=0.55)
        subtitle = t("1M 序列为什么切了会坏？", 34, WHITE).next_to(title, DOWN, buff=0.35)

        # 关键视觉：1M 序列切 8 段 → 8 张 GPU
        bar = seq_bar().set_width(config.frame_width * 0.75)
        gpus = gpu_rack().set_width(config.frame_width * 0.75)
        gpus.next_to(bar, DOWN, buff=0.5)
        arrows = VGroup(*[Arrow(bar[i].get_bottom(), gpus[i].get_top(),
                                color=MUTED, buff=0.08, stroke_width=3) for i in range(8)])
        stage = VGroup(bar, gpus, arrows).next_to(subtitle, DOWN, buff=1.3)

        self.add(brand, series, title, subtitle, stage)


if __name__ == "__main__":
    pass
