# AGENTS.md — 项目级 Agent 配置

本文件是规则索引，详细内容拆分到 `docs/` 下各专题文档。

## 文章写作流程（硬性门禁）

起草大纲前**必须先调用 grill-me skill** 与作者深入讨论（`.agents/skills/grill-me/SKILL.md`）。禁止 AI 单方面生成 `.grill/<slug>.md` 日志。自动成稿在大纲之后还必须采集作者原声槽（进稿 ≥5 处）才写 `weixin.md`——**逐槽交互**：AI 给槽位位置+建议句，作者逐条手动输入，全部槽位走完才结束，禁止批量「过」式代填。详见 [`docs/writing-flow.md`](docs/writing-flow.md)。

**正文篇幅：一般 2000 字左右**（可视字数，含尾部总计 ≤2500），紧凑优先、不拉长（2026-09-13 作者口径）。

启动新文章（选题/大纲阶段）**必须先读爆款经验** [`docs/viral-article-playbook.md`](docs/viral-article-playbook.md)，标题/开头/结构逐项对照揣摩后再动笔。

## 素材直出公众号草稿 Skill

项目级 skill：[`.agents/skills/raw-material-to-wechat-draft/SKILL.md`](.agents/skills/raw-material-to-wechat-draft/SKILL.md)

封装了「作者扔原始素材 → AI 归纳整理（原声句逐字保留）→ 作者检查点确认 → 双轨配图 → 渲染 → 存公众号草稿箱」流程。关键规则：

- 素材入口：`scripts/new-raw-topic.sh` 创建 `content/<日期>-<slug>/raw.md`，作者把想表达的一切贴进去
- 动笔前必须读风格语料 `branding/style-corpus/style-features.md`（手敲贴图 + 长文 raw.md 金标准；2026-08-23 及之后贴图不当风格样本）
- 原声句逐字保留，AI 只补结构、过渡和公众号惯例
- 整理后必须停在检查点（结构 + 原声句清单 + 配图清单），作者确认前禁止出图
- 双轨配图：AI 概念图 4-6 张（封面 21:9），数字/结构用脚本画图，AI 图禁止承载数字
- 只存草稿箱（`--submit` / `draft/add`），禁止直接发布

## 数学公式

详见 [`docs/math-latex.md`](docs/math-latex.md)。

规则：使用 LaTeX 公式。独立公式用 `$$...$$`，内联公式用 `$...$`。

## 图片生成

默认后端：**yairouter**，客户端 `scripts/yairouter_img.py`。默认模型 **gpt-image-2.5-sunburst**；快速出图可用 **gpt-image-2.5-flare**（`--model` / cards.json 的 `model` 字段）；API 失败自动沿链降级 `gpt-image-2.5-flare → grok-imagine-image-quality`（grok 不支持 size 参数、输出固定 1024x1024 JPEG 需裁剪封面，脚本自动转真 PNG，详见 [`docs/image-generation.md`](docs/image-generation.md)）。默认 1K，封面图强制 **21:9**。⚠️ 上游 API 忽略 size 参数（2026-08-07 实测；2026-09-09 复验 2.5 系列），输出尺寸以实际返回为准。prompt 内文字/数字/年份必须与正文一致。详细流程见 [`docs/image-generation.md`](docs/image-generation.md)。

**API Key 规则**：若 shell 环境 / `.env` 中找不到所需 API Key（如 `YAI_API_KEY`、`MINIMAX_API_KEY` 等），**先 `source ~/.bash_env`** 再重试，不要直接报「缺 key」或擅自换后端。`~/.bash_env` 是作者维护的全局密钥文件（含 `YAI_API_KEY` 等）。

## 贴图素材归档 + Infographic 生成流程

