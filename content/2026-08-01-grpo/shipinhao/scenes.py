#!/usr/bin/env python3
"""《GRPO为什么省显存，却撑不住长程任务？》视频号 Manim 动画（竖屏 1080×1920）

9 个场景 S1-S9（S9 = 关注引导 CTA），与 storyboard.md 一一对应。
通用工具在 scripts/manim_helpers.py；本文件只放 VOICE_DUR / TAIL / 场景类。
时间轴锚点 = tts/sentence-boundaries.json 句级边界（口播实测，禁止按预估排布）。
渲染：
  python3 -m manim render -ql --disable_caching scenes.py S1 S2 S3 S4 S5 S6 S7 S8 S9
  python3 -m manim render -qm --disable_caching scenes.py S1 S2 S3 S4 S5 S6 S7 S8 S9
构建：python3 scripts/manim_video_build.py content/2026-08-01-grpo/shipinhao
"""
from __future__ import annotations

import pathlib
import sys


def _scripts_dir() -> str:
    """向上查找项目 scripts/ 目录（含 manim_helpers.py），不依赖场景文件深度。"""
    p = pathlib.Path(__file__).resolve().parent
    for _ in range(6):
        cand = p / "scripts"
        if (cand / "manim_helpers.py").exists():
            return str(cand)
        p = p.parent
    raise RuntimeError("找不到 scripts/manim_helpers.py")


sys.path.insert(0, _scripts_dir())
from manim_helpers import *

config.background_color = "#0F1A30"

# 口播实测时长（voice_process 输出，勿改）
VOICE_DUR = {"S1": 17.135, "S2": 35.919, "S3": 29.985, "S4": 26.107,
             "S5": 33.481, "S6": 29.233, "S7": 32.911, "S8": 38.612,
             "S9": 13.851}
TAIL = 2.5  # 渲染缓冲（build 会截到 0.1s）


# ---------------- S1 ----------------

# ---------------- S1 ----------------

# ---------------- S1 ----------------

# ---------------- S1 ----------------

# ---------------- S1 ----------------

# ---------------- S1 ----------------

# ---------------- S1 ----------------

# ---------------- S1 ----------------

# ---------------- S1 ----------------

# ---------------- S1 ----------------

# ---------------- S1 ----------------

# ---------------- S1 ----------------

# ---------------- S1 ----------------

# ---------------- S1 ----------------
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

