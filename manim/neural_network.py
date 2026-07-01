"""
Manim 模板：神经网络可视化
一个简单的全连接层前向传播动画
"""
from manim import *
from manim.base_scene import BaseScene, BLUE_ACCENT, ORANGE_ACCENT, GREEN_ACCENT

# ponytail: 单文件自包含，不依赖外部数据


class NeuralNetworkViz(BaseScene):
    """神经网络前向传播可视化"""

    def construct(self):
        self.show_title("神经网络", "Neural Network")

        # 直觉
        self.show_intuition("一群投票者，每人投一票，加权汇总后做决定")

        # 画一个 3-4-2 的网络
        layers = [3, 4, 2]
        layer_x = [-3, 0, 3]
        neurons = []
        colors = [BLUE_ACCENT, GREEN_ACCENT, ORANGE_ACCENT]

        for i, (n, x) in enumerate(zip(layers, layer_x)):
            layer_neurons = []
            for j in range(n):
                pos = UP * (1 - j * (2 / (n - 1))) if n > 1 else ORIGIN
                circle = Circle(radius=0.3, color=colors[i], stroke_width=2)
                circle.move_to(RIGHT * x + pos)
                layer_neurons.append(circle)
            neurons.append(layer_neurons)

        # 画连接线
        connections = []
        for i in range(len(neurons) - 1):
            for n1 in neurons[i]:
                for n2 in neurons[i + 1]:
                    line = Line(
                        n1.get_center(), n2.get_center(),
                        stroke_width=1, color=GREY_D, stroke_opacity=0.5
                    )
                    connections.append(line)

        all_neurons = [n for layer in neurons for n in layer]
        all_connections = VGroup(*connections)
        all_neurons_group = VGroup(*all_neurons)

        # 逐步动画
        # 先画连接
        self.play(Create(all_connections), run_time=1.5)
        # 再画神经元
        self.play(Create(all_neurons_group), run_time=1.5)
        self.wait(1)

        # 前向传播动画：信号从左到右流动
        for i in range(len(neurons) - 1):
            # 点亮当前层
            for n in neurons[i]:
                self.play(
                    n.animate.set_fill(colors[i], opacity=0.6),
                    run_time=0.2,
                )
            # 信号传播
            for n1 in neurons[i]:
                for n2 in neurons[i + 1]:
                    dot = Dot(
                        n1.get_center(), color=colors[i], radius=0.06
                    )
                    self.add(dot)
                    self.play(
                        dot.animate.move_to(n2.get_center()),
                        run_time=0.3,
                    )
                    self.remove(dot)
            self.wait(0.5)

        # 点亮输出层
        for n in neurons[-1]:
            self.play(
                n.animate.set_fill(colors[-1], opacity=0.6),
                run_time=0.3,
            )
        self.wait(1)

        # 清理
        self.play(
            FadeOut(all_connections), FadeOut(all_neurons_group),
        )

        # 公式
        self.show_formula(
            r"a^{(l)} = \sigma(W^{(l)} a^{(l-1)} + b^{(l)})",
            "每一层 = 激活函数(权重 × 上层输出 + 偏置)"
        )

        # 要点
        self.show_bullet_points([
            "权重 W 控制每个连接的强度",
            "偏置 b 是阈值，超过才激活",
            "激活函数 σ 引入非线性",
        ])