需要「把某批贴图按发表时间下载归档、读图提取主要文字、再生成一张 info graphic 图片」时，**必须走固化流程**：`scripts/tietu_infographic.py`（读取公众号发表记录 `item_show_type=8` 贴图 → 按 `content/<日期>-tietu/<标题>/` 归档原始素材 → OCR 写 `summary.json` → 按 briefs 写 `prompt.md` 并生成每目录一张 `infographic.png`）。**所有产物（原始素材、识别文案、prompt、最终图）统一放在 `content/` 下，按发布日期 + 标题组织**，禁止放项目外目录。详细步骤、目录约定、依赖与坑（PNG-as-jpg、size 参数被忽略、CDN URL 需带 query 否则 400、ConnectionError 重跑）见 [`docs/tietu-infographic-flow.md`](docs/tietu-infographic-flow.md)。

触发词示例：「把最近的贴图归档并生成信息图」「贴图原图下载 + infographic」。执行前先 `source ~/.bash_env` 取 `YAI_API_KEY`；贴图清单以 `branding/style-corpus/publish-data*.json` 的 `item_show_type=8` 为准，发布时间缺失时从贴图页 `send_time` 回填。

## 多平台内容一致性

衍生内容（小红书卡片/文案等）**必须以 `weixin.md` 为准**，禁止参照 `draft.md`。weixin.md 不存在则暂停生成。

## 小红书文案格式

详见 [`docs/xiaohongshu-copy.md`](docs/xiaohongshu-copy.md)。

规则：文案写入独立 `copy.txt`，禁止嵌入 `cards.json` 或内联输出。纯文本、≤1000字、末尾带话题标签。

## 知乎推广回答

知乎不支持 Markdown → 输出 `.md` + `.html` 两份文件。公式用 Unicode，回答须有独立价值 + ≥3 处公众号引流钩子。详见 [`docs/zhihu-promotion.md`](docs/zhihu-promotion.md)。

## 知乎发布 Skill

项目级 skill：[`.agents/skills/post-zhihu/SKILL.md`](.agents/skills/post-zhihu/SKILL.md)

封装了「内容裁剪 → 链接替换 → LaTeX 公式保留 → HTML 生成 → CDP 粘贴 → 图片上传 → 发布回写」的知乎专栏/回答全自动发布流程。关键规则：
- 知乎原生支持 MathJax，公式保留 `$$...$$` 不转 Unicode
- 正文中的微信链接必须替换为知乎链接（查 `templates/zhihu-urls.yaml`）
- 图片必须串行上传到知乎 CDN（`pic*.zhihu.com`），禁止外部图床
- 发布后必须回填知乎 URL 到 `draft-status.yaml` 的 `zhihu_url` 字段
- 末尾引流只提及公众号名称和回复关键词，不放可点击外链

## 小红书内容策略

入口必须是痛点（不是概念）。封面图钩子 ≤8 字，标签用长尾词。详见 [`docs/xiaohongshu-strategy.md`](docs/xiaohongshu-strategy.md)。

## 微信文章链接规则

- **默认主题 grace**（对应发布管线 mdnice `scienceBlue`，主色蓝 `#0F4C81`）：项目已配置 `.baoyu-skills/baoyu-markdown-to-html/EXTEND.md`（预览）与 `.baoyu-skills/baoyu-post-to-wechat/EXTEND.md`（发布）双线 `default_theme: grace`、`default_color: blue`，渲染无需显式传 `--theme`/`--color`。改主题在这里改，两处同改。
- 系列导航链接**必须**是微信 URL（`https://mp.weixin.qq.com/s/...`），禁止相对路径
- 未发布用 `（待发布）` 标注，发布后补 URL
- 发布后**必须**把微信 URL 记入 frontmatter `wechatUrl` 字段，供后续文章引用
- **尾部惯例**：尾部只用合集链接收纳逐篇链接，不用单篇链接堆叠
- **尾部「🔥 热门文章」**：链接**必须**由 `scripts/hot_articles.py --md --cited <本文weixin.md>` 生成（数据源：最近审计 `docs/wechat-data-audit-log.json` 聚合历史最高阅读量 Top 6，自动过滤贴图，再追加本文引用到的相关公众号文章），**禁止**手写或凭记忆挑最近发布的文章；生成的链接行间**不留空行**（空行会被渲染成独立段落 `<p margin:1.5em>`，微信端视觉上多出一条空行），**每行行尾带两个空格**（Markdown 硬换行→`<br>`，否则 mdnice 软换行渲染成裸 `\n`→微信编辑器拼成一行或拆成带 padding 的独立段）；发布前跑一遍 `--self-check` 确认榜单未漂移

