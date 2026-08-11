#!/usr/bin/env python3
"""《BPE分词：AI为什么把文字切成碎片？》视频号 Manim 动画（竖屏 1080×1920）

大模型原理 · 第 1 篇。8 个场景 S1-S8 与 storyboard.md 一一对应，末尾 Cover 封面帧。
布局规范：VGroup 原子化 + 锚点链 + 安全区 + 比例坐标。
用法（在 shipinhao/ 目录下执行）：
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

# 每场景配音时长（ffprobe 实测），渲染时长 = 配音 + TAIL
VOICE_DUR = {"S1": 18.07, "S2": 24.41, "S3": 33.21, "S4": 20.6, "S5": 28.15, "S6": 24.09, "S7": 23.19, "S8": 30.38}
TAIL = 2.5  # 段尾缓冲（build 会截到 0.1s）

# 安全区（画布比例坐标）：上避标题、下避 footer/字幕、左右避边
SAFE_TOP = config.frame_height / 2 - 1.5      # 5.61
SAFE_BOTTOM = -config.frame_height / 2 + 3.0  # 内容最低点 y ≥ -4.11（距底 ≥399px）
SAFE_X = config.frame_width / 2 - 0.4


def t(text: str, size: float = 34, color: str = WHITE, weight: str = "NORMAL") -> Text:
    return Text(text, font=FONT, font_size=size, color=color, weight=weight)


class _Base(Scene):
    scene_dur = 12.0

    def setup(self):
        self.scene_dur = VOICE_DUR[self.__class__.__name__] + TAIL

    def at(self, tm: float):
        """推进到配音时间轴绝对时刻（动画动作挂到台词节点上）。"""
        d = tm - self.time
        if d > 0.01:
            self.wait(d)

    def pad_to_voice(self):
        """末尾补齐等待，使场景总时长 = 配音时长 + TAIL 缓冲。"""
        elapsed = self.time
        target = self.scene_dur
        if target > elapsed:
            self.wait(target - elapsed)

    def footer(self, text: str = "数解AI · 大模型原理"):
        f = t(text, 20, MUTED).to_edge(DOWN, buff=1.15)
        self.add(f)

    def head(self, text: str, color: str = YELL):
        h = t(text, 48, color, "BOLD")
        if h.width > config.frame_width * 0.88:
            h.set_width(config.frame_width * 0.88)
        h.to_edge(UP, buff=1.2)
        self.play(FadeIn(h, shift=DOWN * 0.3))
        return h

    def fit_width(self, mob, frac: float = 0.8):
        """长内容限宽：不超过画布宽的 frac，防越界截断。"""
        return mob.set_width(config.frame_width * frac)


def letter_blocks(word: str, hi: set | None = None,
                  size: float = 0.62, color: str = WHITE) -> VGroup:
    """逐字母方块行。hi 集合里的字母用黄色高亮。"""
    hi = hi or set()
    blocks = VGroup()
    for ch in word:
        c = YELL if ch in hi else color
        b = Rectangle(height=size, width=size, color=c, fill_color=c, fill_opacity=0.22)
        lab = t(ch, size * 60, c if ch in hi else WHITE, "BOLD")  # size单位≈135px，60pt/单位≈占75%高
        blocks.add(VGroup(b, lab))
    blocks.arrange(RIGHT, buff=0.1)
    return blocks


def token_blocks(words: list, color: str = CYAN,
                 size: float = 0.8) -> VGroup:
    """一串 token 块（每块一个词/字）。文字自动限宽到框内 78%，防溢出。"""
    blocks = VGroup()
    for w in words:
        b = Rectangle(height=size, width=size * 1.8, color=color,
                      fill_color=color, fill_opacity=0.16)
        lab = t(w, size * 45, WHITE)
        lab.set_width(b.width * 0.78)
        blocks.add(VGroup(b, lab))
    blocks.arrange(RIGHT, buff=0.14)
    return blocks


def boxed_text(label: str, box_w: float, box_h: float, color: str,
               font_size: float, text_color: str = WHITE,
               bold: bool = False) -> VGroup:
    """统一「框 + 自适应文字」：文字限宽到框内 72%，杜绝溢出/截断。"""
    box = Rectangle(height=box_h, width=box_w, color=color,
                    fill_color=color, fill_opacity=0.16)
    txt = t(label, font_size, text_color, "BOLD" if bold else "NORMAL")
    txt.set_width(box_w * 0.72)
    return VGroup(box, txt)


# ---------------- S1 开场钩子：strawberry 数 r ----------------
class S1(_Base):
    def construct(self):
        self.footer()
        self.head("BPE 分词 · 大模型原理 第 1 篇")

        # 主视觉：strawberry 字母块，两个 r 高亮
        sb = letter_blocks("strawberry", hi={"r"}, size=0.72)
        sb.set_width(config.frame_width * 0.85)
        sb.next_to(UP * (config.frame_height / 2 - 1.5), DOWN, buff=0.5)
        self.at(0.00)
        self.play(FadeIn(sb, scale=0.9), run_time=1.0)

        q = t("strawberry 里有几个字母 r？", 40, WHITE, "BOLD")
        q.next_to(sb, DOWN, buff=0.6)
        self.at(1.03)
        self.play(FadeIn(q, shift=UP * 0.2), run_time=0.8)

        # 模型答 2 个（红叉）
        wrong = VGroup(
            t("2024 年最先进的模型答：", 30, MUTED),
            t("2 个", 48, RED, "BOLD"),
        ).arrange(RIGHT, buff=0.5)
        wrong.next_to(q, DOWN, buff=0.9)
        self.at(3.85)
        self.play(FadeIn(wrong, shift=UP * 0.2), run_time=0.8)
        x = t("✗", 44, RED, "BOLD").next_to(wrong, RIGHT, buff=0.4)
        self.play(FadeIn(x), run_time=0.4)

        # 正确答案 3 个（绿勾）
        right = VGroup(
            t("正确答案：", 30, MUTED),
            t("3 个", 48, GREEN, "BOLD"),
        ).arrange(RIGHT, buff=0.5)
        right.next_to(wrong, DOWN, buff=0.8)
        self.at(8.12)
        self.play(FadeIn(right, shift=UP * 0.2), run_time=0.7)
        ok = t("✓", 44, GREEN, "BOLD").next_to(right, RIGHT, buff=0.4)
        self.play(FadeIn(ok), run_time=0.4)

        # 反差
        iron = VGroup(
            t("能做微积分、能写代码的模型", 32, WHITE),
            t("数字母却翻车", 32, WHITE),
        ).arrange(DOWN, buff=0.2)
        iron.next_to(right, DOWN, buff=0.9)
        self.at(10.26)
        self.play(FadeIn(iron, shift=UP * 0.2), run_time=0.9)

        # 核心问句
        ask = t("它到底是怎么“看”文字的？", 44, YELL, "BOLD")
        ask.next_to(iron, DOWN, buff=0.9)
        self.at(14.54)
        self.play(FadeIn(ask, scale=0.9), run_time=0.9)
        self.at(17.96)
        self.pad_to_voice()


# ---------------- S2 模型按 token 读字 ----------------
class S2(_Base):
    def construct(self):
        self.footer()
        head = self.head("模型为什么不直接读文字？")

        # 页 1：文字 → 整数编号
        def id_card(word: str, num: str, color: str):
            w = t(word, 36, color, "BOLD")
            box = Rectangle(height=1.0, width=1.9, color=YELL, fill_color=YELL, fill_opacity=0.18)
            n = t(num, 34, YELL, "BOLD")
            b = VGroup(box, n)
            row = VGroup(w, b).arrange(RIGHT, buff=1.1)
            a = Arrow(row[0].get_right(), row[1].get_left(), color=MUTED,
                      buff=0.1, stroke_width=4)
            return VGroup(row[0], a, row[1])  # 文字 + 自适应箭头 + 数字框，避免重叠

        c1 = id_card("“猫”", "642", CYAN)
        c2 = id_card("“Transformer”", "105668", GREEN)
        cards = VGroup(c1, c2).arrange(DOWN, buff=0.9)
        cards.next_to(head, DOWN, buff=1.2)
        for c in cards:
            self.play(FadeIn(c[0]), run_time=0.5)
            self.play(Create(c[1]), run_time=0.6)
            self.play(FadeIn(c[2], shift=UP * 0.15), run_time=0.6)

        only = t("它只认整数编号", 40, YELL, "BOLD").next_to(cards, DOWN, buff=1.0)
        self.at(7.06)
        self.play(FadeIn(only, scale=0.9), run_time=0.8)

        # 页 2：分词器三步链（节点文字限宽防溢出）
        self.at(10.15)
        self.play(*[FadeOut(m, shift=DOWN * 0.2) for m in (cards, only)], run_time=0.5)
        chain = VGroup()
        for i, (lab, col) in enumerate([("文字", WHITE), ("token 片段", CYAN), ("token ID", YELL)]):
            chain.add(boxed_text(lab, 2.0, 1.1, col, 30, col if i < 2 else YELL, bold=True))
            if i < 2:
                chain.add(Arrow(LEFT * 0.4, RIGHT * 0.4, color=MUTED, stroke_width=5))
        chain.arrange(RIGHT, buff=0.2)
        chain.next_to(head, DOWN, buff=1.4)
        self.fit_width(chain, 0.9)
        self.play(FadeIn(chain[0], shift=UP * 0.1), run_time=0.6)
        self.play(Create(chain[1]), FadeIn(chain[2], shift=UP * 0.1), run_time=0.7)
        self.play(Create(chain[3]), FadeIn(chain[4], shift=UP * 0.1), run_time=0.7)
        note = t("切得越碎，占的编号越多", 30, MUTED).next_to(chain, DOWN, buff=0.8)
        self.at(14.11)
        self.play(FadeIn(note), run_time=0.6)

        # 页 3：词表规模
        self.at(15.44)
        self.play(*[FadeOut(m, shift=DOWN * 0.2) for m in (chain, note)], run_time=0.5)
        big = t("129,280", 64, YELL, "BOLD").next_to(head, DOWN, buff=1.2)
        cap = t("DeepSeek-V4-Pro 的词表条目数", 32, WHITE).next_to(big, DOWN, buff=0.4)
        self.play(FadeIn(big, scale=0.85), run_time=0.8)
        self.play(FadeIn(cap), run_time=0.6)

        warn = t("≠ 12 万个“完整词”", 36, RED, "BOLD").next_to(cap, DOWN, buff=0.9)
        self.at(20.29)
        self.play(FadeIn(warn, scale=0.9), run_time=0.7)
        frag = t("是能拼出一切的碎片", 36, GREEN, "BOLD").next_to(warn, DOWN, buff=0.7)
        self.at(22.05)
        self.play(FadeIn(frag, shift=UP * 0.2), run_time=0.8)
        # 装饰视觉：碎片示例（贴合“能拼出一切的碎片”台词）
        frags = token_blocks(["low", "st", "7", "B"], color=GREEN, size=0.55)
        frags.next_to(frag, DOWN, buff=0.7)
        self.at(23.20)
        self.play(FadeIn(frags, shift=UP * 0.15), run_time=0.7)
        self.at(24.17)
        self.pad_to_voice()


# ---------------- S3 BPE 怎么把小片段粘成大块 ----------------
class S3(_Base):
    def construct(self):
        self.footer()
        head = self.head("BPE 怎么粘出大块？")

        # 页 1：四个词 + 拆字符（加大间距，内容下移铺满）
        words = VGroup(*[t(w, 34, WHITE, "BOLD") for w in ["low", "low", "lower", "lowest"]])
        words.arrange(RIGHT, buff=1.2)
        words.next_to(head, DOWN, buff=1.3)
        self.at(2.65)
        self.play(FadeIn(words, shift=UP * 0.15), run_time=0.9)

        split = VGroup(
            letter_blocks("low", size=0.58),
            letter_blocks("low", size=0.58),
            letter_blocks("lower", size=0.58),
            letter_blocks("lowest", size=0.58),
        )
        split.arrange(DOWN, buff=0.5)
        split.next_to(words, DOWN, buff=1.3)
        self.fit_width(split, 0.72)
        self.at(4.86)
        self.play(FadeIn(split, shift=UP * 0.15), run_time=1.0)
        hint = t("先拆成字符，数相邻字符对", 30, MUTED).next_to(split, DOWN, buff=0.7)
        self.at(9.29)
        self.play(FadeIn(hint), run_time=0.5)

        # 页 2：统计表 + 合并动画
        self.at(11.94)
        self.play(*[FadeOut(m, shift=DOWN * 0.2) for m in (words, split, hint)], run_time=0.5)
        stats = VGroup()
        for pair, cnt, hi in [("(l, o)", "4 次", True), ("(o, w)", "4 次", True),
                              ("(w, e)", "2 次", False), ("(e, r)", "1 次", False)]:
            c = YELL if hi else MUTED
            row = VGroup(
                t(pair, 34, c if hi else WHITE, "BOLD" if hi else "NORMAL"),
                t(cnt, 34, c, "BOLD"),
            ).arrange(RIGHT, buff=0.6)
            stats.add(row)
        stats.arrange(RIGHT, buff=1.0)
        stats.next_to(head, DOWN, buff=1.1)
        self.fit_width(stats, 0.9)
        self.play(FadeIn(stats, shift=UP * 0.2), run_time=0.9)
        self.at(14.59)
        best = t("最高频：(l, o)", 36, YELL, "BOLD").next_to(stats, DOWN, buff=0.7)
        self.play(FadeIn(best, scale=0.9), run_time=0.6)

        # 合并动画：l o → lo → low
        self.at(18.13)
        lo = letter_blocks("lo", size=0.62)
        lo.next_to(best, DOWN, buff=0.9)
        self.play(FadeIn(lo, shift=UP * 0.2), run_time=0.7)
        m1 = t("l + o → lo", 32, GREEN, "BOLD").next_to(lo, RIGHT, buff=0.6)
        self.play(FadeIn(m1), run_time=0.5)
        self.at(20.34)
        low = letter_blocks("low", size=0.62)
        low.next_to(lo, DOWN, buff=0.7)
        self.play(FadeIn(low, shift=UP * 0.2), run_time=0.7)
        m2 = t("lo + w → low", 32, GREEN, "BOLD").next_to(low, RIGHT, buff=0.6)
        self.play(FadeIn(m2), run_time=0.5)
        badge_text = t("low 成了一个 token", 30, "#16213E", "BOLD")
        badge_box = Rectangle(height=1.0, width=3.6, color=YELL, fill_color=YELL, fill_opacity=0.9)
        badge_text.set_width(badge_box.width * 0.8)  # 限宽防截字
        badge = VGroup(badge_box, badge_text)
        badge.next_to(low, DOWN, buff=0.8)
        self.at(21.67)
        self.play(FadeIn(badge, scale=0.9), run_time=0.6)

        # 页 3：lowest 拆分 + 结论
        self.at(24.32)
        self.play(*[FadeOut(m, shift=DOWN * 0.2) for m in (stats, best, lo, m1, low, m2, badge)], run_time=0.5)
        ls = letter_blocks("lowest", size=0.62)
        ls.next_to(head, DOWN, buff=1.0)
        self.play(FadeIn(ls), run_time=0.7)
        brk = VGroup(
            t("= low + e + s + t", 36, WHITE, "BOLD"),
            t("（low 见过，整体保留；e、s、t 保持小块）", 28, MUTED),
        ).arrange(DOWN, buff=0.35)
        brk.next_to(ls, DOWN, buff=0.8)
        self.at(26.09)
        self.play(FadeIn(brk, shift=UP * 0.2), run_time=0.8)

        concl = VGroup(
            t("常见片段，越合越大", 38, YELL, "BOLD"),
            t("罕见片段，先保持小块", 38, GREEN, "BOLD"),
        ).arrange(DOWN, buff=0.45)
        concl.next_to(brk, DOWN, buff=1.0)
        self.at(28.74)
        self.play(FadeIn(concl, scale=0.9), run_time=0.9)
        self.at(32.99)
        self.pad_to_voice()


# ---------------- S4 四步代码骨架 ----------------
class S4(_Base):
    def construct(self):
        self.footer()
        head = self.head("核心就四步")

        steps = VGroup()
        for i, (lab, sub) in enumerate([("① 数 pair", "统计相邻字符对"),
                                        ("② 找最高频", "出现次数最多"),
                                        ("③ 合并", "粘成新片段"),
                                        ("④ 循环", "回到第 ① 步")]):
            box = Rectangle(height=1.6, width=1.75, color=CYAN, fill_color=CYAN, fill_opacity=0.12)
            title = t(lab, 30, YELL if i == 3 else WHITE, "BOLD")
            title.set_width(box.width * 0.8)
            s = t(sub, 22, MUTED)
            s.set_width(box.width * 0.75)
            steps.add(VGroup(box, VGroup(title, s).arrange(DOWN, buff=0.2)))
        steps.arrange(RIGHT, buff=0.45)
        steps.next_to(head, DOWN, buff=1.2)
        self.fit_width(steps, 0.92)
        self.at(0.47)
        for s in steps:
            self.play(FadeIn(s, shift=UP * 0.08), run_time=0.6)

        # 循环箭头：放在卡片组下方（弧向下凸，不遮挡任何元素），标签在弧下方
        loop = CurvedArrow(
            steps[3].get_bottom() + DOWN * 0.3,
            steps[0].get_bottom() + DOWN * 0.3,
            angle=-PI / 2, color=YELL, stroke_width=5,
        )
        self.at(6.51)
        self.play(Create(loop), run_time=0.8)
        loop_lab = t("循环", 26, YELL, "BOLD").next_to(loop, DOWN, buff=0.15)
        self.play(FadeIn(loop_lab), run_time=0.4)

        code = t("频率统计 → 选 pair → 合并 → 更新词表", 32, GREEN, "BOLD")
        code.next_to(loop_lab, DOWN, buff=0.5)  # 整体下移到弧下方，避开弧线
        self.fit_width(code, 0.9)
        self.at(9.30)
        self.play(FadeIn(code, shift=UP * 0.1), run_time=0.7)

        extra = VGroup(
            t("真实 tokenizer 还要处理：", 28, MUTED),
            t("空格 · Unicode · 字节 · 特殊 token", 28, WHITE),
        ).arrange(DOWN, buff=0.2)
        extra.next_to(code, DOWN, buff=0.8)
        self.at(14.42)
        self.play(FadeIn(extra), run_time=0.7)

        core = t("但骨架就是这个循环", 40, YELL, "BOLD").next_to(extra, DOWN, buff=0.9)
        self.at(18.14)
        self.play(FadeIn(core, scale=0.9), run_time=0.7)
        self.at(20.37)
        self.pad_to_voice()


# ---------------- S5 真实 tokenizer：14 个 token ----------------
class S5(_Base):
    def construct(self):
        self.footer()
        head = self.head("DeepSeek-V4-Pro 怎么切？")

        # 页 1：句子 + 14 token
        sent = t("请用 Python 写一个 Transformer，参数量 7B。", 32, WHITE, "BOLD")
        sent.next_to(head, DOWN, buff=1.0)
        self.fit_width(sent, 0.9)
        self.at(2.72)
        self.play(FadeIn(sent, shift=UP * 0.2), run_time=0.7)

        row1 = ["请", "用", "Python", "写", "一个", "Transformer", "，"]
        row2 = ["参数", "量", "7", "B", "。"]
        toks = VGroup(
            token_blocks(row1, size=0.72),
            token_blocks(row2, size=0.72),
        ).arrange(DOWN, buff=0.4)
        toks.next_to(sent, DOWN, buff=0.8)
        self.fit_width(toks, 0.9)
        self.at(4.53)
        for r in toks:
            for b in r:
                self.play(FadeIn(b, scale=0.8), run_time=0.08)
        self.at(8.15)
        big = VGroup(
            t("14", 60, YELL, "BOLD"),
            t("个 token", 40, YELL, "BOLD"),
        ).arrange(RIGHT, buff=0.3)
        big.next_to(toks, DOWN, buff=0.8)
        self.play(FadeIn(big, scale=0.85), run_time=0.7)
        note = t("英文整词保留，数字 7B 拆成 7 和 B", 28, MUTED).next_to(big, DOWN, buff=0.6)
        self.at(10.41)
        self.play(FadeIn(note), run_time=0.5)

        # 页 2：乱码视角 vs ID 视角
        self.at(11.77)
        self.play(*[FadeOut(m, shift=DOWN * 0.2) for m in (sent, toks, big, note)], run_time=0.5)
        garb = VGroup(
            t("打印出来像乱码？", 40, RED, "BOLD"),
            t("è¯·  çĶ¨  åĨĻ …", 30, RED),
        ).arrange(DOWN, buff=0.5)
        garb.next_to(head, DOWN, buff=1.0)
        self.play(FadeIn(garb, shift=UP * 0.2), run_time=0.8)

        byte_chain = VGroup(
            t("中文", 30, WHITE, "BOLD"),
            t("→ UTF-8 字节", 30, CYAN, "BOLD"),
            t("→ 合并", 30, GREEN, "BOLD"),
        ).arrange(RIGHT, buff=0.4)
        byte_chain.next_to(garb, DOWN, buff=0.9)
        self.at(14.49)
        self.play(FadeIn(byte_chain, shift=UP * 0.2), run_time=0.7)
        wtf = t("byte-level 的“工作现场”", 30, MUTED).next_to(byte_chain, DOWN, buff=0.6)
        self.play(FadeIn(wtf), run_time=0.5)

        # 页 3：看 ID 就清楚了
        self.at(18.56)
        self.play(*[FadeOut(m, shift=DOWN * 0.2) for m in (garb, byte_chain, wtf)], run_time=0.5)
        ids = VGroup(
            VGroup(t("Transformer", 32, GREEN, "BOLD"), t("→ 1 个 token", 32, WHITE)).arrange(RIGHT, buff=0.6),
            VGroup(t("7B", 32, WHITE, "BOLD"), t("→ 7 / B 两个 token", 32, YELL)).arrange(RIGHT, buff=0.6),
        ).arrange(DOWN, buff=0.7)
        ids.next_to(head, DOWN, buff=1.1)
        self.fit_width(ids, 0.9)
        self.play(FadeIn(ids[0], shift=UP * 0.2), run_time=0.7)
        self.at(20.83)
        self.play(FadeIn(ids[1], shift=UP * 0.2), run_time=0.7)

        ok = VGroup(
            t("乱码 ≠ 输入坏了", 38, GREEN, "BOLD"),
            t("只是显示不友好", 30, MUTED),
        ).arrange(DOWN, buff=0.3)
        ok.next_to(ids, DOWN, buff=1.0)
        self.at(24.45)
        self.play(FadeIn(ok, scale=0.9), run_time=0.8)
        self.at(27.98)
        self.pad_to_voice()


# ---------------- S6 纯中文 + strawberry ----------------
class S6(_Base):
    def construct(self):
        self.footer()
        head = self.head("换句纯中文试试")

        # 页 1：6 个 token
        sent = t("今天天气真好，适合出去玩", 38, WHITE, "BOLD")
        sent.next_to(head, DOWN, buff=1.1)
        self.fit_width(sent, 0.9)
        self.at(0.89)
        self.play(FadeIn(sent, shift=UP * 0.2), run_time=0.7)

        toks = token_blocks(["今天", "天气", "真好", "，", "适合", "出去玩"], size=0.8)
        toks.next_to(sent, DOWN, buff=0.9)
        self.fit_width(toks, 0.92)
        self.at(4.45)
        for b in toks:
            self.play(FadeIn(b, scale=0.85), run_time=0.12)
        self.at(8.02)
        big = VGroup(
            t("6", 60, YELL, "BOLD"),
            t("个 token", 40, YELL, "BOLD"),
        ).arrange(RIGHT, buff=0.3)
        big.next_to(toks, DOWN, buff=0.8)
        self.play(FadeIn(big, scale=0.85), run_time=0.7)
        edge = t("边界不按人类的词划线", 32, MUTED).next_to(big, DOWN, buff=0.7)
        self.at(11.58)
        self.play(FadeIn(edge), run_time=0.6)

        # 页 2：strawberry → st / raw / berry
        self.at(15.14)
        self.play(*[FadeOut(m, shift=DOWN * 0.2) for m in (sent, toks, big, edge)], run_time=0.5)
        back = t("再看开头的 strawberry", 36, WHITE, "BOLD").next_to(head, DOWN, buff=1.0)
        self.play(FadeIn(back, shift=UP * 0.2), run_time=0.6)
        self.at(16.92)
        cut = token_blocks(["st", "raw", "berry"], color=YELL, size=0.95)
        cut.next_to(back, DOWN, buff=0.9)
        self.play(FadeIn(cut, scale=0.9), run_time=0.8)

        concl = VGroup(
            t("不是逐字母清单", 36, RED, "BOLD"),
            t("而是三个碎片", 36, GREEN, "BOLD"),
        ).arrange(DOWN, buff=0.3)
        concl.next_to(cut, DOWN, buff=1.0)
        self.at(20.48)
        self.play(FadeIn(concl, scale=0.9), run_time=0.8)
        self.at(23.87)
        self.pad_to_voice()


# ---------------- S7 切法为什么影响使用 ----------------
class S7(_Base):
    def construct(self):
        self.footer()
        head = self.head("切法不同，影响使用")

        # 页 1：token 多 → 窗口小 / 费用高（嵌套文字逐一限宽，防溢出）
        more = t("token 越多", 44, YELL, "BOLD").next_to(head, DOWN, buff=1.2)
        self.at(0.86)
        self.play(FadeIn(more, scale=0.9), run_time=0.7)

        def impact_box(title: str, sub: str, col: str):
            box = Rectangle(height=1.5, width=3.3, color=col, fill_color=col, fill_opacity=0.14)
            tt = t(title, 32, col, "BOLD")
            tt.set_width(box.width * 0.85)
            ss = t(sub, 26, WHITE)
            ss.set_width(box.width * 0.8)
            return VGroup(box, VGroup(tt, ss).arrange(DOWN, buff=0.15))

        box1 = impact_box("上下文窗口", "能放的原文更少", CYAN)
        box2 = impact_box("API 费用", "按 token 计量，用量更高", RED)
        cols = VGroup(box1, box2).arrange(RIGHT, buff=1.2)
        cols.next_to(more, DOWN, buff=1.0)
        self.fit_width(cols, 0.92)
        self.at(2.59)
        self.play(FadeIn(box1, shift=UP * 0.1), run_time=0.7)
        self.at(5.18)
        self.play(FadeIn(box2, shift=UP * 0.1), run_time=0.7)

        # 页 2：三个字符串（结论直接接在下方，不切页）
        self.at(9.07)
        self.play(*[FadeOut(m, shift=DOWN * 0.2) for m in (more, box1, box2)], run_time=0.5)
        s1 = t("中文说明", 34, WHITE, "BOLD")
        s2 = t("Python 函数", 34, WHITE, "BOLD")
        s3 = t("7B + UTF-8", 34, WHITE, "BOLD")
        rows = VGroup(
            VGroup(s1, Rectangle(height=0.5, width=2.4, color=YELL, fill_color=YELL, fill_opacity=0.7)).arrange(RIGHT, buff=0.7),
            VGroup(s2, Rectangle(height=0.5, width=3.6, color=CYAN, fill_color=CYAN, fill_opacity=0.7)).arrange(RIGHT, buff=0.7),
            VGroup(s3, Rectangle(height=0.5, width=4.8, color=GREEN, fill_color=GREEN, fill_opacity=0.7)).arrange(RIGHT, buff=0.7),
        )
        rows.arrange(DOWN, buff=0.75)
        rows.next_to(head, DOWN, buff=1.1)
        self.fit_width(rows, 0.92)
        cap = t("三个字符串，长度差不多，token 数却完全不同", 30, MUTED).next_to(rows, DOWN, buff=0.9)
        self.fit_width(cap, 0.9)
        for r in rows:
            self.play(FadeIn(r, shift=UP * 0.15), run_time=0.7)
        self.at(14.26)
        self.play(FadeIn(cap), run_time=0.6)

        # 结论（承接上方，不切页）
        self.at(17.28)
        concl = VGroup(
            t("数“字”不够，数“词”也不够", 38, RED, "BOLD"),
            t("真正进模型的是 token 序列", 38, YELL, "BOLD"),
        ).arrange(DOWN, buff=0.5)
        concl.next_to(cap, DOWN, buff=0.9)
        self.play(FadeIn(concl, scale=0.9), run_time=0.9)
        self.at(22.98)
        self.pad_to_voice()


# ---------------- S8 方法对比 + 链路 + 品牌尾卡 ----------------
class S8(_Base):
    def construct(self):
        self.footer("数解AI · 大模型原理")
        head = self.head("BPE 只是其中一种")

        # 页 1：三种方法（文字限宽防溢出）
        methods = VGroup()
        for name, desc, col in [("BPE", "找最高频片段合并", YELL),
                                ("WordPiece", "选提升模型概率的", CYAN),
                                ("Unigram", "从大词表删不重要的", GREEN)]:
            box = Rectangle(height=1.8, width=2.2, color=col, fill_color=col, fill_opacity=0.12)
            title = t(name, 34, col, "BOLD")
            title.set_width(box.width * 0.85)
            d = t(desc, 24, WHITE)
            d.set_width(box.width * 0.8)
            methods.add(VGroup(box, VGroup(title, d).arrange(DOWN, buff=0.2)))
        methods.arrange(RIGHT, buff=0.7)
        methods.next_to(head, DOWN, buff=1.2)
        self.fit_width(methods, 0.92)
        self.at(0.72)
        for m in methods:
            self.play(FadeIn(m, shift=UP * 0.08), run_time=0.6)

        goal = VGroup(
            t("目标一样：", 30, MUTED),
            t("常见的短一点，罕见的也能表示", 34, YELL, "BOLD"),
        ).arrange(RIGHT, buff=0.4)
        goal.next_to(methods, DOWN, buff=0.9)
        self.fit_width(goal, 0.92)
        self.at(8.53)
        self.play(FadeIn(goal, scale=0.9), run_time=0.7)

        # 页 2：整条链路（两行蛇形，避免单行 7 节点拥挤）
        self.at(13.92)
        self.play(*[FadeOut(m, shift=DOWN * 0.2) for m in (methods, goal)], run_time=0.5)
        r1_specs = [("文字", WHITE), ("预分词", MUTED), ("字节", CYAN), ("BPE 合并", YELL)]
        r2_specs = [("token", GREEN), ("token ID", YELL), ("嵌入向量", CYAN)]

        def node_row(specs):
            row = VGroup()
            for lab, col in specs:
                row.add(boxed_text(lab, 1.75, 1.0, col, 26, col if col != MUTED else WHITE, bold=True))
                if row.__len__() < len(specs):
                    row.add(Arrow(LEFT * 0.3, RIGHT * 0.3, color=MUTED, stroke_width=4))
            row.arrange(RIGHT, buff=0.12)
            return row

        r1 = node_row(r1_specs)
        r2 = node_row(r2_specs)
        chain = VGroup(r1, r2).arrange(DOWN, buff=0.85)
        chain.next_to(head, DOWN, buff=1.3)
        self.fit_width(chain, 0.95)
        bend = Arrow(r1.get_bottom(), r2.get_top(), color=YELL, stroke_width=5, buff=0.1)
        for i, m in enumerate(r1):
            if i % 2 == 0:
                self.play(FadeIn(m, shift=UP * 0.1), run_time=0.25)
            else:
                self.play(Create(m), run_time=0.2)
        self.play(Create(bend), run_time=0.3)
        for i, m in enumerate(r2):
            if i % 2 == 0:
                self.play(FadeIn(m, shift=UP * 0.1), run_time=0.25)
            else:
                self.play(Create(m), run_time=0.2)

        q1 = t("下一篇：token ID 怎么变成坐标？", 34, WHITE, "BOLD").next_to(chain, DOWN, buff=1.0)
        self.fit_width(q1, 0.9)
        self.at(23.35)
        self.play(FadeIn(q1, shift=UP * 0.2), run_time=0.7)

        # 品牌尾卡
        self.at(26.04)
        self.play(*[FadeOut(m, shift=DOWN * 0.25) for m in (head, chain, q1)], run_time=0.7)

        logo = ImageMobject("avatar-sjai-round.png")
        logo.scale_to_fit_width(3.6)
        logo.move_to(UP * config.frame_height * 0.105)  # 上移，保证尾卡文字最低点距底 ≥399px 不撞字幕
        follow = VGroup(
            t("关注「数解AI」", 44, YELL, "BOLD"),
            t("《BPE分词：AI为什么把文字切成碎片？》", 26, WHITE, "BOLD"),
            t("查看公众号文章 · 图文全解", 24, GREEN),
            t("下一篇：词嵌入 · 5 万个 0 变坐标", 22, MUTED),
        ).arrange(DOWN, buff=0.4)
        follow.next_to(logo, DOWN, buff=0.8)
        self.play(FadeIn(logo, scale=0.9), run_time=0.8)
        self.play(FadeIn(follow, scale=0.85), run_time=0.8)
        self.at(30.08)
        self.pad_to_voice()


# ---------------- 封面（视频号竖屏封面，-s 渲染单帧） ----------------
class Cover(Scene):
    """封面帧：品牌条 + 系列标签 + 主/副标题 + 关键视觉。
    渲染：python3 -m manim render -qm -s scenes.py Cover
    """
    def construct(self):
        brand = t("数解AI · 大模型原理", 20, MUTED).to_edge(DOWN, buff=1.15)
        series = t("大模型原理 · 第 1 篇", 26, CYAN).to_edge(UP, buff=1.4)
        title = t("BPE 分词", 54, YELL, "BOLD").next_to(series, DOWN, buff=0.55)
        subtitle = t("AI 为什么把文字切成碎片？", 34, WHITE).next_to(title, DOWN, buff=0.35)

        # 关键视觉：strawberry → st / raw / berry
        sb = letter_blocks("strawberry", hi={"r"}, size=0.6)
        arrow = t("→", 40, MUTED, "BOLD")
        cut = token_blocks(["st", "raw", "berry"], color=YELL, size=0.85)
        stage = VGroup(sb, arrow, cut).arrange(RIGHT, buff=0.5)
        stage.next_to(subtitle, DOWN, buff=1.3)
        stage.set_width(config.frame_width * 0.92)

        self.add(brand, series, title, subtitle, stage)


if __name__ == "__main__":
    pass
