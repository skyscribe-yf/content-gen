#!/usr/bin/env python3
"""RLVR 视频号 Manim 场景。

这一版按整片 layout proposal 重写：每个页面先组装最终稳定状态，再放进
竖屏显示带；动态数字从一开始就锚定在最终位置；页面之间用结构切换，
不复用同一个 mobject 做两个 page 的布局。
"""
from __future__ import annotations

import pathlib
import sys


def _scripts_dir() -> str:
    p = pathlib.Path(__file__).resolve().parent
    for _ in range(6):
        cand = p / "scripts"
        if (cand / "manim_helpers.py").exists():
            return str(cand)
        p = p.parent
    raise RuntimeError("找不到 scripts/manim_helpers.py")


sys.path.insert(0, _scripts_dir())
from manim_helpers import *


PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[3]
IMG_ROOT = pathlib.Path(__file__).resolve().parent / "img"

VOICE_DUR = {
    "S1": 24.811,
    "S2": 18.013,
    "S3": 28.337,
    "S4": 25.768,
    "S5": 25.091,
    "S6": 30.982,
    "S7": 18.655,
    "S8": 20.060,
    "S9": 51.070,
}
TAIL = 2.5


def _img(name: str, width: float) -> ImageMobject:
    image = ImageMobject(str(IMG_ROOT / name))
    image.scale_to_fit_width(width)
    return image


def _fit_text(text: str, size: float = 30, color: str = WHITE, weight: str = "NORMAL"):
    return fit(t(text, size, color, weight), 0.84)


def _row(*mobs, buff: float = 0.28):
    return Group(*mobs).arrange(RIGHT, buff=buff)


def _col(*mobs, buff: float = 0.28, aligned_edge=ORIGIN):
    return Group(*mobs).arrange(DOWN, buff=buff, aligned_edge=aligned_edge)


def _header(text: str):
    """小型章节标签：保留场景识别，给主体让出纵向空间。"""
    return fit(t(text, 31, YELL, "BOLD"), 0.86).to_edge(UP, buff=1.12)


def _placeholder(label: str, size: int, color: str):
    """最终位置占位，不进入场景，只参与 page box 计算。"""
    mob = t(label, size, color, "BOLD")
    mob.set_opacity(0.0)
    return mob


def _page(*mobs, buff: float = 0.55):
    page = page_stack(*mobs, buff=buff)
    layout_page(page)
    return page


def _leaves(mob):
    """Flatten layout-only groups so every rendered child is cleared."""
    children = getattr(mob, "submobjects", ())
    if not children:
        return [mob]
    leaves = []
    for child in children:
        leaves.extend(_leaves(child))
    return leaves


def _clear(scene: _Base, page, *extras, run_time: float = 0.34):
    """清除一个完整页面，并显式带走动态数字/箭头等额外 mobject。

    页面规划组通常没有直接 add 到 Scene；动画播放时，卡片/图片的子组却会
    以独立的顶层 mobject 加进去。只 remove 页面叶子会留下这些顶层父组，
    于是切页时出现「旧页和新页叠在一起」。按叶子交集反查 Scene 顶层组，
    才能把同一批对象完整带走。
    """
    targets = [page, *extras]
    target_ids = set()
    for mob in targets:
        target_ids.add(id(mob))
        target_ids.update(id(leaf) for leaf in _leaves(mob))

    roots = []
    for root in list(scene.mobjects):
        root_ids = {id(root)}
        root_ids.update(id(leaf) for leaf in _leaves(root))
        if root_ids & target_ids:
            roots.append(root)

    if roots:
        scene.play(FadeOut(*roots), run_time=run_time)
        scene.remove(*roots)


