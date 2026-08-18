class S1(_Base):
    """S1：开场钩子 —— agent 修 bug 崩了 + SWE-Marathon 得分对比。
    页1（0.00-12.90）agent 修 bug 循环：任务卡 + 读代码→跑测试→改文件 3 卡循环 +
    进度条 200 步到顶 → 红叉崩掉；
    页2（12.90-22.19）「这不是段子」+ SWE-Marathon 基准 + GLM-5.1 得分 1.0（满分 100）；
    页3（22.19-27.14）不是它不聪明：记忆 20 万字撑不到任务结束；
    页4（27.14-39.35）GLM-5.2 记忆 100 万字 → 得分 13.0（+1200% 爆点）→ 为什么失忆 → 两道墙卡片。
    时间轴 = s1 锚点表（39.35s）；数字走 counter_value / grow_bar。"""

    def construct(self):
        self.bg()
        self.footer()
        footer_mob = self.mobjects[-1]
        head = t("AI 程序员的一天", 38, YELL, "BOLD").to_edge(UP, buff=1.2)
        self.play(type_in(head, run_time=1.1))  # 0.00-1.10

        # ---------- 页1（0.00-12.90）：修 bug 循环 + 200 步崩掉 ----------
        task = _card("任务：修一个编译器的 bug", 6.4, 1.7, CYAN, WHITE, 32, CARD_FILL, "BOLD")
        c1 = _card("读代码", 1.9, 1.5, CYAN, WHITE, 28, CARD_FILL, "BOLD")
        c2 = _card("跑测试", 1.9, 1.5, GREEN, WHITE, 28, CARD_FILL, "BOLD")
        c3 = _card("改文件", 1.9, 1.5, YELL, WHITE, 28, CARD_FILL, "BOLD")
        loop = VGroup(c1, c2, c3).arrange(RIGHT, buff=0.9)
        loop_lab = t("修 bug 循环", 26, MUTED)
        bar_ph = Rectangle(width=4.5, height=0.9, fill_opacity=0.0, stroke_opacity=0.0)
        step_ph = Rectangle(width=2.2, height=1.0, fill_opacity=0.0, stroke_opacity=0.0)
        bar_row = VGroup(bar_ph, step_ph).arrange(RIGHT, buff=0.4, aligned_edge=DOWN)
        page1 = page_stack(task, loop_lab, loop, bar_row, buff=0.8)
        layout_page(page1)
        # 进度条单独居中（2026-08-19 打磨：原与「200 步」成组居中导致进度条偏左）
        bar_row.shift(RIGHT * (step_ph.get_width() + 0.4) / 2)
        # 箭头在整页定位后创建（位置基于最终坐标）
        ar1 = Arrow(c1.get_right() + RIGHT * 0.1, c2.get_left() - RIGHT * 0.1, color=MUTED, stroke_width=4, buff=0)
        ar2 = Arrow(c2.get_right() + RIGHT * 0.1, c3.get_left() - RIGHT * 0.1, color=MUTED, stroke_width=4, buff=0)
        back = CurvedArrow(c3.get_bottom() + DOWN * 0.35, c1.get_bottom() + DOWN * 0.35,
                           angle=-PI / 2, color=MUTED, stroke_width=4)
        back_lab = t("循环", 22, MUTED).next_to(back, DOWN, buff=0.15)

        self.at(2.38)
        self.play_scroll_unroll(task, run_time=0.8)  # 2.38-3.18（修一个编译器的bug。）
        self.at(4.24)
        self.play(type_in(loop_lab, run_time=0.4))  # 4.24-4.64（读代码、跑测试、）
        self.play_scroll_unroll(c1, run_time=0.6)  # 4.64-5.24
        self.at(6.74)
        self.play_scroll_unroll(c2, run_time=0.6)  # 6.74-7.34
        self.at(8.07)
        self.play_scroll_unroll(c3, run_time=0.6)  # 8.07-8.67（改文件——干到第200步，）
        self.at(8.67)
        self.play(Create(ar1), Create(ar2), run_time=0.5)  # 8.67-9.17
        self.at(9.17)
        self.play(Create(back), run_time=0.4)  # 9.17-9.57
        self.play(type_in(back_lab, run_time=0.3))  # 9.57-9.87
        self.at(9.75)
        bar = Rectangle(width=4.5, height=0.9, color=YELL, fill_color=YELL, fill_opacity=0.85)
        bar.move_to(bar_ph.get_center())
        tr = ValueTracker(0)
        self.add(bar)
        self.grow_bar(bar, tr, 4.5, run_time=1.0)  # 9.75-10.75 进度条长满
        self.at(10.75)
        step = self.counter_value(0, 200, suffix=" 步", size=44, color=YELL,
                                   anchor=step_ph, run_time=0.6)  # 10.75-11.35
        self.at(11.52)
        cross = self.play_red_cross(bar, run_time=0.65)  # 11.52-12.17 崩掉
        self.at(12.17)
        boom = t("任务崩了", 40, WHITE, "BOLD")
        fit(boom, 0.9)
        boom.next_to(bar, DOWN, buff=0.5)
        self.play(type_in(boom, run_time=0.5))  # 12.17-12.67
        self.at(12.90)
        self.play(FadeOut(VGroup(task, loop_lab, loop, ar1, ar2, back, back_lab, bar, step, cross, boom),
                          shift=UP * 0.03), run_time=0.3)  # 12.90-13.20 换页

        # ---------- 页2（12.90-22.19）：这不是段子 + SWE-Marathon + GLM-5.1 1.0 分 ----------
        notjoke = t("这不是段子", 72, YELL, "BOLD")
        fit(notjoke, 0.9)
        swe = t("SWE-Marathon", 52, CYAN, "BOLD")
        fit(swe, 0.9)
        desc = t("专门测 AI 程序员超长任务的基准", 34, WHITE)
        fit(desc, 0.9)
        g51 = t("GLM-5.1", 32, MUTED, "BOLD")
        score_ph = Rectangle(width=2.4, height=1.5, fill_opacity=0.0, stroke_opacity=0.0)
        full = t("满分 100", 32, MUTED)
        score_row = VGroup(g51, score_ph, full).arrange(RIGHT, buff=0.5, aligned_edge=ORIGIN)
        page2 = page_stack(notjoke, swe, desc, score_row, buff=1.2)
        layout_page(page2)

        self.at(13.20)
        self.play(type_in(notjoke, run_time=0.9))  # 13.20-14.10（这不是段子。）
        self.at(14.29)
        self.play(type_in(swe, run_time=0.7))  # 14.29-14.99（SWE-Marathon，）
        self.at(15.41)
        self.play(type_in(desc, run_time=0.9))  # 15.41-16.31（专门测AI程序员超长任务的基准，）
        self.at(18.04)
        self.play(type_in(g51, run_time=0.5))  # 18.04-18.54（GLM-5.1在上面只得了1.0分，）
        self.at(18.54)
        score1 = self.counter_value(0, 1.0, decimals=1, size=56, color=MUTED,
                                    anchor=score_ph, run_time=0.5)  # 18.54-19.04
        self.at(20.84)
        self.play(type_in(full, run_time=0.5))  # 20.84-21.34（满分100。）
        self.at(22.19)
        self.play(FadeOut(VGroup(notjoke, swe, desc, g51, score1, full),
                          shift=UP * 0.03), run_time=0.3)  # 22.19-22.49 换页

        # ---------- 页3（22.19-27.14）：不是它不聪明，记忆 20 万字 ----------
        notsmart = t("不是它不聪明", 60, WHITE, "BOLD")
        fit(notsmart, 0.9)
        mem_lab = t("记忆只有", 34, WHITE)
        mem_ph = Rectangle(width=3.0, height=1.5, fill_opacity=0.0, stroke_opacity=0.0)
        mem_row = VGroup(mem_lab, mem_ph).arrange(RIGHT, buff=0.3, aligned_edge=ORIGIN)
        cant = t("撑不到任务结束", 56, RED, "BOLD")
        fit(cant, 0.9)
        mem_note = t("20 万字 = 200K tokens", 28, MUTED)
        fit(mem_note, 0.9)
        page3 = page_stack(notsmart, mem_row, cant, mem_note, buff=1.2)
        layout_page(page3)

        self.at(22.49)
        self.play(type_in(notsmart, run_time=0.9))  # 22.49-23.39（不是它不聪明，）
        self.at(23.38)
        self.play(type_in(mem_lab, run_time=0.5))  # 23.38-23.88（是它的记忆只有20万字，）
        self.at(23.88)
        mem20 = self.counter_value(0, 20, suffix=" 万字", size=52, color=YELL,
                                   anchor=mem_ph, run_time=0.6)  # 23.88-24.48
        self.at(25.48)
        self.play(type_in(cant, run_time=0.8))  # 25.48-26.28（撑不到任务结束。）
        self.at(26.28)
        self.emphasize(cant, run_time=0.6)  # 26.28-26.88
        self.at(26.88)
        self.play(type_in(mem_note, run_time=0.4))  # 26.88-27.28
        self.at(27.14)
        self.play(FadeOut(VGroup(notsmart, mem_lab, mem20, cant, mem_note),
                          shift=UP * 0.03), run_time=0.3)  # 27.14-27.44 换页

        # ---------- 页4（27.14-39.35）：GLM-5.2 100 万字 → 13.0 +1200% → 两道墙 ----------
        g52 = t("GLM-5.2 把记忆扩到", 32, WHITE)
        mem2_ph = Rectangle(width=3.2, height=1.2, fill_opacity=0.0, stroke_opacity=0.0)
        mem2_row = VGroup(g52, mem2_ph).arrange(RIGHT, buff=0.3, aligned_edge=ORIGIN)
        score2_lab = t("得分跳到", 32, WHITE)
        score2_ph = Rectangle(width=3.4, height=1.3, fill_opacity=0.0, stroke_opacity=0.0)
        score2_row = VGroup(score2_lab, score2_ph).arrange(RIGHT, buff=0.3, aligned_edge=ORIGIN)
        why = t("为什么干到一半会失忆？", 48, YELL, "BOLD")
        fit(why, 0.9)
        w1 = _card("墙一：计算 O(T²)", 3.7, 1.5, CYAN, WHITE, 28, CARD_FILL, "BOLD")
        w2 = _card("墙二：存储 KV cache", 3.7, 1.5, CYAN, WHITE, 28, CARD_FILL, "BOLD")
        walls = VGroup(w1, w2).arrange(RIGHT, buff=0.5)
        pct_ph = Rectangle(width=3.4, height=1.0, fill_opacity=0.0, stroke_opacity=0.0)
        page4 = page_stack(mem2_row, score2_row, pct_ph, why, walls, buff=0.7)
        layout_page(page4)

        self.at(27.44)
        self.play(type_in(g52, run_time=0.6))  # 27.44-28.04（GLM-5.2把记忆扩到100万字，）
        self.at(28.04)
        mem100 = self.counter_value(0, 100, suffix=" 万字", size=52, color=YELL,
                                    anchor=mem2_ph, run_time=0.7)  # 28.04-28.74
        self.at(29.92)
        self.play(type_in(score2_lab, run_time=0.5))  # 29.92-30.42（得分跳到13.0——涨了1200%。）
        self.at(30.42)
        score13 = self.counter_value(0, 13.0, decimals=1, size=64, color=YELL,
                                     anchor=score2_ph, run_time=0.6)  # 30.42-31.02
        self.at(31.02)
        pct = self.counter_value(0, 1200, suffix="%", size=44, color=YELL,
                                 anchor=pct_ph, run_time=0.5)  # 31.02-31.52
        plus = t("+", 44, YELL, "BOLD")
        plus.next_to(pct, LEFT, buff=0.08)
        plus.align_to(pct, ORIGIN)
        self.play(type_in(plus, run_time=0.3))  # 31.02-31.32
        self.at(31.52)
        self.emphasize(pct, run_time=0.5)  # 31.52-32.02
        self.at(32.03)
        self.play(type_in(why, run_time=1.0))  # 32.03-33.03（为什么干到一半会失忆？）
        self.at(34.07)
        self.play_scroll_unroll(w1, run_time=0.8)  # 34.07-34.87（不是记性差，）
        self.at(34.87)
        self.play_scroll_unroll(w2, run_time=0.8)  # 34.87-35.67（是两道数学硬墙。）
        self.at(37.26)
        self.emphasize(VGroup(w1, w2), mode="circumscribe", run_time=0.8)  # 37.26-38.06
        self.at(38.06)
        self.transition_out(head, footer_mob, g52, mem100, score2_lab, score13, pct, plus, why, w1, w2)  # 38.06-38.66
        self.pad_to_voice()


