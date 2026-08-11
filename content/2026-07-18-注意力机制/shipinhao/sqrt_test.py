from manim import *
from scenes import sqrt_group, FONT, YELL, WHITE, CYAN

config.pixel_width = 1080
config.pixel_height = 1920
config.frame_width = 8.0
config.frame_height = 14.2222
config.background_color = "#16213E"

class SqrtTest(Scene):
    def construct(self):
        # 三档字号并排
        g26 = sqrt_group(26, CYAN)
        g52 = sqrt_group(52, YELL)
        g52b = sqrt_group(52, YELL, "BOLD")
        row = VGroup(g26, g52, g52b).arrange(RIGHT, buff=1.5).move_to(ORIGIN)
        self.add(row)
