class S8(_Base):
    """S8：GRPO 的进化 —— 变体三卡（Dr.GRPO/DAPO/GPG）→ 2026 仍是默认 →
    短/长任务分栏 → 爆点「算法选择，正在变得任务相关」→ RLVR 预告 →
    互动题（16 个输出 / 15 全错 / 1 全对 → 扩大 G 还是改 verifier）。
    时间轴 = tts 句级边界（s8 锚点表 38.612s）；数字走 counter_value。"""

    def _cnt(self, start, end, suffix="", size=52, color=YELL,
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
        # ---------- 全局：背景 + 页脚 + 标题（0.00-1.10）----------
        self.bg()
        self.footer()
        footer_mob = self.mobjects[-1]
        head = t("GRPO 的进化", 38, YELL, "BOLD").to_edge(UP, buff=1.2)
        self.play(type_in(head, run_time=1.1))  # 0.00-1.10

        # ---------- 页1（0.00-11.11）：变体三卡 ----------
        lead = t("2025 年，变体冒出一堆", 27, WHITE)
        fit(lead, 0.9)
        c1 = boxed("Dr.GRPO：修长度归一化", 5.6, 1.0, CYAN, 26)
        c2 = boxed("DAPO：按 token 汇总", 5.6, 1.0, GREEN, 26)
        c3 = boxed("GPG：连 KL 都不要", 5.6, 1.0, YELL, 26, weight="BOLD")
        layout_page(page_stack(lead, c1, c2, c3, buff=0.6))

        self.at(1.2)
        self.play(type_in(lead, run_time=0.9))  # 1.2-2.1
        self.at(2.74)
        self.play_scroll_unroll(c1, run_time=1.4)  # 2.74-4.14（Dr.GRPO 修长度归一化，）
        self.at(5.52)
        self.play_scroll_unroll(c2, run_time=1.4)  # 5.52-6.92（DAPO 按 token 汇总，）
        self.at(8.40)
        self.play_scroll_unroll(c3, run_time=1.4)  # 8.40-9.80（GPG 连 KL 都不要。）

        self.at(11.11)
        self.play(FadeOut(VGroup(lead, c1, c2, c3), shift=UP * 0.03), run_time=0.3)  # 11.11-11.41 换页

        # ---------- 页2（11.11-20.43）：2026 仍是默认 + 短/长分栏 ----------
        lab_default = t("2026 年依然是默认", 38, YELL, "BOLD")
        fit(lab_default, 0.9)
        sub_default = t("不是最好，是性价比无人能及", 30, WHITE)
        fit(sub_default, 0.9)
        sc = boxed("短任务：便宜又稳", 3.3, 1.5, GREEN, 28, weight="BOLD")
        lc = boxed("长任务：请回 critic", 3.3, 1.5, YELL, 28, weight="BOLD")
        row = VGroup(sc, lc).arrange(RIGHT, buff=0.5)
        layout_page(page_stack(lab_default, sub_default, row, buff=0.8))

        self.play(type_in(lab_default, run_time=0.9))  # 11.41-12.31（但 GRPO 在 2026 年依然是默认）
        self.at(14.16)
        self.play(type_in(sub_default, run_time=0.9))  # 14.16-15.06（是性价比无人能及。）
        self.at(15.50)
        self.play_scroll_unroll(sc, run_time=1.3)  # 15.50-16.80（短任务，便宜又稳；）
        self.at(17.59)
        self.play_scroll_unroll(lc, run_time=1.3)  # 17.59-18.89（长任务，再考虑请回 critic。）

        self.at(20.43)
        self.play(FadeOut(VGroup(lab_default, sub_default, sc, lc),
                          shift=UP * 0.03), run_time=0.3)  # 20.43-20.73 换页

        # ---------- 页3（20.43-25.71）：爆点 —— 算法选择正在变得任务相关 ----------
        kw1 = t("算法选择，", 52, WHITE, "BOLD")
        kw2 = t("正在变得任务相关", 88, YELL, "BOLD")
        fit(kw2, 0.9)
        layout_page(page_stack(kw1, kw2, buff=1.9))

        self.play(type_in(kw1, run_time=0.8))  # 20.73-21.53（算法选择，）
        self.at(22.31)
        self.play(type_in(kw2, run_time=1.0))  # 22.31-23.31（正在变得任务相关。）
        self.at(23.31)
        self.emphasize(kw2, mode="circumscribe", run_time=1.2)  # 23.31-24.51 画圈爆点
        self.at(25.71)
        self.play(FadeOut(VGroup(kw1, kw2), shift=UP * 0.03), run_time=0.3)  # 25.71-26.01 换页

        # ---------- 页4（25.71-38.61）：RLVR 预告 + 互动题 ----------
        card_next = boxed("下一篇：RLVR 可验证奖励", 5.2, 1.0, CYAN, 26, weight="BOLD")
        q_lab = t("留道题", 26, MUTED)

        # 三数字：16 个输出 / 15 全错 / 1 全对；用透明占位先整体居中，数字滚动原位落点
        n16_ph = Rectangle(width=2.5, height=0.8, fill_opacity=0.0, stroke_opacity=0.0)
        n15_ph = Rectangle(width=2.2, height=0.8, fill_opacity=0.0, stroke_opacity=0.0)
        n1_ph = Rectangle(width=1.5, height=0.8, fill_opacity=0.0, stroke_opacity=0.0)
        n15_ph.next_to(n16_ph, DOWN, buff=0.45, aligned_edge=LEFT)
        n1_ph.next_to(n15_ph, RIGHT, buff=0.9, aligned_edge=DOWN)
        nums_ph = VGroup(n16_ph, n15_ph, n1_ph)

        q_big = t("扩大 G，还是先改 verifier？", 30, YELL, "BOLD")
        fit(q_big, 0.9)
        cmt = t("评论区聊聊", 28, WHITE, "BOLD")
        layout_page(page_stack(card_next, q_lab, nums_ph, q_big, cmt, buff=0.5))

        self.play_scroll_unroll(card_next, run_time=1.3)  # 26.01-27.31（我们拆 RLVR。）
        self.at(28.45)
        self.play(type_in(q_lab, run_time=0.5))  # 28.45-28.95（留道题：）
        n16 = self._cnt(0, 16, suffix=" 个输出", size=52, color=YELL,
                        pos=lambda g: g.move_to(n16_ph),
                        run_time=1.0)  # 28.95-29.95（一个 prompt 生成 16 个输出，）
        n15 = self._cnt(0, 15, suffix=" 全错", size=52, color=RED,
                        pos=lambda g: g.move_to(n15_ph),
                        run_time=0.9)  # 29.95-30.85（15 个全错、）
        self.at(32.1)  # 1 个全对（台词 32.10-33.35，勿提前）
        n1 = self._cnt(0, 1, suffix=" 全对", size=52, color=GREEN,
                       pos=lambda g: g.move_to(n1_ph),
                       run_time=0.7)  # 32.1-32.8
        self.at(33.35)
        self.play(type_in(q_big, run_time=1.0))  # 33.35-34.35（你会扩大 G，还是先改 verifier？）
        self.at(35.92)
        self.play(type_in(cmt, run_time=0.8))  # 35.92-36.72（评论区聊聊。）
        self.at(37.0)
        self.emphasize(cmt, mode="indicate", run_time=0.7)  # 37.0-37.7

        # ---------- 结尾转场（带走全部可见元素）→ pad_to_voice ----------
        self.at(38.0)
        self.transition_out(head, footer_mob, card_next, q_lab, n16, n15, n1, q_big, cmt)
        self.pad_to_voice()
