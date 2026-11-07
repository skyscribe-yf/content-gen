# AGENTS.md — 项目级 Agent 配置

本文件只放**硬红线 + 任务路由表**，每次请求全量加载，每 KB 都计费。详细规则、历史数据、示例模板一律现查 `docs/` 对应文件；**禁止把细节抄回本文件**。

## 0. 任务路由表（动手前先定位）

| 要做什么 | 必读 |
|---|---|
| 新文章选题/大纲 | `.agents/skills/grill-me/SKILL.md` + `docs/writing-flow.md` + `docs/viral-article-playbook.md` + `docs/content-matrix.md` + `docs/note-material-source.md` |
| 作者扔素材直出 | `.agents/skills/raw-material-to-wechat-draft/SKILL.md` |
| 起标题/封面字 | `docs/article-title-seo.md` |
| 配图/封面 | `docs/image-generation.md` |
| 贴图（图文消息） | `docs/tietu-viral-playbook.md` + `docs/tietu-infographic-flow.md` |
| 成稿质量核查 | `docs/article-quality-check.md` |
| 发布前最终检查 | `docs/pre-publish-final-check.md` |
| 存草稿箱/发布 | `.agents/skills/baoyu-post-to-wechat/SKILL.md`（grace + blue） |
| 知乎 | `.agents/skills/post-zhihu/SKILL.md` + `docs/zhihu-promotion.md` |
| 小红书 | `docs/xiaohongshu-strategy.md` + `docs/xiaohongshu-copy.md` |
| 视频号 | `.agents/skills/manim-article-video/SKILL.md` 或 `gemini-video-to-shipinhao/SKILL.md` |
| 数据复盘/审计 | `.agents/skills/wechat-data-audit/SKILL.md` + `docs/wechat-data-insights.md` |
| 运营策略/排期 | `docs/wechat-ops.md` |
| 数学公式 | `docs/math-latex.md` |

## 1. 写作流程硬门禁

- 起草大纲前**必须先调 grill-me skill** 与作者讨论；禁止 AI 单方面生成 `.grill/<slug>.md`
- 自动成稿：大纲后采集作者原声槽（**进稿 ≥5 处**），**逐槽交互**（AI 给槽位+建议句，作者逐条输入），禁止批量「过」式代填
- 排版硬规则：① 原声句禁加 ★ 前缀、禁套 blockquote，按正文段落直排；② 正文第一段禁标题开场（禁 `##` 起首、禁把标题抄成第一行）
- 正文 **~2000 字**（含尾部 ≤2500），紧凑优先不拉长
- 动笔前必读爆款经验 `docs/viral-article-playbook.md`，标题/开头/结构逐项对照

→ 详规：`docs/writing-flow.md`

## 2. 封面与配图红线

- 封面文字**必须脚本叠加**：AI 只出无字深色底图（prompt 写明 no text）→ `make_cover.py` 裁 21:9 + PIL 叠金色发光字（Noto Sans CJK Bold）；**禁止 AI 生图直写中文**；封面文字总字数 **≤12**
- 每篇必跑 `scripts/check_cover.py`（21:9 + 文字块高 ≤25% + 每行字高 ≥8% 防裁切；`precheck_and_open.sh` 自动调用）；验收必须放大文字区逐字看底部笔画——PIL 画布高度 ≥ 字体 ascent+descent，否则每字底部被静裁
- 默认后端 yairouter / `gpt-image-2.5-sunburst`（快速用 flare）；上游忽略 size 参数以实际返回为准；prompt 内文字/数字/年份须与正文一致；AI 概念图禁承载数字
- 缺 API Key 先 `source ~/.bash_env` 再重试，禁止未找 key 就换后端

→ 详规（含叠字脚本画布陷阱、降级链）：`docs/image-generation.md`

## 3. 发布硬门禁（顺序不可乱；只存草稿箱，禁止直接发布）

1. **机器质检**：`bash scripts/precheck_and_open.sh content/<日期>-<slug>`（quality_check + check_cover + 微信链接溯源）
2. **VS Code 等作者改**（自动打开 content-gen 工作区定位 weixin.md），AI 停在这里等
3. **复检** `--no-open`；FAIL 若由作者改稿产生，作者拍板，AI 禁擅自改回
4. **才存草稿箱**：`baoyu-post-to-wechat`（grace + blue，remote-api）
- 成稿后必须过 `docs/article-quality-check.md` 全清单（19 项 + 发布后回拉第 20 项 `--published`）
- 封面 `00-cover.png` 必须存在；图片与 `weixin.md` 同级、**无 `images/` 前缀**；目录名 = 发布日期（变更即重命名目录）
- 发布入口必须交 `weixin.md` 走 mdnice 管线，**禁止预渲染 HTML 再发布**；主题双线固定 grace+blue（`.baoyu-skills` 两处 EXTEND.md），改主题两处同改
- 发布后第一时间把微信 URL 写进 frontmatter `wechatUrl`

→ 9 项最终检查清单：`docs/pre-publish-final-check.md`；图片路径事故根因：`docs/wechat-image-path.md`

## 4. 内容红线

