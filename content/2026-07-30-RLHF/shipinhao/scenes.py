#!/usr/bin/env python3
"""《RLHF怎么让模型选出好回答？》视频号 Manim 动画（竖屏 1080×1920）

8 个场景 S1-S8 + 封面 Cover，与 storyboard.md 一一对应。
通用工具（t/_card/boxed/fit/type_in/arc_curve/_Base 等）在 scripts/manim_helpers.py，
本文件只放：VOICE_DUR（配音时长）、TAIL、场景类。
用法：
  python3 -m manim render -qm --disable_caching scenes.py S1 S2 S3 S4 S5 S6 S7 S8
  python3 -m manim render -qm -s --disable_caching scenes.py Cover
"""
from __future__ import annotations

import pathlib
import sys


def _scripts_dir() -> str:
    """向上查找项目 scripts/ 目录（含 manim_helpers.py），不依赖场景文件深度。"""
    p = pathlib.Path(__file__).resolve().parent
    for _ in range(6):
        cand = p / "scripts"
        if (cand / "manim_helpers.py").exists():
            return str(cand)
        p = p.parent
    raise RuntimeError("找不到 scripts/manim_helpers.py")


sys.path.insert(0, _scripts_dir())
from manim_helpers import *

config.background_color = "#0F1A30"

# 配音时长（口播实测，勿改）
VOICE_DUR = {"S1": 28.288, "S2": 19.456, "S3": 30.144, "S4": 29.568,
             "S5": 30.187, "S6": 38.784, "S7": 34.624, "S8": 36.416}
TAIL = 2.5
# 渲染缓冲（build 会截到 0.1s）


def t(text: str, size: float = 34, color: str = WHITE, weight: str = "NORMAL") -> Text:
    return Text(text, font=FONT, font_size=size, color=color, weight=weight)


# ---------------- S1 开场钩子：三个回答 + 人 vs 模型 ----------------
class S1(_Base):
    def construct(self):
        self.bg()
        self.footer()
        head = t("同一个问题，三个回答", 38, YELL, "BOLD").to_edge(UP, buff=1.2)
        self.play(type_in(head, run_time=1.1))
        # 开场小字：点明示例模型（布局规范 25，QA A12）；常驻左上角不与下方内容重叠
        hint = t("本片以 InstructGPT 为例", 20, MUTED).to_corner(UL, buff=0.6)
        self.play(type_in(hint, run_time=0.6))

        # 段1（0-9s）：问题框 + 左对齐三卡 + 旁置 ✔✗
        # pause anchors: 3.119, 6.149, 8.682
        q = _card("请解释「梯度下降」", 5.4, 1.1, MUTED, WHITE, 28, CARD_FILL2, "BOLD")
        q.next_to(head, DOWN, buff=1.0)
        self.play_scroll_unroll(q, run_time=1.5)

        # 三卡：统一宽 5.4、高 1.1，与问题框同宽、左对齐（右侧留位放 ✔✗）
        CARD_W = 5.4
        a = _card("A · 定义+步骤，像说明书", CARD_W, 1.1, CYAN, WHITE, 26, CARD_FILL, "NORMAL")
        b = _card("B · 语气自然，却说反了", CARD_W, 1.1, CYAN, WHITE, 26, CARD_FILL, "NORMAL")
        c = _card("C · 很谨慎，没回答", CARD_W, 1.1, CYAN, WHITE, 26, CARD_FILL, "NORMAL")
        rows = VGroup(a, b, c).arrange(DOWN, buff=0.6, aligned_edge=LEFT)
        rows.next_to(q, DOWN, buff=1.1)
        rows.align_to(q, LEFT)  # 与问题框左对齐
        self.at(1.0)
        self.play_scroll_unroll(a, run_time=1.2)
        self.at(3.119)
        self.play_scroll_unroll(b, run_time=1.2)
        self.at(6.149)
        self.play_scroll_unroll(c, run_time=1.2)

        # 段2（9-11s）：旁置 ✔/✗ 标记（放大再缩小闪烁）
        # 8.682, 10.817
        self.at(8.682)
        chk_a = self.play_mark("✔", a, GREEN)
        self.at(9.8)
        x_b = self.play_mark("✗", b, RED)
        self.at(10.5)
        qm_c = self.play_mark("?", c, MUTED)

        # 段3（11-13s）：只能留一个，你选哪个
        self.at(11.4)
        self.play(FadeOut(VGroup(rows, chk_a, x_b, qm_c), shift=UP * 0.03), run_time=0.3)
        sel = t("只能留一个，你选哪个？", 36, YELL, "BOLD")
        fit(sel, 0.95)
        sel.next_to(q, DOWN, buff=1.4)
        self.play(type_in(sel, run_time=1.1))

        # 段4（14-17s）：人可以凭常识判断 → 选中 C
        # 14.087, 16.681
        self.at(14.087)
        self.play(FadeOut(sel, shift=UP * 0.03), run_time=0.3)
        human = boxed("人可以凭常识判断", 4.6, 1.1, GREEN, 30, fill=0.2, weight="BOLD")
        human.next_to(q, DOWN, buff=1.3)
        self.play_scroll_unroll(human, run_time=1.7)
        self.at(15.5)
        ca = boxed("A", 1.6, 1.0, GREEN, 26, fill=0.25, weight="BOLD")   # 人凭常识选 A（高亮）
        cb = boxed("B", 1.6, 1.0, MUTED, 26, fill=0.08)
        cc = boxed("C", 1.6, 1.0, MUTED, 26, fill=0.08)
        trio = VGroup(ca, cb, cc).arrange(RIGHT, buff=0.7).next_to(human, DOWN, buff=1.2)
        self.play(FadeIn(trio, shift=DOWN * 0.05), run_time=0.5)
        self.at(16.2)
        self.play(ca.animate.scale(1.15), cb.animate.set_opacity(0.5),
                  cc.animate.set_opacity(0.5), run_time=0.5)
        pick = t("人：看语义，直接挑 A", 26, GREEN, "BOLD").next_to(trio, DOWN, buff=1.0)
        self.play(type_in(pick, run_time=0.8))

        # 段5（18-22s）：模型不行，只能看到数字
        # 18.84, 20.091, 22.174
        self.at(18.84)
        self.play(FadeOut(VGroup(human, trio, pick), shift=UP * 0.03), run_time=0.3)
        lab = t("模型不行，它只能看到一组数字", 30, WHITE, "BOLD")
        fit(lab, 0.95)
        lab.next_to(q, DOWN, buff=1.3)
        self.play(type_in(lab, run_time=1.1))
        # 三个纵向立柱（1.3 / 0.7 / 0.2）并排，从底部向上生长
        self.at(20.091)
        bar_grp = VGroup()
        for h, v, col in ((2.6, "1.3", CYAN), (1.4, "0.7", GREEN), (0.4, "0.2", MUTED)):
            bar = Rectangle(width=0.75, height=h, color=col, fill_color=col, fill_opacity=0.7)
            val = t(v, 28, col, "BOLD").next_to(bar, DOWN, buff=0.2)
            bar_grp.add(VGroup(bar, val))
        bar_grp.arrange(RIGHT, buff=1.1, aligned_edge=DOWN).next_to(lab, DOWN, buff=1.5)
        for bg in bar_grp:
            self.play(GrowFromEdge(bg[0], DOWN, run_time=0.4), type_in(bg[1], run_time=0.4), run_time=0.4)
        self.at(21.6)
        zero = t("它对「好」毫无概念，只有数字", 26, MUTED).next_to(bar_grp, DOWN, buff=1.1)
        self.play(type_in(zero, run_time=0.8))

        # 段6（23-28s）：需要有人把"更好"变成训练信号 → RLHF
        # 23.636, 26.451
        self.at(23.636)
        self.play(FadeOut(VGroup(lab, bar_grp, zero), shift=UP * 0.03), run_time=0.3)
        need = t("把「这个回答更好」变成训练信号", 30, WHITE, "BOLD")
        fit(need, 0.95)
        need.next_to(q, DOWN, buff=1.3)
        self.play(type_in(need, run_time=1.0))
        self.at(26.451)
        rlhf = t("这就是 RLHF", 44, YELL, "BOLD")
        fit(rlhf, 0.95)
        rlhf.next_to(need, DOWN, buff=1.2)
        self.play(type_in(rlhf, run_time=1.1))
        self.pad_to_voice()



