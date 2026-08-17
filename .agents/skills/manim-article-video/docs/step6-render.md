# Step 6 渲染验证（-ql 冒烟 → -qm 成品）

```bash
# 先低质量冒烟（快），抽帧检查布局/中文渲染/越界
python3 -m manim render -ql --disable_caching scenes.py S1 S2 ...
# 再高质量渲染（1080×1920@30fps，输出在 media/videos/scenes/1920p30/）
python3 -m manim render -qm --disable_caching scenes.py S1 S2 S3 S4 S5 S6 S7 S8
```

⚠️ `-qm` 输出目录名按像素高度叫 `1920p30`（不是 1080p30）；`-ql` 是 15fps 只用于布局验证。

**每个场景 `construct` 末尾必须 `pad_to_voice()`**，动画动作按配音时间轴 `at(t)` 排布（见 step5-scenes.md）。

## 渲染后 → 派 manim-qa-reviewer

渲染完成（及 build 完成）后，**必须派 `.pi/agents/manim-qa-reviewer` subagent 跑质量检查**，逐项过 `docs/qa-checklist.md` 的检查单（每项都是事故换来的，勿跳）。**宣称完成前必须跑完**，用户时间轴反馈大多是这里漏查：

```bash
# 渲染后：检查 build_SN.mp4 无字幕帧 + scenes.py 代码审查（布局/重叠/FadeOut/像素贴边/弧线穿圆）
# 构建后：检查成片（字幕/音画/静音/尾卡）
```

QA 报告 PASS/FAIL + 证据（文件:行号 / 帧图路径）。FAIL 项由主 agent 修复后重渲染、重跑 QA，直到全 PASS。

自查要点（QA subagent 的检查来源，亦可先自查）：

1. 元素完整 + 整页规划合规：无出画布、无截断；每页先 `page_stack()` 组稳定 box 再 `layout_page()`，上下留白相等且各 ≤ 显示带 30%（内容高度 ≥40%，`layout_page` 已硬校验）；无 `next_to(head, DOWN, buff=4.x)` 接龙
2. 无相互重叠：同屏元素间不压叠（允许刻意叠放的 z_index 场景）
3. 无压 footer/标题：底部 y>1800 只应有 footer，顶部 y<120 只应有标题
4. 代码审查：场景内每个 mobject 都能沿 next_to/arrange 链追溯到锚点，无裸 move_to 魔法数字
5. 像素级贴边扫描（必做，肉眼常漏）：每场景抽 70% 时间点帧，非背景像素到画布边缘距离 ≤2px 即为超界（2026-08-10 事故：S5 标签组总宽 8.3 单位 > 画布 8 单位，「左」/「块」字各被裁一半）
6. 框内文字溢出：每场景 30%/60%/90% 三档抽帧逐个框目测（badge 首字母被裁、token 块长英文溢出、9 字描述超框）；动画中帧（30%/60%）检查 FadeIn 中间态无错位
7. 箭头语义：弧线起终点在正确元素上（循环箭头贴元素顶=「帽子」）；链路折线箭头行间位置正确；**连接箭头不贴框/贴地、两端居中、换页后无残留**
8. 弧线遮挡：弧线扫过区域内不得有文字/框/标签——像素验证先排除底部字幕区（y>1450 黄色像素=字幕），再判断黄/绿元素相对位置
9. **换页 FadeOut 清单**：每个 Scene 的每次 FadeOut 与当页 `play`/`add` 过的 mobject 对账（含 Arrow/Axes/head/prefix、段内换页）。漏一个即 FAIL（预训练 prefix/gpt 残留、归一化箭头残留、RLHF S7 lab/shortcuts 残留）
10. **音画**：`full.subtitle.json` 句子起点 vs `at()`，关键词画面偏差 >1s 即 FAIL；最后一个 `play` ≥ 配音 80%
11. **公式**：台词含「等于 / NLL / RMSNorm / 公式」时抽对应帧，须见组装公式且上标在字母 UR
12. **同组 boxed()**：宽度相同 + 入场是 `play_scroll_unroll`（grep `FadeIn(.*boxed` / `FadeIn(l[0-9]` 即嫌疑）
13. **开场模型小字**：原理系列 S1 前 3 秒须有「以 XX 为例」MUTED 行
14. **字幕不裁**：成品抽字幕帧，黄字右缘 x<1036（左右各留 ≥44px）
