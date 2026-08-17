class S1(_Base):
    def construct(self):
        # ============ 开场（0.00-1.03）：背景 + 页脚 + 标题 ============
        self.bg()
        # footer 内联创建（与 self.footer() 完全一致），以便 transition_out 收走
        ftr = t("数解AI · 大模型原理", 20, MUTED).to_edge(DOWN, buff=1.15)
        self.add(ftr)
        head = t("Critic：扔掉还是请回？", 38, YELL, "BOLD")
        fit(head, 0.9)
        head.to_edge(UP, buff=1.0)
        self.play(type_in(head, run_time=1.1))
        hint = t("本片拆解 GRPO 算法", 20, MUTED).to_corner(UL, buff=0.6)
        self.play(type_in(hint, run_time=0.5))  # 开场 3 秒内 MUTED 小字（A12）

        # ============ 页1（0.00-10.54）：所有人扔 Critic → 智谱请回 → GLM 两代 ============
        # 先整体排布再逐个拉幕：等宽四卡 + 转折句，整页落入纵向带并贴理想底部
        c1 = _card("所有人：扔掉 Critic", 5.6, 1.10, RED, WHITE, 28, CARD_FILL, "BOLD")
        cap2 = t("智谱却把它请了回来", 26, YELL, "BOLD")
        c2 = _card("智谱：请回 Critic", 5.6, 1.10, GREEN, WHITE, 28, CARD_FILL, "BOLD")
        c3 = _card("GLM-5.2：用回 PPO", 5.6, 0.90, CYAN, WHITE, 28, CARD_FILL, "BOLD")
        c4 = _card("上一代 GLM-5.1：？", 5.6, 0.90, MUTED, WHITE, 28, CARD_FILL, "BOLD")
        layout_page(page_stack(c1, cap2, c2, c3, c4, buff=0.45))

        self.at(1.03)
        self.play_scroll_unroll(c1, run_time=1.2)
        x1 = self.play_red_cross(c1, run_time=0.65)
        self.play(type_in(cap2, run_time=0.8))
        self.play_scroll_unroll(c2, run_time=1.2)
        chk = self.play_mark("✔", c2, GREEN, run_time=0.4)

        self.at(5.80)
        self.play_scroll_unroll(c3, run_time=1.3)
        self.play_scroll_unroll(c4, run_time=1.3)

        # 换页：10.54 前清空本页全部元素（含红叉/绿勾）
        self.at(10.0)
        self.play(FadeOut(VGroup(c1, x1, cap2, c2, chk, c3, c4), shift=UP * 0.03), run_time=0.4)

        # ============ 页2（10.54-17.14）：GRPO 主角 → 省掉老师模型 → 长程之问 ============
        badge = cnode("GRPO", YELL, radius=0.90, fs=32)
        capb = t("今天的主角", 26, YELL, "BOLD")
        c5 = _card("Critic 老师模型", 5.6, 1.1, MUTED, WHITE, 28, CARD_FILL, "BOLD")
        q = t("为什么长程任务，却撑不住？", 34, YELL, "BOLD")
        fit(q, 0.9)

        # 长程轨迹曲线（象征长程任务，不承载数字）
        def traj_fn(t):
            x = -3.0 + 6.0 * t
            y = 0.5 * np.sin(5 * np.pi * t) - 0.4 * t
            return np.array([x, y, 0.0])

        traj = ParametricFunction(traj_fn, color=CYAN, stroke_width=6)
        traj.stretch_to_fit_height(0.7)  # 压扁波动，给长问句和卡片留出呼吸空间
        layout_page(page_stack(badge, capb, c5, q, traj, buff=0.4))

        self.at(10.54)
        self.play(FadeIn(badge, shift=DOWN * 0.05), run_time=0.5)
        self.play(type_in(capb, run_time=0.5))
        self.emphasize(badge, mode="circumscribe", color=CYAN, run_time=0.8)
        self.breathe(badge, scale=1.03, run_time=1.2, loops=1)

        self.at(13.60)
        self.play_scroll_unroll(c5, run_time=1.2)
        x2 = self.play_red_cross(c5, run_time=0.6)

        self.at(15.26)
        self.play(type_in(q, run_time=1.0))
        self.play(Create(traj), run_time=0.8)

        self.emphasize(q, mode="indicate", run_time=0.8)

        # 末尾统一转场：收走全部可见元素（head + footer + 本页内容）
        self.transition_out(head, ftr, hint, badge, capb, c5, x2, q, traj, run_time=0.6)
        self.pad_to_voice()
