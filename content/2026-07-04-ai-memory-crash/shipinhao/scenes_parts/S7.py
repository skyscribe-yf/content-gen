class S7(_Base):
    """S7：第三招 —— MLA 压缩 KV cache。
    页1（0.00-11.02）标准 KV：每个 token 缓存完整 Key/Value，维度 6144；
    页2（11.02-18.11）MLA 用 512 维压缩表示（宽条→窄条 morph），压缩超 10 倍；
    页3（18.11-24.48）KV cache 从 5 TB 压到 78 GB：不可行 → 多卡能扛；
    页4（24.48-41.26）三招协同缺一不可：各拆一道墙 → 任何一招缺失都跑不动。
    时间轴 = s7 锚点表（41.26s）；数字走 counter_value / morph。"""

    def construct(self):
        self.bg()
        self.footer()
        footer_mob = self.mobjects[-1]
        head = t("第三招：MLA", 38, YELL, "BOLD").to_edge(UP, buff=1.2)
        self.play(type_in(head, run_time=1.1))  # 0.00-1.10

        # ---------- 页1（0.00-11.02）：标准 KV 6144 维 ----------
        mla = t("MLA", 76, YELL, "BOLD")
        fit(mla, 0.9)
        job = t("压缩 KV cache", 44, WHITE, "BOLD")
        fit(job, 0.9)
        std = t("标准 KV：每个 token 缓存完整的 Key、Value 向量", 36, WHITE)
        fit(std, 0.9)
        std_lab = t("标准 KV：完整缓存", 26, MUTED)
        fit(std_lab, 0.9)
        dim_ph = Rectangle(width=3.4, height=1.6, fill_opacity=0.0, stroke_opacity=0.0)
        dim_row = VGroup(t("维度", 30, WHITE), dim_ph).arrange(RIGHT, buff=0.3, aligned_edge=ORIGIN)
        page1 = page_stack(mla, job, std, std_lab, dim_row, buff=0.85)
        layout_page(page1)

        self.at(0.41)
        self.play(type_in(mla, run_time=0.8))  # 0.41-1.21（MLA，）
        self.at(2.72)
        self.play(type_in(job, run_time=0.7))  # 2.72-3.42（压缩KV cache。标准KV，）
        self.at(4.41)
        self.play(type_in(std, run_time=0.9))  # 4.41-5.31（每个token缓存完整的Key、Value向量，）
        self.at(5.31)
        self.play(type_in(std_lab, run_time=0.4))  # 5.31-5.71
        self.at(8.41)
        self.play(type_in(dim_row[0], run_time=0.4))  # 8.41-8.81（维度6144。）
        self.at(8.81)
        dim6144 = self.counter_value(0, 6144, size=56, color=YELL,
                                     anchor=dim_ph, run_time=0.8)  # 8.81-9.61
        self.at(11.02)
        self.play(FadeOut(VGroup(mla, job, std, std_lab, dim_row, dim6144),
                          shift=UP * 0.03), run_time=0.3)  # 11.02-11.32 换页

        # ---------- 页2（11.02-18.11）：6144 → 512 压缩 ----------
        how = t("MLA 用 512 维的压缩表示替代", 44, WHITE, "BOLD")
        fit(how, 0.9)
        wide = Rectangle(width=5.6, height=1.7, color=MUTED, fill_color=CARD_FILL2, fill_opacity=1.0)
        wide_lab = t("6144 维", 28, MUTED, "BOLD").next_to(wide, DOWN, buff=0.25)
        narrow = Rectangle(width=0.5, height=1.7, color=YELL, fill_color=YELL, fill_opacity=0.9)
        narrow_lab = t("512 维", 28, YELL, "BOLD").next_to(narrow, DOWN, buff=0.25)
        bars = VGroup(wide, wide_lab)
        unfold = t("需要时再展开", 32, MUTED)
        fit(unfold, 0.9)
        x10 = t("压缩超过 10 倍", 56, YELL, "BOLD")
        fit(x10, 0.9)
        page2 = page_stack(how, bars, unfold, x10, buff=1.05)
        layout_page(page2)
        narrow.move_to(wide.get_center())
        narrow_lab.next_to(narrow, DOWN, buff=0.25)

        self.at(11.32)
        self.play(type_in(how, run_time=0.9))  # 11.32-12.22（MLA用512维的压缩表示替代，）
        self.at(12.22)
        self.play(FadeIn(wide, shift=DOWN * 0.05), run_time=0.5)  # 12.22-12.72
        self.at(12.72)
        self.play(type_in(wide_lab, run_time=0.4))  # 12.72-13.12
        self.at(15.14)
        self.play(FadeOut(wide_lab, run_time=0.3))  # 15.14-15.44 旧标签先走
        self.morph_to(wide, narrow, run_time=0.9)  # 15.44-16.34 宽条→窄条
        self.at(16.34)
        self.play(type_in(narrow_lab, run_time=0.4))  # 16.34-16.74
        self.at(16.74)
        self.play(type_in(unfold, run_time=0.5))  # 16.74-17.24（需要时再展开——）
        self.play(type_in(x10, run_time=0.8))  # 17.24-18.04（压缩超10倍。1M上下文，）
        self.at(17.24)
        self.emphasize(x10, run_time=0.6)  # 17.24-17.84
        self.at(18.11)
        self.play(FadeOut(VGroup(how, wide, wide_lab, narrow, narrow_lab, unfold, x10),
                          shift=UP * 0.03), run_time=0.3)  # 18.11-18.41 换页

        # ---------- 页3（18.11-24.48）：5 TB → 78 GB ----------
        from5 = t("KV cache 从 5 TB", 38, WHITE, "BOLD")
        fit(from5, 0.9)
        to78 = t("压到 78 GB", 48, YELL, "BOLD")
        fit(to78, 0.9)
        b5_ph = Rectangle(width=6.0, height=0.8, fill_opacity=0.0, stroke_opacity=0.0)
        b78_ph = Rectangle(width=1.0, height=0.8, fill_opacity=0.0, stroke_opacity=0.0)
        row5 = VGroup(t("5 TB", 26, MUTED, "BOLD"), b5_ph).arrange(RIGHT, buff=0.4)
        row78 = VGroup(t("78 GB", 26, YELL, "BOLD"), b78_ph).arrange(RIGHT, buff=0.4)
        imp = t("从完全不可行", 32, MUTED)
        fit(imp, 0.9)
        ok = t("变成多卡能扛", 38, GREEN, "BOLD")
        fit(ok, 0.9)
        page3 = page_stack(from5, to78, row5, row78, imp, ok, buff=0.7)
        layout_page(page3)

        bar5 = Rectangle(width=6.0, height=0.8, color=MUTED, fill_color=MUTED, fill_opacity=0.9)
        bar78 = Rectangle(width=1.0, height=0.8, color=YELL, fill_color=YELL, fill_opacity=0.9)
        bar5.move_to(b5_ph.get_center())
        bar78.move_to(b78_ph.get_center())
        tr5 = ValueTracker(0)
        tr78 = ValueTracker(0)

        self.at(18.41)
        self.play(type_in(from5, run_time=0.7))  # 18.41-19.11（KV cache从5TB，）
        self.at(19.46)
        self.play(type_in(to78, run_time=0.8))  # 19.46-20.26（压到78GB。）
        self.at(20.26)
        # 柱子标签与条并行出现（2026-08-19 打磨：原 5 TB/78 GB 标签从未显示）
        self.grow_bar(bar5, tr5, 6.0, run_time=0.5,
                      extra_anims=[type_in(row5[0], run_time=0.4)])  # 20.26-20.76 5TB 长条+标签
        self.at(20.76)
        self.grow_bar(bar78, tr78, 1.0, run_time=0.4,
                      extra_anims=[type_in(row78[0], run_time=0.4)])  # 20.76-21.16 78GB 短条+标签
        self.at(21.30)
        self.play(type_in(imp, run_time=0.7))  # 21.30-22.00（从完全不可行，）
        self.at(22.00)
        cross_imp = self.play_red_cross(imp, run_time=0.65)  # 22.00-22.65 不可行被否
        self.at(23.09)
        self.play(type_in(ok, run_time=0.8))  # 23.09-23.89（变成多卡能扛。）
        self.at(23.89)
        mk_ok = self.play_mark("✔", ok, GREEN, run_time=0.5)  # 23.89-24.39
        self.at(24.48)
        self.play(FadeOut(VGroup(from5, to78, row5, row78, bar5, bar78, imp, cross_imp, ok, mk_ok),
                          shift=UP * 0.03), run_time=0.3)  # 24.48-24.78 换页

        # ---------- 页4（24.48-41.26）：三招协同缺一不可 ----------
        trio = t("三招协同", 40, WHITE, "BOLD")
        fit(trio, 0.9)
        must = t("缺一不可", 56, YELL, "BOLD")
        fit(must, 0.9)
        c1 = _card("DSA 拆掉注意力的平方项", 5.4, 1.3, CYAN, WHITE, 28, CARD_FILL, "BOLD")
        c2 = _card("IndexShare 拆掉 Indexer 的平方项", 5.4, 1.3, CYAN, WHITE, 28, CARD_FILL, "BOLD")
        c3 = _card("MLA 压掉 KV 的线性增长", 5.4, 1.3, CYAN, WHITE, 28, CARD_FILL, "BOLD")
        cards = VGroup(c1, c2, c3).arrange(DOWN, buff=0.35)
        miss = t("任何一招缺失，1M 上下文", 32, WHITE)
        fit(miss, 0.9)
        dead = t("都跑不动", 60, RED, "BOLD")
        fit(dead, 0.9)
        page4 = page_stack(trio, must, cards, miss, dead, buff=0.6)
        layout_page(page4)

        self.at(24.78)
        self.play(type_in(trio, run_time=0.7))  # 24.78-25.48（三招协同，）
        self.at(26.34)
        self.play(type_in(must, run_time=0.8))  # 26.34-27.14（缺一不可：）
        self.at(27.14)
        self.emphasize(must, run_time=0.6)  # 27.14-27.74
        self.at(28.63)
        self.play_scroll_unroll(c1, run_time=0.8)  # 28.63-29.43（DSA拆掉注意力的平方项，）
        self.at(29.43)
        mk1 = self.play_mark("✔", c1, GREEN, run_time=0.4)  # 29.43-29.83
        self.at(31.32)
        self.play_scroll_unroll(c2, run_time=0.8)  # 31.32-32.12（IndexShare拆掉Indexer的平方项，）
        self.at(32.12)
        mk2 = self.play_mark("✔", c2, GREEN, run_time=0.4)  # 32.12-32.52
        self.at(34.48)
        self.play_scroll_unroll(c3, run_time=0.7)  # 34.48-35.18（MLA压掉KV的线性增长。）
        self.at(35.18)
        mk3 = self.play_mark("✔", c3, GREEN, run_time=0.4)  # 35.18-35.58
        self.at(35.72)
        self.play(type_in(miss, run_time=0.8))  # 35.72-36.52（任何一招缺失，1M上下文，）
        self.at(38.34)
        self.play(type_in(dead, run_time=1.0))  # 38.34-39.34（都跑不动。）
        self.at(39.34)
        cross_dead = self.play_red_cross(dead, run_time=0.65)  # 39.34-39.99
        self.at(39.99)
        self.transition_out(head, footer_mob, trio, must, c1, c2, c3, mk1, mk2, mk3, miss, dead, cross_dead)  # 39.99-40.59
        self.pad_to_voice()