```yaml
---
title: "梯度下降：蒙着眼下山"
wechatUrl: "https://mp.weixin.qq.com/s/abc123"
---
```

### 尾部链接示例

```markdown
📖 **[训练回路合集](https://mp.weixin.qq.com/mp/appmsgalbum?__biz=XXX&action=getalbum&album_id=YYY)**：梯度下降 → 损失函数 → 反向传播 → Softmax → 残差连接 → Adam
```

## 微信话题标签

每篇 `weixin.md` 末尾**必须**添加 3-5 个话题标签（`#标签`），用于搜一搜 SEO 和话题聚合。格式：系列标签 + 2-3 个主题标签 + `#数解AI`。详见 [`docs/wechat-topic-tags.md`](docs/wechat-topic-tags.md)。

## 公众号菜单维护

「热门文章」≤5 篇（手动管理），「全部合集」永久不变（合集页 URL）。发新文时勾选合集 + 记入 frontmatter `wechatUrl`。详见 [`docs/wechat-menu.md`](docs/wechat-menu.md)。

## 文章标题

详见 [`docs/article-title-seo.md`](docs/article-title-seo.md)。

核心原则：**关键词前置** + **痛点驱动点击** + **搜一搜 SEO**。关键信息须落在前 22 字内（微信信息流截断窗口），**全标题长度可适度放宽**，以自然通顺优先；含 1 个专业关键词，套标题公式生成，过 9 条自检清单。

**封面标题规格（写入封面 prompt 的硬性要求）**：封面文字 = 文章标题**一字不差**；版式=金色发光标题横贯全幅（无左右分栏）、每行字号约画面高度 1/9–1/8、**整块文字高度不超过画面高度 1/4**、两行居中、数字准确、背景压暗退后、画面禁止任何其他文字。详见 [`docs/image-generation.md`](docs/image-generation.md)「封面标题显眼度规格」。

## 贴图标题与封面（爆款规律）

新建贴图（选题定档、标题/封面定稿前）**必须先读** [`docs/tietu-viral-playbook.md`](docs/tietu-viral-playbook.md)（2026-10-04 从历史贴图量级对照提炼，含量级三档表 + 同日对照证据），逐项过文内执行清单。核心规律：

- **题材事件量级定档**：出圈事件（价格战/全网新闻）> 圈内大事件 > 圈内小事件；第三档预期放百级，标题再好也救不了题材
- **标题三件套**：品牌词/事件词前置（必中）+ 情绪/强立场 + 利益/站队钩子，至少中两个；带一个可转发的具体数字
- **杜绝谜语化**：陌生人 3 秒说不出讲什么就重写；「网络」「大模型」这类泛指不算品牌词
- **封面大字 = 定稿标题核心句**，热点词进大字（信息流里标题+封面同帧，禁止两套说法、禁止热点词埋小字）
- **贴图不做反直觉疑问句**（那是文章轨公式，别混用）；热点当天/次日发 + 开启群发通知

## 理论与实践结合

理论知识点必须关联最新国产模型（HuggingFace config.json）。模型优先级：DeepSeek-V4 > GLM-5.2 > Kimi K2.6 > Qwen3。引用须标注来源。详见 [`docs/theory-practice.md`](docs/theory-practice.md)。

## 数据时效性