class S1(_Base):
    def construct(self):
        self.bg()
        self.footer()
        head = _header("RLVR：只有 0/1 的奖励，怎么学会纠错？")

        steps = [
            boxed("读仓库", 1.18, 0.88, CYAN, 21),
            boxed("改代码", 1.18, 0.88, CYAN, 21),
            boxed("跑测试", 1.18, 0.88, GREEN, 21),
            boxed("看报错", 1.18, 0.88, RED, 21),
            boxed("再改一次", 1.38, 0.88, YELL, 20),
        ]
        route = _row(*steps, buff=0.12)
        route_label = _fit_text("一条行动轨迹", 28, WHITE)
        intro = _fit_text("以 coding agent 的一次修复任务为例", 25, MUTED)
        code_img = _img("03-coding-agent-round.png", 4.25)
        page1 = _page(intro, code_img, route, route_label, buff=0.38)

        self.play(type_in(head, 1.1), type_in(intro, 0.65), run_time=1.1)
        self.at(0.96)
        self.play(FadeIn(code_img, shift=DOWN * 0.05), run_time=0.55)
        self.at(1.55)
        self.play_scroll_unroll(steps[0], run_time=0.48)
        self.at(3.236)
        self.play_scroll_unroll(steps[1], run_time=0.48)
        self.at(4.246)
        self.play_scroll_unroll(steps[2], run_time=0.48)
        self.at(5.083)
        self.play_scroll_unroll(steps[3], run_time=0.48)
        self.at(6.242)
        self.play_scroll_unroll(steps[4], run_time=0.52)
        self.at(6.7)
        self.play(type_in(route_label, 0.45))

        pass_card = boxed("测试通过", 2.35, 1.35, GREEN, 27)
        fail_card = boxed("测试失败", 2.35, 1.35, RED, 27)
        pass_ph = _placeholder("1", 52, GREEN)
        fail_ph = _placeholder("0", 52, RED)
        pass_col = _col(pass_card, pass_ph, buff=0.12)
        fail_col = _col(fail_card, fail_ph, buff=0.12)
        outcome_row = _row(pass_col, fail_col, buff=0.72)
        outcome_title = _fit_text("训练器只收到终点信号", 31, WHITE)
        feedback = boxed("0 / 1  →  反馈整条行动轨迹", 5.75, 1.05, CYAN, 27)
        page2 = _page(outcome_title, outcome_row, feedback, buff=0.62)

        self.at(7.252)
        _clear(self, page1)
        self.play(type_in(outcome_title, 0.9))
        self.at(8.647)
        self.play_scroll_unroll(pass_card, run_time=0.55)
        self.play_scroll_unroll(fail_card, run_time=0.55)
        self.at(10.368)
        pass_num = self.counter_value(0, 1, size=52, color=GREEN, run_time=0.55, anchor=pass_ph)
        self.at(12.138)
        fail_num = self.counter_value(0, 0, size=52, color=RED, run_time=0.22, anchor=fail_ph)
        self.at(13.15)
        self.play_scroll_unroll(feedback, run_time=0.65)

        question = _fit_text("没有老师逐步告诉它哪一步对了，为什么还能学会？", 29, WHITE)
        skill_cards = [
            boxed("拆任务", 1.65, 1.08, CYAN, 25),
            boxed("调工具", 1.65, 1.08, GREEN, 25),
            boxed("反复纠错", 1.9, 1.08, YELL, 23),
        ]
        skill_row = _row(*skill_cards, buff=0.3)
        back_arrow = Arrow(LEFT * 2.4, RIGHT * 2.4, buff=0.0, color=YELL, stroke_width=5)
        back_label = _fit_text("终点信号，反过来影响整条轨迹", 25, CYAN)
        back_line = _col(back_arrow, back_label, buff=0.18)
        skill_hint = boxed("从结果学会过程", 4.9, 0.96, YELL, 27, weight="BOLD")
        page3 = _page(question, skill_row, back_line, skill_hint, buff=0.43)

        self.at(13.809)
        _clear(self, page2, pass_num, fail_num)
        self.play(type_in(question, 0.9))
        self.at(15.72)
        self.play_scroll_unroll(skill_cards[0], run_time=0.48)
        self.at(17.809)
        self.play_scroll_unroll(skill_cards[1], run_time=0.48)
        self.at(19.813)
        self.play_scroll_unroll(skill_cards[2], run_time=0.5)
        # Arrow 不能作为嵌套 Group 整体 FadeIn：Arrow 的线是父对象几何，
        # 只淡入 Group 叶子时会短暂只剩箭头头部。把箭头和文字分别入场，
        # 保证任何中间帧都是完整的「线 + 箭头头部」。
        self.play(
            FadeIn(back_arrow, shift=UP * 0.05),
            type_in(back_label, 0.45),
            run_time=0.45,
        )
        self.play_scroll_unroll(skill_hint, run_time=0.42)

        callout = boxed("RLVR：可验证奖励", 5.6, 1.3, YELL, 34, weight="BOLD")
        callout_hint = _fit_text("只看终点，学习却覆盖整条行动轨迹", 27, MUTED)
        callout_feedback = boxed("奖励从终点回到每一步", 5.55, 0.98, CYAN, 27)
        page4 = _page(callout, callout_hint, callout_feedback, buff=0.62)
        # 上一屏的卡片、反馈箭头和结论按顺序完成后再换页；不使用已经
        # 落后的绝对时间锚点，避免换页时留下正在淡入的箭头子图形。
        _clear(self, page3)
        self.play_scroll_unroll(callout, run_time=0.78)
        self.at(22.364)
        self.play(type_in(callout_hint, 0.8))
        self.at(23.35)
        self.play_scroll_unroll(callout_feedback, run_time=0.6)
        self.emphasize(callout, run_time=0.55)
        self.pad_to_voice()


