class S2(_Base):
    """S2：GRPO 诞生 —— DeepSeekMath 2024 起点 → 规则判分（概念图 exam-grading）→
    不训练 critic（红叉否定）→ 三卡（不训练 critic / 多份答案 / 组内平均分参照）→
    R1-Zero AIME 2024 15.6%→77.9%（数字滚动爆点）→ 反思涌现。
    时间轴锚点 = tts 句级边界（口播实测，禁止预估）；数字走 _cnt 数字滚动
    （counter_value 定位先行版，S3/S5 同款，避免原地滚动后跳位）。"""

    def _cnt(self, start, end, suffix="", decimals=1, size=64, color=YELL,
             pos=None, run_time=1.8):
        """数字滚动定位先行版：滚动前先 pos(grp) 摆位，避免滚动后跳位。
        suffix 用 updater 跟随数字右缘（DecimalNumber 变宽时左缘固定、右缘右移）。"""
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
        # ---------- 全局：背景 + 页脚 + 标题（0.00-1.10）----------
        self.bg()
        self.footer()
        footer_mob = self.mobjects[-1]  # footer() 不返回引用，取最近 add 的 mob 供 transition_out 带走
        head = t("GRPO 的诞生：从数学题开始", 38, YELL, "BOLD")
        fit(head, 0.9)
        head.to_edge(UP, buff=1.0)
        self.play(type_in(head, run_time=1.1))  # 0.00-1.10（GRPO 的起点，）

        # ---------- 页0（2.80-6.11）：DeepSeekMath · 2024 起点卡 ----------
        card_ds = _card("DeepSeekMath · 2024", 6.2, 3.6, CYAN, WHITE, 40, CARD_FILL, "BOLD")
        layout_page(card_ds)
        self.at(2.80)
        self.play_scroll_unroll(card_ds, run_time=1.3)  # 2.80-4.10（…DeepSeek 的 DeepSeekMath。）
        self.at(5.70)
        self.play(FadeOut(card_ds, shift=UP * 0.03), run_time=0.4)  # 5.70-6.10

        # ---------- 页1（6.11-11.55）：概念图 + 图下标注 ----------
        img = ImageMobject("img/exam-grading-round.png")
        img.scale_to_fit_width(4.2)  # 图为主：放进纵向带中心，四周留白均衡
        cap = t("数学题有标准答案，规则就能判分", 26, WHITE)
        fit(cap, 0.9)
        layout_page(page_stack(img, cap, buff=0.55))
        self.at(6.11)
        self.play(FadeIn(img, shift=DOWN * 0.05), run_time=0.8)  # 6.11-6.91（观察很朴素：）
        self.at(7.68)
        self.play(type_in(cap, run_time=1.0))  # 7.68-8.68（数学题有标准答案，规则就能判分，）
        self.at(11.63)
        self.play(FadeOut(Group(img, cap), shift=UP * 0.03), run_time=0.4)  # 11.63-12.03（台词 11.634 结束后再换页）

        # ---------- 页2（11.63-15.25）：否定卡 + 红叉（何必）----------
        card_q = _card("训练大模型猜每一步的价值？", 6.6, 3.6, MUTED, WHITE, 34, CARD_FILL, "BOLD")
        layout_page(card_q)
        self.at(11.63)
        self.play_scroll_unroll(card_q, run_time=1.2)  # 11.63-12.83（何必再训练一个大模型…）
        self.at(12.90)
        cross_q = self.play_red_cross(card_q)  # 12.90-13.50 打叉否定
        self.at(14.85)
        self.play(FadeOut(VGroup(card_q, cross_q), shift=UP * 0.03), run_time=0.4)  # 14.85-15.25

        # ---------- 页3（15.25-21.15）：三卡竖排（等宽 5.8×0.95，居中留白）----------
        c_a = _card("不训练 critic", 5.8, 0.95, GREEN, WHITE, 28, CARD_FILL, "BOLD")
        c_b = _card("同题生成多份答案", 5.8, 0.95, CYAN, WHITE, 28, CARD_FILL, "BOLD")
        c_c = _card("组内平均分当参照", 5.8, 0.95, YELL, WHITE, 28, CARD_FILL, "BOLD")
        cards = page_stack(c_a, c_b, c_c, buff=0.65)
        layout_page(cards)
        self.at(15.25)
        self.play_scroll_unroll(c_a, run_time=1.3)  # 15.25-16.55（于是 GRPO 不训练 critic，）
        self.at(18.30)
        self.play_scroll_unroll(c_b, run_time=1.3)  # 18.30-19.60（让同一道题生成多份答案，）
        self.at(19.70)
        self.play_scroll_unroll(c_c, run_time=1.0)  # 19.70-20.70（拿组内平均分当参照。）
        self.at(20.75)
        self.play(FadeOut(cards, shift=UP * 0.03), run_time=0.4)  # 20.75-21.15

        # ---------- 页4（21.20-32.85）：R1-Zero 路线 + AIME 数字滚动爆点 ----------
        lab_r1 = _card("DeepSeek-R1-Zero 用这条路线", 6.4, 1.05, CYAN, WHITE, 28, CARD_FILL, "BOLD")
        aime_lab = t("AIME 2024 正确率", 24, MUTED)
        # 先出旧值 15.6%（数字对比先旧后新，2026-08-16 用户反馈 00:49）
        old = VGroup(t("15.6%", 28, MUTED), t("→", 28, MUTED)).arrange(RIGHT, buff=0.12)
        num_ph = Rectangle(width=2.5, height=1.0, fill_opacity=0.0, stroke_opacity=0.0)
        num_row = VGroup(old, num_ph).arrange(RIGHT, buff=0.35, aligned_edge=DOWN)
        layout_page(page_stack(lab_r1, aime_lab, num_row, buff=0.7))

        self.at(21.20)
        self.play_scroll_unroll(lab_r1, run_time=1.2)  # 21.20-22.40（DeepSeek-R1-Zero 用这条路线，）
        self.at(23.60)
        self.play(type_in(aime_lab, run_time=0.5))  # 23.60-24.10（AIME 2024 正确率从…）
        self.at(25.50)
        self.play(type_in(old, run_time=0.5))  # 25.50-26.00 先出旧值 15.6%
        self.at(26.2)
        num = self._cnt(15.6, 77.9, suffix="%", decimals=1, size=64, color=YELL,
                        pos=lambda g: g.next_to(old, RIGHT, buff=0.35, aligned_edge=DOWN),
                        run_time=1.8)  # 26.2-28.0 15.6%→77.9% 数字滚动（旧值已在场）
        self.at(29.20)
        self.emphasize(num, mode="indicate", run_time=0.6)  # 29.20-29.80 爆点聚焦
        self.at(32.45)
        self.play(FadeOut(VGroup(lab_r1, aime_lab, num, old), shift=UP * 0.03),
                  run_time=0.4)  # 32.45-32.85

        # ---------- 页5（32.89-37.30）：反思涌现 ----------
        learn = t("还自发学会了", 28, MUTED)
        refl = t("反思", 64, YELL, "BOLD")
        bubble = _card("等等，我算错了？", 5.0, 1.25, MUTED, MUTED, 26, CARD_FILL2, "NORMAL")
        layout_page(page_stack(learn, refl, bubble, buff=0.8))
        self.at(32.89)
        self.play(type_in(learn, run_time=0.6))  # 32.89-33.49（还自发学会了）
        self.at(33.80)
        self.play_scroll_unroll(bubble, run_time=1.0)  # 33.80-34.80（学会反思期间展示气泡，勿留静音期）
        self.at(35.31)
        self.play(type_in(refl, run_time=0.5))  # 35.31-35.81（反思）
        self.at(35.85)
        self.emphasize(refl, mode="indicate", run_time=0.4)  # 35.85-36.25

        # ---------- 结尾转场（带走全部可见元素）→ pad_to_voice ----------
        self.transition_out(head, footer_mob, learn, refl, bubble, run_time=0.6)  # 37.30-37.90
        self.pad_to_voice()