# ---------------- S2 三道工序：SFT 教听话，RLHF 教选择 ----------------
class S2(_Base):
    def construct(self):
        self.bg()
        self.footer()
        head = t("先说清它在哪一步", 38, YELL, "BOLD").to_edge(UP, buff=1.2)
        self.play(type_in(head, run_time=1.1))

        # 段1（0-8s）：垂直流程图：预训练 → SFT → RLHF，各带目标标签
        # pauses: 0.522, 2.482, 5.278, 7.44
        self.at(0.522)
        # 三工序节点
        nodes = [
            ("预训练", "预测下一个 token", CYAN),
            ("SFT", "教它听指令", GREEN),
            ("RLHF", "多个答案里选更好", YELL),
        ]
        boxes = []
        prev = None
        for i, (name, goal, col) in enumerate(nodes):
            nb = boxed(name, 3.2, 1.0, col, 30, fill=0.2, weight="BOLD")
            gl = t(goal, 24, WHITE)
            cell = VGroup(nb, gl).arrange(DOWN, buff=0.25)
            if prev is None:
                cell.next_to(head, DOWN, buff=1.0)
            else:
                cell.next_to(prev, DOWN, buff=0.6)
            boxes.append(cell)
            prev = cell
        # 显示：框拉幕 + 目标文字打字
        self.play_scroll_unroll(boxes[0][0], run_time=0.9)
        self.play(type_in(boxes[0][1], run_time=0.5))
        self.at(2.482)
        ar1 = Arrow(boxes[0].get_bottom(), boxes[1].get_top(), color=MUTED, buff=0.15, stroke_width=5)
        self.play(Create(ar1), run_time=0.5)
        self.play_scroll_unroll(boxes[1][0], run_time=0.9)
        self.play(type_in(boxes[1][1], run_time=0.5))
        self.at(5.278)
        ar2 = Arrow(boxes[1].get_bottom(), boxes[2].get_top(), color=MUTED, buff=0.15, stroke_width=5)
        self.play(Create(ar2), run_time=0.5)
        self.play_scroll_unroll(boxes[2][0], run_time=0.9)
        self.play(type_in(boxes[2][1], run_time=0.5))

        # 段2（7-12s）：RLHF 是更难的一步 → 设问
        # 7.44, 10.428, 12.217
        self.at(7.44)
        # 高亮 RLHF 框：只降低填充不透明度（露出深背景），边框/文字保持 YELL 不变（set_color 会把填充也变黄导致黄字看不清）
        self.play(boxes[2][0].animate.set_fill_opacity(0.35), run_time=0.4)
        harder = t("RLHF 是更难的一步", 30, YELL, "BOLD").next_to(boxes[2], DOWN, buff=0.8)
        self.play(type_in(harder, run_time=0.8))
        self.at(10.428)
        q = t("哪种接法更有帮助、更准确、更安全？", 27, WHITE, "BOLD")
        fit(q, 0.95)
        q.next_to(harder, DOWN, buff=0.8)
        self.play(type_in(q, run_time=1.0))

        # 段3（14.8-19.5s）：不是三次重复，是三个不同目标
        # 台词：哪一种更有帮助…更安全(12.22-15.66) 它们不是三次重复(15.66) 而是三个不同的目标(17.66)
        self.at(14.8)
        self.play(FadeOut(VGroup(boxes[0], boxes[1], boxes[2], ar1, ar2, harder, q),
                          shift=UP * 0.03), run_time=0.3)
        notrepeat = t("不是三次重复", 32, RED, "BOLD")
        fit(notrepeat, 0.95)
        notrepeat.next_to(head, DOWN, buff=1.4)
        self.at(14.9)
        self.play(type_in(notrepeat, run_time=0.8))
        self.at(15.662)
        self.play_red_cross(notrepeat)
        self.at(17.3)
        three = t("是三个不同的目标", 34, GREEN, "BOLD")
        fit(three, 0.95)
        three.next_to(notrepeat, DOWN, buff=1.5)
        self.play(type_in(three, run_time=1.0))
        self.pad_to_voice()


