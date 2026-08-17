# 竖屏整页规划（page layout asset，2026-08-16 用户拍板）

本文是 Manim 视频号**页面排版**的唯一资产文档：任何场景写页面前先读本文。
`step5-scenes.md` 保留全部硬性规范；本文只沉淀「整页规划」算法与用法。

## 1. 目标

每次换页都按**该页全部元素的最终稳定状态**规划一个完整屏幕：

- 先得到整页 box；
- 再计算整页 box 在显示带中的位置；
- 上下边界留白**严格相等**，且各边 ≤ 显示带 30%（内容高度 ≥ 显示带 40%）；
- 元素位置全部由整页 box 派生，禁止「第一条放中间/顶上，其余向下平铺」的接龙式排布。

## 2. 显示带常量（`scripts/manim_helpers.py` 已固化）

| 常量 | 值 | 含义 |
|---|---|---|
| `PAGE_TOP` | `FH * 0.32` | 显示带上边界（标题下方） |
| `PAGE_BOTTOM` | `-FH * 0.292` | 显示带下边界（距底 ≈400px，字幕上方） |
| `PAGE_BAND` | `PAGE_TOP - PAGE_BOTTOM` | 整页可用高度 |
| `MAX_PAGE_MARGIN` | `0.30` | 上下留白各 ≤ 显示带 30% |
| `MIN_PAGE_FILL` | `0.40` | 内容高度 ≥ 显示带 40% |

## 3. 两段式算法

```text
输入：本页全部稳定元素 mobs[]
1. 组装整页 box：
   page = page_stack(*mobs, buff=页内间距)
2. 整页放版：
   layout_page(page)
     - page.set_x(0)
     - min_h = PAGE_BAND * MIN_PAGE_FILL
     - if page.height < min_h: raise ValueError   # 强制先解决短页
     - if page.height > PAGE_BAND: scale_to_fit_height(PAGE_BAND)
     - page.set_y((PAGE_TOP + PAGE_BOTTOM) / 2)   # 上下留白相等
3. 元素动画只负责“出现”，不负责改位置：
   type_in / play_scroll_unroll / FadeIn / counter 逐个播放
```

## 4. 稳定 box 规则

- **数字**：先用透明 `Rectangle` 按终值尺寸占位，`_cnt()`/`counter_value()` 实际数字 `move_to(占位)`；滚动过程不参与 box。
- **公式 morph**：`num_f → frac_f → full_f` 三段全部先 `move_to(formula_slot)`，整页只放一个 formula_slot。
- **闪烁/强调装饰**：`play_red_cross`、`circumscribe`、`indicate`、`breathe`、红叉/勾、轨迹拖尾都**不参与** `layout_page` box。
- **概念图/曲线**：以 Manim bbox 为规划依据；渲染后抽帧复核可见内容仍在安全区。
- **透明占位**：只允许数字终值占位，禁止用透明占位把短页“撑高”。

## 5. 短页满足 40% 的放大清单

内容高度不足显示带 40% 时，优先按页型放大，不要改显示带：

| 页型 | 手段（实测值） |
|---|---|
| 单卡页 | `_card(w≈6.2~6.6, h=3.6, fs=34~40)` |
| 三步/三原因横卡 | 卡高 2.0、`buff=0.9` |
| 两行爆点 | 字号 52/88、`buff=1.9` |
| 上下箭头 + 问号 | `？` 字号 170、箭头 100、`buff=1.3` |
| 两栏选择卡 | 卡高 1.5、标题 38、副标 30、`buff=0.8` |
| 长句 + 关键词 | 关键词 42~64、`buff=0.8~0.85` |
| 文字 + 柱/网格 | 柱高 2.4、文字 32、`buff=0.7` |

## 6. 正确 / 错误示例

```python
# ✅ 先组页，再放版
line = t("把同一个 prompt 想成同一道题", 30, WHITE)
num_ph = Rectangle(width=2.2, height=0.8, fill_opacity=0, stroke_opacity=0)
page = page_stack(line, num_ph, buff=0.8)
layout_page(page)
self.play(type_in(line, run_time=0.9))
num = self.counter_value(0, 64, suffix=" 个").move_to(num_ph)

# ❌ 从标题往下接龙：页面重心漂移、留白不等
line.next_to(head, DOWN, buff=4.5)
num_ph.next_to(line, DOWN, buff=0.4)
```

## 7. 代码资产位置

- `scripts/manim_helpers.py`：`PAGE_*`、`layout_page()`、`page_stack()`
- `scripts/manim_scene_template.py`：新场景骨架已内置整页规划示例
- `scenes_parts/S*.py`：多 agent 分工时，每页同样调 `page_stack()`/`layout_page()`，合并后由模板头部提供函数

## 8. 回归测试资产

- `tests/test_manim_layout.py`：显示带契约、page_stack 居中、layout_page 等留白、短页 ValueError、超高页缩放
- `tests/test_manim_video_build.py`：sentence-boundaries 优先级、pauses 兜底、英文/数字串不拆断

## 9. QA 钩子

- `qa-checklist.md` A10：整页规划 + 上下留白相等 + 内容最低点 399~800px
- `qa-checklist.md` A20：稳定 box 规则（闪烁元素不参与、数字终值占位）
- `pitfalls.md` #41：接龙式排布/留白不等
- `decisions.md` #47：生效决策与沿革