# ---------------- S2 ----------------
class S2(_Base):
    """S2：GRPO 诞生 —— DeepSeekMath 2024 起点 → 规则判分（概念图 exam-grading）→
    不训练 critic（红叉否定）→ 三卡（不训练 critic / 多份答案 / 组内平均分参照）→
    R1-Zero AIME 2024 15.6%→77.9%（数字滚动爆点）→ 反思涌现。
    时间轴锚点 = tts 句级边界（口播实测，禁止预估）；数字走 _cnt 数字滚动
    （counter_value 定位先行版，S3/S5 同款，避免原地滚动后跳位）。"""

    def _cnt(self, start, end, suffix="", decimals=1, size=64, color=YELL,
             pos=None, run_time=1.8):
        """数字滚动定位先行版：滚动前先 pos(grp) 摆位，避免滚动后跳位。
        suffix 用 updater 跟随数字右缘（DecimalNumber 变宽时左缘固定、右缘右移）。"""
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
        footer_mob = self.mobjects[-1]  # footer() 不返回引用，取最近 add 的 mob 供 transition_out 带走
        head = t("GRPO 的诞生：从数学题开始", 38, YELL, "BOLD")
        fit(head, 0.9)
        head.to_edge(UP, buff=1.0)
        self.play(type_in(head, run_time=1.1))  # 0.00-1.10（GRPO 的起点，）

        # ---------- 页0（2.80-6.11）：DeepSeekMath · 2024 起点卡 ----------
        card_ds = _card("DeepSeekMath · 2024", 6.2, 3.6, CYAN, WHITE, 40, CARD_FILL, "BOLD")
        layout_page(card_ds)
        self.at(2.80)
        self.play_scroll_unroll(card_ds, run_time=1.3)  # 2.80-4.10（…DeepSeek 的 DeepSeekMath。）
        self.at(5.70)
        self.play(FadeOut(card_ds, shift=UP * 0.03), run_time=0.4)  # 5.70-6.10

        # ---------- 页1（6.11-11.55）：概念图 + 图下标注 ----------
        img = ImageMobject("img/exam-grading-round.png")
        img.scale_to_fit_width(4.2)  # 图为主：放进纵向带中心，四周留白均衡
        cap = t("数学题有标准答案，规则就能判分", 26, WHITE)
        fit(cap, 0.9)
        layout_page(page_stack(img, cap, buff=0.55))
        self.at(6.11)
        self.play(FadeIn(img, shift=DOWN * 0.05), run_time=0.8)  # 6.11-6.91（观察很朴素：）
        self.at(7.68)
        self.play(type_in(cap, run_time=1.0))  # 7.68-8.68（数学题有标准答案，规则就能判分，）
        self.at(11.63)
        self.play(FadeOut(Group(img, cap), shift=UP * 0.03), run_time=0.4)  # 11.63-12.03（台词 11.634 结束后再换页）

        # ---------- 页2（11.63-15.25）：否定卡 + 红叉（何必）----------
        card_q = _card("训练大模型猜每一步的价值？", 6.6, 3.6, MUTED, WHITE, 34, CARD_FILL, "BOLD")
        layout_page(card_q)
        self.at(11.63)
        self.play_scroll_unroll(card_q, run_time=1.2)  # 11.63-12.83（何必再训练一个大模型…）
        self.at(12.90)
        cross_q = self.play_red_cross(card_q)  # 12.90-13.50 打叉否定
        self.at(14.85)
        self.play(FadeOut(VGroup(card_q, cross_q), shift=UP * 0.03), run_time=0.4)  # 14.85-15.25

        # ---------- 页3（15.25-21.15）：三卡竖排（等宽 5.8×0.95，居中留白）----------
        c_a = _card("不训练 critic", 5.8, 0.95, GREEN, WHITE, 28, CARD_FILL, "BOLD")
        c_b = _card("同题生成多份答案", 5.8, 0.95, CYAN, WHITE, 28, CARD_FILL, "BOLD")
        c_c = _card("组内平均分当参照", 5.8, 0.95, YELL, WHITE, 28, CARD_FILL, "BOLD")
        cards = page_stack(c_a, c_b, c_c, buff=0.65)
        layout_page(cards)
        self.at(15.25)
        self.play_scroll_unroll(c_a, run_time=1.3)  # 15.25-16.55（于是 GRPO 不训练 critic，）
        self.at(18.30)
        self.play_scroll_unroll(c_b, run_time=1.3)  # 18.30-19.60（让同一道题生成多份答案，）
        self.at(19.70)
        self.play_scroll_unroll(c_c, run_time=1.0)  # 19.70-20.70（拿组内平均分当参照。）
        self.at(20.75)
        self.play(FadeOut(cards, shift=UP * 0.03), run_time=0.4)  # 20.75-21.15

        # ---------- 页4（21.20-32.85）：R1-Zero 路线 + AIME 数字滚动爆点 ----------
        lab_r1 = _card("DeepSeek-R1-Zero 用这条路线", 6.4, 1.05, CYAN, WHITE, 28, CARD_FILL, "BOLD")
        aime_lab = t("AIME 2024 正确率", 24, MUTED)
        # 先出旧值 15.6%（数字对比先旧后新，2026-08-16 用户反馈 00:49）
        old = VGroup(t("15.6%", 28, MUTED), t("→", 28, MUTED)).arrange(RIGHT, buff=0.12)
        num_ph = Rectangle(width=2.5, height=1.0, fill_opacity=0.0, stroke_opacity=0.0)
        num_row = VGroup(old, num_ph).arrange(RIGHT, buff=0.35, aligned_edge=DOWN)
        layout_page(page_stack(lab_r1, aime_lab, num_row, buff=0.7))

        self.at(21.20)
        self.play_scroll_unroll(lab_r1, run_time=1.2)  # 21.20-22.40（DeepSeek-R1-Zero 用这条路线，）
        self.at(23.60)
        self.play(type_in(aime_lab, run_time=0.5))  # 23.60-24.10（AIME 2024 正确率从…）
        self.at(25.50)
        self.play(type_in(old, run_time=0.5))  # 25.50-26.00 先出旧值 15.6%
        self.at(26.2)
        num = self._cnt(15.6, 77.9, suffix="%", decimals=1, size=64, color=YELL,
                        pos=lambda g: g.next_to(old, RIGHT, buff=0.35, aligned_edge=DOWN),
                        run_time=1.8)  # 26.2-28.0 15.6%→77.9% 数字滚动（旧值已在场）
        self.at(29.20)
        self.emphasize(num, mode="indicate", run_time=0.6)  # 29.20-29.80 爆点聚焦
        self.at(32.45)
        self.play(FadeOut(VGroup(lab_r1, aime_lab, num, old), shift=UP * 0.03),
                  run_time=0.4)  # 32.45-32.85

        # ---------- 页5（32.89-37.30）：反思涌现 ----------
        learn = t("还自发学会了", 28, MUTED)
        refl = t("反思", 64, YELL, "BOLD")
        bubble = _card("等等，我算错了？", 5.0, 1.25, MUTED, MUTED, 26, CARD_FILL2, "NORMAL")
        layout_page(page_stack(learn, refl, bubble, buff=0.8))
        self.at(32.89)
        self.play(type_in(learn, run_time=0.6))  # 32.89-33.49（还自发学会了）
        self.at(33.80)
        self.play_scroll_unroll(bubble, run_time=1.0)  # 33.80-34.80（学会反思期间展示气泡，勿留静音期）
        self.at(35.31)
        self.play(type_in(refl, run_time=0.5))  # 35.31-35.81（反思）
        self.at(35.85)
        self.emphasize(refl, mode="indicate", run_time=0.4)  # 35.85-36.25

        # ---------- 结尾转场（带走全部可见元素）→ pad_to_voice ----------
        self.transition_out(head, footer_mob, learn, refl, bubble, run_time=0.6)  # 37.30-37.90
        self.pad_to_voice()

# ---------------- S3 ----------------
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

