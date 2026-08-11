#!/usr/bin/env python3
"""《FP4量化：4位数字怎么做到无损》视频号 Manim 动画（竖屏 1080×1920）

8 个场景 S1-S8，与 storyboard.md 一一对应。
布局规范（2026-08-11 分页模式 v3，用户反馈 v2 内容太少画面太空）：
  - 每场景 2-3 页（合并单元素页：S1/S2/S3/S7 变 2 页），每页 3-5 个元素
  - 元素大字号：head 50-56、正文 38-44、强调 48-60、图表 1.3x，间距 buff 0.8-1.1
  - 目标：每页内容垂直占屏 ≥40%（内容最低点距底 ≤800px），且 ≥385px（两行字幕上方）
  - 动作挂 at(t) 台词节点，覆盖 ≥80% 配音时长
用法（在 shipinhao/ 目录下执行）：
  python3 -m manim render -qm scenes.py S1 S2 S3 S4 S5 S6 S7 S8
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

# 每个场景的配音时长（ffprobe 实测，2026-08-11 MiniMax 重配音），渲染时长 = 配音 + 缓冲
VOICE_DUR = {"S1": 27.99, "S2": 23.20, "S3": 34.81, "S4": 32.89,
             "S5": 30.66, "S6": 36.82, "S7": 32.11, "S8": 30.97}
TAIL = 2.5  # 段尾缓冲（build 会截到 0.1s）

# 安全区（画布比例坐标）：上避标题、下避 footer/字幕、左右避边
SAFE_TOP = config.frame_height / 2 - 1.5
SAFE_BOTTOM = -config.frame_height / 2 + 2.5
SAFE_X = config.frame_width / 2 - 0.4


def t(text: str, size: float = 34, color: str = WHITE, weight: str = "NORMAL") -> Text:
    return Text(text, font=FONT, font_size=size, color=color, weight=weight)


class _Base(Scene):
    scene_dur = 12.0

    def setup(self):
        self.scene_dur = VOICE_DUR[self.__class__.__name__] + TAIL

    def at(self, t: float):
        """推进到配音时间轴绝对时刻（动画动作挂到台词节点上）。"""
        self.wait(max(0.0, t - self.time))

    def next_page(self, old: VGroup, t: float, run_time: float = 0.5):
        """切页：淡出旧页（新页元素随后逐个 FadeIn）。"""
        self.at(t)
        self.play(FadeOut(old, shift=DOWN * 0.15), run_time=run_time)

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


def bit_chips(bits: str, labels: list[str], color: str = YELL) -> VGroup:
    """4 个位方块 + 下方标签（如 S E E M / 符号 指数 指数 尾数）。"""
    boxes = VGroup(*[Rectangle(height=1.3, width=1.3, color=color,
                               fill_color=color, fill_opacity=0.16) for _ in bits])
    boxes.arrange(RIGHT, buff=0.35)
    chars = VGroup(*[t(b, 50, color, "BOLD") for b in bits])
    for b, c in zip(boxes, chars):
        c.move_to(b)
    labs = VGroup(*[t(l, 30, MUTED) for l in labels])
    for b, l in zip(boxes, labs):
        l.next_to(b, DOWN, buff=0.6)
    return VGroup(boxes, chars, labs)


def num_chips(vals: list[str], color: str = CYAN, h: float = 1.1, w: float = 1.3) -> VGroup:
    """数字筹码行（如 0.5、1、1.5、2、3、4、6）。"""
    chips = VGroup()
    for v in vals:
        b = Rectangle(height=h, width=w, color=color,
                      fill_color=color, fill_opacity=0.16)
        chips.add(VGroup(b, t(v, 38, color, "BOLD").move_to(b)))
    chips.arrange(RIGHT, buff=0.25)
    return chips


# ---------------- S1 开场钩子：账本游戏（2 页） ----------------
class S1(_Base):
    def construct(self):
        self.footer()
        head = t("FP4 量化 · 先做个游戏", 52, YELL, "BOLD").to_edge(UP, buff=1.2)
        self.fit_width(head, 0.96)
        self.add(head)

        # 页1：账本数字 + 误差规则
        sub = t("账本上只能写这 7 个数：", 40, WHITE).next_to(head, DOWN, buff=1.2)
        nums = num_chips(["0.5", "1", "1.5", "2", "3", "4", "6"])
        self.fit_width(nums, 0.92)
        nums.next_to(sub, DOWN, buff=1.2)
        map_txt = t("0.8 只能写成 1 · 3.7 只能写成 4 → 最多带 25% 误差", 38, RED)
        self.fit_width(map_txt, 0.96)
        map_txt.next_to(nums, DOWN, buff=1.3)
        ledger = t("要拿这本账，记一亿个参数。你干不干？", 44, WHITE)
        self.fit_width(ledger, 0.94)
        ledger.next_to(map_txt, DOWN, buff=1.3)
        p1 = VGroup(sub, nums, map_txt, ledger)
        self.at(0.4)
        self.play(FadeIn(sub, shift=DOWN * 0.3))
        self.at(1.8)  # 台词「你的账本上…」
        self.play(FadeIn(nums, shift=UP * 0.2), run_time=0.9)
        self.at(8.6)  # 台词「0.8 只能写成 1…」
        self.play(FadeIn(map_txt, shift=UP * 0.2))
        self.at(14.6)  # 台词「要拿这本账…」
        self.play(FadeIn(ledger, shift=UP * 0.2))

        # 页2：DeepSeek 干了（爆点页 + 16 可选值网格）
        ds = t("反正我不干。但 DeepSeek 干了：1.6T 参数，全用 4 位", 48, GREEN, "BOLD")
        self.fit_width(ds, 0.96)
        ds.next_to(head, DOWN, buff=1.5)
        grid = VGroup(*[Rectangle(height=0.42, width=0.42, color=YELL,
                                  fill_color=YELL, fill_opacity=0.18) for _ in range(16)])
        grid.arrange_in_grid(rows=4, cols=4, buff=0.16)
        grid.next_to(ds, DOWN, buff=1.3)
        boom = t("16 个可选值，你跟我说无损？", 64, RED, "BOLD")
        self.fit_width(boom, 0.94)
        boom.next_to(grid, DOWN, buff=1.3)
        p2 = VGroup(ds, grid, boom)
        self.next_page(p1, 18.2)  # 台词「反正我不干…」
        self.at(18.8)
        self.play(FadeIn(ds, shift=UP * 0.2))
        self.at(21.5)  # 台词「16 个可选值…」前铺垫
        self.play(FadeIn(grid, scale=0.8), run_time=0.7)
        self.at(24.8)  # 台词「16 个可选值…」
        self.play(FadeIn(boom, scale=0.9), run_time=0.9)
        self.pad_to_voice()


# ---------------- S2 E2M1 格式解剖（2 页） ----------------
class S2(_Base):
    def construct(self):
        self.footer()
        head = t("E2M1：1 符号 + 2 指数 + 1 尾数", 50, YELL, "BOLD").to_edge(UP, buff=1.2)
        self.fit_width(head, 0.96)
        self.add(head)

        # 页1：位结构 + 7 个正数 + 动态范围
        bits = bit_chips("SEEM", ["符号", "指数", "指数", "尾数"])
        bits.next_to(head, DOWN, buff=1.0)
        nums = num_chips(["0.5", "1", "1.5", "2", "3", "4", "6"], h=1.0, w=1.2)
        self.fit_width(nums, 0.92)
        nums.next_to(bits, DOWN, buff=1.0)
        cap = t("能表示的正数，就这 7 个", 34, MUTED).next_to(nums, DOWN, buff=0.5)
        boom = t("最大的才 6？连 10 都装不下", 52, RED, "BOLD")
        self.fit_width(boom, 0.94)
        boom.next_to(cap, DOWN, buff=0.9)
        dyn = VGroup(
            t("动态范围 12 倍", 42, YELL, "BOLD"),
            t("精度比 FP8 糙 4 倍", 38, WHITE),
        ).arrange(RIGHT, buff=1.4)
        self.fit_width(dyn, 0.94)
        dyn.next_to(boom, DOWN, buff=0.9)
        p1 = VGroup(bits, nums, cap, boom, dyn)
        self.at(0.5)  # 台词「这个账本有个学名…」
        self.play(FadeIn(bits, shift=UP * 0.2), run_time=0.8)
        self.at(8.2)  # 台词「正数就 7 个…」
        self.play(FadeIn(nums, shift=UP * 0.2), FadeIn(cap))
        self.at(10.6)
        self.play(FadeIn(boom, scale=0.9), run_time=0.8)
        self.at(12.4)  # 台词「动态范围 12 倍…」
        self.play(FadeIn(dyn, shift=UP * 0.2))

        # 页2：32 元素共享 scale
        cells = VGroup(*[Rectangle(height=0.6, width=0.6, color=CYAN,
                                   fill_color=CYAN, fill_opacity=0.35) for _ in range(32)])
        cells.arrange_in_grid(rows=2, cols=16, buff=0.12)
        self.fit_width(cells, 0.88)
        sc = Rectangle(height=1.7, width=cells.width + 0.7, color=YELL,
                       fill_color=YELL, fill_opacity=0.06)
        sc.move_to(cells)
        sg = t("scale", 34, YELL, "BOLD").next_to(sc, DOWN, buff=0.7)
        struct = VGroup(sc, cells, sg)
        struct.next_to(head, DOWN, buff=1.5)
        key = t("32 个元素共享一个 2 的幂的 scale", 46, WHITE)
        self.fit_width(key, 0.96)
        key.next_to(struct, DOWN, buff=1.2)
        p2 = VGroup(struct, key)
        self.next_page(p1, 13.4)  # 台词「但关键在结构…」
        self.at(14.0)
        self.play(FadeIn(cells), run_time=0.7)
        self.at(15.6)
        self.play(FadeIn(sc), FadeIn(sg))
        self.at(17.2)
        self.play(FadeIn(key, shift=UP * 0.2), run_time=1.0)
        self.at(18.6)
        self.play(Indicate(key), run_time=0.8)
        self.pad_to_voice()


# ---------------- S3 STE 直通梯度（2 页） ----------------
class S3(_Base):
    def construct(self):
        self.footer()
        head = t("量化不可微，怎么训练？", 52, YELL, "BOLD").to_edge(UP, buff=1.2)
        self.fit_width(head, 0.96)
        self.add(head)

        # 页1：阶梯函数 + 梯度归零
        steps = VGroup(*[Rectangle(height=0.8, width=0.9, color=WHITE,
                                   fill_color=WHITE, fill_opacity=0.12) for _ in range(5)])
        steps.arrange(RIGHT, buff=0)
        for i in range(1, 5):
            steps[i].shift(UP * 0.8 * i)
        stg = VGroup(t("Q(W) 阶梯函数", 32, MUTED).next_to(steps, UP, buff=0.25), steps)
        stg.next_to(head, DOWN, buff=1.0)
        zero = t("导数 = 0", 44, RED, "BOLD").next_to(steps, DOWN, buff=0.8)
        dead = t("梯度归零 → 权重永不更新 → 训练当场死给你看", 38, RED)
        self.fit_width(dead, 0.96)
        dead.next_to(zero, DOWN, buff=0.8)
        p1 = VGroup(stg, zero, dead)
        self.at(0.5)  # 台词「量化不可微…」
        self.play(FadeIn(head, shift=DOWN * 0.3))
        self.at(3.2)  # 台词「量化是阶梯函数…」
        self.play(FadeIn(steps, shift=UP * 0.2), run_time=0.8)
        self.at(7.2)
        self.play(FadeIn(zero, scale=0.9))
        self.at(9.2)
        self.play(FadeIn(dead, shift=UP * 0.2))

        # 页2：STE 前向/反传 + 实验数据
        ste = t("STE：假装量化器不存在", 46, YELL, "BOLD").next_to(head, DOWN, buff=1.5)
        fw = VGroup(
            t("前向", 36, GREEN, "BOLD"),
            t("W → 量化 → 前向计算", 38, WHITE),
        ).arrange(RIGHT, buff=0.6)
        bw = VGroup(
            t("反传", 36, CYAN, "BOLD"),
            t("梯度原样穿墙，直通回 W", 38, WHITE),
        ).arrange(RIGHT, buff=0.6)
        paths = VGroup(fw, bw).arrange(DOWN, buff=0.7)
        self.fit_width(paths, 0.94)
        paths.next_to(ste, DOWN, buff=1.2)
        ok = t("严格说是错的，但它是 QAT 的事实标准", 36, MUTED)
        self.fit_width(ok, 0.96)
        ok.next_to(paths, DOWN, buff=1.2)
        exp = VGroup(
            t("实验：STE 0.993", 40, GREEN, "BOLD"),
            t("截断 6.866（纹丝不动）", 40, RED, "BOLD"),
            t("基线 0.951", 40, WHITE, "BOLD"),
        ).arrange(RIGHT, buff=0.7)
        self.fit_width(exp, 0.96)
        exp.next_to(ok, DOWN, buff=1.2)
        p2 = VGroup(ste, paths, ok, exp)
        self.next_page(p1, 11.8)  # 台词「STE 很粗暴…」
        self.at(12.4)
        self.play(FadeIn(ste, shift=UP * 0.2))
        self.at(13.8)
        self.play(FadeIn(fw, shift=UP * 0.15))
        self.at(16.2)  # 台词「反传假装量化器不存在…」
        self.play(FadeIn(bw, shift=UP * 0.15))
        self.at(20.6)  # 台词「严格说这是错的…」
        self.play(FadeIn(ok))
        self.at(26.2)  # 台词「实验里，截断那列…」
        self.play(FadeIn(exp, shift=UP * 0.2), run_time=0.9)
        self.at(28.6)
        self.play(Indicate(exp[0]), run_time=0.8)
        self.pad_to_voice()


# ---------------- S4 无损藏在回程（3 页） ----------------
class S4(_Base):
    def construct(self):
        self.footer()
        head = t("「无损」藏在回程里", 52, YELL, "BOLD").to_edge(UP, buff=1.2)
        self.fit_width(head, 0.96)
        self.add(head)

        # 页1：去程有损 / 回程无损
        note = t("先说明白：无损不是 FP4 不丢精度", 44, MUTED).next_to(head, DOWN, buff=1.5)
        lossy = VGroup(
            t("去程：master → FP4", 48, RED, "BOLD"),
            t("25% 精度，丢得明明白白", 44, RED),
        ).arrange(DOWN, buff=0.45)
        lossless = VGroup(
            t("回程：FP4 → FP8", 48, GREEN, "BOLD"),
            t("零信息损失", 44, GREEN),
        ).arrange(DOWN, buff=0.45)
        pair = VGroup(lossy, lossless).arrange(RIGHT, buff=2.0)
        self.fit_width(pair, 0.96)
        pair.next_to(note, DOWN, buff=1.5)
        p1 = VGroup(note, pair)
        self.at(0.4)  # 台词「「无损」藏在哪？」
        self.play(FadeIn(head, shift=DOWN * 0.3))
        self.at(2.6)  # 台词「先说明白：无损不是 FP4 不丢精度…」
        self.play(FadeIn(note, shift=UP * 0.2))
        self.at(6.8)
        self.play(FadeIn(lossy, shift=UP * 0.2), FadeIn(lossless, shift=UP * 0.2))

        # 页2：事实① 数轴
        f1h = t("事实 ①  FP4 能表示的数，FP8 全能精确表示", 38, WHITE, "BOLD")
        self.fit_width(f1h, 0.96)
        f1h.next_to(head, DOWN, buff=1.5)
        axis = Line(LEFT * 3.4, RIGHT * 3.4, color=MUTED, stroke_width=4)
        e4m3 = VGroup(*[Line(UP * 0.4, DOWN * 0.4, color=MUTED, stroke_width=3)
                        for _ in range(25)])
        e4m3.arrange(RIGHT, buff=0)
        e4m3.scale_to_fit_width(6.8)
        e2m1 = VGroup(*[Line(UP * 0.75, DOWN * 0.75, color=YELL, stroke_width=6)
                        for _ in [0.5, 1, 1.5, 2, 3, 4, 6]])
        e2m1.arrange(RIGHT, buff=0)
        e2m1.scale_to_fit_width(6.8 * 0.9)
        axg = VGroup(axis, e4m3, e2m1)
        axg.next_to(f1h, DOWN, buff=1.2)
        lab_a = t("E4M3：尾数 3 位，细到「八分之几」", 32, MUTED).next_to(axg, DOWN, buff=0.7)
        lab_b = t("E2M1：只会「半个、一个、一个半」", 32, YELL).next_to(lab_a, DOWN, buff=0.7)
        p2 = VGroup(f1h, axg, lab_a, lab_b)
        self.next_page(p1, 10.8)  # 台词「两个算术事实…」
        self.at(11.4)
        self.play(FadeIn(f1h, shift=UP * 0.2))
        self.at(12.6)
        self.play(Create(axis), run_time=0.4)
        self.at(13.8)
        self.play(FadeIn(e4m3), run_time=0.5)
        self.at(15.2)
        self.play(FadeIn(e2m1), run_time=0.5)
        self.at(16.6)
        self.play(FadeIn(lab_a), FadeIn(lab_b))

        # 页3：事实② + 结论（scale 阶梯装饰）
        f2h = t("事实 ②  scale 是 2 的幂：只移指数位，无新误差", 42, WHITE, "BOLD")
        self.fit_width(f2h, 0.98)
        f2h.next_to(head, DOWN, buff=1.5)
        lads = VGroup()
        for i, v in enumerate(["1", "2", "4", "8"]):
            b = Rectangle(height=0.45 + i * 0.4, width=0.85, color=CYAN,
                          fill_color=CYAN, fill_opacity=0.25)
            lads.add(VGroup(b, t(v, 30, CYAN, "BOLD").next_to(b, UP, buff=0.12)))
        lads.arrange(RIGHT, buff=0.3, aligned_edge=DOWN)
        self.fit_width(lads, 0.7)
        lads.next_to(f2h, DOWN, buff=1.2)
        boom = t("就这？我卡了两天没想通的「无损」，一句话就完了", 50, RED, "BOLD")
        self.fit_width(boom, 0.98)
        boom.next_to(lads, DOWN, buff=1.3)
        p3 = VGroup(f2h, lads, boom)
        self.next_page(p2, 19.0)  # 台词「scale 是 2 的幂…」
        self.at(19.6)
        self.play(FadeIn(f2h, shift=UP * 0.2))
        self.at(21.5)  # 台词「只移指数位…」
        self.play(FadeIn(lads, shift=UP * 0.2), run_time=0.8)
        self.at(30.4)  # 台词「就这？…一句话就完了」
        self.play(FadeIn(boom, scale=0.9), run_time=0.9)
        self.pad_to_voice()


# ---------------- S5 边界：两千倍（2 页） ----------------
class S5(_Base):
    def construct(self):
        self.footer()
        head = t("边界：scale 比值不能太悬殊", 50, YELL, "BOLD").to_edge(UP, buff=1.2)
        self.fit_width(head, 0.96)
        self.add(head)

        # 页1：E4M3 范围 + 公式推导
        rng = VGroup(
            t("E4M3 范围", 42, MUTED),
            t("最小 ≈ 0.016", 46, WHITE),
            t("最大 448", 46, WHITE),
        ).arrange(RIGHT, buff=0.8)
        self.fit_width(rng, 0.94)
        rng.next_to(head, DOWN, buff=1.5)
        f1 = t("v_max = 6·s_max ≤ 448", 48, WHITE)
        f2 = t("v_min = 0.5·s_min ≥ 2⁻⁶", 48, WHITE)
        f3 = t("⇒  s_max / s_min ≤ ≈2.4×10³（约两千倍）", 56, YELL, "BOLD")
        block = VGroup(f1, f2, f3).arrange(DOWN, buff=0.9)
        self.fit_width(block, 0.96)
        block.next_to(rng, DOWN, buff=1.3)
        p1 = VGroup(rng, block)
        self.at(0.3)  # 台词「但有个边界。」
        self.play(FadeIn(head, shift=DOWN * 0.3))
        self.at(1.8)  # 台词「E4M3 最大到 448…」
        self.play(FadeIn(rng, shift=UP * 0.2))
        self.at(3.6)  # 台词「子块 scale 的比值…」
        self.play(FadeIn(f1, shift=UP * 0.2), run_time=0.7)
        self.at(5.8)
        self.play(FadeIn(f2, shift=UP * 0.2), run_time=0.7)
        self.at(8.6)
        self.play(FadeIn(f3, shift=UP * 0.2), run_time=0.7)

        # 页2：实验表 + 搬家比喻 + 容量上限
        rows = VGroup(
            VGroup(t("≤ 2000", 38, GREEN, "BOLD"), t("误差 0.000 · 逐位相等", 36, GREEN)).arrange(RIGHT, buff=0.9),
            VGroup(t("3000", 38, RED, "BOLD"), t("误差 320 · 溢出饱和", 36, RED)).arrange(RIGHT, buff=0.9),
            VGroup(t("10⁴", 38, RED, "BOLD"), t("误差 1600", 36, RED)).arrange(RIGHT, buff=0.9),
        ).arrange(DOWN, buff=0.55)
        self.fit_width(rows, 0.94)
        rows.next_to(head, DOWN, buff=1.5)
        m1 = t("搬家：4 位小箱子 → 8 位大箱子", 40, WHITE)
        m2 = t("东西整块，格子更密，放得下", 38, GREEN)
        meta = VGroup(m1, m2).arrange(DOWN, buff=0.5)
        self.fit_width(meta, 0.96)
        meta.next_to(rows, DOWN, buff=1.3)
        m3 = t("但容量有上限——塞不下，就扁了", 38, RED)
        self.fit_width(m3, 0.96)
        m3.next_to(meta, DOWN, buff=1.3)
        p2 = VGroup(rows, meta, m3)
        self.next_page(p1, 15.8)  # 台词「两千以内…超过三千，溢出饱和」
        self.at(16.4)
        self.play(FadeIn(rows, shift=UP * 0.2), run_time=0.9)
        self.at(18.6)  # 台词「打个比方，搬家…」
        self.play(FadeIn(m1, shift=UP * 0.15), run_time=0.5)
        self.at(21.6)
        self.play(FadeIn(m2, shift=UP * 0.15), run_time=0.5)
        self.at(27.2)  # 台词「但容量有上限…」
        self.play(FadeIn(m3, shift=UP * 0.15), run_time=0.5)
        self.pad_to_voice()


# ---------------- S6 训练模拟 · 推理真量化 + 显存账（2 页） ----------------
class S6(_Base):
    def construct(self):
        self.footer()
        head = t("训练模拟 · 部署真量化", 50, YELL, "BOLD").to_edge(UP, buff=1.2)
        self.fit_width(head, 0.96)
        self.add(head)

        # 页1：流程链 + 训练/推理双栏
        chain = VGroup(
            t("FP32 master", 44, WHITE),
            t("→ FP4 →", 46, YELL),
            t("FP8 前向", 44, WHITE),
        ).arrange(RIGHT, buff=0.5)
        self.fit_width(chain, 0.94)
        chain.next_to(head, DOWN, buff=1.5)
        badge = t("直接复用 V3 的 FP8 框架 · 不加任何修改", 46, GREEN, "BOLD")
        self.fit_width(badge, 0.96)
        badge.next_to(chain, DOWN, buff=1.3)
        tr = VGroup(
            t("训练 / 反传", 46, CYAN, "BOLD"),
            t("FP32 master + 模拟 FP4", 44, WHITE),
        ).arrange(DOWN, buff=0.45)
        inf = VGroup(
            t("推理 / rollout", 46, GREEN, "BOLD"),
            t("直接用真 FP4 权重", 44, WHITE),
        ).arrange(DOWN, buff=0.45)
        cols = VGroup(tr, inf).arrange(RIGHT, buff=2.0)
        self.fit_width(cols, 0.94)
        cols.next_to(badge, DOWN, buff=1.4)
        p1 = VGroup(chain, badge, cols)
        self.at(0.5)  # 台词「这套设计换来的大奖…」
        self.play(FadeIn(head, shift=DOWN * 0.3))
        self.at(3.0)
        self.play(FadeIn(chain, shift=UP * 0.2))
        self.at(5.6)
        self.play(FadeIn(badge, shift=UP * 0.2), run_time=0.8)
        self.at(10.5)  # 台词「算笔账…」
        self.play(FadeIn(cols, shift=UP * 0.2))

        # 页2：显存账 + 省 776GB
        acc = t("专家权重 1.55T，占总参数 97%", 40, WHITE, "BOLD")
        self.fit_width(acc, 0.94)
        acc.next_to(head, DOWN, buff=1.1)
        bars = VGroup()
        for lab, v, col in [("FP8：1.55 TB", 20, RED), ("FP4：776 GB", 10, GREEN)]:
            b = Rectangle(height=v / 20 * 4.5, width=1.2, color=col,
                          fill_color=col, fill_opacity=0.55)
            bars.add(VGroup(b, t(lab, 32, col, "BOLD").next_to(b, UP, buff=0.25)))
        bars.arrange(RIGHT, buff=2.2)
        self.fit_width(bars, 0.9)
        bars.next_to(acc, DOWN, buff=1.0)
        save = t("H800：20 张 → 不到 10 张 · 省 776GB ≈ 再装一个 700B 模型", 38, GREEN, "BOLD")
        self.fit_width(save, 0.98)
        save.next_to(bars, DOWN, buff=1.0)
        p2 = VGroup(acc, bars, save)
        self.next_page(p1, 12.6)  # 台词「专家权重 1.55T…」
        self.at(13.2)
        self.play(FadeIn(acc, shift=UP * 0.2))
        self.at(16.0)  # 台词「FP8 存要 1.55TB，FP4 只要 776GB…」
        self.play(*[GrowFromEdge(b[0], DOWN) for b in bars], run_time=0.9)
        self.at(18.2)
        self.play(*[FadeIn(b[1]) for b in bars])
        self.at(31.2)  # 台词「省下的 776GB…」
        self.play(FadeIn(save, shift=UP * 0.2))
        self.pad_to_voice()


# ---------------- S7 indexer：99.7%（2 页） ----------------
class S7(_Base):
    def construct(self):
        self.footer()
        head = t("indexer：99.7% 召回怎么保住", 50, YELL, "BOLD").to_edge(UP, buff=1.2)
        self.fit_width(head, 0.96)
        self.add(head)

        # 页1：两处量化 + top-k 排序直觉
        q1 = VGroup(
            t("① QK path 全 FP4", 38, WHITE, "BOLD"),
            t("连激活都量化，比权重更狠", 34, RED),
        ).arrange(DOWN, buff=0.3)
        q2 = VGroup(
            t("② 分数 FP32 → BF16", 38, WHITE, "BOLD"),
            t("选择器提速 2 倍", 34, GREEN),
        ).arrange(DOWN, buff=0.3)
        qs = VGroup(q1, q2).arrange(RIGHT, buff=1.8)
        self.fit_width(qs, 0.96)
        qs.next_to(head, DOWN, buff=1.5)
        ins = t("top-k 选的是排序，不是绝对值", 44, YELL, "BOLD")
        self.fit_width(ins, 0.94)
        ins.next_to(qs, DOWN, buff=1.3)
        rank = VGroup(
            t("第 1 名 · 第 1000 名", 38, GREEN),
            t("BF16 扰动 0.4%，次序不动", 34, MUTED),
        ).arrange(DOWN, buff=0.35)
        rank.next_to(ins, DOWN, buff=1.3)
        p1 = VGroup(qs, ins, rank)
        self.at(0.5)  # 台词「99.7% 的召回怎么保住？」
        self.play(FadeIn(head, shift=DOWN * 0.3))
        self.at(3.4)  # 台词「V4 对 indexer 做了两处量化…」
        self.play(FadeIn(q1, shift=UP * 0.2))
        self.at(7.2)
        self.play(FadeIn(q2, shift=UP * 0.2))
        self.at(13.0)  # 台词「分数压到 BF16，选择器提速 2 倍…」
        self.play(FadeIn(ins, shift=UP * 0.2))
        self.at(19.6)  # 台词「直觉：top-k 选的是排序…」
        self.play(FadeIn(rank, shift=UP * 0.2))

        # 页2：压线互换（爆点页）
        edge = VGroup(
            t("压线的第 1024、1025 名", 48, RED, "BOLD"),
            t("可能互换 → 召回掉 0.3%", 44, RED),
        ).arrange(DOWN, buff=0.45)
        edge.next_to(head, DOWN, buff=1.5)
        boom = t("前 1024 名，99.7% 还是原来那些人", 60, GREEN, "BOLD")
        self.fit_width(boom, 0.96)
        boom.next_to(edge, DOWN, buff=1.6)
        p2 = VGroup(edge, boom)
        self.next_page(p1, 24.2)  # 台词「BF16 扰动 0.4%…」
        self.at(24.8)
        self.play(FadeIn(edge, shift=UP * 0.2))
        self.at(27.8)
        self.play(FadeIn(boom, scale=0.9), run_time=0.9)
        self.pad_to_voice()


# ---------------- S8 收尾 + 品牌尾卡（3 页） ----------------
class S8(_Base):
    def construct(self):
        self.footer()
        head = t("为什么后训练才上 QAT？", 50, YELL, "BOLD").to_edge(UP, buff=1.2)
        self.fit_width(head, 0.96)
        self.add(head)

        # 页1：预训练 vs 后训练
        pre = VGroup(
            t("33T tokens 预训练：全 FP8", 42, WHITE),
            t("FP4 QAT：后训练阶段引入", 42, CYAN),
        ).arrange(RIGHT, buff=1.4)
        self.fit_width(pre, 0.96)
        pre.next_to(head, DOWN, buff=1.5)
        guess = VGroup(
            t("报告没解释，我的猜测：", 42, MUTED),
            t("预训练最贵、最敏感，没必要冒险；", 42, WHITE),
            t("后训练是「临门一脚」", 48, GREEN, "BOLD"),
        ).arrange(DOWN, buff=0.55)
        self.fit_width(guess, 0.96)
        guess.next_to(pre, DOWN, buff=1.4)
        p1 = VGroup(pre, guess)
        self.at(0.5)  # 台词「为什么 33T 预训练全用 FP8…」
        self.play(FadeIn(head, shift=DOWN * 0.3))
        self.at(2.5)
        self.play(FadeIn(pre, shift=UP * 0.2))
        self.at(7.0)  # 台词「报告没解释…我的猜测…」
        self.play(FadeIn(guess[0], shift=UP * 0.15), run_time=0.5)
        self.at(8.6)
        self.play(FadeIn(guess[1], shift=UP * 0.15), run_time=0.5)
        self.at(11.5)  # 台词「后训练是临门一脚」
        self.play(FadeIn(guess[2], shift=UP * 0.15), run_time=0.5)

        # 页2：金句 + 美学（16 级台阶装饰）
        gold = t("模型先学会知识，再学会在 16 个台阶上表达", 52, YELL, "BOLD")
        self.fit_width(gold, 0.98)
        gold.next_to(head, DOWN, buff=1.5)
        stairs = VGroup(*[Rectangle(height=0.28, width=0.5, color=GREEN,
                                    fill_color=GREEN, fill_opacity=0.3) for _ in range(8)])
        stairs.arrange(RIGHT, buff=0)
        for i in range(1, 8):
            stairs[i].shift(UP * 0.28 * i)
        self.fit_width(stairs, 0.6)
        stairs.next_to(gold, DOWN, buff=1.2)
        aes = t("把有损量化放进训练适应，把回程压缩做成无损", 42, WHITE)
        self.fit_width(aes, 0.96)
        aes.next_to(stairs, DOWN, buff=1.2)
        p2 = VGroup(gold, stairs, aes)
        self.next_page(p1, 13.5)  # 台词「一句话：模型先学会知识…」
        self.at(14.1)
        self.play(FadeIn(gold, scale=0.9), run_time=0.8)
        self.at(16.5)  # 台词「再学会在 16 个台阶上表达」
        self.play(FadeIn(stairs, shift=UP * 0.2), run_time=0.8)
        self.at(19.8)  # 台词「FP4 的美学…」
        self.play(FadeIn(aes, shift=UP * 0.2))

        # 页3：下一篇 + 品牌卡
        next_t = t("下一篇：KV 缓存存进 SSD · 1M 上下文秒开", 40, CYAN, "BOLD")
        self.fit_width(next_t, 0.96)
        next_t.next_to(head, DOWN, buff=1.5)
        p3 = VGroup(next_t)
        self.next_page(p2, 26.4)  # 台词「下一篇：KV 缓存存进 SSD…」
        self.at(27.0)
        self.play(FadeIn(next_t, shift=UP * 0.2), run_time=0.7)

        # 品牌卡：淡出全部（整体上移，底部 ≥ 字幕区上方）
        self.at(27.8)
        self.play(*[FadeOut(m, shift=DOWN * 0.25) for m in (head, next_t)], run_time=0.7)

        logo = ImageMobject("avatar-sjai-round.png")
        logo.scale_to_fit_width(4.2)
        logo.move_to(UP * config.frame_height * 0.24)  # 画布比例坐标（锚点，上移避字幕区）
        follow = VGroup(
            t("关注「数解AI」", 56, YELL, "BOLD"),
            t("《FP4量化：4位数字怎么做到无损》", 36, WHITE, "BOLD"),
            t("查看公众号文章 · 图文全解", 34, GREEN),
            t("下一篇：KV 缓存进 SSD", 30, MUTED),
        ).arrange(DOWN, buff=0.55)
        follow.next_to(logo, DOWN, buff=1.4)  # 锚点链：跟随 logo
        self.at(28.8)
        self.play(FadeIn(logo, scale=0.9), run_time=0.9)
        self.at(30.0)
        self.play(FadeIn(follow, scale=0.85), run_time=0.8)
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
        title = t("FP4 量化", 54, YELL, "BOLD").next_to(series, DOWN, buff=1.0)
        subtitle = t("4 位数字怎么做到无损？", 34, WHITE).next_to(title, DOWN, buff=0.8)

        # 关键视觉：4 位结构 + 7 个数字 + 16 个可选值
        bits = bit_chips("SEEM", ["符号", "指数", "指数", "尾数"])
        bits.scale(0.9)
        nums = num_chips(["0.5", "1", "1.5", "2", "3", "4", "6"], h=0.9, w=1.1)
        nums.scale(0.9)
        total = t("1+2+1 位 = 16 个可选值", 26, MUTED)
        stage = VGroup(bits, nums, total).arrange(DOWN, buff=0.55)
        stage.scale_to_fit_width(config.frame_width * 0.86)
        stage.next_to(subtitle, DOWN, buff=1.7)

        self.add(brand, series, title, subtitle, stage)


if __name__ == "__main__":
    pass
