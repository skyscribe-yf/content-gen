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
44. **silencedetect 报的静音边界 ≠ 下一句语音起点**（2026-08-19 ai-memory 四轮修复被证伪）→ silencedetect/能量包络只能检测「有/无声音」，不能区分内容：d=0.35 阈值太粗时静音边界偏移 0.4-2s，把它当「下一句起点」会把字幕挂到错误句子（9.74s 被误当 GLM 起点，实际还在说「在长序列下同时爆炸」）。**能区分内容的唯一手段是 ASR**（MiMo mimo-v2.5-asr，scripts/mimo_srt.py）；用户报「XX:XX 声音滞后」→ 提取 2s 音频 ASR → 与字幕对比 → 细窗精修 sentence-boundaries.json（完整方法见 av-sync.md）
45. **sentence-boundaries.json 直接拿 [0.0, *pauses, dur] 当字幕边界**（2026-08-19 根因）→ 边界错会固化进 SB 且无校验直接进成品。build 已内置 `validate_sentence_ts()`（文本一致性 fail-fast + 边界单调性 + pauses 漂移 >0.4s 告警），勿绕开；精修边界后必须过 build 校验 + 复验用户报点。scenes.py 配套坑：挂 `at_clip()` 的动画 run_time 越过下一 clip 起点会触发 at_strict 报错，短句 clip（<0.5s）动画 run_time ≤ clip 时长 - 0.05s（S8 c21「评」0.36s，FadeIn 0.6s → 回退）
46. **`tts_sb_create.py` 的 TAG_RE 漏 `<#0.5#>` 停顿标签**（2026-10-03 TRPO 篇 root cause）→ SB 的 clip 文本残留 `<#0.5#>`，与 build 的 `strip_tts_tags` 口径不一致 → `validate_sentence_ts` fail-fast（「SB 文本与配音不一致」）。修：`TAG_RE` 增加 `<#[\d.]+#>`（已固化）；顺带发现剥离后 clip 起点更准（S2-c03 6.00→6.59，停顿不再算进字幕），**剥离会合并相邻 clip（S5 11→10 条）→ 场景里所有 `at_clip` id 必须重新核对语义，不能只看 id 是否存在**
47. **`bg()` 背景矩形尺寸刚好等于画布**（2026-10-03 TRPO 篇 QA A18）→ `camera_zoom_to` 推近时相机 frame 移出画布边界，顶部露出 `config.background_color` 平板带 + 硬缝（实测 134px、3.2s）。修：背景矩形放大到 `2.2×FW × 2.2×FH`、渐变改 5 色等分 `[c0,c0,c1,c2,c2]`（已固化进 `manim_helpers.bg()`），画面内仍是原来的三段渐变
48. **末段 `transition_out` 早于配音收尾**（2026-10-03 TRPO 篇 QA X1）→ 元素全部退场后仍剩 1.2-2.4s 纯背景空屏而配音继续念（S1/S2/S3/S5 实测）。修：转场前插入显式 `wait()` 把转场窗口对齐到「末句配音结束 - 0.6s」，使滑出恰好收在段末；`TAIL=0.1` 吸收不了 0.6s 转场，别指望 pad 兜底
49. **预检器（check_manim_scene --strict）三条硬约定**（2026-10-05 PPO 篇实测，违反即 FAIL）：① 裸 `self.at(t)` 必须落在句边界 ±0.12s 内（at_not_on_boundary）——段内多拍不要用裸 at()；② **不要用 `at_clip(id, offset)` 做段内锚定**：运行时正确，但 checker 按 clip 原始起点算 next_at，前一个动作全部误报 action_overrun；③ 相邻两个「单动画 reveal」（play/scroll_unroll/counter_value/grow_bar，animation_count 都是 1）必报 serial_animation——解法是合并成一拍多动画 play（count≥2 不触发）：双条对比用多条同拍生长 helper（_grow_bars，ValueTracker 每条一个、updater 复刻 grow_bar）、双数字滚动把另一条 tracker 的 `animate.set_value` 挂进 counter_value 的 extra_anims、多卡片入场用 `play_scroll_unroll_many`。另：15/30fps 帧取整会把段内最后一个动作推过下一 clip 起点（1.5s→1.533s），段内末动作与下一 clip 边界留 ≥0.15s 余量
50. **manim 解释器路径**：本机默认 `python3`（~/python3）**没有 manim**，`python3 -m manim` 报 No module named manim；渲染用 `/usr/bin/python3 -m manim`（Manim Community 0.21.0 在系统 python 的 user site）
