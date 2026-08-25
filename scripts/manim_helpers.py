#!/usr/bin/env python3
"""Manim 视频号通用工具模块 — 所有文章 shipinhao/scenes.py 共享（勿复制进文章目录）

用法（scenes.py 开头）：
  import sys, pathlib
  sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "scripts"))
  from manim_helpers import *
  config.background_color = "#0F1A30"   # 可选：覆盖默认背景
  VOICE_DUR = {"S1": 28.288, ...}        # 每篇自己的配音时长（_Base.setup 自动从本模块读取）
  TAIL = 2.5                             # 渲染缓冲（build 截到 0.1s）

硬性约定（用户拍板，勿改回）：
  - 所有裸文字入场用 type_in()（逐字打字），禁止一次性 FadeIn 整段文字
  - 方框/卡片入场用 play_scroll_unroll()（席子式从左向右摊开，框字同步）
  - FadeIn 仅用于：公式、天平、圆形节点、徽章组、✔✗ 标记、logo
  - FadeOut 必须带走本页全部元素（含箭头/Axes/装饰），换页时新旧元素无交叉
  - 循环弧线用 arc_curve()（贝塞尔，不穿圆、箭头尖贴圆周）
  - 动效库 v2（2026-08-18）：镜头推拉必须成对（推近后拉回，场景末帧相机全画布）；breathe 幅度 ≤3%；trace_dot 的 dot 换页必须 FadeOut 带走
"""
from __future__ import annotations

import inspect
import math
import os
import re
import sys
import numpy as np
from manim import *

# ---- 竖屏 9:16 画布（与 build 脚本 PlayRes 绑定，勿改）----
config.pixel_width = 1080
config.pixel_height = 1920
config.frame_width = 8.0
config.frame_height = 14.2222
config.background_color = "#16213E"      # 每篇可覆盖

FONT = "Noto Sans CJK SC"
YELL = "#FFD54A"
CYAN = "#5FC4E8"
GREEN = "#7ED7A0"
RED = "#FF7B72"
MUTED = "#9AA7BD"
WHITE = "#F2F5FA"

# 柔和卡片色（与深蓝背景协调）
CARD_FILL = "#2C3F60"      # 卡片默认实心填充（中性石板蓝，避开黄/青/绿/红高亮色）
CARD_FILL2 = "#223450"     # 次卡片实心填充
CARD_BORDER = "#5C769D"    # 卡片默认边框
TXT_HL = "#8FB4E6"         # 正文柔和亮字

# 卡片文字设计 token：所有 card 统一使用，场景不得为单个卡片手调缩放。
CARD_TEXT_MAX_FS = 48
CARD_TEXT_MIN_FS = 18
CARD_TEXT_MAX_LINES = 4
CARD_TEXT_LINE_SPACING = 0.42

FH = config.frame_height
FW = config.frame_width

# ---- 竖屏整页规划（2026-08-16 用户拍板：先算整页 box，再算元素起点）----
# 每页先组装「该页全部元素的最终稳定状态」，得到整体 box；再放入标题下方→字幕安全区上方的显示带，
# 上下留白严格相等，且各边留白 ≤ 显示带 10%（内容高度 ≥ 显示带 80%）。
# 闪烁/强调类装饰（红叉/circumscribe/indicate/breathe/数字滚动）不参与整页 box，按稳定后几何计算。
PAGE_TOP = FH * 0.32           # 显示带上边界（标题下方）
PAGE_BOTTOM = -FH * 0.292      # 显示带下边界（距底 ≈400px，字幕上方）
PAGE_BAND = PAGE_TOP - PAGE_BOTTOM
MAX_PAGE_MARGIN = 0.10         # 上下留白各 ≤ 显示带 10%（2026-08-19 用户拍板：留白各自小于 10% 即可，原 30%）
MIN_PAGE_FILL = 1 - 2 * MAX_PAGE_MARGIN  # 内容高度 ≥ 显示带 80%


def layout_page(block: Group):
    """整页规划器：先量稳定后的整页 box，再垂直居中放入显示带。
    - 上下留白完全相等；
    - 内容高度不足显示带 80% 直接 ValueError，逼着先把短页元素放大/加页内间距；
    - 超过显示带才等比缩小（正常情况下应通过减内容/拆页避免）。
    页面元素位置全部由整页 box 派生，禁止「第一条放中间、其余向下平铺」的接龙式排布。
    """
    block.move_to(ORIGIN)
    block.set_x(0.0)
    min_h = PAGE_BAND * MIN_PAGE_FILL
    if block.height < min_h:
        raise ValueError(
            f"页面内容高度 {block.height:.2f} < 显示带 80%({min_h:.2f})，"\
            "请先放大元素或增加页内间距再 layout_page"
        )
    if block.height > PAGE_BAND:
        block.scale_to_fit_height(PAGE_BAND)
    if block.width > FW:
        block.scale_to_fit_width(FW)
    block.set_y((PAGE_TOP + PAGE_BOTTOM) / 2.0)
    return block


def page_stack(*mobs, buff: float = 0.55):
    """纵向堆叠并水平居中：整页规划的标准组装方式。
    Group 兼容 ImageMobject（VGroup 不接受），先 arrange 定页内相对位置，再交给 layout_page。
    """
    grp = Group(*mobs).arrange(DOWN, buff=buff)
    grp.set_x(0.0)
    return grp


# ---- 矮页自动排版（2026-08-26 用户拍板：1-3 行文字页禁止大 buff 撑高）----
# 解决「两句/三句各挂上下两端、中间巨大留空」：长句按语义标点（逗号/分号/顿号/箭头→）
# 自动拆多行占空间 + 字号放大 + 紧凑行距 + 整组垂直居中（上下留白均分）。
# 多元素/图表/数字页继续用 page_stack+layout_page 全屏模式，两者按页选择。
PAGE_AUTO_FILL = 0.70           # 矮页目标内容高度（显示带 70%，上下留白各 15% → 不再有中间空洞）
PAGE_AUTO_MAX_SCALE = 1.5      # 元素最大放大倍率（字号视觉上限）
PAGE_AUTO_BUFF = 0.42          # 矮页行距（紧凑，不靠行距撑高）
PAGE_AUTO_LINE_W = 0.58        # 行宽上限（画布比例，超过则拆行）


