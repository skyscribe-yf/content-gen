class S6(_Base):
    """S6：第二招 —— IndexShare 递归稀疏化。
    页1（0.00-12.42）稀疏化可以递归：DSA 第一层 → IndexShare 第二层；
    页2（12.42-19.54）78 层只有 21 层跑 Indexer，57 层复用索引；
    页3（19.54-30.44）凭什么？跨层相似度 >0.8，4 层窗口内复用有效；
    页4（30.44-40.05）两招叠加 2.9 倍 → 计算墙翻过去 → 存储墙悬念。
    时间轴 = s6 锚点表（40.05s）；数字走 counter_value。"""

    def construct(self):
        self.bg()
        self.footer()
        footer_mob = self.mobjects[-1]
        head = t("第二招：IndexShare", 38, YELL, "BOLD").to_edge(UP, buff=1.2)
        self.play(type_in(head, run_time=1.1))  # 0.00-1.10

        # ---------- 页1（0.00-12.42）：稀疏化可以递归 ----------
        insight = t("最独家的洞察", 32, MUTED)
        fit(insight, 0.9)
        rec = t("稀疏化，可以递归", 68, YELL, "BOLD")
        fit(rec, 0.9)
        l1 = _card("第一层：DSA 稀疏化注意力", 5.8, 1.7, CYAN, WHITE, 30, CARD_FILL, "BOLD")
        l2 = _card("第二层：IndexShare 稀疏化 Indexer", 5.8, 1.7, CYAN, WHITE, 30, CARD_FILL, "BOLD")
        layers = VGroup(l1, l2).arrange(DOWN, buff=0.4)
        page1 = page_stack(insight, rec, layers, buff=0.95)
        layout_page(page1)

        self.at(3.05)
        self.play(type_in(insight, run_time=0.6))  # 3.05-3.65（这就是GLM-5.2最独家的洞察：）
        self.at(3.96)
        self.play(type_in(rec, run_time=1.0))  # 3.96-4.96（稀疏化，可以递归。）
        self.at(4.96)
        self.emphasize(rec, run_time=0.6)  # 4.96-5.56
        self.at(5.35)
        self.play_scroll_unroll(l1, run_time=0.8)  # 5.35-6.15（DSA是第一层稀疏化；）
        self.at(7.67)
        self.play_scroll_unroll(l2, run_time=0.9)  # 7.67-8.57（IndexShare是第二层——对Indexer，也做稀疏。）
        self.at(12.42)
        self.play(FadeOut(VGroup(insight, rec, layers), shift=UP * 0.03), run_time=0.3)  # 12.42-12.72 换页

        # ---------- 页2（12.42-19.54）：78 层 → 21 层 ----------
        lab78 = t("78 层里，只有 21 层跑 Indexer", 36, WHITE, "BOLD")
        fit(lab78, 0.9)
        # 78 个小方块（13 列 × 6 行），21 层点亮
        blocks = VGroup(*[Rectangle(width=0.4, height=0.4, color=MUTED,
                                    fill_color=CARD_FILL2, fill_opacity=1.0) for _ in range(78)])
        blocks.arrange_in_grid(rows=6, cols=13, buff=0.15)
        lit = blocks[:21]
        rest = blocks[21:]
        cnt_ph = Rectangle(width=3.0, height=1.0, fill_opacity=0.0, stroke_opacity=0.0)
        cnt_row = VGroup(t("剩下", 30, WHITE), cnt_ph).arrange(RIGHT, buff=0.3, aligned_edge=ORIGIN)
        reuse = t("直接复用最近的索引", 34, CYAN, "BOLD")
        fit(reuse, 0.9)
        page2 = page_stack(lab78, blocks, cnt_row, reuse, buff=0.7)
        layout_page(page2)

        self.at(12.72)
        self.play(type_in(lab78, run_time=0.9))  # 12.72-13.62（78层里，只有21层跑Indexer，）
        self.at(16.00)
        self.play(*[b.animate.set_fill(YELL, opacity=0.9).set_color(YELL) for b in lit],
                  run_time=0.8, lag_ratio=0.1)  # 16.00-16.80 21 层点亮
        self.at(16.80)
        self.play(type_in(cnt_row[0], run_time=0.4))  # 16.80-17.20（剩下57层，）
        self.at(17.20)
        cnt57 = self.counter_value(0, 57, suffix=" 层", size=52, color=YELL,
                                   anchor=cnt_ph, run_time=0.5)  # 17.20-17.70
        self.at(17.45)
        self.play(type_in(reuse, run_time=0.9))  # 17.45-18.35（直接复用最近的索引。）
        self.at(19.54)
        self.play(FadeOut(VGroup(lab78, blocks, cnt_row, cnt57, reuse),
                          shift=UP * 0.03), run_time=0.3)  # 19.54-19.84 换页

        # ---------- 页3（19.54-30.44）：凭什么？相似度 >0.8 ----------
        why = t("凭什么？", 68, YELL, "BOLD")
        fit(why, 0.9)
        sim = t("相邻层的注意力模式高度相似", 36, WHITE)
        fit(sim, 0.9)
        sim_ph = Rectangle(width=2.6, height=1.6, fill_opacity=0.0, stroke_opacity=0.0)
        sim_row = VGroup(t("跨层相似度", 30, WHITE), sim_ph).arrange(RIGHT, buff=0.3, aligned_edge=ORIGIN)
        win = t("4 层窗口内复用依然有效", 36, GREEN, "BOLD")
        fit(win, 0.9)
        page3 = page_stack(why, sim, sim_row, win, buff=1.2)
        layout_page(page3)

        self.at(19.84)
        self.play(type_in(why, run_time=0.7))  # 19.84-20.54（凭什么？）
        self.at(20.84)
        self.play(type_in(sim, run_time=0.9))  # 20.84-21.74（相邻Transformer层的注意力模式高度相似，）
        self.at(24.76)
        self.play(type_in(sim_row[0], run_time=0.5))  # 24.76-25.26（跨层相似度超过0.8，）
        self.at(25.26)
        sim08 = self.counter_value(0, 0.8, decimals=1, size=56, color=YELL,
                                   anchor=sim_ph, run_time=0.6)  # 25.26-25.86
        self.at(25.86)
        self.emphasize(sim08, run_time=0.5)  # 25.86-26.36
        self.at(27.54)
        self.play(type_in(win, run_time=0.9))  # 27.54-28.44（4层窗口内复用依然有效。）
        self.at(30.44)
        self.play(FadeOut(VGroup(why, sim, sim_row, sim08, win),
                          shift=UP * 0.03), run_time=0.3)  # 30.44-30.74 换页

        # ---------- 页4（30.44-40.05）：2.9 倍 + 翻墙 + 悬念 ----------
        two = t("两招叠加，1M 上下文下", 34, WHITE)
        fit(two, 0.9)
        gain_ph = Rectangle(width=3.0, height=1.7, fill_opacity=0.0, stroke_opacity=0.0)
        gain_row = VGroup(t("每 token 计算量降低", 30, WHITE), gain_ph).arrange(RIGHT, buff=0.3, aligned_edge=ORIGIN)
        over = t("计算这道墙，翻过去了", 48, GREEN, "BOLD")
        fit(over, 0.9)
        q = t("那存储那道墙呢？", 44, CYAN, "BOLD")
        fit(q, 0.9)
        page4 = page_stack(two, gain_row, over, q, buff=1.2)
        layout_page(page4)

        self.at(30.74)
        self.play(type_in(two, run_time=0.9))  # 30.74-31.64（两招叠加，1M上下文下，）
        self.at(33.69)
        self.play(type_in(gain_row[0], run_time=0.6))  # 33.69-34.29（每token计算量降低2.9倍。）
        self.at(34.29)
        gain = self.counter_value(0, 2.9, decimals=1, suffix=" 倍", size=60, color=YELL,
                                  anchor=gain_ph, run_time=0.7)  # 34.29-34.99
        self.at(34.99)
        self.emphasize(gain, run_time=0.6)  # 34.99-35.59
        self.at(36.66)
        self.play(type_in(over, run_time=0.9))  # 36.66-37.56（计算这道墙，翻过去了。）
        self.at(37.56)
        mk_over = self.play_mark("✔", over, GREEN, run_time=0.5)  # 37.56-38.06
        self.at(38.84)
        self.play(type_in(q, run_time=0.8))  # 38.84-39.64（那存储那道墙呢？）
        self.at(39.64)
        self.transition_out(head, footer_mob, two, gain_row, gain, over, mk_over, q)  # 39.64-40.24
        self.pad_to_voice()


