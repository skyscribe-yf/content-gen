class S7(_Base):
    """S7：GRPO 的边界 —— 转折「不是万能」→ 长程轨迹概念图 → 步骤归因 → 零方差除零红叉 → 奖励黑客。
    时间轴 = tts 句级边界（s7 锚点表 32.911s，禁止预估）；
    生动化：①概念图 long-trajectory-round.png（FadeIn + 图下标注）+ ③transition_out；
    否定用 play_red_cross，质疑用 emphasize(wiggle)，emphasize 全场景 ≤2 次。"""

    def construct(self):
        # ---------- 全局：背景 + 页脚 + 标题（0.00-1.10）----------
        self.bg()
        self.footer()
        footer_mob = self.mobjects[-1]  # footer() 不返回引用，取最近 add 的 mob 供 transition_out 带走
        head = t("GRPO 的边界", 38, YELL, "BOLD").to_edge(UP, buff=1.2)
        self.play(type_in(head, run_time=1.1))  # 0.00-1.10

        # ---------- 页1（0.00-11.51）：转折爆点 + 长程轨迹概念图 ----------
        big = t("但 GRPO 不是万能的", 36, YELL, "BOLD")
        fit(big, 0.9)
        excl = VGroup(
            Line(UP * 0.42, DOWN * 0.06, color=YELL, stroke_width=14),
            Dot(DOWN * 0.32, radius=0.085, color=YELL),
        )  # 自绘黄色惊叹号（禁 emoji）
        excl.next_to(big, RIGHT, buff=0.22)
        excl.align_to(big, ORIGIN)
        big_row = VGroup(big, excl).set_x(0.0)

        img = ImageMobject("img/long-trajectory-round.png")
        img.scale_to_fit_width(4.3)  # 图为主：整页居中，底部仍留字幕安全缝
        cap = t("轨迹几百步，压缩后长度参差不齐", 26, WHITE)
        fit(cap, 0.9)
        layout_page(page_stack(big_row, img, cap, buff=0.42))
        img_grp = Group(img, cap)

        self.play(type_in(big, run_time=1.0),
                  FadeIn(excl, shift=UP * 0.05, run_time=0.5))  # 1.10-2.10（但 GRPO 不是万能的。转折爆点）
        self.at(2.15)
        self.play(FadeIn(img, shift=DOWN * 0.05), run_time=0.6)  # 2.15-2.75（长程任务里，）
        self.at(3.44)
        self.play(type_in(cap, run_time=1.0))  # 3.44-4.44（轨迹可能几百步，压缩后长度参差不齐）
        self.at(8.79)
        self.breathe(img_grp, scale=1.02, run_time=1.2, loops=1)  # 8.79-9.99 滞留期轻呼吸
        self.at(11.51)
        self.play(FadeOut(Group(big, excl, img, cap), shift=UP * 0.03), run_time=0.4)  # 11.51-11.91 换页（带图）

        # ---------- 页2（11.51-18.98）：步骤归因 ----------
        p2a = t("整段回答的相对分数，", 26, MUTED)
        fit(p2a, 0.9)
        p2b = t("越来越难回答：", 26, MUTED)
        fit(p2b, 0.9)
        q2 = t("到底哪一步做对了？", 36, YELL, "BOLD")
        fit(q2, 0.9)
        card_attr = boxed("步骤归因问题", 2.8, 0.8, YELL, 26, weight="BOLD")
        layout_page(page_stack(p2a, p2b, q2, card_attr, buff=0.55))

        self.play(type_in(p2a, run_time=0.9))  # 11.91-12.81（整段回答的相对分数，）
        self.at(13.45)
        self.play(type_in(p2b, run_time=0.8))  # 13.45-14.25（越来越难回答：）
        self.at(15.10)
        self.play(type_in(q2, run_time=1.0))  # 15.10-16.10（到底哪一步做对了？）
        self.at(16.79)
        self.play_scroll_unroll(card_attr, run_time=1.2)  # 16.79-17.99（这就是步骤归因问题。）
        self.emphasize(card_attr, mode="indicate", run_time=0.8)  # 17.99-18.79 爆点聚焦
        self.at(18.98)
        self.play(FadeOut(VGroup(p2a, p2b, q2, card_attr), shift=UP * 0.03), run_time=0.4)  # 18.98-19.38 换页

        # ---------- 页3（18.98-26.40）：零方差 —— std=0 除零失效 ----------
        card_zv = boxed("零方差", 2.2, 0.8, YELL, 28, weight="BOLD")
        formula = MathTex(r"\frac{r_i - \text{mean}}{\text{std}}",
                          tex_to_color_map={r"\text{mean}": MUTED, r"\text{std}": CYAN})
        if formula.width > 5.5:
            formula.set_width(5.5)
        small = t("全对或全错，标准差是零", 22, WHITE)
        res = t("归一化直接失效", 26, WHITE, "BOLD")
        fit(res, 0.9)
        layout_page(page_stack(card_zv, formula, small, res, buff=0.55))

        self.play_scroll_unroll(card_zv, run_time=1.0)  # 19.38-20.38（还有零方差：）
        self.at(20.60)
        self.play(FadeIn(formula, shift=DOWN * 0.05), run_time=0.6)  # 20.60-21.20（一组样本全对或全错，）
        self.play(type_in(small, run_time=0.9))  # 20.60-21.50（全对或全错，标准差是零）
        self.breathe(formula, scale=1.02, run_time=1.2, loops=1)  # 21.50-22.70 滞留期轻呼吸
        self.at(22.90)
        cross = self.play_red_cross(formula)  # 22.90-23.55（标准差是零 → std=0 除零失效）
        self.at(24.45)
        self.play(type_in(res, run_time=0.9))  # 24.45-25.35（归一化直接失效。）
        self.at(26.40)
        self.play(FadeOut(VGroup(card_zv, formula, small, cross, res), shift=UP * 0.03), run_time=0.4)  # 26.40-26.80 换页

        # ---------- 页4（26.40-32.91）：奖励黑客 ----------
        card_hack = _card("奖励黑客", 4.2, 1.4, RED, WHITE, 36, CARD_FILL, "BOLD")
        l1 = t("不是做对，", 32, WHITE)
        l2 = t("而是比同伴差得少", 42, YELL, "BOLD")
        fit(l2, 0.9)
        layout_page(page_stack(card_hack, l1, l2, buff=0.85))

        self.play_scroll_unroll(card_hack, run_time=1.2)  # 26.80-28.00（以及奖励黑客——模型学会的，）
        self.at(28.46)
        self.play(type_in(l1, run_time=0.9))  # 28.46-29.36（可能不是做对，）
        self.at(30.00)
        self.play(type_in(l2, run_time=1.0))  # 30.00-31.00（而是比同伴差得少。）
        self.emphasize(l2, mode="wiggle")  # 31.00-31.80 质疑语气

        # ---------- 结尾转场（带走全部可见元素）→ pad_to_voice ----------
        self.at(32.91)
        self.transition_out(head, footer_mob, card_hack, l1, l2)  # 32.91-33.51
        self.pad_to_voice()
