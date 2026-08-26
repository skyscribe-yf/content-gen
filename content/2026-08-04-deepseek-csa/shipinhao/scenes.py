#!/usr/bin/env python3
"""《DeepSeek-V4 为什么不用 MLA？》视频号场景（布局重写版 2026-08-27）。

- 6 个场景 S1-S6，与 storyboard.md 一一对应（2026-08-25 拍板 6 段收紧）
- 配音：MiniMax 精英男声 male-qn-jingying（speed 1.0 pitch +2）——音轨未动
- 时间轴锚点 = tts/sentence-boundaries.json 的 clip id（at_clip 精确挂接）
- 布局按最新规范（2026-08-26/27）：
  * 矮页（1-4 行文字/结论页）→ page_auto（语义标点拆行 + 字号放大 + 垂直居中，无中间空洞）
  * 多元素/图表/卡片页 → page_stack + layout_page（内容高度 ≥ 显示带 80%）
  * 段内换页 FadeOut（带齐本页全部元素，A3 对账），段末统一 transition_out（S6 尾卡除外）
  * 动画降噪（决策 #51）：每页 1 个主视觉动效；emphasize 全片仅 2 处（S2 L²、S3 条收缩）
- 概念图：img/s1-longctx-round.png、s2-compress-round.png、s4-hca-round.png（AI 图禁数字）
- 数字全部脚本画图：S5 四个百分比 counter_value；S3 L→L/m 条收缩 Transform（不编造数字）
"""
from __future__ import annotations

import pathlib
import sys


def _scripts_dir() -> str:
    p = pathlib.Path(__file__).resolve().parent
    for _ in range(6):
        candidate = p / "scripts"
        if (candidate / "manim_helpers.py").exists():
            return str(candidate)
        p = p.parent
    raise RuntimeError("找不到 scripts/manim_helpers.py")


sys.path.insert(0, _scripts_dir())
from manim_helpers import *


IMG = pathlib.Path(__file__).resolve().parent / "img"
ROOT = pathlib.Path(__file__).resolve().parent.parent.parent.parent  # content-gen/

# ffprobe tts/s1.wav ... tts/s6.wav（精英男声 male-qn-jingying，speed 1.0 pitch +2）
VOICE_DUR = {
    "S1": 21.85,
    "S2": 39.00,
    "S3": 36.86,
    "S4": 34.39,
    "S5": 37.29,
    "S6": 36.15,
}
TAIL = 2.5


def _header(label: str):
    return fit(t(label, 34, YELL, "BOLD"), 0.86).to_edge(UP, buff=1.12)


def _footer(scene):
    footer = t("数解AI · DeepSeek 技术解密", 20, MUTED).to_edge(DOWN, buff=1.15)
    scene.add(footer)
    return footer


def _fit(mob, max_w: float = 7.7):
    if mob.width > max_w:
        mob.set_width(max_w)
    return mob


def _label(text: str, size: float = 32, color: str = WHITE, weight: str = "BOLD"):
    return _fit(t(text, size, color, weight))


def _block(lines, size: float = 50, color: str = WHITE, weight: str = "BOLD",
           sub_size: float = 34, sub_color: str = MUTED):
    main = _fit(t(lines[0], size, color, weight))
    if len(lines) == 1:
        return main
    sub = _fit(t(lines[1], sub_size, sub_color))
    return VGroup(main, sub).arrange(DOWN, buff=0.16)


def _image_mob(name: str, width: float) -> ImageMobject:
    image = ImageMobject(str(IMG / name))
    image.scale_to_fit_width(width)
    return image


def _chip(letter: str, color: str, size: float = 0.95) -> VGroup:
    """小徽章：圆角方块 + 字母（徽章组 FadeIn 合规）。"""
    box = RoundedRectangle(corner_radius=0.18, width=size, height=size,
                           color=color, stroke_width=2.5,
                           fill_color=CARD_FILL, fill_opacity=1.0)
    txt = t(letter, 30, WHITE, "BOLD")
    return VGroup(box, txt)


