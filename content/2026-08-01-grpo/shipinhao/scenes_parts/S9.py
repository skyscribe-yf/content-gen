class S9(_Base):
    """S9：关注引导 CTA + 品牌尾卡（全片最后一场景）。
    页1：点赞/转发 → 关注「数解AI」→ 继续往下拆（8.18 transition_out 换页）；
    页2：尾卡四要素（avatar + 关注引导 + 当期标题 + 查看公众号文章）FadeIn 后
    停留到画面最后（QA B5 检查末帧），不再滑出。
    时间轴 = tts 句级边界（0.00/2.42/5.99/8.18/10.49/12.91）；无数字台词。"""

    def construct(self):
        # ---------- 全局：背景 + 页脚 + 标题（0.00-1.10）----------
        self.bg()
        self.footer()
        footer_mob = self.mobjects[-1]
        head = t("感谢观看", 38, YELL, "BOLD").to_edge(UP, buff=1.2)
        self.play(type_in(head, run_time=1.1))  # 0.00-1.10

        # ---------- 页1（0.00-8.18）：有帮助 → 点赞/转发 → 关注 → 继续拆 ----------
        line1 = t("如果你觉得这条视频有帮助", 28, WHITE)
        fit(line1, 0.9)
        like = _card("点赞", 2.2, 0.8, YELL, YELL, 26, CARD_FILL, "BOLD")
        share = _card("转发", 2.2, 0.8, CYAN, CYAN, 26, CARD_FILL, "BOLD")
        cta = VGroup(like, share).arrange(RIGHT, buff=0.6)
        follow = t("关注「数解AI」", 40, YELL, "BOLD")
        fit(follow, 0.9)
        cont = t("后面我们继续往下拆", 28, WHITE)
        fit(cont, 0.9)
        layout_page(page_stack(line1, cta, follow, cont, buff=0.55))

        self.play(type_in(line1, run_time=0.9))  # 1.10-2.00（如果你觉得这条视频有帮助，）
        self.at(2.42)
        self.play_scroll_unroll(like, run_time=1.2)   # 2.42-3.62（欢迎点赞、）
        self.play_scroll_unroll(share, run_time=1.2)  # 3.62-4.82（转发，）
        self.play(type_in(follow, run_time=1.1))  # 4.82-5.92（也请关注「数解AI」，）
        self.at(5.99)
        self.play(type_in(cont, run_time=0.9))  # 5.99-6.89（后面我们继续往下拆。）

        # 换页：transition_out 带走页1 全部元素 + head + footer（8.18-8.78）
        self.at(8.18)
        self.transition_out(head, footer_mob, line1, cta, follow, cont)  # 8.18-8.78

        # ---------- 页2（8.18-13.85）：尾卡四要素，停留到结尾 ----------
        more = t("想获得更多细节解读", 24, MUTED)
        fit(more, 0.9)

        # 尾卡四要素（10.49-13.85，voice「可以到公众号查看同名文章，我们下期见。」）
        logo = ImageMobject("avatar-sjai-round.png")
        logo.scale_to_fit_width(3.2)  # 适度缩小，保证整组落在字幕安全区上方
        follow2 = t("关注「数解AI」", 34, YELL, "BOLD")
        fit(follow2, 0.9)
        title = t("《GRPO为什么省显存，却撑不住长程任务？》", 24, WHITE, "BOLD")
        fit(title, 0.92)
        wc = t("查看公众号文章", 26, GREEN, "BOLD")
        fit(wc, 0.9)
        nxt = t("下一篇：RLVR", 20, MUTED)
        tail = Group(logo, follow2, title, wc, nxt).arrange(DOWN, buff=0.35)
        layout_page(Group(more, tail).arrange(DOWN, buff=0.5))

        self.play(type_in(more, run_time=0.7))  # 8.78-9.48（想获得更多细节解读，）
        self.at(10.49)
        self.play(FadeIn(logo, shift=UP * 0.05), run_time=0.4)  # 10.49-10.89
        self.play(type_in(follow2, run_time=0.7))  # 10.89-11.59
        self.at(11.6)
        self.play(type_in(title, run_time=0.8))  # 11.6-12.4（查看同名文章）
        self.at(12.5)
        self.play(type_in(wc, run_time=0.6))  # 12.5-13.1
        self.play(type_in(nxt, run_time=0.5))  # 13.1-13.6（我们下期见。）

        # ---------- 结尾：尾卡保持到最后，直接 pad（不再 transition_out）----------
        self.pad_to_voice()
