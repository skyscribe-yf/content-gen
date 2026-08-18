#!/usr/bin/env python3
"""《DeepSeek便宜30倍的秘密：MoE混合专家入门》视频号场景。

本文件只有场景编排；通用布局、卡片和动效都在 ``scripts/manim_helpers.py``。
时间轴来源是本目录 ``tts/full.subtitle.json`` 和切分后的 ``tts/sN.wav``：
``VOICE_DUR`` 使用 ffprobe 的实测值，字幕起点换算为每个 wav 的本地时钟。
full.subtitle.json 没有 clip id，因此每个 ``self.at`` 都直接写本地字幕边界，
并在注释中标明对应的字幕条目。这样预检器不需要猜测场景偏移。
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

# ffprobe tts/s1.wav ... tts/s8.wav（2026-08-19，未使用估算值）。
VOICE_DUR = {
    "S1": 35.754667,
    "S2": 64.853333,
    "S3": 38.997333,
    "S4": 39.338667,
    "S5": 46.592000,
    "S6": 33.877333,
    "S7": 36.266667,
    "S8": 49.794708,
}
TAIL = 2.5

# full.subtitle.json 的 time_begin（毫秒）减去累计 wav 偏移（秒）后的本地句首。
# S1: subtitle[0..3]；S2: [5..9]；S3: [11..12]；S4: [14..17]；
# S5: [19..22]；S6: [24..26]；S7: [28..30]；S8: [32..35]。
# 每段开头的句子可能落在切分静音前 0.03~0.11s，故各段首帧从 0 开始，
# 后续动作严格挂到本表的句首；预检器以累计 VOICE_DUR 建立同一张本地表。
LOCAL_SUBTITLE_BOUNDARIES = {
    "S1": (0.000000, 14.821451, 20.196871, 30.711020),
    "S2": (14.883564, 27.034721, 34.592816, 47.131592, 63.102431),
    "S3": (11.976580, 26.326512, 38.779528),
    "S4": (6.137343, 18.694848, 22.514531, 35.478386),
    "S5": (13.972644, 15.853460, 24.440354, 33.786385, 46.088472),
    "S6": (2.171256, 16.451528, 24.899102, 33.165406),
    "S7": (15.983220, 19.164354, 29.794604, 35.425443),
    "S8": (14.592925, 28.385578, 37.425261, 46.097914),
}


def _header(label: str):
    return fit(t(label, 34, YELL, "BOLD"), 0.86).to_edge(UP, buff=1.12)


def _page(*mobjects, buff: float = 0.75):
    """Build the complete stable page, then apply the shared page planner."""
    page = page_stack(*mobjects, buff=buff)
    layout_page(page)
    return page


def _image(name: str, width: float) -> ImageMobject:
    image = ImageMobject(str(IMG / name))
    image.scale_to_fit_width(width)
    return image


def _footer(scene):
    footer = t("数解AI · DeepSeek 技术解密", 20, MUTED).to_edge(DOWN, buff=1.15)
    scene.add(footer)
    return footer


def _leaves(mobject):
    children = getattr(mobject, "submobjects", ())
    if not children:
        return [mobject]
    leaves = []
    for child in children:
        leaves.extend(_leaves(child))
    return leaves


def _roots_for(scene, *targets):
    """Resolve page members back to scene roots before clearing a page."""
    wanted = set()
    for target in targets:
        wanted.add(id(target))
        wanted.update(id(leaf) for leaf in _leaves(target))
    roots = []
    for root in list(scene.mobjects):
        ids = {id(root)}
        ids.update(id(leaf) for leaf in _leaves(root))
        if ids & wanted:
            roots.append(root)
    return roots


def _clear(scene, page, *extras, run_time: float = 0.28):
    roots = _roots_for(scene, page, *extras)
    if roots:
        scene.play(FadeOut(*roots), run_time=run_time)
        scene.remove(*roots)


def _transition(scene, *targets, run_time: float = 0.55):
    """Remove every visible root, including dynamic counters and decorations."""
    roots = _roots_for(scene, *targets)
    if roots:
        scene.play(
            Group(*roots).animate.shift(RIGHT * 0.85 + DOWN * 0.45).set_opacity(0),
            run_time=run_time,
            rate_func=smooth,
        )
        scene.remove(*roots)


def _result_row(name: str, multiple: str, color: str):
    label = t(name, 25, color, "BOLD")
    if label.width > 2.55:
        label.set_width(2.55)
    slot = dynamic_slot(1.85, 0.72)
    tail = t(multiple, 25, color, "BOLD")
    if tail.width > 1.50:
        tail.set_width(1.50)
    row = stable_row(label, slot, tail, buff=0.34)
    return row, (label, slot, tail)


def _reveal_page_title(scene, title, run_time: float = 0.7):
    scene.play(type_in(title, run_time), run_time=run_time)


# ---------------- S1 开场钩子 ----------------
class S1(_Base):
    def construct(self):
        self.bg()
        footer = _footer(self)
        head = _header("DeepSeek 便宜 30 倍，秘密藏在哪？")

        big = boxed("便宜 30 倍", 6.5, 2.35, YELL, 52, weight="BOLD")
        q = boxed("秘密到底藏在哪？", 6.5, 1.55, WHITE, 40, weight="BOLD")
        first = boxed("第一轮：很重\n系统提示词 · 仓库目录 · 团队规则 · 相关文件", 6.5, 2.25, CYAN, 34, weight="BOLD")
        second = boxed("第二轮：还是失败，再查一下", 6.5, 1.75, GREEN, 38, weight="BOLD")
        page1 = _page(big, q, first, second, buff=0.52)

        # subtitle[0]：开场钩子与第一轮；subtitle[1]：第二轮。
        self.play_parallel(type_in(head, 0.72), run_time=0.72)
        self.play_scroll_unroll_many(big, q, first, run_time=0.78)
        self.at(14.821451)  # subtitle[1]
        self.play_scroll_unroll_many(second, run_time=0.72)

        title2 = t("两个问题同时出现", 38, WHITE, "BOLD")
        q1 = boxed("问题 1：重复的仓库上下文，\n能不能不再重复收费？", 6.6, 2.25, CYAN, 37, weight="BOLD")
        q2 = boxed("问题 2：每个 token，\n能不能不必让所有参数同时计算？", 6.6, 2.25, GREEN, 37, weight="BOLD")
        page2 = _page(title2, q1, q2, buff=1.0)
        self.at(20.196871)  # subtitle[2]
        _clear(self, page1)
        _reveal_page_title(self, title2)
        self.play_scroll_unroll_many(q1, q2, run_time=0.74)

        title3 = t("两个答案", 38, WHITE, "BOLD")
        a1 = boxed("缓存 → 不再重复收费", 6.4, 1.95, CYAN, 40, weight="BOLD")
        a2 = boxed("MoE → 不必全参数计算", 6.4, 1.95, GREEN, 40, weight="BOLD")
        note = boxed("便宜 30 倍不是通用结论：\n输入、缓存命中和输出必须分开算", 6.4, 2.15, YELL, 34, weight="BOLD")
        page3 = _page(title3, a1, a2, note, buff=0.85)
        self.at(30.711020)  # subtitle[3]
        _clear(self, page2)
        _reveal_page_title(self, title3)
        self.play_scroll_unroll_many(a1, a2, note, run_time=0.75)
        self.at(35.649751)  # subtitle[3] end / scene tail
        self.emphasize(note, mode="circumscribe", color=YELL, run_time=0.55)
        _transition(self, head, footer, page3)
        self.pad_to_voice()


# ---------------- S2 价格账 ----------------
class S2(_Base):
    def construct(self):
        self.bg()
        footer = _footer(self)
        head = _header("先看账：官方价格（每百万 token）")

        note = boxed("价格要拆成：普通输入 · 缓存命中 · 输出", 6.7, 1.75, YELL, 38, weight="BOLD")
        unit = t("2026 年 7 月核验 · 单位：每百万 token", 29, MUTED, "BOLD")
        price_rows = [
            boxed("DeepSeek-V4 Pro   输入 ¥3 · 缓存 ¥0.025 · 输出 ¥6", 6.7, 1.35, YELL, 30),
            boxed("GLM-5.2   输入 ¥8 · 缓存 ¥2 · 输出 ¥28", 6.7, 1.35, CYAN, 30),
            boxed("GPT-5.6 Sol   输入 ¥33.99 · 缓存 ¥3.40 · 输出 ¥204", 6.7, 1.35, GREEN, 30),
            boxed("Claude Fable 5   输入 ¥67.99 · 缓存 ¥6.80 · 输出 ¥340", 6.7, 1.35, MUTED, 30),
        ]
        page1 = _page(note, unit, *price_rows, buff=0.33)

        # subtitle[4] 句首是场景首句；首卡从 0 进入，句中边界用 [5]/[6]。
        self.play_parallel(type_in(head, 0.72), run_time=0.72)
        self.play_scroll_unroll_many(note, run_time=0.72)
        self.at(14.883564)  # subtitle[5]
        self.play_parallel(type_in(unit, 0.55), run_time=0.55)
        self.play_scroll_unroll_many(price_rows[0], price_rows[1], run_time=0.72)
        self.at(27.034721)  # subtitle[6]
        self.play_scroll_unroll_many(price_rows[2], price_rows[3], run_time=0.72)

        title2 = t("每 1M 总 token 的真实结构", 37, WHITE, "BOLD")
        structure = [
            boxed("输入 99.5%", 6.5, 1.30, CYAN, 37, weight="BOLD"),
            boxed("输出 0.5%", 6.5, 1.30, YELL, 37, weight="BOLD"),
            boxed("缓存命中 95%", 6.5, 1.30, GREEN, 37, weight="BOLD"),
            boxed("新写 5%", 6.5, 1.30, YELL, 37, weight="BOLD"),
        ]
        structure_note = boxed("输入占绝大多数，而输入里大多数又命中缓存", 6.5, 1.55, WHITE, 32, weight="BOLD")
        page2 = _page(title2, *structure, structure_note, buff=0.40)
        self.at(34.592816)  # subtitle[7]
        _clear(self, page1)
        _reveal_page_title(self, title2)
        self.play_scroll_unroll_many(*structure, structure_note, run_time=0.78)

        formula = boxed("成本 = 0.995 × (0.95 × 0.025 + 0.05 × 3) + 0.005 × 6", 6.8, 1.70, YELL, 30, weight="BOLD")
        row_defs = [
            _result_row("DeepSeek-V4 Pro", "1 倍", YELL),
            _result_row("GLM-5.2", "12 倍", CYAN),
            _result_row("GPT-5.6 Sol", "29.2 倍", GREEN),
            _result_row("Claude Fable 5", "56.7 倍", MUTED),
        ]
        result_rows = [item[0] for item in row_defs]
        row_parts = [item[1] for item in row_defs]
        # Give the four result rows enough planned vertical rhythm for the
        # shared page band.  The card fitter still owns text size; this is
        # only the page-level spacing contract, not a per-card text tweak.
        page3 = _page(formula, *result_rows, buff=0.62)
        self.at(47.131592)  # subtitle[8]
        _clear(self, page2)
        self.play_scroll_unroll_many(formula, run_time=0.72)
        self.wait(0.067)  # 一帧阶段标记；同一字幕[8]内的独立可审计 reveal
        values = (0.203, 2.429, 5.924, 11.509)
        counters = []
        for index, (parts, value) in enumerate(zip(row_parts, values)):
            # Stable slot geometry is finalized before this animation.  The
            # zero-length wait separates deliberate sibling counter actions
            # for static auditing without adding a visible pause.
            name, slot, multiple = parts
            counters.append(self.counter_value(
                0,
                value,
                decimals=3,
                size=43,
                color=WHITE,
                run_time=0.55,
                anchor=slot,
                extra_anims=[type_in(name, 0.45), type_in(multiple, 0.45)],
            ))
            if index < len(row_parts) - 1:
                self.wait(0.067)
        self.at(63.102431)  # subtitle[9]
        self.emphasize(result_rows[2], mode="circumscribe", color=GREEN, run_time=0.55)
        self.emphasize(result_rows[3], mode="circumscribe", color=MUTED, run_time=0.55)
        _transition(self, head, footer, page3, *counters)
        self.pad_to_voice()


# ---------------- S3 直觉：全科会诊 vs 分诊台 ----------------
class S3(_Base):
    def construct(self):
        self.bg()
        footer = _footer(self)
        head = _header("稠密模型 vs 混合专家")

        title1 = t("稠密模型：一次全科会诊", 38, WHITE, "BOLD")
        image1 = _image("s1-consult-round.png", 4.35)
        cap1 = boxed("一个 token 进入前馈网络，相关计算单元全都参与", 6.5, 1.50, CYAN, 32, weight="BOLD")
        page1 = _page(title1, image1, cap1, buff=0.62)
        self.play_parallel(type_in(head, 0.72), run_time=0.72)
        self.play_parallel(type_in(title1, 0.65), FadeIn(image1, shift=DOWN * 0.05), run_time=0.65)
        self.play_scroll_unroll_many(cap1, run_time=0.68)

        title2 = t("MoE：先分诊，再找专家", 38, WHITE, "BOLD")
        image2 = _image("s3-triage-round.png", 4.35)
        cap2 = boxed("先看 token 状态，再决定请哪些专家；不是每份知识都同时计算", 6.5, 1.75, GREEN, 31, weight="BOLD")
        page2 = _page(title2, image2, cap2, buff=0.58)
        self.at(11.976580)  # subtitle[11]
        _clear(self, page1)
        self.play_parallel(type_in(title2, 0.68), FadeIn(image2, shift=DOWN * 0.05), run_time=0.68)
        self.play_scroll_unroll_many(cap2, run_time=0.74)

        title3 = t("DeepSeek-V3 的配置", 38, WHITE, "BOLD")
        config_rows = [
            boxed("256 个路由专家", 6.4, 1.65, CYAN, 39, weight="BOLD"),
            boxed("每个 token 只选 8 个", 6.4, 1.65, GREEN, 39, weight="BOLD"),
            boxed("另有 1 个共享专家", 6.4, 1.65, YELL, 39, weight="BOLD"),
        ]
        config_note = boxed("总容量可以很大，单次计算却不必跑完所有专家", 6.4, 1.55, WHITE, 32, weight="BOLD")
        conclusion = boxed("MoE 不是免费变大，而是只找最相关的人干活", 6.4, 1.75, YELL, 35, weight="BOLD")
        page3 = _page(title3, *config_rows, config_note, conclusion, buff=0.35)
        self.at(26.326512)  # subtitle[12]
        _clear(self, page2)
        _reveal_page_title(self, title3)
        self.play_scroll_unroll_many(*config_rows, config_note, conclusion, run_time=0.78)
        self.at(38.779528)  # subtitle[13]，段尾前的下一句边界
        self.emphasize(conclusion, mode="circumscribe", color=YELL, run_time=0.55)
        _transition(self, head, footer, page3)
        self.pad_to_voice()


# ---------------- S4 数学：打分→选人→合并 ----------------
class S4(_Base):
    def construct(self):
        self.bg()
        footer = _footer(self)
        head = _header("路由器怎么选人？")

        bridge = boxed("三步：打分 → 选人 → 合并", 6.6, 1.45, WHITE, 38, weight="BOLD")
        step1 = cnode("打分", CYAN, radius=1.0, fs=30)
        step2 = cnode("选人", GREEN, radius=1.0, fs=30)
        step3 = cnode("合并", YELL, radius=1.0, fs=30)
        steps = VGroup(step1, step2, step3).arrange(RIGHT, buff=0.55)
        arrow1 = Arrow(step1.get_right(), step2.get_left(), color=MUTED, buff=0.12, stroke_width=4)
        arrow2 = Arrow(step2.get_right(), step3.get_left(), color=MUTED, buff=0.12, stroke_width=4)
        step_group = Group(step1, arrow1, step2, arrow2, step3)
        subline = boxed("设当前 token 的表示是 x，共有 N 个专家", 6.6, 1.35, CYAN, 31)
        subline2 = boxed("为每个专家打分 → 取 Top-k → 按权重合并", 6.6, 1.35, GREEN, 31)
        page1 = _page(bridge, step_group, subline, subline2, buff=0.72)

        self.play_parallel(type_in(head, 0.72), run_time=0.72)
        self.play_parallel(type_in(bridge, 0.62), FadeIn(step_group), run_time=0.62)
        self.play_scroll_unroll_many(subline, subline2, run_time=0.70)

        title2 = t("把三步写成公式", 38, WHITE, "BOLD")
        f1 = boxed("打分：sᵢ(x) = router(x)ᵢ", 6.6, 1.75, CYAN, 37, weight="BOLD")
        f2 = boxed("选人：Top-k，取分数最高的 k 个", 6.6, 1.75, GREEN, 37, weight="BOLD")
        f3 = boxed("合并：y = Σ wᵢ(x) · Expertᵢ(x)", 6.6, 1.75, YELL, 37, weight="BOLD")
        page2 = _page(title2, f1, f2, f3, buff=0.80)
        self.at(6.137343)  # subtitle[14]
        _clear(self, page1)
        _reveal_page_title(self, title2)
        self.play_scroll_unroll_many(f1, f2, f3, run_time=0.82)

        title3 = t("256 个专家打分，只选前 8 个", 36, WHITE, "BOLD")
        cells = VGroup(*[
            Rectangle(width=0.30, height=0.30, color=CYAN, fill_color=CYAN, fill_opacity=0.55)
            for _ in range(256)
        ])
        cells.arrange_in_grid(16, 16, buff=0.02)
        selected = VGroup(*cells[:8])
        score_note = boxed("Top-8：只激活分数最高的 8 个", 6.4, 1.45, GREEN, 35, weight="BOLD")
        page3 = _page(title3, cells, score_note, buff=0.62)
        self.at(18.694848)  # subtitle[15]
        _clear(self, page2)
        _reveal_page_title(self, title3)
        self.play(FadeIn(cells, run_time=0.58))
        self.at(22.514531)  # subtitle[16]
        self.play_parallel(*[cell.animate.set_color(YELL).set_fill(YELL, opacity=0.9) for cell in selected], run_time=0.52)
        self.play_scroll_unroll_many(score_note, run_time=0.65)

        title4 = t("专家前馈计算 ≈ 全量的", 38, WHITE, "BOLD")
        fraction = boxed("8 / 256 = 1 / 32", 6.4, 2.45, YELL, 54, weight="BOLD")
        fraction_note = boxed("这是 MoE 最核心的省算力来源", 6.4, 1.80, WHITE, 32, weight="BOLD")
        title5 = t("但注意边界", 40, WHITE, "BOLD")
        bad = boxed("端到端快 32 倍", 6.4, 2.25, RED, 42, weight="BOLD")
        good = boxed("注意力、路由器、通信、内存访问都还在", 6.4, 1.45, WHITE, 32, weight="BOLD")
        tail = boxed("稀疏计算 ≠ API 价格的全部解释", 6.4, 1.65, YELL, 37, weight="BOLD")
        # 同一个 subtitle[17] 同时讲 1/32 的边界，放在一张稳定整页中，
        # 避免在同一字幕起点硬切两页造成串行 reveal 和中间残影。
        page4 = _page(title4, fraction, fraction_note, title5, bad, good, tail, buff=0.48)
        self.at(35.478386)  # subtitle[17]
        _clear(self, page3)
        _reveal_page_title(self, title4)
        self.play_scroll_unroll_many(fraction, fraction_note, bad, good, tail, run_time=0.82)
        _reveal_page_title(self, title5, run_time=0.62)
        self.wait(0.067)  # 一帧阶段标记；同一字幕内的独立纠错动作
        cross = self.play_red_cross(bad, run_time=0.60)
        _transition(self, head, footer, page4, cross)
        self.pad_to_voice()


# ---------------- S5 负载均衡 ----------------
class S5(_Base):
    def construct(self):
        self.bg()
        footer = _footer(self)
        head = _header("负载不均衡：都挤一个科室")

        title1 = t("分诊的第二个问题", 38, WHITE, "BOLD")
        image = _image("s5-queue-round.png", 4.30)
        cap = boxed("所有病人都被送往同一科 → 排队，其他科室闲着", 6.5, 1.65, RED, 33, weight="BOLD")
        page1 = _page(title1, image, cap, buff=0.62)
        self.play_parallel(type_in(head, 0.72), run_time=0.72)
        self.play_parallel(type_in(title1, 0.65), FadeIn(image, shift=DOWN * 0.05), run_time=0.65)
        self.play_scroll_unroll_many(cap, run_time=0.68)

        title2 = t("早期做法：辅助损失", 38, WHITE, "BOLD")
        tax = boxed("把拥堵变成训练目标里的税", 6.4, 1.85, CYAN, 38, weight="BOLD")
        w1 = boxed("太强：干扰原本该学的任务", 3.1, 2.05, RED, 31, weight="BOLD")
        w2 = boxed("太弱：压不住拥挤", 3.1, 2.05, MUTED, 31, weight="BOLD")
        tradeoffs = VGroup(w1, w2).arrange(RIGHT, buff=0.35)
        note2 = boxed("目标：鼓励 token 均匀分配", 6.4, 1.40, WHITE, 32, weight="BOLD")
        page2 = _page(title2, tax, tradeoffs, note2, buff=0.70)
        self.at(13.972644)  # subtitle[19]
        _clear(self, page1)
        _reveal_page_title(self, title2)
        self.play_scroll_unroll_many(tax, run_time=0.70)
        self.at(15.853460)  # subtitle[20]
        self.play_scroll_unroll_many(w1, w2, note2, run_time=0.72)

        title3 = t("DeepSeek-V3：无辅助损失负载均衡", 37, WHITE, "BOLD")
        guide = boxed("偏置调节：改谁能进候选队列", 6.4, 1.85, GREEN, 38, weight="BOLD")
        b1 = boxed("太忙：下一轮不容易入选", 3.1, 2.05, YELL, 31, weight="BOLD")
        b2 = boxed("太闲：提高入选机会", 3.1, 2.05, CYAN, 31, weight="BOLD")
        biases = VGroup(b1, b2).arrange(RIGHT, buff=0.35)
        note3 = boxed("按排队长度导流，而不是改模型要学的任务", 6.4, 1.40, WHITE, 31, weight="BOLD")
        page3 = _page(title3, guide, biases, note3, buff=0.70)
        self.at(24.440354)  # subtitle[21]
        _clear(self, page2)
        _reveal_page_title(self, title3)
        self.play_scroll_unroll_many(guide, b1, b2, note3, run_time=0.72)

        title4 = t("两种思路，解决同一个拥堵", 37, WHITE, "BOLD")
        cmp1 = boxed("辅助损失：直接改训练目标", 3.1, 2.20, CYAN, 31, weight="BOLD")
        cmp2 = boxed("偏置调节：改候选队列", 3.1, 2.20, GREEN, 31, weight="BOLD")
        compare = VGroup(cmp1, cmp2).arrange(RIGHT, buff=0.35)
        tail = boxed("解决的不是会不会回答，\n而是 token 能否稳定分散到不同 GPU 上", 6.4, 2.00, YELL, 34, weight="BOLD")
        page4 = _page(title4, compare, tail, buff=1.15)
        self.at(33.786385)  # subtitle[22]
        _clear(self, page3)
        _reveal_page_title(self, title4)
        self.play_scroll_unroll_many(cmp1, cmp2, tail, run_time=0.76)
        self.at(46.088472)  # subtitle[23]
        self.emphasize(tail, mode="circumscribe", color=YELL, run_time=0.55)
        _transition(self, head, footer, page4)
        self.pad_to_voice()


# ---------------- S6 MoE 省的是哪一段 ----------------
class S6(_Base):
    def construct(self):
        self.bg()
        footer = _footer(self)
        head = _header("MoE 省下来的，是哪一段？")

        title1 = t("Transformer 里的两段结构", 37, WHITE, "BOLD")
        token = cnode("token", YELL, radius=0.78, fs=23)
        attn = boxed("注意力层\n让 token 看上下文", 2.35, 2.0, CYAN, 30, weight="BOLD")
        ffn = boxed("FFN\n更深的非线性变换", 2.35, 2.0, MUTED, 30, weight="BOLD")
        block = VGroup(attn, ffn).arrange(DOWN, buff=0.32)
        exp = boxed("专家集合\nMoE 替换 FFN", 2.7, 2.55, GREEN, 32, weight="BOLD")
        flow = VGroup(token, block, exp).arrange(RIGHT, buff=0.56)
        flow_arrow1 = Arrow(token.get_right(), block.get_left(), color=MUTED, buff=0.12, stroke_width=4)
        flow_arrow2 = Arrow(block.get_right(), exp.get_left(), color=GREEN, buff=0.12, stroke_width=4)
        flow_all = Group(token, flow_arrow1, block, flow_arrow2, exp)
        note1 = boxed("MoE 把 FFN 替换成专家集合", 6.4, 1.45, WHITE, 34, weight="BOLD")
        page1 = _page(title1, flow_all, note1, buff=0.68)
        self.play_parallel(type_in(head, 0.72), run_time=0.72)
        self.play_parallel(type_in(title1, 0.65), FadeIn(flow_all), run_time=0.65)
        self.at(2.171256)  # subtitle[24]
        self.play_scroll_unroll_many(note1, run_time=0.70)

        title2 = t("更准确的说法", 39, WHITE, "BOLD")
        bad = boxed("90% 参数没有用", 6.4, 2.15, RED, 43, weight="BOLD")
        good = boxed("这一次前向计算，大多数路由专家没有被调用", 6.4, 1.80, GREEN, 35, weight="BOLD")
        still = boxed("它们仍是模型容量的一部分，只是这次没被选中", 6.4, 1.65, WHITE, 32, weight="BOLD")
        page2 = _page(title2, bad, good, still, buff=0.72)
        self.at(16.451528)  # subtitle[25]
        _clear(self, page1)
        _reveal_page_title(self, title2)
        self.play_scroll_unroll_many(bad, good, still, run_time=0.76)
        self.wait(0.067)
        cross = self.play_red_cross(bad, run_time=0.60)

        title3 = t("代价转移到工程问题", 38, WHITE, "BOLD")
        c1 = boxed("token 要分发到正确的专家", 3.1, 2.15, CYAN, 32, weight="BOLD")
        c2 = boxed("专家输出还要收回来", 3.1, 2.15, GREEN, 32, weight="BOLD")
        comms = VGroup(c1, c2).arrange(RIGHT, buff=0.35)
        tail = boxed("专家越分散，通信越可能成为瓶颈", 6.4, 1.75, YELL, 37, weight="BOLD")
        page3 = _page(title3, comms, tail, buff=1.30)
        self.at(24.899102)  # subtitle[26]
        _clear(self, page2, cross)
        _reveal_page_title(self, title3)
        self.play_scroll_unroll_many(c1, c2, tail, run_time=0.76)
        self.at(33.165406)  # subtitle[26] end
        self.emphasize(tail, mode="circumscribe", color=YELL, run_time=0.55)
        _transition(self, head, footer, page3)
        self.pad_to_voice()


# ---------------- S7 回到价格：三层钥匙 ----------------
class S7(_Base):
    def construct(self):
        self.bg()
        footer = _footer(self)
        head = _header("把 30 倍拆开：三层钥匙")

        l1 = boxed("第一层 · 缓存复用：95% 命中，重复上下文很便宜", 6.6, 2.15, CYAN, 36, weight="BOLD")
        l1b = boxed("提示缓存的作用，不是 MoE 专属", 6.6, 1.45, WHITE, 33, weight="BOLD")
        l2 = boxed("第二层 · 稀疏计算：专家前馈只运行必要专家", 6.6, 2.15, GREEN, 36, weight="BOLD")
        page1 = _page(l1, l1b, l2, buff=1.0)
        # S7 的第一句从上一段静音边界开始，句首在本 wav 之前约 0.21s；
        # 首卡因此在场景起点出现，subtitle[28] 精确锚定第二层。
        self.play_parallel(type_in(head, 0.72), run_time=0.72)
        self.play_scroll_unroll_many(l1, l1b, run_time=0.74)
        self.at(15.983220)  # subtitle[28]
        self.play_scroll_unroll_many(l2, run_time=0.74)

        l3 = boxed("第三层 · 系统工程：把稀疏计算变成低账单", 6.6, 2.15, YELL, 36, weight="BOLD")
        chips = VGroup(*[
            boxed(label, 1.18, 1.45, MUTED, 25, weight="BOLD")
            for label in ("数值精度", "通信", "并行策略", "批处理", "服务调度")
        ]).arrange(RIGHT, buff=0.12)
        tail = boxed("任何一环效率不足，省下的算力都会被等网络、等显存、等队列吃掉", 6.6, 1.85, YELL, 34, weight="BOLD")
        page2 = _page(l3, chips, tail, buff=1.0)
        self.at(19.164354)  # subtitle[29]
        _clear(self, page1)
        self.play_scroll_unroll_many(l3, *chips, run_time=0.74)
        self.at(29.794604)  # subtitle[30]
        self.play_scroll_unroll_many(tail, run_time=0.74)
        self.at(35.425443)  # subtitle[31] 即将开始，收束转场
        _transition(self, head, footer, page2)
        self.pad_to_voice()


# ---------------- S8 总结 + 尾卡 ----------------
class S8(_Base):
    def construct(self):
        self.bg()
        footer = _footer(self)
        head = _header("更完整的公式")

        equation = boxed("低成本 API =", 6.4, 1.45, WHITE, 40, weight="BOLD")
        terms = [
            boxed("缓存复用", 1.50, 2.25, CYAN, 29, weight="BOLD"),
            boxed("稀疏计算", 1.50, 2.25, GREEN, 29, weight="BOLD"),
            boxed("低精度计算", 1.50, 2.25, YELL, 29, weight="BOLD"),
            boxed("高效通信与服务", 1.50, 2.25, MUTED, 27, weight="BOLD"),
        ]
        term_group = VGroup(*terms).arrange(RIGHT, buff=0.12)
        note1 = boxed("四把钥匙缺一不可", 6.4, 1.45, YELL, 35, weight="BOLD")
        page1 = _page(equation, term_group, note1, buff=0.92)
        self.play_parallel(type_in(head, 0.72), type_in(equation, 0.72), run_time=0.72)
        self.play_scroll_unroll_many(*terms, note1, run_time=0.78)

        title2 = t("一句话总结", 39, WHITE, "BOLD")
        row1 = boxed("¥0.203\n每 1M 总 token", 2.05, 3.05, YELL, 34, weight="BOLD")
        row2 = boxed("1 / 30\n约 GPT-5.6 Sol", 2.05, 3.05, GREEN, 34, weight="BOLD")
        row3 = boxed("1 / 56.7\n约 Claude Fable 5", 2.05, 3.05, CYAN, 34, weight="BOLD")
        summary_rows = VGroup(row1, row2, row3).arrange(RIGHT, buff=0.28)
        note2 = boxed("按笔者真实写代码的 token 结构", 6.4, 1.45, WHITE, 32, weight="BOLD")
        page2 = _page(title2, summary_rows, note2, buff=1.00)
        self.at(14.592925)  # subtitle[32]
        _clear(self, page1)
        _reveal_page_title(self, title2)
        self.play_scroll_unroll_many(row1, row2, row3, note2, run_time=0.78)

        title3 = t("下一篇预告", 39, WHITE, "BOLD")
        mla = boxed("MLA：多头潜在注意力\n减少 KV 缓存的显存压力", 6.4, 2.65, YELL, 37, weight="BOLD")
        note3 = boxed("当上下文越来越长", 6.4, 1.45, MUTED, 34, weight="BOLD")
        page3 = _page(title3, mla, note3, buff=1.25)
        self.at(28.385578)  # subtitle[33]
        _clear(self, page2)
        _reveal_page_title(self, title3)
        self.play_scroll_unroll_many(mla, note3, run_time=0.76)

        title4 = t("评论区聊聊", 39, WHITE, "BOLD")
        question = boxed("你更愿意为更强的模型付高价，\n还是用足够强、但能反复调用的模型做日常开发？", 6.4, 2.75, GREEN, 35, weight="BOLD")
        page4 = _page(title4, question, buff=1.35)
        self.at(37.425261)  # subtitle[34]
        _clear(self, page3)
        _reveal_page_title(self, title4)
        self.play_scroll_unroll_many(question, run_time=0.80)

        logo = ImageMobject(str(pathlib.Path(__file__).resolve().parent / "avatar-sjai-round.png"))
        logo.scale_to_fit_width(3.45)
        follow = VGroup(
            t("关注「数解AI」", 44, YELL, "BOLD"),
            t("《DeepSeek便宜30倍的秘密：MoE混合专家入门》", 25, WHITE, "BOLD"),
            t("查看公众号文章 · 图文全解", 25, GREEN),
            t("下一篇：MLA 多头潜在注意力", 23, MUTED),
        ).arrange(DOWN, buff=0.38)
        brand_page = _page(logo, follow, buff=0.68)
        self.at(46.097914)  # subtitle[35]
        _clear(self, page4)
        self.play_parallel(FadeIn(logo, scale=0.9), type_in(follow, run_time=0.82), run_time=0.82)
        _transition(self, head, footer, brand_page)
        self.pad_to_voice()