def _fade_page(scene, *items, run_time: float = 0.5):
    """段内换页：带走本页全部元素（A3 对账），轻微上移淡出。"""
    scene.play(FadeOut(Group(*items), shift=UP * 0.03), run_time=run_time)


# ---------------- S1 开场钩子：存不下 -> 找不动 ----------------
class S1(_Base):
    def construct(self):
        self.bg()
        footer = _footer(self)
        head = _header("百万上下文：存不下，还是找不动？")
        note0 = t("以 DeepSeek-V4 为例", 24, MUTED).next_to(head, DOWN, buff=0.5)

        # 页 1（矮页）：双卡对比 + 结论行
        save = _block(("「存不下」", "每个位置存储太贵"), 50, CYAN, "BOLD", 34)
        find = _block(("「找不动」", "位置数量太多"), 50, YELL, "BOLD", 34)
        line = _label("MLA 解决了前者，后者才要命", 46, WHITE, "BOLD")
        page1 = page_auto(save, find, line)

        # 页 2：概念图（长上下文，重点被淹）
        img = _image_mob("s1-longctx-round.png", 5.4)
        cap = _label("百万 token 历史，重点被淹没了", 40, WHITE, "BOLD")
        page2 = page_stack(img, cap, buff=1.1)
        layout_page(page2)

        # 页 3（矮页）：答案 + 悬念
        v4 = _label("V4：CSA + HCA 混合注意力", 56, YELL, "BOLD")
        q = _label("MLA 已经很省，为什么非要换？", 48, WHITE, "BOLD")
        page3 = page_auto(v4, q)

        self.at_clip("s1-c01")
        self.play_parallel(type_in(head, run_time=0.7), FadeIn(note0, shift=DOWN * 0.05),
                           run_time=0.7)
        self.at_clip("s1-c02")
        self.play(type_in(save, run_time=0.62), run_time=0.62)
        self.at_clip("s1-c03")
        self.play_parallel(type_in(find, run_time=0.62), type_in(line, run_time=0.6),
                           run_time=0.62)  # 对比卡 + 结论行同拍
        self.at_clip("s1-c04")
        _fade_page(self, page1)
        self.play(FadeIn(img, shift=DOWN * 0.05), run_time=0.7)
        self.at_clip("s1-c05")
        self.play(type_in(cap, run_time=0.6), run_time=0.6)
        _fade_page(self, page2, run_time=0.45)
        self.at_clip("s1-c06")
        self.play(type_in(v4, run_time=0.65), run_time=0.65)
        self.at_clip("s1-c07")
        self.play(type_in(q, run_time=0.8), run_time=0.8)
        self.transition_out(head, footer, note0, v4, q, run_time=0.6)
        self.pad_to_voice()


