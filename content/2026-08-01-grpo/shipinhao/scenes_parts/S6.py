class S6(_Base):
    """S6：PPO vs GRPO —— 双栏对比（critic token 级 vs 整输出 output 级）→
    代价是方差（Axes 双曲线：方差 1/G 下降 + 采样成本线性涨 + trace_dot）→
    最优组大小 G*（GSM8K ≈ 32 / MATH ≈ 64 counter_value）。
    时间轴 = tts 句级边界（s6 重录后 29.233s，2026-08-16）；数字走 counter_value，
    曲线走 Axes 手绘坐标图；trace_dot 返回 VGroup(dot, trail) 换页整体带走。"""

    def _cnt(self, start, end, suffix="", size=48, color=YELL,
             pos=None, run_time=0.9, decimals=0):
        """数字滚动（S5 同款）：滚动前先 pos(grp) 摆位，suffix 用 updater 跟随数字右缘。"""
        num = DecimalNumber(start, mob_class=Text, num_decimal_places=decimals,
                            font_size=size, color=color)
        grp = num
        if suffix:
            tail = t(suffix, int(size * 0.42), color, "BOLD")
            tail.next_to(num, RIGHT, buff=0.12)
            tail.align_to(num, DOWN)
            grp = VGroup(num, tail)
            tail.add_updater(lambda m: (m.next_to(num, RIGHT, buff=0.12),
                                        m.align_to(num, DOWN)))
        if pos is not None:
            pos(grp)
        tr = ValueTracker(start)
        num.add_updater(lambda m: m.set_value(tr.get_value()))
        self.add(grp)
        self.play(tr.animate.set_value(end), run_time=run_time, rate_func=smooth)
        num.clear_updaters()
        if suffix:
            tail.clear_updaters()
        return grp

    def construct(self):
        # ---------- 全局：背景 + 页脚 + 标题（0.00-0.60）----------
        self.bg()
        self.footer()
        footer_mob = self.mobjects[-1]
        head = t("PPO vs GRPO：差在哪？", 38, YELL, "BOLD").to_edge(UP, buff=1.2)
        self.play(type_in(head, run_time=0.6))  # 0.00-0.60（那 GRPO 和 PPO 差在哪？）

        # ---------- 页1（0.66-12.53）：双栏对比 ----------
        # 左栏 PPO（白，宽 3.0）
        ppo_t = t("PPO", 30, WHITE, "BOLD")
        ppo_c1 = boxed("critic 逐 token 估分", 3.0, 0.95, WHITE, 26)
        ppo_c2 = boxed("粒度细", 3.0, 0.95, CYAN, 26)
        ppo_c3 = boxed("但要额外训练", 3.0, 0.95, WHITE, 26)
        ppo_col = VGroup(ppo_t, ppo_c1, ppo_c2, ppo_c3).arrange(DOWN, buff=0.85)

        # 右栏 GRPO（黄高亮，宽 3.0）
        grpo_t = t("GRPO", 30, YELL, "BOLD")
        grpo_c1 = boxed("整输出一个分", 3.0, 0.95, YELL, 26, weight="BOLD")
        grpo_c2 = boxed("粒度粗", 3.0, 0.95, WHITE, 26)
        grpo_c3 = boxed("零训练成本", 3.0, 0.95, GREEN, 26, weight="BOLD")
        grpo_col = VGroup(grpo_t, grpo_c1, grpo_c2, grpo_c3).arrange(DOWN, buff=0.85)
        cols = VGroup(ppo_col, grpo_col).arrange(RIGHT, buff=1.0)
        layout_page(cols)

        self.at(0.66)
        self.play(type_in(ppo_t, run_time=0.5))  # 0.66-1.16（PPO 的 critic…）
        self.at(1.3)
        self.play_scroll_unroll(ppo_c1, run_time=1.2)  # 1.3-2.5（给每个 token 独立估分 0.81-3.10）
        self.at(3.10)
        self.play_scroll_unroll(ppo_c2, run_time=1.0)  # 3.10-4.10（粒度细 3.10-6.04）
        self.at(6.04)
        self.play_scroll_unroll(ppo_c3, run_time=1.1)  # 6.04-7.14（但要额外训练 6.04-7.12）
        self.at(7.2)
        mk_x = self.play_mark("✗", ppo_c3, color=RED, run_time=0.5)  # 7.2-7.7 额外训练是负担
        self.at(7.7)
        self.play(type_in(grpo_t, run_time=0.5))  # 7.7-8.2（GRPO 给整个输出打一个分 7.12-8.95）
        self.at(8.3)
        self.play_scroll_unroll(grpo_c1, run_time=1.2)  # 8.3-9.5
        self.at(8.95)
        self.play_scroll_unroll(grpo_c2, run_time=1.0)  # 8.95-9.95（粒度粗 8.95-11.47）
        self.at(11.47)
        self.play_scroll_unroll(grpo_c3, run_time=0.8)  # 11.47-12.27（但零训练成本 11.47-12.53）

        self.at(12.53)
        self.play(FadeOut(VGroup(ppo_t, ppo_c1, ppo_c2, ppo_c3, grpo_t,
                                 grpo_c1, grpo_c2, grpo_c3, mk_x),
                          shift=UP * 0.03), run_time=0.3)  # 12.53-12.83 换页（代价是方差 12.53 起）

        # ---------- 页2（12.53-21.04）：代价是方差 —— Axes 双曲线 ----------
        lab_v = t("代价是方差", 30, YELL, "BOLD")
        axes = Axes(
            x_range=[0, 12, 3], y_range=[0, 6, 2],
            x_length=5.0, y_length=3.0,
            axis_config={"color": MUTED, "stroke_width": 3,
                         "include_ticks": True, "include_tip": True,
                         "tip_shape": StealthTip},
        )
        xlab = t("组大小 G", 20, MUTED).next_to(axes.x_axis, DOWN, buff=0.28)
        ylab = t("方差/成本", 20, MUTED).next_to(axes.y_axis, LEFT, buff=0.25)
        curve1 = axes.plot(lambda x: 4.2 / x + 0.15, x_range=[0.9, 11.5], color=CYAN)
        curve1.set_stroke(width=5)
        line2 = axes.plot(lambda x: 0.42 * x, x_range=[0.9, 11.5], color=GREEN)
        line2.set_stroke(width=5)
        lab1 = t("方差（随 G 下降）", 20, CYAN).next_to(curve1.point_from_proportion(0.62), UR, buff=0.12)
        lab2 = t("采样成本（线性涨）", 20, GREEN).next_to(line2.point_from_proportion(0.85), UR, buff=0.12)
        chart = VGroup(axes, xlab, ylab, curve1, line2, lab1, lab2)
        fit(chart, 0.88)  # 带 y 轴标签后整图限宽，杜绝左右被裁
        layout_page(page_stack(lab_v, chart, buff=0.5))

        self.play(type_in(lab_v, run_time=0.8))  # 12.9-13.7（代价是方差：12.53-14.25）
        self.at(14.25)
        self.play(FadeIn(axes, shift=DOWN * 0.05), run_time=0.6)  # 14.25-14.85（有限组大小下估计波动更大 14.25-15.77）
        self.play(type_in(xlab, run_time=0.5), type_in(ylab, run_time=0.5))  # 14.9-15.4
        self.at(15.77)
        self.play(Create(curve1), run_time=0.7)  # 15.77-16.47（方差随 G 增大而下降 15.77-18.71）
        self.play(type_in(lab1, run_time=0.5))  # 16.5-17.0
        dot = self.trace_dot(curve1, color=CYAN, run_time=0.9)  # 17.0-17.9 沿曲线滑行留尾
        self.at(18.71)
        self.play(Create(line2), run_time=0.7)  # 18.71-19.41（采样成本却线性上涨 18.71-21.04）
        self.play(type_in(lab2, run_time=0.5))  # 19.5-20.0

        self.at(21.04)
        self.play(FadeOut(VGroup(lab_v, axes, xlab, ylab, curve1, line2,
                                 lab1, lab2, dot), shift=UP * 0.03), run_time=0.3)  # 21.04-21.34 换页（dot+trail 带走）

        # ---------- 页3（21.04-29.23）：最优组大小 G* ----------
        lab_g = t("存在一个最优组大小", 30, YELL, "BOLD")
        fit(lab_g, 0.9)

        # 数字行：GSM8K ≈ 32（左）| MATH ≈ 64（右），同一行
        g1_lab = t("GSM8K ≈", 28, WHITE)
        n32_ph = Rectangle(width=0.9, height=0.7, fill_opacity=0.0, stroke_opacity=0.0)
        pair32 = VGroup(g1_lab, n32_ph).arrange(RIGHT, buff=0.12, aligned_edge=DOWN)
        m_lab = t("MATH ≈", 28, WHITE)
        n64_ph = Rectangle(width=0.9, height=0.7, fill_opacity=0.0, stroke_opacity=0.0)
        pair64 = VGroup(m_lab, n64_ph).arrange(RIGHT, buff=0.12, aligned_edge=DOWN)
        num_row = VGroup(pair32, pair64).arrange(RIGHT, buff=1.4)

        # G* 曲线图（数字行下方）
        axes2 = Axes(
            x_range=[0, 12, 3], y_range=[0, 6, 2],
            x_length=5.0, y_length=2.5,
            axis_config={"color": MUTED, "stroke_width": 3,
                         "include_ticks": True, "include_tip": True,
                         "tip_shape": StealthTip},
        )
        xlab2 = t("组大小 G", 20, MUTED).next_to(axes2.x_axis, DOWN, buff=0.25)
        ylab2 = t("误差", 20, MUTED).next_to(axes2.y_axis, LEFT, buff=0.25)
        cur2 = axes2.plot(lambda x: 4.2 / x + 0.15, x_range=[0.9, 11.5], color=CYAN)
        cur2.set_stroke(width=5)
        gstar_x = 4.2
        gstar_y = 4.2 / gstar_x + 0.15
        gline = DashedLine(axes2.c2p(gstar_x, 0.1), axes2.c2p(gstar_x, gstar_y + 0.35),
                           color=YELL, stroke_width=4, dash_length=0.12)
        glab = t("G*", 26, YELL, "BOLD").next_to(axes2.c2p(gstar_x, gstar_y + 0.35), UP, buff=0.1)
        chart2 = VGroup(axes2, xlab2, ylab2, cur2, gline, glab)
        fit(chart2, 0.88)
        layout_page(page_stack(lab_g, num_row, chart2, buff=0.55))

        self.play(type_in(lab_g, run_time=0.8))  # 21.4-22.2（所以存在一个最优组大小 21.04-23.23）
        self.at(22.3)
        self.play(type_in(g1_lab, run_time=0.3))  # 22.3-22.6（GSM8K 上大约 32 21.04-23.23）
        n32 = self._cnt(0, 32, suffix="", size=48, color=YELL,
                        pos=lambda g: g.move_to(n32_ph),
                        run_time=0.8)  # 22.7-23.5
        self.at(23.23)
        self.play(type_in(m_lab, run_time=0.4))  # 23.23-23.63（M 23.23-25.65）
        # n64 在 27.80 才滚动（上大约 64 27.80-29.23），勿提前定义（_cnt 定义即播放）
        self.at(23.7)
        self.play(FadeIn(axes2, shift=DOWN * 0.05), run_time=0.5)  # 23.7-24.2（ATH 段 25.65-27.80 前）
        self.play(type_in(xlab2, run_time=0.4), type_in(ylab2, run_time=0.4))  # 24.2-24.6
        self.at(24.6)
        self.play(Create(cur2), run_time=0.7)  # 24.6-25.3
        self.at(25.3)
        self.play(Create(gline), run_time=0.4)  # 25.3-25.7
        self.play(type_in(glab, run_time=0.4))  # 25.7-26.1
        dot2 = self.trace_dot(cur2, color=CYAN, run_time=1.0)  # 26.1-27.1（ATH 段填充）
        self.at(27.2)
        self.breathe(axes2, scale=1.02, run_time=1.0, loops=1)  # 27.2-28.2 滞留期轻呼吸
        self.at(27.80)
        n64 = self._cnt(0, 64, suffix="", size=48, color=YELL,
                        pos=lambda g: g.move_to(n64_ph),
                        run_time=0.9)  # 27.80-28.7（上大约 64 27.80-29.23）
        self.at(28.8)
        self.emphasize(n64, mode="indicate", run_time=0.4)  # 28.8-29.2

        # ---------- 结尾转场（带走全部可见元素）→ pad_to_voice ----------
        self.at(29.2)
        self.transition_out(head, footer_mob, lab_g, g1_lab, m_lab, n32, n64,
                            axes2, xlab2, ylab2, cur2, gline, glab, dot2)
        self.pad_to_voice()