# ---------------- S4 ----------------
class S4(_Base):
    def construct(self):
        # ---------- 全局：背景 + 页脚 + 标题（0.00-1.10）----------
        self.bg()
        self.footer()
        footer_mob = self.mobjects[-1]  # footer() 不返回引用，取最近 add 的 mob 供 transition_out 带走
        head = t("核心机制：考试类比", 38, YELL, "BOLD").to_edge(UP, buff=1.2)

        # ---------- 页1（0.00-10.20）：考试类比搭建 ----------
        q = t("GRPO 怎么工作？", 40, YELL, "BOLD")
        line1 = t("把同一个 prompt 想成同一道题，", 28, WHITE)
        fit(line1, 0.9)

        # 答卷小纸片（成组小徽章，FadeIn 合规）
        def make_paper():
            sheet = Rectangle(width=0.72, height=0.78, color=MUTED, stroke_width=2,
                              fill_color=WHITE, fill_opacity=0.07)
            ln = VGroup(*[Line(LEFT * 0.2, RIGHT * 0.2, color=MUTED, stroke_width=1.5) for _ in range(3)])
            for i, l in enumerate(ln):
                l.move_to(sheet.get_center() + UP * (0.14 - i * 0.16))
            return VGroup(sheet, ln)

        papers = VGroup(*[make_paper() for _ in range(5)]).arrange(RIGHT, buff=0.22)
        g_lab = t("G 份答卷", 24, CYAN, "BOLD")
        paper_row = VGroup(papers, g_lab).arrange(RIGHT, buff=0.35)

        # 标准答案 → 自动裁判（同组等宽卡，分两次拉幕）
        card_ans = _card("标准答案", 2.3, 0.8, GREEN, GREEN, 26, CARD_FILL, "BOLD")
        card_judge = _card("自动裁判", 2.3, 0.8, YELL, YELL, 26, CARD_FILL, "BOLD")
        pair = VGroup(card_ans, card_judge).arrange(RIGHT, buff=1.0)
        arrow = Arrow(card_ans.get_right() + RIGHT * 0.08, card_judge.get_left() - RIGHT * 0.08,
                      color=MUTED, stroke_width=4, buff=0)
        badge_row = VGroup(card_ans, arrow, card_judge)
        layout_page(page_stack(q, line1, paper_row, badge_row, buff=0.6))

        self.play(type_in(head, run_time=1.1), type_in(q, run_time=0.9))  # 0.00-1.10
        self.at(1.95)
        self.play(type_in(line1, run_time=0.9))  # 1.95-2.85
        self.at(4.84)
        self.play(FadeIn(papers, shift=DOWN * 0.05, lag_ratio=0.15), run_time=0.6)  # 4.84-5.44
        self.play(type_in(g_lab, run_time=0.5))  # 5.44-5.94
        self.at(6.90)
        self.play_scroll_unroll(card_ans, run_time=1.1)  # 6.90-8.00
        self.at(8.48)
        self.play(Create(arrow), run_time=0.35)          # 8.48-8.83
        self.play_scroll_unroll(card_judge, run_time=1.0)  # 8.83-9.83

        # 换页 → 页2a（10.20-12.66）：不请老师逐步批改（否定红叉）
        self.at(10.20)
        self.play(FadeOut(VGroup(q, line1, paper_row, badge_row), shift=UP * 0.03), run_time=0.3)  # 10.20-10.50
        card_teach = _card("老师逐步批改", 5.0, 3.6, MUTED, WHITE, 40, CARD_FILL, "BOLD")
        layout_page(card_teach)
        self.play_scroll_unroll(card_teach, run_time=1.0)  # 10.50-11.50
        cross = self.play_red_cross(card_teach)            # 11.50-12.10
        self.play(FadeOut(VGroup(card_teach, cross), shift=UP * 0.03), run_time=0.3)  # 12.10-12.40

        # 换页 → 页2b（12.66-14.42）：概念图（多份答卷围绕平均分）
        img = ImageMobject("img/class-average-round.png")
        img.scale_to_fit_width(3.8)  # 图为主：居中放大，上下留白均衡
        cap = t("先看全班平均分：", 26, WHITE)
        layout_page(page_stack(img, cap, buff=0.55))
        self.at(12.66)
        self.play(FadeIn(img, shift=DOWN * 0.05), run_time=0.6)  # 12.66-13.26
        self.play(type_in(cap, run_time=0.8))  # 13.26-14.06

        # 换页 → 页2c（14.42-19.45）：平均分参照 + 高于/低于
        self.at(14.42)
        self.play(FadeOut(Group(img, cap), shift=UP * 0.03), run_time=0.3)  # 14.42-14.72
        axis = Line(LEFT * 2.3, RIGHT * 2.3, color=MUTED, stroke_width=4)
        lab_mean = t("平均分", 24, MUTED)
        axis_row = VGroup(axis, lab_mean).arrange(RIGHT, buff=0.25)
        bars_hi = VGroup(Rectangle(width=0.5, height=0.7, color=GREEN, fill_color=GREEN, fill_opacity=0.55),
                         Rectangle(width=0.5, height=1.0, color=GREEN, fill_color=GREEN, fill_opacity=0.55),
                         Rectangle(width=0.5, height=0.85, color=GREEN, fill_color=GREEN, fill_opacity=0.55))
        bars_hi.arrange(RIGHT, buff=0.4, aligned_edge=DOWN)
        bars_lo = VGroup(Rectangle(width=0.5, height=0.8, color=RED, fill_color=RED, fill_opacity=0.55),
                         Rectangle(width=0.5, height=0.6, color=RED, fill_color=RED, fill_opacity=0.55),
                         Rectangle(width=0.5, height=0.7, color=RED, fill_color=RED, fill_opacity=0.55))
        bars_lo.arrange(RIGHT, buff=0.4, aligned_edge=UP)
        label_hi = t("高于平均 → 正向信号", 26, GREEN, "BOLD")
        fit(label_hi, 0.9)
        label_lo = t("低于平均 → 概率下降", 26, RED, "BOLD")
        fit(label_lo, 0.9)
        chart = VGroup(label_hi, bars_hi, axis_row, bars_lo, label_lo).arrange(DOWN, buff=0.42)
        layout_page(chart)
        self.play(Create(axis), run_time=0.5)                    # 14.72-15.22
        self.play(type_in(lab_mean, run_time=0.4))               # 15.22-15.62
        self.play(*[GrowFromEdge(b, DOWN) for b in bars_hi], run_time=0.55)  # 15.62-16.17
        self.play(type_in(label_hi, run_time=0.75))              # 16.17-16.92
        self.play(*[GrowFromEdge(b, UP) for b in bars_lo], run_time=0.9)     # 16.92-17.82
        self.play(type_in(label_lo, run_time=0.8))               # 17.82-18.62

        # 换页 → 页3a（19.45-22.94）：全班都对 / 全班都错
        self.at(19.45)
        self.play(FadeOut(VGroup(axis, lab_mean, bars_hi, bars_lo, label_hi, label_lo),
                          shift=UP * 0.03), run_time=0.3)        # 19.45-19.75
        l_allok = t("可要是全班都对，", 28, WHITE)
        ok_row = VGroup(t("✔", 44, GREEN, "BOLD"), t("✔", 44, GREEN, "BOLD"),
                        t("✔", 44, GREEN, "BOLD")).arrange(RIGHT, buff=0.7)
        l_allbad = t("或者全班都错呢？", 28, WHITE)
        bad_row = VGroup(t("✗", 44, RED, "BOLD"), t("✗", 44, RED, "BOLD"),
                         t("✗", 44, RED, "BOLD")).arrange(RIGHT, buff=0.7)
        layout_page(page_stack(l_allok, ok_row, l_allbad, bad_row, buff=0.72))
        self.play(type_in(l_allok, run_time=0.8))                # 19.75-20.55
        self.play(FadeIn(ok_row, scale=1.4), run_time=0.5)       # 20.55-21.05
        self.at(21.12)
        self.play(type_in(l_allbad, run_time=0.8))               # 21.12-21.92
        self.play(FadeIn(bad_row, scale=1.4), run_time=0.5)      # 21.92-22.42

        # 换页 → 页3b（22.94-24.19）：大家分数一样 → 等长条
        self.at(22.94)
        self.play(FadeOut(VGroup(l_allok, ok_row, l_allbad, bad_row), shift=UP * 0.03), run_time=0.3)  # 22.94-23.24
        l_same = t("大家分数一样，", 32, WHITE)
        bars_same = VGroup(*[Rectangle(width=0.7, height=2.4, color=CYAN,
                                       fill_color=CYAN, fill_opacity=0.55) for _ in range(3)])
        bars_same.arrange(RIGHT, buff=0.6, aligned_edge=DOWN)
        layout_page(page_stack(l_same, bars_same, buff=0.7))
        self.play(*[GrowFromEdge(b, DOWN) for b in bars_same],
                  type_in(l_same, run_time=0.5), run_time=0.55)  # 23.24-23.79
        self.play(FadeOut(VGroup(l_same, bars_same), shift=UP * 0.03), run_time=0.3)  # 23.85-24.15

        # 换页 → 页3c（24.19-26.11）：不知道该往哪边改（问号 + 双向箭头）
        dir_grp = VGroup(t("↑", 100, MUTED, "BOLD"), t("？", 170, YELL, "BOLD"),
                         t("↓", 100, MUTED, "BOLD")).arrange(RIGHT, buff=0.9)
        l_last = t("模型就不知道该往哪边改了", 32, WHITE)
        fit(l_last, 0.9)
        layout_page(page_stack(dir_grp, l_last, buff=1.3))
        self.at(24.19)
        self.play(FadeIn(dir_grp, scale=1.2), run_time=0.5)      # 24.19-24.69
        self.play(type_in(l_last, run_time=0.9))                 # 24.69-25.59
        self.emphasize(dir_grp[1], mode="wiggle")                # 25.59-26.39

        # 结尾转场（带走全部可见元素）→ pad_to_voice
        self.transition_out(head, footer_mob, dir_grp, l_last)   # 26.39-26.99
        self.pad_to_voice()

