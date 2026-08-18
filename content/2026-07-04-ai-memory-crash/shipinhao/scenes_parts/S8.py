class S8(_Base):
    """S8：总结 + 翻墙概念图 + 品牌尾卡。
    页1（0.00-7.87）回到开头：问题 + 两道墙（注意力 O(T²) / KV cache 线性增长）红叉同时爆炸；
    页2（7.87-16.07）GLM-5.2 三招翻墙：wall-jump 概念图 + DSA→IndexShare→MLA 链依次亮 +
    1M 上下文「从数学上不可能→变成工程上可行」（红叉→✔）；
    页3（16.07-24.56）SWE-Marathon 回扣：1.0→13.0 counter + 双得分条（13×）+ +1200% +
    「不是魔法，是数学」爆点；
    页4（24.56-32.47）更深的启示：稀疏化→selector→下一个瓶颈 递归链 + 下一篇预告（推测解码）；
    页5（32.47-43.30）开放式问题 + 品牌尾卡（avatar + 关注「数解AI」+ 当期标题 + 查看公众号文章），
    尾卡停留到末帧（QA B5），不再滑出。
    时间轴 = s8 锚点表（43.30s）；数字走 counter_value / grow_bar。"""

    def construct(self):
        # ---------- 全局：背景 + 页脚 + 标题（0.00-1.10）----------
        self.bg()
        self.footer()
        footer_mob = self.mobjects[-1]
        head = t("回到开头", 38, YELL, "BOLD").to_edge(UP, buff=1.2)
        self.play(type_in(head, run_time=1.1))  # 0.00-1.10

        # ---------- 页1（0.00-7.87）：回到开头 —— 两道墙同时爆炸 ----------
        q = t("AI 为什么干到一半会崩？", 36, YELL, "BOLD")
        fit(q, 0.9)
        lead = t("因为记忆是有代价的", 28, WHITE)
        wall1 = _card("注意力 O(T²)", 5.6, 1.5, CYAN, WHITE, 32, CARD_FILL, "BOLD")
        wall2 = _card("KV cache 线性增长", 5.6, 1.5, CYAN, WHITE, 32, CARD_FILL, "BOLD")
        boom = t("在长序列下同时爆炸", 34, WHITE, "BOLD")
        layout_page(page_stack(q, lead, wall1, wall2, boom, buff=0.7))

        self.at(0.57)
        self.play(type_in(q, run_time=1.0))  # 0.57-1.57（AI为什么干到一半会崩？）
        self.at(1.98)
        self.play(type_in(lead, run_time=0.9))  # 1.98-2.88（因为记忆是有代价的——）
        self.at(2.88)
        self.play_scroll_unroll(wall1, run_time=1.2)  # 2.88-4.08（注意力的O(T²)，）
        self.at(4.06)
        self.play_scroll_unroll(wall2, run_time=1.2)  # 4.06-5.26（KV cache的线性增长，）
        self.at(6.17)
        self.play(type_in(boom, run_time=0.9))  # 6.17-7.07（在长序列下同时爆炸。）
        self.at(7.07)
        cross1 = self.play_red_cross(VGroup(wall1, wall2))  # 7.07-7.72 两道墙同时被否
        self.at(7.87)
        self.play(FadeOut(VGroup(q, lead, wall1, wall2, boom, cross1), shift=UP * 0.03), run_time=0.3)  # 7.87-8.17 换页

        # ---------- 页2（7.87-16.07）：GLM-5.2 三招翻墙 → 1M 不可能 → 可行 ----------
        img = ImageMobject("img/wall-jump-round.png")
        img.scale_to_fit_width(3.2)
        cap = t("GLM-5.2 用三招翻墙", 26, YELL, "BOLD")
        fit(cap, 0.9)
        c1 = _card("DSA", 1.4, 0.9, CYAN, WHITE, 30, CARD_FILL, "BOLD")
        c2 = _card("IndexShare", 2.4, 0.9, CYAN, WHITE, 30, CARD_FILL, "BOLD")
        c3 = _card("MLA", 1.4, 0.9, CYAN, WHITE, 30, CARD_FILL, "BOLD")
        chain = VGroup(c1, c2, c3).arrange(RIGHT, buff=0.8)
        big1m = t("1M 上下文", 44, YELL, "BOLD")
        fit(big1m, 0.9)
        impossible = t("从数学上不可能", 30, WHITE)
        feasible = t("变成工程上可行", 30, GREEN, "BOLD")
        layout_page(page_stack(img, cap, chain, big1m, impossible, feasible, buff=0.45))
        ar1 = t("→", 30, MUTED, "BOLD")  # 链箭头（布局后定位，装饰不参与整页 box）
        ar2 = t("→", 30, MUTED, "BOLD")
        ar1.move_to((c1.get_right() + c2.get_left()) / 2)
        ar2.move_to((c2.get_right() + c3.get_left()) / 2)

        self.at(8.17)
        self.play(FadeIn(img, shift=DOWN * 0.05), run_time=0.5)  # 8.17-8.67（GLM-5.2用三招翻墙，）
        self.at(8.67)
        self.play(type_in(cap, run_time=0.8))  # 8.67-9.47
        self.at(9.47)
        self.play(type_in(big1m, run_time=1.0))  # 9.47-10.47（把1M上下文，）
        self.play_scroll_unroll(c1, run_time=0.7)  # 10.47-11.17
        self.at(10.17)
        self.play_scroll_unroll(c2, run_time=0.7)  # 10.17-10.87
        self.at(10.87)
        self.play(type_in(ar1, run_time=0.3))  # 10.87-11.17
        self.at(11.17)
        self.play_scroll_unroll(c3, run_time=0.7)  # 11.17-11.87
        self.at(11.87)
        self.play(type_in(ar2, run_time=0.3))  # 11.87-12.17
        self.at(11.99)
        self.play(type_in(impossible, run_time=0.9))  # 11.99-12.89（从数学上不可能，）
        self.at(12.89)
        cross2 = self.play_red_cross(impossible)  # 12.89-13.54
        self.at(14.58)
        self.play(type_in(feasible, run_time=0.9))  # 14.58-15.48（变成工程上可行。）
        self.at(15.48)
        chk = self.play_mark("✔", feasible, GREEN, run_time=0.5)  # 15.48-15.98
        self.at(16.07)
        self.play(FadeOut(Group(img, cap, c1, c2, c3, ar1, ar2, big1m, impossible, cross2, feasible, chk),
                          shift=UP * 0.03), run_time=0.3)  # 16.07-16.37 换页

        # ---------- 页3（16.07-24.56）：SWE-Marathon 1.0 → 13.0 +1200% 回扣 ----------
        lab = t("SWE-Marathon 得分", 28, CYAN, "BOLD")
        fit(lab, 0.9)
        old = VGroup(t("1.0", 40, MUTED, "BOLD"), t("→", 40, MUTED, "BOLD")).arrange(RIGHT, buff=0.12)
        num_ph = Rectangle(width=2.2, height=0.9, fill_opacity=0.0, stroke_opacity=0.0)
        num_row = VGroup(old, num_ph).arrange(RIGHT, buff=0.35, aligned_edge=ORIGIN)
        b1_ph = Rectangle(width=0.4, height=0.5, fill_opacity=0.0, stroke_opacity=0.0)
        b2_ph = Rectangle(width=5.2, height=0.5, fill_opacity=0.0, stroke_opacity=0.0)
        row1 = VGroup(t("GLM-5.1", 20, MUTED, "BOLD"), b1_ph).arrange(RIGHT, buff=0.4)
        row2 = VGroup(t("GLM-5.2", 20, YELL, "BOLD"), b2_ph).arrange(RIGHT, buff=0.4)
        pct_ph = Rectangle(width=3.0, height=0.75, fill_opacity=0.0, stroke_opacity=0.0)
        magic = t("不是魔法，", 30, WHITE)
        math = t("是数学。", 48, YELL, "BOLD")
        fit(math, 0.9)
        layout_page(page_stack(lab, num_row, row1, row2, pct_ph, magic, math, buff=0.5))

        bar1 = Rectangle(width=0.4, height=0.5, color=MUTED, fill_color=MUTED, fill_opacity=0.9)
        bar2 = Rectangle(width=5.2, height=0.5, color=YELL, fill_color=YELL, fill_opacity=0.9)
        bar1.move_to(b1_ph.get_center())
        bar2.move_to(b2_ph.get_center())
        tr1 = ValueTracker(0)
        tr2 = ValueTracker(0)

        self.at(16.37)
        self.play(type_in(lab, run_time=0.5))  # 16.37-16.87（SWE-Marathon从1.0到13.0，）
        self.at(16.87)
        self.play(type_in(old, run_time=0.5))  # 16.87-17.37 先出旧值 1.0（淡化标签）
        self.at(17.37)
        num = self.counter_value(1.0, 13.0, decimals=1, size=64, color=YELL,
                                 anchor=num_ph, run_time=0.6)  # 17.37-17.97 1.0→13.0 滚动
        # 柱子标签与条并行出现（2026-08-19 打磨：原 GLM-5.1/5.2 标签从未显示）
        self.grow_bar(bar1, tr1, 0.4, run_time=0.5,
                      extra_anims=[type_in(row1[0], run_time=0.4)])  # 17.97-18.47 GLM-5.1 条+标签
        self.at(18.47)
        self.grow_bar(bar2, tr2, 5.2, run_time=0.5,
                      extra_anims=[type_in(row2[0], run_time=0.4)])  # 18.47-18.97 GLM-5.2 条+标签（13×）
        self.at(18.97)
        pct = self.counter_value(0, 1200, suffix="%", size=56, color=YELL,
                                 anchor=pct_ph, run_time=0.6)  # 19.27-19.87 涨了1200%
        plus = t("+", 56, YELL, "BOLD")
        plus.next_to(pct, LEFT, buff=0.08)
        plus.align_to(pct, ORIGIN)
        self.play(type_in(plus, run_time=0.3))  # 18.97-19.27
        self.at(19.55)
        self.play(type_in(magic, run_time=0.9))  # 19.55-20.45（不是魔法，）
        self.at(20.45)
        self.breathe(magic, scale=1.03, run_time=1.2, loops=1)  # 20.45-21.65
        self.at(22.68)
        self.play(type_in(math, run_time=1.0))  # 22.68-23.68（是数学。）
        self.at(23.68)
        self.emphasize(math, mode="circumscribe", run_time=0.8)  # 23.68-24.48 爆点
        self.at(24.56)
        self.play(FadeOut(VGroup(lab, old, num, bar1, bar2, pct, plus, magic, math),
                          shift=UP * 0.03), run_time=0.3)  # 24.56-24.86 换页

        # ---------- 页4（24.56-32.47）：更深的启示 + 下一篇预告 ----------
        lab2 = t("更深的启示", 30, MUTED)
        insight = t("稀疏化可以递归", 56, YELL, "BOLD")
        fit(insight, 0.9)
        n1 = cnode("稀疏化", CYAN, radius=0.85, fs=24)
        n2 = cnode("selector", CYAN, radius=0.85, fs=24)
        n3 = cnode("下一个瓶颈", RED, radius=0.95, fs=24)
        rec_chain = VGroup(n1, n2, n3).arrange(RIGHT, buff=0.9)
        next_lab = t("下一篇", 28, CYAN, "BOLD")
        next_card = _card("AI 为什么说话这么慢？", 6.4, 1.2, CYAN, WHITE, 26, CARD_FILL, "BOLD")
        sub = t("——推测解码的数学", 24, WHITE)
        layout_page(page_stack(lab2, insight, rec_chain, next_lab, next_card, sub, buff=0.6))
        ar3 = Arrow(n1.get_right() + RIGHT * 0.1, n2.get_left() - RIGHT * 0.1,
                    color=MUTED, stroke_width=4, buff=0)
        ar4 = Arrow(n2.get_right() + RIGHT * 0.1, n3.get_left() - RIGHT * 0.1,
                    color=MUTED, stroke_width=4, buff=0)

        self.at(24.86)
        self.play(type_in(lab2, run_time=0.6))  # 24.86-25.46（更深的启示：）
        self.at(25.46)
        self.breathe(lab2, scale=1.03, run_time=1.2, loops=1)  # 25.46-26.66
        self.at(26.82)
        self.play(type_in(insight, run_time=1.0))  # 26.82-27.82（稀疏化可以递归——）
        self.at(27.82)
        self.play(FadeIn(n1, shift=DOWN * 0.05), run_time=0.4)  # 27.82-28.22（任何selector自己，）
        self.at(28.22)
        self.play(FadeIn(n2, shift=DOWN * 0.05), run_time=0.4)  # 28.22-28.62
        self.play(Create(ar3), run_time=0.3)  # 28.62-28.92
        self.at(28.92)
        self.play(FadeIn(n3, shift=DOWN * 0.05), run_time=0.4)  # 28.92-29.32（都可能成为下一个瓶颈。）
        self.play(Create(ar4), run_time=0.3)  # 29.32-29.62
        self.at(29.33)
        self.play(type_in(next_lab, run_time=0.6))  # 29.33-29.93（下一篇，）
        self.at(29.93)
        self.breathe(next_lab, scale=1.03, run_time=0.8, loops=1)  # 29.93-30.73
        self.at(30.77)
        self.play_scroll_unroll(next_card, run_time=1.2)  # 30.77-31.97（拆「AI为什么说话这么慢」——推测解码的数学。）
        self.at(31.97)
        self.play(type_in(sub, run_time=0.5))  # 31.97-32.47
        self.at(32.47)
        self.play(FadeOut(VGroup(lab2, insight, n1, n2, n3, ar3, ar4, next_lab, next_card, sub),
                          shift=UP * 0.03), run_time=0.3)  # 32.47-32.77 换页

        # ---------- 页5（32.47-43.30）：开放式问题 + 品牌尾卡 ----------
        q1 = t("你觉得，", 28, WHITE)
        q2 = t("1M 上下文真的有必要吗？", 40, YELL, "BOLD")
        fit(q2, 0.9)
        cmt = t("评论区聊聊", 30, WHITE, "BOLD")
        logo = ImageMobject("avatar-sjai-round.png")
        logo.scale_to_fit_width(2.6)
        follow = t("关注「数解AI」", 36, YELL, "BOLD")
        fit(follow, 0.9)
        title = t("《为什么AI上下文越长越慢？两道数学硬墙一次讲透》", 22, WHITE, "BOLD")
        fit(title, 0.9)
        wc = t("查看公众号文章", 26, GREEN, "BOLD")
        fit(wc, 0.9)
        layout_page(page_stack(q1, q2, cmt, logo, follow, title, wc, buff=0.45))
        tail_grp = Group(logo, follow, title, wc)

        self.at(32.77)
        self.play(type_in(q1, run_time=0.8))  # 32.77-33.57（你觉得，）
        self.at(33.57)
        self.breathe(q1, scale=1.03, run_time=1.0, loops=1)  # 33.57-34.57
        self.at(34.64)
        self.play(type_in(q2, run_time=1.0))  # 34.64-35.64（1M上下文真的有必要吗？）
        self.at(35.64)
        self.emphasize(q2, mode="circumscribe", run_time=1.0)  # 35.64-36.64
        self.at(36.64)
        self.breathe(q2, scale=1.02, run_time=1.0, loops=1)  # 36.64-37.64
        self.at(37.96)
        self.play(type_in(cmt, run_time=0.8))  # 37.96-38.76（评...论区聊聊。）
        self.at(38.76)
        self.emphasize(cmt, mode="indicate", run_time=0.8)  # 38.76-39.56
        self.at(39.87)
        self.transition_out(head, footer_mob, q1, q2, cmt)  # 39.87-40.47 换页到尾卡
        self.at(40.47)
        self.play(FadeIn(logo, shift=UP * 0.05), run_time=0.5)  # 40.47-40.97（论区聊聊。）
        self.at(40.97)
        self.play(type_in(follow, run_time=0.7))  # 40.97-41.67
        self.at(41.67)
        self.play(type_in(title, run_time=0.8))  # 41.67-42.47
        self.at(42.47)
        self.play(type_in(wc, run_time=0.6))  # 42.47-43.07
        self.at(43.07)
        self.breathe(tail_grp, scale=1.02, run_time=1.2, loops=1)  # 43.07-44.27 尾卡停留到末帧
        self.pad_to_voice()