# ---------------- S2 注意力成本 + DSA ----------------
class S2(_Base):
    def construct(self):
        self.bg()
        footer = _footer(self)
        head = _header("注意力：读得越多，越卡")

        # 页 1（矮页 + 徽章行）：Q-K 相关性 + L² 平方增长
        t1 = _label("Q 和 K 比相关性，再加权 V", 48, WHITE, "BOLD")
        qc = _chip("Q", CYAN)
        kc = _chip("K", CYAN)
        vc = _chip("V", GREEN)
        chips = VGroup(qc, kc, vc).arrange(RIGHT, buff=1.15)
        l2 = _label("历史长度 L：配对数 ≈ L²", 50, YELL, "BOLD")
        note = _label("长上下文，就是被这个平方项卡住", 40, MUTED)
        page1 = page_auto(t1, chips, l2, note)

        # 页 2（矮页 + 徽章行）：DSA 索引器打分 + TopK
        idx = _label("DSA：轻量索引器打分", 46, CYAN, "BOLD")
        cells = VGroup(*[
            RoundedRectangle(corner_radius=0.15, width=0.62, height=0.62,
                             color=MUTED, stroke_width=2.5,
                             fill_color=CARD_FILL, fill_opacity=1.0)
            for _ in range(8)
        ]).arrange(RIGHT, buff=0.2)
        selected = cells[2:5]
        topk = _label("只保留最高的 k 个位置", 50, GREEN, "BOLD")
        core = _label("核心注意力从此只读这 k 个位置", 46, WHITE, "BOLD")
        page2 = page_auto(idx, cells, topk, core)

        # 页 3（矮页）：索引器仍面对长序列（痛点）
        prob = _label("可索引器面对的，", 46, WHITE, "BOLD")
        met = _label("仍是整段原始历史 —— 目录，", 46, WHITE, "BOLD")
        met2 = _label("还得从整本书逐页扫出来", 50, YELL, "BOLD")
        q = _label("这瓶颈，堵住了吗？", 56, YELL, "BOLD")
        page3 = page_auto(prob, met, met2, q)

        self.at_clip("s2-c01")
        self.play_parallel(type_in(head, run_time=0.7), type_in(t1, run_time=0.7),
                           run_time=0.7)
        self.at_clip("s2-c02")
        self.play(FadeIn(qc, shift=DOWN * 0.05), run_time=0.4)
        self.at_clip("s2-c03")
        self.play(FadeIn(kc, shift=DOWN * 0.05), run_time=0.4)
        self.at_clip("s2-c04")
        self.play(FadeIn(vc, shift=DOWN * 0.05), run_time=0.5)
        self.at_clip("s2-c06")
        self.play(type_in(l2, run_time=0.7), run_time=0.7)
        self.emphasize(l2, run_time=0.8)
        self.at_clip("s2-c07")
        self.play(type_in(note, run_time=0.6), run_time=0.6)
        _fade_page(self, page1)
        self.at_clip("s2-c08")
        self.play(type_in(idx, run_time=0.6), run_time=0.6)
        self.at_clip("s2-c09")
        self.play(FadeIn(cells, shift=DOWN * 0.05), run_time=0.5)
        self.at_clip("s2-c10")
        self.play_parallel(type_in(topk, run_time=0.6),
                           *[c.animate.set_fill(GREEN, opacity=0.9) for c in selected],
                           run_time=0.6)
        self.at_clip("s2-c11")
        self.play(type_in(core, run_time=0.6), run_time=0.6)
        _fade_page(self, page2)
        self.at_clip("s2-c12")
        self.play(type_in(prob, run_time=0.6), run_time=0.6)
        self.at_clip("s2-c13")
        self.play(type_in(met, run_time=0.7), run_time=0.7)
        self.at_clip("s2-c14")
        self.play(type_in(met2, run_time=0.6), run_time=0.6)
        self.at_clip("s2-c15")
        self.play(type_in(q, run_time=0.7), run_time=0.7)
        self.transition_out(head, footer, prob, met, met2, q, run_time=0.6)
        self.pad_to_voice()