# ---------------- S5 ----------------
class S5(_Base):
    """S5：GRPO 四步 —— 采样(G 个输出，DeepSeekMath 用 64) → 算奖励 → 组内归一化
    (z-score 公式三段 morph) → 策略更新(clip 刹车 / KL 尺子)。
    爆点：基础版本优势整段共享（常数）。时间轴 = tts 句级边界；数字走 counter_value，
    公式走 MathTex（texlive 已装）。"""

    def _cnt(self, start, end, suffix="", size=56, color=YELL,
             pos=None, run_time=0.9):
        """数字滚动（S3 同款定位先行版）：滚动前先 pos(grp) 摆位，避免原地滚动后跳位。
        suffix 用 updater 跟随数字右缘（DecimalNumber 变宽时左缘固定、右缘右移）。"""
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
        # ---------- 全局：背景 + 页脚 + 标题（0.00-0.50）----------
        self.bg()
        self.footer()
        footer_mob = self.mobjects[-1]  # footer() 不返回引用，取最近 add 的 mob 供 transition_out 带走
        head = t("GRPO 就四步", 38, YELL, "BOLD").to_edge(UP, buff=1.2)
        # 锚点窗口仅 0.51s（0.00-0.51），标题 type_in 压到 0.5 不侵占下一句
        self.play(type_in(head, run_time=0.5))  # 0.00-0.50

        # ---------- 页1（0.00-8.78）：第一步 · 采样 ----------
        s1 = t("第一步", 30, CYAN, "BOLD")
        chip_s = boxed("采样", 1.7, 0.72, YELL, 30, weight="BOLD")
        step_row = VGroup(s1, chip_s).arrange(RIGHT, buff=0.4).set_x(0.0)
        line1 = t("每个问题生成 G 个输出", 27, WHITE)
        fit(line1, 0.9)

        # G 份输出小方格（2×4 徽章组，FadeIn 合规）
        chips = VGroup(
            VGroup(*[Rectangle(width=0.45, height=0.45, color=CYAN,
                               fill_color=CYAN, fill_opacity=0.22) for _ in range(4)]).arrange(RIGHT, buff=0.2),
            VGroup(*[Rectangle(width=0.45, height=0.45, color=CYAN,
                               fill_color=CYAN, fill_opacity=0.22) for _ in range(4)]).arrange(RIGHT, buff=0.2),
        ).arrange(DOWN, buff=0.2)
        g_lab = t("G 个输出", 22, MUTED)
        # DeepSeekMath 标签居中放 chips 下方（勿放右侧：偏右 + 与 chips 重叠，2026-08-16 用户反馈）
        ds_lab = t("DeepSeekMath", 24, CYAN, "BOLD")
        if ds_lab.width > 1.7:
            ds_lab.set_width(1.7)
        num_ph = Rectangle(width=1.6, height=0.75, fill_opacity=0.0, stroke_opacity=0.0)
        layout_page(page_stack(step_row, line1, chips, g_lab, ds_lab, num_ph, buff=0.5))

        self.at(0.51)
        self.play(type_in(s1, run_time=0.5))  # 0.51-1.01（第一步，）
        self.at(2.21)
        self.play_scroll_unroll(chip_s, run_time=1.2)  # 2.21-3.41（采样：）
        self.at(3.79)
        self.play(type_in(line1, run_time=0.9))  # 3.79-4.69（每个问题生成 G 个输出，）
        self.at(4.75)
        self.play(FadeIn(chips, shift=DOWN * 0.05, lag_ratio=0.12), run_time=0.55)  # 4.75-5.30
        self.at(5.35)
        self.play(type_in(g_lab, run_time=0.5))  # 5.35-5.85
        self.at(6.33)
        self.play(type_in(ds_lab, run_time=0.5))  # 6.33-6.83（DeepSeekMath 用 64。）
        num64 = self._cnt(0, 64, suffix=" 个", size=52, color=YELL,
                          pos=lambda g: g.move_to(num_ph),
                          run_time=1.1)  # 6.9-8.0
        self.at(8.0)
        self.emphasize(num64, mode="indicate", run_time=0.45)  # 8.0-8.45（64 爆点）

        self.at(8.48)
        self.play(FadeOut(VGroup(s1, chip_s, line1, chips, g_lab, ds_lab, num64),
                          shift=UP * 0.03), run_time=0.3)  # 8.48-8.78

        # ---------- 页2a（8.78-18.23）：第二步算奖励 + 第三步组内归一化 + z-score 公式 ----------
        s2 = t("第二步", 30, CYAN, "BOLD")
        chip_r = boxed("算奖励", 1.8, 0.72, GREEN, 28, weight="BOLD")
        row2 = VGroup(s2, chip_r).arrange(RIGHT, buff=0.4).set_x(0.0)
        s3 = t("第三步", 30, CYAN, "BOLD")
        chip_n = boxed("组内归一化", 2.4, 0.72, YELL, 26, weight="BOLD")
        row3 = VGroup(s3, chip_n).arrange(RIGHT, buff=0.4).set_x(0.0)

        # z-score 公式三段：分子 → 分数线+分母 → 相对优势；三段共用同一居中槽位
        num_f = MathTex(r"r_i - \text{mean}",
                        tex_to_color_map={r"\text{mean}": MUTED})
        frac_f = MathTex(r"\frac{r_i - \text{mean}}{\text{std}}",
                         tex_to_color_map={r"\text{mean}": MUTED, r"\text{std}": CYAN})
        full_f = MathTex(r"\hat{A}_i = \frac{r_i - \text{mean}}{\text{std}}",
                         tex_to_color_map={r"\hat{A}_i": YELL,
                                           r"\text{mean}": MUTED, r"\text{std}": CYAN})
        if full_f.width > 5.5:
            full_f.set_width(5.5)
        formula_slot = Rectangle(width=5.6, height=1.05, fill_opacity=0.0, stroke_opacity=0.0)
        for f in (num_f, frac_f, full_f):
            f.move_to(formula_slot)
        rel_lab = t("相对优势", 22, YELL, "BOLD")
        rel_lab.next_to(formula_slot, DOWN, buff=0.2)  # 勿放公式右侧（右缘超界被裁，2026-08-16 用户反馈）
        layout_page(page_stack(row2, row3, formula_slot, rel_lab, buff=0.55))
        for f in (num_f, frac_f, full_f):
            f.move_to(formula_slot)  # 槽位随整页居中后再对齐，避免公式偏位

        self.at(8.78)
        self.play(type_in(s2, run_time=0.5))  # 8.78-9.28（第二步，）
        self.at(9.4)
        self.play_scroll_unroll(chip_r, run_time=1.2)  # 9.4-10.6（算奖励。）
        self.at(10.78)
        self.play(type_in(s3, run_time=0.5))  # 10.78-11.28（第三步，）
        self.at(11.4)
        self.play_scroll_unroll(chip_n, run_time=1.2)  # 11.4-12.6（组内归一化：）
        self.at(12.87)
        self.play(FadeIn(num_f, shift=DOWN * 0.05), run_time=0.6)  # 12.87-13.47（每个分数减去组内平均，）
        self.at(15.03)
        self.morph_to(num_f, frac_f, run_time=0.8)  # 15.03-15.83（再除以组内波动，）
        self.at(16.64)
        self.morph_to(frac_f, full_f, run_time=0.8)  # 16.64-17.44（得到相对优势。）
        self.at(17.44)
        self.play(type_in(rel_lab, run_time=0.45))  # 17.44-17.89
        self.at(17.9)
        self.play(FadeOut(VGroup(s2, chip_r, s3, chip_n, full_f, rel_lab),
                          shift=UP * 0.03), run_time=0.3)  # 17.9-18.2

        # ---------- 页2b（18.23-25.06）：注意爆点 —— 优势整段共享 ----------
        chip_warn = boxed("注意", 1.6, 0.62, YELL, 28, weight="BOLD")
        line_a = t("基础版本里，优势在整个回答上是常数", 27, WHITE)
        fit(line_a, 0.9)
        tok_lab = t("同一个输出里的每个 token", 22, MUTED)
        # token 小方格一行（一个输出拆成多个 token）
        tokens = VGroup(*[Rectangle(width=0.42, height=0.42, color=WHITE,
                                    fill_color=WHITE, fill_opacity=0.12) for _ in range(7)])
        tokens.arrange(RIGHT, buff=0.12)
        card_s = _card("共享同一个分数", 3.7, 0.74, YELL, YELL, 26, CARD_FILL, "BOLD")
        layout_page(page_stack(chip_warn, line_a, tok_lab, tokens, card_s, buff=0.5))

        self.at(18.23)
        self.play_scroll_unroll(chip_warn, run_time=0.75)  # 18.23-18.98（注意，）
        self.at(19.01)
        self.play(type_in(line_a, run_time=0.9))  # 19.01-19.91（基础版本里…每个 token，）
        self.at(20.0)
        self.play(type_in(tok_lab, run_time=0.6))  # 20.0-20.6
        self.at(20.65)
        self.play(FadeIn(tokens, shift=DOWN * 0.05, lag_ratio=0.12), run_time=0.55)  # 20.65-21.2
        self.at(21.3)
        self.breathe(tokens, scale=1.02, run_time=1.0, loops=1)  # 滞留期轻呼吸 21.3-22.3
        self.at(22.98)
        self.play_scroll_unroll(card_s, run_time=1.2)  # 22.98-24.18（共享同一个分数。）
        self.at(24.18)
        self.emphasize(card_s, mode="indicate", run_time=0.6)  # 24.18-24.78 爆点聚焦
        self.at(24.8)
        self.play(FadeOut(VGroup(chip_warn, line_a, tok_lab, tokens, card_s),
                          shift=UP * 0.03), run_time=0.25)  # 24.8-25.05

        # ---------- 页3（25.06-33.48）：第四步 · 策略更新 ----------
        s4 = t("第四步", 30, CYAN, "BOLD")
        chip_u = boxed("策略更新", 2.0, 0.72, YELL, 28, weight="BOLD")
        row4 = VGroup(s4, chip_u).arrange(RIGHT, buff=0.4).set_x(0.0)
        upd_f = MathTex(r"\frac{\pi_\theta}{\pi_{\text{old}}} \times \hat{A}_i",
                        tex_to_color_map={r"\hat{A}_i": YELL, r"\pi_{\text{old}}": MUTED})
        if upd_f.width > 5.5:
            upd_f.set_width(5.5)
        upd_slot = Rectangle(width=5.6, height=1.0, fill_opacity=0.0, stroke_opacity=0.0)
        upd_f.move_to(upd_slot)
        chip_clip = boxed("clip 当刹车", 2.6, 0.64, RED, 26, weight="BOLD")
        chip_kl = boxed("KL 当尺子", 2.6, 0.64, CYAN, 26, weight="BOLD")
        chip_row = VGroup(chip_clip, chip_kl).arrange(RIGHT, buff=0.4)
        layout_page(page_stack(row4, upd_slot, chip_row, buff=0.6))
        upd_f.move_to(upd_slot)  # 槽位随整页居中后再对齐

        self.at(25.06)
        self.play(type_in(s4, run_time=0.5))  # 25.06-25.56（第四步，）
        self.at(26.86)
        self.play_scroll_unroll(chip_u, run_time=1.2)  # 26.86-28.06（策略更新：）
        self.at(29.09)
        self.play(FadeIn(upd_f, shift=DOWN * 0.05), run_time=0.8)  # 29.09-29.89（概率比乘优势，）
        self.at(30.91)
        self.play_scroll_unroll(chip_clip, run_time=1.2)  # 30.91-32.11（clip 当刹车，）
        self.at(32.2)
        self.play_scroll_unroll(chip_kl, run_time=1.2)  # 32.2-33.4（KL 当尺子。）

        # ---------- 结尾转场（带走全部可见元素）→ pad_to_voice ----------
        self.transition_out(head, footer_mob, s4, chip_u, upd_f, chip_clip, chip_kl)  # 33.4-34.0
        self.pad_to_voice()

