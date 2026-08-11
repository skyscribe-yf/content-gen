#!/usr/bin/env python3
"""《大模型 API 为什么这么慢？首字延迟揭秘》视频号 Manim 动画（竖屏 1080×1920）

8 个场景 S1-S8，与 storyboard.md 一一对应。
用法：
  python3 -m manim -qh scenes.py S1 S2 S3 S4 S5 S6 S7 S8 -j 8
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
VOICE_DUR = {"S1": 9.44, "S2": 10.88, "S3": 13.60, "S4": 10.72,
             "S5": 10.40, "S6": 17.60, "S7": 12.64, "S8": 10.72}
TAIL = 2.5  # 段尾缓冲


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

    def footer(self, text: str = "数解AI · 大模型 API 为什么这么慢"):
        f = t(text, 20, MUTED).to_edge(DOWN, buff=1.15)
        self.add(f)


# ---------------- S1 开场钩子 ----------------
class S1(_Base):
    def construct(self):
        self.footer()
        title = t("你以为请求直达 GPU？", 46, WHITE, "BOLD").to_edge(UP, buff=1.2)
        self.play(FadeIn(title, shift=DOWN * 0.4))

        # 客户端方块
        client = Rectangle(height=1.1, width=1.9, color=CYAN, fill_color=CYAN, fill_opacity=0.15)
        cl = t("请求", 30, CYAN)
        cgroup = VGroup(client, cl).move_to(LEFT * 3.0 + UP * 1.0)
        self.play(FadeIn(cgroup, shift=RIGHT * 0.3))

        # GPU 方块
        gpu = Rectangle(height=1.1, width=1.9, color=GREEN, fill_color=GREEN, fill_opacity=0.15)
        gtxt = t("GPU", 30, GREEN)
        ggroup = VGroup(gpu, gtxt).move_to(RIGHT * 3.0 + UP * 1.0)
        self.play(FadeIn(ggroup, shift=LEFT * 0.3))

        # 直线箭头
        line = Arrow(cgroup.get_right(), ggroup.get_left(), color=MUTED, buff=0.15)
        self.play(Create(line))
        self.wait(0.4)

        # 箭头被切断，裂开
        brk = DashedLine(cgroup.get_right(), ggroup.get_left(), color=RED, dash_length=0.12)
        self.play(Transform(line, brk), run_time=0.6)
        self.wait(0.3)

        # 问题文字
        q = t("十几秒过去，第一个字还没来", 36, RED, "BOLD").move_to(UP * 1.0 - DOWN * 2.4)
        q2 = t("到底慢在哪？", 40, YELL, "BOLD").next_to(q, DOWN, buff=0.4)
        self.play(Write(q), run_time=1.2)
        self.play(FadeIn(q2, shift=UP * 0.2))
        self.wait(1.2)
        self.pad_to_voice()



# ---------------- S2 TTFT 定义 ----------------
class S2(_Base):
    def construct(self):
        self.footer()
        head = t("首字延迟 TTFT", 44, YELL, "BOLD").to_edge(UP, buff=1.2)
        sub = t("Time To First Token", 26, MUTED).next_to(head, DOWN, buff=0.35)
        self.play(FadeIn(head, shift=DOWN * 0.3), FadeIn(sub))

        # 时间轴
        axis = Line(LEFT * 3.2, RIGHT * 3.2, color=MUTED).shift(DOWN * 0.2)
        treq = Dot(axis.get_left(), color=CYAN, radius=0.09)
        tfirst = Dot(axis.get_right(), color=YELL, radius=0.09)
        self.play(Create(axis), FadeIn(treq), FadeIn(tfirst))

        lreq = t("t_request\n按下发送", 22, CYAN).next_to(treq, DOWN, buff=0.5)
        lfirst = t("t_first\n收到首 token", 22, YELL).next_to(tfirst, DOWN, buff=0.5)
        self.play(FadeIn(lreq), FadeIn(lfirst))

        # 高亮区间 = TTFT
        span = Rectangle(height=0.5, width=axis.get_width(), color=RED, fill_color=RED, fill_opacity=0.25)
        span.move_to(axis.get_center())
        self.play(Create(span))
        lab = t("TTFT：从按下发送，到看到第一个字", 30, WHITE, "BOLD").move_to(UP * 0.9)
        self.play(FadeIn(lab, shift=UP * 0.2))
        self.wait(1.2)
        self.pad_to_voice()



# ---------------- S3 服务链路 ----------------
class S3(_Base):
    def construct(self):
        self.footer()
        head = t("请求不是直通 GPU 的电线", 38, YELL, "BOLD").to_edge(UP, buff=1.2)
        self.play(FadeIn(head, shift=DOWN * 0.3))

        nodes = ["客户端", "网关·鉴权", "模型路由", "排队·批处理", "prefill", "decode", "流式返回"]
        colors = [CYAN, MUTED, MUTED, MUTED, GREEN, GREEN, CYAN]
        boxes = VGroup()
        for i, (name, col) in enumerate(zip(nodes, colors)):
            b = Rectangle(height=0.85, width=3.4, color=col, fill_color=col, fill_opacity=0.12)
            l = t(name, 26, col)
            g = VGroup(b, l).move_to(UP * (4.2 - i * 1.28))
            boxes.add(g)
        # 竖排：上→下
        for i, g in enumerate(boxes):
            g.move_to(UP * (4.6 - i * 1.32))
            g.set_y(4.6 - i * 1.32)

        arrows = VGroup()
        for i in range(len(nodes) - 1):
            a = Arrow(boxes[i].get_bottom(), boxes[i + 1].get_top(), color=MUTED, buff=0.1, stroke_width=3)
            arrows.add(a)

        for i, g in enumerate(boxes):
            self.play(FadeIn(g, shift=DOWN * 0.15), run_time=0.45)
            if i < len(arrows):
                self.play(Create(arrows[i]), run_time=0.25)

        # 服务层 vs 模型层标注
        svc = t("服务层", 22, MUTED).next_to(boxes[3], LEFT, buff=0.5).shift(LEFT * 0.3)
        mdl = t("模型推理", 22, MUTED).next_to(boxes[5], LEFT, buff=0.5).shift(LEFT * 0.3)
        self.play(FadeIn(svc), FadeIn(mdl))
        self.wait(1.0)
        self.pad_to_voice()



# ---------------- S4 prefill 平方增长 ----------------
class S4(_Base):
    def construct(self):
        self.footer()
        head = t("prefill：开口前先读完全部输入", 34, YELL, "BOLD").to_edge(UP, buff=1.2)
        self.play(FadeIn(head, shift=DOWN * 0.3))

        # 左：小输入 3 点（3 对）
        left_pts = VGroup(*[Dot(color=CYAN, radius=0.10) for _ in range(3)]).arrange(RIGHT, buff=0.7)
        left_pts.move_to(LEFT * 2.2 + DOWN * 0.4)
        left_edges = VGroup()
        for i in range(3):
            for j in range(i + 1, 3):
                left_edges.add(Line(left_pts[i].get_center(), left_pts[j].get_center(), color=MUTED, stroke_width=3))
        lcap = t("输入 n=3\n配对 3 对", 24, WHITE).next_to(left_pts, DOWN, buff=0.7)

        # 右：大输入 6 点（15 对）
        right_pts = VGroup(*[Dot(color=GREEN, radius=0.09) for _ in range(6)]).arrange(RIGHT, buff=0.45)
        right_pts.move_to(RIGHT * 2.2 + DOWN * 0.4)
        right_edges = VGroup()
        for i in range(6):
            for j in range(i + 1, 6):
                right_edges.add(Line(right_pts[i].get_center(), right_pts[j].get_center(), color=MUTED, stroke_width=2))
        rcap = t("输入翻倍 n=6\n配对 15 对 ≈ 5 倍", 24, YELL, "BOLD").next_to(right_pts, DOWN, buff=0.7)

        self.play(FadeIn(left_pts))
        self.play(*[Create(e) for e in left_edges], run_time=0.8)
        self.play(FadeIn(lcap))
        self.wait(0.3)
        self.play(FadeIn(right_pts), FadeOut(left_edges), FadeOut(left_pts), FadeOut(lcap))
        self.play(*[Create(e) for e in right_edges], run_time=1.2)
        self.play(FadeIn(rcap))

        formula = t("C_prefill ∝ T_in²", 36, YELL, "BOLD").move_to(UP * 0.6)
        note = t("输入翻一倍，工作量接近四倍", 30, WHITE, "BOLD").next_to(formula, DOWN, buff=0.5)
        self.play(FadeIn(formula, shift=UP * 0.3), FadeIn(note))
        self.wait(1.2)
        self.pad_to_voice()



# ---------------- S5 decode + KV Cache ----------------
class S5(_Base):
    def construct(self):
        self.footer()
        head = t("decode：逐 token 生成", 40, YELL, "BOLD").to_edge(UP, buff=1.2)
        self.play(FadeIn(head, shift=DOWN * 0.3))

        # token 序列从左到右逐个出现
        tokens = VGroup()
        for i in range(6):
            b = Square(side_length=0.9, color=GREEN, fill_color=GREEN, fill_opacity=0.12)
            l = t("tok", 18, GREEN)
            g = VGroup(b, l)
            tokens.add(g)
        tokens.arrange(RIGHT, buff=0.35).move_to(UP * 1.6)

        for g in tokens:
            self.play(FadeIn(g, shift=UP * 0.15), run_time=0.3)

        # KV Cache 条增长
        kvc = t("KV Cache（历史 Key / Value）", 26, CYAN).move_to(DOWN * 1.0)
        self.play(FadeIn(kvc))
        bar = Rectangle(height=0.5, width=0.3, color=CYAN, fill_color=CYAN, fill_opacity=0.6)
        bar.move_to(DOWN * 1.9, aligned_edge=LEFT)
        self.play(GrowFromEdge(bar, LEFT), run_time=0.5)
        self.wait(0.4)

        m1 = t("M_KV ∝ T_in", 32, CYAN, "BOLD").move_to(DOWN * 3.1)
        m2 = t("缓存随历史线性增长，\n但省掉重复计算", 26, WHITE).next_to(m1, DOWN, buff=0.5)
        self.play(FadeIn(m1), FadeIn(m2))
        self.wait(1.2)
        self.pad_to_voice()



# ---------------- S6 真实日志数据 ----------------
class S6(_Base):
    def construct(self):
        self.footer()
        head = t("真实日志：输入越长，首字越慢", 34, YELL, "BOLD").to_edge(UP, buff=1.2)
        self.play(FadeIn(head, shift=DOWN * 0.3))

        buckets = ["0-16K", "16-32K", "32-64K", "64-96K", "96-128K"]
        vals = [4.7, 6.6, 7.9, 11.8, 14.0]
        maxv = 15.0
        bars = VGroup()
        bw = 0.85
        for i, (name, v) in enumerate(zip(buckets, vals)):
            h = v / maxv * 4.4
            bar = Rectangle(height=h, width=bw, color=YELL if i in (0, 4) else MUTED,
                            fill_color=YELL if i in (0, 4) else MUTED, fill_opacity=0.55)
            lab = t(f"{v}s", 22, WHITE if i in (0, 4) else MUTED).next_to(bar, UP, buff=0.12)
            bl = t(name, 20, MUTED).next_to(bar, DOWN, buff=0.12)
            g = VGroup(bar, lab, bl)
            bars.add(g)
        bars.arrange(RIGHT, buff=0.5).move_to(DOWN * 0.8)
        self.play(*[GrowFromEdge(b[0], DOWN) for b in bars], run_time=1.5)
        self.play(*[FadeIn(b[1], shift=UP * 0.2) for b in bars],
                  *[FadeIn(b[2], shift=DOWN * 0.2) for b in bars])

        # TPS 平线
        tps = t("首字后生成速度：稳定 25-30 token/s", 28, GREEN, "BOLD").move_to(DOWN * 4.6)
        self.play(FadeIn(tps, shift=UP * 0.2))
        note = t("输入翻近 3 倍：TTFT 4.7s → 14.0s", 30, WHITE, "BOLD").move_to(UP * 1.8)
        self.play(FadeIn(note))
        self.wait(1.2)
        self.pad_to_voice()



# ---------------- S7 四把扳手 ----------------
class S7(_Base):
    def construct(self):
        self.footer()
        head = t("四把扳手，各管一段", 42, YELL, "BOLD").to_edge(UP, buff=1.2)
        self.play(FadeIn(head, shift=DOWN * 0.3))

        items = [
            ("① 减输入", "压缩提示词与历史", CYAN),
            ("② KV Cache", "历史不重复计算", GREEN),
            ("③ 推测解码", "草稿模型先猜一段", CYAN),
            ("④ 量化", "降低精度，减少搬运", GREEN),
        ]
        cards = VGroup()
        for name, desc, col in items:
            c = Rectangle(height=2.0, width=3.3, color=col, fill_color=col, fill_opacity=0.08)
            n = t(name, 32, col, "BOLD")
            d = t(desc, 22, WHITE)
            g = VGroup(c, VGroup(n, d).arrange(DOWN, buff=0.25))
            cards.add(g)
        cards.arrange_in_grid(rows=2, cols=2, buff=0.7).move_to(DOWN * 0.4)

        for g in cards:
            self.play(FadeIn(g, shift=UP * 0.2), run_time=0.5)

        tail = t("采样参数管的是“选哪个 token”，\n管不了排队和 prefill", 26, MUTED).move_to(DOWN * 4.3)
        self.play(FadeIn(tail))
        self.wait(1.0)
        self.pad_to_voice()



# ---------------- S8 结尾引导 ----------------
class S8(_Base):
    def construct(self):
        self.footer("数解AI · 大模型 API 为什么这么慢")
        head = t("API 用户真正能做的", 40, YELL, "BOLD").to_edge(UP, buff=1.2)
        self.play(FadeIn(head, shift=DOWN * 0.3))

        rows = [
            ("记 4 个字段", "输入 token · 输出 token · TTFT · TPS", CYAN),
            ("按负载分组", "短 prompt 和长上下文分开看", GREEN),
            ("看 P50 与 P90", "典型体验 + 长尾有多难受", YELL),
        ]
        items = VGroup()
        for name, desc, col in rows:
            n = t(name, 30, col, "BOLD")
            d = t(desc, 24, WHITE)
            g = VGroup(n, d).arrange(DOWN, buff=0.18)
            items.add(g)
        items.arrange(DOWN, buff=0.9).move_to(UP * 0.2)
        for g in items:
            self.play(FadeIn(g, shift=UP * 0.25), run_time=0.6)

        # 切换品牌卡：建议淡出，品牌图 + 关注引导
        self.play(*[FadeOut(g, shift=DOWN * 0.25) for g in items], FadeOut(head), run_time=0.7)

        logo = ImageMobject("avatar-sjai-round.png")
        logo.scale_to_fit_width(3.6).move_to(UP * 0.9)
        self.play(FadeIn(logo, scale=0.9), run_time=0.9)

        follow = VGroup(
            t("关注「数解AI」", 44, YELL, "BOLD"),
            t("继续拆大模型推理链路", 28, WHITE),
        ).arrange(DOWN, buff=0.35).next_to(logo, DOWN, buff=0.9)
        self.play(FadeIn(follow, scale=0.85), run_time=0.8)
        self.wait(1.0)
        self.pad_to_voice()


if __name__ == "__main__":
    pass
