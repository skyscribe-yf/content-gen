"""
Manim场景：Softmax：温和的投票
系列：深度学习基础
"""
from manim import *
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from base_scene import BaseScene


class SoftmaxScene(BaseScene):
    """Softmax：温和的投票——把任意分数变成温和的概率投票"""

    def construct(self):
        # 1. 驱动问题
        self.show_title("Softmax", 
                        "把任意分数变成温和的概率投票")

        # 2. 直觉
        self.show_intuition("把任意分数变成温和的概率投票")

        # 3. 数学原理
        # self.show_formula(r"...", "解释")

        # 4. 算法可视化
        # TODO: 用Manim动画展示数值稳定实现

        # 5. 实测（融合篇）
        # TODO: 分屏展示模型输出

        # 6. 回扣
        # self.show_intuition("实测验证了...")