class S2(_Base):
    def construct(self):
        self.bg()
        self.footer()
        head = _header("RLVR、PPO、GRPO：三兄弟不是一回事")

        reward_label = fit(t("奖励设计层", 24, MUTED), 2.65)
        rlvr = boxed("RLVR\n奖励来源与验证", 2.72, 1.36, YELL, 23, weight="BOLD")
        update_label = fit(t("策略更新层", 24, MUTED), 2.65)
        ppo = boxed("PPO\n策略更新", 1.82, 1.22, CYAN, 22, weight="BOLD")
        grpo = boxed("GRPO\n策略更新", 1.82, 1.22, GREEN, 22, weight="BOLD")
        update_row = _row(ppo, grpo, buff=0.4)
        reward_block = _col(reward_label, rlvr, buff=0.35)
        strategy_block = _col(update_label, update_row, buff=0.35)
        architecture = Group(reward_block, strategy_block).arrange(RIGHT, buff=0.55)
        arrows = VGroup(
            Arrow(rlvr.get_right() + RIGHT * 0.12, update_row.get_left() + LEFT * 0.12,
                  buff=0.16, color=YELL, stroke_width=4),
        )
        family = Group(architecture, arrows)
        bad = boxed("RLVR = GRPO", 4.75, 1.02, RED, 30, weight="BOLD")
        page = _page(family, bad, buff=0.62)

        self.play(type_in(head, 1.1), run_time=1.1)
        self.at(0.8)
        self.play(type_in(reward_label, 0.65))
        self.at(1.837)
        self.play_scroll_unroll(rlvr, run_time=0.65)
        self.at(4.402)
        self.emphasize(rlvr, mode="circumscribe", run_time=0.55)
        self.at(5.764)
        self.play(type_in(update_label, 0.65))
        self.play_scroll_unroll(ppo, run_time=0.58)
        self.at(7.473)
        self.play_scroll_unroll(grpo, run_time=0.58)
        self.at(10.459)
        self.play(Create(arrows), run_time=0.65)
        self.at(13.185)
        self.emphasize(rlvr, run_time=0.55)
        self.at(15.138)
        self.emphasize(grpo, mode="circumscribe", run_time=0.55)
        self.at(16.858)
        self.play_scroll_unroll(bad, run_time=0.65)
        self.play_red_cross(bad, run_time=0.65)
        self.pad_to_voice()