# ---------------- S3 时间线：InstructGPT → ChatGPT + 1.3B vs 175B ----------------
class S3(_Base):
    def construct(self):
        self.bg()
        self.footer()
        head = t("两个名字，别搞混", 38, YELL, "BOLD").to_edge(UP, buff=1.2)
        self.play(type_in(head, run_time=1.1))

        # 段1（0-10s）：横向时间轴 + 两个节点
        # pauses: 0.361, 2.154, 3.717, 6.08, 7.634, 8.766
        self.at(0.361)
        axis = Line(LEFT * 3.0, RIGHT * 3.0, color=MUTED, stroke_width=3).next_to(head, DOWN, buff=1.6)
        # 时间刻度
        d1 = t("2022.3", 20, CYAN).move_to(axis.get_left() + RIGHT * 1.0 + DOWN * 0.35)
        d2 = t("2022.11.30", 20, GREEN).move_to(axis.get_right() + LEFT * 1.0 + DOWN * 0.35)
        p1 = Dot(axis.get_left() + RIGHT * 1.0, color=CYAN, radius=0.09)
        p2 = Dot(axis.get_right() + LEFT * 1.0, color=GREEN, radius=0.09)
        self.play(Create(axis), run_time=0.6)
        self.play(type_in(d1, run_time=0.6), FadeIn(p1), run_time=0.6)
        self.at(3.717)
        self.play(type_in(d2, run_time=0.6), FadeIn(p2), run_time=0.6)
        # 节点卡：同宽同高、左对齐，灰字说明各自性质
        self.at(6.08)
        ig = _card("InstructGPT 论文", 5.4, 1.1, CYAN, CYAN, 26, CARD_FILL, "BOLD")
        igtag = t("（论文/证明题）", 22, MUTED)
        igcell = VGroup(ig, igtag).arrange(DOWN, buff=0.3)
        igcell.next_to(axis, DOWN, buff=1.3)
        igcell.align_to(axis, LEFT)
        self.play_scroll_unroll(ig, run_time=1.4)
        self.play(type_in(igtag, run_time=0.6))
        self.at(8.766)
        cg = _card("ChatGPT 研究预览", 5.4, 1.1, GREEN, GREEN, 26, CARD_FILL, "BOLD")
        cgtag = t("（产品/应用题）", 22, MUTED)
        cgcell = VGroup(cg, cgtag).arrange(DOWN, buff=0.3)
        cgcell.next_to(igcell, DOWN, buff=0.9)
        cgcell.align_to(axis, LEFT)
        self.play_scroll_unroll(cg, run_time=1.4)
        self.play(type_in(cgtag, run_time=0.6))
        igcell.add(cgcell)  # 合并便于后续 FadeOut

        # 段2（10-18s）：论文 vs 产品（证明题 vs 应用题）
        # 10.073, 11.917, 13.273, 15.257
        self.at(11.917)
        self.play(FadeOut(VGroup(axis, d1, d2, p1, p2, ig, igtag, cg, cgtag), shift=UP * 0.03), run_time=0.3)
        paper = _card("InstructGPT = 论文/证明题", 5.4, 1.1, CYAN, CYAN, 27, CARD_FILL, "BOLD")
        paper.next_to(head, DOWN, buff=1.3)
        self.play_scroll_unroll(paper, run_time=1.5)
        self.at(13.273)
        prod = _card("ChatGPT = 产品/应用题", 5.4, 1.1, GREEN, GREEN, 27, CARD_FILL, "BOLD")
        prod.next_to(paper, DOWN, buff=1.0)
        prod.align_to(paper, LEFT)
        ar = Arrow(paper.get_bottom(), prod.get_top(), color=MUTED, buff=0.15, stroke_width=5)
        self.play_scroll_unroll(prod, run_time=1.2)
        self.play(Create(ar), run_time=0.5)

        # 段3（13-30s）：天平 175B vs 1.3B 输出质量倾斜爆点
        # 台词锚点（场景内）：论文给过冲击性结果13.2、1.3B参数15.48、超过175B 17.77、不是小模型更强20.25
        self.at(13.3)
        self.play(FadeOut(VGroup(paper, prod, ar), shift=UP * 0.03), run_time=0.3)
        shock = t("冲击性结果", 32, YELL, "BOLD").next_to(head, DOWN, buff=1.4)
        self.play(type_in(shock, run_time=0.8))
        # 天平：支点定在上中部，吊杆连盘、砝码坐盘上
        self.at(15.2)
        pivot = np.array([0.0, 2.9, 0.0])
        rig, pans, piv = self.build_balance("175B", "GPT-3.5", "1.3B", "InstructGPT",
                                            center=pivot, beam=4.6, pan_y=-1.0)
        self.play(FadeIn(rig, shift=DOWN * 0.05), FadeIn(pans, shift=DOWN * 0.05), run_time=0.7)
        self.at(16.4)
        why_lab = t("比的是「输出质量」，不是参数量", 24, MUTED).next_to(pans, DOWN, buff=0.6)
        why_lab.set_x(0)
        self.play(type_in(why_lab, run_time=0.8))

        # 倾斜：InstructGPT 一侧（右）下沉 → 质量胜出（盘组保持水平）
        self.at(17.6)
        self.tilt_balance(rig, pans, piv, -0.30, run_time=1.0)
        win = t("小模型，输出却更被偏好", 30, YELL, "BOLD")
        fit(win, 0.9)
        win.next_to(why_lab, DOWN, buff=0.8)
        self.play(type_in(win, run_time=1.0))
        self.at(20.2)
        why = t("不是小模型更强，是后训练贴近用户意图", 24, WHITE)
        fit(why, 0.95)
        why.next_to(win, DOWN, buff=0.8)
        self.play(type_in(why, run_time=1.0))
        self.pad_to_voice()