# ---------------- S3 CSA：先压成目录，再选章节 ----------------
class S3(_Base):
    def construct(self):
        self.bg()
        footer = _footer(self)
        head = _header("CSA：先把整本书压成目录")

        # 页 1：概念图（书压成目录）
        img = _image_mob("s2-compress-round.png", 5.4)
        cap = _label("整本书，压成紧凑目录", 40, WHITE, "BOLD")
        page1 = page_stack(img, cap, buff=1.1)
        layout_page(page1)

        # 页 2（矮页 + 徽章行）：压缩块 + 双流重叠
        block = _label("每个压缩块覆盖 m 个 token", 50, WHITE, "BOLD")
        cells = VGroup(*[
            RoundedRectangle(corner_radius=0.15, width=0.75, height=0.75,
                             color=CYAN, stroke_width=2.5,
                             fill_color=CARD_FILL, fill_opacity=1.0)
            for _ in range(4)
        ]).arrange(RIGHT, buff=0.25)
        streams = _label("双流重叠：相邻摘要共享范围", 48, CYAN, "BOLD")
        note = _label("避免块边界切断依赖", 40, MUTED)
        page2 = page_auto(block, cells, streams, note)

        # 页 3：候选条收缩（主视觉）：L → L/m（不编造具体数字）
        lab = _label("压缩条目数量", 42, WHITE, "BOLD")
        row = VGroup(t("L", 60, YELL, "BOLD"), t("→", 46, MUTED, "BOLD"),
                     t("L/m", 60, GREEN, "BOLD")).arrange(RIGHT, buff=0.5)
        bar_wide = Rectangle(width=5.8, height=1.3, color=YELL,
                             fill_color=YELL, fill_opacity=0.85)
        bar_short = Rectangle(width=1.6, height=1.3, color=GREEN,
                              fill_color=GREEN, fill_opacity=0.85)
        bar_short.move_to(bar_wide.get_center())
        tag = _label("候选池长度", 34, MUTED)
        page3 = page_stack(lab, row, bar_wide, tag, buff=1.5)
        layout_page(page3)

        # 页 4（矮页）：索引器面对压缩条目
        l1 = _label("索引器面对的，更短的压缩条目", 46, WHITE, "BOLD")
        topk = _label("候选池变小，扫描成本跟着缩小", 50, YELL, "BOLD")
        core = _label("核心注意力，只读选中的条目", 46, GREEN, "BOLD")
        page4 = page_auto(l1, topk, core)

        self.at_clip("s3-c01")
        self.play_parallel(type_in(head, run_time=0.7), FadeIn(img, shift=DOWN * 0.05),
                           run_time=0.7)
        self.at_clip("s3-c02")
        self.play(type_in(cap, run_time=0.6), run_time=0.6)
        _fade_page(self, page1)
        self.at_clip("s3-c04")
        self.play_parallel(type_in(block, run_time=0.6), FadeIn(cells, shift=DOWN * 0.05),
                           run_time=0.6)
        self.at_clip("s3-c06")
        self.play(type_in(streams, run_time=0.6), run_time=0.6)
        self.at_clip("s3-c07")
        self.play(type_in(note, run_time=0.6), run_time=0.6)
        _fade_page(self, page2)
        self.at_clip("s3-c08")
        self.play_parallel(type_in(lab, run_time=0.5), FadeIn(row, shift=DOWN * 0.05),
                           type_in(tag, run_time=0.5), run_time=0.6)
        # 主视觉：条出现 → 收缩 L→L/m → 强调，Succession 单 play 连拍（同 clip 内，不插锚点）
        self.play(Succession(
            FadeIn(bar_wide, shift=DOWN * 0.05, run_time=0.3),
            Transform(bar_wide, bar_short, run_time=1.0),
            Indicate(bar_wide, color=YELL, run_time=0.7),
        ))
        _fade_page(self, page3, run_time=0.45)
        self.at_clip("s3-c09")
        self.play(type_in(l1, run_time=0.7), run_time=0.7)
        self.at_clip("s3-c12")
        self.play(type_in(topk, run_time=0.7), run_time=0.7)
        self.at_clip("s3-c13")
        self.play(type_in(core, run_time=0.7), run_time=0.7)
        self.transition_out(head, footer, l1, topk, core, run_time=0.6)
        self.pad_to_voice()


