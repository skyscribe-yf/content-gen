#!/usr/bin/env python3
"""Manim 竖屏视频号场景模板 — 拷贝到新文章的 shipinhao/ 目录改造成 scenes.py

用法：
  cp scripts/manim_scene_template.py content/<日期>-<主题>/shipinhao/scenes.py
  # 然后：改 VOICE_DUR（ffprobe 实测每段配音）、加/改场景类、渲染

渲染：
  python3 -m manim render -ql --disable_caching scenes.py S1 S2 ...   # 布局验证（15fps）
  python3 -m manim render -qm --disable_caching scenes.py S1 S2 ...   # 成品（1080×1920@30fps）

构建（scripts/manim_video_build.py，自动 mux 配音 + 拼接 + 字幕 + 烧录）：
  python3 scripts/manim_video_build.py content/<日期>-<主题>/shipinhao

⚠️ 硬性规则：
  - 每个场景 construct 末尾必须 self.pad_to_voice()（否则时长 < 配音）
  - 中文 Text 必须 font=FONT（Noto Sans CJK SC）
  - footer 用 buff=1.15，勿改回 0.5（会撞底部烧录字幕）
  - 品牌尾卡：品牌图先裁圆角透明 PNG（见 SKILL.md），ImageMobject 引用
"""
from __future__ import annotations

from manim import *

# ---- 竖屏 9:16 画布（不要改，与 build 脚本 PlayRes 绑定）----
config.pixel_width = 1080
config.pixel_height = 1920
config.frame_width = 8.0
config.frame_height = 14.2222
config.background_color = "#16213E"

FONT = "Noto Sans CJK SC"
YELL = "#FFD54A"      # 主强调（与字幕黄一致）
CYAN = "#58C4DD"
GREEN = "#7ED7A0"
RED = "#FF8A80"
MUTED = "#AAB4C8"
WHITE = "#F0F3F8"

# 每段配音时长（ffprobe 实测 tts/sN.wav），渲染时长 = 配音 + TAIL
VOICE_DUR = {"S1": 10.0, "S2": 10.0}
TAIL = 2.5            # 渲染缓冲（build 脚本会截到 0.1s，这里留足动画余量）


def t(text: str, size: float = 34, color: str = WHITE, weight: str = "NORMAL") -> Text:
    return Text(text, font=FONT, font_size=size, color=color, weight=weight)


class _Base(Scene):
    scene_dur = 12.0

    def setup(self):
        self.scene_dur = VOICE_DUR[self.__class__.__name__] + TAIL

    def pad_to_voice(self):
        """末尾补齐等待，使场景总时长 = 配音时长 + TAIL 缓冲。每个 construct 末尾必调。"""
        elapsed = self.time
        target = self.scene_dur
        if target > elapsed:
            self.wait(target - elapsed)

    def footer(self, text: str = "数解AI · <文章标题>"):
        f = t(text, 20, MUTED).to_edge(DOWN, buff=1.15)
        self.add(f)


# ---------------- S1 示例：开场钩子 ----------------
class S1(_Base):
    def construct(self):
        self.footer()
        title = t("<钩子标题>", 46, WHITE, "BOLD").to_edge(UP, buff=1.2)
        self.play(FadeIn(title, shift=DOWN * 0.4))
        # ... 画面元素（方块/箭头/公式，参考 2026-08-03-推理加速/shipinhao/scenes.py 的 8 场景）
        self.wait(1.0)
        self.pad_to_voice()


# ---------------- SN 示例：品牌尾卡（最后一个场景必做）----------------
class S2(_Base):
    def construct(self):
        self.footer("数解AI · <文章标题>")
        # ... 正文建议/总结要点逐个 FadeIn ...

        # 尾卡：正文淡出 → 品牌图 → 关注引导
        self.play(*[FadeOut(m, shift=DOWN * 0.25) for m in self.mobjects], run_time=0.7)

        logo = ImageMobject("avatar-sjai-round.png")   # 圆角透明版，放 shipinhao/ 目录
        logo.scale_to_fit_width(3.6).move_to(UP * 0.9)
        self.play(FadeIn(logo, scale=0.9), run_time=0.9)

        follow = VGroup(
            t("关注「数解AI」", 44, YELL, "BOLD"),
            t("继续拆<系列名>", 28, WHITE),
        ).arrange(DOWN, buff=0.35).next_to(logo, DOWN, buff=0.9)
        self.play(FadeIn(follow, scale=0.85), run_time=0.8)
        self.wait(1.0)
        self.pad_to_voice()


if __name__ == "__main__":
    pass