# ---------------- S4 经典三工序①②：SFT 进赛道 + 人类比较 ----------------
class S4(_Base):
    def construct(self):
        self.bg()
        self.footer()
        head = t("经典 RLHF 怎么走？", 38, YELL, "BOLD").to_edge(UP, buff=1.2)
        self.play(type_in(head, run_time=1.1))

        # 段1（0-10s）：工序① SFT 进赛道
        # pauses: 0.445, 2.588, 4.754, 9.966
        self.at(0.445)
        # 赛道：一条水平线 + 起点
        track = Line(LEFT * 2.6, RIGHT * 2.6, color=MUTED, stroke_width=4).next_to(head, DOWN, buff=1.9)
        start = t("起点", 20, MUTED).move_to(track.get_left() + DOWN * 0.35)
        self.play(Create(track), type_in(start, run_time=0.6), run_time=0.6)
        # base model 起点球
        base_dot = Dot(track.get_left(), color=WHITE, radius=0.12)
        self.play(FadeIn(base_dot), run_time=0.3)
        self.at(2.588)
        step1 = boxed("① 先用 SFT 进赛道", 4.8, 1.1, CYAN, 30, fill=0.2, weight="BOLD")
        step1.next_to(track, DOWN, buff=0.9)
        self.play_scroll_unroll(step1, run_time=1.5)
        # base dot 沿赛道向右滑
        self.at(4.754)
        self.play(base_dot.animate.move_to(track.get_center()), run_time=0.7)
        # 运动员类比
        self.at(7.0)
        athlete = t("像运动员先学会动作，再谈比赛", 24, MUTED).next_to(step1, DOWN, buff=0.9)
        self.play(type_in(athlete, run_time=0.8))

        # 段2（10-20s）：工序② 人类只比较两个
        # 9.966, 10.885, 12.857, 14.65, 17.446, 19.576
        self.at(9.966)
        self.play(FadeOut(VGroup(track, start, base_dot, step1, athlete), shift=UP * 0.03), run_time=0.3)
        step2 = boxed("② 人类不写答案，只比较两个", 6.0, 1.1, GREEN, 28, fill=0.2, weight="BOLD")
        step2.next_to(head, DOWN, buff=1.3)
        self.play_scroll_unroll(step2, run_time=1.5)
        self.at(10.885)
        prompt = boxed("同一 prompt", 3.4, 1.0, WHITE, 28, fill=0.08, weight="BOLD")
        prompt.next_to(step2, DOWN, buff=1.2)
        self.play_scroll_unroll(prompt, run_time=1.5)
        # A 和 B 两个回答
        self.at(12.857)
        a = boxed("回答 A", 3.0, 1.1, CYAN, 28, fill=0.15, weight="BOLD")
        b = boxed("回答 B", 3.0, 1.1, GREEN, 28, fill=0.15, weight="BOLD")
        pair = VGroup(a, b).arrange(RIGHT, buff=1.6).next_to(prompt, DOWN, buff=1.2)
        self.play_scroll_unroll(a, run_time=1.0)
        self.play_scroll_unroll(b, run_time=1.0)
        # 标注员选择
        self.at(14.65)
        picker = t("标注员：选哪个更好？", 28, YELL, "BOLD")
        picker.next_to(pair, DOWN, buff=1.2)
        self.play(type_in(picker, run_time=0.8))
        # 高亮选中 A
        self.at(17.446)
        self.play(a.animate.set_fill_opacity(0.35).scale(1.05), b.animate.set_opacity(0.6), run_time=0.5)
        chosen_tag = t("chosen", 24, GREEN, "BOLD").next_to(a, DOWN, buff=0.4)
        self.play(type_in(chosen_tag, run_time=0.6))

        # 段3（19.8-29.6s）：不换页——在 A/B 回答卡上直接打 ✓/✗（chosen/rejected）
        # 台词：偏好数据写成(19.72) chosen A(21.59) rejected B(22.93) 不是宇宙真理(25.66)
        self.at(19.8)
        ck_a = t("✓", 40, GREEN, "BOLD").next_to(a, UP, buff=0.12)
        ck_a.align_to(a, RIGHT)
        self.play(FadeIn(ck_a, scale=1.5), run_time=0.4)
        self.at(21.6)
        xk_b = t("✗", 40, RED, "BOLD").next_to(b, UP, buff=0.12)
        xk_b.align_to(b, RIGHT)
        self.play(FadeIn(xk_b, scale=1.5), run_time=0.4)
        self.at(22.9)
        rej_tag = t("rejected", 24, RED, "BOLD").next_to(b, DOWN, buff=0.4)
        self.play(type_in(rej_tag, run_time=0.6))
        self.at(25.6)
        truth = t("chosen 不是宇宙真理，只是这位标注员更偏好", 25, MUTED)
        fit(truth, 0.95)
        truth.next_to(picker, DOWN, buff=0.7)
        truth.set_x(0)
        self.play(type_in(truth, run_time=0.8))
        self.pad_to_voice()