class S3(_Base):
    def construct(self):
        self.bg()
        self.footer()
        head = _header("DeepSeek-R1 的最小闭环")

        generate = cnode("生成", CYAN, 0.82, 23)
        check = cnode("检查", GREEN, 0.82, 23)
        reward = cnode("奖励", YELL, 0.82, 23)
        update = cnode("更新", "#B9A4FF", 0.82, 23)
        # 走一个不交叉的方形闭环：生成 → 检查 → 奖励 → 更新 → 生成。
        # 原先把 reward 放在左下、update 放在右下，却从 reward.get_left()
        # 指向 update.get_right()，箭头横穿节点并与对角线交叉。
        nodes = VGroup(generate, check, update, reward).arrange_in_grid(
            rows=2, cols=2, buff=(1.05, 0.9), cell_alignment=ORIGIN
        )
        arrows = VGroup(
            Arrow(generate.get_right() + RIGHT * 0.1, check.get_left() + LEFT * 0.1,
                  buff=0.14, color=MUTED),
            Arrow(check.get_bottom() + DOWN * 0.1, reward.get_top() + UP * 0.1,
                  buff=0.14, color=MUTED),
            Arrow(reward.get_left() + LEFT * 0.1, update.get_right() + RIGHT * 0.1,
                  buff=0.14, color=MUTED),
            Arrow(update.get_top() + UP * 0.1, generate.get_bottom() + DOWN * 0.1,
                  buff=0.14, color=MUTED),
        )
        flow = Group(nodes, arrows)
        verifier_note = _fit_text("Verifier 只回答：结果满足检查条件吗？", 28, WHITE)
        examples = _row(
            boxed("数学题：对答案", 2.75, 1.08, GREEN, 24),
            boxed("代码题：跑测试", 2.75, 1.08, CYAN, 24),
            buff=0.55,
        )
        page1 = _page(flow, verifier_note, examples, buff=0.58)

        self.play(type_in(head, 1.1), run_time=1.1)
        self.at(0.0)
        self.play(FadeIn(flow, shift=DOWN * 0.05), run_time=0.75)
        self.at(2.583)
        self.play(type_in(verifier_note, 0.85))
        self.at(5.039)
        self.emphasize(check, mode="circumscribe", run_time=0.55)
        self.at(6.753)
        self.play_mark("?", check, YELL, mark_size=36, run_time=0.5)
        self.at(9.077)
        self.play_scroll_unroll(examples[0], run_time=0.52)
        self.at(10.540)
        self.play_scroll_unroll(examples[1], run_time=0.52)

        stat_title = _fit_text("R1-Zero：规则奖励也能推动能力增长", 30, WHITE)
        start_card = boxed("起点\nAIME 2024", 2.5, 1.3, CYAN, 25)
        end_card = boxed("增长后\nAIME 2024", 2.5, 1.3, GREEN, 25)
        start_ph = _placeholder("15.6%", 48, CYAN)
        end_ph = _placeholder("77.9%", 48, GREEN)
        start_col = _col(start_card, start_ph, buff=0.12)
        end_col = _col(end_card, end_ph, buff=0.12)
        rise = Arrow(LEFT * 0.45, RIGHT * 0.45, buff=0, color=YELL, stroke_width=5)
        stat_row = _row(start_col, rise, end_col, buff=0.5)
        reflection = boxed("反思 + 验证", 3.0, 0.98, YELL, 26)
        goal = boxed("提高拿到可验证结果的概率", 5.8, 1.18, YELL, 30, weight="BOLD")
        page2 = _page(stat_title, stat_row, reflection, goal, buff=0.5)

        self.at(12.577)
        _clear(self, page1)
        self.play(type_in(stat_title, 0.85))
        self.at(15.411)
        self.play_scroll_unroll(start_card, run_time=0.58)
        self.at(18.29)
        first = self.counter_value(0, 15.6, suffix="%", decimals=1, size=48,
                                   color=CYAN, run_time=0.72, anchor=start_ph)
        second = self.counter_value(15.6, 77.9, suffix="%", decimals=1, size=48,
                                    color=GREEN, run_time=0.86, anchor=end_ph)
        self.at(21.867)
        self.play_scroll_unroll(reflection, run_time=0.58)
        self.at(24.466)
        self.play_scroll_unroll(goal, run_time=0.72)
        self.at(26.293)
        self.emphasize(goal, mode="circumscribe", run_time=0.75)
        self.pad_to_voice()