所有价格、版本号、参数规模必须实时搜索验证，标题数字和正文一致。⚠️ AI 模型倾向将 DeepSeek V4 Pro 发布时间记为"2025"，**实际为 2026 年 4 月**，所有涉及 V4 Pro 的 prompt/正文须显式标注"2026"。详见 [`docs/data-freshness.md`](docs/data-freshness.md)。

## 人物故事嵌入

**禁止**独立人物故事/传记文章。人物只能作为嵌入技术文章的钩子（≤10% 篇幅）。标题禁止以人物名开头。详见 [`docs/story-embed.md`](docs/story-embed.md)。

## 公众号运营

详见 [`docs/wechat-ops.md`](docs/wechat-ops.md)。

**选题规划**：写新文章前先查 [`docs/content-matrix.md`](docs/content-matrix.md)（内容矩阵与 DeepSeek 反常识选题库，2026-08-26 建立）。

⚠️ **推荐权重恢复期（2026-08-22 起，临时 1–2 周）**：见 `docs/wechat-ops.md`「推荐权重恢复期规则」。恢复期内**「合格才发」优先于日更**（允许断更）、执行质量门禁加严 6 条（见该节 B，任何一条不过不发）、禁同日双发同题材、发布后不改标题/摘要、恢复期互动增量（可回答问题 + 作者 1 小时内回复前 3 条 + 一句话总结卡）。**双轨框架（2026-08-29 确立）**：账号级推荐量靠**贴图轨**（热点事件当天发贴图 + 开群发 + 情绪词标题，禁与文章同日同题材）；文章轨目标文章级指标（数学篇为主力，RL 篇暂停或挂现实模型钩子）。**监控指标（2026-08-29 修正）**：账号级每日推荐量含贴图推荐流（贴图与文章推荐独立），不再作为文章策略判据；改为文章级指标——新发文章 7 日阅读 150–300、留言 ≥5、分享率 ≥10%，滚动窗口 5–7 篇 ≥4 篇达标即退出恢复期。

## 公众号运营数据验证

内容策略决策的实证基础。账号日新增关注不能直接归因到单篇文章。详见 [`docs/wechat-data-insights.md`](docs/wechat-data-insights.md)。

## 公众号数据审计 Skill

项目级 skill：[`.agents/skills/wechat-data-audit/SKILL.md`](.agents/skills/wechat-data-audit/SKILL.md)

封装了「Cookie 注入 → 采集内容/用户数据 → 分析 → 写入项目文档」的完整工作流。AI 在接到数据复盘或运营分析类请求时应优先加载此 skill。