# ---------------- S5 奖励模型：把排序变成分数 ----------------
class S5(_Base):
    def construct(self):
        self.bg()
        self.footer()
        head = t("奖励模型：把排序变成分数", 38, YELL, "BOLD").to_edge(UP, buff=1.2)
        self.play(type_in(head, run_time=1.1))

        # 段1（0-9s）：回答 → 奖励模型 → 分数（简洁垂直流程）
        # pauses: 3.056, 5.485, 7.467, 9.086
        self.at(0.6)
        prob = _card("模型参数读不了「人类觉得 A 比 B 好」", 6.2, 1.1, MUTED, WHITE, 27, CARD_FILL2, "BOLD")
        prob.next_to(head, DOWN, buff=1.3)
        self.play_scroll_unroll(prob, run_time=1.7)
        # 奖励模型（模型本体，居中），下面左→右 回答→分数
        self.at(3.056)
        rm = _card("奖励模型 RM", 3.2, 1.0, GREEN, GREEN, 26, CARD_FILL, "BOLD")
        rm.next_to(prob, DOWN, buff=1.3)
        self.play_scroll_unroll(rm, run_time=1.5)
        self.at(5.485)
        ans = _card("回答", 2.2, 1.0, CYAN, WHITE, 28, CARD_FILL, "BOLD")
        score = Rectangle(width=2.2, height=1.0, color=GREEN, fill_color=GREEN, fill_opacity=0.7)
        sc_val = t("2.7", 32, GREEN, "BOLD").next_to(score, DOWN, buff=0.2)
        # 回答在左，分数在右（箭头连接），水平对齐
        ans.next_to(rm, DOWN, buff=1.0).shift(LEFT * 1.4)
        score.move_to(ans.get_center() + RIGHT * 3.6)
        sc_val.next_to(score, DOWN, buff=0.2)
        arrow = Arrow(ans.get_right(), score.get_left(), color=YELL, buff=0.2, stroke_width=6)
        self.play_scroll_unroll(ans, run_time=1.0)
        self.play(Create(arrow), run_time=0.5)
        self.play(GrowFromEdge(score, LEFT, run_time=0.6), type_in(sc_val, run_time=0.6), run_time=0.6)
        self.at(7.6)
        sim = t("像一个「人类偏好模拟器」", 28, CYAN, "BOLD")
        fit(sim, 0.85)
        sim.next_to(score, DOWN, buff=1.1)
        sim.set_x(0)
        self.play(type_in(sim, run_time=1.0))

        # 段2（9-18s）：偏好建模公式 + sigmoid 曲线
        # 9.086, 11.985, 14.601, 16.054
        self.at(9.086)
        self.play(FadeOut(VGroup(prob, ans, arrow, rm, score, sc_val, sim), shift=UP * 0.03), run_time=0.3)
        formula = sigma_term("w", "l", 28, WHITE)
        fit(formula, 0.95)
        formula.next_to(head, DOWN, buff=1.3)
        self.play(FadeIn(formula, shift=DOWN * 0.05), run_time=0.7)
        # 两个分数条：w 高 l 低
        self.at(11.985)
        fw = Rectangle(width=2.2, height=1.3, color=GREEN, fill_color=GREEN, fill_opacity=0.6)
        fl = Rectangle(width=2.2, height=0.6, color=RED, fill_color=RED, fill_opacity=0.5)
        fwl = t("r(y_w) 高", 22, GREEN, "BOLD").next_to(fw, DOWN, buff=0.2)
        fll = t("r(y_l) 低", 22, RED, "BOLD").next_to(fl, DOWN, buff=0.2)
        bars = VGroup(VGroup(fw, fwl), VGroup(fl, fll)).arrange(RIGHT, buff=1.4, aligned_edge=DOWN)
        bars.next_to(formula, DOWN, buff=1.2)
        self.play(GrowFromEdge(fw, LEFT, run_time=0.6), type_in(fwl, run_time=0.6), run_time=0.6)
        self.play(GrowFromEdge(fl, LEFT, run_time=0.6), type_in(fll, run_time=0.6), run_time=0.6)
        # sigmoid 曲线
        self.at(14.601)
        self.play(FadeOut(VGroup(formula, bars), shift=UP * 0.03), run_time=0.3)
        axes = Axes(x_range=[-4, 4], y_range=[0, 1.1], x_length=5.6, y_length=2.6,
                    axis_config={"color": MUTED, "stroke_width": 3,
                                 "include_ticks": False, "include_tip": True})
        axes.next_to(head, DOWN, buff=1.5)
        sig = axes.plot(lambda x: 1 / (1 + np.exp(-x)), x_range=[-4, 4],
                        color=YELL, stroke_width=5)
        self.play(Create(axes), run_time=0.6)
        self.play(Create(sig), run_time=0.9)
        self.at(17.9)
        siglab = t("差值过 sigmoid → 0~1 概率", 28, WHITE)
        fit(siglab, 0.95)
        siglab.next_to(axes, DOWN, buff=0.9)
        siglab.set_x(0)
        self.play(type_in(siglab, run_time=0.8))

        # 段3（19.8-30s）：危险边界
        # 台词：但模拟器有危险边界(19.9) 学到的只是标注数据里的偏好(21.7) 奖励模型…(23.98)
        self.at(19.8)
        self.play(FadeOut(VGroup(axes, sig, siglab), shift=UP * 0.03), run_time=0.3)
        warn = boxed("危险边界", 4.0, 1.0, RED, 30, fill=0.15, weight="BOLD")
        warn.next_to(head, DOWN, buff=1.3)
        self.play_scroll_unroll(warn, run_time=1.5)
        self.at(21.7)
        l1 = t("偏爱长答案 → 觉得越长越好", 27, WHITE)
        l1.next_to(warn, DOWN, buff=0.9)
        self.play(type_in(l1, run_time=1.0))
        self.at(22.3)
        l2 = t("偏爱礼貌 → 觉得越客气越可靠", 27, WHITE)
        l2.next_to(l1, DOWN, buff=0.8)
        self.play(type_in(l2, run_time=1.0))
        self.at(23.8)
        self.play(FadeOut(VGroup(l1, l2), shift=UP * 0.03), run_time=0.3)
        concl = t("奖励模型是偏好的压缩，不是事实裁判", 29, YELL, "BOLD")
        fit(concl, 0.95)
        concl.next_to(warn, DOWN, buff=1.1)
        self.at(23.9)
        self.play(type_in(concl, run_time=1.1))
        self.pad_to_voice()