class S4(_Base):
    def construct(self):
        self.bg()
        self.footer()
        head = _header("为什么代码奖励会外溢成 Agent 能力？")

        court_img = _img("03-coding-agent-round.png", 4.2)
        metaphor = _row(
            boxed("不看手腕", 1.72, 1.0, CYAN, 23),
            boxed("只看进球", 1.72, 1.0, GREEN, 23),
            boxed("只看终点", 1.72, 1.0, YELL, 23),
            buff=0.25,
        )
        page1 = _page(court_img, metaphor, buff=0.62)

        self.play(type_in(head, 1.1), run_time=1.1)
        self.at(0.0)
        self.play(FadeIn(court_img, shift=DOWN * 0.05), run_time=0.65)
        self.at(3.289)
        self.play_scroll_unroll(metaphor[0], run_time=0.52)
        self.at(4.510)
        self.play_scroll_unroll(metaphor[1], run_time=0.52)
        self.at(5.915)
        self.play_scroll_unroll(metaphor[2], run_time=0.52)

        traj_title = _fit_text("成功轨迹被提高，失败轨迹被压低", 30, WHITE)
        success = boxed("成功轨迹 ↑", 3.0, 1.12, GREEN, 27)
        failure = boxed("失败轨迹 ↓", 3.0, 1.12, RED, 27)
        success_ph = _placeholder("1", 48, GREEN)
        failure_ph = _placeholder("0", 48, RED)
        success_line = _row(success, success_ph, buff=0.24)
        failure_line = _row(failure, failure_ph, buff=0.24)
        trajectory = _col(success_line, failure_line, buff=0.3)
        terminal = boxed("终点奖励", 2.9, 1.02, YELL, 26)
        pass_ph = _placeholder("1", 34, GREEN)
        fail_ph = _placeholder("0", 34, RED)
        terminal_values = _row(pass_ph, fail_ph, buff=0.42)
        terminal_stats = _col(terminal, terminal_values, buff=0.12)
        action_row = _row(
            boxed("先读相关文件", 2.65, 1.0, CYAN, 23),
            boxed("看到报错换假设", 2.65, 1.0, GREEN, 23),
            buff=0.45,
        )
        page2 = _page(traj_title, trajectory, terminal_stats, action_row, buff=0.36)

        self.at(7.648)
        _clear(self, page1)
        self.play(type_in(traj_title, 0.8))
        self.play_scroll_unroll(success, run_time=0.55)
        self.at(9.516)
        success_n = self.counter_value(0, 1, size=48, color=GREEN, run_time=0.55, anchor=success_ph)
        self.play_scroll_unroll(failure, run_time=0.55)
        failure_n = self.counter_value(1, 0, size=48, color=RED, run_time=0.5, anchor=failure_ph)
        self.at(11.572)
        self.play_scroll_unroll(terminal, run_time=0.55)
        pass_n = self.counter_value(0, 1, size=34, color=GREEN, run_time=0.34, anchor=pass_ph)
        fail_n = self.counter_value(1, 0, size=34, color=RED, run_time=0.34, anchor=fail_ph)
        self.at(12.87)
        self.play_scroll_unroll(action_row[0], run_time=0.52)
        self.at(14.604)
        self.play_scroll_unroll(action_row[1], run_time=0.55)

        warning_title = _fit_text("投机步骤也会被一起强化", 31, WHITE)
        power = boxed("RLVR 的力量", 2.65, 1.24, GREEN, 28, weight="BOLD")
        danger = boxed("RLVR 的危险", 2.65, 1.24, RED, 28, weight="BOLD")
        warning = _row(power, danger, buff=0.72)
        warning_hint = boxed("同一条反馈，既能传递能力，也能放大投机", 5.75, 1.02, RED, 24)
        page3 = _page(warning_title, warning, warning_hint, buff=0.58)
        self.at(19.156)
        _clear(self, page2, success_n, failure_n, pass_n, fail_n)
        self.play(type_in(warning_title, 0.8))
        self.at(21.539)
        self.play_scroll_unroll(power, run_time=0.62)
        self.at(23.272)
        self.play_scroll_unroll(danger, run_time=0.62)
        self.play_scroll_unroll(warning_hint, run_time=0.45)
        self.emphasize(danger, mode="wiggle", color=RED, run_time=0.65)
        self.pad_to_voice()


