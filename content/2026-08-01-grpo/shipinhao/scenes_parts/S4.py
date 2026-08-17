class S4(_Base):
    def construct(self):
        # ---------- 全局：背景 + 页脚 + 标题（0.00-1.10）----------
        self.bg()
        self.footer()
        footer_mob = self.mobjects[-1]  # footer() 不返回引用，取最近 add 的 mob 供 transition_out 带走
        head = t("核心机制：考试类比", 38, YELL, "BOLD").to_edge(UP, buff=1.2)

        # ---------- 页1（0.00-10.20）：考试类比搭建 ----------
        q = t("GRPO 怎么工作？", 40, YELL, "BOLD")
        line1 = t("把同一个 prompt 想成同一道题，", 28, WHITE)
        fit(line1, 0.9)

        # 答卷小纸片（成组小徽章，FadeIn 合规）
        def make_paper():
            sheet = Rectangle(width=0.72, height=0.78, color=MUTED, stroke_width=2,
                              fill_color=WHITE, fill_opacity=0.07)
            ln = VGroup(*[Line(LEFT * 0.2, RIGHT * 0.2, color=MUTED, stroke_width=1.5) for _ in range(3)])
            for i, l in enumerate(ln):
                l.move_to(sheet.get_center() + UP * (0.14 - i * 0.16))
            return VGroup(sheet, ln)

        papers = VGroup(*[make_paper() for _ in range(5)]).arrange(RIGHT, buff=0.22)
        g_lab = t("G 份答卷", 24, CYAN, "BOLD")
        paper_row = VGroup(papers, g_lab).arrange(RIGHT, buff=0.35)

        # 标准答案 → 自动裁判（同组等宽卡，分两次拉幕）
        card_ans = _card("标准答案", 2.3, 0.8, GREEN, GREEN, 26, CARD_FILL, "BOLD")
        card_judge = _card("自动裁判", 2.3, 0.8, YELL, YELL, 26, CARD_FILL, "BOLD")
        pair = VGroup(card_ans, card_judge).arrange(RIGHT, buff=1.0)
        arrow = Arrow(card_ans.get_right() + RIGHT * 0.08, card_judge.get_left() - RIGHT * 0.08,
                      color=MUTED, stroke_width=4, buff=0)
        badge_row = VGroup(card_ans, arrow, card_judge)
        layout_page(page_stack(q, line1, paper_row, badge_row, buff=0.6))

        self.play(type_in(head, run_time=1.1), type_in(q, run_time=0.9))  # 0.00-1.10
        self.at(1.95)
        self.play(type_in(line1, run_time=0.9))  # 1.95-2.85
        self.at(4.84)
        self.play(FadeIn(papers, shift=DOWN * 0.05, lag_ratio=0.15), run_time=0.6)  # 4.84-5.44
        self.play(type_in(g_lab, run_time=0.5))  # 5.44-5.94
        self.at(6.90)
        self.play_scroll_unroll(card_ans, run_time=1.1)  # 6.90-8.00
        self.at(8.48)
        self.play(Create(arrow), run_time=0.35)          # 8.48-8.83
        self.play_scroll_unroll(card_judge, run_time=1.0)  # 8.83-9.83

        # 换页 → 页2a（10.20-12.66）：不请老师逐步批改（否定红叉）
        self.at(10.20)
        self.play(FadeOut(VGroup(q, line1, paper_row, badge_row), shift=UP * 0.03), run_time=0.3)  # 10.20-10.50
        card_teach = _card("老师逐步批改", 5.0, 3.6, MUTED, WHITE, 40, CARD_FILL, "BOLD")
        layout_page(card_teach)
        self.play_scroll_unroll(card_teach, run_time=1.0)  # 10.50-11.50
        cross = self.play_red_cross(card_teach)            # 11.50-12.10
        self.play(FadeOut(VGroup(card_teach, cross), shift=UP * 0.03), run_time=0.3)  # 12.10-12.40

        # 换页 → 页2b（12.66-14.42）：概念图（多份答卷围绕平均分）
        img = ImageMobject("img/class-average-round.png")
        img.scale_to_fit_width(3.8)  # 图为主：居中放大，上下留白均衡
        cap = t("先看全班平均分：", 26, WHITE)
        layout_page(page_stack(img, cap, buff=0.55))
        self.at(12.66)
        self.play(FadeIn(img, shift=DOWN * 0.05), run_time=0.6)  # 12.66-13.26
        self.play(type_in(cap, run_time=0.8))  # 13.26-14.06

        # 换页 → 页2c（14.42-19.45）：平均分参照 + 高于/低于
        self.at(14.42)
        self.play(FadeOut(Group(img, cap), shift=UP * 0.03), run_time=0.3)  # 14.42-14.72
        axis = Line(LEFT * 2.3, RIGHT * 2.3, color=MUTED, stroke_width=4)
        lab_mean = t("平均分", 24, MUTED)
        axis_row = VGroup(axis, lab_mean).arrange(RIGHT, buff=0.25)
        bars_hi = VGroup(Rectangle(width=0.5, height=0.7, color=GREEN, fill_color=GREEN, fill_opacity=0.55),
                         Rectangle(width=0.5, height=1.0, color=GREEN, fill_color=GREEN, fill_opacity=0.55),
                         Rectangle(width=0.5, height=0.85, color=GREEN, fill_color=GREEN, fill_opacity=0.55))
        bars_hi.arrange(RIGHT, buff=0.4, aligned_edge=DOWN)
        bars_lo = VGroup(Rectangle(width=0.5, height=0.8, color=RED, fill_color=RED, fill_opacity=0.55),
                         Rectangle(width=0.5, height=0.6, color=RED, fill_color=RED, fill_opacity=0.55),
                         Rectangle(width=0.5, height=0.7, color=RED, fill_color=RED, fill_opacity=0.55))
        bars_lo.arrange(RIGHT, buff=0.4, aligned_edge=UP)
        label_hi = t("高于平均 → 正向信号", 26, GREEN, "BOLD")
        fit(label_hi, 0.9)
        label_lo = t("低于平均 → 概率下降", 26, RED, "BOLD")
        fit(label_lo, 0.9)
        chart = VGroup(label_hi, bars_hi, axis_row, bars_lo, label_lo).arrange(DOWN, buff=0.42)
        layout_page(chart)
        self.play(Create(axis), run_time=0.5)                    # 14.72-15.22
        self.play(type_in(lab_mean, run_time=0.4))               # 15.22-15.62
        self.play(*[GrowFromEdge(b, DOWN) for b in bars_hi], run_time=0.55)  # 15.62-16.17
        self.play(type_in(label_hi, run_time=0.75))              # 16.17-16.92
        self.play(*[GrowFromEdge(b, UP) for b in bars_lo], run_time=0.9)     # 16.92-17.82
        self.play(type_in(label_lo, run_time=0.8))               # 17.82-18.62

        # 换页 → 页3a（19.45-22.94）：全班都对 / 全班都错
        self.at(19.45)
        self.play(FadeOut(VGroup(axis, lab_mean, bars_hi, bars_lo, label_hi, label_lo),
                          shift=UP * 0.03), run_time=0.3)        # 19.45-19.75
        l_allok = t("可要是全班都对，", 28, WHITE)
        ok_row = VGroup(t("✔", 44, GREEN, "BOLD"), t("✔", 44, GREEN, "BOLD"),
                        t("✔", 44, GREEN, "BOLD")).arrange(RIGHT, buff=0.7)
        l_allbad = t("或者全班都错呢？", 28, WHITE)
        bad_row = VGroup(t("✗", 44, RED, "BOLD"), t("✗", 44, RED, "BOLD"),
                         t("✗", 44, RED, "BOLD")).arrange(RIGHT, buff=0.7)
        layout_page(page_stack(l_allok, ok_row, l_allbad, bad_row, buff=0.72))
        self.play(type_in(l_allok, run_time=0.8))                # 19.75-20.55
        self.play(FadeIn(ok_row, scale=1.4), run_time=0.5)       # 20.55-21.05
        self.at(21.12)
        self.play(type_in(l_allbad, run_time=0.8))               # 21.12-21.92
        self.play(FadeIn(bad_row, scale=1.4), run_time=0.5)      # 21.92-22.42

        # 换页 → 页3b（22.94-24.19）：大家分数一样 → 等长条
        self.at(22.94)
        self.play(FadeOut(VGroup(l_allok, ok_row, l_allbad, bad_row), shift=UP * 0.03), run_time=0.3)  # 22.94-23.24
        l_same = t("大家分数一样，", 32, WHITE)
        bars_same = VGroup(*[Rectangle(width=0.7, height=2.4, color=CYAN,
                                       fill_color=CYAN, fill_opacity=0.55) for _ in range(3)])
        bars_same.arrange(RIGHT, buff=0.6, aligned_edge=DOWN)
        layout_page(page_stack(l_same, bars_same, buff=0.7))
        self.play(*[GrowFromEdge(b, DOWN) for b in bars_same],
                  type_in(l_same, run_time=0.5), run_time=0.55)  # 23.24-23.79
        self.play(FadeOut(VGroup(l_same, bars_same), shift=UP * 0.03), run_time=0.3)  # 23.85-24.15

        # 换页 → 页3c（24.19-26.11）：不知道该往哪边改（问号 + 双向箭头）
        dir_grp = VGroup(t("↑", 100, MUTED, "BOLD"), t("？", 170, YELL, "BOLD"),
                         t("↓", 100, MUTED, "BOLD")).arrange(RIGHT, buff=0.9)
        l_last = t("模型就不知道该往哪边改了", 32, WHITE)
        fit(l_last, 0.9)
        layout_page(page_stack(dir_grp, l_last, buff=1.3))
        self.at(24.19)
        self.play(FadeIn(dir_grp, scale=1.2), run_time=0.5)      # 24.19-24.69
        self.play(type_in(l_last, run_time=0.9))                 # 24.69-25.59
        self.emphasize(dir_grp[1], mode="wiggle")                # 25.59-26.39

        # 结尾转场（带走全部可见元素）→ pad_to_voice
        self.transition_out(head, footer_mob, dir_grp, l_last)   # 26.39-26.99
        self.pad_to_voice()