# ---------------- S6 ----------------
class S6(_Base):
    """S6：PPO vs GRPO —— 双栏对比（critic token 级 vs 整输出 output 级）→
    代价是方差（Axes 双曲线：方差 1/G 下降 + 采样成本线性涨 + trace_dot）→
    最优组大小 G*（GSM8K ≈ 32 / MATH ≈ 64 counter_value）。
    时间轴 = tts 句级边界（s6 重录后 29.233s，2026-08-16）；数字走 counter_value，
    曲线走 Axes 手绘坐标图；trace_dot 返回 VGroup(dot, trail) 换页整体带走。"""

    def _cnt(self, start, end, suffix="", size=48, color=YELL,
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
        # ---------- 全局：背景 + 页脚 + 标题（0.00-0.60）----------
        self.bg()
        self.footer()
        footer_mob = self.mobjects[-1]
        head = t("PPO vs GRPO：差在哪？", 38, YELL, "BOLD").to_edge(UP, buff=1.2)
        self.play(type_in(head, run_time=0.6))  # 0.00-0.60（那 GRPO 和 PPO 差在哪？）

        # ---------- 页1（0.66-12.53）：双栏对比 ----------
        # 左栏 PPO（白，宽 3.0）
        ppo_t = t("PPO", 30, WHITE, "BOLD")
        ppo_c1 = boxed("critic 逐 token 估分", 3.0, 0.95, WHITE, 26)
        ppo_c2 = boxed("粒度细", 3.0, 0.95, CYAN, 26)
        ppo_c3 = boxed("但要额外训练", 3.0, 0.95, WHITE, 26)
        ppo_col = VGroup(ppo_t, ppo_c1, ppo_c2, ppo_c3).arrange(DOWN, buff=0.85)

        # 右栏 GRPO（黄高亮，宽 3.0）
        grpo_t = t("GRPO", 30, YELL, "BOLD")
        grpo_c1 = boxed("整输出一个分", 3.0, 0.95, YELL, 26, weight="BOLD")
        grpo_c2 = boxed("粒度粗", 3.0, 0.95, WHITE, 26)
        grpo_c3 = boxed("零训练成本", 3.0, 0.95, GREEN, 26, weight="BOLD")
        grpo_col = VGroup(grpo_t, grpo_c1, grpo_c2, grpo_c3).arrange(DOWN, buff=0.85)
        cols = VGroup(ppo_col, grpo_col).arrange(RIGHT, buff=1.0)
        layout_page(cols)

        self.at(0.66)
        self.play(type_in(ppo_t, run_time=0.5))  # 0.66-1.16（PPO 的 critic…）
        self.at(1.3)
        self.play_scroll_unroll(ppo_c1, run_time=1.2)  # 1.3-2.5（给每个 token 独立估分 0.81-3.10）
        self.at(3.10)
        self.play_scroll_unroll(ppo_c2, run_time=1.0)  # 3.10-4.10（粒度细 3.10-6.04）
        self.at(6.04)
        self.play_scroll_unroll(ppo_c3, run_time=1.1)  # 6.04-7.14（但要额外训练 6.04-7.12）
        self.at(7.2)
        mk_x = self.play_mark("✗", ppo_c3, color=RED, run_time=0.5)  # 7.2-7.7 额外训练是负担
        self.at(7.7)
        self.play(type_in(grpo_t, run_time=0.5))  # 7.7-8.2（GRPO 给整个输出打一个分 7.12-8.95）
        self.at(8.3)
        self.play_scroll_unroll(grpo_c1, run_time=1.2)  # 8.3-9.5
        self.at(8.95)
        self.play_scroll_unroll(grpo_c2, run_time=1.0)  # 8.95-9.95（粒度粗 8.95-11.47）
        self.at(11.47)
        self.play_scroll_unroll(grpo_c3, run_time=0.8)  # 11.47-12.27（但零训练成本 11.47-12.53）

        self.at(12.53)
        self.play(FadeOut(VGroup(ppo_t, ppo_c1, ppo_c2, ppo_c3, grpo_t,
                                 grpo_c1, grpo_c2, grpo_c3, mk_x),
                          shift=UP * 0.03), run_time=0.3)  # 12.53-12.83 换页（代价是方差 12.53 起）

        # ---------- 页2（12.53-21.04）：代价是方差 —— Axes 双曲线 ----------
        lab_v = t("代价是方差", 30, YELL, "BOLD")
        axes = Axes(
            x_range=[0, 12, 3], y_range=[0, 6, 2],
            x_length=5.0, y_length=3.0,
            axis_config={"color": MUTED, "stroke_width": 3,
                         "include_ticks": True, "include_tip": True,
                         "tip_shape": StealthTip},
        )
        xlab = t("组大小 G", 20, MUTED).next_to(axes.x_axis, DOWN, buff=0.28)
        ylab = t("方差/成本", 20, MUTED).next_to(axes.y_axis, LEFT, buff=0.25)
        curve1 = axes.plot(lambda x: 4.2 / x + 0.15, x_range=[0.9, 11.5], color=CYAN)
        curve1.set_stroke(width=5)
        line2 = axes.plot(lambda x: 0.42 * x, x_range=[0.9, 11.5], color=GREEN)
        line2.set_stroke(width=5)
        lab1 = t("方差（随 G 下降）", 20, CYAN).next_to(curve1.point_from_proportion(0.62), UR, buff=0.12)
        lab2 = t("采样成本（线性涨）", 20, GREEN).next_to(line2.point_from_proportion(0.85), UR, buff=0.12)
        chart = VGroup(axes, xlab, ylab, curve1, line2, lab1, lab2)
        fit(chart, 0.88)  # 带 y 轴标签后整图限宽，杜绝左右被裁
        layout_page(page_stack(lab_v, chart, buff=0.5))

        self.play(type_in(lab_v, run_time=0.8))  # 12.9-13.7（代价是方差：12.53-14.25）
        self.at(14.25)
        self.play(FadeIn(axes, shift=DOWN * 0.05), run_time=0.6)  # 14.25-14.85（有限组大小下估计波动更大 14.25-15.77）
        self.play(type_in(xlab, run_time=0.5), type_in(ylab, run_time=0.5))  # 14.9-15.4
        self.at(15.77)
        self.play(Create(curve1), run_time=0.7)  # 15.77-16.47（方差随 G 增大而下降 15.77-18.71）
        self.play(type_in(lab1, run_time=0.5))  # 16.5-17.0
        dot = self.trace_dot(curve1, color=CYAN, run_time=0.9)  # 17.0-17.9 沿曲线滑行留尾
        self.at(18.71)
        self.play(Create(line2), run_time=0.7)  # 18.71-19.41（采样成本却线性上涨 18.71-21.04）
        self.play(type_in(lab2, run_time=0.5))  # 19.5-20.0

        self.at(21.04)
        self.play(FadeOut(VGroup(lab_v, axes, xlab, ylab, curve1, line2,
                                 lab1, lab2, dot), shift=UP * 0.03), run_time=0.3)  # 21.04-21.34 换页（dot+trail 带走）

        # ---------- 页3（21.04-29.23）：最优组大小 G* ----------
        lab_g = t("存在一个最优组大小", 30, YELL, "BOLD")
        fit(lab_g, 0.9)

        # 数字行：GSM8K ≈ 32（左）| MATH ≈ 64（右），同一行
        g1_lab = t("GSM8K ≈", 28, WHITE)
        n32_ph = Rectangle(width=0.9, height=0.7, fill_opacity=0.0, stroke_opacity=0.0)
        pair32 = VGroup(g1_lab, n32_ph).arrange(RIGHT, buff=0.12, aligned_edge=DOWN)
        m_lab = t("MATH ≈", 28, WHITE)
        n64_ph = Rectangle(width=0.9, height=0.7, fill_opacity=0.0, stroke_opacity=0.0)
        pair64 = VGroup(m_lab, n64_ph).arrange(RIGHT, buff=0.12, aligned_edge=DOWN)
        num_row = VGroup(pair32, pair64).arrange(RIGHT, buff=1.4)

        # G* 曲线图（数字行下方）
        axes2 = Axes(
            x_range=[0, 12, 3], y_range=[0, 6, 2],
            x_length=5.0, y_length=2.5,
            axis_config={"color": MUTED, "stroke_width": 3,
                         "include_ticks": True, "include_tip": True,
                         "tip_shape": StealthTip},
        )
        xlab2 = t("组大小 G", 20, MUTED).next_to(axes2.x_axis, DOWN, buff=0.25)
        ylab2 = t("误差", 20, MUTED).next_to(axes2.y_axis, LEFT, buff=0.25)
        cur2 = axes2.plot(lambda x: 4.2 / x + 0.15, x_range=[0.9, 11.5], color=CYAN)
        cur2.set_stroke(width=5)
        gstar_x = 4.2
        gstar_y = 4.2 / gstar_x + 0.15
        gline = DashedLine(axes2.c2p(gstar_x, 0.1), axes2.c2p(gstar_x, gstar_y + 0.35),
                           color=YELL, stroke_width=4, dash_length=0.12)
        glab = t("G*", 26, YELL, "BOLD").next_to(axes2.c2p(gstar_x, gstar_y + 0.35), UP, buff=0.1)
        chart2 = VGroup(axes2, xlab2, ylab2, cur2, gline, glab)
        fit(chart2, 0.88)
        layout_page(page_stack(lab_g, num_row, chart2, buff=0.55))

        self.play(type_in(lab_g, run_time=0.8))  # 21.4-22.2（所以存在一个最优组大小 21.04-23.23）
        self.at(22.3)
        self.play(type_in(g1_lab, run_time=0.3))  # 22.3-22.6（GSM8K 上大约 32 21.04-23.23）
        n32 = self._cnt(0, 32, suffix="", size=48, color=YELL,
                        pos=lambda g: g.move_to(n32_ph),
                        run_time=0.8)  # 22.7-23.5
        self.at(23.23)
        self.play(type_in(m_lab, run_time=0.4))  # 23.23-23.63（M 23.23-25.65）
        # n64 在 27.80 才滚动（上大约 64 27.80-29.23），勿提前定义（_cnt 定义即播放）
        self.at(23.7)
        self.play(FadeIn(axes2, shift=DOWN * 0.05), run_time=0.5)  # 23.7-24.2（ATH 段 25.65-27.80 前）
        self.play(type_in(xlab2, run_time=0.4), type_in(ylab2, run_time=0.4))  # 24.2-24.6
        self.at(24.6)
        self.play(Create(cur2), run_time=0.7)  # 24.6-25.3
        self.at(25.3)
        self.play(Create(gline), run_time=0.4)  # 25.3-25.7
        self.play(type_in(glab, run_time=0.4))  # 25.7-26.1
        dot2 = self.trace_dot(cur2, color=CYAN, run_time=1.0)  # 26.1-27.1（ATH 段填充）
        self.at(27.2)
        self.breathe(axes2, scale=1.02, run_time=1.0, loops=1)  # 27.2-28.2 滞留期轻呼吸
        self.at(27.80)
        n64 = self._cnt(0, 64, suffix="", size=48, color=YELL,
                        pos=lambda g: g.move_to(n64_ph),
                        run_time=0.9)  # 27.80-28.7（上大约 64 27.80-29.23）
        self.at(28.8)
        self.emphasize(n64, mode="indicate", run_time=0.4)  # 28.8-29.2

        # ---------- 结尾转场（带走全部可见元素）→ pad_to_voice ----------
        self.at(29.2)
        self.transition_out(head, footer_mob, lab_g, g1_lab, m_lab, n32, n64,
                            axes2, xlab2, ylab2, cur2, gline, glab, dot2)
        self.pad_to_voice()

# ---------------- S7 ----------------
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

# ---------------- S8 ----------------
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

# ---------------- S9 ----------------
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
