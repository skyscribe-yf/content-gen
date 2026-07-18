# AGENTS.md — 项目级 Agent 配置

本文件是规则索引，详细内容拆分到 `docs/` 下各专题文档。

## 文章写作流程（硬性门禁）

起草大纲前**必须先调用 grill-me skill** 与作者深入讨论（`.agents/skills/grill-me/SKILL.md`）。禁止 AI 单方面生成 `.grill/<slug>.md` 日志。详见 [`docs/writing-flow.md`](docs/writing-flow.md)。

## 数学公式

详见 [`docs/math-unicode.md`](docs/math-unicode.md)。

规则：禁用 LaTeX（`$...$` / `$$...$$`），全部用 Unicode 字符。独立公式用引用块+加粗，内联公式用加粗。

## 图片生成

唯一后端：**zairouter**（gpt-image-2）。默认 1K，封面图强制 **21:9**。具体尺寸由 `scripts/zairouter_client.py` 控制。prompt 内文字/数字/年份必须与正文一致。详细流程见 [`docs/image-generation.md`](docs/image-generation.md)。

## 多平台内容一致性

衍生内容（小红书卡片/文案等）**必须以 `weixin.md` 为准**，禁止参照 `draft.md`。weixin.md 不存在则暂停生成。

## 小红书文案格式

详见 [`docs/xiaohongshu-copy.md`](docs/xiaohongshu-copy.md)。

规则：文案写入独立 `copy.txt`，禁止嵌入 `cards.json` 或内联输出。纯文本、≤1000字、末尾带话题标签。

## 知乎推广回答

知乎不支持 Markdown → 输出 `.md` + `.html` 两份文件。公式用 Unicode，回答须有独立价值 + ≥3 处公众号引流钩子。详见 [`docs/zhihu-promotion.md`](docs/zhihu-promotion.md)。

## 小红书内容策略

入口必须是痛点（不是概念）。封面图钩子 ≤8 字，标签用长尾词。详见 [`docs/xiaohongshu-strategy.md`](docs/xiaohongshu-strategy.md)。

## 微信文章链接规则

- 系列导航链接**必须**是微信 URL（`https://mp.weixin.qq.com/s/...`），禁止相对路径
- 未发布用 `（待发布）` 标注，发布后补 URL
- 发布后**必须**把微信 URL 记入 frontmatter `wechatUrl` 字段，供后续文章引用
- **尾部惯例**：尾部只用合集链接收纳逐篇链接，不用单篇链接堆叠

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

## 公众号菜单维护

「热门文章」≤5 篇（手动管理），「全部合集」永久不变（合集页 URL）。发新文时勾选合集 + 记入 frontmatter `wechatUrl`。详见 [`docs/wechat-menu.md`](docs/wechat-menu.md)。

## 文章标题

详见 [`docs/article-title-seo.md`](docs/article-title-seo.md)。

核心原则：**关键词前置** + **痛点驱动点击** + **搜一搜 SEO**。标题 ≤22 字，含 1 个专业关键词，套标题公式生成，过 6 条自检清单。

## 理论与实践结合

理论知识点必须关联最新国产模型（HuggingFace config.json）。模型优先级：DeepSeek-V4 > GLM-5.2 > Kimi K2.6 > Qwen3。引用须标注来源。详见 [`docs/theory-practice.md`](docs/theory-practice.md)。

## 数据时效性

所有价格、版本号、参数规模必须实时搜索验证，标题数字和正文一致。⚠️ AI 模型倾向将 DeepSeek V4 Pro 发布时间记为"2025"，**实际为 2026 年 4 月**，所有涉及 V4 Pro 的 prompt/正文须显式标注"2026"。详见 [`docs/data-freshness.md`](docs/data-freshness.md)。

## 人物故事嵌入

**禁止**独立人物故事/传记文章。人物只能作为嵌入技术文章的钩子（≤10% 篇幅）。标题禁止以人物名开头。详见 [`docs/story-embed.md`](docs/story-embed.md)。

## 公众号运营

详见 [`docs/wechat-ops.md`](docs/wechat-ops.md)。

## 公众号运营数据验证

内容策略决策的实证基础。账号日新增关注不能直接归因到单篇文章。详见 [`docs/wechat-data-insights.md`](docs/wechat-data-insights.md)。

## 公众号数据审计 Skill

项目级 skill：[`.agents/skills/wechat-data-audit/SKILL.md`](.agents/skills/wechat-data-audit/SKILL.md)

封装了「Cookie 注入 → 采集内容/用户数据 → 分析 → 写入项目文档」的完整工作流。AI 在接到数据复盘或运营分析类请求时应优先加载此 skill。

关键规则：
- 每天最多 1 篇，间隔 ≥2 天
- 末尾含关注引导（价值承诺 + 系列结构）
- 结尾含 1 个开放式问题引导留言
- 摘要须含 2-3 个搜索关键词

## 文章质量核查

草稿写完后**必须执行**，全部通过才能进入发布流程。详见 [`docs/article-quality-check.md`](docs/article-quality-check.md)（含 9 项核查清单）。

## 发布前检查

**规则**：调用 `baoyu-post-to-wechat` 发布前，必须确认以下三项就绪：

1. **封面图已生成** — `00-cover.png` 存在于文章目录，缺失则先生成
2. **wechatUrl 已补** — 发布后第一时间把微信 URL 写入 frontmatter `wechatUrl` 字段
3. **目录名 = 发布日期** — 发布日期变更时同步重命名目录
4. **图片路径正确** — 图片与 `weixin.md` 同级，无 `images/` 前缀（详见 `docs/wechat-image-path.md`）

## 公众号图片路径

详见 [`docs/wechat-image-path.md`](docs/wechat-image-path.md)（硬性规则，发布 45166 的根因）。

## 小红书卡片结构

**规则**：小红书卡片数量控制在 **6 张以内**（精简掉冗余的代码实操和独立关注引导页）。

推荐序列：封面钩子 → 核心问题 → 直觉解释 → 关键洞察 → 实验数据 → 总结+关注

封面必须遵循策略（≤8 字痛点钩子 + 大面积留白），生成前先清理旧文件。

## 目录命名

**规则**：文章目录名用**发布日期**（如 `2026-07-07-softmax`），不用创建日期。发布日期变更时须同步重命名目录。