# ---------------- S6 策略更新 + KL 约束 ----------------
class S6(_Base):
    def construct(self):
        self.bg()
        self.footer()
        head = t("策略更新：加一道 KL 约束", 38, YELL, "BOLD").to_edge(UP, buff=1.2)
        self.play(type_in(head, run_time=1.1))

        # 段1（0-12s）：闭环流程：策略生成→奖励打分→调整策略（圆形节点 + 弧线箭头）
        # cnode/edge_pt/arc_curve 来自 manim_helpers（贝塞尔弧线不穿圆，箭头尖贴圆周）
        self.at(2.232)
        ctr = np.array([0.0, 1.35, 0.0])
        R = 2.0
        pa_pos = ctr + R * np.array([0.0, 1.0, 0.0])                            # 调整策略（顶）
        pg_pos = ctr + R * np.array([np.cos(7 * np.pi / 6), np.sin(7 * np.pi / 6), 0.0])   # 策略生成（左下）
        ps_pos = ctr + R * np.array([np.cos(11 * np.pi / 6), np.sin(11 * np.pi / 6), 0.0])  # 奖励打分（右下）
        g = cnode("策略生成", CYAN).move_to(pg_pos)
        s = cnode("奖励打分", GREEN).move_to(ps_pos)
        a = cnode("调整策略", YELL).move_to(pa_pos)
        self.play(FadeIn(g, shift=DOWN * 0.05), FadeIn(s, shift=DOWN * 0.05),
                  FadeIn(a, shift=DOWN * 0.05), run_time=0.6)
        self.at(4.0)
        # 弧线箭头（外凸，不穿圆，箭头尖端贴圆周）：底部 策略→奖励、右侧 奖励→调整、左侧 调整→策略
        ar1 = arc_curve(pg_pos, -50 * DEGREES, ps_pos, -130 * DEGREES, (0.55, -0.35), (-0.55, -0.35))
        ar2 = arc_curve(ps_pos, 20 * DEGREES, pa_pos, -45 * DEGREES, (0.4, 0.5), (0.35, -0.2))
        ar3 = arc_curve(pa_pos, -135 * DEGREES, pg_pos, 150 * DEGREES, (-0.35, -0.2), (-0.4, 0.5))
        self.play(Create(ar1), run_time=0.6)
        self.play(Create(ar2), Create(ar3), run_time=0.6)
        self.at(6.429)
        self.play(a[0].animate.set_fill_opacity(0.45), run_time=0.4)
        high = t("让高奖励回答更容易出现", 24, WHITE)
        fit(high, 0.95)
        high.move_to(np.array([0.0, 1.7, 0.0]))
        self.play(type_in(high, run_time=0.8))

        # 段2（9.6-18s）：只看奖励走极端 → 红叉
        # 台词：但只看奖励(9.71) 模型会走极端(12.53) 堆礼貌…骗分(14.63)
        self.at(9.6)
        self.play(FadeOut(VGroup(g, s, a, ar1, ar2, ar3, high), shift=UP * 0.03), run_time=0.3)
        extreme = boxed("只看奖励 → 走极端", 5.4, 1.1, RED, 30, fill=0.15, weight="BOLD")
        extreme.next_to(head, DOWN, buff=1.3)
        self.at(9.8)
        self.play_scroll_unroll(extreme, run_time=1.5)
        # 骗分手段逐条出现
        self.at(14.165)
        cheat = VGroup()
        for i, (txt, col) in enumerate((("重复套话", RED), ("堆礼貌", RED), ("像好答案的格式", RED))):
            c = t(txt, 26, col, "BOLD").next_to(extreme, DOWN, buff=0.9 + i * 0.7)
            cheat.add(c)
        self.play(*[type_in(c, run_time=0.8) for c in cheat], run_time=0.8)
        self.at(16.851)
        s6_cross = self.play_red_cross(extreme)

        # 段3（18-30s）：KL 双分布约束
        # 19.527, 21.461, 23.119, 24.813, 26.742
        self.at(19.527)
        self.play(FadeOut(VGroup(extreme, cheat, s6_cross), shift=UP * 0.03), run_time=0.3)
        kl = boxed("加一道 KL 约束：别离参考太远", 6.0, 1.1, CYAN, 27, fill=0.2, weight="BOLD")
        kl.next_to(head, DOWN, buff=1.3)
        self.play_scroll_unroll(kl, run_time=1.5)
        # 双分布：参考模型(灰) 与 策略(黄) 分开，KL 拉回策略分布
        self.at(21.461)
        base_curve = gaussian_curve(center=-0.7, spread=0.7, amp=1.6, color=MUTED)
        pol_curve = gaussian_curve(center=0.7, spread=0.8, amp=1.5, color=YELL)
        dist = VGroup(base_curve, pol_curve).next_to(kl, DOWN, buff=1.1)
        bl = t("参考模型分布", 20, MUTED).next_to(base_curve.get_top(), UP, buff=0.2)
        pl = t("策略分布", 20, YELL, "BOLD").next_to(pol_curve.get_top(), UP, buff=0.2)
        self.play(Create(base_curve), type_in(bl, run_time=1.0), run_time=1.0)
        self.play(Create(pol_curve), type_in(pl, run_time=1.0), run_time=1.0)
        self.at(23.3)
        pull = Arrow(pol_curve.get_top(), base_curve.get_top(), color=YELL, buff=0.1, stroke_width=5)
        pull_lab = t("KL 拉回，别跑太远", 24, YELL, "BOLD").next_to(pull, RIGHT, buff=0.35)
        self.play(Create(pull), type_in(pull_lab, run_time=0.8), run_time=0.8)
        self.at(25.5)
        goal = t("max 奖励 − β·KL", 32, WHITE, "BOLD")
        fit(goal, 0.95)
        goal.next_to(dist, DOWN, buff=1.3)
        self.play(type_in(goal, run_time=0.8))

        # 段4（27.2-38.8s）：β 权衡 + 教练类比
        # 台词：β太小骗分走偏(27.21) 教练(31.21) 记住(34.14) 别把原模型推太远(35.16)
        self.at(27.2)
        self.play(FadeOut(VGroup(kl, base_curve, pol_curve, bl, pl, pull, pull_lab, goal), shift=UP * 0.03), run_time=0.3)
        beta = t("β 太小骗分走偏，太大不敢改变", 28, YELL, "BOLD")
        fit(beta, 0.95)
        beta.next_to(head, DOWN, buff=1.3)
        self.at(27.3)
        self.play(type_in(beta, run_time=1.0))
        self.at(31.3)
        coach = boxed("像教练：不允许为拿分改规则", 5.6, 1.2, WHITE, 27, fill=0.12, weight="BOLD")
        coach.next_to(beta, DOWN, buff=1.2)
        self.play_scroll_unroll(coach, run_time=1.5)
        self.at(34.2)
        remember = t("别推太远，再沿奖励方向调整", 29, GREEN, "BOLD")
        fit(remember, 0.95)
        remember.next_to(coach, DOWN, buff=1.1)
        self.play(type_in(remember, run_time=1.1))
        self.pad_to_voice()