# ---------------- S4 HCA 更狠，不挑 ----------------
class S4(_Base):
    def construct(self):
        self.bg()
        footer = _footer(self)
        head = _header("HCA：压得更狠，不挑章节")

        # 页 1：概念图（精读 vs 概览）
        img = _image_mob("s4-hca-round.png", 5.5)
        cap = _label("CSA 精读重点 · HCA 快速概览", 50, WHITE, "BOLD")
        csa_txt = _label("CSA 挑章节", 36, CYAN, "BOLD")
        hca_txt = _label("HCA 短摘要", 36, GREEN, "BOLD")
        chips = Group(csa_txt, hca_txt).arrange(RIGHT, buff=1.0)
        page1 = page_stack(img, cap, chips, buff=1.4)
        layout_page(page1)

        # 页 2：m token → 摘要（主视觉：合并）
        sum_lab = _label("每 m 个 token，直接汇成一个摘要", 54, WHITE, "BOLD")
        cells = VGroup(*[
            RoundedRectangle(corner_radius=0.15, width=1.0, height=1.0,
                             color=CYAN, stroke_width=2.5,
                             fill_color=CARD_FILL, fill_opacity=1.0)
            for _ in range(3)
        ]).arrange(RIGHT, buff=0.3)
        big = RoundedRectangle(corner_radius=0.18, width=2.8, height=1.7,
                               color=GREEN, stroke_width=2.5,
                               fill_color=CARD_FILL, fill_opacity=1.0)
        visual = Group(cells, big).arrange(RIGHT, buff=1.2)
        merge = Arrow(cells.get_right(), big.get_left(), color=MUTED,
                      buff=0.12, stroke_width=5)
        visual.add(merge)
        dense = _label("序列足够短，直接做稠密注意力", 52, YELL, "BOLD")
        page2 = page_stack(sum_lab, visual, dense, buff=2.1)
        layout_page(page2)

        # 页 3（矮页）：总结 + 悬念
        read = _label("CSA：挑几章精读", 44, CYAN, "BOLD")
        cover = _label("HCA：极短摘要保全局", 44, GREEN, "BOLD")
        hybrid = _label("交替堆叠 = 混合注意力", 50, YELL, "BOLD")
        q = _label("到底省了多少？", 54, WHITE, "BOLD")
        page3 = page_auto(read, cover, hybrid, q)

        self.at_clip("s4-c01")
        self.play_parallel(type_in(head, run_time=0.7), FadeIn(img, shift=DOWN * 0.05),
                           run_time=0.9)
        self.at_clip("s4-c03")
        self.play_parallel(type_in(cap, run_time=0.6), type_in(csa_txt, run_time=0.5),
                           type_in(hca_txt, run_time=0.5), run_time=0.6)
        self.wait(1.4)  # 页 1 驻留（对应「HCA 压得更狠，不做稀疏选择」台词）
        _fade_page(self, page1, run_time=0.45)
        self.at_clip("s4-c04")
        self.play_parallel(type_in(sum_lab, run_time=0.7), FadeIn(cells, shift=DOWN * 0.05),
                           run_time=0.7)
        self.at_clip("s4-c05")
        self.play_parallel(Create(merge), FadeIn(big, shift=DOWN * 0.05), run_time=0.6)
        self.at_clip("s4-c06")
        self.play(type_in(dense, run_time=0.6), run_time=0.6)
        _fade_page(self, page2)
        self.at_clip("s4-c07")
        self.play(type_in(read, run_time=0.6), run_time=0.6)
        self.at_clip("s4-c08")
        self.play(type_in(cover, run_time=0.6), run_time=0.6)
        self.at_clip("s4-c10")
        self.play(type_in(hybrid, run_time=0.6), run_time=0.6)
        self.at_clip("s4-c12")
        self.play(type_in(q, run_time=0.7), run_time=0.7)
        self.transition_out(head, footer, read, cover, hybrid, q, run_time=0.6)
        self.pad_to_voice()