def layout_center(block: Group):
    """矮页版整页规划：行组垂直居中、上下留白严格相等，不强制 80% 高度门禁。
    用于 1-4 行文字页（page_auto）；信息密集页仍用 layout_page。
    """
    block.move_to(ORIGIN)
    block.set_x(0.0)
    if block.height > PAGE_BAND:
        block.scale_to_fit_height(PAGE_BAND)
    if block.width > FW:
        block.scale_to_fit_width(FW)
    block.set_y((PAGE_TOP + PAGE_BOTTOM) / 2.0)
    return block


def _wrap_text_mob(mob: Mobject, max_w: float) -> Mobject:
    """超宽 Text 按语义标点拆成多行（\n 重建，同字号/颜色/字重）。
    断行符（用户拍板 2026-07-26）：逗号、分号、顿号、冒号、箭头 →（含「→」两侧）。
    每行 ≤ max_w；无标点的长行按字数硬拆；短行不拆。非 Text 原样返回。
    """
    if not isinstance(mob, Text) or mob.width <= max_w:
        return mob
    text = getattr(mob, "original_text", mob.text)  # .text 会丢空格，用 original_text
    fs = float(mob.font_size)
    # 文字色存在 glyph submobject 上（顶层 .color 是 stroke 黑色）
    color = mob.submobjects[0].get_color() if mob.submobjects else WHITE
    weight = getattr(mob, "weight", "NORMAL")
    per_char = fs * 0.0109  # 中文全角字近似宽度（u/px 系数，实测 44px≈0.48u）
    limit = max(4, int(max_w / per_char))
    # 断行符（用户拍板 2026-08-26）：逗号、分号、箭头 →（箭头后断）；顿号/冒号/句号不拆。
    # 「」引号对整体原子化：在「前断开，保证引号内容不拆断。
    parts = re.split(r"(?<=[，；])|(?=「)", text)
    pieces: list[str] = []
    for part in parts:
        if "→" in part:
            seg = re.split(r"(?<=→)", part)  # 箭头挂行尾，不独立成行
            for s in seg:
                pieces.extend(_hard_split(s, limit))
        else:
            pieces.extend(_hard_split(part, limit))
    # 相邻的极短块（≤2 字）并回上一行，避免碎片化
    lines: list[str] = []
    for p in pieces:
        p = p.strip()
        if not p:
            continue
        if lines and len(p) <= 2 and len(lines[-1]) + len(p) <= limit:
            lines[-1] += p
        else:
            lines.append(p)
    if len(lines) <= 1:
        return mob
    new = t("\n".join(lines), fs, color, weight, line_spacing=0.6)
    mob.become(new)  # 就地替换：调用方持有的原引用变成多行文本（位置/颜色/字形同步）
    return mob


def _hard_split(text: str, limit: int) -> list[str]:
    """超限段按目标行数**均衡**拆行（复用 _balanced_lines 行均分算法）：
    先算目标行数 n = 权重/上限，再均分行宽 —— 避免贪心填满首行造成的 2-3 字悬尾行。
    断行不拆断英文 token 与「」引号对（_balanced_lines 已原子化）。"""
    if len(text) <= limit:
        return [text]
    weight = sum(1 if ch.isascii() else 2 for ch in text)
    n = max(2, math.ceil(weight / (limit * 2)))
    lines = [ln for ln in _balanced_lines(text, n) if ln]
    return lines or [text]


def page_auto(*mobs, buff: float = PAGE_AUTO_BUFF, fill: float = PAGE_AUTO_FILL,
              max_scale: float = PAGE_AUTO_MAX_SCALE, max_line_w: float = PAGE_AUTO_LINE_W):
    """矮页自动排版（1-4 行文字/元素页首选，替代 _page 传大 buff 撑高）：
    1. 超宽行按逗号/分号/箭头等语义标点拆成多行（占满空间）；
    2. 整组高度不足显示带 fill 比例 → 元素等比放大（字号视觉变大）；
    3. 行距保持紧凑（buff），垂直居中，上下留白均分 —— 无中间空洞。
    返回排好位置的 Group（元素仍按惯例逐个 type_in/scroll_unroll 入场）。
    """
    items = [_wrap_text_mob(m, FW * max_line_w) for m in mobs]
    grp = Group(*items).arrange(DOWN, buff=buff)
    target = PAGE_BAND * fill
    scale = min(max_scale, target / grp.height) if grp.height < target else 1.0
    wmax = max((m.width for m in items), default=0.0)
    if wmax * scale > FW * 0.9:
        scale = min(scale, FW * 0.9 / wmax)
    if scale > 1.01:
        for m in items:
            m.scale(scale)
        grp = Group(*items).arrange(DOWN, buff=buff)
    layout_center(grp)
    return grp



def t(text: str, size: float = 34, color: str = WHITE, weight: str = "NORMAL",
      line_spacing: float = -1) -> Text:
    return Text(text, font=FONT, font_size=size, color=color, weight=weight,
                line_spacing=line_spacing)