关键规则：
- 每天最多 1 篇，日更节奏（2026-07-25 起试行；推荐权重恢复期豁免，见「公众号运营」节），固定 20:00 发布
- 末尾含关注引导（价值承诺 + 系列结构）
- 结尾含 1 个开放式问题引导留言
- 摘要须含 2-3 个搜索关键词
- 最新审计：2026-10-07 早场（数据截至 2026-10-06，累计关注 **1,070**（4 天净增仅 +3），广告收入累计 **96.28 元**、收入滞后至 10-05）。🔴 **推荐深度回落**：10-03→10-05 推荐连续下滑 134→107→**89（09-27 以来最低）**，10-06 靠两张贴图反弹 164；推荐来源占比 80.1%→**74.3%**，公众号消息占比抬升 10.5%→14.0%。**0ag 判断被坐实：推荐池没有独立趋势，跟着内容强度走**；贴图 T+0 即拉当日推荐、文章推荐仍 T+1 到账。**完读率 KPI 首轮完整读数（n=4）**：给 Agent 记忆 22% > 流形假设 21% > RL 16%（T+0 的 11% 质疑解除）> 问 AI 100 遍 12%；⚠️ **0ah.7 历史数据核查（23 篇回测）：完读率与阅读/涨粉/分享零或负相关、被渠道结构主导，已降级为诊断指标**（同渠道横向比 + <15% 发文门禁预警，完读率 T+7 定档）；**结果 KPI 维持 T+7 阅读 ∈[150,300] + 分享率 ≥10%**；**流形假设（T+7 190 读/分享率 15.3%）成第 2 篇达标文章**，滚动 7 篇达标 2/7 < 4，**恢复期仍不退出**。广告位快照**新增 `tietuFeed`（贴图底部推荐流）**口径；日均曝光 182 < 200，eCPM/CTR 继续不作决策依据。本轮免扫码采集**第三次复验成功**，cookie 已自动回写 `.env`。详见 [`docs/wechat-data-insights.md`](docs/wechat-data-insights.md) 0ah 节。
- 历史审计：2026-10-03 早场（数据截至 2026-10-02，累计关注 **1,067**，累计广告收入 **95.53 元**、昨日 +0.25）。🟡 **推荐：占比创新高但绝对量已回落**——账号推荐来源 **80.1%**（连续 4 轮抬升 60.6→68.4→79.6→80.1，项目记录），近 7 日推荐 1,139 vs 前 7 日 977（**+16.6%**）；但 09-30 见顶 255 后已回落到 10-01 的 134 / 10-02 的 148，**上轮的「阶梯抬升」主要是 09-30 流形假设+贴图拉动，不是推荐池独立趋势**。**恢复期仍不退出**：滚动 7 篇达标 **1 篇**（仅 09-24 四家架构 KV：225 读/推荐 76.4%/分享率 16.9%），远低于 ≥4 的退出线。⚠️ **2026-10-03 作者拍板两条口径修正**：① **留言指标已污染，不再作为 KPI**——作者说明「3 条评论」基本是自己留的 + 跟元宝互动的，后台数据也印证（21 条内容里 12 条恰好 3、3 条为 0，是恒定人工基线）；**下一阶段 KPI 换成完读率**，留言引导继续做但不背 KPI。② **新发文章一律等满 24 小时再判读**（含完读率、均读）——本快照里 10-02 RL 篇的「完读率 11%」是 T+0，不可作结论。三广告位 7 日合计 2.16 元，7 日曝光 1,355、日均 194 < 200，**eCPM/CTR 本轮不作决策依据**。搜一搜 **0.6%**（连降 4 轮）。⚠️ 本轮修正两处口径事故：`articles[].reads` 统一取发表记录「阅读人数」列、`articles[].share` 统一为百分比（此前两轮误存小数比例）——跨 0af/0ag 比较单篇阅读会看到跳变。
- 🔴 **采集纪律（2026-10-01 新增）**：判定「后台登录态失效」**必须先枚举所有 Chrome profile 的 cookie 创建时间**——本轮活会话在 `~/.config/google-chrome/Default`（09-29 21:54），而 `.env` 的 `WECHAT_COOKIE` 是 09-27 17:01 的死快照。只盯 `.env` 会**误判为需扫码**（本轮差点让作者白扫）。✅ 可用解法：复制主 profile 最小集到 `/tmp/wx-live-profile` + headless Chrome（9335 端口）自解密 cookie，不打扰用户正在运行的 Chrome；**v11 libsecret 手工解密会失败，不要在那条路耗时**。脚本 `scripts/wx_audit_browser.py` + `scripts/wx_audit_collect.py`。后台菜单「流量主」**已改名「广告收入」**；用户分析页不可直接 URL 访问；收入页正文在顶层 `#wxadcontainer`；单篇饼图是 SVG aria 需分别抓百分比与标签再 zip。
- 🔴 **口径修正（承 09-27）**：文章推荐 **T+1 到账**，单篇推荐一律看累计。⚠️ **另新增两条口径警告**（2026-10-01）：① 单篇**详情页 = 去重人数**、**发表记录列表 = 阅读次数**，09-30 流形假设篇 60 人 vs 120 次，**差 2 倍不可混用**；② 内容分析页的单篇列表**固定近 30 天 Top10、无法按日切换**，按日取数走「发表记录」。「四家横向对照型」拉量、「大数字分配悬念型」（新增：2345 万 + 只分到 12.7%？）拉量、「猎奇翻车型」拉互动，三类轮换。详见 [`docs/wechat-data-insights.md`](docs/wechat-data-insights.md) 0af 节
- 历史审计：2026-10-01 下午场（数据截至 2026-09-30，累计关注 **1,060**，累计广告收入 95.05 元）。🟢 推荐连续 3 天阶梯抬升（09-27 谷底 98 → 09-30 峰值 255），近 7 日推荐 +24%，但 10-03 复采显示该抬升未能延续。09-30 流形假设篇 T+0 60 人 → T+2 164 人，验证推荐 T+1 到账。历史审计：2026-09-27 晚场（数据截至 2026-09-26，累计关注 **1,043**，累计广告收入 93.07 元）。🔴 **重大口径修正：文章推荐是 T+1 到账**——09-24 KV 篇当日仅 17 读、次日 88 读（其中推荐 67），累计 144 读里推荐占 **72.9%**；此前多轮用「发布当日读数低」判读「推荐未恢复」是错的。09-17 短原创《AI中有趣的对抗思想居然无处不在》已补录（`2026-09-17-adversarial-thought`）。⚠️ `backfill-types` 标题集快照滞后，09-20~09-30 新发贴图已补入 `branding/style-corpus/tietu-extra.json`（2026-10-01 追加 4 条）——**单篇类型判读一律以后台 `item_show_type` 原始字段为准**。详见 0ae 节
- 数字事实源：[`docs/wechat-data-audit-log.json`](docs/wechat-data-audit-log.json)，结构见同名 `.schema.json`，操作脚本为 `scripts/wechat_audit_log.py`，报告生成脚本为 `scripts/wechat_audit_report.py`，产物为 `docs/wechat-data-audit-report.html`
- **每日流量渠道明细事实源（2026-08-27 新增）**：[`docs/wechat-daily-sources-log.json`](docs/wechat-daily-sources-log.json)，结构见同名 `.schema.json`——按天 × 传播渠道阅读人数（含每日推荐量）；每次采内容分析后跑 `python scripts/wechat_audit_log.py append-sources --input <tendency_*.xls>` 增量入库，逐日历史只认这份台账
- **视频号数字事实源（2026-08-25 新增）**：[`docs/shipinhao-data-log.json`](docs/shipinhao-data-log.json)，结构见同名 `.schema.json`——视频号播放/完播/点赞/评论数据，与公众号日志分离（后台登录体系不同，公众号 Cookie 不通用）

