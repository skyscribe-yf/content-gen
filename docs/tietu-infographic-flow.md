# 贴图素材归档 + Infographic 生成流程

> 2026-09-09 建立（v2 结构）。把公众号「贴图」（图片消息，`item_show_type=8`）的原始截图下载归档、OCR 提取主要文字，并基于要点生成一张 info graphic 风格图片。**所有产物统一放在 `content/` 下，按日期 + 标题组织。**
>
> ⚠️ **v2 结构（2026-09-09 确立）**：不再使用旧的 `branding/style-corpus/tietu-images/` 归档，改为 `content/<日期>-tietu/<标题>/` 一级子目录内放全套产物（原始素材 + 识别文案 + prompt + 最终图）。

## 目标（双轨框架中的「贴图轨」素材落盘）

1. 按**发表日期**把原图下载到 `content/<日期>-tietu/<标题>/`；
2. 逐张 OCR 提取图片里主要文字，写进 `summary.json`（识别文案）；
3. 读取/归纳要点后，写出手敲风格的 `prompt.md`，为每一条贴图生成一张扁平 info graphic（`infographic.png`），放入同一目录。

## 目录约定（v2）

```
content/
├── 2026-09-07-tietu/
│   ├── ollama的峰谷价模式叠加1-3优惠还可以的/
│   │   ├── 01.jpg … 04.jpg      # 原始素材（按图序命名）
│   │   ├── summary.json          # 逐张 OCR 识别文案
│   │   ├── prompt.md             # 生成 info graphic 的 prompt
│   │   └── infographic.png       # 最终生成的 info graphic
│   └── c++之父锐评AI，到底谁膨胀的更厉害/
│       └── …
└── 2026-08-24-tietu/
    └── …（每天最多一个 -tietu 容器，内放多条贴图子目录）
```

- **容器目录**：`content/<YYYY-MM-DD>-tietu/`，按发布日期。
- **子目录**：`<标题 slug>`（清洗后截断 40 字符），一条贴图一个子目录。
- 四个层级产物：**原始素材 `*.jpg`** / **识别文案 `summary.json`** / **生成 prompt `prompt.md`** / **最终图 `infographic.png`**。

## 主要事实源

- **贴图清单（标题/发布时间/图片 URL）**：`branding/style-corpus/publish-data.json` 及 `publish-data-*.json` 快照中的 `item_show_type=8` 条目；`wechat-published-index.json` 提供历史索引。脚本 `list_tietu()` 合并这些快照并按时序去重。
- **发布时间**：部分快照 `sent_info.time` 缺失（为 0/无），需按 `wechat-published-index.json` 的 URL 抓取贴图页 `send_time` / `ct` 回填。
- **贴图轨运营背景**：[wechat-ops.md](wechat-ops.md)「双轨框架」与 [wechat-data-insights.md](wechat-data-insights.md)。
- **infographic 要点 briefs**：由 AI 读取 OCR 结果归纳，存为一个 JSON（`tietu-infographic-briefs.json`），字段含 `dir / title / point / keypoints[]`。

## 脚本

固化脚本：[`scripts/tietu_infographic.py`](../scripts/tietu_infographic.py)。

```bash
# 步骤 1+2：抓取贴图清单并下载原图到 content/<日期>-tietu/<标题>/
python scripts/tietu_infographic.py --download

# 步骤 3：OCR（自动把 PNG-as-jpg 归一化后逐张识别，写入 summary.json）
python scripts/tietu_infographic.py --ocr

# 步骤 4：按 briefs 生成 prompt.md + infographic.png（幂等，跳过已存在）
python scripts/tietu_infographic.py --infographic --briefs /tmp/tietu-infographic-briefs.json

# 只处理含指定子串的目录
python scripts/tietu_infographic.py --infographic --briefs /tmp/tietu-infographic-briefs.json '20260903-1758' '20260904-1345'
```

> 脚本默认输出根目录为 `content/`（以 `<日期>-tietu/<标题>` 落地）；旧版 `--root` 指向 `图片/贴图归档` 的参数已废弃。

## 依赖与注意

- **API Key**：`yairouter_img.py` 需要 `YAI_API_KEY`；若 shell 环境与项目 `.env` 都没有，先 `source ~/.bash_env` 再执行（全局密钥文件）。
- **OCR**：`dim ocr recognize <img> --output-mode text --json`。
- **图片生成后端**：`scripts/yairouter_img.py`（默认 gpt-image-2，失败自动 fallback grok-imagine-image-quality）。
- ⚠️ **上游 API 忽略 size 参数**（2026-08-07 实测），请求 `1024x1024` 可能返回 `1024x1536`，info graphic 输出尺寸以实际返回为准，不做强制裁剪。
- ⚠️ 部分 CDN 图片实际为 **PNG 却命名 `.jpg`**（如 `sz_mmbiz_png/...?wx_fmt=png`），直接 `image.read`/`ocr` 会报 "Image signature does not match"，脚本 `normalize_jpg()` 用 PIL 转真 JPEG 修复。
- ⚠️ CDN 图片 URL 带 query（`/0?wx_fmt=jpeg`）时必须**带完整 query** 才能下载；直接裸 URL（缺 `/0?wx_fmt=...`）会返回 **HTTP 400**。
- 生成 infographic 若遇 `requests.ConnectionError`（连接被重置），属上游偶发，重跑 `--infographic` 即可（幂等跳过已成功项）。
- **人工核读**：素材多为 X/推特/新闻截图，OCR 可能误识别（如 `Ox Alpha` 识别成 `Dx Alpha`、专名 `崔添翼` 等）。生成 infographic 前建议核读 `summary.json`；发布仍走既定质量门禁。

## 迁移说明（v1 → v2）

- 旧归档位于 `branding/style-corpus/tietu-images/`（`YYYYMMDD-HHMM-slug` 目录），已按发布日期 + 标题迁入 `content/<日期>-tietu/<标题>/`。
- `content/2026-09-07-tietu-infographic/`（扁平，含 ollama/cpp 两个 prompt + 两张图）已并入 `content/2026-09-07-tietu/<标题>/`。
- 迁移时各目录的 `jpg`（原始素材）、`summary.json`（识别文案）、`prompt*.md`、`infographic.png` 一并落位，无缺失。

## 相关文档

- 图片生成后端规范：[image-generation.md](image-generation.md)
- 贴图轨运营策略：[wechat-ops.md](wechat-ops.md)（双轨框架 / 贴图轨）
- 公众号数据审计：[wechat-data-audit/](../.agents/skills/wechat-data-audit/SKILL.md)