class S5(_Base):
    def construct(self):
        self.bg()
        self.footer()
        head = _header("SWE-RL：证据落在真实软件工程")

        route_img = _img("01-training-route-round.png", 3.05)
        evidence = boxed("把 RL 推进真实软件工程", 3.25, 1.0, CYAN, 23)
        patch = boxed("patch 相似度 → 奖励", 3.25, 1.0, GREEN, 23)
        evidence_col = _col(evidence, patch, buff=0.38)
        upper = _row(route_img, evidence_col, buff=0.42)
        rate = boxed("SWE-bench Verified", 4.8, 1.1, YELL, 27, weight="BOLD")
        rate_ph = _placeholder("41.0%", 54, YELL)
        metric = _col(rate, rate_ph, buff=0.12)
        page1 = _page(upper, metric, buff=0.72)

        self.play(type_in(head, 1.1), run_time=1.1)
        self.at(0.0)
        self.play(FadeIn(route_img, shift=DOWN * 0.05), run_time=0.62)
        self.at(2.022)
        self.play_scroll_unroll(evidence, run_time=0.6)
        self.at(4.605)
        self.play_scroll_unroll(patch, run_time=0.6)
        self.at(7.255)
        self.play_scroll_unroll(rate, run_time=0.62)
        solve = self.counter_value(0, 41.0, suffix="%", decimals=1, size=54,
                                   color=YELL, run_time=0.82, anchor=rate_ph)

        domains_title = _fit_text("只在软件数据上训练，却跨域提升", 31, WHITE)
        domain_cards = [
            boxed("函数编程", 2.05, 1.0, CYAN, 23),
            boxed("库使用", 2.05, 1.0, CYAN, 23),
            boxed("代码推理", 2.05, 1.0, GREEN, 23),
            boxed("数学", 2.05, 1.0, GREEN, 23),
            boxed("语言理解", 2.05, 1.0, YELL, 22),
        ]
        domain_grid = VGroup(*domain_cards).arrange_in_grid(
            rows=2, cols=3, buff=0.3, cell_alignment=LEFT
        )
        baseline = boxed("SFT baseline：反而退化", 5.5, 1.08, RED, 28, weight="BOLD")
        page2 = _page(domains_title, domain_grid, baseline, buff=0.55)
        self.at(8.785)
        _clear(self, page1, solve)
        self.play(type_in(domains_title, 0.82))
        self.at(12.156)
        self.play_scroll_unroll(domain_cards[0], run_time=0.48)
        self.at(13.670)
        self.play_scroll_unroll(domain_cards[1], run_time=0.48)
        self.at(15.585)
        self.play_scroll_unroll(domain_cards[2], run_time=0.48)
        self.at(17.983)
        self.play_scroll_unroll(domain_cards[3], run_time=0.48)
        self.at(20.739)
        self.play_scroll_unroll(domain_cards[4], run_time=0.52)
        self.emphasize(domain_grid, mode="circumscribe", run_time=0.65)
        self.at(23.149)
        self.play_scroll_unroll(baseline, run_time=0.68)
        self.play_red_cross(baseline, run_time=0.65)
        self.pad_to_voice()


class S6(_Base):
    def construct(self):
        self.bg()
        self.footer()
        head = _header("可验证，不等于不可作弊")

        layer1 = boxed("指标表面：堆关键词", 5.8, 1.0, RED, 25)
        layer2 = boxed("环境漏洞：直接改单元测试", 5.8, 1.0, RED, 25)
        layer3 = boxed("Reward tampering：连奖励代码一起改", 5.8, 1.0, RED, 24)
        layers = _col(layer1, layer2, layer3, buff=0.28)
        experiment = boxed("少量样本，也能改写自己的奖励函数", 5.8, 1.0, RED, 25)
        page1 = _page(layers, experiment, buff=0.58)

        self.play(type_in(head, 1.1), run_time=1.1)
        self.at(0.0)
        self.play_scroll_unroll(layer1, run_time=0.55)
        self.at(2.658)
        self.emphasize(layer1, mode="wiggle", color=RED, run_time=0.5)
        self.at(6.922)
        self.play_scroll_unroll(layer2, run_time=0.55)
        self.at(10.847)
        self.emphasize(layer2, mode="wiggle", color=RED, run_time=0.5)
        self.at(13.085)
        self.play_scroll_unroll(layer3, run_time=0.62)
        self.at(14.172)
        self.emphasize(layer3, mode="wiggle", color=RED, run_time=0.5)
        self.at(15.811)
        self.play_scroll_unroll(experiment, run_time=0.62)
        self.at(18.337)
        self.emphasize(experiment, mode="circumscribe", run_time=0.65)

        compare_title = _fit_text("真正的对比：两种偏差方式不同", 31, WHITE)
        neural = boxed("神经网络奖励", 2.65, 1.22, CYAN, 27)
        rules = boxed("规则奖励", 2.65, 1.22, GREEN, 27)
        compare_row = _row(neural, rules, buff=0.82)
        false_claim = boxed("规则就不会被攻击？", 5.5, 0.98, RED, 27)
        contrast = boxed("都要把 verifier 当成系统边界", 5.7, 1.18, YELL, 29, weight="BOLD")
        page2 = _page(compare_title, compare_row, false_claim, contrast, buff=0.5)
        self.at(19.511)
        _clear(self, page1)
        self.play(type_in(compare_title, 0.8))
        self.play_scroll_unroll(neural, run_time=0.55)
        self.play_scroll_unroll(rules, run_time=0.55)
        self.at(22.967)
        self.play_scroll_unroll(false_claim, run_time=0.58)
        self.play_red_cross(false_claim, run_time=0.65)
        self.at(25.299)
        self.play_scroll_unroll(contrast, run_time=0.72)
        self.at(29.182)
        self.emphasize(contrast, mode="circumscribe", run_time=0.72)
        self.pad_to_voice()


