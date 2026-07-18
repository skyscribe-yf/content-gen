# 图片生成

项目图片生成唯一后端：**zairouter**（gpt-image-2）。

---

## 封面图规则

**公众号封面图必须使用电影宽幅 21:9**（`size: "21:9"`），禁止使用 1:1 正方形或 16:9。

原因：电影宽幅（2.35:1）在微信消息列表和朋友圈分享中不会被裁切，视觉冲击力更强，且能容纳更多画面内容。16:9 仍有轻微裁切风险。

## 语言规则

**所有图片中的文字必须使用中文**，包括标题、标签、坐标轴、图例、注释等。Prompt 中需明确写明中文文字内容，避免生成英文图片后返工。

---

## ⭐ zairouter API (gpt-image-2) — 唯一后端

客户端脚本：`scripts/zairouter_client.py`

**默认参数（成本控制）**：
- **size: `1:1`**（1024×1024，正方形）
- **quality: `high`**

**默认分辨率规则**：所有图片默认 1K，包括封面图。`1:1` = 1024×1024，`21:9` = 1248×528。需要 2K/4K 时**必须先告知费用差异并要求用户确认**，不得擅自升级。

**ENV**：需要 `ZAI_API_KEY` 环境变量（已在 `.env` 中配置）

### Size 快捷映射

zairouter 直接使用 W×H 像素尺寸。脚本内置了常用尺寸的快捷名：

| 快捷名 | 实际尺寸 | 推荐场景 |
|--------|----------|----------|
| `1:1` | 1024×1024 | 正方形配图（默认） |
| `1:1-2k` | 2048×2048 | 正方形高清 |
| `21:9` | 1248×528 | 电影宽幅 1K（封面图） |
| `21:9-2k` | 2688×1152 | 电影宽幅 2K |
| `21:9-4k` | 3840×1648 | 电影宽幅 4K |
| `16:9` | 1088×608 | 横版配图 |
| `16:9-4k` | 3840×2160 | 横版 4K |
| `9:16` | 608×1088 | 竖版配图 |
| `9:16-4k` | 2160×3840 | 竖版 4K |
| `3:4` | 768×1024 | 小红书卡片 |
| `4:3` | 1024×768 | 传统横版 |
| `3:2` | 1024×688 | 横版插图 |
| `2:3` | 688×1024 | 竖版插图 |

**ZAI Router 最长边限制 ≤ 3840**。超出会返回 HTTP 400。

**场景速查**：

| 用途 | size | 像素 |
|------|------|------|
| 公众号封面（默认 1K） | `21:9` | 1248×528 |
| 小红书卡片 | `3:4` | 768×1024 |
| 正方形配图 | `1:1` | 1024×1024 |
| 竖版海报 | `9:16` | 608×1088 |

**费用递增**：像素量决定成本。1K 最便宜，4K 最高。

### 批量生成

通过 JSON 配置文件 + `--config` 参数，每张卡片可覆盖全局 size：

```json
{
  "output_dir": "content/my-article/images",
  "size": "1:1",
  "quality": "high",
  "cards": [
    {
      "title": "封面",
      "prompt": "A cinematic illustration of...",
      "size": "21:9",
      "filename": "cover.png"
    },
    {
      "title": "卡片2",
      "prompt": "An infographic showing...",
      "size": "3:4",
      "filename": "card-01.png"
    }
  ]
}
```

---

## apimart.ai API (gpt-image-2) — 历史后端（禁用）

客户端脚本：`scripts/apimart_client.py`

**默认参数**：size: `1:1`, resolution: `1k`。ENV：`API_MART_KEY`。

使用 size（比例）+ resolution（分辨率）两级参数。支持 1k/2k/4k 分辨率。

---

## xabcimg API (gpt-image-2) — 历史后端（禁用）

客户端脚本：`scripts/xabc_client.py`

**默认参数（成本控制）**：
- **quality: `medium`**
- **size: `1024x1024`**

**升级确认规则**：若用户未显式指定 quality 或 size，**一律使用上述默认值**。需要升级到 `high` quality 或更大尺寸（如 `1792x1024`）时，**必须先告知费用差异并要求用户确认，得到明确同意后才生成**。

**支持的尺寸**：
- `1024x1024` — 1:1 正方形（默认，最便宜）
- `1792x1024` — 16:9 宽屏
- `1024x1792` — 竖版

**ENV**：需要 `XABC_MING_SESSION` 环境变量（已在 `.env` 中配置）

---

## yairouter API (gpt-image-1) — 历史后端（禁用）

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