# ---------------- S7 概念实验：三答案 + 奖励黑客 ----------------
class S7(_Base):
    def construct(self):
        self.bg()
        self.footer()
        head = t("示意实验：还是三个回答", 38, YELL, "BOLD").to_edge(UP, buff=1.2)
        self.play(type_in(head, run_time=1.1))

        # 段1（0-14s）：三候选 A/B/C
        # pauses: 1.367, 2.758, 4.834, 8.716
        self.at(1.367)
        CARD_W = 5.6
        a = _card("A · 准确，但句子很短", CARD_W, 0.95, CYAN, WHITE, 26, CARD_FILL, "NORMAL")
        b = _card("B · 流畅，却说成「沿梯度上升」", CARD_W, 0.95, CYAN, WHITE, 26, CARD_FILL, "NORMAL")
        c = _card("C · 谨慎，几乎没回答", CARD_W, 0.95, CYAN, WHITE, 26, CARD_FILL, "NORMAL")
        rows = VGroup(a, b, c).arrange(DOWN, buff=0.6, aligned_edge=LEFT).next_to(head, DOWN, buff=1.3)
        self.play_scroll_unroll(a, run_time=1.2)
        self.at(2.758)
        self.play_scroll_unroll(b, run_time=1.2)
        self.at(4.834)
        self.play_scroll_unroll(c, run_time=1.2)
        # 标红 B 的错误（红色 ✗ 标记 + 下方短说明，不触边）
        self.at(8.716)
        err_mark = self.play_mark("✗", b, RED)
        err = t("B 把「沿梯度上升」说反了", 26, RED, "BOLD")
        fit(err, 0.9)
        err.next_to(rows.get_bottom(), DOWN, buff=0.7)
        self.play(type_in(err, run_time=0.8))

        # 段2（14-24s）：排序动画
        # 11.064, 14.084, 16.504, 18.461, 19.87
        self.at(11.064)
        self.play(FadeOut(VGroup(rows, err, err_mark), shift=UP * 0.03), run_time=0.3)
        lab = t("看重事实 → 怎么排？", 30, WHITE).next_to(head, DOWN, buff=1.4)
        self.play(type_in(lab, run_time=0.8))
        # 排序条：A > B > C（事实）
        self.at(14.084)
        fact_bars = VGroup()
        for w, v, col in ((2.6, "A 事实最对", GREEN), (1.6, "B 说反了", CYAN), (0.8, "C 没答", MUTED)):
            bar = Rectangle(width=w, height=0.7, color=col, fill_color=col, fill_opacity=0.7)
            val = t(v, 22, col, "BOLD").next_to(bar, LEFT, buff=0.3)
            fact_bars.add(VGroup(bar, val))
        fact_bars.arrange(DOWN, buff=0.5).next_to(lab, DOWN, buff=1.2)
        # 三条并行生长（逐条播放会与换页交叉）
        self.play(*[GrowFromEdge(bg[0], LEFT, run_time=0.6) for bg in fact_bars],
                  *[type_in(bg[1], run_time=0.6) for bg in fact_bars], run_time=0.6)
        # 台词：看重表达(14.42) 好不是固定分数(16.86)
        self.at(14.7)
        self.play(FadeOut(VGroup(lab, fact_bars), shift=UP * 0.03), run_time=0.3)
        lab2 = t("看重表达 → 反过来了", 30, WHITE).next_to(head, DOWN, buff=1.4)
        self.play(type_in(lab2, run_time=0.8))
        self.at(16.3)
        expr_bars = VGroup()
        for w, v, col in ((2.4, "B 更像好答案", GREEN), (1.8, "A 太短", CYAN), (0.8, "C 拒答", MUTED)):
            bar = Rectangle(width=w, height=0.7, color=col, fill_color=col, fill_opacity=0.7)
            val = t(v, 22, col, "BOLD").next_to(bar, LEFT, buff=0.3)
            expr_bars.add(VGroup(bar, val))
        expr_bars.arrange(DOWN, buff=0.5).next_to(lab2, DOWN, buff=1.2)
        self.play(*[GrowFromEdge(bg[0], LEFT, run_time=0.6) for bg in expr_bars],
                  *[type_in(bg[1], run_time=0.6) for bg in expr_bars], run_time=0.6)
        self.at(16.9)
        self.play(FadeOut(VGroup(lab2, expr_bars), shift=UP * 0.03), run_time=0.3)
        notfixed = t("「好」不是固定分数", 32, YELL, "BOLD")
        fit(notfixed, 0.95)
        notfixed.next_to(head, DOWN, buff=1.5)
        self.at(17.3)
        self.play(type_in(notfixed, run_time=1.0))

        # 段3（20.3-34.6s）：错误捷径 → 奖励黑客越界
        # 台词：更麻烦的是(19.0) 奖励模型可能学到错误捷径(19.96) 长答案得分高(22.74)
        self.at(20.15)
        self.play(FadeOut(notfixed, shift=UP * 0.03), run_time=0.3)
        shortcuts = t("奖励模型可能学到错误捷径", 30, RED, "BOLD")
        fit(shortcuts, 0.95)
        shortcuts.next_to(head, DOWN, buff=1.4)
        self.at(20.5)  # FadeOut(20.45) 完成后才入场，不与前页标题交叉
        self.play(type_in(shortcuts, run_time=1.0))
        # 三条捷径（台词：长答案得分高22.74、礼貌得分高25.37、拒答更安全27.45）
        self.at(22.8)
        sc1 = t("长答案得分高 → 无限扩写", 26, WHITE).next_to(shortcuts, DOWN, buff=1.0)
        sc2 = t("礼貌得分高 → 堆客套", 26, WHITE).next_to(sc1, DOWN, buff=0.7)
        sc3 = t("拒答更安全 → 普通问题也回避", 26, WHITE).next_to(sc2, DOWN, buff=0.7)
        self.play(type_in(sc1, run_time=0.8))
        self.at(24.9)
        self.play(type_in(sc2, run_time=0.8))
        self.at(27.0)
        self.play(type_in(sc3, run_time=0.8))
        # 越界：突破一条红线（shortcuts 一并带走，否则与边界线/标签重叠）
        self.at(30.089)
        self.play(FadeOut(VGroup(shortcuts, sc1, sc2, sc3), shift=UP * 0.03), run_time=0.3)
        boundary = Line(LEFT * 3.2, RIGHT * 3.2, color=RED, stroke_width=5).next_to(head, DOWN, buff=2.6)
        b_lab = t("边界：别只顾表面特征", 24, RED, "BOLD").next_to(boundary, UP, buff=0.4)
        self.play(Create(boundary), type_in(b_lab, run_time=0.7), run_time=0.7)
        self.at(32.633)
        over = t("越界 → 奖励黑客的入口", 32, YELL, "BOLD")
        fit(over, 0.95)
        over.next_to(boundary, DOWN, buff=1.2)
        self.play(type_in(over, run_time=1.0))
        self.pad_to_voice()


