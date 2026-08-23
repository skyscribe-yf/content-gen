# 检查点：大模型价格战续集贴图

> 素材直出 · 检查点产物（作者确认前禁止写正文/出图）
> 素材：`raw.md`（2026-08-23）｜ 事实核对：DeepSeek/OpenCode/CommandCode/Ollama 官方文档 + `../token-stats` 实测数据（近 3 天 2026-08-20 ~ 08-22）

## 一、标题（已定，作者确认）

> ⚠️ 08-22 复盘红线：标题与开头不能有「续集/上篇/拆给你看」痕迹；「大模型价格战」话题标签进文末。

**✅ 免费模型夹击，DeepSeek凭什么还是最爽**（18 字，反常识提问 + 热点）

（关键词建议：DeepSeek 供应商 / API 价格 / 免费模型；发文时摘要补 2-3 个长尾词。）

## 二、结构大纲（贴图体 · 短段落 · 先结论后吐槽）

1. **开头结论**：免费模型夹击下（ox-alpha-free、muse-spark、mimo 折扣们），绕一圈还是 DeepSeek 供应商最爽——因为输出速度。
2. **新面孔 Dim Agent**：1 毛钱 1.3 亿 token、速度极快——可惜性价比没那么高。（⚠️ 素材缺口，见第五节）
3. **OpenCode**：额度恢复了点，但大不如前。数据佐证：8/18 后 DeepSeek 用量掉到 0，现在跑免费模型；官方当前 DeepSeek V4 Pro 月额度只剩 $15（最初 $60）。
4. **Ollama 20 美金**：还是很耐用，偶尔速度慢。实测近 3 天跑了 520M tokens 主力就是它；速度 p50 ≈ 276 tps 但偶发慢。
5. **官方 API**：贵得离谱。v4-pro 平峰 4.5/13.5 元每百万，高峰 9/27——第三方几乎 1/10。
6. **DeepSeek 周末平峰**：周末全天算平峰（半价），但依然很贵。
7. **CommandCode Go**：额度本来很多，均价≈OpenCode 的 1/3；但速度不稳定 + 周限（每周 $6、5 小时 $3 滚动窗口）之后，1 美金套餐用起来极为不爽。
8. **结尾互动**：开放式问题（你现在的主力 API 是哪个？评论区交流交流）。

## 三、原声句清单（原文逐字进稿，只修错别字）

| # | 原声句 | 位置 |
|---|--------|------|
| 1 | 各种免费模型夹击来袭下，需要爽用还得是输出速度快的 deepSeek 供应商 | 开头 |
| 2 | 这次新加入了 Dim Agent，1毛钱可以用大1.3亿token，速度极快，可惜性价比没有那么高 | 第 2 段 |
| 3 | OpenCode 的额度虽然有所恢复，但是已经大不如前了 | 第 3 段 |
| 4 | Ollama 20美金套餐依然是很耐用的，就是偶尔速度有点慢 | 第 4 段 |
| 5 | 官方的 API，那就是贵的离谱了！ | 第 5 段 |
| 6 | 好在 DeepSeek 把周末的价格调整到了平峰，但是依然是很贵的存在！ | 第 6 段 |
| 7 | commandcode go 套餐的额度本来也很多，均价大约是 opencode 的1/3，但是速度有些不稳定，而且加上了周限之后的1美金套餐，用起来极为不爽（「和 ollama pro 持平」按作者决定删除） | 第 7 段 |

## 四、配图清单（贴图规格 · 短图文）

### 概念图（AI 生成，禁止承载具体数字/年份，封面 21:9）

1. **封面 21:9**：免费模型大军围攻一座「速度」堡垒（DeepSeek 主题），攻防感
2. 第 4 段 Ollama：堡垒里打盹的守卫（耐用但偶尔慢）
3. 第 5-6 段：高山上的贵价招牌（官方 API 高不可攀）→ 可选，视篇幅

### 脚本数据图（数字必须用脚本画，禁止 AI 图承载）

