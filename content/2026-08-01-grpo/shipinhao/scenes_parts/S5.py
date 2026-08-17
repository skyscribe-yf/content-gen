class S5(_Base):
    """S5：GRPO 四步 —— 采样(G 个输出，DeepSeekMath 用 64) → 算奖励 → 组内归一化
    (z-score 公式三段 morph) → 策略更新(clip 刹车 / KL 尺子)。
    爆点：基础版本优势整段共享（常数）。时间轴 = tts 句级边界；数字走 counter_value，
    公式走 MathTex（texlive 已装）。"""

    def _cnt(self, start, end, suffix="", size=56, color=YELL,
             pos=None, run_time=0.9):
        """数字滚动（S3 同款定位先行版）：滚动前先 pos(grp) 摆位，避免原地滚动后跳位。
        suffix 用 updater 跟随数字右缘（DecimalNumber 变宽时左缘固定、右缘右移）。"""
        num = DecimalNumber(start, mob_class=Text, num_decimal_places=0,
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
        # ---------- 全局：背景 + 页脚 + 标题（0.00-0.50）----------
        self.bg()
        self.footer()
        footer_mob = self.mobjects[-1]  # footer() 不返回引用，取最近 add 的 mob 供 transition_out 带走
        head = t("GRPO 就四步", 38, YELL, "BOLD").to_edge(UP, buff=1.2)
        # 锚点窗口仅 0.51s（0.00-0.51），标题 type_in 压到 0.5 不侵占下一句
        self.play(type_in(head, run_time=0.5))  # 0.00-0.50

        # ---------- 页1（0.00-8.78）：第一步 · 采样 ----------
        s1 = t("第一步", 30, CYAN, "BOLD")
        chip_s = boxed("采样", 1.7, 0.72, YELL, 30, weight="BOLD")
        step_row = VGroup(s1, chip_s).arrange(RIGHT, buff=0.4).set_x(0.0)
        line1 = t("每个问题生成 G 个输出", 27, WHITE)
        fit(line1, 0.9)

        # G 份输出小方格（2×4 徽章组，FadeIn 合规）
        chips = VGroup(
            VGroup(*[Rectangle(width=0.45, height=0.45, color=CYAN,
                               fill_color=CYAN, fill_opacity=0.22) for _ in range(4)]).arrange(RIGHT, buff=0.2),
            VGroup(*[Rectangle(width=0.45, height=0.45, color=CYAN,
                               fill_color=CYAN, fill_opacity=0.22) for _ in range(4)]).arrange(RIGHT, buff=0.2),
        ).arrange(DOWN, buff=0.2)
        g_lab = t("G 个输出", 22, MUTED)
        # DeepSeekMath 标签居中放 chips 下方（勿放右侧：偏右 + 与 chips 重叠，2026-08-16 用户反馈）
        ds_lab = t("DeepSeekMath", 24, CYAN, "BOLD")
        if ds_lab.width > 1.7:
            ds_lab.set_width(1.7)
        num_ph = Rectangle(width=1.6, height=0.75, fill_opacity=0.0, stroke_opacity=0.0)
        layout_page(page_stack(step_row, line1, chips, g_lab, ds_lab, num_ph, buff=0.5))

        self.at(0.51)
        self.play(type_in(s1, run_time=0.5))  # 0.51-1.01（第一步，）
        self.at(2.21)
        self.play_scroll_unroll(chip_s, run_time=1.2)  # 2.21-3.41（采样：）
        self.at(3.79)
        self.play(type_in(line1, run_time=0.9))  # 3.79-4.69（每个问题生成 G 个输出，）
        self.at(4.75)
        self.play(FadeIn(chips, shift=DOWN * 0.05, lag_ratio=0.12), run_time=0.55)  # 4.75-5.30
        self.at(5.35)
        self.play(type_in(g_lab, run_time=0.5))  # 5.35-5.85
        self.at(6.33)
        self.play(type_in(ds_lab, run_time=0.5))  # 6.33-6.83（DeepSeekMath 用 64。）
        num64 = self._cnt(0, 64, suffix=" 个", size=52, color=YELL,
                          pos=lambda g: g.move_to(num_ph),
                          run_time=1.1)  # 6.9-8.0
        self.at(8.0)
        self.emphasize(num64, mode="indicate", run_time=0.45)  # 8.0-8.45（64 爆点）

        self.at(8.48)
        self.play(FadeOut(VGroup(s1, chip_s, line1, chips, g_lab, ds_lab, num64),
                          shift=UP * 0.03), run_time=0.3)  # 8.48-8.78

        # ---------- 页2a（8.78-18.23）：第二步算奖励 + 第三步组内归一化 + z-score 公式 ----------
        s2 = t("第二步", 30, CYAN, "BOLD")
        chip_r = boxed("算奖励", 1.8, 0.72, GREEN, 28, weight="BOLD")
        row2 = VGroup(s2, chip_r).arrange(RIGHT, buff=0.4).set_x(0.0)
        s3 = t("第三步", 30, CYAN, "BOLD")
        chip_n = boxed("组内归一化", 2.4, 0.72, YELL, 26, weight="BOLD")
        row3 = VGroup(s3, chip_n).arrange(RIGHT, buff=0.4).set_x(0.0)

        # z-score 公式三段：分子 → 分数线+分母 → 相对优势；三段共用同一居中槽位
        num_f = MathTex(r"r_i - \text{mean}",
                        tex_to_color_map={r"\text{mean}": MUTED})
        frac_f = MathTex(r"\frac{r_i - \text{mean}}{\text{std}}",
                         tex_to_color_map={r"\text{mean}": MUTED, r"\text{std}": CYAN})
        full_f = MathTex(r"\hat{A}_i = \frac{r_i - \text{mean}}{\text{std}}",
                         tex_to_color_map={r"\hat{A}_i": YELL,
                                           r"\text{mean}": MUTED, r"\text{std}": CYAN})
        if full_f.width > 5.5:
            full_f.set_width(5.5)
        formula_slot = Rectangle(width=5.6, height=1.05, fill_opacity=0.0, stroke_opacity=0.0)
        for f in (num_f, frac_f, full_f):
            f.move_to(formula_slot)
        rel_lab = t("相对优势", 22, YELL, "BOLD")
        rel_lab.next_to(formula_slot, DOWN, buff=0.2)  # 勿放公式右侧（右缘超界被裁，2026-08-16 用户反馈）
        layout_page(page_stack(row2, row3, formula_slot, rel_lab, buff=0.55))
        for f in (num_f, frac_f, full_f):
            f.move_to(formula_slot)  # 槽位随整页居中后再对齐，避免公式偏位

        self.at(8.78)
        self.play(type_in(s2, run_time=0.5))  # 8.78-9.28（第二步，）
        self.at(9.4)
        self.play_scroll_unroll(chip_r, run_time=1.2)  # 9.4-10.6（算奖励。）
        self.at(10.78)
        self.play(type_in(s3, run_time=0.5))  # 10.78-11.28（第三步，）
        self.at(11.4)
        self.play_scroll_unroll(chip_n, run_time=1.2)  # 11.4-12.6（组内归一化：）
        self.at(12.87)
        self.play(FadeIn(num_f, shift=DOWN * 0.05), run_time=0.6)  # 12.87-13.47（每个分数减去组内平均，）
        self.at(15.03)
        self.morph_to(num_f, frac_f, run_time=0.8)  # 15.03-15.83（再除以组内波动，）
        self.at(16.64)
        self.morph_to(frac_f, full_f, run_time=0.8)  # 16.64-17.44（得到相对优势。）
        self.at(17.44)
        self.play(type_in(rel_lab, run_time=0.45))  # 17.44-17.89
        self.at(17.9)
        self.play(FadeOut(VGroup(s2, chip_r, s3, chip_n, full_f, rel_lab),
                          shift=UP * 0.03), run_time=0.3)  # 17.9-18.2

        # ---------- 页2b（18.23-25.06）：注意爆点 —— 优势整段共享 ----------
        chip_warn = boxed("注意", 1.6, 0.62, YELL, 28, weight="BOLD")
        line_a = t("基础版本里，优势在整个回答上是常数", 27, WHITE)
        fit(line_a, 0.9)
        tok_lab = t("同一个输出里的每个 token", 22, MUTED)
        # token 小方格一行（一个输出拆成多个 token）
        tokens = VGroup(*[Rectangle(width=0.42, height=0.42, color=WHITE,
                                    fill_color=WHITE, fill_opacity=0.12) for _ in range(7)])
        tokens.arrange(RIGHT, buff=0.12)
        card_s = _card("共享同一个分数", 3.7, 0.74, YELL, YELL, 26, CARD_FILL, "BOLD")
        layout_page(page_stack(chip_warn, line_a, tok_lab, tokens, card_s, buff=0.5))

        self.at(18.23)
        self.play_scroll_unroll(chip_warn, run_time=0.75)  # 18.23-18.98（注意，）
        self.at(19.01)
        self.play(type_in(line_a, run_time=0.9))  # 19.01-19.91（基础版本里…每个 token，）
        self.at(20.0)
        self.play(type_in(tok_lab, run_time=0.6))  # 20.0-20.6
        self.at(20.65)
        self.play(FadeIn(tokens, shift=DOWN * 0.05, lag_ratio=0.12), run_time=0.55)  # 20.65-21.2
        self.at(21.3)
        self.breathe(tokens, scale=1.02, run_time=1.0, loops=1)  # 滞留期轻呼吸 21.3-22.3
        self.at(22.98)
        self.play_scroll_unroll(card_s, run_time=1.2)  # 22.98-24.18（共享同一个分数。）
        self.at(24.18)
        self.emphasize(card_s, mode="indicate", run_time=0.6)  # 24.18-24.78 爆点聚焦
        self.at(24.8)
        self.play(FadeOut(VGroup(chip_warn, line_a, tok_lab, tokens, card_s),
                          shift=UP * 0.03), run_time=0.25)  # 24.8-25.05

        # ---------- 页3（25.06-33.48）：第四步 · 策略更新 ----------
        s4 = t("第四步", 30, CYAN, "BOLD")
        chip_u = boxed("策略更新", 2.0, 0.72, YELL, 28, weight="BOLD")
        row4 = VGroup(s4, chip_u).arrange(RIGHT, buff=0.4).set_x(0.0)
        upd_f = MathTex(r"\frac{\pi_\theta}{\pi_{\text{old}}} \times \hat{A}_i",
                        tex_to_color_map={r"\hat{A}_i": YELL, r"\pi_{\text{old}}": MUTED})
        if upd_f.width > 5.5:
            upd_f.set_width(5.5)
        upd_slot = Rectangle(width=5.6, height=1.0, fill_opacity=0.0, stroke_opacity=0.0)
        upd_f.move_to(upd_slot)
        chip_clip = boxed("clip 当刹车", 2.6, 0.64, RED, 26, weight="BOLD")
        chip_kl = boxed("KL 当尺子", 2.6, 0.64, CYAN, 26, weight="BOLD")
        chip_row = VGroup(chip_clip, chip_kl).arrange(RIGHT, buff=0.4)
        layout_page(page_stack(row4, upd_slot, chip_row, buff=0.6))
        upd_f.move_to(upd_slot)  # 槽位随整页居中后再对齐

        self.at(25.06)
        self.play(type_in(s4, run_time=0.5))  # 25.06-25.56（第四步，）
        self.at(26.86)
        self.play_scroll_unroll(chip_u, run_time=1.2)  # 26.86-28.06（策略更新：）
        self.at(29.09)
        self.play(FadeIn(upd_f, shift=DOWN * 0.05), run_time=0.8)  # 29.09-29.89（概率比乘优势，）
        self.at(30.91)
        self.play_scroll_unroll(chip_clip, run_time=1.2)  # 30.91-32.11（clip 当刹车，）
        self.at(32.2)
        self.play_scroll_unroll(chip_kl, run_time=1.2)  # 32.2-33.4（KL 当尺子。）

        # ---------- 结尾转场（带走全部可见元素）→ pad_to_voice ----------
        self.transition_out(head, footer_mob, s4, chip_u, upd_f, chip_clip, chip_kl)  # 33.4-34.0
        self.pad_to_voice()