- 衍生内容（小红书卡片/文案等）**必须以 `weixin.md` 为准**，禁参照 draft.md；weixin.md 不存在则暂停生成
- 价格/版本号/参数规模**必须实时搜索验证**，标题数字与正文一致；⚠️ DeepSeek V4 Pro 发布于 **2026 年 4 月**，禁写 2025
- 人物禁独立成篇：只能作嵌入技术文的钩子（≤10% 篇幅），标题禁人名开头
- 理论须挂最新国产模型（优先级 DeepSeek-V4 > GLM-5.2 > Kimi K2.6 > Qwen3，引 HF config.json），标注来源
- 文章间导航链接**必须微信 URL**（`https://mp.weixin.qq.com/s/...`），禁相对路径；未发布用 `（待发布）` 标注，发布后补 URL
- 尾部：**不放合集导航、不放下一篇预告**（2026-11-07 废止，合集聚合改由后台勾选）；「🔥 热门文章」必须 `scripts/hot_articles.py --md --cited <本文weixin.md>` 生成（禁手写），行间不留空行、行尾两空格，发布前跑 `--self-check`；正例模板见 `docs/pre-publish-final-check.md` 6c 节
- 文末 3-5 个话题标签（系列 + 主题 + `#数解AI`）
- 数学公式用 LaTeX：独立 `$$...$$`，内联 `$...$`
- 贴图标题/封面定稿前必读 `docs/tietu-viral-playbook.md`：品牌词/事件词前置 + 情绪立场 + 利益钩子至少中两个，封面大字 = 标题核心句，禁谜语，热点当天/次日发 + 开群发
- 小红书：文案写独立 `copy.txt`（纯文本 ≤1000 字、末尾话题标签），禁嵌入 cards.json；卡片 ≤6 张
- 知乎：不支持 Markdown，输出 `.md` + `.html` 两份；公式 Unicode；须有独立价值 + ≥3 处公众号引流钩子

## 5. 素材源与 vault 纪律

- 作者 Obsidian 笔记是**一等素材源**：主 vault `~/vaults/papers`（先读 `AI-Chats/_INDEX.md` 一屏扫题）；旧 vault 在未挂载 NTFS，只读挂载用完卸掉
- 三类内容分清：一手事实（带 arXiv ID/issue 号，仍要开原文复核）/ 作者原生观点（`我的判断` 等，**逐字保留禁改写**）/ AI 归纳（只当线索，进稿重写）
- ⚠️ vault 属作者私人资料：**禁止把原文搬进 `content/` 或提交**；`学习/未命名.md` 含明文 API 密钥，禁止读取/引用
- 贴图归档走 `scripts/tietu_infographic.py`，产物统一放 `content/<日期>-tietu/<标题>/`，禁放项目外目录

→ 详规：`docs/note-material-source.md`、`docs/tietu-infographic-flow.md`

## 6. 数据与运营口径

- 数字事实源：`docs/wechat-data-audit-log.json`（结构见同名 `.schema.json`，操作 `scripts/wechat_audit_log.py`）、`docs/wechat-daily-sources-log.json`、`docs/shipinhao-data-log.json`（视频号独立）
- **每轮审计结论与历史摘要不在本文件** → 现查 `docs/wechat-data-insights.md`（按 0xx 节定位）
- 发布节奏：每天最多 1 篇，固定 **22:00**（恢复期可断更，合格才发优先于日更）
- 恢复期规则、双轨框架、文章级 KPI（T+7 阅读 150–300 / 分享率 ≥10%）→ `docs/wechat-ops.md`
- 标题/台账/frontmatter 一律以后台 `msg_title` 为准；`scripts/verify_published_urls.py` 可全量或单篇核验
- ⚠️ 后台「发表记录」只收录群发记录，未群发已发布文章不在其中，不能当「全量已发布」校验源
- 菜单：「热门文章」≤5 篇手动管理，「全部合集」永久不变 → `docs/wechat-menu.md`

## 7. 关键脚本速查

| 脚本 | 用途 |
|---|---|
| `scripts/precheck_and_open.sh` | 机器质检 + 打开作者工作区（`--no-open` 复检；`--published` 发布后回拉模式） |
| `scripts/quality_check.py` | 质量门禁通用版；每篇定制项（原声/承重数字/术语/内链/豁免）外置到 `content/<篇>/quality_check.json`；`--published` 跳过成稿期门禁只查发布不变量 |
| `scripts/check_cover.py` | 封面 21:9 / 文字块高 / 每行字高门禁 |
| `scripts/hot_articles.py` | 尾部热门文章生成（`--self-check` 验榜单漂移） |
| `scripts/make_cover.py` | 封面叠字通用版；封面文字外置到 `content/<篇>/cover_spec.json`，产物 `00-cover.png` + `cover_meta.json` |
| `scripts/yairouter_img.py` | AI 配图 |
| `scripts/tietu_infographic.py` | 贴图归档 + infographic |
| `scripts/burn_shipinhao.py` | 视频号字幕烧录（禁手拼 ffmpeg） |
| `scripts/wechat_audit_log.py` | 审计台账读写 |

---

*2026-11-07 重构：原 40KB 混合索引/规则/审计历史的版本已拆分——详情进 `docs/` 各专题文件，审计历史移至 `docs/wechat-data-insights.md`，尾部正例模板移至 `docs/pre-publish-final-check.md` 6c 节。改动前完整版见 git 历史。*
