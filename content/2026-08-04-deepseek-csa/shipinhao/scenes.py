#!/usr/bin/env python3
"""《DeepSeek-V4 为什么不用 MLA？》视频号场景（MiniMax 精英男声版 2026-08-26）。

- 6 个场景 S1-S6，与 storyboard.md 一一对应（2026-08-25 拍板 6 段收紧）
- 配音：MiniMax 精英男声 male-qn-jingying（2026-08-26 用户拍板默认）
- 时间轴锚点 = tts/sentence-boundaries.json 的 clip id（at_clip 精确挂接，字幕块粒度）
- 动画降噪：每页 1 个主视觉动效，其余静态 type_in/scroll_unroll 入场
- 概念图：img/s1-longctx-round.png、s2-compress-round.png、s4-hca-round.png（AI 图禁数字）
- 数字全部脚本画图（grow_bar / counter_value）
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

# ffprobe tts/s1.wav ... tts/s6.wav（2026-08-26：精英男声 male-qn-jingying，speed 1.0 pitch +2）
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


def _page(*mobjects, buff: float = 0.75):
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


def _fit(mob, max_w: float = 7.7):
    if mob.width > max_w:
        mob.set_width(max_w)
    return mob


def _reveal(scene, mob, run_time: float = 0.6, **kw):
    scene.play(type_in(mob, run_time), run_time=run_time, **kw)


def _reveal_title(scene, title, run_time: float = 0.6):
    scene.play(type_in(title, run_time), run_time=run_time)


def _label(text: str, size: float = 32, color: str = WHITE, weight: str = "BOLD"):
    return _fit(t(text, size, color, weight))


def _block(lines, size: float = 34, color: str = WHITE, weight: str = "BOLD",
           sub_size: float = 27, sub_color: str = MUTED):
    main = _fit(t(lines[0], size, color, weight))
    if len(lines) == 1:
        return main
    sub = _fit(t(lines[1], sub_size, sub_color))
    block = VGroup(main, sub).arrange(DOWN, buff=0.16)
    return block


def _leaves(mobject):
    children = getattr(mobject, "submobjects", ())
    if not children:
        return [mobject]
    leaves = []
    for child in children:
        leaves.extend(_leaves(child))
    return leaves


def _roots_for(scene, *targets):
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


def _dissolve(scene, *targets, run_time: float = 1.05):
    """溶解式换页：元素像素化成同色小方块 → 方块随机方向飞散淡出。"""
    roots = _roots_for(scene, *targets)
    if not roots:
        return
    rng = np.random.default_rng(20260826)
    shards: list[VGroup] = []
    whole: list = []
    for root in roots:
        w, h = root.width, root.height
        if w < 0.08 or h < 0.08:
            whole.append(root)
            shards.append(None)
            continue
        color = root.get_color()
        ncols = max(2, min(22, int(w / 0.22)))
        nrows = max(2, min(8, int(h / 0.22) + 1))
        cell_w, cell_h = w / ncols, h / nrows
        left, bottom = root.get_left()[0], root.get_bottom()[1]
        grid = VGroup()
        for i in range(ncols):
            for j in range(nrows):
                cell = Rectangle(width=cell_w * 1.08, height=cell_h * 1.08,
                                 fill_color=color, fill_opacity=0.95,
                                 stroke_width=0)
                cell.move_to(np.array([left + cell_w * (i + 0.5),
                                       bottom + cell_h * (j + 0.5), 0]))
                grid.add(cell)
        shards.append(grid)
    appear = [root.animate.set_opacity(0) for root in roots]
    appear += [g.animate.set_opacity(1.0) for g in shards if g is not None]
    if appear:
        scene.play(*appear, run_time=0.25 * run_time, rate_func=smooth)
    fly = []
    for grid in shards:
        if grid is None:
            continue
        for cell in grid:
            vx = rng.uniform(-1.1, 1.1)
            vy = rng.uniform(-1.0, 0.6) - 0.15
            fly.append(cell.animate.shift(np.array([vx, vy, 0])).set_opacity(0))
    for root in whole:
        fly.append(root.animate.shift(DOWN * 0.6).set_opacity(0))
    if fly:
        scene.play(*fly, run_time=0.75 * run_time, rate_func=smooth)
    scene.remove(*roots, *[g for g in shards if g is not None])


def _tail_dissolve(scene, *targets, run_time: float = 1.05):
    """在段末（TAIL 缓冲）溶解，避免 dissolve 落在最后一句台词的中间造成空屏。
    计算 dissolve 起点 = 配音时长 - dissolve 时长，使它在配音结束后、进入 TAIL 时才溶解。"""
    scene_name = scene.__class__.__name__
    seg_dur = VOICE_DUR.get(scene_name, 0.0)
    # dissolve 起点 ≈ seg_dur（配音结束）；让 dissolve 在 TAIL 中完成
    target = max(0.0, seg_dur)
    if scene.time < target - 0.05:
        scene.wait(target - scene.time)
    _dissolve(scene, *targets, run_time=run_time)


# ---------------- S1 开场钩子：存不下 -> 找不动 ----------------
class S1(_Base):
    def construct(self):
        self.bg()
        footer = _footer(self)
        head = _header("百万上下文：存不下，还是找不动？")

        # 页 1：存不下 vs 找不动 双卡对比
        save = _block(("「存不下」", "每个位置存储太贵"), 50, CYAN, "BOLD", 34)
        find = _block(("「找不动」", "位置数量太多"), 50, YELL, "BOLD", 34)
        line = _fit(t("MLA 解决了前者，后者才要命", 46, WHITE, "BOLD"))
        page1 = _page(save, find, line, buff=2.6)
        note0 = t("以 DeepSeek-V4 为例", 24, MUTED).next_to(head, DOWN, buff=0.5)

        self.at_clip("s1-c01")
        _reveal_title(self, head, 0.7)
        self.play(FadeIn(note0, shift=DOWN * 0.05), run_time=0.4)
        self.at_clip("s1-c02")
        _reveal(self, save, 0.62)
        self.at_clip("s1-c03")
        _reveal(self, find, 0.62)
        self.at_clip("s1-c05")
        _reveal(self, line, 0.62)

        # 页 2：概念图（长上下文难找重点）
        img = _image("s1-longctx-round.png", 5.4)
        cap = _label("百万 token 历史，重点被淹没了", 40, WHITE, "BOLD")
        page2 = _page(img, cap, buff=1.1)
        self.at_clip("s1-c06")
        _clear(self, page1)
        self.play(FadeIn(img, shift=DOWN * 0.05), run_time=0.8)
        self.at_clip("s1-c07")
        self.play(type_in(cap, 0.6), run_time=0.6)
        self.wait(0.6)
        # 问题收尾（无新 clip，静默揭示后 dissolve）
        v4 = _label("V4：CSA + HCA 混合注意力", 56, YELL, "BOLD")
        q = _label("MLA 已经很省，为什么非要换？", 48, WHITE, "BOLD")
        page3 = _page(v4, q, buff=5.9)
        _clear(self, page2)
        _reveal(self, v4, 0.6)
        _reveal(self, q, 0.7)
        _tail_dissolve(self, head, footer, page3, note0)
        self.pad_to_voice()


# ---------------- S2 注意力成本 + DSA ----------------
class S2(_Base):
    def construct(self):
        self.bg()
        footer = _footer(self)
        head = _header("注意力：读得越多，越卡")

        # 页 1：Q-K 相关性 + L² 平方增长（主视觉）
        t1 = _label("Q 和 K 比相关性，再加权 V", 50, WHITE, "BOLD")
        l2 = _label("历史长度 L：查询键配对 ≈ L²", 52, YELL, "BOLD")
        note = _label("长上下文，就是被这个平方项卡住", 42, MUTED)
        page1 = _page(t1, l2, note, buff=3.0)
        self.at_clip("s2-c01")
        _reveal_title(self, head, 0.7)
        self.at_clip("s2-c03")
        _reveal(self, t1, 0.7)
        self.at_clip("s2-c04")
        _reveal(self, l2, 0.7)
        self.at_clip("s2-c07")
        _reveal(self, note, 0.6)

        # 页 2：DSA 索引器打分 + TopK（主视觉：TopK 选中）
        idx = _label("DSA：轻量索引器打分", 46, CYAN, "BOLD")
        topk = _label("只保留最高的 k 个位置", 52, GREEN, "BOLD")
        core = _label("核心注意力只读这 k 个位置", 46, WHITE, "BOLD")
        page2 = _page(idx, topk, core, buff=3.0)
        self.at_clip("s2-c08")
        _clear(self, page1)
        _reveal(self, idx, 0.6)
        self.at_clip("s2-c09")
        _reveal(self, topk, 0.7)
        self.at_clip("s2-c11")
        _reveal(self, core, 0.6)

        # 页 3：索引器仍面对长序列（痛点）
        prob = _label("可索引器面对的，仍是整段原始历史", 48, WHITE, "BOLD")
        met = _label("目录，还得从整本书逐页扫出来", 52, YELL, "BOLD")
        q = _label("这瓶颈，堵住了吗？", 56, RED, "BOLD")
        page3 = _page(prob, met, q, buff=3.0)
        self.at_clip("s2-c12")
        _clear(self, page2)
        _reveal(self, prob, 0.6)
        self.at_clip("s2-c13")
        _reveal(self, met, 0.7)
        self.at_clip("s2-c15")
        _reveal(self, q, 0.7)
        _tail_dissolve(self, head, footer, page3)
        self.pad_to_voice()


# ---------------- S3 CSA：先压成目录，再选章节 ----------------
class S3(_Base):
    def construct(self):
        self.bg()
        footer = _footer(self)
        head = _header("CSA：先把整本书压成目录")

        # 页 1：概念图（书压成目录/压缩）
        img = _image("s2-compress-round.png", 5.4)
        cap = _label("整本书，压成紧凑目录", 40, WHITE, "BOLD")
        page1 = _page(img, cap, buff=1.1)
        self.at_clip("s3-c01")
        _reveal_title(self, head, 0.7)
        self.at_clip("s3-c02")
        self.play(FadeIn(img, shift=DOWN * 0.05), run_time=0.8)
        self.at_clip("s3-c03")
        _reveal(self, cap, 0.6)

        # 页 2：m 个 token 一块 + 双流重叠（主视觉）
        block = _label("每个压缩块覆盖 m 个 token", 50, WHITE, "BOLD")
        streams = _label("双流重叠：相邻摘要共享范围", 48, CYAN, "BOLD")
        note = _label("避免块边界切断依赖", 42, MUTED)
        page2 = _page(block, streams, note, buff=3.0)
        self.at_clip("s3-c04")
        _clear(self, page1)
        _reveal(self, block, 0.6)
        self.at_clip("s3-c05")
        _reveal(self, streams, 0.6)
        self.at_clip("s3-c06")
        _reveal(self, note, 0.6)

        # 页 3：压缩条目数量 L → L/m（counter 主视觉）
        lab = _block(("压缩条目数量", "从 L 降到 L/m"), 52, WHITE, "BOLD", 40)
        slot = dynamic_slot(5.0, 2.2)
        page3 = _page(lab, slot, buff=3.4)
        self.at_clip("s3-c08")
        _clear(self, page2)
        self.play_parallel(type_in(lab, 0.6), run_time=0.6)
        cnt = self.counter_value(0, 260, suffix=" 条", size=72, color=YELL,
                                 run_time=1.2, anchor=slot)

        # 页 4：索引器面对压缩条目 + TopK
        idx = _label("索引器面对：更短的压缩条目", 46, WHITE, "BOLD")
        topk = _label("候选池变小，扫描成本跟着缩小", 50, YELL, "BOLD")
        core = _label("核心注意力只读选中条目", 46, GREEN, "BOLD")
        page4 = _page(idx, topk, core, buff=3.0)
        self.at_clip("s3-c09")
        _clear(self, page3, cnt)
        _reveal(self, idx, 0.6)
        self.at_clip("s3-c12")
        _reveal(self, topk, 0.7)
        self.at_clip("s3-c13")
        _reveal(self, core, 0.6)
        _tail_dissolve(self, head, footer, page4)
        self.pad_to_voice()


# ---------------- S4 HCA：更狠，不挑 ----------------
class S4(_Base):
    def construct(self):
        self.bg()
        footer = _footer(self)
        head = _header("HCA：压得更狠，不挑章节")

        # 页 1：概念图（精读 vs 概览）
        img = _image("s4-hca-round.png", 5.2)
        cap = _label("CSA 精读重点，HCA 快速概览", 44, WHITE, "BOLD")
        csa_chip = _card("CSA 挑章节", 2.6, 1.5, CYAN, WHITE, 28)
        hca_chip = _card("HCA 短摘要", 2.6, 1.5, GREEN, WHITE, 28)
        chips = Group(csa_chip, hca_chip).arrange(RIGHT, buff=0.5)
        group = Group(img, cap, chips).arrange(DOWN, buff=0.8)
        page1 = _page(group, buff=1.0)
        self.at_clip("s4-c01")
        _reveal_title(self, head, 0.7)
        self.at_clip("s4-c02")
        self.play(FadeIn(img, shift=DOWN * 0.05), run_time=0.8)
        self.at_clip("s4-c04")
        self.play_parallel(type_in(cap, 0.6), type_in(csa_chip, 0.5),
                           type_in(hca_chip, 0.5), run_time=0.7)

        # 页 2：CSA(挑 TopK) vs HCA(不挑) 双卡（同一 clip 内并行动画）
        csa = _card("CSA：压缩后还要挑 TopK", 6.2, 2.2, CYAN, WHITE, 32)
        hca = _card("HCA：压得更狠，不做稀疏选择", 6.2, 2.2, YELL, WHITE, 32)
        page2 = _page(csa, hca, buff=3.4)
        _clear(self, page1)
        self.play_scroll_unroll_many(csa, hca, run_time=1.0)

        # 页 3：m' 汇总成摘要 → 稠密注意力（主视觉）
        sum_ = _label("每 m′ 个 token 直接汇成一个摘要", 46, WHITE, "BOLD")
        dense = _label("序列足够短，直接做稠密注意力", 46, YELL, "BOLD")
        page3 = _page(sum_, dense, buff=6.2)
        self.at_clip("s4-c05")
        _clear(self, page2)
        _reveal(self, sum_, 0.7)
        self.at_clip("s4-c06")
        _reveal(self, dense, 0.7)

        # 页 4：精读 vs 覆盖 双卡 + 混合注意力
        read = _label("CSA：挑几章精读", 42, CYAN, "BOLD")
        cover = _label("HCA：极短摘要保全局", 42, GREEN, "BOLD")
        hybrid = _label("两种交替堆叠 = 混合注意力", 50, YELL, "BOLD")
        q = _label("到底省了多少？", 54, WHITE, "BOLD")
        page4 = _page(read, cover, hybrid, q, buff=2.5)
        self.at_clip("s4-c07")
        _clear(self, page3)
        self.play_parallel(type_in(read, 0.6), type_in(cover, 0.6), run_time=0.6)
        self.at_clip("s4-c10")
        _reveal(self, hybrid, 0.6)
        self.at_clip("s4-c12")
        _reveal(self, q, 0.7)
        _tail_dissolve(self, head, footer, page4)
        self.pad_to_voice()


# ---------------- S5 论文数字 ----------------
class S5(_Base):
    def construct(self):
        self.bg()
        footer = _footer(self)
        head = _header("1M 上下文：到底省了多少？")

        # 页 1：V4-Pro 27% / 10%（counter 主视觉）
        t1 = _label("V4-Pro 相对 V3.2（1M 上下文）", 40, WHITE, "BOLD")
        lab1 = _label("推理 FLOPs", 42, CYAN, "BOLD")
        slot1 = dynamic_slot(2.6, 0.9)
        lab2 = _label("KV 缓存", 42, GREEN, "BOLD")
        slot2 = dynamic_slot(2.6, 0.9)
        page1 = _page(t1, lab1, slot1, lab2, slot2, buff=1.4)
        self.at_clip("s5-c01")
        _reveal_title(self, head, 0.7)
        self.at_clip("s5-c02")
        self.play_parallel(type_in(lab1, 0.6), run_time=0.6)
        cnt1 = self.counter_value(0, 27, suffix="%", size=64, color=YELL,
                                  run_time=1.2, anchor=slot1)
        self.at_clip("s5-c04")
        _reveal(self, lab2, 0.6)
        cnt2 = self.counter_value(0, 10, suffix="%", size=64, color=YELL,
                                  run_time=1.0, anchor=slot2)

        # 页 2：V4-Flash 10% / 7%（counter 主视觉）
        t2 = _label("V4-Flash 更激进", 40, WHITE, "BOLD")
        lab3 = _label("推理 FLOPs", 42, CYAN, "BOLD")
        slot3 = dynamic_slot(2.6, 0.9)
        lab4 = _label("KV 缓存", 42, GREEN, "BOLD")
        slot4 = dynamic_slot(2.6, 0.9)
        page2 = _page(t2, lab3, slot3, lab4, slot4, buff=1.4)
        self.at_clip("s5-c05")
        _clear(self, page1, cnt1, cnt2)
        self.play_parallel(type_in(lab3, 0.6), type_in(t2, 0.5), run_time=0.6)
        cnt3 = self.counter_value(0, 10, suffix="%", size=64, color=YELL,
                                  run_time=1.0, anchor=slot3)
        self.at_clip("s5-c07")
        _reveal(self, lab4, 0.6)
        cnt4 = self.counter_value(0, 7, suffix="%", size=64, color=YELL,
                                  run_time=1.0, anchor=slot4)

        # 页 3：模型卡（1.6T/49B/1M + 284B/13B）
        pro = _card("Pro：1.6T 参数 · 49B 激活 · 1M 上下文", 6.4, 1.9, CYAN, WHITE, 30)
        flash = _card("Flash：284B 参数 · 13B 激活 · 1M 上下文", 6.4, 1.9, GREEN, WHITE, 30)
        note = _label("1M 场景的估算比较，非所有任务固定快", 40, MUTED)
        page3 = _page(pro, flash, note, buff=2.2)
        self.at_clip("s5-c08")
        _clear(self, page2, cnt3, cnt4)
        self.play_scroll_unroll(pro, run_time=1.0)
        self.at_clip("s5-c11")
        self.play_scroll_unroll(flash, run_time=1.0)
        self.at_clip("s5-c13")
        _reveal(self, note, 0.6)
        _tail_dissolve(self, head, footer, page3)
        self.pad_to_voice()


# ---------------- S6 总结 + 品牌尾卡 ----------------
class S6(_Base):
    def construct(self):
        self.bg()
        footer = _footer(self)
        head = _header("注意力的下一步：少找一点")

        # 页 1：四机制总结链
        mla = _card("MLA 压缩存储", 4.8, 1.4, CYAN, WHITE, 28)
        dsa = _card("DSA 减少精读", 4.8, 1.4, GREEN, WHITE, 28)
        csa = _card("CSA 缩短候选池", 4.8, 1.4, YELL, WHITE, 28)
        hca = _card("HCA 保留全局", 4.8, 1.4, CYAN, WHITE, 28)
        page1 = _page(mla, dsa, csa, hca, buff=0.9)
        self.at_clip("s6-c01")
        _reveal_title(self, head, 0.7)
        self.at_clip("s6-c03")
        self.play_scroll_unroll(mla, run_time=0.8)
        self.at_clip("s6-c04")
        self.play_scroll_unroll(dsa, run_time=0.8)
        self.at_clip("s6-c05")
        self.play_scroll_unroll(csa, run_time=0.8)
        self.at_clip("s6-c06")
        self.play_scroll_unroll(hca, run_time=0.8)

        # 页 2：核心观点（大卡 + 支撑，撑满页）
        key = _card("不是 MLA 不行了，而是百万上下文要求位置本身也变少", 6.6, 5.6, YELL, WHITE, 52)
        sub = _label("每一步都在解决上一步的瓶颈", 44, MUTED)
        page2 = _page(key, sub, buff=1.2)
        self.at_clip("s6-c07")
        _clear(self, page1)
        self.play_scroll_unroll(key, run_time=1.0)
        self.at_clip("s6-c08")
        _reveal(self, sub, 0.7)

        # 页 3：下一篇预告 + 互动（压缩到 s6-c09..s6-c15）
        next_ = _label("下一篇：K=V、Partial RoPE、de-RoPE", 42, GREEN, "BOLD")
        q = _label("你选完整保留但检索贵，", 38, WHITE, "BOLD")
        q2 = _label("还是先压缩更快、但可能漏细节？", 38, WHITE, "BOLD")
        discuss = _label("评论区聊聊！", 58, YELL, "BOLD")
        page3 = _page(next_, q, q2, discuss, buff=1.9)
        self.at_clip("s6-c09")
        _clear(self, page2)
        self.play_parallel(type_in(next_, 0.6), type_in(q, 0.6),
                           type_in(q2, 0.6), type_in(discuss, 0.6), run_time=0.7)
        self.wait(0.2)

        # 尾卡（并行 reveal，在 s6-c13/c14 进入，远早于 36.15s 配音末尾）
        avatar = ImageMobject(str(ROOT / "avatar-sjai-round.png"))
        avatar.scale_to_fit_width(3.6)
        follow = _label("关注「数解AI」", 46, YELL, "BOLD")
        t_title = _fit(t("《DeepSeek-V4 为什么不用 MLA？》", 28, WHITE, "BOLD"), 7.4)
        guide = _label("下一篇：K=V / Partial RoPE / de-RoPE", 34, GREEN, "BOLD")
        page4 = _page(avatar, follow, t_title, guide, buff=1.3)
        self.at_clip("s6-c14")
        _clear(self, page3, head, footer)
        self.play(FadeIn(avatar, scale=1.5), run_time=0.8)
        self.play_parallel(type_in(follow, 0.6), type_in(t_title, 0.6),
                           type_in(guide, 0.6), run_time=0.8)
        self.wait(1.4)
        self.pad_to_voice()
