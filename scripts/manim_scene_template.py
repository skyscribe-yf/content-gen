#!/usr/bin/env python3
"""Manim 竖屏视频号场景模板 — 拷贝到新文章的 shipinhao/ 目录改造成 scenes.py

通用工具（t/_card/boxed/boxrow/fit/sup/sub/type_in/cnode/arc_curve/_Base 全家桶）统一在
  scripts/manim_helpers.py（勿复制进文章目录），本文件只需：
  1. 写 VOICE_DUR（ffprobe 实测每段配音）+ TAIL
  2. 可选覆盖 config.background_color
  3. 写场景类 S1..SN（继承 _Base）

用法：
  cp scripts/manim_scene_template.py content/<日期>-<主题>/shipinhao/scenes.py
  # 然后：改 VOICE_DUR、加/改场景类、渲染

渲染：
  python3 -m manim render -ql --disable_caching scenes.py S1 S2 ...   # 布局验证（15fps）
  python3 -m manim render -qm --disable_caching scenes.py S1 S2 ...   # 成品（1080×1920@30fps）

构建（scripts/manim_video_build.py，自动 mux 配音 + 拼接 + 字幕 + 烧录）：
  python3 scripts/manim_video_build.py content/<日期>-<主题>/shipinhao

⚠️ 硬性规则（详见 .agents/skills/manim-article-video/SKILL.md）：
  - 每个场景 construct 末尾必须 self.pad_to_voice()（否则时长 < 配音）
  - 每页先组装全部元素的稳定状态，再 layout_page() 整页垂直居中：上下留白相等，
    且各 ≤ 显示带 30%（内容高度 ≥ 40%，不足会 ValueError）——禁止 next_to(head) 向下接龙
  - 闪烁/强调类装饰（红叉/circumscribe/indicate/breathe/数字滚动）不参与整页 box
  - 裸文字入场用 type_in()（逐字），卡片用 play_scroll_unroll()（席子式），禁止整段 FadeIn
  - FadeOut 必须带走本页全部元素（含箭头/Axes/装饰），换页无交叉
  - 闭环弧线用 arc_curve()（贝塞尔不穿圆），禁用 CurvedArrow
  - footer 用 buff=1.15，勿改回 0.5（会撞底部烧录字幕）
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

# 可选：覆盖默认背景（#16213E）
# config.background_color = "#0F1A30"

# 每段配音时长（ffprobe 实测 tts/sN.wav），渲染时长 = 配音 + TAIL
VOICE_DUR = {"S1": 10.0, "S2": 10.0}
TAIL = 2.5            # 渲染缓冲（build 脚本会截到 0.1s，这里留足动画余量）


class S1(_Base):
    def construct(self):
        self.bg()
        self.footer()
        head = t("标题", 38, YELL, "BOLD").to_edge(UP, buff=1.2)

        # --- 整页规划标准写法：先建本页全部稳定元素 → 组装 → layout_page 居中 ---
        line = t("一句正文", 30, WHITE)
        card = _card("核心卡片", 5.6, 3.6, CYAN, WHITE, 40, CARD_FILL, "BOLD")
        page = page_stack(line, card, buff=0.8)
        layout_page(page)   # 上下留白相等；内容高度 ≥ 显示带 40%，不足会报错

        self.play(type_in(head, run_time=1.1))
        self.at(1.0)
        self.play(type_in(line, run_time=0.9))       # 位置已在整页规划中定好，动画只负责出现
        self.at(2.2)
        self.play_scroll_unroll(card, run_time=1.2)
        # ... 按配音时间轴 self.at(t) 排动画 ...
        self.pad_to_voice()   # ← 必加，否则场景时长 < 配音时长
