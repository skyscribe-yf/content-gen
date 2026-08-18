class S5(_Base):
    """S5：第一招 —— DSA 稀疏注意力。
    页1（0.00-10.71）GLM-5.2 给出答案（不止一招）+ 标准注意力回顾（看所有历史）；
    页2（10.71-19.46）DSA 加 Indexer：从历史挑最相关 2048 个（概念图）；
    页3（19.46-27.20）从跟所有人握手 → 只跟 2048 个人握手 → 计算量线性增长；
    页4（27.20-38.74）陷阱：Indexer 自己也是 O(T²) → 问题只是换了个位置。
    时间轴 = s5 锚点表（38.74s）；数字走 counter_value。"""

    def construct(self):
        self.bg()
        self.footer()
        footer_mob = self.mobjects[-1]
        head = t("第一招：DSA 稀疏注意力", 38, YELL, "BOLD").to_edge(UP, buff=1.2)
        self.play(type_in(head, run_time=1.1))  # 0.00-1.10

        # ---------- 页1（0.00-10.71）：答案 + 标准注意力回顾 ----------
        ans = t("GLM-5.2 给出了答案", 40, WHITE, "BOLD")
        fit(ans, 0.9)
        more = t("而且不止一招", 52, YELL, "BOLD")
        fit(more, 0.9)
        std = t("标准注意力：每个 token 看所有历史 token", 32, WHITE)
        fit(std, 0.9)
        # 标准注意力示意：8 个历史点水平直线 + 最前方高亮点 + 弧线箭头（2026-08-19 打磨）
        # 弧线从历史点指向高亮点（当前 token），越远的历史弧线越高、不重叠
        hist = VGroup(*[Dot(radius=0.13, color=CYAN) for _ in range(8)])
        hist.arrange(RIGHT, buff=0.4)
        all_lab = t("看所有历史", 26, MUTED)
        page1 = page_stack(ans, more, std, all_lab, hist, buff=1.3)
        layout_page(page1)
        cur = Dot(radius=0.18, color=YELL)  # 高亮点：当前 token（最前方/最右）
        cur.next_to(hist, RIGHT, buff=0.6)
        arcs = VGroup()
        dmax = np.linalg.norm(hist[0].get_center() - cur.get_center())
        for h in hist:
            d = np.linalg.norm(h.get_center() - cur.get_center())
            frac = d / dmax
            # CurvedArrow 负角 = 向上拱；越远的历史弧线越高（不重叠）
            angle = -(PI / 6 + frac * PI / 4)
            arcs.add(CurvedArrow(h.get_center(), cur.get_center(),
                                 angle=angle, color=MUTED, stroke_width=2.5))

        self.at(0.51)
        self.play(type_in(ans, run_time=0.7))  # 0.51-1.21（GLM-5.2给出了答案，）
        self.at(2.19)
        self.play(type_in(more, run_time=0.8))  # 2.19-2.99（而且不止一招。）
        self.at(2.99)
        self.emphasize(more, run_time=0.6)  # 2.99-3.59
        self.at(3.86)
        self.play(type_in(std, run_time=0.9))  # 3.86-4.76（DSA，稀疏注意力。标准注意力，）
        self.at(6.88)
        self.play(FadeIn(hist, shift=DOWN * 0.05), run_time=0.5)  # 6.88-7.38（每个token看所有历史token。）
        self.at(7.38)
        self.play(type_in(all_lab, run_time=0.4))  # 7.38-7.78
        self.play(FadeIn(cur, run_time=0.3))  # 7.78-8.08 高亮点（当前 token）
        self.at(7.68)
        self.play(*[Create(a) for a in arcs], run_time=1.0, lag_ratio=0.15)  # 7.68-8.68 弧线依次画出
        self.at(10.71)
        self.play(FadeOut(VGroup(ans, more, std, all_lab, cur, hist, arcs),
                          shift=UP * 0.03), run_time=0.3)  # 10.71-11.01 换页

        # ---------- 页2（10.71-19.46）：Indexer 挑 2048 个 ----------
        idx = t("DSA 加了一个 Indexer", 34, WHITE, "BOLD")
        fit(idx, 0.9)
        img = ImageMobject("img/indexer-round.png")
        img.scale_to_fit_width(4.2)
        pick = t("先从历史里挑出最相关的 2048 个", 34, YELL, "BOLD")
        fit(pick, 0.9)
        only = t("只在这 2048 个上算注意力", 32, WHITE)
        fit(only, 0.9)
        page2 = page_stack(idx, img, pick, only, buff=0.6)
        layout_page(page2)

        self.at(11.01)
        self.play(type_in(idx, run_time=0.8))  # 11.01-11.81（DSA加了一个Indexer：）
        self.at(13.02)
        self.play(FadeIn(img, shift=DOWN * 0.05), run_time=0.6)  # 13.02-13.62（先从历史里挑出最相关的2048个，）
        self.at(13.62)
        self.play(type_in(pick, run_time=0.9))  # 13.62-14.52
        self.at(16.45)
        self.play(type_in(only, run_time=0.9))  # 16.45-17.35（只在这2048个上算注意力。）
        self.at(19.46)
        self.play(FadeOut(Group(idx, img, pick, only), shift=UP * 0.03), run_time=0.3)  # 19.46-19.76 换页

        # ---------- 页3（19.46-27.20）：握手 → 2048 个人 → 线性增长 ----------
        all_hand = t("从跟所有人握手", 38, MUTED)
        fit(all_hand, 0.9)
        few_hand = t("变成只跟最相关的 2048 个人握手", 48, YELL, "BOLD")
        fit(few_hand, 0.9)
        linear = t("T 再大，计算量只线性增长", 44, WHITE, "BOLD")
        fit(linear, 0.9)
        formula = VGroup(t("FLOPs: c × T × 2048", 42, CYAN, "BOLD")).arrange(RIGHT, buff=0.1)
        fit(formula, 0.9)
        o2o = t("O(T²) → O(T×k)", 34, MUTED)
        fit(o2o, 0.9)
        page3 = page_stack(all_hand, few_hand, linear, formula, o2o, buff=1.15)
        layout_page(page3)

        self.at(19.76)
        self.play(type_in(all_hand, run_time=0.7))  # 19.76-20.46（从跟所有人握手，）
        self.at(20.98)
        self.play(type_in(few_hand, run_time=1.0))  # 20.98-21.98（变成只跟最相关的2048个人握手。T再大，）
        self.at(21.98)
        self.emphasize(few_hand, run_time=0.6)  # 21.98-22.58
        self.at(24.45)
        self.play(type_in(linear, run_time=0.9))  # 24.45-25.35（计算量只线性增长。）
        self.at(25.35)
        self.play(type_in(formula, run_time=0.8))  # 25.35-26.15
        self.at(26.15)
        self.play(type_in(o2o, run_time=0.5))  # 26.15-26.65
        self.at(27.20)
        self.play(FadeOut(VGroup(all_hand, few_hand, linear, formula, o2o),
                          shift=UP * 0.03), run_time=0.3)  # 27.20-27.50 换页

        # ---------- 页4（27.20-38.74）：陷阱：Indexer 自己也是 O(T²) ----------
        trap = t("但这里有个陷阱", 46, WHITE, "BOLD")
        fit(trap, 0.9)
        idx2 = t("Indexer 自己，也是 O(T²)", 52, RED, "BOLD")
        fit(idx2, 0.9)
        sel = t("它要从 T 个 token 里选出 2048 个", 36, WHITE)
        fit(sel, 0.9)
        scan = t("本身就要算一遍所有 token", 36, WHITE)
        fit(scan, 0.9)
        q = t("问题，只是换了个位置", 46, CYAN, "BOLD")
        fit(q, 0.9)
        page4 = page_stack(trap, idx2, sel, scan, q, buff=1.05)
        layout_page(page4)

        self.at(27.50)
        self.play(type_in(trap, run_time=0.8))  # 27.50-28.30（但这里有个陷阱——Indexer自己，）
        self.at(28.78)
        self.play(type_in(idx2, run_time=0.9))  # 28.78-29.68（也是O(T²)。）
        self.at(29.68)
        cross_idx = self.play_red_cross(idx2, run_time=0.65)  # 29.68-30.33
        self.at(30.27)
        self.play(type_in(sel, run_time=0.8))  # 30.27-31.07（它要从T个token里选出2048个，）
        self.at(31.89)
        self.play(type_in(scan, run_time=0.9))  # 31.89-32.79（本身就要算一遍所有token。）
        self.at(35.08)
        self.play(type_in(q, run_time=0.9))  # 35.08-35.98（问题，只是换了个位置。）
        self.at(35.98)
        self.breathe(q, scale=1.03, run_time=1.0, loops=1)  # 35.98-36.98
        self.at(36.98)
        self.transition_out(head, footer_mob, trap, idx2, cross_idx, sel, scan, q)  # 36.98-37.58
        self.pad_to_voice()


