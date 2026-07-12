# 知乎推广回答格式

## 核心规则

知乎编辑器是**富文本（WYSIWYG）**，不支持 Markdown。直接把 `**加粗**`、`>`、`| 表格 |`、`##` 贴进去会乱码。

**输出两份文件**：
- `promote/zhihu-{slug}.md` — 内容源，方便后续修改
- `promote/zhihu-{slug}.html` — 浏览器打开 → Ctrl+A → Ctrl+C → 贴进知乎编辑器

## HTML 格式要求

### 必须自包含

单个 HTML 文件，内嵌 CSS，不依赖外部样式表。打开即所见即所得。

### 必须的 CSS 样式

```css
body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
  font-size: 16px; line-height: 1.8; color: #1a1a1a;
  max-width: 720px; margin: 40px auto; padding: 0 20px;
}
h1 { font-size: 24px; font-weight: 700; margin: 32px 0 16px; }
h2 { font-size: 20px; font-weight: 700; margin: 28px 0 12px;
     padding-bottom: 6px; border-bottom: 1px solid #eee; }
h3 { font-size: 17px; font-weight: 700; margin: 24px 0 10px; }
blockquote {
  margin: 16px 0; padding: 12px 16px;
  background: #f6f8fa; border-left: 4px solid #1a6dd4;
  border-radius: 0 4px 4px 0;
}
table { border-collapse: collapse; width: 100%; margin: 16px 0; font-size: 15px; }
th, td { border: 1px solid #ddd; padding: 10px 14px; text-align: left; }
th { background: #f4f6f8; font-weight: 600; }
.cta {
  background: #f0f7ff; border: 1px solid #b8d8ff;
  padding: 16px 20px; border-radius: 8px; margin: 20px 0;
}
```

### 公式处理

禁用 LaTeX（知乎富文本编辑器不支持 `$...$`）。全部用 **Unicode 字符 + 加粗** 表示，放在 `<blockquote>` 内：

```html
<blockquote><p><strong>θₜ₊₁ = θₜ − η · m̂ₜ / (√v̂ₜ + ε)</strong></p></blockquote>
```

下标的 Unicode 字符速查：

| 含义 | 字符 | 示例 |
|------|------|------|
| 下标 t | ₜ | θₜ, gₜ, vₜ |
| 下标 t-1 | ₜ₋₁ | θₜ₋₁, mₜ₋₁ |
| 下标 t+1 | ₜ₊₁ | θₜ₊₁ |
| hat（估计） | ̂ | m̂ₜ, v̂ₜ |
| 平方 | ² | gₜ² |
| beta | β | β₁, β₂ |

### 分隔线

用 `<hr>` 不用 `---`。

## 回答内容结构

### 引流目标

驱动读者关注微信公众号「数解AI」，回复关键词获取完整文章（含原创图解）。

### 必须包含的元素

1. **痛点钩子开头** — 第一句直击读者困惑（"你看不懂不是因为数学难，而是……"）
2. **实质性内容** — 抽取 weixin.md 的核心洞察，不是摘要转发，是独立有价值的内容
3. **生活化比方** — 每个核心概念配一个生活类比（浓雾下山、水龙头旋钮等）
4. **真实模型数据** — DeepSeek / Qwen / Kimi 等国产模型的实际配置参数
5. **下篇预告** — 用下一篇内容诱发关注动机
6. **系列导航** — 列出系列文章结构，暗示"关注后都能看到"
7. **CTA 区域** — 用 `.cta` 样式框，明确告知关注方式、回复关键词、你能获得什么

### 引流钩子埋点（至少 3 处）

| 位置 | 形式 | 示例 |
|------|------|------|
| 开头附近 | 暗示有图解 | "（图见文末原文）" |
| 正文中段 | 提及公众号完整版 | "完整版（含 7 张原创图解 + 椭球可视化）发在公众号" |
| 结尾 | CTA 框 | "关注「数解AI」，回复'Adam'直接收到这篇" |

### 禁止行为

- 禁止回答正文中出现任何可点击外链（URL）——知乎会对含外链的回答降权或折叠。引流只能通过纯文字提及公众号名称和回复关键词
- 禁止纯广告——必须有独立于公众号文章之外的完整内容价值
- 禁止直接贴公众号文章全文——知乎回答是独立的二次创作
- 禁止在回答中用知乎不支持的格式（代码块、LaTeX、Mermaid 等）
- 禁止不包含 CTA——每篇回答必须有明确的公众号关注引导

## 命名规范

```
promote/zhihu-{article-slug}.md    # 内容源（Markdown）
promote/zhihu-{article-slug}.html  # 知乎粘贴版（HTML）
```

article-slug 取文章的核心技术关键词，如 `adam`、`softmax`、`moe`。

## 发布流程

1. 从 weixin.md 提取核心洞察，写 `promote/zhihu-{slug}.md`
2. 将 md 转换为自包含 HTML，保存为 `promote/zhihu-{slug}.html`
3. 浏览器打开 HTML → 检查渲染效果
4. Ctrl+A → Ctrl+C → 粘贴到知乎编辑器 → 检查格式
5. 修正粘贴后可能丢失的格式（如有）
6. 发布

## 自检清单

- [ ] HTML 文件在浏览器中打开后，加粗、引用、表格、列表是否全部正常渲染？
- [ ] 公式是否全部用 Unicode + `<strong>` + `<blockquote>`，没有 `$...$`？
- [ ] 是否至少埋了 3 处引流钩子（暗示图解 → 提完整版 → CTA 框）？
- [ ] CTA 框是否包含：关注公众号名称 + 回复关键词 + 你能获得什么？
- [ ] 回答是否能独立成篇（不依赖公众号原文）？
- [ ] 是否有至少 2 个生活化比方？
- [ ] 是否引用了至少一个国产模型的实际配置数据？