# ---------------- S5 论文数字 ----------------
class S5(_Base):
    def construct(self):
        self.bg()
        footer = _footer(self)
        head = _header("1M 上下文：到底省了多少？")

        # 页 1：V4-Pro 27% / 10%（counter 主视觉）
        t1 = _label("V4-Pro 相对 V3.2（1M 上下文）", 48, WHITE, "BOLD")
        lab1 = _label("推理 FLOPs", 48, CYAN, "BOLD")
        slot1 = dynamic_slot(2.8, 1.7)
        lab2 = _label("KV 缓存", 48, GREEN, "BOLD")
        slot2 = dynamic_slot(2.8, 1.7)
        row1 = stable_row(lab1, slot1, buff=0.6)
        row2 = stable_row(lab2, slot2, buff=0.6)
        page1 = page_stack(t1, row1, row2, buff=2.0)
        layout_page(page1)

        # 页 2：V4-Flash 10% / 7%（counter 主视觉）
        t2 = _label("V4-Flash 更激进", 48, WHITE, "BOLD")
        lab3 = _label("推理 FLOPs", 48, CYAN, "BOLD")
        slot3 = dynamic_slot(2.8, 1.7)
        lab4 = _label("KV 缓存", 48, GREEN, "BOLD")
        slot4 = dynamic_slot(2.8, 1.7)
        row3 = stable_row(lab3, slot3, buff=0.6)
        row4 = stable_row(lab4, slot4, buff=0.6)
        page2 = page_stack(t2, row3, row4, buff=2.0)
        layout_page(page2)

        # 页 3：模型卡
        pro = _card("Pro：1.6T 参数 · 49B 激活 · 1M 上下文", 6.4, 1.9, CYAN, WHITE, 30)
        flash = _card("Flash：284B 参数 · 13B 激活 · 1M 上下文", 6.4, 1.9, GREEN, WHITE, 30)
        note = _label("1M 场景的估算比较", 40, MUTED)
        note2 = _label("不是所有任务都固定快这么多", 40, MUTED)
        page3 = page_stack(pro, flash, note, note2, buff=1.25)
        layout_page(page3)

        self.at_clip("s5-c01")
        self.play_parallel(type_in(head, run_time=0.7), type_in(t1, run_time=0.6),
                           run_time=0.7)
        self.at_clip("s5-c02")
        self.play(type_in(lab1, run_time=0.6), run_time=0.6)
        self.at_clip("s5-c03")
        cnt1 = self.counter_value(0, 27, suffix="%", size=64, color=YELL,
                                  run_time=1.2, anchor=slot1)
        self.at_clip("s5-c04")
        cnt2 = self.counter_value(0, 10, suffix="%", size=64, color=YELL,
                                  run_time=1.0, anchor=slot2,
                                  extra_anims=[type_in(lab2, 0.6)])
        _fade_page(self, page1, cnt1, cnt2, run_time=0.45)
        self.at_clip("s5-c05")
        self.play(type_in(t2, run_time=0.6), run_time=0.6)
        self.at_clip("s5-c06")
        cnt3 = self.counter_value(0, 10, suffix="%", size=64, color=YELL,
                                  run_time=1.0, anchor=slot3,
                                  extra_anims=[type_in(lab3, 0.6)])
        self.at_clip("s5-c07")
        cnt4 = self.counter_value(0, 7, suffix="%", size=64, color=YELL,
                                  run_time=1.0, anchor=slot4,
                                  extra_anims=[type_in(lab4, 0.6)])
        _fade_page(self, page2, cnt3, cnt4, run_time=0.45)
        self.at_clip("s5-c08")
        self.play_scroll_unroll(pro, run_time=0.9)
        self.at_clip("s5-c11")
        self.play_scroll_unroll(flash, run_time=1.0)
        self.at_clip("s5-c13")
        self.play(type_in(note, run_time=0.6), run_time=0.6)
        self.at_clip("s5-c14")
        self.play(type_in(note2, run_time=0.6), run_time=0.6)
        self.transition_out(head, footer, pro, flash, note, note2, run_time=0.6)
        self.pad_to_voice()


