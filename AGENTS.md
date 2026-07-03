# AGENTS.md — 项目级 Agent 配置

## 数学公式：必须用 Unicode，禁用 LaTeX

**规则**：公众号文章的 Markdown 源文件中，所有数学公式必须用 Unicode 字符书写，**禁止使用 LaTeX 语法**（`$...$` 和 `$$...$$`）。

**原因**：微信公众号不原生支持 LaTeX 渲染。baoyu-markdown-to-html 的 MathJax/KaTeX 渲染在部分微信客户端上不生效，公式会显示为原始 LaTeX 代码。

**Unicode 替换对照表**：

| LaTeX | Unicode | 示例 |
|-------|---------|------|
| `\frac{a}{b}` | a/b | ∂L/∂ŷ |
| `\sum` | Σ | Σ(yᵢ − ŷᵢ)² |
| `\partial` | ∂ | ∂L/∂x |
| `\nabla` | ∇ | ∇f(θ) |
| `\theta` | θ | θₜ₊₁ |
| `\alpha` | α | α·∇f |
| `\hat{y}` | ŷ | y − ŷ |
| `\log` | log | log(p) |
| `\times` | × | 2 × 0.99 |
| `\approx` | ≈ | 1/0.49 ≈ 2.04 |
| `\in` | ∈ | y ∈ {0,1} |
| `_{i}` | ᵢ | yᵢ, ŷᵢ |
| `_{t+1}` | ₜ₊₁ | θₜ₊₁ |
| `^{2}` | ² | (y−ŷ)² |
| `-` (减/负) | − (U+2212) | −1/ŷ |
| `\cdot` | · | y·log(ŷ) |

**独立公式写法**：不用 `$$...$$`，直接用普通文本段落，居中效果由 HTML/CSS 处理。

```
❌ $$ L_{MSE} = \frac{1}{n} \sum_{i=1}^{n} (y_i - \hat{y}_i)^2 $$
✅ L_MSE = (1/n) Σ(yᵢ − ŷᵢ)²
```

**内联公式写法**：不用 `$...$`，直接写 Unicode。

```
❌ 梯度被 $p(1-p)$ 因子压扁
✅ 梯度被 p(1−p) 因子压扁
```

**自检**：写完后 `grep '$' draft.md` 应该没有结果（美元符号只出现在金额上下文中）。

### 公式样式

独立公式（独占一行的）用**引用块**包裹，让渲染后带背景色和蓝色左边框，与正文区分：

```
> **L_MSE = (1/n) Σ(yᵢ − ŷᵢ)²**
```

渲染效果：浅灰背景 + 蓝色左边框 + 加粗蓝色字体，视觉上明显突出。

内联公式（嵌在句子中的）用**加粗**标记：

```
MSE的梯度被 **p(1−p)** 因子压扁了
```

渲染效果：蓝色加粗字体（grace 主题的 strong 标签样式为 `color: #0F4C81; font-weight: bold`）。

**公式样式三原则**：
1. 独立公式 → 引用块 + 加粗（背景 + 蓝字）
2. 内联公式 → 加粗（蓝字）
3. 公式绝不能和正文用相同样式——读者一眼就要能区分

---

## 图片生成

### 后端：yairouter API (gpt-image-1)

项目使用 yairouter.com 的 OpenAI 兼容 API 生成高质量图片。

**端点**: `https://api.yairouter.com/v1/images/generations`
**模型**: `gpt-image-1`
**认证**: `Authorization: Bearer $XAI_API_KEY`
**质量**: `quality: "high"`

**请求示例**:
```json
{
  "model": "gpt-image-1",
  "prompt": "A cinematic cover image...",
  "n": 1,
  "size": "1792x1024",
  "quality": "high"
}
```

**支持的尺寸** (宽x高):
- `1792x768` — 2.35:1 电影宽幅（封面题图）
- `1792x1024` — 16:9 宽屏（横版插图）
- `1024x1024` — 1:1 正方形
- `1024x1792` — 竖版（手机/小红书封面）

**返回格式**: `data[0].b64_json` (base64 编码 PNG)

**集成到 baoyu skills**:
- `baoyu-cover-image`: 设置 `preferred_image_backend` 时，可通过自定义脚本调用此 API
- `baoyu-article-illustrator`: 同上

**ENV**: 需要 `XAI_API_KEY` 环境变量（已在 `.env` 中配置）

**调用方式** (Node.js):
```javascript
const https = require('https');
const postData = JSON.stringify({
  model: 'gpt-image-1',
  prompt: 'your prompt here',
  n: 1,
  size: '1792x1024',
  quality: 'high'
});
const options = {
  hostname: 'api.yairouter.com',
  path: '/v1/images/generations',
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${process.env.XAI_API_KEY}`,
    'Content-Type': 'application/json',
    'Content-Length': Buffer.byteLength(postData)
  }
};
```

**费用**: gpt-image-1, high quality, 按图片尺寸计费

---

## 多平台内容一致性规则

**规则**：生成小红书卡片（cards.json）、文案（copy.md）或其他平台衍生内容时，**必须以 `weixin.md`（微信最终发布版）为准**，禁止参照 `draft.md`。

**原因**：`draft.md` 是初稿，经过审校和修正后的最终版本保存在 `weixin.md` 中。从 draft 衍生的内容会携带已被修正的错误（如：draft 中的「3个AI模型PK」已被 weixin.md 改为「学习率对比实验」，但 XHS 卡片仍沿用旧版生成）。

**执行检查清单**：
1. 生成 cards.json / copy.md 前，先确认 `weixin.md` 存在
2. 逐节对比 draft.md → weixin.md 的差异，以 weixin.md 为准
3. 如果 weixin.md 不存在（文章尚未定稿），则暂停衍生内容生成
4. 生成后自检：卡片内容是否与 weixin.md 对应章节一致

---

## 微信文章链接规则

**系列导航中的链接必须是微信文章URL**（`https://mp.weixin.qq.com/s/...`），不能用相对路径。

**原因**：微信公众号不支持相对路径链接，`../2026-07-03-梯度下降/draft.md` 这种链接在微信里完全无效。

**规则**：
1. 系列导航中的「上一篇」「下一篇」链接必须是 `https://mp.weixin.qq.com/s/xxxxx` 格式
2. 如果前一篇尚未发布，用 `（待发布）` 标注，发布后立即补上URL
3. 发布成功后，**必须把微信URL记录到文章的 frontmatter 中**（`wechatUrl` 字段），方便后续文章引用

**frontmatter 示例**：
```yaml
---
title: "梯度下降：蒙着眼下山"
wechatUrl: "https://mp.weixin.qq.com/s/abc123"
---
```

**引用方式**：下一篇写系列导航时，读取前一篇的 `wechatUrl` 字段填入链接。
