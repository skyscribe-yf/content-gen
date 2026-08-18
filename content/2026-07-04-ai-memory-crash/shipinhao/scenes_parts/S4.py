class S4(_Base):
    """S4：实测 —— O(T²) 是物理定律。
    页1（0.00-8.15）实验设定：PyTorch 标准注意力，从 1K 往上测；
    页2（8.15-16.16）延迟曲线：1K 0.1s → 2K 0.38s → 4K 1.53s（翻 15 倍爆点）；
    页3（16.16-26.67）32K 崩溃：电脑黑屏重启；
    页4（26.67-37.28）32K×32K 矩阵吃光内存 → O(T²) 不是理论是物理定律 → 翻不过去？悬念。
    时间轴 = s4 锚点表（37.28s）；数字走 counter_value / 曲线 Create。"""

    def construct(self):
        self.bg()
        self.footer()
        footer_mob = self.mobjects[-1]
        head = t("实测：O(T²) 是物理定律", 38, YELL, "BOLD").to_edge(UP, buff=1.2)
        self.play(type_in(head, run_time=1.1))  # 0.00-1.10

        # ---------- 页1（0.00-8.15）：实验设定 ----------
        when = t("写这篇文章时，我做了个实验", 32, MUTED)
        fit(when, 0.9)
        code = _card("PyTorch 实现标准注意力", 6.0, 2.3, CYAN, WHITE, 32, CARD_FILL, "BOLD")
        from1k = t("从 1K 序列开始往上测", 40, WHITE, "BOLD")
        fit(from1k, 0.9)
        seq = t("1K → 4K → 32K → …", 30, CYAN, "BOLD")
        fit(seq, 0.9)
        page1 = page_stack(when, code, from1k, seq, buff=1.15)
        layout_page(page1)

        self.at(1.86)
        self.play(type_in(when, run_time=0.7))  # 1.86-2.56（写这篇文章时，）
        self.at(3.37)
        self.play_scroll_unroll(code, run_time=0.9)  # 3.37-4.27（我用PyTorch实现标准注意力，）
        self.at(5.99)
        self.play(type_in(from1k, run_time=0.8))  # 5.99-6.79（从1K序列往上测。）
        self.at(6.79)
        self.play(type_in(seq, run_time=0.6))  # 6.79-7.39
        self.at(8.15)
        self.play(FadeOut(VGroup(when, code, from1k, seq), shift=UP * 0.03), run_time=0.3)  # 8.15-8.45 换页

        # ---------- 页2（8.15-16.16）：延迟曲线 ----------
        axes = Axes(
            x_range=[0, 4.5, 1], y_range=[0, 1.8, 0.5],
            x_length=5.6, y_length=4.4,
            axis_config={"color": MUTED, "stroke_width": 2.5,
                         "include_ticks": False, "include_tip": True},
        )
        xlab = t("序列长度 (K)", 22, MUTED).next_to(axes, DOWN, buff=0.25)
        ylab = t("延迟 (s)", 22, MUTED).next_to(axes, LEFT, buff=0.3)
        curve = axes.plot(lambda x: 0.1 * x ** 2, x_range=[0.5, 4.2], color=YELL, stroke_width=4)
        p1 = Dot(axes.c2p(1, 0.1), color=YELL, radius=0.1)
        p2 = Dot(axes.c2p(2, 0.38), color=YELL, radius=0.1)
        p3 = Dot(axes.c2p(4, 1.53), color=YELL, radius=0.1)
        lab1 = t("1K 0.1s", 24, WHITE).next_to(p1, UP, buff=0.15)
        lab2 = t("2K 0.38s", 24, WHITE).next_to(p2, UP, buff=0.15)
        lab3 = t("4K 1.53s", 24, WHITE).next_to(p3, UP, buff=0.15)
        x15 = t("长度翻 4 倍，延迟翻 15 倍", 40, YELL, "BOLD")
        fit(x15, 0.9)
        # 曲线/点/标签必须与 axes 同组移动（2026-08-19 修复：原不在 page2 内，
        # layout_page 移动 axes 后曲线与点相对 x 轴错位 0.68 数据单位）
        axes_grp = VGroup(axes, curve, p1, p2, p3, lab1, lab2, lab3)
        page2 = page_stack(axes_grp, xlab, x15, buff=0.95)
        layout_page(page2)
        ylab.next_to(axes, LEFT, buff=0.3)

        self.at(8.45)
        self.play(Create(axes), run_time=0.6)  # 8.45-9.05（1K，）
        self.at(9.05)
        self.play(FadeIn(p1, shift=DOWN * 0.05), run_time=0.3)  # 9.05-9.35
        self.at(9.35)
        self.play(type_in(lab1, run_time=0.4))  # 9.35-9.75（0.1秒。）
        self.at(10.15)
        self.play(FadeIn(p2, shift=DOWN * 0.05), run_time=0.3)  # 10.15-10.45（2K，）
        self.at(10.45)
        self.play(type_in(lab2, run_time=0.4))  # 10.45-10.85（0.38秒。）
        self.at(12.35)
        self.play(FadeIn(p3, shift=DOWN * 0.05), run_time=0.3)  # 12.35-12.65（4K，）
        self.at(12.65)
        self.play(type_in(lab3, run_time=0.4))  # 12.65-13.05（1.53秒——长度翻4倍，）
        self.at(13.22)
        self.play(Create(curve), run_time=1.0)  # 13.22-14.22 抛物线画出
        self.at(14.55)
        self.play(type_in(x15, run_time=0.9))  # 14.55-15.45（延迟翻了15倍。）
        self.at(15.45)
        self.emphasize(x15, run_time=0.6)  # 15.45-16.05
        self.at(16.16)
        self.play(FadeOut(VGroup(axes, xlab, ylab, curve, p1, p2, p3, lab1, lab2, lab3, x15),
                          shift=UP * 0.03), run_time=0.3)  # 16.16-16.46 换页

        # ---------- 页3（16.16-26.67）：32K 崩溃 ----------
        then = t("然后，我试着跑 32K", 40, WHITE, "BOLD")
        fit(then, 0.9)
        btn = _card("32K", 2.6, 1.6, YELL, WHITE, 48, CARD_FILL, "BOLD")
        crash = t("电脑，直接崩了", 48, RED, "BOLD")
        fit(crash, 0.9)
        noerr = t("没有报错，没有警告", 32, WHITE)
        fit(noerr, 0.9)
        black = t("就是黑屏重启", 44, WHITE, "BOLD")
        fit(black, 0.9)
        page3 = page_stack(then, btn, crash, noerr, black, buff=0.8)
        layout_page(page3)

        self.at(16.46)
        self.play(type_in(then, run_time=0.8))  # 16.46-17.26（然后，）
        self.at(18.38)
        self.play_scroll_unroll(btn, run_time=0.7)  # 18.38-19.08（我试着跑32K。电脑，）
        self.at(19.08)
        self.emphasize(btn, run_time=0.6)  # 19.08-19.68
        self.at(20.87)
        self.play(type_in(crash, run_time=0.9))  # 20.87-21.77（直接崩了。没有报错，）
        self.at(21.77)
        cross_btn = self.play_red_cross(btn, run_time=0.65)  # 21.77-22.42 32K 被否
        self.at(22.59)
        self.play(type_in(noerr, run_time=0.8))  # 22.59-23.39（没有警告，）
        self.at(24.75)
        self.play(type_in(black, run_time=0.9))  # 24.75-25.65（就是黑屏重启。）
        self.at(25.65)
        screen = Rectangle(width=FW, height=FH, fill_color="#000000", fill_opacity=0.92, stroke_width=0)
        self.play(FadeIn(screen, run_time=0.5))  # 25.65-26.15 黑屏盖住
        self.at(26.67)
        self.play(FadeOut(VGroup(then, btn, crash, noerr, black, cross_btn, screen),
                          shift=UP * 0.03), run_time=0.3)  # 26.67-26.97 换页

        # ---------- 页4（26.67-37.28）：矩阵吃内存 + 物理定律 ----------
        mat = t("32K × 32K 的注意力矩阵", 40, WHITE, "BOLD")
        fit(mat, 0.9)
        eat = t("光这一个，就吃掉了所有内存", 34, RED, "BOLD")
        fit(eat, 0.9)
        nottheory = t("O(T²) 不是理论", 44, WHITE, "BOLD")
        fit(nottheory, 0.9)
        law = t("是物理定律", 72, YELL, "BOLD")
        fit(law, 0.9)
        q = t("那这道墙，真的翻不过去吗？", 40, CYAN, "BOLD")
        fit(q, 0.9)
        page4 = page_stack(mat, eat, nottheory, law, q, buff=0.95)
        layout_page(page4)

        self.at(26.97)
        self.play(type_in(mat, run_time=0.8))  # 26.97-27.77（32K的注意力矩阵，光这一个，）
        self.at(28.73)
        self.play(type_in(eat, run_time=0.7))  # 28.73-29.43（就吃掉了所有内存。）
        self.at(29.75)
        self.play(type_in(nottheory, run_time=0.9))  # 29.75-30.65（O(T²)不是理论，）
        self.at(31.88)
        self.play(type_in(law, run_time=1.0))  # 31.88-32.88（是物理定律。）
        self.at(32.88)
        self.emphasize(law, mode="circumscribe", run_time=0.8)  # 32.88-33.68
        self.at(33.74)
        self.play(type_in(q, run_time=0.9))  # 33.74-34.64（那这道墙，真的翻不过去吗？）
        self.at(34.64)
        self.breathe(q, scale=1.03, run_time=1.0, loops=1)  # 34.64-35.64
        self.at(35.64)
        self.transition_out(head, footer_mob, mat, eat, nottheory, law, q)  # 35.64-36.24
        self.pad_to_voice()