## 视频号视频加工 Skill

项目级 skill：[`.agents/skills/gemini-video-to-shipinhao/SKILL.md`](.agents/skills/gemini-video-to-shipinhao/SKILL.md)

封装了「Gemini Notebook 视频 → 视频号成品」全流程：MiMo ASR 字幕 → 拆长句 → 对照公众号文章校对 → 定位/去除 Gemini logo → 烧录黄色字幕 → 替换片尾品牌页为关注卡 → 归档。关键规则：

- 字幕基准是 `weixin.md`，术语/年份必须逐条对照校对（MiMo 误听清单见 SKILL）
- 烧录必须用 `scripts/burn_shipinhao.py`（滤镜顺序、字号补偿、码率参数、片尾截断点探测已固化，禁止手动拼 ffmpeg 命令丢滤镜链）
- SRT 备份不得与视频同名（VLC 自动加载同名 .srt 会叠加显示）
- 产物归档 `content/<日期>-<主题>/shipinhao/`，发布时用「扩展链接」挂公众号文章

## Manim 文章视频 Skill

项目级 skill：[`.agents/skills/manim-article-video/SKILL.md`](.agents/skills/manim-article-video/SKILL.md)

封装了「公众号文章 → Manim 动画视频号成品」全流程：分镜脚本 → MiMo 逐段配音 → Manim 竖屏场景 → 渲染 → `scripts/manim_video_build.py` 一键构建（mux 配音 + 无缝拼接 + 黄色字幕 + 品牌尾卡）→ 验证归档。关键规则：