def _balanced_lines(label: str, line_count: int) -> list[str]:
    """Split a label into roughly balanced lines without assuming Latin spaces.

    Manim's ``Text.set_width`` can only make an overlong label smaller.  For a
    tall card that is the wrong trade-off: wrapping gives the label a readable
    font size and uses the vertical space that the card deliberately reserves.
    """
    if line_count <= 1 or len(label) <= 1:
        return [label]
    # Keep Latin/number tokens whole, but allow CJK runs to use the available
    # vertical space character by character.  This avoids both "DeepSeek"
    # being split and a mixed label such as "256 个路由专家" being forced into
    # one tiny line merely because it contains a space.
    tokens = re.findall(r"「[^」]*」|[A-Za-z0-9.%+/_-]+|[\u3400-\u9fff]|[^\s]", label)
    if not tokens:
        return [label]

    def token_weight(token: str) -> int:
        # 「」引号对按内容字符数计权重（视觉宽度），不按整串 2 计
        if len(token) > 1 and (token.startswith("「") or token.endswith("」")):
            return sum(1 if c.isascii() else 2 for c in token)
        return len(token) if token.isascii() else 2

    def join_tokens(items: list[str]) -> str:
        result = ""
        for token in items:
            needs_space = (
                bool(result)
                and " " in label
                and (result[-1].isascii() or token[0].isascii())
                and token not in ",.!?;:%，。！？；：、"
            )
            result += (" " if needs_space else "") + token
        return result

    lines: list[str] = []
    cursor = 0
    for line_index in range(line_count):
        remaining_lines = line_count - line_index
        remaining = tokens[cursor:]
        if not remaining:
            break
        if remaining_lines == 1:
            lines.append(join_tokens(remaining))
            break
        target = max(1, int(np.ceil(sum(map(token_weight, remaining)) / remaining_lines)))
        current = [remaining[0]]
        current_weight = token_weight(remaining[0])
        cursor += 1
        while cursor < len(tokens):
            next_weight = token_weight(tokens[cursor])
            tokens_left = len(tokens) - cursor
            if current_weight + next_weight > target and tokens_left >= remaining_lines - 1:
                break
            current.append(tokens[cursor])
            current_weight += next_weight
            cursor += 1
        lines.append(join_tokens(current))
    closing_punctuation = "，。！？；：、,.!?;:%)]}》」』"
    for index in range(1, len(lines)):
        while lines[index] and lines[index][0] in closing_punctuation:
            lines[index - 1] += lines[index][0]
            lines[index] = lines[index][1:].lstrip()
    return [line for line in lines if line]


def fit_text_in_box(label: str, width: float, height: float, fs: float = 28,
                    color: str = WHITE, weight: str = "NORMAL",
                    width_ratio: float = 0.76, height_ratio: float = 0.72,
                    min_fs: float = CARD_TEXT_MIN_FS,
                    max_fs: float = CARD_TEXT_MAX_FS,
                    max_lines: int | None = None,
                    line_spacing: float = CARD_TEXT_LINE_SPACING) -> Text:
    """Create readable text that fits a fixed card, wrapping before shrinking.

    Candidates with one to ``max_lines`` lines are measured against the card's
    actual layout box and the largest readable font is selected, capped by the
    shared ``CARD_TEXT_MAX_FS`` token.  Multiline candidates use the shared
    ``CARD_TEXT_LINE_SPACING`` token and their complete rendered height is
    measured, so growing a card vertically can grow its label without manual
    scene-specific font constants.  The returned object is not positioned;
    callers align it to their card after construction.
    """
    max_w = max(0.1, width * width_ratio)
    max_h = max(0.1, height * height_ratio)
    min_fs = min(float(min_fs), float(fs))
    if max_lines is None:
        max_lines = min(CARD_TEXT_MAX_LINES, max(1, len(label)))
    max_fs = max(min_fs, max_fs)

    best: tuple[float, int, Text] | None = None
    for line_count in range(1, max_lines + 1):
        lines = _balanced_lines(label, line_count)
        for size in np.linspace(max_fs, min_fs, 31):
            candidate = t("\n".join(lines), float(size), color, weight,
                          line_spacing=line_spacing if len(lines) > 1 else -1)
            if candidate.width <= max_w + 1e-6 and candidate.height <= max_h + 1e-6:
                # Font size is primary, with a small fragmentation penalty so
                # a two-line 46pt label wins over a three-line 48pt label.
                score = float(size) - 1.5 * (len(lines) - 1)
                key = (score, -len(lines), candidate)
                if best is None or key[:2] > best[:2]:
                    best = key
                break
    if best is not None:
        return best[2]

    # Extremely long labels still get a deterministic result.  The final
    # width clamp is a last resort, not the normal fitting path.
    fallback = t(label, min_fs, color, weight)
    if fallback.width > max_w:
        fallback.set_width(max_w)
    if fallback.height > max_h:
        fallback.set_height(max_h)
    return fallback


def _card(label: str, w: float, h: float, border: str, txt_fill: str,
          fs: float = 28, fill: str = CARD_FILL, weight: str = "NORMAL") -> VGroup:
    """统一风格卡片：实心填充 + 轻微圆角 + 左对齐自适应文字。
    文字优先换行并利用高卡的可用高度，最终宽度 ≤ 框宽 76%，水平居左、垂直居中。
    圆角半径 0.18，默认填充 CARD_FILL（中性石板蓝，不与黄/青/绿/红高亮色混淆）。"""
    box = RoundedRectangle(corner_radius=0.18, width=w, height=h,
                           color=border, stroke_width=2.5,
                           fill_color=fill, fill_opacity=1.0)
    txt = fit_text_in_box(label, w, h, fs, txt_fill, weight)
    grp = VGroup(box, txt)
    txt.align_to(box, LEFT)
    txt.move_to(box.get_center())
    txt.shift(LEFT * w * 0.10)  # 文字略靠左，不居中
    return grp


def boxed(label: str, w: float, h: float, color: str, fs: float = 28,
          fill: float = 0.12, wc=None, weight: str = "NORMAL") -> VGroup:
    """兼容旧调用：返回统一风格卡片（color 作为边框与文字色）。"""
    return _card(label, w, h, color, wc or color, fs, CARD_FILL, weight)


def boxrow(labels, w, h, colors, fs=28, fill=CARD_FILL, left=True, gap=0.55, weight="NORMAL"):
    """同一屏多个竖直排列的卡片：统一宽度 w、统一高度 h，左对齐堆叠。
    labels: list[str], colors: list[边框色]。返回 VGroup(逐卡)。"""
    cards = [_card(lb, w, h, c, c, fs, fill, weight) for lb, c in zip(labels, colors)]
    grp = VGroup(*cards)
    grp.arrange(DOWN, buff=gap, aligned_edge=LEFT if left else ORIGIN)
    return grp


def dynamic_slot(width: float, height: float = 0.6) -> Rectangle:
    """Reserve geometry for a value that will be animated later.

    Put this transparent slot in the final row/group before calling a dynamic
    helper such as ``counter_value``.  The animated value can then be anchored
    to the slot and cannot push a neighbour, drift off-canvas, or appear on a
    different baseline when its width changes from one to two digits.
    """
    return Rectangle(width=width, height=height, stroke_opacity=0, fill_opacity=0)


