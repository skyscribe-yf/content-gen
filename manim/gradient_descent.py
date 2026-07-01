"""
Manim 模板：梯度下降可视化
在2D等高线图上展示梯度下降过程
"""
from manim import *
from manim.base_scene import BaseScene, BLUE_ACCENT, ORANGE_ACCENT, RED_ACCENT

import numpy as np


class GradientDescentViz(BaseScene):
    """梯度下降等高线可视化"""

    def construct(self):
        self.show_title("梯度下降", "在参数空间中找最低点")

        # 直觉
        self.show_intuition("站在山上，每一步往最陡的下坡走")

        # 等高线图
        # ponytail: 简单二次函数 f(x,y) = x² + 2y² + xy
        axes = Axes(
            x_range=[-3, 3], y_range=[-3, 3],
            axis_config={"color": GREY_D, "stroke_width": 1},
        ).scale(0.9)

        # 画等高线
        contours = VGroup()
        for level in [0.5, 1, 2, 4, 8]:
            # 近似画椭圆等高线
            c = Ellipse(
                width=level * 0.8, height=level * 1.2,
                stroke_color=BLUE_ACCENT, stroke_width=1,
                stroke_opacity=0.5, fill_opacity=0,
            )
            contours.add(c)

        self.play(Create(axes), Create(contours), run_time=2)

        # 梯度下降路径
        path_points = [
            np.array([2.5, 1.5, 0]),
            np.array([2.0, 1.0, 0]),
            np.array([1.5, 0.6, 0]),
            np.array([1.0, 0.2, 0]),
            np.array([0.6, -0.1, 0]),
            np.array([0.3, -0.05, 0]),
            np.array([0.1, 0.0, 0]),
        ]
        path_points = [axes.c2p(*p[:2]) + DOWN * 0.3 for p in path_points]

        # 画路径
        path = VGroup()
        for i in range(len(path_points) - 1):
            line = Line(
                path_points[i], path_points[i + 1],
                color=ORANGE_ACCENT, stroke_width=3,
            )
            path.add(line)

        # 动画：逐步走
        dot = Dot(path_points[0], color=RED_ACCENT, radius=0.1)
        self.add(dot)

        for i in range(len(path_points) - 1):
            self.play(
                dot.animate.move_to(path_points[i + 1]),
                Create(path[i]),
                run_time=0.5,
            )
            # 画梯度箭头（从当前点指向下一步方向）
            arrow = Arrow(
                path_points[i],
                path_points[i + 1],
                buff=0.1,
                color=YELLOW,
                stroke_width=2,
                max_tip_length_to_length_ratio=0.3,
            )
            self.play(GrowArrow(arrow), run_time=0.3)
        self.wait(1)

        self.play(FadeOut(axes), FadeOut(contours), FadeOut(path), FadeOut(dot))

        # 公式
        self.show_formula(
            r"\theta_{t+1} = \theta_t - \alpha \nabla f(\theta_t)",
            "新位置 = 当前位置 - 学习率 × 梯度"
        )

        # 三种情况
        self.show_bullet_points([
            "学习率太大 → 跳过最低点，来回震荡",
            "学习率太小 → 走得太慢，浪费时间",
            "学习率刚好 → 稳定收敛到最低点",
        ])