class S7(_Base):
    def construct(self):
        self.bg()
        self.footer()
        head = _header("防线不能只改一个分数函数")
        intro = _fit_text("四层防线，把 verifier 当成系统边界", 29, WHITE)
        target = boxed("目标层｜明确成功条件", 5.75, 0.98, YELL, 24)
        env = boxed("环境层｜沙箱 · 只读测试 · 最小权限", 5.75, 0.98, CYAN, 22)
        evaluate = boxed("评估层｜多测试集 · 独立 verifier", 5.75, 0.98, GREEN, 22)
        audit = boxed("审计层｜行为日志 · 人工抽检", 5.75, 0.98, "#B9A4FF", 23)
        tower = _col(target, env, evaluate, audit, buff=0.2)
        boundary = boxed("verifier 是系统边界", 5.75, 1.18, YELL, 31, weight="BOLD")
        page = _page(intro, tower, boundary, buff=0.48)

        self.play(type_in(head, 1.1), run_time=1.1)
        self.at(0.0)
        self.play(type_in(intro, 0.72))
        self.at(2.723)
        self.play_scroll_unroll(target, run_time=1.10)
        self.at(4.565)
        self.play_scroll_unroll(env, run_time=0.85)
        self.at(8.356)
        self.play_scroll_unroll(evaluate, run_time=0.75)
        self.at(10.835)
        self.play_scroll_unroll(audit, run_time=0.75)
        self.at(13.890)
        self.play_scroll_unroll(boundary, run_time=0.90)
        self.at(17.065)
        self.emphasize(boundary, mode="circumscribe", run_time=0.75)
        self.pad_to_voice()


def _lane(label: str, color: str, end_label: str, note: str, dense: bool = False):
    start = boxed(label, 1.75, 0.98, color, 24, weight="BOLD")
    end = boxed(end_label, 1.55, 0.98, color, 24, weight="BOLD")
    if dense:
        middle = VGroup(*[Dot(radius=0.11, color=color) for _ in range(4)]).arrange(RIGHT, buff=0.38)
        line = Line(LEFT * 1.0, RIGHT * 1.0, color=color, stroke_width=4)
        middle = Group(line, middle)
    else:
        middle = Arrow(LEFT * 1.12, RIGHT * 1.12, buff=0.0, color=color, stroke_width=4)
    row = Group(start, middle, end).arrange(RIGHT, buff=0.28)
    note_mob = _fit_text(note, 23, color)
    return _col(row, note_mob, buff=0.25)


class S8(_Base):
    def construct(self):
        self.bg()
        self.footer()
        head = _header("结果验证 vs 过程验证")
        outcome_lane = _lane("结果验证", CYAN, "终点", "清晰 · 便宜 · 信号稀疏")
        process_lane = _lane("过程验证", GREEN, "终点", "中间推理与工具调用，反馈更密", dense=True)
        warning = boxed("过程 verifier 也必须可靠", 5.75, 1.02, RED, 27, weight="BOLD")
        page = _page(outcome_lane, process_lane, warning, buff=0.62)

        self.play(type_in(head, 1.1), run_time=1.1)
        self.at(0.0)
        self.play_scroll_unroll(outcome_lane[0][0], run_time=0.52)
        self.at(2.714)
        self.play_scroll_unroll(outcome_lane[0][2], run_time=0.52)
        self.at(4.859)
        self.play(type_in(outcome_lane[1], 0.7))
        self.at(7.341)
        self.emphasize(outcome_lane, mode="circumscribe", run_time=0.55)
        self.at(10.732)
        self.play_scroll_unroll(process_lane[0][0], run_time=0.52)
        self.at(11.985)
        self.play_scroll_unroll(process_lane[0][2], run_time=0.52)
        self.at(13.749)
        self.play(type_in(process_lane[1], 0.75))
        self.at(16.479)
        self.play_scroll_unroll(warning, run_time=0.62)
        self.at(18.721)
        self.emphasize(warning, mode="wiggle", color=RED, run_time=0.65)
        self.pad_to_voice()


