class S3(_Base):
    """S3：为什么 GRPO 成了开源社区的新默认？
    三原因 → 典型 RLHF 四份权重 vs GRPO 一到两份 → 70B 显存账本（140/560/140-280GB）。
    时间轴锚点 = tts/sentence-boundaries.json s3 句级边界（口播实测，禁止预估）。
    数字动效：grow_bar 对比条 + 数字滚动；无概念图（本场景是数字/结构内容，走脚本画图）。
    """

    def _cnt(self, start, end, suffix="", size=56, color=YELL,
             pos=None, run_time=0.9):
        """数字滚动（counter_value 的定位先行版）：
        helper 版先 add 在原点滚动、返回后才 next_to 跳位（QA A9 中间态风险），
        本版本在滚动前通过 pos(grp) 先摆位。suffix 用 updater 跟随数字右缘
        （DecimalNumber 变宽时左缘固定、右缘右移，静态 suffix 会被压到）。"""
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
        self.bg()
        footer = t("数解AI · 大模型原理", 20, MUTED).to_edge(DOWN, buff=1.15)
        self.add(footer)
        head = t("为什么 GRPO 成了新默认？", 38, YELL, "BOLD").to_edge(UP, buff=1.2)
        self.play(type_in(head, run_time=1.1))
        self.breathe(head, scale=1.03, run_time=1.2, loops=1)  # 问句滞留全片，轻呼吸

        # ---- 段1（0-10.03）：原因有三 + 三张原因卡 ----
        cnt1_ph = Rectangle(width=2.2, height=0.8, fill_opacity=0.0, stroke_opacity=0.0)
        cards1 = VGroup(
            boxed("少训练\n一套大模型", 2.15, 2.0, CYAN, 24, 0.15, weight="BOLD"),
            boxed("少一组\n估值超参", 2.15, 2.0, GREEN, 24, 0.15, weight="BOLD"),
            boxed("实现\n还简单", 2.15, 2.0, YELL, 24, 0.15, weight="BOLD"),
        )
        cards1.arrange(RIGHT, buff=0.35)
        layout_page(page_stack(cnt1_ph, cards1, buff=0.9))
        self.at(3.16)
        cnt1 = self._cnt(0, 3, " 个原因", size=56,
                         pos=lambda g: g.move_to(cnt1_ph))
        self.at(4.52)
        self.play_scroll_unroll(cards1[0], run_time=1.2)
        self.at(6.40)
        self.play_scroll_unroll(cards1[1], run_time=1.2)
        self.at(8.07)
        self.play_scroll_unroll(cards1[2], run_time=1.2)

        # ---- 段2（10.03-17.13）：典型 RLHF 要同时扛四份模型权重 ----
        self.at(10.03)
        self.play(FadeOut(VGroup(cnt1, cards1), shift=UP * 0.03), run_time=0.3)
        lab2 = t("典型 RLHF 要同时扛", 27, CYAN, "BOLD")
        chips2 = VGroup(*[boxed(w, 1.55, 1.05, CYAN, 22, 0.15, weight="BOLD")
                          for w in ("策略", "critic", "奖励", "参考")])
        chips2.arrange(RIGHT, buff=0.32)
        cnt2_ph = Rectangle(width=2.4, height=0.8, fill_opacity=0.0, stroke_opacity=0.0)
        layout_page(page_stack(lab2, chips2, cnt2_ph, buff=0.7))
        self.play(type_in(lab2, run_time=0.8))
        self.play_scroll_unroll(chips2[0], run_time=1.2)
        self.at(13.19)
        # 三枚权重 chip 在 13.19-15.46 窗口内逐枚拉幕（窗口仅 2.27s，压到 0.72 节奏）
        self.play_scroll_unroll(chips2[1], run_time=0.72)
        self.play_scroll_unroll(chips2[2], run_time=0.72)
        self.play_scroll_unroll(chips2[3], run_time=0.72)
        self.at(15.46)
        cnt2 = self._cnt(0, 4, " 份权重", size=64,
                         pos=lambda g: g.move_to(cnt2_ph))
        self.emphasize(cnt2, mode="indicate", run_time=0.6)  # 「四份」爆点
        self.at(17.13)
        self.play(FadeOut(VGroup(lab2, chips2, cnt2), shift=UP * 0.03), run_time=0.3)

        # ---- 段3（17.13-21.49）：GRPO 用规则判分，只要一到两份 ----
        lab3 = t("GRPO 用规则判分", 27, GREEN, "BOLD")
        chips3 = VGroup(*[boxed(w, 1.6, 1.05, GREEN, 22, 0.15, weight="BOLD")
                          for w in ("策略", "参考")])
        chips3.arrange(RIGHT, buff=0.55)
        cnt3_ph = Rectangle(width=1.8, height=0.8, fill_opacity=0.0, stroke_opacity=0.0)
        layout_page(page_stack(lab3, chips3, cnt3_ph, buff=0.7))
        self.play(type_in(lab3, run_time=0.7))
        self.play_scroll_unroll(chips3[0], run_time=1.1)
        self.at(19.41)
        self.play_scroll_unroll(chips3[1], run_time=1.0)
        cnt3 = self._cnt(1, 2, " 份", size=56,
                         pos=lambda g: g.move_to(cnt3_ph))
        self.at(21.49)
        self.play(FadeOut(VGroup(lab3, chips3, cnt3), shift=UP * 0.03), run_time=0.3)

        # ---- 段4（21.49-29.98）：70B 显存账本 —— 1 份 140GB / 4 份 560GB / GRPO 140-280GB ----
        # （21.49 锚点已在上方 FadeOut 处消耗，后续动画直接续排，不再重复 at）
        # 三行条形图先摆进纵向带中心，再逐行生长；数值位置用透明占位先留好，避免生数后挤压
        rows4 = [
            (1.25, 2.35, CYAN, "70B · 1 份", 18),
            (5.0, 1.00, RED, "4 份权重", 18),
            (2.5, -0.35, GREEN, "GRPO 1–2 份", 16),
        ]
        bars, labs4, cnts4, spots4 = [], [], [], []
        for w, y, col, lab, fs in rows4:
            lb = t(lab, fs, WHITE)
            lb.move_to(np.array([- (FW / 2 - 0.5) + lb.width / 2, y, 0]))  # 左缘 x=-3.5
            labs4.append(lb)
            bar = Rectangle(width=w, height=0.55, color=col,
                            fill_color=col, fill_opacity=0.75)
            # 条左起点 -1.9：与标签右缘（-2.3）留 ≥0.3 缝（2026-08-16 用户反馈 01:22 重叠）
            bar.move_to(np.array([-1.9 + w / 2, y - 0.275, 0]))
            bars.append(bar)
            spot = Rectangle(width=1.35, height=0.5, fill_opacity=0.0, stroke_opacity=0.0)
            spot.move_to(np.array([bar.get_center()[0], y + 0.35, 0]))
            spots4.append(spot)
        layout_page(VGroup(*labs4, *bars, *spots4))
        self.play(type_in(labs4[0], run_time=0.5))
        self.add(bars[0])
        self.grow_bar(bars[0], ValueTracker(0), 1.25, run_time=0.9)
        cnts4.append(self._cnt(0, 140, "GB", size=30, color=CYAN,
                               pos=lambda g: g.move_to(spots4[0])))
        self.at(24.72)
        self.play(type_in(labs4[1], run_time=0.4))
        self.add(bars[1])
        self.grow_bar(bars[1], ValueTracker(0), 5.0, run_time=0.9)
        cnts4.append(self._cnt(0, 560, "GB", size=30, color=RED,
                               pos=lambda g: g.move_to(spots4[1]),
                               run_time=0.75))
        self.at(26.91)
        self.play(type_in(labs4[2], run_time=0.4))
        self.add(bars[2])
        self.grow_bar(bars[2], ValueTracker(0), 2.5, run_time=1.0)
        cnts4.append(self._cnt(140, 280, "GB", size=30, color=GREEN,
                               pos=lambda g: g.move_to(spots4[2])))

        self.transition_out(head, footer, VGroup(*labs4), VGroup(*bars),
                            VGroup(*cnts4), run_time=0.6)
        self.pad_to_voice()
