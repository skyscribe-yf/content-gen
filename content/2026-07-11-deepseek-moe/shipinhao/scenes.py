#!/usr/bin/env python3
"""《DeepSeek便宜30倍的秘密：MoE混合专家入门》视频号场景（口播版 v3 2026-08-20）。

v3 视觉重设计（用户反馈「文本框太多太丑、公式没用 LaTeX」后重写）：
  - 去框化：除红叉目标外所有内容改为裸文字（t()），入场一律 type_in；
    数字槽用细下划线代替小方框；公式全部 MathTex（LaTeX）渲染。
  - 公式：S2 成本公式、S4 三步公式（s_i(x)/Top-k/y=Σw·Expert）、S4 分数
    （\\frac{8}{256}=\\frac{1}{32}）、S8 两个分数（\\frac{1}{30} / \\frac{1}{56.7}）
  - 动效：camera_zoom_to 成对推拉（S2 公式 / S4 分数）、trace_dot（S6）、
    breathe（滞留元素微动）、emphasize（结论圈注）、counter_value（S2 结果行）
  - 时间轴锚点 ``self.at_clip("sN-cXX")`` 来自录音室生成的
    ``tts/sentence-boundaries.json``（2026-08-20 重录后逐句 start/end）。
  - ``VOICE_DUR`` 为 voice_process.py 修音后 ffprobe 实测值（重录版）。
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

# ffprobe tts/s1.wav ... tts/s8.wav（2026-08-20 重录修音后实测）。
VOICE_DUR = {
    "S1": 43.142,
    "S2": 59.903,
    "S3": 39.378,
    "S4": 41.051,
    "S5": 41.624,
    "S6": 30.833,
    "S7": 44.308,
    "S8": 32.594,
}
TAIL = 2.5


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


def _dissolve(scene, *targets, run_time: float = 1.05):
    """溶解式换页（2026-08-20 用户拍板，替换滑动淡出）：
    元素像素化成同色小方块（马赛克化）→ 方块随机方向飞散淡出。
    时长分配 = 0.25×run_time(化像素) + 0.75×run_time(飞散)。
    结束把原元素与碎块全部移出场景（A3 对账）。"""
    roots = _roots_for(scene, *targets)
    if not roots:
        return
    rng = np.random.default_rng(20260820)
    shards: list[VGroup] = []
    whole: list = []
    for root in roots:
        w, h = root.width, root.height
        if w < 0.08 or h < 0.08:
            whole.append(root)  # 太小的元素（箭头等）整体飘落淡出
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
    # 阶段 1：原元素淡出的同时，马赛克块显现并压实
    appear = [root.animate.set_opacity(0) for root in roots]
    appear += [g.animate.set_opacity(1.0) for g in shards if g is not None]
    if appear:
        scene.play(*appear, run_time=0.25 * run_time, rate_func=smooth)
    # 阶段 2：碎块随机方向飞散 + 淡出
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


def _fit(mob, max_w: float = 7.7):
    """超宽文字行等比缩小，避免整页被 layout_page 压到贴边。"""
    if mob.width > max_w:
        mob.set_width(max_w)
    return mob


def _reveal(scene, mob, run_time: float = 0.6, **kw):
    """裸文字统一入场：type_in（逐字打字）。"""
    scene.play(type_in(mob, run_time), run_time=run_time, **kw)


def _reveal_title(scene, title, run_time: float = 0.6):
    scene.play(type_in(title, run_time), run_time=run_time)


def _reveal_formula(scene, formula, run_time: float = 0.65):
    """公式统一入场：FadeIn（公式属 FadeIn 允许类型）。"""
    scene.play(FadeIn(formula), run_time=run_time)


def _block(lines, size: float = 34, color: str = WHITE, weight: str = "BOLD",
           sub_size: float = 27, sub_color: str = MUTED):
    """多行文字块：主行 + 副行（副行颜色更弱）；行宽 >7.7 自动缩放防贴边。"""
    def _w(mob):
        if mob.width > 7.7:
            mob.set_width(7.7)
        return mob
    main = _fit(t(lines[0], size, color, weight))
    if len(lines) == 1:
        return main
    sub = _fit(t(lines[1], sub_size, sub_color))
    block = VGroup(main, sub).arrange(DOWN, buff=0.16)
    return block


def _result_row(name: str, color: str):
    """结果行：模型名 + 下划线数字槽（无方框）。"""
    label = t(name, 32, color, "BOLD")
    if label.width > 4.4:
        label.set_width(4.4)
    slot = Rectangle(width=1.9, height=0.05, color=color, fill_color=color,
                     fill_opacity=0.35, stroke_width=0)
    row = stable_row(label, slot, buff=0.55)
    return row, (label, slot)


def _bg_extension(scene, top: float = 9.2):
    """Zoom 场景专用：画布上方补一块与渐变顶部同色的平色，避免推近时露出底色带。"""
    ext = Rectangle(width=FW + 0.1, height=top - FH / 2, fill_color="#1F2F53",
                    fill_opacity=1.0, stroke_width=0)
    ext.move_to(np.array([0.0, (FH / 2 + top) / 2, 0.0]))
    scene.add(ext)


# ---------------- S1 开场钩子 ----------------
class S1(_Base):
    def construct(self):
        self.bg()
        footer = _footer(self)
        head = _header("DeepSeek 便宜 30 倍，秘密藏在哪？")

        big = t("便宜 30 倍", 64, YELL, "BOLD")
        cap = t("对 GPT-5.6 Sol 的实际价格差", 28, MUTED)
        q = t("秘密到底藏在哪？", 52, WHITE, "BOLD")
        first = _block(("第一轮：很重", "系统提示词 · 仓库目录\n团队规则 · 相关文件"),
                       40, CYAN, "BOLD", 30)
        second = t("第二轮：还是失败，再查一下", 42, GREEN, "BOLD")
        page1 = _page(big, cap, q, first, second, buff=0.90)

        self.at_clip("s1-c01")  # DeepSeek 便宜 30 倍
        _reveal_title(self, head, 0.7)
        self.at_clip("s1-c01", offset=0.8)  # 钩子大字稍后出现
        _reveal(self, big, 0.62)
        self.wait(0.067)
        _reveal(self, cap, 0.5)
        self.at_clip("s1-c02")  # 秘密到底藏在哪
        _reveal(self, q, 0.6)
        self.at_clip("s1-c03")  # 用代码助手修报错
        _reveal(self, first, 0.72)
        self.at_clip("s1-c08")  # 第二轮，你往往只补一句
        _reveal(self, second, 0.62)

        title2 = t("两个问题同时出现", 44, WHITE, "BOLD")
        q1 = _block(("问题 1：重复的仓库上下文", "能不能不再重复收费？"),
                    40, CYAN, "BOLD", 38)
        q2 = _block(("问题 2：每个 token，", "能不能不必让所有参数同时计算？"),
                    40, GREEN, "BOLD", 38)
        page2 = _page(title2, q1, q2, buff=2.1)
        self.at_clip("s1-c10")  # 这时两个问题同时出现
        _clear(self, page1)
        _reveal_title(self, title2)
        self.at_clip("s1-c11")  # 重复的仓库上下文
        _reveal(self, q1, 0.7)
        self.at_clip("s1-c13")  # 每个 token
        _reveal(self, q2, 0.7)

        title3 = t("两个答案", 44, WHITE, "BOLD")
        a1 = _block(("缓存 → 不再重复收费", "提示缓存解决输入侧的重复"), 40, CYAN, "BOLD", 28)
        a2 = _block(("MoE → 不必全参数计算", "混合专家解决计算侧的开销"), 40, GREEN, "BOLD", 28)
        note = _block(("便宜 30 倍不是通用结论：", "输入、缓存命中和输出必须分开算"),
                      38, YELL, "BOLD", 30)
        page3 = _page(title3, a1, a2, note, buff=1.4)
        self.at_clip("s1-c15")  # 前一个问题由缓存回答
        roots = _roots_for(self, page2)
        others = [r for r in roots if r is not q1]
        self.play(FadeOut(*others), FadeOut(q1), run_time=0.28)
        self.remove(*others)
        self.remove(q1)
        _reveal_title(self, title3)
        self.wait(0.067)
        _reveal(self, a1, 0.62)
        self.at_clip("s1-c17")  # 后一个，正是混合专家 MoE
        _reveal(self, a2, 0.62)
        self.at_clip("s1-c19")  # 便宜 30 倍不是通用结论
        _reveal(self, note, 0.7)
        self.emphasize(note, mode="circumscribe", color=YELL, run_time=0.55)
        self.at_clip("s1-c21")  # 缓存命中和输出
        self.wait(0.5)
        _dissolve(self, head, footer, page3)
        self.pad_to_voice()


# ---------------- S2 价格账 ----------------
class S2(_Base):
    def construct(self):
        self.bg()
        _bg_extension(self)  # 推近时相机可见到渐变 rect 上方，补平色
        footer = _footer(self)
        head = _header("先看账：官方价格（每百万 token）")

        note = _fit(t("价格要拆成：普通输入 · 缓存命中 · 输出", 38, YELL, "BOLD"))
        unit = _fit(t("2026 年 7 月核验 · 单位：每百万 token", 28, MUTED))
        price_rows = [
            _block(("DeepSeek-V4 Pro", "输入 ¥3 · 缓存 ¥0.025 · 输出 ¥6"), 38, YELL, "BOLD", 28),
            _block(("GLM-5.2", "输入 ¥8 · 缓存 ¥2 · 输出 ¥28"), 38, CYAN, "BOLD", 28),
            _block(("GPT-5.6 Sol", "输入 ¥33.99 · 缓存 ¥3.40 · 输出 ¥204"), 38, GREEN, "BOLD", 28),
            _block(("Claude Fable 5", "输入 ¥67.99 · 缓存 ¥6.80 · 输出 ¥340"), 38, MUTED, "BOLD", 28),
        ]
        page1 = _page(note, unit, *price_rows, buff=0.75)

        self.play_parallel(type_in(head, 0.7), run_time=0.7)
        self.at_clip("s2-c02", offset=0.3)  # 2026 年 7 月核验的官方价
        _reveal(self, note, 0.6)
        self.at_clip("s2-c03")  # 每百万 token
        _reveal(self, unit, 0.5)
        self.at_clip("s2-c04")  # DeepSeek-V4 Pro
        _reveal(self, price_rows[0], 0.62)
        self.at_clip("s2-c08")  # GLM-5.2
        _reveal(self, price_rows[1], 0.62)
        self.at_clip("s2-c10")  # GPT-5.6 Sol 和 Claude Fable 5
        _reveal(self, price_rows[2], 0.62)
        self.wait(0.067)
        _reveal(self, price_rows[3], 0.62)

        title2 = t("每 1M 总 token 的真实结构", 40, WHITE, "BOLD")
        structure = [
            t("输入 99.5%", 42, CYAN, "BOLD"),
            t("输出 0.5%", 42, YELL, "BOLD"),
            t("缓存命中 95%", 42, GREEN, "BOLD"),
            t("新写 5%", 42, YELL, "BOLD"),
        ]
        structure_note = _fit(t("输入占绝大多数，而输入里大多数又命中缓存", 30, WHITE))
        page2 = _page(title2, *structure, structure_note, buff=0.85)
        self.at_clip("s2-c14")  # 每 1M 总 token
        _clear(self, page1)
        _reveal_title(self, title2)
        self.at_clip("s2-c15")  # 99.5% 是输入
        _reveal(self, structure[0], 0.55)
        self.at_clip("s2-c16")  # 0.5% 是输出
        _reveal(self, structure[1], 0.55)
        self.wait(0.067)
        _reveal(self, structure[2], 0.55)  # 输入里 95% 命中缓存（同句内）
        self.at_clip("s2-c17")  # 只有 5% 是新写的
        _reveal(self, structure[3], 0.55)
        self.wait(0.067)
        _reveal(self, structure_note, 0.6)

        formula_label = t("成本（元 / 每 1M 总 token）", 30, MUTED)
        formula = MathTex(r"0.995\times(0.95\times0.025+0.05\times3)+0.005\times6",
                          font_size=34, color=YELL)
        row_defs = [
            _result_row("DeepSeek-V4 Pro", YELL),
            _result_row("GLM-5.2", CYAN),
            _result_row("GPT-5.6 Sol", GREEN),
            _result_row("Claude Fable 5", MUTED),
        ]
        result_rows = [item[0] for item in row_defs]
        row_parts = [item[1] for item in row_defs]
        page3 = _page(formula_label, formula, *result_rows, buff=1.0)
        self.at_clip("s2-c18")  # 套进公式
        _clear(self, page2)
        self.play_parallel(type_in(formula_label, 0.5), FadeIn(formula), run_time=0.5)
        self.wait(0.067)
        self.camera_zoom_to(formula, scale=0.9, run_time=0.6)  # 念公式推近
        self.at_clip("s2-c19")  # DeepSeek 2 毛钱
        self.camera_zoom_to(run_time=0.7)  # 拉回
        counters = []
        counters.append(self.counter_value(
            0, 0.203, decimals=3, size=44, color=WHITE, run_time=0.55,
            anchor=row_parts[0][1],
            extra_anims=[type_in(row_parts[0][0], 0.45)],
        ))
        self.at_clip("s2-c20")  # GLM 2 块 4
        counters.append(self.counter_value(
            0, 2.429, decimals=3, size=44, color=WHITE, run_time=0.55,
            anchor=row_parts[1][1],
            extra_anims=[type_in(row_parts[1][0], 0.45)],
        ))
        self.wait(0.067)
        counters.append(self.counter_value(  # GPT 5 块 9（同句内）
            0, 5.924, decimals=3, size=44, color=WHITE, run_time=0.55,
            anchor=row_parts[2][1],
            extra_anims=[type_in(row_parts[2][0], 0.45)],
        ))
        self.at_clip("s2-c21")  # Claude 11 块 5
        counters.append(self.counter_value(
            0, 11.509, decimals=3, size=44, color=WHITE, run_time=0.55,
            anchor=row_parts[3][1],
            extra_anims=[type_in(row_parts[3][0], 0.45)],
        ))
        self.at_clip("s2-c22")  # 对 GPT 是 29.2 倍
        self.emphasize(result_rows[2], mode="circumscribe", color=GREEN, run_time=0.55)
        self.at_clip("s2-c25")  # 对最贵的 Claude
        self.emphasize(result_rows[3], mode="circumscribe", color=MUTED, run_time=0.55)
        self.at_clip("s2-c26")  # 价格账只是结果
        self.breathe(formula, loops=2)  # 滞留期微动
        self.at_clip("s2-c30")  # 么不必每次都为所有参数付计算费
        self.wait(1.5)
        _dissolve(self, head, footer, page3, *counters)
        self.pad_to_voice()


# ---------------- S3 直觉：全科会诊 vs 分诊台 ----------------
class S3(_Base):
    def construct(self):
        self.bg()
        footer = _footer(self)
        head = _header("稠密模型 vs 混合专家")

        title1 = t("稠密模型：一次全科会诊", 40, WHITE, "BOLD")
        image1 = _image("s1-consult-round.png", 4.6)
        cap1 = t("一个 token 进入前馈网络，\n相关计算单元全都参与", 32, CYAN)
        page1 = _page(title1, image1, cap1, buff=1.45)
        self.play_parallel(type_in(head, 0.7), type_in(title1, 0.6), run_time=0.7)
        self.at_clip("s3-c02")  # 像一次全科会诊
        self.play(FadeIn(image1, shift=DOWN * 0.05), run_time=0.6)
        self.at_clip("s3-c03")  # 一个 token 进入前馈网络
        _reveal(self, cap1, 0.65)
        self.at_clip("s3-c04")  # 相关计算单元全都参与
        self.breathe(image1, loops=1)  # 滞留图微动

        title2 = t("MoE：先分诊，再找专家", 40, WHITE, "BOLD")
        image2 = _image("s3-triage-round.png", 4.6)
        cap2 = t("先看 token 状态，再决定请哪些专家；\n不是每份知识都同时计算", 32, GREEN)
        page2 = _page(title2, image2, cap2, buff=1.45)
        self.at_clip("s3-c05")  # 混合专家 MoE 像分诊台
        _clear(self, page1)
        _reveal_title(self, title2)
        self.at_clip("s3-c06")  # 先看 token 的状态（再决定请哪些专家同句）
        self.play(FadeIn(image2, shift=DOWN * 0.05), run_time=0.6)
        self.wait(0.067)
        _reveal(self, cap2, 0.65)
        self.at_clip("s3-c09")  # 专家不是人工贴好的标签
        self.breathe(image2, loops=2)  # 滞留图微动

        title3 = t("DeepSeek-V3 的配置", 40, WHITE, "BOLD")
        config_rows = [
            t("256 个路由专家", 42, CYAN, "BOLD"),
            t("每个 token 只选 8 个", 42, GREEN, "BOLD"),
            t("另有 1 个共享专家", 42, YELL, "BOLD"),
        ]
        config_note = _fit(t("总容量可以很大，单次计算却不必跑完所有专家", 30, WHITE))
        conclusion = _fit(t("MoE 不是免费变大，而是只找最相关的人干活", 36, YELL, "BOLD"))
        page3 = _page(title3, *config_rows, config_note, conclusion, buff=0.9)
        self.at_clip("s3-c10")  # DeepSeek-V3：
        _clear(self, page2)
        _reveal_title(self, title3)
        self.at_clip("s3-c11")  # 256 个路由专家
        _reveal(self, config_rows[0], 0.6)
        self.at_clip("s3-c12")  # 每个 token 只选 8 个
        _reveal(self, config_rows[1], 0.6)
        self.at_clip("s3-c13")  # 另有 1 个共享专家
        _reveal(self, config_rows[2], 0.6)
        self.at_clip("s3-c14")  # 总容量可以很大
        _reveal(self, config_note, 0.6)
        self.at_clip("s3-c16")  # 所以 MoE 不是免费变大
        _reveal(self, conclusion, 0.65)
        self.at_clip("s3-c18")  # 只找最相关的人干活
        self.emphasize(conclusion, mode="circumscribe", color=YELL, run_time=0.55)
        self.wait(0.2)
        _dissolve(self, head, footer, page3)
        self.pad_to_voice()


# ---------------- S4 数学：打分→选人→合并 ----------------
class S4(_Base):
    def construct(self):
        self.bg()
        _bg_extension(self)  # 推近时相机可见到渐变 rect 上方，补平色
        footer = _footer(self)
        head = _header("路由器怎么选人？")

        bridge = t("三步：打分 → 选人 → 合并", 40, WHITE, "BOLD")
        step1 = cnode("打分", CYAN, radius=1.0, fs=30)
        step2 = cnode("选人", GREEN, radius=1.0, fs=30)
        step3 = cnode("合并", YELL, radius=1.0, fs=30)
        steps = VGroup(step1, step2, step3).arrange(RIGHT, buff=0.55)
        arrow1 = Arrow(step1.get_right(), step2.get_left(), color=MUTED, buff=0.12, stroke_width=4)
        arrow2 = Arrow(step2.get_right(), step3.get_left(), color=MUTED, buff=0.12, stroke_width=4)
        step_group = Group(step1, arrow1, step2, arrow2, step3)
        subline = _fit(t("设当前 token 的表示是 x，共有 N 个专家", 32, CYAN))
        subline2 = _fit(t("为每个专家打分 → 取 Top-k → 按权重合并", 32, GREEN))
        page1 = _page(bridge, step_group, subline, subline2, buff=1.55)

        self.play_parallel(type_in(head, 0.7), run_time=0.7)
        self.at_clip("s4-c02")  # 三步：打分
        _reveal(self, bridge, 0.6)
        self.at_clip("s4-c03")  # 选人、合并
        self.play(FadeIn(step1), FadeIn(arrow1, step2), FadeIn(arrow2, step3),
                  run_time=1.5, lag_ratio=0.33)  # 三步逐节点出现
        self.at_clip("s4-c04")  # 设当前 token 的表示是 x
        _reveal(self, subline, 0.6)
        self.at_clip("s4-c05")  # 路由器先为每个专家打分
        _reveal(self, subline2, 0.6)

        title2 = t("把三步写成公式", 40, WHITE, "BOLD")
        f1 = MathTex(r"s_i(x)=\mathrm{router}(x)_i", font_size=40, color=CYAN)
        f2 = t("Top-k：取分数最高的 k 个", 36, GREEN, "BOLD")
        f3 = MathTex(r"y=\sum_i w_i(x)\,\mathrm{Expert}_i(x)", font_size=38, color=YELL)
        page2 = _page(title2, f1, f2, f3, buff=1.55)
        self.at_clip("s4-c06")  # s 等于 router 对 x 的输出
        _clear(self, page1)
        _reveal_title(self, title2)
        _reveal_formula(self, f1, 0.6)
        self.at_clip("s4-c07")  # 再取分数最高的 k 个专家
        _reveal(self, f2, 0.6)
        self.at_clip("s4-c10")  # 最后把选中专家的输出
        _reveal_formula(self, f3, 0.6)

        title3 = t("256 个专家打分，只选前 8 个", 36, WHITE, "BOLD")
        title3 = fit(title3, 0.86)
        cells = VGroup(*[
            Rectangle(width=0.30, height=0.30, color=CYAN, fill_color=CYAN, fill_opacity=0.55)
            for _ in range(256)
        ])
        cells.arrange_in_grid(16, 16, buff=0.02)
        selected = VGroup(*cells[:8])
        score_note = t("Top-8：只激活分数最高的 8 个专家", 34, GREEN, "BOLD")
        page3 = _page(title3, cells, score_note, buff=0.62)
        self.at_clip("s4-c12")  # 如果 256 个专家只选 8 个
        _clear(self, page2)
        _reveal_title(self, title3)
        self.play(FadeIn(cells, run_time=0.55))
        self.at_clip("s4-c14")  # 大致是全量的 8 除以 256
        self.play_parallel(*[cell.animate.set_color(YELL).set_fill(YELL, opacity=0.9) for cell in selected],
                           run_time=0.5)
        self.wait(0.067)
        _reveal(self, score_note, 0.55)

        title4 = t("专家前馈计算 ≈ 全量的", 40, WHITE, "BOLD")
        fraction = MathTex(r"\frac{8}{256}=\frac{1}{32}", font_size=84, color=YELL)
        fraction_note = t("这是 MoE 最核心的省算力来源", 30, WHITE)
        title5 = t("但注意边界", 40, WHITE, "BOLD")
        bad = t("端到端快 32 倍", 42, RED, "BOLD")
        good = _fit(t("注意力、路由器、通信、内存访问都还在", 32, WHITE))
        tail = t("稀疏计算 ≠ API 价格的全部解释", 36, YELL, "BOLD")
        page4 = _page(title4, fraction, fraction_note, title5, bad, good, tail, buff=0.5)
        self.at_clip("s4-c15")  # 也就是三十二分之一
        _clear(self, page3)
        _reveal_title(self, title4, run_time=0.5)
        _reveal_formula(self, fraction, 0.6)
        self.at_clip("s4-c16")  # 但注意边界
        self.camera_zoom_to(fraction, scale=0.85, run_time=0.7)  # 分数推近
        _reveal_title(self, title5, 0.5)
        self.at_clip("s4-c17")  # 这不是端到端快 32 倍
        self.camera_zoom_to(run_time=0.55)  # 拉回
        _reveal(self, bad, 0.6)
        self.at_clip("s4-c18")  # 只激活 8 个专家
        cross = self.play_red_cross(bad, run_time=0.55)
        self.wait(0.067)
        _reveal(self, good, 0.6)
        self.at_clip("s4-c19")  # 能解释稀疏计算
        _reveal(self, tail, 0.6)
        self.at_clip("s4-c21")  # 独解释 API 价格
        self.wait(0.95)
        _dissolve(self, head, footer, page4, cross)
        self.pad_to_voice()


# ---------------- S5 负载均衡 ----------------
class S5(_Base):
    def construct(self):
        self.bg()
        footer = _footer(self)
        head = _header("负载不均衡：都挤一个科室")

        title1 = t("分诊的第二个问题", 40, WHITE, "BOLD")
        image = _image("s5-queue-round.png", 4.5)
        cap = _fit(t("所有病人都被送往同一科 → 排队，其他科室闲着", 32, RED))
        page1 = _page(title1, image, cap, buff=1.6)
        self.play_parallel(type_in(head, 0.7), type_in(title1, 0.6), run_time=0.7)
        self.at_clip("s5-c02")  # 如果所有病人都被送往同一科
        self.play(FadeIn(image, shift=DOWN * 0.05), run_time=0.6)
        self.at_clip("s5-c03")  # 那个科室排队
        _reveal(self, cap, 0.6)
        self.at_clip("s5-c04")  # 其他科室闲着
        self.breathe(image, loops=1)  # 滞留图微动

        title2 = t("早期做法：辅助损失", 40, WHITE, "BOLD")
        tax = _block(("把拥堵变成训练目标里的「税」", "直接惩罚不平衡的分配"), 38, CYAN, "BOLD", 28)
        w1 = _block(("太强", "干扰模型原本该学的任务"), 36, RED, "BOLD", 28)
        w2 = _block(("太弱", "压不住拥挤"), 36, MUTED, "BOLD", 28)
        tradeoffs = _fit(VGroup(w1, w2).arrange(RIGHT, buff=0.7))
        note2 = t("目标：鼓励 token 均匀分配", 30, WHITE)
        page2 = _page(title2, tax, tradeoffs, note2, buff=1.45)
        self.at_clip("s5-c05")  # 早期做法
        _clear(self, page1)
        _reveal_title(self, title2)
        self.at_clip("s5-c06")  # 在训练目标里加辅助损失
        _reveal(self, tax, 0.6)
        self.at_clip("s5-c07")  # 干扰模型原本该学的任务
        _reveal(self, w1, 0.6)
        self.at_clip("s5-c08")  # 太弱
        _reveal(self, w2, 0.6)
        self.wait(0.067)
        _reveal(self, note2, 0.55)

        title3 = t("DeepSeek-V3：无辅助损失负载均衡", 36, WHITE, "BOLD")
        title3 = fit(title3, 0.86)
        guide = _block(("偏置调节：改谁能进候选队列", "忙的更难入选，闲的更容易"), 38, GREEN, "BOLD", 28)
        b1 = _block(("太忙", "下一轮不容易入选"), 34, YELL, "BOLD", 27)
        b2 = _block(("太闲", "提高入选机会"), 34, CYAN, "BOLD", 27)
        biases = _fit(VGroup(b1, b2).arrange(RIGHT, buff=0.7))
        note3 = _fit(t("按排队长度导流，而不是改模型要学的任务", 30, WHITE))
        page3 = _page(title3, guide, biases, buff=2.6)
        self.at_clip("s5-c09")  # DeepSeek-V3 用的是无辅助损失的负载均衡
        _clear(self, page2)
        _reveal_title(self, title3)
        self.at_clip("s5-c10")  # 系统给较忙或较闲的专家
        _reveal(self, guide, 0.6)
        self.at_clip("s5-c11")  # 调整选择时的偏置
        _reveal(self, b1, 0.55)
        self.wait(0.067)
        _reveal(self, b2, 0.55)

        title4 = t("两种思路，解决同一个拥堵", 36, WHITE, "BOLD")
        title4 = fit(title4, 0.86)
        cmp1 = _block(("辅助损失", "直接改训练目标"), 42, CYAN, "BOLD", 30)
        cmp2 = _block(("偏置调节", "改候选队列"), 42, GREEN, "BOLD", 30)
        compare = _fit(VGroup(cmp1, cmp2).arrange(RIGHT, buff=0.7))
        tail = _block(("解决的不是会不会回答，", "而是 token 能否稳定分散到不同 GPU 上"), 34, YELL, "BOLD", 30)
        page4 = _page(title4, compare, note3, tail, buff=1.45)
        self.at_clip("s5-c12")  # 可以把辅助损失想成收拥堵税
        _clear(self, page3)
        _reveal_title(self, title4, 0.5)
        self.at_clip("s5-c12", offset=0.9)  # 辅助损失（同句内）
        _reveal(self, cmp1, 0.6)
        self.at_clip("s5-c13")  # 而偏置调节
        _reveal(self, cmp2, 0.6)
        self.at_clip("s5-c14")  # 更像分诊台按排队长度导流
        _reveal(self, note3, 0.55)
        self.at_clip("s5-c15")  # 它解决的不是模型会不会回答
        _reveal(self, tail, 0.65)
        self.at_clip("s5-c16")  # 而是 token 能
        self.emphasize(tail, mode="circumscribe", color=YELL, run_time=0.55)
        self.at_clip("s5-c17")  # 否稳定分散到不同 GPU 上
        self.wait(1.2)
        _dissolve(self, head, footer, page4)
        self.pad_to_voice()


# ---------------- S6 MoE 省的是哪一段 ----------------
class S6(_Base):
    def construct(self):
        self.bg()
        footer = _footer(self)
        head = _header("MoE 省下来的，是哪一段？")

        title1 = t("Transformer 里的两段结构", 38, WHITE, "BOLD")
        token = cnode("token", YELL, radius=0.78, fs=23)
        attn = _block(("注意力层", "让 token 看上下文"), 34, CYAN, "BOLD", 26)
        ffn = _block(("前馈网络 FFN", "更深的非线性变换"), 34, MUTED, "BOLD", 26)
        block = VGroup(attn, ffn).arrange(DOWN, buff=0.45)
        exp = _block(("专家集合", "MoE 替换 FFN"), 36, GREEN, "BOLD", 27)
        flow = VGroup(token, block, exp).arrange(RIGHT, buff=0.45)
        flow_arrow1 = Arrow(token.get_right(), block.get_left(), color=MUTED, buff=0.12, stroke_width=4)
        flow_arrow2 = Arrow(block.get_right(), exp.get_left(), color=GREEN, buff=0.12, stroke_width=4)
        flow_all = _fit(Group(token, flow_arrow1, block, flow_arrow2, exp))
        note1 = t("MoE 把 FFN 替换成专家集合", 32, WHITE)
        page1 = _page(title1, flow_all, note1, buff=2.5)
        self.play_parallel(type_in(head, 0.5), run_time=0.5)
        self.at_clip("s6-c02")  # 到底是哪一段
        _reveal_title(self, title1, 0.6)
        self.at_clip("s6-c03")  # Transformer 里
        self.play(FadeIn(token, flow_arrow1), run_time=0.5)
        self.at_clip("s6-c04")  # 注意力层负责让 token 看上下文
        _reveal(self, attn, 0.6)
        self.at_clip("s6-c05")  # 前馈网络 FFN
        _reveal(self, ffn, 0.6)
        self.at_clip("s6-c06")  # 负责对每个 token 做更深的变换
        self.breathe(ffn, loops=1)  # 滞留卡微动
        self.at_clip("s6-c07")  # MoE 通常把后者，替换成专家集合
        self.play(FadeIn(flow_arrow2), run_time=0.4)
        self.wait(0.067)
        _reveal(self, exp, 0.6)
        self.wait(0.067)
        _reveal(self, note1, 0.55)
        # token 走一遍完整流程：token → 注意力 → FFN → 专家集合
        path = VMobject()
        path.set_points_as_corners([
            token.get_center(), attn.get_center(), ffn.get_center(), exp.get_center(),
        ])
        dot = self.trace_dot(path, run_time=1.2)
        self.at_clip("s6-c08")  # 所以更准确的说法不是 90% 参数没有用
        _clear(self, page1, dot)

        title2 = t("更准确的说法", 40, WHITE, "BOLD")
        bad = t("90% 参数没有用", 42, RED, "BOLD")
        good = _block(("这一次前向计算，", "大多数路由专家没有被调用"), 38, GREEN, "BOLD", 30)
        still = _block(("它们仍是模型容量的一部分，", "只是这次没被选中"), 34, WHITE, "BOLD", 28)
        page2 = _page(title2, bad, good, still, buff=1.35)
        _reveal_title(self, title2, 0.5)
        self.at_clip("s6-c08", offset=1.5)  # 90% 参数没有用（句内）
        _reveal(self, bad, 0.6)
        self.at_clip("s6-c09")  # 而是：在当前 token 的这一次前向计算中
        cross = self.play_red_cross(bad, run_time=0.55)
        self.wait(0.067)
        _reveal(self, good, 0.6)
        self.at_clip("s6-c11")  # 它们仍是模型容量的一部分
        _reveal(self, still, 0.6)
        self.at_clip("s6-c12", offset=0.8)  # 只是这次没被选中（句尾前清场）
        _clear(self, page2, cross)

        title3 = t("代价转移到工程问题", 40, WHITE, "BOLD")
        c1 = _block(("分发", "token 转给正确专家"), 40, CYAN, "BOLD", 29)
        c2 = _block(("收回", "专家输出汇总"), 40, GREEN, "BOLD", 29)
        comms = _fit(VGroup(c1, c2).arrange(RIGHT, buff=0.7))
        tail = t("专家越分散，通信越可能成为瓶颈", 36, YELL, "BOLD")
        page3 = _page(title3, comms, tail, buff=2.5)
        self.at_clip("s6-c13")  # 专家越分散
        _reveal_title(self, title3, 0.5)
        self.at_clip("s6-c13", offset=0.6)  # 分发/聚合（同句内）
        self.play(FadeIn(c1), FadeIn(c2), run_time=0.6)
        self.at_clip("s6-c14")  # 通信越可能成为瓶颈
        _reveal(self, tail, 0.5)
        self.emphasize(tail, mode="circumscribe", color=YELL, run_time=0.4)
        _dissolve(self, head, footer, page3, run_time=0.85)
        self.pad_to_voice()


# ---------------- S7 回到价格：三层钥匙 + 完整公式 ----------------
class S7(_Base):
    def construct(self):
        self.bg()
        footer = _footer(self)
        head = _header("把 30 倍拆开：三层钥匙")

        l1 = _block(("第一层 · 缓存复用", "95% 命中，重复的仓库上下文变得很便宜"), 40, CYAN, "BOLD", 30)
        l1b = t("提示缓存的作用，不是 MoE 专属", 32, WHITE)
        l2 = _block(("第二层 · 稀疏计算", "专家前馈只运行必要专家"), 40, GREEN, "BOLD", 30)
        page1 = _page(l1, l1b, l2, buff=2.6)
        self.play_parallel(type_in(head, 0.7), run_time=0.7)
        self.at_clip("s7-c02")  # 缓存复用
        _reveal(self, l1, 0.65)
        self.at_clip("s7-c04")  # 让重复的仓库上下文变得很便宜
        _reveal(self, l1b, 0.6)
        self.at_clip("s7-c07")  # 第二层
        _reveal(self, l2, 0.65)

        l3 = _block(("第三层 · 系统工程", "把稀疏计算变成低账单"), 40, YELL, "BOLD", 30)
        chips = [
            t(label, 30, MUTED, "BOLD")
            for label in ("数值精度", "通信", "并行策略", "批处理", "服务调度")
        ]
        chips_row1 = VGroup(chips[0], chips[1], chips[2]).arrange(RIGHT, buff=0.6)
        chips_row2 = VGroup(chips[3], chips[4]).arrange(RIGHT, buff=0.6)
        tail = _block(("任何一环效率不足，", "省下的算力都会被等网络、等显存、等队列吃掉"), 34, YELL, "BOLD", 30)
        page2 = _page(l3, chips_row1, chips_row2, tail, buff=1.9)
        self.at_clip("s7-c10")  # 系统工程
        _clear(self, page1)
        _reveal(self, l3, 0.65)
        self.at_clip("s7-c11")  # 还要靠数值精度
        _reveal(self, chips[0], 0.5)
        self.at_clip("s7-c12")  # 通信
        _reveal(self, chips[1], 0.5)
        self.at_clip("s7-c13")  # 并行策略、批处理和服务调度
        _reveal(self, chips[2], 0.5)
        self.wait(0.067)
        _reveal(self, chips[3], 0.5)
        self.wait(0.067)
        _reveal(self, chips[4], 0.5)
        self.at_clip("s7-c14")  # 任何一环效率不足
        _reveal(self, tail, 0.6)

        title2 = t("更完整的公式", 40, WHITE, "BOLD")
        equation = t("低成本 API =", 40, WHITE, "BOLD")
        terms = [
            t("缓存复用", 36, CYAN, "BOLD"),
            t("稀疏计算", 36, GREEN, "BOLD"),
            t("低精度计算", 36, YELL, "BOLD"),
            t("高效通信与服务", 34, MUTED, "BOLD"),
        ]
        plus = t("＋", 30, MUTED)
        term_row1 = VGroup(terms[0], plus.copy(), terms[1], plus.copy()).arrange(RIGHT, buff=0.22)
        term_row2 = VGroup(terms[2], plus.copy(), terms[3]).arrange(RIGHT, buff=0.22)
        note1 = t("四把钥匙缺一不可", 34, YELL, "BOLD")
        page3 = _page(title2, equation, term_row1, term_row2, note1, buff=1.25)
        self.at_clip("s7-c17")  # 更完整的公式：低成本 API
        _clear(self, page2)
        _reveal_title(self, title2)
        self.wait(0.067)
        _reveal(self, equation, 0.55)
        self.at_clip("s7-c18")  # 等于缓存复用
        _reveal(self, terms[0], 0.6)
        self.at_clip("s7-c19")  # 加稀疏计算
        _reveal(self, terms[1], 0.6)
        self.at_clip("s7-c20")  # 加低精度计算
        _reveal(self, terms[2], 0.6)
        self.wait(0.067)
        _reveal(self, terms[3], 0.6)
        self.at_clip("s7-c21")  # MoE 负责谁干活
        _reveal(self, note1, 0.55)
        self.at_clip("s7-c22")  # 但不负责全部故事
        self.emphasize(note1, mode="circumscribe", color=YELL, run_time=0.45)
        self.wait(0.05)
        _dissolve(self, head, footer, page3, run_time=0.95)
        self.pad_to_voice()


# ---------------- S8 总结 + 尾卡 ----------------
class S8(_Base):
    def construct(self):
        self.bg()
        footer = _footer(self)
        head = _header("一句话总结")

        title2 = t("按真实写代码的 token 结构", 40, WHITE, "BOLD")
        row1 = _block(("¥0.203", "每 1M 总 token"), 58, YELL, "BOLD", 30)
        row2 = VGroup(MathTex(r"\frac{1}{30}", font_size=56, color=GREEN),
                      t("约 GPT-5.6 Sol", 30, MUTED)).arrange(DOWN, buff=0.15)
        row3 = VGroup(MathTex(r"\frac{1}{56.7}", font_size=56, color=CYAN),
                        t("约 Claude Fable 5", 30, MUTED)).arrange(DOWN, buff=0.15)
        summary_rows = VGroup(row1, row2, row3).arrange(DOWN, buff=0.7)
        note2 = _fit(t("DeepSeek-V4 Pro 每 1M 总 token 约 2 毛钱", 32, WHITE))
        page1 = _page(title2, summary_rows, note2, buff=0.85)
        self.play_parallel(type_in(head, 0.7), run_time=0.7)
        self.at_clip("s8-c02")  # 按笔者真实写代码的 token 结构
        _reveal_title(self, title2)
        self.at_clip("s8-c03")  # DeepSeek-V4 Pro 每 1M 总 token 约 2 毛钱
        _reveal(self, row1, 0.65)
        self.wait(0.067)
        _reveal(self, note2, 0.6)
        self.at_clip("s8-c04")  # 约是 GPT-5.6 Sol 的 30 分之一
        _reveal(self, row2, 0.65)
        self.at_clip("s8-c05")  # 是本文最贵的 Claude Fable 5 的 56.7 分之一
        _reveal(self, row3, 0.65)
        self.wait(0.067)
        self.breathe(row1, loops=2)  # 滞留微动

        title3 = t("下一篇预告", 40, WHITE, "BOLD")
        mla = _block(("MLA：多头潜在注意力", "减少 KV 缓存的显存压力"), 42, YELL, "BOLD", 30)
        note3 = t("当上下文越来越长", 30, MUTED)
        page2 = _page(title3, mla, note3, buff=2.5)
        self.at_clip("s8-c06")  # 下一篇
        _clear(self, page1)
        _reveal_title(self, title3)
        self.at_clip("s8-c08")  # 模型怎样用 MLA
        _reveal(self, mla, 0.6)
        self.at_clip("s8-c09")  # 减少 KV 缓存的显存压力
        _reveal(self, note3, 0.5)

        title4 = t("最后留个问题", 40, WHITE, "BOLD")
        opt_a = _block(("为更强的模型付高价", "性能优先"), 40, CYAN, "BOLD", 28)
        opt_b = _block(("用足够强、可反复调用的模型", "做日常开发"), 36, GREEN, "BOLD", 28)
        page3 = _page(title4, opt_a, opt_b, buff=2.4)
        self.at_clip("s8-c10")  # 最后留个问题
        _clear(self, page2)
        _reveal_title(self, title4)
        self.at_clip("s8-c11")  # 你更愿意为更强的模型付高价
        _reveal(self, opt_a, 0.7)
        self.at_clip("s8-c12")  # 还是用足够强、但能反复调用的模型
        _reveal(self, opt_b, 0.7)

        logo = ImageMobject(str(pathlib.Path(__file__).resolve().parent / "avatar-sjai-round.png"))
        logo.scale_to_fit_width(3.45)
        follow = VGroup(
            t("关注「数解AI」", 44, YELL, "BOLD"),
            t("《DeepSeek便宜30倍的秘密：MoE混合专家入门》", 25, WHITE, "BOLD"),
            t("查看公众号文章 · 图文全解", 25, GREEN),
            t("下一篇：MLA 多头潜在注意力", 23, MUTED),
        ).arrange(DOWN, buff=0.38)
        brand_page = _page(logo, follow, buff=0.8)
        self.at_clip("s8-c13")  # 评论区聊聊
        _clear(self, page3)
        _dissolve(self, head, footer)
        self.play_parallel(FadeIn(logo, scale=0.9), type_in(follow, run_time=0.8), run_time=0.8)
        self.pad_to_voice()
