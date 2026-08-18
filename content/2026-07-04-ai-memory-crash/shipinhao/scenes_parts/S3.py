class S3(_Base):
    """S3：墙二 —— KV cache 笔记写不下。
    页1（0.00-8.52）笔记比喻 + 笔记山概念图 + KV cache 定义；
    页2（8.52-19.12）每个 token 缓存 Key/Value（公式 T×d×L×2）→ 1M 传统方式要 5 TB；
    页3（19.12-25.93）H100 才 80 GB vs 5 TB → 大 60 倍爆点；
    页4（25.93-37.17）两道墙叠压：计算炸了、存储也炸了 → 数学上跑不动定格。
    时间轴 = s3 锚点表（37.17s）；数字走 counter_value / grow_bar。"""

    def construct(self):
        self.bg()
        self.footer()
        footer_mob = self.mobjects[-1]
        head = t("第二道墙：笔记写不下", 38, YELL, "BOLD").to_edge(UP, buff=1.2)
        self.play(type_in(head, run_time=1.1))  # 0.00-1.10

        # ---------- 页1（0.00-8.52）：笔记比喻 + 概念图 + KV cache ----------
        note = t("每次握完手，还得记笔记", 30, WHITE)
        fit(note, 0.9)
        img = ImageMobject("img/notebooks-round.png")
        img.scale_to_fit_width(4.4)
        full = t("笔记越多，本子写不下了", 40, RED, "BOLD")
        fit(full, 0.9)
        kv = _card("KV cache：显存爆炸的那道墙", 6.4, 1.5, CYAN, WHITE, 32, CARD_FILL, "BOLD")
        page1 = page_stack(note, img, full, kv, buff=0.7)
        layout_page(page1)

        self.at(1.60)
        self.play(type_in(note, run_time=0.8))  # 1.60-2.40（还得记笔记，）
        self.at(3.00)
        self.play(FadeIn(img, shift=DOWN * 0.05), run_time=0.6)  # 3.00-3.60（方便下次直接查。人越多，）
        self.at(4.94)
        self.play(type_in(full, run_time=0.9))  # 4.94-5.84（笔记越多，本子写不下了。）
        self.at(5.84)
        self.emphasize(full, run_time=0.6)  # 5.84-6.44
        self.at(7.01)
        self.play_scroll_unroll(kv, run_time=0.9)  # 7.01-7.91（这就是KV cache——显存爆炸的那道墙。）
        self.at(8.52)
        self.play(FadeOut(Group(note, img, full, kv), shift=UP * 0.03), run_time=0.3)  # 8.52-8.82 换页

        # ---------- 页2（8.52-19.12）：KV 公式 + 5 TB ----------
        tok = t("每个 token，都要缓存自己的", 32, WHITE)
        fit(tok, 0.9)
        kv_lab = t("Key 和 Value", 46, CYAN, "BOLD")
        fit(kv_lab, 0.9)
        formula = VGroup(t("KV cache = T × d × L × 2 bytes", 34, YELL, "BOLD")).arrange(RIGHT, buff=0.1)
        fit(formula, 0.9)
        query = t("供后续 token 直接查询", 26, MUTED)
        fit(query, 0.9)
        ctx = t("100 万字的上下文，传统方式记", 32, WHITE)
        fit(ctx, 0.9)
        tb_ph = Rectangle(width=3.2, height=1.5, fill_opacity=0.0, stroke_opacity=0.0)
        tb_row = VGroup(t("要", 32, WHITE), tb_ph).arrange(RIGHT, buff=0.3, aligned_edge=ORIGIN)
        page2 = page_stack(tok, kv_lab, formula, query, ctx, tb_row, buff=0.7)
        layout_page(page2)

        self.at(8.82)
        self.play(type_in(tok, run_time=0.8))  # 8.82-9.62（每个token，）
        self.at(12.23)
        self.play(type_in(kv_lab, run_time=0.7))  # 12.23-12.93（都要缓存自己的Key和Value。）
        self.at(12.93)
        self.play(type_in(formula, run_time=0.9))  # 12.93-13.83
        self.at(13.48)
        self.play(type_in(query, run_time=0.5))  # 13.48-13.98
        self.play(type_in(ctx, run_time=0.9))  # 13.98-14.88（100万字的上下文，传统方式记，）
        self.at(17.72)
        self.play(type_in(tb_row[0], run_time=0.4))  # 17.72-18.12（要5TB显存。）
        self.at(18.12)
        tb5 = self.counter_value(0, 5, suffix=" TB", size=64, color=YELL,
                                 anchor=tb_ph, run_time=0.6)  # 18.12-18.72
        self.at(19.12)
        self.play(FadeOut(VGroup(tok, kv_lab, formula, query, ctx, tb_row, tb5),
                          shift=UP * 0.03), run_time=0.3)  # 19.12-19.42 换页

        # ---------- 页3（19.12-25.93）：H100 80 GB vs 5 TB → 60 倍 ----------
        h100 = t("一张 H100 才 80 GB", 38, WHITE, "BOLD")
        fit(h100, 0.9)
        b80_ph = Rectangle(width=1.6, height=0.8, fill_opacity=0.0, stroke_opacity=0.0)
        b5t_ph = Rectangle(width=6.0, height=0.8, fill_opacity=0.0, stroke_opacity=0.0)
        row80 = VGroup(t("80 GB", 26, MUTED, "BOLD"), b80_ph).arrange(RIGHT, buff=0.4)
        row5t = VGroup(t("5 TB", 26, YELL, "BOLD"), b5t_ph).arrange(RIGHT, buff=0.4)
        big60 = t("大 60 倍", 72, YELL, "BOLD")
        fit(big60, 0.9)
        cmp_lab = t("显存对比", 26, MUTED)
        page3 = page_stack(h100, cmp_lab, row80, row5t, big60, buff=0.9)
        layout_page(page3)

        bar80 = Rectangle(width=1.6, height=0.8, color=MUTED, fill_color=MUTED, fill_opacity=0.9)
        bar5t = Rectangle(width=6.0, height=0.8, color=YELL, fill_color=YELL, fill_opacity=0.9)
        bar80.move_to(b80_ph.get_center())
        bar5t.move_to(b5t_ph.get_center())
        tr80 = ValueTracker(0)
        tr5t = ValueTracker(0)

        self.at(19.42)
        # 80 GB 标签与标题同时出现（2026-08-19 打磨：原 80GB 标签缺失、条出现过晚）
        self.grow_bar(bar80, tr80, 1.6, run_time=0.8,
                      extra_anims=[type_in(h100, run_time=0.8), type_in(row80[0], run_time=0.4)])  # 19.42-20.22
        self.at(20.22)
        self.play(type_in(cmp_lab, run_time=0.4))  # 20.22-20.62
        self.at(21.03)
        self.play(type_in(row5t[0], run_time=0.4))  # 21.03-21.43（5TB，）
        self.grow_bar(bar5t, tr5t, 6.0, run_time=0.7)  # 21.43-22.13 5TB 条长满
        self.at(23.40)
        self.play(type_in(big60, run_time=0.9))  # 23.40-24.30（比它大60倍。）
        self.at(24.30)
        self.emphasize(big60, run_time=0.6)  # 24.30-24.90
        self.at(25.93)
        self.play(FadeOut(VGroup(h100, cmp_lab, row80, row5t, bar80, bar5t, big60),
                          shift=UP * 0.03), run_time=0.3)  # 25.93-26.23 换页

        # ---------- 页4（25.93-37.17）：两道墙叠压 + 数学上跑不动 ----------
        stack = t("两道墙叠在一起", 40, WHITE, "BOLD")
        fit(stack, 0.9)
        w1 = _card("计算炸了", 3.4, 1.8, CYAN, WHITE, 32, CARD_FILL, "BOLD")
        w2 = _card("存储也炸了", 3.4, 1.8, CYAN, WHITE, 32, CARD_FILL, "BOLD")
        walls = VGroup(w1, w2).arrange(RIGHT, buff=0.5)
        why = t("大多数模型的记忆，只能停在几万字", 32, WHITE)
        fit(why, 0.9)
        notwant = t("不是不想扩", 32, WHITE)
        fit(notwant, 0.9)
        math = t("是数学上跑不动", 52, YELL, "BOLD")
        fit(math, 0.9)
        page4 = page_stack(stack, walls, why, notwant, math, buff=0.8)
        layout_page(page4)

        self.at(26.23)
        self.play(type_in(stack, run_time=0.7))  # 26.23-26.93（两道墙叠在一起：）
        self.at(27.67)
        self.play_scroll_unroll(w1, run_time=0.6)  # 27.67-28.27（计算炸了，）
        self.at(28.83)
        self.play_scroll_unroll(w2, run_time=0.6)  # 28.83-29.43（存储也炸了。）
        self.at(29.43)
        cross_walls = self.play_red_cross(VGroup(w1, w2), run_time=0.65)  # 29.43-30.08 两道墙都被否
        self.at(30.40)
        self.play(type_in(why, run_time=0.9))  # 30.40-31.30（这就是为什么大多数模型的记忆，）
        self.at(32.94)
        self.play(type_in(notwant, run_time=0.7))  # 32.94-33.64（只能停在几万字——不是不想扩，）
        self.at(34.82)
        self.play(type_in(math, run_time=1.0))  # 34.82-35.82（是数学上跑不动。）
        self.at(35.82)
        self.emphasize(math, mode="circumscribe", run_time=0.8)  # 35.82-36.62
        self.at(36.62)
        self.transition_out(head, footer_mob, stack, w1, w2, cross_walls, why, notwant, math)  # 36.62-37.22
        self.pad_to_voice()


