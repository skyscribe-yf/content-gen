class S2(_Base):
    """S2：墙一 —— 握手 O(T²)。
    页1（0.00-7.75）注意力定义 + 会议室概念图；
    页2（7.75-17.31）10 人 45 次全连接图 → 100 人 4950 次爆点；
    页3（17.31-26.68）翻 10 倍 → 翻 100 倍 → 第一道墙 O(T²)；
    页4（26.68-36.82）100 万字 = 1 万字计算量的 1 万倍 → GPU 扛不住 → 第二道墙悬念。
    时间轴 = s2 锚点表（36.82s）；数字走 counter_value / Create。"""

    def construct(self):
        self.bg()
        self.footer()
        footer_mob = self.mobjects[-1]
        head = t("第一道墙：握手爆炸", 38, YELL, "BOLD").to_edge(UP, buff=1.2)
        self.play(type_in(head, run_time=1.1))  # 0.00-1.10

        # ---------- 页1（0.00-7.75）：注意力定义 + 会议室概念图 ----------
        defn = t("每个词，都要回头看之前所有的词", 30, WHITE)
        fit(defn, 0.9)
        img = ImageMobject("img/handshake-round.png")
        img.scale_to_fit_width(5.2)
        cap = t("想象一个会议室", 30, CYAN, "BOLD")
        fit(cap, 0.9)
        page1 = page_stack(defn, img, cap, buff=0.8)
        layout_page(page1)

        self.at(2.36)
        self.play(type_in(defn, run_time=1.0))  # 2.36-3.36（每个词，都要回头看之前所有的词。）
        self.at(6.07)
        self.play(FadeIn(img, shift=DOWN * 0.05), run_time=0.6)  # 6.07-6.67（想象一个会议室。）
        self.at(6.67)
        self.play(type_in(cap, run_time=0.6))  # 6.67-7.27
        self.at(7.75)
        self.play(FadeOut(Group(defn, img, cap), shift=UP * 0.03), run_time=0.3)  # 7.75-8.05 换页

        # ---------- 页2（7.75-17.31）：10 人 45 次 → 100 人 4950 次 ----------
        lab10 = t("10 个人开会", 40, WHITE, "BOLD")
        fit(lab10, 0.9)
        # 10 点圆周均匀分布 + 全连接 45 线（2026-08-19 打磨：原两行排布改圆形）
        pts10 = VGroup(*[Dot(radius=0.15, color=CYAN) for _ in range(10)])
        for i, p in enumerate(pts10):
            ang = 2 * PI * i / 10 - PI / 2
            p.move_to(1.8 * np.array([np.cos(ang), np.sin(ang), 0]))
        cnt10_ph = Rectangle(width=2.6, height=1.6, fill_opacity=0.0, stroke_opacity=0.0)
        cnt10_row = VGroup(t("一共", 30, WHITE), cnt10_ph).arrange(RIGHT, buff=0.3, aligned_edge=ORIGIN)
        full_lab = t("全连接：两两握手", 26, MUTED)
        page2 = page_stack(lab10, full_lab, pts10, cnt10_row, buff=0.8)
        layout_page(page2)
        # 连线在整页定位后创建（端点基于 pts10 最终坐标，2026-08-19 修复错位）
        lines10 = VGroup()
        for i in range(10):
            for j in range(i + 1, 10):
                lines10.add(Line(pts10[i].get_center(), pts10[j].get_center(),
                                 color=MUTED, stroke_width=2.5))

        self.at(8.05)
        self.play(type_in(lab10, run_time=0.7))  # 8.05-8.75（10个人开会，）
        self.at(8.75)
        self.play(type_in(full_lab, run_time=0.4))  # 8.75-9.15
        self.at(9.21)
        self.play(FadeIn(pts10, shift=DOWN * 0.05), run_time=0.5)  # 9.21-9.71（每个人要跟其他9个人握手，）
        self.at(9.71)
        self.play(*[Create(l) for l in lines10], run_time=1.2, lag_ratio=0.15)  # 9.71-10.91 45 线逐条画出
        self.at(11.88)
        self.play(type_in(cnt10_row[0], run_time=0.4))  # 11.88-12.28（一共45次。）
        self.at(12.28)
        cnt45 = self.counter_value(0, 45, suffix=" 次", size=52, color=YELL,
                                   anchor=cnt10_ph, run_time=0.6)  # 12.28-12.88
        self.at(13.65)
        self.play(FadeOut(VGroup(lab10, full_lab, pts10, lines10, cnt10_row, cnt45),
                          shift=UP * 0.03), run_time=0.3)  # 13.65-13.95 换页

        # ---------- 页2b（13.65-17.31）：100 人 4950 次爆点 ----------
        lab100 = t("100 个人开会？", 48, YELL, "BOLD")
        fit(lab100, 0.9)
        # 大圆 + 20 点全连接大弧（12点→10点，300°）+ 小点弧（10点→12点，不连线）
        # 2026-08-19 二次打磨：替换「6 点 + 省略号」方案
        big_circle = Circle(radius=2.3, color=MUTED, stroke_width=2.5)
        cnt100_ph = Rectangle(width=3.0, height=1.4, fill_opacity=0.0, stroke_opacity=0.0)
        page2b = page_stack(lab100, big_circle, cnt100_ph, buff=0.95)
        layout_page(page2b)
        # 点在整页定位后创建（基于大圆最终坐标）
        ctr = big_circle.get_center()
        # 20 个大点：12点(PI/2) 顺时针 300° 到 10点(-7PI/6)，两两全连接
        big_pts = VGroup(*[Dot(ctr + 2.3 * np.array([np.cos(PI / 2 - (5 * PI / 3) * i / 19),
                                                      np.sin(PI / 2 - (5 * PI / 3) * i / 19), 0]),
                              color=CYAN, radius=0.11) for i in range(20)])
        links = VGroup()
        for i in range(20):
            for j in range(i + 1, 20):
                links.add(Line(big_pts[i].get_center(), big_pts[j].get_center(),
                               color=MUTED, stroke_width=1.2, stroke_opacity=0.45))
        # 12 个小点：10点(5PI/6) 逆时针到 12点(PI/2)，不连线
        small_pts = VGroup()
        for i in range(12):
            ang = 5 * PI / 6 - (PI / 3) * i / 11
            small_pts.add(Dot(ctr + 2.25 * np.array([np.cos(ang), np.sin(ang), 0]),
                              color=CYAN, radius=0.055))

        self.at(13.95)
        self.play(type_in(lab100, run_time=0.8))  # 13.95-14.75（100个人开会？）
        self.at(15.29)
        self.play(Create(big_circle), run_time=0.3)  # 15.29-15.59 大圆画出
        self.at(15.59)
        # 20 点 + 45 线快速铺开（lag_ratio 小 → 密密麻麻快速连出）
        self.play(FadeIn(big_pts, run_time=0.2),
                  *[Create(l) for l in links], run_time=0.5, lag_ratio=0.07)  # 15.59-16.09
        self.at(16.09)
        self.play(FadeIn(small_pts, run_time=0.2))  # 16.09-16.29 小点弧
        self.at(16.29)
        cnt4950 = self.counter_value(0, 4950, suffix=" 次", size=56, color=YELL,
                                     anchor=cnt100_ph, run_time=0.7)  # 16.29-16.99
        self.at(17.31)
        self.play(FadeOut(VGroup(lab100, big_circle, big_pts, links, small_pts, cnt4950),
                          shift=UP * 0.03), run_time=0.3)  # 17.31-17.61 换页

        # ---------- 页3（17.31-26.68）：翻 10 倍 → 翻 100 倍 → 第一道墙 ----------
        t10 = t("人数翻 10 倍", 40, WHITE, "BOLD")
        fit(t10, 0.9)
        t100 = t("握手数翻 100 倍", 52, YELL, "BOLD")
        fit(t100, 0.9)
        wall = _card("这就是第一道墙", 5.8, 1.8, CYAN, WHITE, 34, CARD_FILL, "BOLD")
        n1 = t("序列长度翻 N 倍", 32, WHITE)
        n2_base = t("计算量翻 N", 34, WHITE)
        n2_sup = sup("N", "2", 34, 19, YELL, "BOLD")  # 上标独立，布局后定位
        page3 = page_stack(t10, t100, wall, n1, n2_base, buff=0.95)
        layout_page(page3)
        n2_sup.shift(n2_base[-1].get_center() - n2_sup[0].get_center())  # 上标组整体对齐正文 N（N→N² 演变）

        self.at(17.61)
        self.play(type_in(t10, run_time=0.7))  # 17.61-18.31（人数翻10倍，）
        self.at(19.00)
        self.play(type_in(t100, run_time=0.9))  # 19.00-19.90（握手数翻100倍。）
        self.at(19.90)
        self.emphasize(t100, run_time=0.6)  # 19.90-20.50
        self.at(21.00)
        self.play_scroll_unroll(wall, run_time=0.8)  # 21.00-21.80（这就是第一道墙：）
        self.at(22.76)
        self.play(type_in(n1, run_time=0.7))  # 22.76-23.46（序列长度翻N倍，）
        self.at(24.39)
        self.play(type_in(n2_base, run_time=0.9))  # 24.39-25.29（计算量翻N的平方倍。）先出 N
        self.at(25.29)
        self.play(FadeIn(n2_sup[1], run_time=0.4))  # 25.29-25.69 N 变 N²（上标 2 出现）
        self.at(25.69)
        self.emphasize(VGroup(n2_base, n2_sup[1]), run_time=0.6)  # 25.69-26.29
        self.at(26.68)
        self.play(FadeOut(VGroup(t10, t100, wall, n1, n2_base, n2_sup[1]),
                          shift=UP * 0.03), run_time=0.3)  # 26.68-26.98 换页

        # ---------- 页4（26.68-36.82）：1 万倍 + GPU 扛不住 + 第二道墙悬念 ----------
        ctx = t("100 万字的上下文", 36, WHITE, "BOLD")
        fit(ctx, 0.9)
        mult_ph = Rectangle(width=3.4, height=1.5, fill_opacity=0.0, stroke_opacity=0.0)
        mult_row = VGroup(t("计算量是 1 万字的", 30, WHITE), mult_ph).arrange(RIGHT, buff=0.3, aligned_edge=ORIGIN)
        gpu = t("GPU 再快，也扛不住", 42, RED, "BOLD")
        fit(gpu, 0.9)
        next_wall = t("还有第二道墙等着…", 40, CYAN, "BOLD")
        fit(next_wall, 0.9)
        o2 = t("O(T²) 的抛物线，肉眼可见", 28, MUTED)
        fit(o2, 0.9)
        page4 = page_stack(ctx, mult_row, o2, gpu, next_wall, buff=0.95)
        layout_page(page4)

        self.at(26.98)
        self.play(type_in(ctx, run_time=0.7))  # 26.98-27.68（100万字的上下文，）
        self.at(27.68)
        self.play(type_in(o2, run_time=0.5))  # 27.68-28.18
        self.at(28.60)
        self.play(type_in(mult_row[0], run_time=0.6))  # 28.60-29.20（计算量是1万字的1万倍。）
        self.at(29.20)
        mult = self.counter_value(0, 10000, suffix=" 倍", size=56, color=YELL,
                                  anchor=mult_ph, run_time=0.8)  # 29.20-30.00
        self.at(30.00)
        self.emphasize(mult, run_time=0.6)  # 30.00-30.60
        self.at(31.14)
        self.play(type_in(gpu, run_time=0.9))  # 31.14-32.04（GPU再快，也扛不住。）
        self.at(32.04)
        cross_gpu = self.play_red_cross(gpu, run_time=0.65)  # 32.04-32.69 GPU 被否
        self.at(33.82)
        self.play(type_in(next_wall, run_time=0.8))  # 33.82-34.62（可就算算得动，还有第二道墙等着。）
        self.at(34.62)
        self.breathe(next_wall, scale=1.03, run_time=1.0, loops=1)  # 34.62-35.62
        self.at(35.62)
        self.transition_out(head, footer_mob, ctx, mult_row, mult, o2, gpu, cross_gpu, next_wall)  # 35.62-36.22
        self.pad_to_voice()