1. **各家「每百万 token 实际支出 + 输出速度」组合图**：Dim Agent ≈0.0006 元/M、opencode-go ≈0.011、ollama ≈0.143、官方 ≈0（近乎不用）；速度维度标 ollama p50≈276 tps（近 3 天 08/20-22）→ 一张组合对比图

> 贴图惯例 2-3 张图（参考 opencode 杀疯了 2 张 / 第三方 3 张）；如需 0 图版本（纯文字贴图）也可，作者定。

## 五、素材缺口（已全部闭环 ✓）

1. **Dim Agent ✅ 已核实**：您确认 tracker 里标记 dim 的就是 Dim Agent 的 DeepSeek（非官方，fix 中）。实测对上了——token-stats 里 provider=deepseek + key 前缀 N/A 的批次（7/31 起）：**596M tokens，累计可核算成本 ≈ 0.35 元**（≈0.0006 元/M），「1 毛钱 1.3 亿 token」量级吻合；主力 deepseek-v4-flash 470.9M + v4-pro 83M + vision-exp 42.4M（8/22 起，每 M ≈ 0.005-0.011 元）。⚠️ 该批次 tps/ttft 字段为空（tracker fix 中），「速度极快」为作者体感，正文照原声写。
2. **「和 ollama pro 持平」✅ 删除**（作者确认）。
3. **免费模型点名 ✅ 允许**：正文可点名 ox-alpha-free、muse-spark 1.2 contributor、MiMo 折扣（实测 opencode-go 近 3 天 459M 全为这些）。
4. **「OpenCode 额度有所恢复」时点 ✅ 保留原声**：官方 8/18 额度 $60→$30（pricing 注释），8/21 文档更新后 V4 Pro $15/月；您实测 8/18 起 opencode-go 的 DeepSeek 用量≈0（转免费模型），「恢复但不复当年」以原声表达，不引精确时点。

## 六、事实核对表（已查证，正文引用口径）

| 事实 | 结论 | 来源 |
|------|------|------|
| **Dim Agent** | provider=deepseek + key=N/A 批次：596M tokens / ≈0.35 元（≈0.0006 元/M），7/31 起；flash 470.9M + pro 83M + vision-exp 42.4M；tps/ttft 字段暂空（tracker fix 中） | token-stats |
| DeepSeek 官方峰谷价 | 高峰=北京时间周一至周五 9-12/14-18，**周末全天平峰（半价）**；v4-pro 平峰 4.5/13.5 元/M，高峰 9/27 元/M | api-docs.deepseek.com（08-23 抓取） |
| OpenCode Go | $5 首月/$10 月；限 5 小时 $12、每周 $30、每月 $60；**DeepSeek V4 Pro 单模型月额度 $15、Flash $30**；Ox Alpha Free 限时免费 | opencode.ai/docs/go（更新于 08-22） |
| 您的 OpenCode 实测 | 8/18 前 DeepSeek 深用（592M/8-14~17），8/18 起≈0，转 muse-spark/ox-alpha 免费模型；近 3 天 459M 全为免费/超低价模型 | token-stats |
| Ollama Pro | $20/月 或 $200/年；50× Free 用量；5 小时+每周滚动上限；并发 3 个云模型（超出排队=「偶尔慢」来源之一） | ollama.com/pricing |
| 您的 Ollama 实测 | 近 3 天 520M tokens（全部 provider 第 1）；tps p50≈276 | token-stats |
| CommandCode Go | $1/月 → $10 credits；**5 小时 $3 + 每周 $6 滚动限额**；DeepSeek 峰谷价与官方一致 | commandcode.ai/docs/pricing-limits |
| 您的 CommandCode 实测 | 8/16 单日 275M → 8/17 后断崖（周限生效）；近 3 天仅 48M；tps p10 122 / p50 199（波动大），ttft p50≈6.3s 明显偏慢 | token-stats |
| 均价 1/3 | commandcode 0.0019 vs opencode-go 0.0066 元/M（近 14 天，≈29%） | token-stats |
| 官方 API 用量 | 近 3 天自家只用 19.6M（vision-exp），基本不用官方 | token-stats |

---

**请作者确认以上内容（尤其第五节 4 个缺口 + 第三节原声是否可原样进稿）；确认后再写 `weixin.md`、出图。**
