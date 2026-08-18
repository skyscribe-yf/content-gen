#!/usr/bin/env python3
"""《为什么AI上下文越长越慢？两道数学硬墙一次讲透》视频号场景。

所有动作都以本目录 ``tts/sentence-boundaries.json`` 的 clip 为时间锚点。
页面先组装稳定几何，再交给 ``layout_page``；动态数字只进入预留槽位。
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
from manim_helpers import *  # noqa: F401,F403


VOICE_DUR = {
    "S1": 39.353,
    "S2": 36.821,
    "S3": 37.171,
    "S4": 37.277,
    "S5": 38.744,
    "S6": 40.053,
    "S7": 41.264,
    "S8": 43.301,
}
TAIL = 2.5
ASSET_DIR = pathlib.Path(__file__).resolve().parent


def _img(name: str, width: float) -> ImageMobject:
    image = ImageMobject(str(ASSET_DIR / "img" / name))
    image.scale_to_fit_width(width)
    return image


def _arrange_row(*mobs, buff: float = 0.3) -> VGroup:
    return VGroup(*mobs).arrange(RIGHT, buff=buff, aligned_edge=ORIGIN)


class S1(_Base):
    """开场钩子：长任务让 AI 失忆，问题落到两道数学硬墙。"""

    def construct(self):
        self.bg()
        self.footer()
        footer_mob = self.mobjects[-1]
        head = t("AI 程序员的一天", 38, YELL, "BOLD")
        head.to_edge(UP, buff=1.2)

        # Page 1: agent loop and context overflow.
        task = _card("任务：修一个编译器的 bug", 6.3, 1.8, CYAN, WHITE, 32, CARD_FILL, "BOLD")
        c1 = _card("读代码", 1.9, 1.6, CYAN, WHITE, 28, CARD_FILL, "BOLD")
        c2 = _card("跑测试", 1.9, 1.6, GREEN, WHITE, 28, CARD_FILL, "BOLD")
        c3 = _card("改文件", 1.9, 1.6, YELL, WHITE, 28, CARD_FILL, "BOLD")
        loop = VGroup(c1, c2, c3).arrange(RIGHT, buff=0.38)
        loop_lab = t("修 bug 循环", 28, MUTED, "BOLD")
        bar_slot = dynamic_slot(4.5, 0.85)
        step_slot = dynamic_slot(2.1, 0.85)
        metric_row = stable_row(bar_slot, step_slot, buff=0.4, aligned_edge=ORIGIN)
        page1 = page_stack(task, loop_lab, loop, metric_row, buff=0.85)
        layout_page(page1)
        ar1 = Arrow(c1.get_right() + RIGHT * 0.12, c2.get_left() - RIGHT * 0.12,
                    color=MUTED, stroke_width=4, buff=0)
        ar2 = Arrow(c2.get_right() + RIGHT * 0.12, c3.get_left() - RIGHT * 0.12,
                    color=MUTED, stroke_width=4, buff=0)
        bar = Rectangle(width=4.5, height=0.85, color=YELL,
                        fill_color=YELL, fill_opacity=0.85)
        bar.move_to(bar_slot.get_center())

        self.at_clip("s1-c01")
        self.play(type_in(head, run_time=0.9))
        self.at_clip("s1-c02")
        self.play_scroll_unroll(task, run_time=0.8)
        self.at_clip("s1-c03")
        self.play_parallel(type_in(loop_lab, run_time=0.55), FadeIn(loop),
                           Create(ar1), Create(ar2), run_time=0.7)
        self.at_clip("s1-c04")
        tracker = ValueTracker(0)
        self.grow_bar(bar, tracker, 4.5, run_time=0.65)
        overflow = t("上下文满了", 34, RED, "BOLD")
        self.at_clip("s1-c05")
        self.play(type_in(overflow, run_time=0.65))
        # Keep the actual metric in the stable slot; the red label is a local beat.
        self.at_clip("s1-c06")
        step = self.counter_value(0, 200, suffix=" 步", size=46,
                                  color=YELL, anchor=step_slot, run_time=0.65)
        self.at_clip("s1-c07")
        cross = self.play_red_cross(bar, run_time=0.65)
        self.wait(0.07)
        self.play(FadeOut(Group(task, loop_lab, loop, ar1, ar2, bar, step, cross, overflow),
                          shift=UP * 0.03), run_time=0.25)

        # Page 2: benchmark and baseline score.
        notjoke = t("这不是段子", 68, YELL, "BOLD")
        fit(notjoke, 0.86)
        swe = t("SWE-Marathon", 50, CYAN, "BOLD")
        fit(swe, 0.86)
        desc = t("专门测 AI 程序员超长任务的基准", 34, WHITE)
        fit(desc, 0.86)
        baseline = t("GLM-5.1", 32, MUTED, "BOLD")
        score_slot = dynamic_slot(2.3, 1.3)
        full = t("满分 100", 32, MUTED)
        score_row = stable_row(baseline, score_slot, full, buff=0.42)
        page2 = page_stack(notjoke, swe, desc, score_row, buff=1.35)
        layout_page(page2)

        self.at_clip("s1-c08")
        self.play(type_in(notjoke, run_time=0.8))
        self.at_clip("s1-c09")
        self.play(type_in(swe, run_time=0.65))
        self.at_clip("s1-c10")
        self.play(type_in(desc, run_time=0.85))
        self.at_clip("s1-c11")
        score1 = self.counter_value(0, 1.0, decimals=1, size=58,
                                    color=MUTED, anchor=score_slot, run_time=0.65,
                                    extra_anims=[type_in(baseline, run_time=0.5)])
        self.at_clip("s1-c12")
        self.play(type_in(full, run_time=0.5))
        self.wait(0.07)
        self.play(FadeOut(Group(notjoke, swe, desc, baseline, score1, full),
                          shift=UP * 0.03), run_time=0.25)

        # Page 3: the short-memory explanation.
        notsmart = t("不是它不聪明", 58, WHITE, "BOLD")
        fit(notsmart, 0.86)
        mem_label = t("记忆只有", 34, WHITE)
        mem_slot = dynamic_slot(2.8, 1.2)
        mem_row = stable_row(mem_label, mem_slot, buff=0.35)
        cant = t("撑不到任务结束", 54, RED, "BOLD")
        fit(cant, 0.86)
        note = t("20 万字 = 200K tokens", 28, MUTED)
        page3 = page_stack(notsmart, mem_row, cant, note, buff=1.4)
        layout_page(page3)

        self.at_clip("s1-c13")
        self.play(type_in(notsmart, run_time=0.65))
        self.at_clip("s1-c14")
        mem20 = self.counter_value(0, 20, suffix=" 万字", size=50,
                                   color=YELL, anchor=mem_slot, run_time=0.65,
                                   extra_anims=[type_in(mem_label, run_time=0.5)])
        self.at_clip("s1-c15")
        self.play(type_in(cant, run_time=0.7))
        self.wait(0.07)
        self.play(FadeOut(Group(notsmart, mem_label, mem20, cant, note),
                          shift=UP * 0.25), run_time=0.25)

        # Page 4: expanded memory, score jump, and the two walls.
        g52 = t("GLM-5.2 把记忆扩到", 32, WHITE)
        mem100_slot = dynamic_slot(3.0, 1.15)
        mem100_row = stable_row(g52, mem100_slot, buff=0.3)
        score_label = t("得分跳到", 32, WHITE)
        score13_slot = dynamic_slot(2.9, 1.25)
        score13_row = stable_row(score_label, score13_slot, buff=0.3)
        pct_slot = dynamic_slot(2.8, 1.0)
        why = t("为什么干到一半会失忆？", 46, YELL, "BOLD")
        fit(why, 0.86)
        wall1 = _card("墙一：计算 O(T²)", 3.65, 1.65, CYAN, WHITE, 28, CARD_FILL, "BOLD")
        wall2 = _card("墙二：存储 KV cache", 3.65, 1.65, CYAN, WHITE, 28, CARD_FILL, "BOLD")
        walls = VGroup(wall1, wall2).arrange(RIGHT, buff=0.35)
        pct_row = stable_row(t("提升", 30, WHITE), pct_slot, buff=0.25)
        page4 = page_stack(mem100_row, score13_row, pct_row, why, walls, buff=0.62)
        layout_page(page4)

        self.at_clip("s1-c16")
        mem100 = self.counter_value(0, 100, suffix=" 万字", size=50,
                                    color=YELL, anchor=mem100_slot, run_time=0.7,
                                    extra_anims=[type_in(g52, run_time=0.6)])
        self.at_clip("s1-c17")
        score13 = self.counter_value(0, 13.0, decimals=1, size=62,
                                     color=YELL, anchor=score13_slot, run_time=0.6,
                                     extra_anims=[type_in(score_label, run_time=0.45)])
        self.wait(0.07)
        pct = self.counter_value(0, 1200, suffix="%", size=48,
                                 color=YELL, anchor=pct_slot, run_time=0.55,
                                 extra_anims=[type_in(pct_row[0], run_time=0.45)])
        self.at_clip("s1-c18")
        self.play(type_in(why, run_time=0.75))
        self.at_clip("s1-c19")
        self.play(FadeIn(walls), run_time=0.55)
        self.at_clip("s1-c20")
        self.play(type_in(t("是", 40, WHITE, "BOLD"), run_time=0.45))
        self.at_clip("s1-c21")
        self.play(FadeOut(Group(head, footer_mob, g52, mem100, score_label, score13,
                                 pct_row, pct, why, walls), shift=RIGHT * 0.1 + DOWN * 0.03),
                  run_time=0.5)
        self.pad_to_voice()


class S2(_Base):
    """第一道墙：注意力中的全连接让计算量按 O(T²) 增长。"""

    def construct(self):
        self.bg()
        self.footer()
        footer_mob = self.mobjects[-1]
        head = t("第一道墙：握手爆炸", 38, YELL, "BOLD")
        head.to_edge(UP, buff=1.2)

        # Page 1: the meeting-room intuition.
        definition = t("AI 的「记忆」就是注意力", 34, WHITE, "BOLD")
        fit(definition, 0.86)
        image = _img("handshake-round.png", 4.8)
        caption = t("每个词都回头看之前所有的词", 30, CYAN, "BOLD")
        fit(caption, 0.86)
        page1 = page_stack(definition, image, caption, buff=0.9)
        layout_page(page1)

        self.at_clip("s2-c01")
        self.play(type_in(head, run_time=0.85))
        self.at_clip("s2-c02")
        self.play(type_in(definition, run_time=0.9))
        self.at_clip("s2-c03")
        self.play_parallel(FadeIn(image, shift=DOWN * 0.05), type_in(caption, run_time=0.6),
                           run_time=0.7)
        self.play(FadeOut(Group(definition, image, caption), shift=UP * 0.03), run_time=0.25)

        # Page 2: 10 people and 45 handshakes, then the 100-person explosion.
        label10 = t("10 个人开会", 42, WHITE, "BOLD")
        points10 = VGroup(*[Dot(radius=0.13, color=CYAN) for _ in range(10)])
        for index, point in enumerate(points10):
            angle = 2 * PI * index / 10 - PI / 2
            point.move_to(1.75 * np.array([np.cos(angle), np.sin(angle), 0]))
        count_label = t("一共", 30, WHITE)
        count_slot = dynamic_slot(2.7, 1.1)
        count_row = stable_row(count_label, count_slot, buff=0.3)
        relation = t("每个人都要和其他人握手", 28, MUTED)
        page2 = page_stack(label10, relation, points10, count_row, buff=0.85)
        layout_page(page2)
        lines10 = VGroup(*[
            Line(points10[i].get_center(), points10[j].get_center(),
                 color=MUTED, stroke_width=2.0)
            for i in range(10) for j in range(i + 1, 10)
        ])

        self.at_clip("s2-c04")
        self.play(type_in(label10, run_time=0.65))
        self.at_clip("s2-c05")
        self.play_parallel(FadeIn(points10, shift=DOWN * 0.05), Create(lines10),
                           type_in(relation, run_time=0.65), run_time=0.85)
        self.at_clip("s2-c06")
        count45 = self.counter_value(0, 45, suffix=" 次", size=54,
                                     color=YELL, anchor=count_slot, run_time=0.65,
                                     extra_anims=[type_in(count_label, run_time=0.45)])
        self.wait(0.07)
        self.play(FadeOut(Group(label10, relation, points10, lines10, count_label, count45),
                          shift=UP * 0.03), run_time=0.25)

        # Page 2b: dense graph for the 100-person case.
        label100 = t("100 个人开会？", 50, YELL, "BOLD")
        fit(label100, 0.86)
        hub = Circle(radius=2.25, color=MUTED, stroke_width=2.5)
        dense_points = VGroup(*[
            Dot(2.2 * np.array([np.cos(2 * PI * i / 18), np.sin(2 * PI * i / 18), 0]),
                radius=0.1, color=CYAN)
            for i in range(18)
        ])
        dense_lines = VGroup(*[
            Line(dense_points[i].get_center(), dense_points[j].get_center(),
                 color=MUTED, stroke_width=1.0, stroke_opacity=0.55)
            for i in range(18) for j in range(i + 1, 18)
        ])
        count4950_slot = dynamic_slot(3.2, 1.2)
        page2b = page_stack(label100, hub, dense_points, count4950_slot, buff=0.9)
        layout_page(page2b)
        # Rebuild connectors after layout so they follow the final point positions.
        dense_lines = VGroup(*[
            Line(dense_points[i].get_center(), dense_points[j].get_center(),
                 color=MUTED, stroke_width=1.0, stroke_opacity=0.55)
            for i in range(18) for j in range(i + 1, 18)
        ])

        self.at_clip("s2-c07")
        self.play(type_in(label100, run_time=0.75))
        self.at_clip("s2-c08")
        self.play_parallel(Create(hub), FadeIn(dense_points), Create(dense_lines), run_time=0.7)
        count4950 = self.counter_value(0, 4950, suffix=" 次", size=56,
                                       color=YELL, anchor=count4950_slot, run_time=0.65)
        self.wait(0.07)
        self.play(FadeOut(Group(label100, hub, dense_points, dense_lines, count4950),
                          shift=UP * 0.03), run_time=0.25)

        # Page 3: the square law.
        tenfold = t("人数翻 10 倍", 42, WHITE, "BOLD")
        hundredfold = t("握手数翻 100 倍", 54, YELL, "BOLD")
        fit(hundredfold, 0.86)
        wall = _card("这就是第一道墙", 5.8, 1.85, CYAN, WHITE, 36, CARD_FILL, "BOLD")
        n_line = t("序列长度翻 N 倍 → 计算量翻 N² 倍", 34, WHITE, "BOLD")
        fit(n_line, 0.86)
        page3 = page_stack(tenfold, hundredfold, wall, n_line, buff=1.25)
        layout_page(page3)

        self.at_clip("s2-c09")
        self.play(type_in(tenfold, run_time=0.7))
        self.at_clip("s2-c10")
        self.play(type_in(hundredfold, run_time=0.8))
        self.at_clip("s2-c11")
        self.play_scroll_unroll(wall, run_time=0.75)
        self.at_clip("s2-c12")
        self.play(type_in(n_line, run_time=0.75))
        self.at_clip("s2-c13")
        self.emphasize(n_line, run_time=0.6)
        self.wait(0.07)
        self.play(FadeOut(Group(tenfold, hundredfold, wall, n_line), shift=UP * 0.03), run_time=0.25)

        # Page 4: one million characters and the GPU wall.
        context = t("100 万字的上下文", 40, WHITE, "BOLD")
        fit(context, 0.86)
        mult_label = t("计算量是 1 万字的", 31, WHITE)
        mult_slot = dynamic_slot(3.4, 1.15)
        mult_row = stable_row(mult_label, mult_slot, buff=0.3)
        gpu = t("GPU 再快，也扛不住", 46, WHITE, "BOLD")
        fit(gpu, 0.86)
        next_wall = _card("还有第二道墙等着", 5.9, 1.7, CYAN, WHITE, 34, CARD_FILL, "BOLD")
        page4 = page_stack(context, mult_row, gpu, next_wall, buff=1.0)
        layout_page(page4)

        self.at_clip("s2-c14")
        self.play(type_in(context, run_time=0.7))
        self.at_clip("s2-c15")
        mult = self.counter_value(0, 10000, suffix=" 倍", size=58,
                                  color=YELL, anchor=mult_slot, run_time=0.7,
                                  extra_anims=[type_in(mult_label, run_time=0.55)])
        self.at_clip("s2-c16")
        self.play(type_in(gpu, run_time=0.8))
        self.at_clip("s2-c17")
        gpu_cross = self.play_red_cross(gpu, run_time=0.6)
        self.at_clip("s2-c18")
        self.play_scroll_unroll(next_wall, run_time=0.75)
        self.wait(0.07)
        self.play(FadeOut(Group(head, footer_mob, context, mult_label, mult, gpu, gpu_cross, next_wall),
                          shift=RIGHT * 0.1 + DOWN * 0.03), run_time=0.5)
        self.pad_to_voice()


class S3(_Base):
    """第二道墙：KV cache 线性增长，显存装不下。"""

    def construct(self):
        self.bg()
        self.footer()
        footer_mob = self.mobjects[-1]
        head = t("第二道墙：笔记写不下", 38, YELL, "BOLD")
        head.to_edge(UP, buff=1.2)

        note = t("每次握完手，还得记笔记", 34, WHITE, "BOLD")
        image = _img("notebooks-round.png", 4.4)
        full = t("笔记越多，本子写不下了", 44, RED, "BOLD")
        fit(full, 0.86)
        kv_card = _card("KV cache：显存爆炸的那道墙", 6.3, 1.7, CYAN, WHITE, 32, CARD_FILL, "BOLD")
        page1 = page_stack(note, image, full, kv_card, buff=0.72)
        layout_page(page1)

        self.at_clip("s3-c01")
        self.play(type_in(head, run_time=0.85))
        self.at_clip("s3-c02")
        self.play(type_in(note, run_time=0.7))
        self.at_clip("s3-c03")
        self.play(FadeIn(image, shift=DOWN * 0.05), run_time=0.65)
        self.at_clip("s3-c04")
        self.play(type_in(full, run_time=0.85))
        self.at_clip("s3-c05")
        self.play_scroll_unroll(kv_card, run_time=0.75)
        self.wait(0.07)
        self.play(FadeOut(Group(note, image, full, kv_card), shift=UP * 0.03), run_time=0.25)

        token = t("每个 token，都要缓存自己的", 34, WHITE)
        kv = t("Key 和 Value", 48, CYAN, "BOLD")
        fit(kv, 0.86)
        formula = _card("KV cache = T × d × L × 2 bytes", 6.2, 1.55, YELL, WHITE, 30, CARD_FILL, "BOLD")
        context = t("100 万字的上下文，传统方式记", 32, WHITE)
        tb_slot = dynamic_slot(2.8, 1.15)
        tb_row = stable_row(t("要", 32, WHITE), tb_slot, buff=0.3)
        query = t("供后续 token 直接查询", 28, MUTED)
        page2 = page_stack(token, kv, formula, context, tb_row, query, buff=0.55)
        layout_page(page2)

        self.at_clip("s3-c06")
        self.play(type_in(token, run_time=0.7))
        self.at_clip("s3-c07")
        self.play(type_in(kv, run_time=0.7))
        self.at_clip("s3-c08")
        self.play_scroll_unroll(formula, run_time=0.7)
        self.at_clip("s3-c09")
        self.play(type_in(context, run_time=0.65))
        self.at_clip("s3-c10")
        tb5 = self.counter_value(0, 5, suffix=" TB", size=64,
                                 color=YELL, anchor=tb_slot, run_time=0.65,
                                 extra_anims=[type_in(tb_row[0], run_time=0.45)])
        self.wait(0.07)
        self.play(FadeOut(Group(token, kv, formula, context, tb_row, tb5, query),
                          shift=UP * 0.03), run_time=0.25)

        # Page 3: H100 vs the 5 TB requirement.
        h100 = t("一张 H100 才 80 GB", 40, WHITE, "BOLD")
        fit(h100, 0.86)
        bar80_slot = dynamic_slot(1.6, 0.8)
        bar5_slot = dynamic_slot(5.8, 0.8)
        row80 = stable_row(t("80 GB", 28, MUTED, "BOLD"), bar80_slot, buff=0.35)
        row5 = stable_row(t("5 TB", 28, YELL, "BOLD"), bar5_slot, buff=0.35)
        compare = t("显存对比", 28, MUTED)
        sixty = t("大 60 倍", 72, YELL, "BOLD")
        fit(sixty, 0.86)
        page3 = page_stack(h100, compare, row80, row5, sixty, buff=1.1)
        layout_page(page3)
        bar80 = Rectangle(width=1.6, height=0.8, color=MUTED,
                          fill_color=MUTED, fill_opacity=0.9).move_to(bar80_slot.get_center())
        bar5 = Rectangle(width=5.8, height=0.8, color=YELL,
                         fill_color=YELL, fill_opacity=0.9).move_to(bar5_slot.get_center())

        self.at_clip("s3-c11")
        self.play_parallel(type_in(h100, run_time=0.7), type_in(row80[0], run_time=0.45),
                           run_time=0.7)
        self.at_clip("s3-c12")
        self.grow_bar(bar5, ValueTracker(0), 5.8, run_time=0.65)
        self.at_clip("s3-c13")
        self.play_parallel(type_in(row5[0], run_time=0.45), type_in(sixty, run_time=0.8),
                           run_time=0.8)
        self.at_clip("s3-c14")
        self.emphasize(sixty, run_time=0.6)
        self.wait(0.07)
        self.play(FadeOut(Group(h100, compare, row80, row5, bar80, bar5, sixty),
                          shift=UP * 0.03), run_time=0.25)

        # Page 4: both walls at once.
        stack_label = t("两道墙叠在一起", 44, WHITE, "BOLD")
        fit(stack_label, 0.86)
        calc = _card("计算炸了", 3.5, 1.8, CYAN, WHITE, 34, CARD_FILL, "BOLD")
        storage = _card("存储也炸了", 3.5, 1.8, CYAN, WHITE, 34, CARD_FILL, "BOLD")
        walls = VGroup(calc, storage).arrange(RIGHT, buff=0.4)
        why = t("大多数模型的记忆，只能停在几万字", 31, WHITE)
        fit(why, 0.86)
        dead = t("是数学上跑不动", 56, YELL, "BOLD")
        fit(dead, 0.86)
        page4 = page_stack(stack_label, walls, why, dead, buff=1.3)
        layout_page(page4)

        self.at_clip("s3-c15")
        self.play_parallel(type_in(stack_label, run_time=0.65), FadeIn(walls), run_time=0.7)
        self.at_clip("s3-c16")
        walls_cross = self.play_red_cross(walls, run_time=0.6)
        self.at_clip("s3-c17")
        self.play(type_in(why, run_time=0.8))
        self.at_clip("s3-c18")
        self.play(type_in(dead, run_time=0.8))
        self.at_clip("s3-c19")
        self.emphasize(dead, mode="circumscribe", run_time=0.75)
        self.play(FadeOut(Group(head, footer_mob, stack_label, walls, walls_cross, why, dead),
                          shift=RIGHT * 0.1 + DOWN * 0.03), run_time=0.5)
        self.pad_to_voice()


class S4(_Base):
    """实测：O(T²) 从公式变成物理上的黑屏重启。"""

    def construct(self):
        self.bg()
        self.footer()
        footer_mob = self.mobjects[-1]
        head = t("实测：O(T²) 是物理定律", 38, YELL, "BOLD")
        head.to_edge(UP, buff=1.2)

        question = t("这两道墙有多硬？", 46, YELL, "BOLD")
        fit(question, 0.86)
        code = _card("PyTorch 实现标准注意力", 6.0, 2.0, CYAN, WHITE, 34, CARD_FILL, "BOLD")
        start = t("从 1K 序列开始往上测", 40, WHITE, "BOLD")
        fit(start, 0.86)
        sequence = t("1K → 2K → 4K → 32K", 31, CYAN, "BOLD")
        page1 = page_stack(question, code, start, sequence, buff=1.3)
        layout_page(page1)

        self.at_clip("s4-c01")
        self.play(type_in(head, run_time=0.85))
        self.at_clip("s4-c02")
        self.play(type_in(question, run_time=0.65))
        self.at_clip("s4-c03")
        self.play_scroll_unroll(code, run_time=0.8)
        self.at_clip("s4-c04")
        self.play_parallel(type_in(start, run_time=0.75), type_in(sequence, run_time=0.65), run_time=0.8)
        self.play(FadeOut(Group(question, code, start, sequence), shift=UP * 0.03), run_time=0.25)

        # Page 2: axes, measured dots and the quadratic curve.
        axes = Axes(
            x_range=[0, 4.5, 1], y_range=[0, 1.8, 0.5],
            x_length=5.7, y_length=4.3,
            axis_config={"color": MUTED, "stroke_width": 2.5,
                         "include_ticks": False, "include_tip": True},
        )
        curve = axes.plot(lambda x: 0.1 * x ** 2, x_range=[0.6, 4.15], color=YELL, stroke_width=4)
        p1 = Dot(axes.c2p(1, 0.1), color=YELL, radius=0.1)
        p2 = Dot(axes.c2p(2, 0.38), color=YELL, radius=0.1)
        p3 = Dot(axes.c2p(4, 1.53), color=YELL, radius=0.1)
        lab1 = t("1K  0.1s", 24, WHITE).next_to(p1, UP, buff=0.12)
        lab2 = t("2K  0.38s", 24, WHITE).next_to(p2, UP, buff=0.12)
        lab3 = t("4K  1.53s", 24, WHITE).next_to(p3, UP, buff=0.12)
        x_label = t("序列长度 (K)", 24, MUTED).next_to(axes, DOWN, buff=0.2)
        growth = t("长度翻 4 倍，延迟翻 15 倍", 40, YELL, "BOLD")
        fit(growth, 0.86)
        graph = Group(axes, curve, p1, p2, p3, lab1, lab2, lab3)
        page2 = page_stack(graph, x_label, growth, buff=0.9)
        layout_page(page2)

        self.at_clip("s4-c05")
        self.play(Create(axes), run_time=0.55)
        self.at_clip("s4-c06")
        self.play_parallel(FadeIn(p1), type_in(lab1, run_time=0.45), run_time=0.5)
        self.at_clip("s4-c07")
        self.play_parallel(FadeIn(p2), type_in(lab2, run_time=0.45), run_time=0.5)
        self.at_clip("s4-c08")
        self.play_parallel(FadeIn(p3), type_in(lab3, run_time=0.45), run_time=0.5)
        self.at_clip("s4-c09")
        self.play(Create(curve), run_time=0.65)
        self.at_clip("s4-c10")
        self.play(type_in(growth, run_time=0.8))
        self.at_clip("s4-c11")
        self.emphasize(growth, run_time=0.6)
        self.wait(0.07)
        self.play(FadeOut(Group(graph, x_label, growth), shift=UP * 0.03), run_time=0.25)

        # Page 3: the 32K crash.
        try32 = t("然后，我试着跑 32K", 42, WHITE, "BOLD")
        fit(try32, 0.86)
        screen = _card("32K", 2.7, 1.8, YELL, WHITE, 54, CARD_FILL, "BOLD")
        crash = t("电脑直接崩了", 50, RED, "BOLD")
        fit(crash, 0.86)
        black = _card("黑屏重启", 5.8, 1.7, RED, WHITE, 38, CARD_FILL, "BOLD")
        page3 = page_stack(try32, screen, crash, black, buff=1.0)
        layout_page(page3)

        self.at_clip("s4-c12")
        self.play(type_in(try32, run_time=0.7))
        self.at_clip("s4-c13")
        self.play_scroll_unroll(screen, run_time=0.7)
        self.at_clip("s4-c14")
        self.play(type_in(crash, run_time=0.8))
        self.at_clip("s4-c15")
        screen_cross = self.play_red_cross(screen, run_time=0.6)
        self.at_clip("s4-c16")
        self.play_scroll_unroll(black, run_time=0.7)
        self.wait(0.07)
        self.play(FadeOut(Group(try32, screen, screen_cross, crash, black), shift=UP * 0.03), run_time=0.25)

        # Page 4: matrix, memory, and the physical-law conclusion.
        matrix = _card("32K × 32K 注意力矩阵", 6.1, 1.65, CYAN, WHITE, 32, CARD_FILL, "BOLD")
        memory = t("吃掉所有内存", 46, RED, "BOLD")
        fit(memory, 0.86)
        law = _card("O(T²) 不是理论，是物理定律", 6.2, 1.75, YELL, WHITE, 34, CARD_FILL, "BOLD")
        last_q = t("真的翻不过去吗？", 52, WHITE, "BOLD")
        fit(last_q, 0.86)
        page4 = page_stack(matrix, memory, law, last_q, buff=1.0)
        layout_page(page4)

        self.at_clip("s4-c17")
        self.play_scroll_unroll(matrix, run_time=0.75)
        self.at_clip("s4-c18")
        self.play(type_in(memory, run_time=0.7))
        self.at_clip("s4-c19")
        self.play_scroll_unroll(law, run_time=0.75)
        self.at_clip("s4-c20")
        self.emphasize(law, run_time=0.65)
        self.at_clip("s4-c21")
        self.play(type_in(last_q, run_time=0.7))
        self.at_clip("s4-c22")
        cross = self.play_red_cross(last_q, run_time=0.6)
        self.wait(0.07)
        self.play(FadeOut(Group(head, footer_mob, matrix, memory, law, last_q, cross),
                          shift=RIGHT * 0.1 + DOWN * 0.03), run_time=0.5)
        self.pad_to_voice()


class S5(_Base):
    """第一招 DSA：从全连接改成只看最相关的 2048 个 token。"""

    def construct(self):
        self.bg()
        self.footer()
        footer_mob = self.mobjects[-1]
        head = t("第一招：DSA 稀疏注意力", 38, YELL, "BOLD")
        head.to_edge(UP, buff=1.2)

        answer = t("GLM-5.2 给出了答案", 42, YELL, "BOLD")
        fit(answer, 0.86)
        image = _img("indexer-round.png", 4.5)
        intro = t("而且不止一招", 36, WHITE, "BOLD")
        page1 = page_stack(answer, image, intro, buff=0.95)
        layout_page(page1)

        self.at_clip("s5-c01")
        self.play(type_in(head, run_time=0.4))
        self.at_clip("s5-c02")
        self.play_parallel(type_in(answer, run_time=0.7), FadeIn(image), run_time=0.75)
        self.at_clip("s5-c03")
        self.play(type_in(intro, run_time=0.65))
        self.wait(0.07)
        self.play(FadeOut(Group(answer, image, intro), shift=UP * 0.03), run_time=0.25)

        # Page 2: all-history tokens become a selected subset.
        standard = _card("标准注意力：看所有历史 token", 6.2, 1.7, CYAN, WHITE, 30, CARD_FILL, "BOLD")
        indexer = _card("Indexer：先挑最相关的 2048 个", 6.2, 1.7, GREEN, WHITE, 30, CARD_FILL, "BOLD")
        selected = _card("只在 2048 个上算注意力", 6.2, 1.7, YELL, WHITE, 32, CARD_FILL, "BOLD")
        page2 = page_stack(standard, indexer, selected, buff=1.05)
        layout_page(page2)

        self.at_clip("s5-c04")
        self.play_scroll_unroll(standard, run_time=0.8)
        self.at_clip("s5-c05")
        self.play_parallel(FadeIn(VGroup(*[
            Dot(np.array([-2.7 + i * 0.3, 0, 0]), radius=0.07, color=MUTED)
            for i in range(19)
        ])), run_time=0.55)
        self.at_clip("s5-c06")
        self.play_scroll_unroll(indexer, run_time=0.75)
        self.at_clip("s5-c07")
        self.play_scroll_unroll(selected, run_time=0.75)
        self.wait(0.07)
        self.play(FadeOut(Group(standard, indexer, selected), shift=UP * 0.03), run_time=0.25)

        # Page 3: the linear-growth claim.
        all_hand = t("跟所有人握手", 43, WHITE, "BOLD")
        few_hand = t("只跟最相关的 2048 人握手", 43, CYAN, "BOLD")
        fit(few_hand, 0.86)
        linear = _card("T 再大，计算量只线性增长", 6.2, 1.8, GREEN, WHITE, 34, CARD_FILL, "BOLD")
        page3 = page_stack(all_hand, few_hand, linear, buff=2.05)
        layout_page(page3)

        self.at_clip("s5-c09")
        self.play(type_in(all_hand, run_time=0.7))
        self.at_clip("s5-c10")
        self.play(type_in(few_hand, run_time=0.8))
        self.at_clip("s5-c11")
        self.play_scroll_unroll(linear, run_time=0.8)
        self.wait(0.07)
        self.play(FadeOut(Group(all_hand, few_hand, linear), shift=UP * 0.03), run_time=0.25)

        # Page 4: Indexer is itself the trap.
        trap = t("但这里有个陷阱", 48, YELL, "BOLD")
        fit(trap, 0.86)
        indexer_cost = _card("Indexer 自己也是 O(T²)", 6.0, 1.85, RED, WHITE, 36, CARD_FILL, "BOLD")
        explanation = t("它要从 T 个 token 里选出 2048 个", 31, WHITE)
        fit(explanation, 0.86)
        conclusion = t("问题，只是换了个位置", 50, WHITE, "BOLD")
        fit(conclusion, 0.86)
        page4 = page_stack(trap, indexer_cost, explanation, conclusion, buff=1.2)
        layout_page(page4)

        self.at_clip("s5-c12")
        self.play(type_in(trap, run_time=0.75))
        self.at_clip("s5-c13")
        self.play_scroll_unroll(indexer_cost, run_time=0.8)
        self.at_clip("s5-c14")
        self.play(type_in(explanation, run_time=0.75))
        self.at_clip("s5-c15")
        self.emphasize(indexer_cost, mode="circumscribe", run_time=0.7)
        self.at_clip("s5-c16")
        self.play(type_in(conclusion, run_time=0.7))
        self.at_clip("s5-c17")
        cross = self.play_red_cross(indexer_cost, run_time=0.6)
        self.wait(0.07)
        self.play(FadeOut(Group(head, footer_mob, trap, indexer_cost, explanation, conclusion, cross),
                          shift=RIGHT * 0.1 + DOWN * 0.03), run_time=0.5)
        self.pad_to_voice()


class S6(_Base):
    """第二招 IndexShare：稀疏化可以递归，跨层复用索引。"""

    def construct(self):
        self.bg()
        self.footer()
        footer_mob = self.mobjects[-1]
        head = t("第二招：IndexShare", 38, YELL, "BOLD")
        head.to_edge(UP, buff=1.2)

        insight = t("最独家的洞察", 42, YELL, "BOLD")
        recursive = _card("稀疏化，可以递归", 6.0, 1.9, CYAN, WHITE, 38, CARD_FILL, "BOLD")
        layers = VGroup(
            _card("DSA：第一层稀疏化", 5.8, 1.5, CYAN, WHITE, 30, CARD_FILL, "BOLD"),
            _card("IndexShare：第二层稀疏化", 5.8, 1.5, GREEN, WHITE, 30, CARD_FILL, "BOLD"),
        ).arrange(DOWN, buff=0.45)
        page1 = page_stack(insight, recursive, layers, buff=0.75)
        layout_page(page1)

        self.at_clip("s6-c01")
        self.play(type_in(head, run_time=0.85))
        self.at_clip("s6-c02")
        self.play(type_in(insight, run_time=0.6))
        self.at_clip("s6-c03")
        self.play_scroll_unroll(recursive, run_time=0.75)
        self.at_clip("s6-c04")
        self.play(FadeIn(layers[0]), run_time=0.55)
        self.at_clip("s6-c05")
        self.play(FadeIn(layers[1]), run_time=0.55)
        self.wait(0.07)
        self.play(FadeOut(Group(insight, recursive, layers), shift=UP * 0.03), run_time=0.25)

        # Page 2: 78 layers, only 21 compute the selector.
        layer_label = t("78 层 Transformer", 40, WHITE, "BOLD")
        active_slot = dynamic_slot(2.4, 1.1)
        active_row = stable_row(t("跑 Indexer", 31, WHITE), active_slot, buff=0.3)
        reuse = _card("剩下 57 层：直接复用最近的索引", 6.2, 1.8, GREEN, WHITE, 32, CARD_FILL, "BOLD")
        blocks = VGroup(*[
            Rectangle(width=0.22, height=0.32, color=CYAN if i < 21 else MUTED,
                      fill_color=CYAN if i < 21 else MUTED, fill_opacity=0.8,
                      stroke_width=1.0)
            for i in range(78)
        ]).arrange_in_grid(rows=6, cols=13, buff=0.08)
        page2 = page_stack(layer_label, blocks, active_row, reuse, buff=0.62)
        layout_page(page2)

        self.at_clip("s6-c07")
        active = self.counter_value(0, 21, suffix=" 层", size=54,
                                    color=YELL, anchor=active_slot, run_time=0.65,
                                    extra_anims=[type_in(layer_label, run_time=0.7), FadeIn(blocks)])
        self.at_clip("s6-c08")
        self.play_scroll_unroll(reuse, run_time=0.75)
        self.at_clip("s6-c09")
        self.emphasize(reuse, run_time=0.55)
        self.wait(0.07)
        self.play(FadeOut(Group(layer_label, blocks, active_row, active, reuse), shift=UP * 0.03), run_time=0.25)

        # Page 3: why reuse works.
        why = t("凭什么？", 50, YELL, "BOLD")
        similarity = _card("相邻层的注意力模式高度相似", 6.2, 1.7, CYAN, WHITE, 31, CARD_FILL, "BOLD")
        sim_slot = dynamic_slot(2.4, 1.05)
        sim_row = stable_row(t("跨层相似度", 30, WHITE), sim_slot, buff=0.28)
        window = t("4 层窗口内复用依然有效", 38, GREEN, "BOLD")
        fit(window, 0.86)
        page3 = page_stack(why, similarity, sim_row, window, buff=1.1)
        layout_page(page3)

        self.at_clip("s6-c10")
        self.play(type_in(why, run_time=0.7))
        self.at_clip("s6-c11")
        self.play_scroll_unroll(similarity, run_time=0.75)
        self.at_clip("s6-c12")
        sim08 = self.counter_value(0, 0.8, decimals=1, size=58,
                                   color=YELL, anchor=sim_slot, run_time=0.65,
                                   extra_anims=[type_in(sim_row[0], run_time=0.5)])
        self.at_clip("s6-c13")
        self.play(type_in(window, run_time=0.75))
        self.wait(0.07)
        self.play(FadeOut(Group(why, similarity, sim_row, sim08, window), shift=UP * 0.03), run_time=0.25)

        # Page 4: measured gain and the storage suspense.
        stacked = t("两招叠加", 42, WHITE, "BOLD")
        context = t("1M 上下文下", 36, WHITE)
        gain_slot = dynamic_slot(2.8, 1.2)
        gain_row = stable_row(t("每 token 计算量降低", 30, WHITE), gain_slot, buff=0.3)
        passed = _card("计算这道墙，翻过去了", 6.0, 1.8, GREEN, WHITE, 34, CARD_FILL, "BOLD")
        storage_q = t("那存储那道墙呢？", 48, YELL, "BOLD")
        fit(storage_q, 0.86)
        page4 = page_stack(stacked, context, gain_row, passed, storage_q, buff=0.65)
        layout_page(page4)

        self.at_clip("s6-c14")
        self.play(type_in(stacked, run_time=0.7))
        self.at_clip("s6-c15")
        self.play(type_in(context, run_time=0.6))
        self.at_clip("s6-c16")
        gain = self.counter_value(0, 2.9, decimals=1, suffix=" 倍", size=58,
                                  color=YELL, anchor=gain_slot, run_time=0.7,
                                  extra_anims=[type_in(gain_row[0], run_time=0.55)])
        self.at_clip("s6-c17")
        self.play_scroll_unroll(passed, run_time=0.75)
        self.at_clip("s6-c18")
        self.play(type_in(storage_q, run_time=0.7))
        self.wait(0.07)
        self.play(FadeOut(Group(head, footer_mob, stacked, context, gain_row, gain, passed, storage_q),
                          shift=RIGHT * 0.1 + DOWN * 0.03), run_time=0.5)
        self.pad_to_voice()


class S7(_Base):
    """第三招 MLA：压缩 KV cache，并与前两招协同。"""

    def construct(self):
        self.bg()
        self.footer()
        footer_mob = self.mobjects[-1]
        head = t("第三招：MLA 压缩 KV cache", 38, YELL, "BOLD")
        head.to_edge(UP, buff=1.2)

        intro = t("MLA", 56, YELL, "BOLD")
        fit(intro, 0.86)
        subtitle = t("把完整 KV 变成压缩表示", 38, WHITE, "BOLD")
        full_kv = _card("标准 KV：每个 token 缓存完整向量", 6.2, 1.8, CYAN, WHITE, 31, CARD_FILL, "BOLD")
        page1 = page_stack(intro, subtitle, full_kv, buff=2.1)
        layout_page(page1)

        self.at_clip("s7-c01")
        self.play(type_in(head, run_time=0.3))
        self.at_clip("s7-c02")
        self.play(type_in(intro, run_time=0.7))
        self.at_clip("s7-c03")
        self.play_parallel(type_in(subtitle, run_time=0.7), FadeIn(full_kv), run_time=0.7)
        self.play(FadeOut(Group(intro, subtitle, full_kv), shift=UP * 0.03), run_time=0.25)

        # Page 2: 6144 -> 512 dimensions.
        standard = t("完整向量", 34, WHITE, "BOLD")
        standard_slot = dynamic_slot(5.8, 0.75)
        compressed = t("压缩表示", 34, WHITE, "BOLD")
        compressed_slot = dynamic_slot(1.7, 0.75)
        row_standard = stable_row(standard, standard_slot, buff=0.3)
        row_compressed = stable_row(compressed, compressed_slot, buff=0.3)
        over = t("压缩超 10 倍", 54, YELL, "BOLD")
        fit(over, 0.86)
        page2 = page_stack(row_standard, row_compressed, over, buff=2.45)
        layout_page(page2)
        wide = Rectangle(width=5.8, height=0.75, color=CYAN, fill_color=CYAN, fill_opacity=0.8).move_to(standard_slot.get_center())
        narrow = Rectangle(width=1.7, height=0.75, color=GREEN, fill_color=GREEN, fill_opacity=0.8).move_to(compressed_slot.get_center())

        self.at_clip("s7-c04")
        self.add(standard)
        self.grow_bar(wide, ValueTracker(0), 5.8, run_time=0.65)
        self.at_clip("s7-c05")
        self.play(type_in(t("维度 6144", 30, MUTED), run_time=0.55))
        self.at_clip("s7-c06")
        self.add(compressed)
        self.grow_bar(narrow, ValueTracker(0), 1.7, run_time=0.65)
        self.at_clip("s7-c07")
        self.play(type_in(over, run_time=0.75))
        self.wait(0.07)
        self.play(FadeOut(Group(row_standard, row_compressed, wide, narrow, over), shift=UP * 0.03), run_time=0.25)

        # Page 3: storage reduction, with anchored bars.
        cache_label = t("KV cache", 40, WHITE, "BOLD")
        old_slot = dynamic_slot(5.9, 0.8)
        new_slot = dynamic_slot(1.7, 0.8)
        old_row = stable_row(t("5 TB", 30, RED, "BOLD"), old_slot, buff=0.3)
        new_row = stable_row(t("78 GB", 30, GREEN, "BOLD"), new_slot, buff=0.3)
        impossible = t("完全不可行", 44, RED, "BOLD")
        feasible = t("多卡能扛", 48, GREEN, "BOLD")
        page3 = page_stack(cache_label, old_row, new_row, impossible, feasible, buff=1.0)
        layout_page(page3)
        old_bar = Rectangle(width=5.9, height=0.8, color=RED, fill_color=RED, fill_opacity=0.8).move_to(old_slot.get_center())
        new_bar = Rectangle(width=1.7, height=0.8, color=GREEN, fill_color=GREEN, fill_opacity=0.8).move_to(new_slot.get_center())

        self.at_clip("s7-c08")
        self.add(cache_label, old_row[0])
        self.grow_bar(old_bar, ValueTracker(0), 5.9, run_time=0.65)
        self.at_clip("s7-c09")
        self.add(new_row[0])
        self.grow_bar(new_bar, ValueTracker(0), 1.7, run_time=0.65)
        self.at_clip("s7-c10")
        self.play(type_in(impossible, run_time=0.7))
        self.at_clip("s7-c11")
        self.play(type_in(feasible, run_time=0.65))
        self.wait(0.07)
        self.play(FadeOut(Group(cache_label, old_row, new_row, old_bar, new_bar, impossible, feasible), shift=UP * 0.03), run_time=0.25)

        # Page 4: the three fixes are a coordinated system.
        synergy = t("三招协同", 46, YELL, "BOLD")
        must = _card("缺一不可", 5.9, 1.8, YELL, WHITE, 40, CARD_FILL, "BOLD")
        c1 = _card("DSA：拆掉注意力的平方项", 6.0, 1.35, CYAN, WHITE, 27, CARD_FILL, "BOLD")
        c2 = _card("IndexShare：拆掉 Indexer 的平方项", 6.0, 1.35, GREEN, WHITE, 27, CARD_FILL, "BOLD")
        c3 = _card("MLA：压掉 KV 的线性增长", 6.0, 1.35, YELL, WHITE, 27, CARD_FILL, "BOLD")
        trio = VGroup(c1, c2, c3).arrange(DOWN, buff=0.28)
        dead = t("任何一招缺失，1M 上下文都跑不动", 33, WHITE, "BOLD")
        fit(dead, 0.86)
        page4 = page_stack(synergy, must, trio, dead, buff=0.55)
        layout_page(page4)

        self.at_clip("s7-c12")
        self.play(type_in(synergy, run_time=0.7))
        self.at_clip("s7-c13")
        self.play_scroll_unroll(must, run_time=0.7)
        self.at_clip("s7-c14")
        self.play(FadeIn(c1), run_time=0.55)
        self.at_clip("s7-c15")
        self.play(FadeIn(c2), run_time=0.55)
        self.at_clip("s7-c16")
        self.play(FadeIn(c3), run_time=0.55)
        self.at_clip("s7-c17")
        self.play(type_in(dead, run_time=0.65))
        self.at_clip("s7-c18")
        must_cross = self.play_red_cross(must, run_time=0.6)
        self.at_clip("s7-c19")
        self.play(FadeOut(Group(synergy, must, must_cross, trio, dead), shift=UP * 0.03), run_time=0.25)
        self.at_clip("s7-c20")
        self.play(FadeOut(Group(head, footer_mob), shift=RIGHT * 0.1 + DOWN * 0.03), run_time=0.5)
        self.pad_to_voice()


class S8(_Base):
    """总结、回扣实验结果、递归启示和品牌尾卡。"""

    def construct(self):
        self.bg()
        self.footer()
        footer_mob = self.mobjects[-1]
        head = t("翻墙之后，记忆才真正可用", 38, YELL, "BOLD")
        head.to_edge(UP, buff=1.2)

        # Page 1: return to the original failure.
        opening = t("AI 为什么干到一半会崩？", 46, WHITE, "BOLD")
        fit(opening, 0.86)
        wall1 = _card("注意力 O(T²)", 5.8, 1.65, CYAN, WHITE, 34, CARD_FILL, "BOLD")
        wall2 = _card("KV cache 线性增长", 5.8, 1.65, RED, WHITE, 34, CARD_FILL, "BOLD")
        explosion = t("长序列下同时爆炸", 48, RED, "BOLD")
        fit(explosion, 0.86)
        page1 = page_stack(opening, wall1, wall2, explosion, buff=0.9)
        layout_page(page1)

        self.at_clip("s8-c01")
        self.play(type_in(head, run_time=0.4))
        self.at_clip("s8-c02")
        self.play(type_in(opening, run_time=0.65))
        self.at_clip("s8-c03")
        self.play_scroll_unroll(wall1, run_time=0.7)
        self.at_clip("s8-c04")
        self.play_scroll_unroll(wall2, run_time=0.7)
        self.at_clip("s8-c05")
        self.add(explosion)
        cross1 = self.play_red_cross(wall1, run_time=0.6)
        self.wait(0.07)
        self.play(FadeOut(Group(opening, wall1, wall2, explosion, cross1), shift=UP * 0.03), run_time=0.25)

        # Page 2: three engineering moves turn impossible into feasible.
        image = _img("wall-jump-round.png", 4.5)
        chain1 = _card("DSA", 1.55, 1.1, CYAN, WHITE, 30, CARD_FILL, "BOLD")
        chain2 = _card("IndexShare", 2.35, 1.1, GREEN, WHITE, 28, CARD_FILL, "BOLD")
        chain3 = _card("MLA", 1.55, 1.1, YELL, WHITE, 30, CARD_FILL, "BOLD")
        chain = VGroup(chain1, chain2, chain3).arrange(RIGHT, buff=0.28)
        impossible = t("数学上不可能", 42, RED, "BOLD")
        feasible = t("工程上可行", 46, GREEN, "BOLD")
        page2 = page_stack(image, chain, impossible, feasible, buff=0.48)
        layout_page(page2)
        chain_arrows = VGroup(
            Arrow(chain1.get_right() + RIGHT * 0.08, chain2.get_left() - RIGHT * 0.08, buff=0, color=MUTED),
            Arrow(chain2.get_right() + RIGHT * 0.08, chain3.get_left() - RIGHT * 0.08, buff=0, color=MUTED),
        )

        self.at_clip("s8-c06")
        self.play(FadeIn(image, shift=DOWN * 0.05), run_time=0.6)
        self.at_clip("s8-c07")
        self.play_parallel(FadeIn(chain), Create(chain_arrows), run_time=0.65)
        self.at_clip("s8-c08")
        self.play(type_in(impossible, run_time=0.7))
        self.at_clip("s8-c09")
        self.play(type_in(feasible, run_time=0.7))
        self.wait(0.07)
        self.play(FadeOut(Group(image, chain, chain_arrows, impossible, feasible), shift=UP * 0.03), run_time=0.25)

        # Page 3: score callback with anchored values and a growth bar.
        score_label = t("SWE-Marathon", 40, WHITE, "BOLD")
        old_slot = dynamic_slot(1.7, 1.1)
        new_slot = dynamic_slot(2.6, 1.1)
        score_row = stable_row(old_slot, t("→", 42, MUTED), new_slot, buff=0.3)
        pct_slot = dynamic_slot(2.7, 1.0)
        pct_row = stable_row(t("涨了", 34, WHITE), pct_slot, buff=0.3)
        math = _card("不是魔法，是数学", 5.9, 1.85, YELL, WHITE, 42, CARD_FILL, "BOLD")
        page3 = page_stack(score_label, score_row, pct_row, math, buff=0.9)
        layout_page(page3)

        self.at_clip("s8-c10")
        old_score = self.counter_value(0, 1.0, decimals=1, size=60,
                                       color=MUTED, anchor=old_slot, run_time=0.55,
                                       extra_anims=[type_in(score_label, run_time=0.65)])
        self.at_clip("s8-c11")
        new_score = self.counter_value(1.0, 13.0, decimals=1, size=68,
                                       color=YELL, anchor=new_slot, run_time=0.65)
        self.wait(0.07)
        pct = self.counter_value(0, 1200, suffix="%", size=54,
                                 color=YELL, anchor=pct_slot, run_time=0.65,
                                 extra_anims=[type_in(pct_row[0], run_time=0.5)])
        self.at_clip("s8-c12")
        self.play(FadeIn(math), run_time=0.65)
        self.at_clip("s8-c13")
        self.emphasize(math, mode="circumscribe", run_time=0.7)
        self.wait(0.07)
        self.play(FadeOut(Group(score_label, score_row, pct_row, old_score, new_score, pct, math),
                          shift=UP * 0.03), run_time=0.25)

        # Page 4: recursion and the next article.
        insight = t("更深的启示", 44, YELL, "BOLD")
        n1 = _card("稀疏化", 2.0, 1.2, CYAN, WHITE, 30, CARD_FILL, "BOLD")
        n2 = _card("selector", 2.1, 1.2, GREEN, WHITE, 28, CARD_FILL, "BOLD")
        n3 = _card("下一个瓶颈", 2.25, 1.2, YELL, WHITE, 28, CARD_FILL, "BOLD")
        nodes = VGroup(n1, n2, n3).arrange(RIGHT, buff=0.3)
        next_label = t("下一篇：", 32, WHITE)
        next_card = _card("AI 为什么说话这么慢？——推测解码的数学", 6.1, 1.7, CYAN, WHITE, 28, CARD_FILL, "BOLD")
        page4 = page_stack(insight, nodes, next_label, next_card, buff=1.1)
        layout_page(page4)
        arrows = VGroup(
            Arrow(n1.get_right() + RIGHT * 0.08, n2.get_left() - RIGHT * 0.08, buff=0, color=MUTED),
            Arrow(n2.get_right() + RIGHT * 0.08, n3.get_left() - RIGHT * 0.08, buff=0, color=MUTED),
        )

        self.at_clip("s8-c14")
        self.play(type_in(insight, run_time=0.7))
        self.at_clip("s8-c15")
        self.play_parallel(FadeIn(nodes), Create(arrows), run_time=0.7)
        self.at_clip("s8-c16")
        n3_cross = self.play_red_cross(n3, run_time=0.6)
        self.at_clip("s8-c17")
        self.play(type_in(next_label, run_time=0.55))
        self.at_clip("s8-c18")
        self.play_scroll_unroll(next_card, run_time=0.8)
        self.wait(0.07)
        self.play(FadeOut(Group(insight, nodes, n3_cross, arrows, next_label, next_card), shift=UP * 0.03), run_time=0.25)

        # Page 5: question and stable brand end card. It intentionally remains on screen.
        question1 = t("你觉得，", 42, WHITE, "BOLD")
        question2 = t("1M 上下文真的有必要吗？", 46, YELL, "BOLD")
        fit(question2, 0.86)
        comment = t("评论区聊聊", 38, GREEN, "BOLD")
        avatar = ImageMobject(str(ASSET_DIR / "avatar-sjai-round.png"))
        avatar.scale_to_fit_width(2.35)
        follow = t("关注「数解AI」", 36, YELL, "BOLD")
        title = t("《为什么AI上下文越长越慢？两道数学硬墙一次讲透》", 25, WHITE, "BOLD")
        fit(title, 0.84)
        read = t("查看公众号文章", 30, GREEN, "BOLD")
        end_page = page_stack(question1, question2, comment, avatar, follow, title, read, buff=0.38)
        layout_page(end_page)

        self.at_clip("s8-c19")
        self.play(type_in(question1, run_time=0.6))
        self.at_clip("s8-c20")
        self.play(type_in(question2, run_time=0.8))
        self.at_clip("s8-c21")
        self.play(type_in(comment, run_time=0.6))
        self.at_clip("s8-c22")
        self.play_parallel(FadeIn(avatar), type_in(follow, run_time=0.55), run_time=0.65)
        self.play_parallel(type_in(title, run_time=0.8), type_in(read, run_time=0.6), run_time=0.8)
        self.pad_to_voice()