def stable_row(*mobs, buff: float = 0.3, aligned_edge=ORIGIN) -> VGroup:
    """Arrange static and dynamic slots on one shared baseline."""
    return VGroup(*mobs).arrange(RIGHT, buff=buff, aligned_edge=aligned_edge)


def fit(mob, frac: float = 0.85):
    """宽内容守卫：不超过画布宽的 frac（只缩小不放大）。"""
    if mob.width > config.frame_width * frac:
        return mob.set_width(config.frame_width * frac)
    return mob


def sup(base_str: str, sup_str: str, size: float = 30, sup_size: float = 17,
        color: str = WHITE, weight: str = "BOLD") -> VGroup:
    base = t(base_str, size, color, weight)
    s = t(sup_str, sup_size, color, weight)
    s.next_to(base, UP, buff=0.0, aligned_edge=RIGHT)
    return VGroup(base, s)


def sub(base_str: str, sub_str: str, size: float = 30, sub_size: float = 17,
        color: str = WHITE, weight: str = "BOLD") -> VGroup:
    base = t(base_str, size, color, weight)
    s = t(sub_str, sub_size, color, weight)
    s.next_to(base, DOWN, buff=0.02, aligned_edge=RIGHT)
    return VGroup(base, s)


def sigma_term(yw: str, yl: str, size: float = 26, color: str = WHITE) -> VGroup:
    """偏好建模 σ(r(y_w) − r(y_l)) 组装公式（纯 Text + 上下标锚点）。"""
    r1 = sub("r", "φ(x,y" + yw + ")")
    minus = t(" − ", size, color)
    r2 = sub("r", "φ(x,y" + yl + ")")
    inner = VGroup(r1, minus, r2).arrange(RIGHT, buff=0.1)
    sigma = t("σ(", size, color)
    close = t(")", size, color)
    return VGroup(sigma, inner, close).arrange(RIGHT, buff=0.1)


def gaussian_curve(center: float = 0.0, spread: float = 1.0, amp: float = 1.0,
                   color: str = CYAN, n: int = 120) -> VMobject:
    """高斯分布曲线（KL 双分布示意等）。自动裁剪 x 范围，尾部不触边、不截断。"""
    half = max(3.2 * spread, 1.5)
    xs = np.linspace(center - half, center + half, n)
    ys = amp * np.exp(-0.5 * ((xs - center) / spread) ** 2)
    pts = np.stack([xs, ys, np.zeros_like(xs)], axis=1)
    curve = VMobject(color=color, stroke_width=5)
    curve.set_points_smoothly(pts)
    return curve


def type_in(mob, run_time: float = 0.6):
    """快速打字机入场（逐字出现，中文友好）。
    拍板节奏：标题 1.1s、正文 0.8-1.0s、标签 0.5s（勿过快，用户否过「字一次全出」也否过「太快」）。"""
    return AddTextLetterByLetter(mob, run_time=run_time)


def cnode(lab: str, col: str, radius: float = 0.95, fs: float = 24) -> VGroup:
    """圆形流程节点：彩色描边 + 半透明填充 + 限宽文字。"""
    c = Circle(radius=radius, color=col, stroke_width=3,
               fill_color=col, fill_opacity=0.22)
    txt = t(lab, fs, WHITE, "BOLD")
    if txt.width > radius * 1.58:
        txt.set_width(radius * 1.58)
    return VGroup(c, txt)


def edge_pt(center, vec, rr=1.02):
    """从节点中心出发、沿 vec 方向、到半径 rr 处的边缘点（弧线起终点锚点）。"""
    v = np.array(vec, dtype=float)
    if v.ndim == 1 and v.shape[0] == 2:
        v = np.append(v, 0.0)
    return center + rr * v / np.linalg.norm(v)


def arc_curve(c_s, ang_s, c_e, ang_e, c1_extra, c2_extra, color=MUTED,
              node_r: float = 0.95):
    """贝塞尔弧线箭头（闭环流程，2026-08-17 拍板）：
    - 起点在圆 s 外缘（ang_s 处）、终点在圆 e 外缘（ang_e 处）
    - 控制点沿外法向+切向延伸 → 曲线全程不穿圆（CurvedArrow 会穿圆，勿用）
    - 箭头从终点指向终点圆心，尖端恰好落在圆周上（不插进圆）
    验证：渲染后像素级检查弧线色像素到各圆心距离 ≥ 圆半径（文字抗锯齿除外）。
    """
    rr = node_r * 1.15  # 端点距圆心（圆外 15% 半径）
    p_start = c_s + rr * np.array([np.cos(ang_s), np.sin(ang_s), 0.0])
    p_end = c_e + rr * np.array([np.cos(ang_e), np.sin(ang_e), 0.0])
    n_s = (p_start - c_s) / np.linalg.norm(p_start - c_s)
    c2_dir = (p_end - c_e) / np.linalg.norm(p_end - c_e)  # 终点处背离圆心方向
    c1 = n_s * 0.5 + np.array([c1_extra[0], c1_extra[1], 0.0])
    c2 = c2_dir * 0.5 + np.array([c2_extra[0], c2_extra[1], 0.0])
    curve = CubicBezier(p_start, p_start + c1, p_end + c2, p_end,
                        color=color, stroke_width=5)
    # 箭头：从终点指向终点圆心，尖端恰好落在圆周上（不插进圆）
    d_in = (c_e - p_end) / np.linalg.norm(c_e - p_end)
    apex = p_end + d_in * (rr - node_r)
    perp = np.array([-d_in[1], d_in[0], 0.0])
    tip = Polygon(apex, p_end + perp * 0.07, p_end - perp * 0.07,
                  color=color, fill_color=color, fill_opacity=1.0, stroke_width=0)
    return VGroup(curve, tip)


