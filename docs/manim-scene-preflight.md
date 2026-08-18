# Manim 场景首轮设计门禁

这套门禁把“渲染后才发现”的问题提前到分镜脚本阶段。它不替代逐帧验收，而是保证第一次设计已经满足最容易反复返工的结构约束。

## 运行

在项目根目录执行：

```bash
python scripts/check_manim_scene.py content/2026-07-04-ai-memory-crash/shipinhao
python scripts/check_manim_scene.py content/2026-07-11-deepseek-moe/shipinhao --strict
# 渲染新场景时也可让 _Base.at() 对回退直接抛错
MANIM_STRICT_TIMELINE=1 python3 -m manim render -ql scenes.py S1
```

CI 或构建脚本应把 `ERROR` 视为失败；`--strict` 会把布局建议也升级为失败。预检器只做静态分析，不会偷偷改写时间点：时间轴错误必须回到分镜稿修正，否则会把一个错误的 `at()` 继续传播到字幕、配音和后续场景。

## 四条硬约束

1. **时间轴只有一个来源。** 优先使用 `sentence-boundaries.json`，并在场景中用 `self.at_clip("S1-c03")`；不得在动作已经播放完之后再调用更早的裸 `self.at()`。每个场景末尾必须 `pad_to_voice()`。
2. **同一行先定槽位，再放动态值。** 用 `dynamic_slot()` 预留最终宽度，和静态标签一起交给 `stable_row()`；数字、百分比、计数器用 `anchor=slot`。不要让动态对象先在 ORIGIN 出现，再 `next_to()` 静态对象。
3. **同一组同一拍出现。** 同一层级的卡片、柱子和标签要在一个 `self.play(...)` / `self.play_parallel(...)` 中并行；纵向堆叠应先 `page_stack()` 完成最终几何，再统一 reveal。连续调用多个会播放的 helper，预检器会提示可能的“逐个出现、前项晚显示”。
4. **卡片按可读性适配。** `_card()` 使用 `fit_text_in_box()` 测量并优先换行，再缩小字号。字号由实际布局后的宽高动态决定，统一受 `CARD_TEXT_MAX_FS` 限制；多行使用 `CARD_TEXT_LINE_SPACING`，禁止在场景中手写字号补丁。固定框越高，文字应利用可用高度；若仍放不下，拆卡或拆页，不得用一行极小字体填充。

## 设计模板

```python
slot = dynamic_slot(1.45, height=0.7)
row = stable_row(t("步骤", 28), slot, buff=0.35)
layout_page(row)
self.add(row)
self.play(type_in(row[0]), run_time=0.7)
self.counter_value(0, 200, size=52, anchor=slot)
```

这段代码的关键不是具体动画，而是最终几何先确定：静态标签、动态槽位和页面布局在任何动画开始前已经完成。这样数字从一位滚到三位时不会把邻居推走，也不会从画布边缘溢出。