- **用户用文章标题指代文章**，先 grep 定位 `content/<日期>-<主题>/`，再读 `weixin.md`
- **语速定稿 speed 1.0 + pitch +2**（2026-08-25 用户拍板「节奏非常快」后降速，勿擅自改）；段间停顿是红线，段尾缓冲 0.1s；默认时长 3-4 分钟（软上限 5 分钟）、5-6 段分镜、动画降噪（每页 1 个主视觉动效，v2 动效每片 ≤3 处）
- **配音默认用作者克隆音色**（`--clone-audio branding/my-voice-denoised.wav`，MiniMax speech-2.8-turbo 默认、hd 可选；2026-08-11 起 MiMo → MiniMax，用户反馈 MiMo 声音不真实、感情不足）；录音参考 `branding/my-voice-original.m4a`
- 场景 `construct` 末尾必须 `pad_to_voice()` 补齐到配音时长；ASS 时间戳是**厘秒** `h:mm:ss.cc` 不是毫秒
- 结尾品牌尾卡：`avatar-sjai.png` 圆角透明化 + 图下黄色「关注「数解AI」」引导
- 规格（竖屏/时长/配音）先 `ask_user_question`；sudo 类系统操作停下交给用户执行

## 文章质量核查

草稿写完后**必须执行**，全部通过才能进入发布流程。详见 [`docs/article-quality-check.md`](docs/article-quality-check.md)（含 16 项核查清单，第 13 项为爆款检查器，第 14 项为自动成稿原声槽，第 15 项为说人话/去 AI 味，第 16 项为转发/点赞欲检查器，不满足必须改写）。

## 发布前检查

**规则**：调用 `baoyu-post-to-wechat` 发布前，必须确认以下就绪：

1. **封面图已生成** — `00-cover.png` 存在于文章目录，缺失则先生成
2. **wechatUrl 已补** — 发布后第一时间把微信 URL 写入 frontmatter `wechatUrl` 字段
3. **目录名 = 发布日期** — 发布日期变更时同步重命名目录
4. **图片路径正确** — 图片与 `weixin.md` 同级，无 `images/` 前缀（详见 `docs/wechat-image-path.md`）
5. **话题标签已添加** — 文末含 3-5 个 `#标签`（详见 `docs/wechat-topic-tags.md`）
6. **最终检查已通过** — 逐项过 `docs/pre-publish-final-check.md` 的 7 项清单

## 发布前最终检查

发布前最后一道门禁，9 项：标题/关键词 SEO、正文开头无重复封面图、硬件数字核查（GPU/模型/上下文组合可实际跑通）、无「待发布」残留（替换为已发布微信链接）、文末话题标签、尾部系列导航（合集链接 + 箭头链，不漏篇）、下一篇预告、点赞/关注/收藏引导、叙事闭环（开头 ↔ 结尾预告完整逻辑链）。详见 [`docs/pre-publish-final-check.md`](docs/pre-publish-final-check.md)。

## 公众号图片路径

详见 [`docs/wechat-image-path.md`](docs/wechat-image-path.md)（硬性规则，发布 45166 的根因）。

## 小红书卡片结构

**规则**：小红书卡片数量控制在 **6 张以内**（精简掉冗余的代码实操和独立关注引导页）。

推荐序列：封面钩子 → 核心问题 → 直觉解释 → 关键洞察 → 实验数据 → 总结+关注

封面必须遵循策略（≤8 字痛点钩子 + 大面积留白），生成前先清理旧文件。

## 目录命名

**规则**：文章目录名用**发布日期**（如 `2026-07-07-softmax`），不用创建日期。发布日期变更时须同步重命名目录。
