# 图片生成

项目图片生成默认后端：**yairouter**（gpt-image-2）。

> ⚠️ **已知问题（2026-08-07 实测）**：上游官方 API 忽略 `size` 参数——请求任意尺寸（21:9 / 4K / 1:1）实际输出均为 1254x1254 / 1536x1024 / 1024x1536 等固定或轮转尺寸。属官方 API 行为，暂不裁剪、不规避，工具按实际输出保存。详见 [`yairouter-gpt-image-2-experiment.md`](yairouter-gpt-image-2-experiment.md)。

---

## 封面图规则

**公众号封面图必须使用电影宽幅 21:9**（`size: "21:9"`），禁止使用 1:1 正方形或 16:9。

原因：电影宽幅（2.35:1）在微信消息列表和朋友圈分享中不会被裁切，视觉冲击力更强，且能容纳更多画面内容。16:9 仍有轻微裁切风险。

## 语言规则

**所有图片中的文字必须使用中文**，包括标题、标签、坐标轴、图例、注释等。Prompt 中需明确写明中文文字内容，避免生成英文图片后返工。

---

## ⭐ yairouter API (gpt-image-2) — 默认后端

客户端脚本：`scripts/yairouter_img.py`

**默认参数（成本控制）**：
- **size: `1:1`**（1024×1024，正方形）
- **quality: `high`**

**默认分辨率规则**：所有图片默认 1K，包括封面图。`1:1` = 1024×1024，`21:9` = 1248×528。需要 2K/4K 时**必须先告知费用差异并要求用户确认**，不得擅自升级。

**ENV**：需要 `YAI_API_KEY` 环境变量（shell 环境变量优先，`.env` 兜底）

### Size 快捷映射

| 快捷名 | 实际尺寸 | 推荐场景 |
|--------|----------|----------|
| `1:1` | 1024×1024 | 正方形配图（默认） |
| `3:4` | 1024×1536 | 小红书卡片 |
| `16:9` | 1792x1024 | 横版配图 |
| `2.35:1` | 1792x768 | 电影宽幅（封面图） |

> ⚠️ 上述 size 目前不生效（见文件头已知问题），仅为工具接口保留。

**场景速查**：

| 用途 | size | 像素 |
|------|------|------|
| 公众号封面（默认 1K） | `21:9` | 1248×528 |
| 小红书卡片 | `3:4` | 1024×1536 |
| 正方形配图 | `1:1` | 1024×1024 |
| 竖版海报 | `9:16` | 1024×1792 |

**费用递增**：像素量决定成本。1K 最便宜，4K 最高。

### 批量生成

通过 JSON 配置文件 + `--config` 参数，每张卡片可覆盖全局 size：

```json
{
  "output_dir": "content/my-article/images",
  "size": "1024x1536",
  "quality": "high",
  "cards": [
    {
      "title": "封面",
      "prompt": "A cinematic illustration of...",
      "size": "1248x528",
      "filename": "cover.png"
    },
    {
      "title": "卡片2",
      "prompt": "An infographic showing...",
      "size": "1024x1536",
      "filename": "card-01.png"
    }
  ]
}
```

---

## zairouter API (gpt-image-2) — 备选后端

客户端脚本：`scripts/zairouter_client.py`

**端点**: `https://api.zairouter.com/v1/images/generations`
**模型**: `gpt-image-2`
**认证**: `Authorization: Bearer $ZAI_API_KEY`（shell 环境变量优先，`.env` 兜底）

与 yairouter 共享同一上游，**size 参数同样失效**（2026-08-07 实测，见实验报告）。仅在 yairouter 不可用时作为备选。

---

## apimart.ai API (gpt-image-2) — 历史后端（禁用）

客户端脚本：`scripts/apimart_client.py`

**默认参数**：size: `1:1`, resolution: `1k`。ENV：`API_MART_KEY`。

使用 size（比例）+ resolution（分辨率）两级参数。支持 1k/2k/4k 分辨率。