# ---------------- S6 总结 + 品牌尾卡 ----------------
class S6(_Base):
    def construct(self):
        self.bg()
        footer = _footer(self)
        head = _header("注意力的下一步：少找一点")

        # 页 1：四机制总结链
        intro = _label("每一步，都在处理上一步的瓶颈", 40, MUTED)
        mla = _card("MLA 压缩存储", 4.8, 1.3, CYAN, WHITE, 28)
        dsa = _card("DSA 减少精读", 4.8, 1.3, GREEN, WHITE, 28)
        csa = _card("CSA 缩短候选池", 4.8, 1.3, YELL, WHITE, 28)
        hca = _card("HCA 保留全局", 4.8, 1.3, CYAN, WHITE, 28)
        page1 = page_stack(intro, mla, dsa, csa, hca, buff=0.6)
        layout_page(page1)

        # 页 2：核心观点（大卡 + 支撑）
        key2 = _card("不是 MLA 不行了，而是百万上下文要求位置本身也变少", 6.6, 5.6, YELL, WHITE, 52)
        sub = _label("每一步都在解决上一步的瓶颈", 44, MUTED)
        page2 = page_stack(key2, sub, buff=1.0)
        layout_page(page2)

        # 页 3（矮页）：下一篇预告
        next_ = _label("下一篇：K=V、Partial RoPE、de-RoPE", 42, GREEN, "BOLD")
        q1 = _label("一个压缩条目，能同时当键和值？", 42, WHITE, "BOLD")
        q2 = _label("Partial RoPE 为什么只旋转最后 64 维？", 42, WHITE, "BOLD")
        page3 = page_auto(next_, q1, q2)

        # 页 4：品牌尾卡（四要素 + 互动问题）
        avatar = ImageMobject(str(ROOT / "avatar-sjai-round.png"))
        avatar.scale_to_fit_width(3.0)
        follow = _label("关注「数解AI」", 46, YELL, "BOLD")
        title = _fit(t("《DeepSeek-V4 为什么不用 MLA？》", 30, WHITE, "BOLD"), 7.4)
        guide = _label("查看公众号文章 · 评论区聊聊", 30, GREEN, "BOLD")
        aq1 = _label("你选完整保留但检索贵，", 36, WHITE, "BOLD")
        aq2 = _label("还是先压缩更快、但可能漏细节？", 36, WHITE, "BOLD")
        page4 = page_stack(avatar, follow, title, guide, aq1, aq2, buff=0.5)
        layout_page(page4)

        self.at_clip("s6-c01")
        self.play(type_in(head, run_time=0.7), run_time=0.7)
        self.at_clip("s6-c02")
        self.play(type_in(intro, run_time=0.6), run_time=0.6)
        self.at_clip("s6-c03")
        self.play_scroll_unroll(mla, run_time=0.8)
        self.at_clip("s6-c04")
        self.play_scroll_unroll(dsa, run_time=0.8)
        self.at_clip("s6-c05")
        self.play_scroll_unroll(csa, run_time=0.8)
        self.at_clip("s6-c06")
        self.play_scroll_unroll(hca, run_time=0.8)
        _fade_page(self, page1, run_time=0.45)
        self.at_clip("s6-c07")
        self.play_scroll_unroll(key2, run_time=1.1)
        self.at_clip("s6-c08")
        self.play(type_in(sub, run_time=0.6), run_time=0.6)
        _fade_page(self, page2, run_time=0.45)
        self.at_clip("s6-c09")
        self.play(type_in(next_, run_time=0.7), run_time=0.7)
        self.at_clip("s6-c10")
        self.play(type_in(q1, run_time=0.7), run_time=0.7)
        self.at_clip("s6-c11")
        self.play(type_in(q2, run_time=0.7), run_time=0.7)
        self.wait(1.9)  # 预告行驻屏，对应「Partial RoPE …最后 64 维」台词
        _fade_page(self, page3, run_time=0.4)
        self.play(FadeIn(avatar, scale=1.5), run_time=0.7)
        self.at_clip("s6-c13")
        self.play(type_in(follow, run_time=0.6), run_time=0.6)
        self.play_parallel(type_in(title, run_time=0.6), type_in(guide, run_time=0.6), run_time=0.7)
        self.at_clip("s6-c14")
        self.play(type_in(aq1, run_time=0.6), run_time=0.6)
        self.at_clip("s6-c15")
        self.play(type_in(aq2, run_time=0.6), run_time=0.6)
        self.wait(0.4)
        self.pad_to_voice()
