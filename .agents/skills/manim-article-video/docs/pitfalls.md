# 常见坑（快速自查，细节见对应文件）

1. 场景末尾忘调 `pad_to_voice()` → 画面提前定格（step5-scenes.md）
2. 中文乱码/方块 → `Text(..., font="Noto Sans CJK SC")`（step5-scenes.md）
3. `-ql`（15fps）低质量渲染直接当成品 → 成品必须 `-qm`（30fps）（step6-render.md）
4. VLC 同名 SRT 叠加显示 → 字幕备份改名 `xxx-字幕备份.srt`（step8-verify.md）
5. 渲染输出目录猜错 → `-qm` 输出 `media/videos/scenes/1920p30/`（按像素高度命名）（step6-render.md）
6. logo/品牌图背景色与画布不一致 → 先裁圆角透明 PNG（PIL `rounded_rectangle` mask）（step5-scenes.md）
7. 配音稿写公式符号 → TTS 卡顿 2s+（实测 ‖Q‖‖K‖cosθ 停 2.18s）；生成后必须扫段内长静音（≥1.5s），有则口语化重跑（step3-storyboard.md 第 8 条 / step4a-tts.md）
8. `boxed()`/`fit()` 忘加「只缩小不放大」→ 短字符被放大顶出框（Q/K/V/追/猫/qᵢ，2026-08-11 四连发）（step5-scenes.md 规范 9）
9. Text 直渲染 `√d` → √ 与 d 分离不连贯 → 用模板内置 `sqrt_group()`（√ 字形 + 从字形右缘向右延伸的细横线，勿叠粗杠）（step5-scenes.md 规范 16）
10. 标签组整组居中不对准对应条/卡 → 逐个 `next_to` 对准（step5-scenes.md 规范 15）
11. 裸 `FunctionGraph` 无坐标轴 → 曲线悬空，必须 `Axes` + `plot`（step5-scenes.md 规范 16）
12. 弧线角度拍脑袋 → 画过头/对不齐，用 `arctan2` 算起止角（step5-scenes.md 规范 17）
13. 宽文字 `next_to` 到非居中元素后超界 → `set_x(0)` 强制居中（step5-scenes.md 规范 18）
14. 删变量后 FadeOut 残留引用 → NameError，改完 `grep` 复查（2026-08-11 S8 slash→cross）
15. 红字+斜线表示否定 → 用户否：改 `play_red_cross()` 动态大红叉 + 白色文字（step5-scenes.md 规范 19）
16. 场景内新增元素（Axes/装饰）后换页 FadeOut 漏掉它 → 残留到下一页（2026-08-11 S4 坐标轴残留到页3）；改完 grep 每处 FadeOut 与当页元素清单核对
17. `boxed()` 卡片用 `FadeIn` / `GrowFromEdge` 入场 → 不是拉幕（后者会压扁高度）；改 `play_scroll_unroll()`，同组多框等宽（step5-scenes.md 规范 20）
18. 箭头贴框/贴地或换页后还在 → 留缝 + FadeOut 带走箭头（step5-scenes.md 规范 24）
19. 台词在讲公式、画面只有汉字 → 补组装公式，上标锚 UR（step5-scenes.md 规范 25）
20. 发布封面用了 Manim Cover → 改 yairouter 1080×1920（decisions.md 决策 15）
21. 口播录音稿残留 TTS 拟声/停顿标签（`(sighs)`/`<#0.5#>`）→ 真人念不出且干扰停顿分析，口播前必须去掉（step4b-recording.md 门禁 1）
22. 口播录音环境吵/离麦远 → 语音占比 <15%，修音救不回，直接重录（step4b-recording.md 门禁 3/4）
23. 某段录音停顿异常长（≥1.5s）就进下一步 → 字幕时间轴被拖乱，先重录再进 Step 5（step4b-recording.md 门禁 4）
24. scenes.py 的 `at()` 用 TTS 预估时长而不是实际录音 VOICE_DUR → 音画错位；口播必须按录音实测时长写（step4b-recording.md）
25. 某段一致性补偿单频段触顶（+/-6dB）仍对不齐锚段 → 那段频响差异过大救不回，重录再进 Step 5（step4b-recording.md 门禁 5）
26. 闭环流程图用 `CurvedArrow` → 弧线穿圆（RLHF v7 圆内 3009 像素）；用 `arc_curve()`（贝塞尔 + 箭头尖贴圆周），渲染后像素验证（step5-scenes.md 规范 22）
27. 段内换页（段2→段3）FadeOut 漏上段元素 → 残影叠压后文（S7 lab「看重事实」叠 notfixed/shortcuts 5s）；每次 FadeOut 与当页元素清单对账（step5-scenes.md 规范 23）
28. 场景文件里复制粘贴工具函数 → 每篇各自演化、修 bug 漏改副本；用 `scripts/manim_helpers.py` + 模板（step5-scenes.md）
29. 字幕时间轴用预估段长 → AAC padding 累积漂移 ~0.7s，后半段字幕早于画面；build 用 ffprobe 实际段长累计（step7-build.md）。⚠️ 段内也不能只用 pauses.json 重分文本：有 `tts/sentence-boundaries.json` 时必须优先逐句 start/end（见 42）
30. 字幕硬切把英文/数字拆断（InstructGPT、1.3B、DeepSeekMath、77.9%）→ `split_long`/槽分配都按词边界切，英文/数字占比高的句子放宽到 30 字符；写完跑 build --self-test（step7-build.md）
31. 渲染/build 后不派 QA subagent → 漏查事故直接到用户（S7 残影 5s、弧线穿圆）；必须跑 `manim-qa-reviewer`（qa-checklist.md）
32. 配音/录音未确认就设计动画 → 按预估时长排 at()，实际时长一变全部节点重排返工；**先声音后动画**：at() 必须按实测 VOICE_DUR + 字幕时间线（pauses.json / full.subtitle.json）逐条对应（step5-scenes.md 时序门禁）
33. **emoji 当图标**（2026-08-15 实测）→ Manim 0.21 `Text(font="Noto Color Emoji")` 丢彩色字形（CBDT/CBLC 位图），渲染只剩汉字、👍📈⚙️全消失。禁用 emoji，需图标走概念图或自绘矢量原语（vividness.md）
34. **manim 0.21 DecimalNumber 默认 MathTex**（2026-08-15）→ v0.21 起 DecimalNumber 默认 `mob_class=MathTex`，需 latex。**本机已装 texlive（latex 可用）**，但 `counter_value` 仍显式 `mob_class=Text` 规避依赖（数字用 Text 足够，环境波动不受影响）；升级 manim 先单场景 -ql 冒烟确认兼容。复杂公式可用 `MathTex` 渲染（已验证）
35. **AI 概念图带数字/年份**（vividness.md 红线）→ AI 画数字必错（如「2026」画成「206」）；数字/结构/流程必须脚本画图（grow_bar/counter_value/Create），AI 图只管比喻/氛围
36. **transition_out 漏传元素** → 滑出转场漏带走 head/footer/图，残影留到下一场景；必须传当前场景全部可见元素；占用 TAIL 0.6s，pad 剩余，动作覆盖 ≥80% 规则仍满足（vividness.md）
37. **数字对比动画顺序反了**（GRPO 00:49）→ 台词念「从 A 冲到 B」时，画面必须先出 A（旧值淡化标签），再 counter 滚动 A→B；禁止滚动完才补旧值标签（用户反馈「应该先出现 15.6%，再播放 77.9 的动画」）
38. **标签与条/色块重叠**（GRPO 01:22）→ 条图左起点必须与左侧标签右缘留 ≥0.3 缝（S3 段4 标签右缘 -2.3 vs 条左起点 -2.7 重叠 0.4）；数值标签 next_to(条, UP) 的 buff ≥0.25（0.12 贴条上缘）
39. **公式 + 右侧标签超界被裁**（GRPO 02:08）→ 公式 set_width 后右侧再挂标签（如「相对优势」）右缘会超 4.0 被裁；公式右侧标签改放公式下方，或加右缘守卫（get_right()[0] > 3.6 则左移）
40. **内容挤上半屏**（GRPO 用户反馈「内容的编排都太靠上面了」）→ 内容最低点距底 399-800px 是硬性；更上位规则是整页规划：先组稳定 box 再 `layout_page()` 垂直居中（见 41），禁止内容挤上半屏、下半屏空置
41. **页面接龙式排布/留白不等**（2026-08-16 GRPO 用户拍板）→ `next_to(head, DOWN, buff=4.x)` 逐条下接会让页面重心漂移、上下留白不相等；必须每页先 `page_stack()` 组装全部元素的稳定状态（数字用终值占位、闪烁装饰不参与 box），再 `layout_page()` 整页居中。内容高度不足显示带 40% 会 ValueError：放大元素/加大 buff，禁止透明占位撑高。短页典型放大：单卡加高到 3.6、爆点字 56-88、柱体 2.4（step5-scenes.md 整页规划）
42. **文本卡片还是硬方框/透明底/默认色与高亮撞色**（2026-08-16 GRPO 用户反馈）→ 文本方框必须走 `_card()`/`boxed()`：实心 `CARD_FILL=#2C3F60` + `RoundedRectangle(corner_radius=0.18)`；普通 `Rectangle` 只用于柱/数据块/装饰线。高亮色只给强调，不给默认卡片
43. **字幕与声音不同步，但声音与画面同步**（2026-08-16 GRPO 用户反馈）→ 说明 build 的字幕时间轴错了，不是 Manim 动画错。根因：目录里有 `tts/sentence-boundaries.json`（逐句 start/end 与语音严格对应），build 却只认 `pauses.json`，用停顿槽按字数比例重分文本 → 第一句挂 6s、后续整段错位。修复：build 自动优先级改为 `manual-boundaries.json` > `sentence-boundaries.json` > `pauses.json` 兜底 > `full.subtitle.json` > 字数比例；并复测 `subs.srt` 每条与 clip start/end 对齐；孤立标点 clip（如「反思」+「。」）必须由 build 并入前条，禁止纯标点碎片字幕（step7-build.md、decisions #48）
