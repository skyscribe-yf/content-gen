"""
Manim 基础场景模板 —— 数学+AI科普专用
基于 Manim Community Edition

安装: pip install manim
渲染: manim -pql base_scene.py ClassName  (低质量预览)
      manim -pqh base_scene.py ClassName  (高质量输出)
"""
from manim import *


# ponytail: 全局配色，3B1Brown 深色风格
BG_COLOR = "#1a1a2e"
BLUE_ACCENT = "#58c4dd"
ORANGE_ACCENT = "#e07c5a"
GREEN_ACCENT = "#83c167"
RED_ACCENT = "#fc6255"
YELLOW_MATH = "#ffff00"


class BaseScene(Scene):
    """所有科普场景的基类，统一背景和配色"""

    def setup(self):
        self.camera.background_color = BG_COLOR

    def show_title(self, title: str, subtitle: str = ""):
        """显示标题动画"""
        t = Text(title, font_size=48, color=WHITE).move_to(UP * 0.5)
        self.play(Write(t), run_time=1.5)
        if subtitle:
            s = Text(subtitle, font_size=24, color=GREY_B).next_to(t, DOWN, buff=0.3)
            self.play(FadeIn(s), run_time=0.5)
            self.wait(1)
            self.play(FadeOut(t), FadeOut(s))
        else:
            self.wait(1)
            self.play(FadeOut(t))

    def show_formula(self, tex: str, explanation: str = ""):
        """显示公式 + 一句话解释"""
        formula = MathTex(tex, font_size=40, color=YELLOW_MATH)
        self.play(Write(formula), run_time=1.5)
        if explanation:
            exp = Text(explanation, font_size=20, color=GREY_B).next_to(formula, DOWN, buff=0.4)
            self.play(FadeIn(exp), run_time=0.5)
            self.wait(2)
            self.play(FadeOut(exp))
        else:
            self.wait(1)
        return formula

    def show_intuition(self, analogy: str):
        """显示直觉类比（大字居中）"""
        t = Text(analogy, font_size=32, color=BLUE_ACCENT).move_to(ORIGIN)
        self.play(Write(t), run_time=2)
        self.wait(1.5)
        self.play(FadeOut(t))

    def show_bullet_points(self, points: list[str]):
        """逐条显示要点"""
        group = VGroup()
        for i, p in enumerate(points):
            t = Text(f"• {p}", font_size=24, color=WHITE, t2c={p.split()[0]: ORANGE_ACCENT})
            t.next_to(UP * (2 - i * 0.8), buff=0)
            group.add(t)
        for t in group:
            self.play(FadeIn(t, shift=RIGHT * 0.3), run_time=0.5)
        self.wait(2)
        self.play(FadeOut(group))


# === 示例：用基类写一个简单场景 ===

class ExampleGradientDescent(BaseScene):
    """梯度下降直觉 —— 最简示例"""

    def construct(self):
        # 1. 标题
        self.show_title("梯度下降", "Gradient Descent")

        # 2. 直觉
        self.show_intuition("蒙着眼下山，每一步往最陡的方向走")

        # 3. 可视化：一个简单曲面上的下降
        # 画一条"山"的曲线
        axes = Axes(
            x_range=[-3, 3], y_range=[0, 5],
            axis_config={"color": GREY_B},
        ).scale(0.8).shift(DOWN * 0.5)

        curve = axes.plot(lambda x: x**2 / 2 + 1, color=BLUE_ACCENT)
        self.play(Create(axes), Create(curve), run_time=2)

        # 模拟下降的球
        dot = Dot(axes.c2p(2.5, 2.5**2 / 2 + 1), color=ORANGE_ACCENT, radius=0.12)
        self.play(FadeIn(dot))
        for x in [2.0, 1.5, 1.0, 0.5, 0.2, 0.05]:
            self.play(
                dot.animate.move_to(axes.c2p(x, x**2 / 2 + 1)),
                run_time=0.4,
            )
        self.wait(1)
        self.play(FadeOut(axes), FadeOut(curve), FadeOut(dot))

        # 4. 公式
        self.show_formula(
            r"\theta_{t+1} = \theta_t - \alpha \nabla f(\theta_t)",
            "每一步 = 当前位置 - 学习率 × 梯度方向"
        )

        # 5. 要点
        self.show_bullet_points([
            "梯度 ∇f 告诉你哪个方向最陡",
            "学习率 α 控制步子大小",
            "走到梯度≈0的地方，就是极值点",
        ])