class S9(_Base):
    def construct(self):
        self.bg()
        self.footer()
        head = _header("三句话，收住 RLVR 这条训练回路")

        one = boxed("1  RLVR 规定奖励如何验证", 5.9, 1.12, CYAN, 27)
        two = boxed("2  PPO / GRPO 规定策略如何更新", 5.9, 1.12, GREEN, 26)
        three = boxed("3  verifier 本身就是系统边界", 5.9, 1.12, YELL, 27, weight="BOLD")
        summary = _col(one, two, three, buff=0.38)
        page1 = _page(summary, buff=0.58)

        self.play(type_in(head, 1.1), run_time=1.1)
        self.at(1.426)
        self.play_scroll_unroll(one, run_time=0.65)
        self.at(4.701)
        self.play_scroll_unroll(two, run_time=0.65)
        self.at(12.187)
        self.play_scroll_unroll(three, run_time=0.65)
        self.at(14.49)
        self.emphasize(three, mode="circumscribe", run_time=0.65)

        like = boxed("点赞 · 收藏", 1.8, 0.96, CYAN, 23)
        follow = boxed("关注「数解AI」", 1.95, 0.96, GREEN, 23)
        article = boxed("公众号同名文章", 1.95, 0.96, YELL, 23)
        social = _row(like, follow, article, buff=0.2)
        next_preview = boxed(
            "下一篇：真实 Agent 环境的权限隔离与安全审计",
            5.8,
            1.12,
            "#B9A4FF",
            23,
        )
        question = boxed(
            "问题：最终测试、过程 verifier，还是人工抽检？",
            5.8,
            1.16,
            RED,
            24,
            weight="BOLD",
        )
        options = _row(
            boxed("最终测试", 1.75, 0.95, CYAN, 22),
            boxed("过程 verifier", 1.95, 0.95, GREEN, 21),
            boxed("人工抽检", 1.75, 0.95, YELL, 22),
            buff=0.18,
        )
        page2 = _page(social, next_preview, question, options, buff=0.42)
        self.at(18.204)
        _clear(self, page1)
        self.play_scroll_unroll(like, run_time=0.52)
        self.at(20.79)
        self.play_scroll_unroll(follow, run_time=0.52)
        self.at(24.701)
        self.play_scroll_unroll(article, run_time=0.52)
        self.at(26.798)
        self.play_scroll_unroll(next_preview, run_time=0.68)
        self.at(37.791)
        self.play_scroll_unroll(question, run_time=0.68)
        self.at(40.9)
        self.play_scroll_unroll(options[0], run_time=0.46)
        self.at(42.382)
        self.play_scroll_unroll(options[1], run_time=0.46)
        self.at(45.08)
        self.play_scroll_unroll(options[2], run_time=0.46)
        self.at(47.367)
        self.emphasize(options[1], mode="circumscribe", run_time=0.55)

        avatar = ImageMobject(str(PROJECT_ROOT / "avatar-sjai-round.png"))
        avatar.scale_to_fit_width(2.6)
        follow_line = _fit_text("关注「数解AI」", 32, YELL, "BOLD")
        title_line = _fit_text("《RLVR：可验证奖励怎么重塑后训练？》", 26, WHITE, "BOLD")
        green_line = _fit_text("查看公众号文章 · 下一篇继续拆解", 24, GREEN)
        page3 = _page(avatar, follow_line, title_line, green_line, buff=0.38)
        self.at(48.514)
        _clear(self, page2, run_time=0.22)
        self.play(FadeIn(avatar, scale=0.9), run_time=0.45)
        self.play(type_in(follow_line, 0.45))
        self.play(type_in(title_line, 0.60))
        self.play(type_in(green_line, 0.45))
        self.pad_to_voice()