class _Base(MovingCameraScene):
    """场景基类：配音时间轴锚点 + 统一入场动画工具。

    继承 MovingCameraScene（而非 Scene）以支持动效库 v2 的镜头推拉
    （camera_zoom_to 需要 self.camera.frame，2026-08-18 实测 Scene 无 frame）。

    setup 从场景类所在模块读取 VOICE_DUR/TAIL（每个 scenes.py 定义自己的），
    因此 VOICE_DUR 改在 scenes.py 里即可，勿动本文件。
    """

    def setup(self):
        mod = sys.modules[self.__class__.__module__]
        dur = getattr(mod, "VOICE_DUR", {})
        self.scene_dur = dur.get(self.__class__.__name__, 10.0) + getattr(mod, "TAIL", 2.5)
        self.strict_timeline = os.getenv("MANIM_STRICT_TIMELINE", "").lower() in {
            "1", "true", "yes", "on"
        }
        self._timeline_contract = None

    def at(self, t: float):
        """推进到配音时间轴绝对时刻（动画动作挂到台词节点上）。"""
        if t < self.time - 1e-6:
            message = (
                f"时间轴回退：{self.__class__.__name__}.at({t:.3f}) "
                f"< 当前动画时间 {self.time:.3f}；请把动作移到字幕边界之后"
            )
            if self.strict_timeline:
                raise RuntimeError(message)
            return
        if t > self.time:
            self.wait(t - self.time)

    def at_strict(self, target: float, tolerance: float = 0.02):
        """严格推进到绝对时间；回退或明显错过目标时立即报错。"""
        if target < self.time - tolerance:
            raise RuntimeError(
                f"{self.__class__.__name__}.at_strict({target:.3f}) 回退到 "
                f"{self.time:.3f}，动画顺序与字幕不一致"
            )
        self.at(target)

    def at_clip(self, clip_id: str, offset: float = 0.0):
        """按 sentence-boundaries 的 clip id 对齐，而不是手写魔法数字。

        Contract is loaded lazily so ordinary Manim renders remain independent
        of the checker.  Missing metadata is a hard error: silently falling
        back to a guessed timestamp recreates the original sync bug.
        """
        if self._timeline_contract is None:
            try:
                from manim_timeline import TimelineContract
            except ImportError as exc:  # pragma: no cover - only in production
                raise RuntimeError("无法加载 scripts/manim_timeline.py") from exc
            source_file = inspect.getfile(self.__class__)
            self._timeline_contract = TimelineContract.for_scene(source_file)
        target = self._timeline_contract.start_of(clip_id) + offset
        self.at_strict(target)

    def play_parallel(self, *animations, run_time: float | None = None, **kwargs):
        """Play sibling animations in one clock interval.

        This small wrapper makes the intended relationship explicit in scene
        code and gives the static preflight a reliable marker for parallel
        reveals.  Every animation must already be positioned in its final slot.
        """
        if run_time is not None:
            kwargs["run_time"] = run_time
        return self.play(*animations, **kwargs)

    def pad_to_voice(self):
        """末尾兜底补齐，使场景总时长 = 配音时长 + TAIL。每个 construct 末尾必调。"""
        elapsed = self.time
        target = self.scene_dur
        if target > elapsed:
            self.wait(target - elapsed)

    def footer(self, text: str = "数解AI · 大模型原理"):
        f = t(text, 20, MUTED).to_edge(DOWN, buff=1.15)
        self.add(f)

    def bg(self):
        """柔和的纵向渐变背景（顶部更暗、底部更暖），铺满画布垫底。"""
        rect = Rectangle(width=FW + 0.1, height=FH + 0.1,
                         fill_opacity=1.0, stroke_width=0)
        rect.set_fill([color_to_rgb("#0C1424"), color_to_rgb("#1B2B4E"),
                       color_to_rgb("#223358")], opacity=1)
        self.add(rect)

    def play_red_cross(self, target, run_time: float = 0.65):
        """否定/纠错视觉（用户拍板）：两条粗红线 GrowFromCenter 交叉 + 弹跳。
        被否元素文字本身用 WHITE（红叉已表达否定，文字别用红）。"""
        c1 = Line(target.get_corner(UL) + RIGHT * 0.15 + DOWN * 0.15,
                  target.get_corner(DR) + LEFT * 0.15 + UP * 0.15,
                  color=RED, stroke_width=14)
        c2 = Line(target.get_corner(UR) + LEFT * 0.15 + DOWN * 0.15,
                  target.get_corner(DL) + RIGHT * 0.15 + UP * 0.15,
                  color=RED, stroke_width=14)
        cross = VGroup(c1, c2)
        self.play(GrowFromCenter(c1), GrowFromCenter(c2), run_time=0.4)
        self.play(cross.animate.scale(1.1), run_time=0.1)
        self.play(cross.animate.scale(1 / 1.1), run_time=0.1)
        return cross

    def play_mark(self, label: str, target, color: str = GREEN,
                  mark_size: float = 40, run_time: float = 0.5) -> Text:
        """在 target 旁打一个 ✔/✗ 标记：快速放大再缩小（闪烁）后留在原位。
        label 为符号本身（如 '✔' / '✗'）。marker 落点在 target 右侧。"""
        mk = t(label, mark_size, color, "BOLD")
        mk.next_to(target, RIGHT, buff=0.25)
        mk.align_to(target, UP)
        self.play(FadeIn(mk, scale=1.6), run_time=run_time * 0.5)
        self.play(mk.animate.scale(0.62), run_time=run_time * 0.5)
        return mk

    def build_balance(self, left_lab: str, left_sub: str, right_lab: str, right_sub: str,
                      center: np.ndarray = ORIGIN, beam=5.0, pan_y=-1.0):
        """一杆天平：三角支点 + 横梁 + 两侧吊杆 + 盘面 + 砝码块（标签在块内）。
        返回 (rig, pans, pivot)：
          rig   = VGroup(支点, 横梁, 吊杆×2) —— 倾斜时旋转这一部分
          pans  = VGroup(左盘组, 右盘组)      —— 盘 + 砝码，保持水平
          pivot = 旋转中心（横梁中点 = 支点顶点）
        吊杆从横梁两端垂直连到盘面中心（无悬空），砝码块坐落在盘面上。"""
        px, py = center[0], center[1]
        half = beam / 2
        fulcrum = Polygon(
            np.array([px - 0.5, py - 0.7, 0]), np.array([px + 0.5, py - 0.7, 0]),
            np.array([px, py, 0]),
            color=MUTED, stroke_width=3, fill_color=MUTED, fill_opacity=0.25)
        beamline = Line(np.array([px - half, py, 0]), np.array([px + half, py, 0]),
                        color=MUTED, stroke_width=4)
        rod_tip_y = py + pan_y
        l_rod = Line(np.array([px - half, py, 0]), np.array([px - half, rod_tip_y, 0]),
                     color=MUTED, stroke_width=3)
        r_rod = Line(np.array([px + half, py, 0]), np.array([px + half, rod_tip_y, 0]),
                     color=MUTED, stroke_width=3)
        pan_w = 1.55

        def pan(x: float, lab: str, sublab: str, col: str) -> VGroup:
            dish = Line(np.array([x - pan_w / 2, rod_tip_y - 0.06, 0]),
                        np.array([x + pan_w / 2, rod_tip_y - 0.06, 0]),
                        color=MUTED, stroke_width=5)
            block = Rectangle(width=1.1, height=0.78, color=col, stroke_width=2.5,
                              fill_color=col, fill_opacity=0.28)
            block.move_to(np.array([x, rod_tip_y - 0.06 - 0.05 - 0.39, 0]))
            lb = t(lab, 20, WHITE, "BOLD")
            sb = t(sublab, 15, WHITE)
            if lb.width > 0.9:
                lb.set_width(0.9)
            if sb.width > 0.9:
                sb.set_width(0.9)
            vg = VGroup(lb, sb).arrange(DOWN, buff=0.05).move_to(block.get_center())
            return VGroup(dish, block, vg)

        left_pan = pan(px - half, left_lab, left_sub, RED)
        right_pan = pan(px + half, right_lab, right_sub, GREEN)
        rig = VGroup(fulcrum, beamline, l_rod, r_rod)
        return rig, VGroup(left_pan, right_pan), np.array([px, py, 0])

    def tilt_balance(self, rig, pans, pivot, angle: float, run_time: float = 1.0):
        """天平倾斜动画：rig（支点+横梁+吊杆）绕 pivot 旋转，盘组沿弧线跟随且保持水平。
        angle 负值 = 顺时针，右端下沉（右盘更重）。"""
        tracker = ValueTracker(0.0)
        tips = [rig[2].get_end(), rig[3].get_end()]
        offsets = [pan_m.get_center() - tip for pan_m, tip in zip(pans, tips)]
        for pan_m, tip, off in zip(pans, tips, offsets):
            def make_upd(m, tip_, off_):
                def upd(mm):
                    a = tracker.get_value()
                    dx, dy = tip_[0] - pivot[0], tip_[1] - pivot[1]
                    c, s = np.cos(a), np.sin(a)
                    mm.move_to(np.array([pivot[0] + dx * c - dy * s,
                                         pivot[1] + dx * s + dy * c, 0]) + off_)
                return upd
            pan_m.add_updater(make_upd(pan_m, tip, off))
        self.play(rig.animate.rotate(angle, about_point=pivot),
                  tracker.animate.set_value(angle), run_time=run_time)
        pans[0].clear_updaters()
        pans[1].clear_updaters()

    def play_scroll_unroll(self, grp, run_time: float = 1.5):
        """席子式展开（用户拍板 2026-08-14）：框和文字同步从左向右缓慢摊开，
        文字随展开比例逐字露出（非框先出字后淡入）。
        grp = boxed()/_card() 的 VGroup(框, 字)。节奏勿过快（×1.5 起）。"""
        box, txt = grp[0], grp[1]
        left_x = box.get_left()[0]
        y = box.get_center()[1]
        h = box.height
        full_w = box.width
        color = box.get_stroke_color()
        fill_c = box.get_fill_color()
        fill_o = box.get_fill_opacity()
        sw = box.get_stroke_width()

        radius = float(getattr(box, "corner_radius", 0.18))
        tracker = ValueTracker(0.08)
        growing = RoundedRectangle(
            corner_radius=radius, width=0.08, height=h, color=color,
            fill_color=fill_c, fill_opacity=fill_o, stroke_width=sw,
        )
        growing.move_to(np.array([left_x + 0.04, y, 0]))

        def upd(mob):
            w = max(tracker.get_value(), 0.08)
            new = RoundedRectangle(
                corner_radius=radius, width=w, height=h, color=color,
                fill_color=fill_c, fill_opacity=fill_o, stroke_width=sw,
            )
            new.move_to(np.array([left_x + w / 2.0, y, 0]))
            mob.become(new)

        growing.add_updater(upd)
        n = len(txt)

        def txt_upd(m):
            frac = min(tracker.get_value() / full_w, 1.0)
            visible = int(n * frac)
            for i, ch in enumerate(txt):
                ch.set_opacity(1.0 if i < visible else 0.0)

        for ch in txt:
            ch.set_opacity(0.0)
        txt.add_updater(txt_upd)
        self.add(growing, txt)
        self.play(tracker.animate.set_value(full_w),
                  run_time=run_time, rate_func=smooth)
        growing.clear_updaters()
        txt.clear_updaters()
        for ch in txt:
            ch.set_opacity(1.0)
        self.remove(growing)
        self.add(grp)

    def play_scroll_unroll_many(self, *groups, run_time: float = 1.5):
        """Unroll sibling cards in parallel on one shared clock interval.

        Use this for vertical lists, comparison columns, or any group whose
        items have the same semantic start time.  It prevents the common
        failure where cards appear one by one while their shared subtitle has
        already moved on.
        """
        if not groups:
            raise ValueError("play_scroll_unroll_many 至少需要一个卡片组")
        trackers = []
        growing_boxes = []
        text_objects = []
        full_widths = []
        for grp in groups:
            box, txt = grp[0], grp[1]
            left_x = box.get_left()[0]
            y = box.get_center()[1]
            h = box.height
            full_w = box.width
            tracker = ValueTracker(0.08)
            radius = float(getattr(box, "corner_radius", 0.18))
            growing = RoundedRectangle(
                corner_radius=radius, width=0.08, height=h,
                color=box.get_stroke_color(), fill_color=box.get_fill_color(),
                fill_opacity=box.get_fill_opacity(), stroke_width=box.get_stroke_width(),
            )
            growing.move_to(np.array([left_x + 0.04, y, 0]))

            def box_updater(mob, tr=tracker, lx=left_x, yy=y, hh=h,
                            rr=radius, source=box):
                width = max(tr.get_value(), 0.08)
                replacement = RoundedRectangle(
                    corner_radius=rr, width=width, height=hh,
                    color=source.get_stroke_color(),
                    fill_color=source.get_fill_color(),
                    fill_opacity=source.get_fill_opacity(),
                    stroke_width=source.get_stroke_width(),
                )
                replacement.move_to(np.array([lx + width / 2.0, yy, 0]))
                mob.become(replacement)

            growing.add_updater(box_updater)
            character_count = len(txt)

            def text_updater(mob, tr=tracker, fw=full_w, count=character_count):
                visible = int(count * min(tr.get_value() / fw, 1.0))
                for index, char in enumerate(mob):
                    char.set_opacity(1.0 if index < visible else 0.0)

            for char in txt:
                char.set_opacity(0.0)
            txt.add_updater(text_updater)
            self.add(growing, txt)
            trackers.append(tracker)
            growing_boxes.append(growing)
            text_objects.append(txt)
            full_widths.append(full_w)

        self.play(
            *[tracker.animate.set_value(width) for tracker, width in zip(trackers, full_widths)],
            run_time=run_time,
            rate_func=smooth,
        )
        for grp, growing, txt in zip(groups, growing_boxes, text_objects):
            growing.clear_updaters()
            txt.clear_updaters()
            for char in txt:
                char.set_opacity(1.0)
            self.remove(growing)
            self.add(grp)
        return VGroup(*groups)

    def grow_bar(self, rect, tracker, target, run_time=0.7, extra_anims=None, anchor="left", **kw):
        """用 ValueTracker 驱动矩形条从底部生长到 target 宽/高。
        ⚠️ 锚点必须用左下角（get_corner(DL)）并只捕获一次——get_left() 返回左缘中心
        （垂直中点），每帧 become 后参考点抬高半条高 → 条累积上移（2026-08-16 S3 事故）。
        anchor="center" 时以初始水平中心为锚向两侧生长（2026-08-25 修 S1/S2 KV 条左缘
        锚定导致条偏右 215px 的 QA 问题）。
        extra_anims：可选动画列表，与条生长并行播放（如柱子标签 type_in），
        避免「先条后标签」的顺序漂移（2026-08-19 打磨）。
        内部自动 self.add(rect)——调用方不再需要先 add（2026-08-19 修复遗漏 add 导致柱子不显示）。"""
        left_bottom = rect.get_corner(DL)
        center_x = rect.get_center()[0]
        self.add(rect)

        def upd(m):
            w = tracker.get_value()
            new = Rectangle(width=w, height=rect.height,
                            color=rect.get_stroke_color(),
                            fill_color=rect.get_fill_color(),
                            fill_opacity=rect.get_fill_opacity())
            if anchor == "center":
                new.move_to(np.array([center_x, left_bottom[1] + rect.height / 2, 0]))
            else:
                new.move_to(left_bottom + RIGHT * w / 2, aligned_edge=DOWN)
            m.become(new)
        rect.add_updater(upd)
        anims = [tracker.animate.set_value(target)]
        if extra_anims:
            anims.extend(extra_anims)
        self.play(*anims, run_time=run_time, **kw)
        rect.clear_updaters()
        return rect

    def counter_value(self, start: float, end: float, suffix: str = "", decimals: int = 0,
                      size: int = 64, color: str = YELL, run_time: float = 0.9,
                      anchor=None, extra_anims=None) -> DecimalNumber:
        """数字滚动动画（数据动效，2026-08-15 新增）：从 start 滚到 end。
        返回已停在 end 的 VGroup(数字, 后缀)（无后缀时返回 DecimalNumber 本身），
        调用方自行 next_to/arrange 定位。suffix（如 "%" / " 步" / "×"）拼在数字右侧。
        extra_anims 可传同一行静态标签的入场动画，使标签和数字同拍出现，
        避免动态值先出、静态说明后补（或反过来）。
        用法：
          n = self.counter_value(0, 32, suffix=" 组",
                                 extra_anims=[type_in(label, 0.6)])
          n.next_to(card, DOWN, buff=0.5)
        数字类台词（步数/分数/百分比/倍率）优先用本工具，禁止纯文字陈述数字。
        """
        tracker = ValueTracker(start)
        # v0.21 起 DecimalNumber 默认 mob_class=MathTex（需 latex，系统无），显式指定 Text
        num = DecimalNumber(start, mob_class=Text, num_decimal_places=decimals,
                            font_size=size, color=color)
        if suffix:
            tail = t(suffix, int(size * 0.42), color, "BOLD")
            tail.next_to(num, RIGHT, buff=0.12)
            tail.align_to(num, DOWN)
            grp = VGroup(num, tail)
        else:
            grp = num
        # Dynamic numbers must be positioned before they are added/animated.
        # Without an anchor they briefly appear at ORIGIN, which is especially
        # destructive on portrait pages where ORIGIN is often another card.
        if anchor is not None:
            target = anchor.get_center() if hasattr(anchor, "get_center") else np.array(anchor)
            grp.move_to(target)
        if suffix:
            # 在同一个 updater 内先更新数字、再读取它的新宽度定位后缀。
            # 分别给 num/tail 加 updater 会受子图形更新顺序影响，数字从
            # 一位滚到两位时会出现一帧「15.6%」的百分号压住 6。
            def update_number_and_suffix(m):
                m.set_value(tracker.get_value())
                tail.next_to(m, RIGHT, buff=0.12)
                tail.align_to(m, DOWN)

            num.add_updater(update_number_and_suffix)
        else:
            num.add_updater(lambda m: m.set_value(tracker.get_value()))
        self.add(grp)
        animations = [tracker.animate.set_value(end)]
        if extra_anims:
            animations.extend(extra_anims)
        self.play(*animations, run_time=run_time, rate_func=smooth)
        num.clear_updaters()
        if suffix:
            tail.clear_updaters()
            tail.next_to(num, RIGHT, buff=0.12)
            tail.align_to(num, DOWN)
        return grp

    def transition_out(self, *mobs: Mobject, run_time: float = 0.6):
        """场景末尾统一转场（2026-08-15 新增）：全部元素向右下滑出并淡出，
        替代硬切，给下一场景干净的入画起点。在 pad_to_voice() 前调用，
        占用 TAIL 缓冲（2.5s）中约 0.6s，剩余仍由 pad_to_voice 补齐。
        必须传当前场景全部可见元素（含 head / footer），漏传即残影（A3 对账）。
        """
        if not mobs:
            raise ValueError("transition_out 必须传入当前场景全部可见元素（含 head/footer）")
        grp = VGroup(*mobs)
        self.play(grp.animate.shift(RIGHT * 0.9 + DOWN * 0.5).set_opacity(0),
                  run_time=run_time, rate_func=smooth)
        self.remove(grp)

    # ---- 动效库 v2（2026-08-18 新增）：镜头语言 + 形变 + 连续运动 + 强调 + 呼吸 ----

    def camera_zoom_to(self, target=None, scale: float = 0.6, run_time: float = 1.0):
        """镜头推拉（3B1B 式镜头语言）：target 给 mobject → 推近到 scale 倍并中心对准；
        target=None → 拉回全画布。念重点推近、讲完拉回，画面立刻有呼吸感。
        ⚠️ 硬性规则：必须成对使用（推近后拉回），场景末帧相机必须全画布（QA A18）；
        推近后内容仍须在安全区内（A5/A10 对缩放后帧同样适用）。
        用法：
          self.camera_zoom_to(formula)          # 念公式时推近
          self.camera_zoom_to()                  # 讲完拉回全画布
        """
        frame = self.camera.frame
        if target is None:
            self.play(frame.animate.set(width=FW, height=FH).move_to(ORIGIN),
                      run_time=run_time, rate_func=smooth)
        else:
            self.play(frame.animate.scale(scale).move_to(target.get_center()),
                      run_time=run_time, rate_func=smooth)

    def morph_to(self, source, target, run_time: float = 1.0, replace: bool = True):
        """形变动画（3B1B 招牌）：source 平滑变形为 target，比「消失+出现」高级一个量级。
        replace=True  → ReplacementTransform（source 被替换，一次性转换：卡片→曲线、公式→图形）
        replace=False → Transform（source 保留，A→B 对照：旧状态→新状态）
        返回 target。形变时长计入 at() 排布。
        """
        anim = ReplacementTransform if replace else Transform
        self.play(anim(source, target), run_time=run_time)
        return target

    def trace_dot(self, path, color: str = YELL, radius: float = 0.09,
                  run_time: float = 2.0, trail: bool = True):
        """轨迹追踪点：小圆点沿 path 连续滑行（ValueTracker + always_redraw）。
        连续运动是「画面活着」的关键——比离散出现高级一个量级。
        path 支持 ParametricFunction（point_from_function）或任意 VMobject（point_from_proportion）。
        trail=True 时留黄色拖尾（TracedPath）。
        返回 dot（换页必须 FadeOut 带走，QA A19）。
        用法：
          curve = gaussian_curve(0, 1, 1)   # 或 ParametricFunction
          self.play(Create(curve), run_time=0.8)
          dot = self.trace_dot(curve, run_time=2.0)   # 点沿曲线滑行留尾
        """
        tracker = ValueTracker(0.0)
        if hasattr(path, "point_from_function"):
            dot = always_redraw(lambda: Dot(
                path.point_from_function(tracker.get_value()), color=color, radius=radius))
        else:
            dot = always_redraw(lambda: Dot(
                path.point_from_proportion(tracker.get_value()), color=color, radius=radius))
        self.add(dot)
        trail_mob = None
        if trail:
            trail_mob = TracedPath(dot.get_center, stroke_color=color, stroke_width=6)
            self.add(trail_mob)
        self.play(tracker.animate.set_value(1.0), run_time=run_time, rate_func=smooth)
        # 返回 dot（含拖尾）供调用方换页 FadeOut 带走（QA A19：拖尾不随换页移除会残留全片）
        if trail_mob is not None:
            return VGroup(dot, trail_mob)
        return dot

    def emphasize(self, target, mode: str = "indicate", color: str = YELL,
                  run_time: float = 0.8):
        """关键词强调（3B1B 式）：mode 三选一
          indicate     — 抖动放大再缩回（最常用，不遮挡）
          circumscribe — 画圈圈住目标（强调「就是这个」）
          wiggle       — 左右摇摆（否定/质疑语气）
        与 play_red_cross 的区别：红叉是否定，emphasize 是肯定/聚焦。
        时长计入 at() 排布；circumscribe 的圈是装饰，换页 FadeOut 带走。
        """
        if mode == "circumscribe":
            self.play(Circumscribe(target, color=color, run_time=run_time))
        elif mode == "wiggle":
            # 2026-08-25 修正：Wiggle 默认 scale_value=1.1 会把近边元素放大推超画布
            # （Kimi K3 S1 三轴卡实测 1.1× 裁切 0.27s）；纯旋转不放大，
            # rotation_angle 1.08°（0.003TAU）角点扫掠 ≈10px < 11px 边距余量
            self.play(Wiggle(target, scale_value=1.0, rotation_angle=0.003 * TAU,
                             run_time=run_time))
        else:
            self.play(Indicate(target, color=color, run_time=run_time))
        return target

    def breathe(self, target, scale: float = 1.03, run_time: float = 1.2, loops: int = 2):
        """呼吸微动：静态元素滞留期间轻微缩放起伏，避免画面死板。
        幅度 ≤3%（scale ≤1.03，别抢台词注意力）；仅用于滞留 >2s 的元素。
        注意：breathe 占用台词时间，run_time×loops 需计入 at() 排布。
        """
        for _ in range(loops):
            self.play(target.animate.scale(scale), run_time=run_time / 2)
            self.play(target.animate.scale(1 / scale), run_time=run_time / 2)
        return target


# 显式导出（import * 默认跳过下划线开头名）：自定义工具 + 全部非下划线全局名（含 manim 符号）
__all__ = ["_Base", "_card"] + [n for n in dir() if not n.startswith("_")]
