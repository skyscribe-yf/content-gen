# 图片生成

项目图片生成唯一后端：**apimart.ai**。

---

## 语言规则

**所有图片中的文字必须使用中文**，包括标题、标签、坐标轴、图例、注释等。Prompt 中需明确写明中文文字内容，避免生成英文图片后返工。

## 任务管理规则

**禁止在 timeout 时重新提交任务！** `scripts/apimart_client.py` 会把每次提交写入输出目录的 `.apimart-tasks.json`。脚本 timeout 只说明本地轮询超时，不代表服务端任务失败。正确做法：
1. 重新运行同一个 `--config`：脚本会复用 `.apimart-tasks.json` 里的未失败 task，不重新提交
2. 或用 `scripts/poll_tasks.py OUTPUT_DIR TASK_ID:filename...` 轮询已提交 task
3. 只有 API 明确返回 `failed` 后，才允许为同一 prompt 重新提交

绝不重新提交同一张图的任务，避免重复生成浪费费用。

---

## ⭐ apimart.ai API (gpt-image-2) — 首选后端

客户端脚本：`scripts/apimart_client.py`

**默认参数（成本控制）**：
- **size: `1:1`**（正方形）
- **resolution: `1k`**（最便宜）

**升级确认规则**：若用户未显式指定 size 或 resolution，**一律使用上述默认值**。需要升级到 2k/4k 分辨率时，**必须先告知费用差异并要求用户确认，得到明确同意后才生成**。不得擅自使用 2k/4k。

**ENV**：需要 `API_MART_KEY` 环境变量（已在 `.env` 中配置）

### Size × Resolution 对照表

apimart.ai 的 GPT-Image-2 使用 **size（比例）+ resolution（分辨率）** 两级参数控制输出尺寸。

| 参数 | 含义 | 可选值 |
|------|------|--------|
| `size` | 画面宽高比 | `1:1`, `3:2`, `2:3`, `4:3`, `3:4`, `16:9`, `9:16`, `2:1`, `1:2`, `3:1`, `1:3`, `21:9`, `9:21` |
| `resolution` | 输出分辨率档位 | `1k`（最便宜）, `2k`, `4k` |

| size | 1k | 2k | 4k | 推荐场景 |
|------|-----|-----|-----|----------|
| `1:1` | 1024×1024 | 2048×2048 | 2880×2880 | 正方形配图 |
| `16:9` | 1024×576 | 2048×1152 | 3840×2160 | 公众号封面 |
| `3:4` | 768×1024 | 1536×2048 | 2480×3312 | 小红书卡片 |
| `9:16` | 576×1024 | 1152×2048 | 2160×3840 | 竖版海报 |
| `21:9` | 1915×821 | 2688×1152 | 3840×1648 | 电影宽幅 |
| `3:2` | 1536×1024 | 2048×1360 | 3520×2336 | 横版插图 |
| `2:3` | 1024×1536 | 1360×2048 | 2336×3520 | 竖版插图 |
| `4:3` | 1024×768 | 2048×1536 | 3312×2480 | 传统横版 |
| `2:1` | 1536×768 | 2688×1344 | 3840×1920 | 超宽横幅 |
| `1:2` | 768×1536 | 1344×2688 | 1920×3840 | 超高竖版 |
| `3:1` | 1536×512 | 3072×1024 | 3840×1280 | Banner |
| `1:3` | 512×1536 | 1024×3072 | 1280×3840 | 长竖版 |
| `9:21` | 821×1915 | 1152×2688 | 1648×3840 | 手机壁纸 |

**场景速查**：

| 用途 | size | resolution | 像素 |
|------|------|-----------|------|
| 公众号封面 | `16:9` | `2k` | 2048×1152 |
| 公众号封面（高清） | `16:9` | `4k` | 3840×2160 |
| 小红书卡片 | `3:4` | `1k` | 768×1024 |
| 电影宽幅 | `21:9` | `2k` | 2688×1152 |
| 正方形配图 | `1:1` | `1k` | 1024×1024 |
| 竖版海报 | `9:16` | `2k` | 1152×2048 |
| Banner | `3:1` | `2k` | 3072×1024 |

**费用递增**：1k 最便宜 → 2k 约 2-3 倍 → 4k 约 4-6 倍（像素量决定成本）。

### 图生图

支持 `--image-urls` 参数传入参考图 URL，最多 16 张。不传 `size` 时输出分辨率 = 输入图分辨率。

### 批量生成

通过 JSON 配置文件 + `--config` 参数，每张卡片可覆盖全局 size/resolution：

```json
{
  "series_title": "系列标题",
  "output_dir": "content/my-article/images",
  "size": "16:9",
  "resolution": "2k",
  "cards": [
    {
      "title": "卡片1",
      "prompt": "A cinematic illustration of...",
      "filename": "cover.png",
      "n": 1
    },
    {
      "title": "卡片2",
      "prompt": "An infographic showing...",
      "size": "3:4",
      "resolution": "1k",
      "filename": "card-01.png"
    }
  ]
}
```

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