# ---------------- S8 结尾三句话 + 品牌尾卡 ----------------
class S8(_Base):
    def construct(self):
        self.bg()
        self.footer()
        head = t("把这篇压成三句话", 38, YELL, "BOLD").to_edge(UP, buff=1.2)
        self.play(type_in(head, run_time=1.1))

        # ---- 三句话（SFT/RLHF/奖励）----
        # 台词：现在压成三句话(0.66) SFT(2.44) RLHF(5.1) 奖励(10.0)
        self.at(1.78)
        l1 = _card("SFT：教模型按指令回答", 6.2, 1.0, GREEN, GREEN, 27, CARD_FILL, "BOLD")
        l2 = _card("RLHF：用人类偏好，教它在多个回答里选更好", 6.2, 1.0, YELL, YELL, 27, CARD_FILL, "BOLD")
        l3 = _card("奖励：不是事实本身", 6.2, 1.0, RED, RED, 27, CARD_FILL, "BOLD")
        tri = VGroup(l1, l2, l3).arrange(DOWN, buff=0.6, aligned_edge=LEFT).next_to(head, DOWN, buff=1.3)
        self.play_scroll_unroll(l1, run_time=1.4)
        self.at(4.445)
        self.play_scroll_unroll(l2, run_time=1.4)
        self.at(10.0)
        self.play_scroll_unroll(l3, run_time=1.4)

        # ---- 过渡：既然只是偏好的压缩，模型就可能钻空子（台词 12.53~15.9）----
        self.at(12.8)
        self.play(FadeOut(tri, shift=UP * 0.03), run_time=0.3)
        expt = t("既然只是偏好的压缩，模型就可能钻空子", 27, MUTED)
        fit(expt, 0.9)
        expt.next_to(head, DOWN, buff=1.3)
        self.at(12.9)
        self.play(type_in(expt, run_time=1.0))

        # ---- PPO / GRPO / RLVR 预告（台词 16.8~28）----
        self.at(16.8)
        self.play(FadeOut(expt, shift=UP * 0.03), run_time=0.3)
        ppo = t("下一篇：PPO 怎么更新策略", 30, YELL, "BOLD")
        fit(ppo, 0.95)
        ppo.next_to(head, DOWN, buff=1.3)
        self.at(20.4)
        self.play(type_in(ppo, run_time=1.0))
        self.at(24.9)
        more = t("再往后：GRPO 接棒 · RLVR 让答案接受结果检验", 25, CYAN, "BOLD")
        fit(more, 0.95)
        more.next_to(ppo, DOWN, buff=1.1)
        self.play(type_in(more, run_time=1.0))

        # ---- 品牌尾卡 + 互动（台词 28.1~36）----
        self.at(28.0)
        self.play(FadeOut(VGroup(ppo, more), shift=UP * 0.03), run_time=0.3)
        logo = ImageMobject("avatar-sjai-round.png")
        logo.scale_to_fit_width(1.8)
        logo.next_to(head, DOWN, buff=1.0)
        self.at(28.1)
        self.play(FadeIn(logo, shift=DOWN * 0.05), run_time=0.7)
        self.at(29.2)
        follow = t("关注「数解AI」", 36, YELL, "BOLD").next_to(logo, DOWN, buff=0.4)
        self.play(type_in(follow, run_time=1.0))
        self.at(31.8)
        title = t("《RLHF怎么让模型选出好回答？》", 24, WHITE, "BOLD")
        fit(title, 0.85)
        title.next_to(follow, DOWN, buff=0.5)
        self.play(type_in(title, run_time=1.0))
        # 尾部互动（32.9~36，简洁）
        self.at(32.9)
        cta1 = _card("👍 点赞", 1.9, 0.7, YELL, YELL, 20, CARD_FILL, "BOLD")
        cta2 = _card("➕ 关注", 1.9, 0.7, CYAN, CYAN, 20, CARD_FILL, "BOLD")
        cta3 = _card("💬 评论", 1.9, 0.7, GREEN, GREEN, 20, CARD_FILL, "BOLD")
        ctas = VGroup(cta1, cta2, cta3).arrange(RIGHT, buff=0.3).next_to(title, DOWN, buff=0.5)
        fit(ctas, 0.9)
        link = t("查看公众号文章 · 系列合集", 22, GREEN, "BOLD").next_to(ctas, DOWN, buff=0.4)
        fit(link, 0.85)
        ask = t("开头那三个回答，你会怎么排序？评论区聊聊", 21, MUTED).next_to(link, DOWN, buff=0.4)
        fit(ask, 0.85)
        self.play(FadeIn(ctas, shift=DOWN * 0.05), run_time=0.4)
        self.play(type_in(link, run_time=0.8), type_in(ask, run_time=1.0), run_time=1.0)
        self.pad_to_voice()


# ---------------- 封面帧 ----------------
class Cover(Scene):
    """封面帧：系列标签 + 主/副标题 + 三回答视觉 + 品牌。
    渲染：python3 -m manim render -qm -s --disable_caching scenes.py Cover
    关键内容须落在 3:4 安全区（frame y ∈ [-5.33, +5.33]），上下 12.5% 只放装饰。
    """
    def construct(self):
        logo = ImageMobject("avatar-sjai-round.png")
        logo.scale_to_fit_width(1.7)
        logo.to_edge(DOWN, buff=2.15)

        series = t("大模型原理 · 第 9 篇", 26, CYAN).to_edge(UP, buff=2.2)
        title = t("RLHF：怎么让模型选出好回答？", 38, YELL, "BOLD")
        title.set_width(config.frame_width * 0.82)
        title.next_to(series, DOWN, buff=0.5)
        subtitle = t("三个回答 · 人类偏好 · 奖励模型 · 选择更好", 26, WHITE)
        fit(subtitle, 0.9)
        subtitle.next_to(title, DOWN, buff=0.45)

        # 三回答视觉（最有记忆点）+ 状态徽章
        a = boxed("A 准确但生硬", 4.0, 0.9, WHITE, 24, fill=0.12, weight="BOLD")
        b = boxed("B 流畅但说反了", 4.0, 0.9, WHITE, 24, fill=0.12, weight="BOLD")
        c = boxed("C 安全但拒答", 4.0, 0.9, WHITE, 24, fill=0.12, weight="BOLD")
        trio = VGroup(a, b, c).arrange(DOWN, buff=0.5).next_to(subtitle, DOWN, buff=0.8)
        fit(trio, 0.9)
        arrow = t("→ 只能留一个？", 26, YELL, "BOLD")
        arrow.next_to(trio, DOWN, buff=0.6)
        fit(arrow, 0.9)
        sel = t("人凭常识，模型靠 RLHF 教它选", 26, GREEN, "BOLD")
        fit(sel, 0.9)
        sel.next_to(arrow, DOWN, buff=0.6)

        self.add(logo, series, title, subtitle, trio, arrow, sel)


if __name__ == "__main__":
    pass

