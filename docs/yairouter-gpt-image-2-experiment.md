# yairouter gpt-image-2 实测探索报告

日期：2026-08-07（约 20 次真实生成调用，quality=low/medium，最小成本）

## 结论速览

| 项目 | 结果 |
|------|------|
| gpt-image-2 是否在模型列表 | ✅ 是（共 106 个模型） |
| `/v1/images/generations` 是否可用 | ✅ HTTP 200，OpenAI 兼容返回 |
| 返回格式 | ✅ `data[0].b64_json` + `usage`（OpenAI 风格） |
| 中文文字渲染 | ✅ 实测「数解AI」「梯度下降入门」渲染正确 |
| Responses API 路径 | ✅ `/v1/responses` + `image_generation` 工具可用 |
| **size 参数** | ❌ **完全被忽略**（见下） |
| 4K（文档声称支持） | ❌ 实测 3840x2160 请求返回 1254x1254 |
| qwen-image-plus / z-image-turbo | ❌ HTTP 403 当前 key 无权限 |
| grok-imagine-image-quality | ⚠️ 可用但 `size` 参数直接报 400 |
| 与 zairouter 对比 | ⚠️ **zairouter 同样失效**（见下） |

## 关键发现：size 参数被忽略

同一 prompt 请求不同 size，返回的实际图片尺寸完全不由请求决定：

```
请求 size        → 实际输出（yairouter）
1024x1024        → 1254x1254（多次稳定）
1024x1536        → 1254x1254
1536x1024        → 1254x1254
1248x528 (21:9)  → 1024x1536（竖版！）
3840x2160 (4K)   → 1536x1024 / 1254x1254
auto             → 1254x1254
```

- 同参数连续 3 次请求：全部返回 1254x1254（单次会话内稳定）
- 不同时段多次测试：出现过 1254x1254、1536x1024、1024x1536、1086x1448 四种输出
- 疑似多个上游节点轮转，各节点固定输出自己的默认尺寸，服务端丢弃请求的 size
- Responses API 同样失效：请求 `size: 1024x1024`，响应对象里明确写着 `"size": "1254x1254"`

### 官方文档与实测矛盾

yairouter 官方博客（2026-04-25，7-18 复验）声称：

> `3840x2160` / `2160x3840` 4K 输出成功，解码后 JPEG 文件尺寸确认一致。

实测（2026-08-07）不支持该声明。4K 请求返回 1254x1254 PNG。

### zairouter（项目现有后端）同样失效

对照实验（同一天）：

```
请求 size        → 实际输出（zairouter）
1024x1024        → 1086x1448
1248x528 (21:9)  → 1254x1254
3840x2160 (4K)   → 1024x1536
```

说明这不是 yairouter 特有缺陷，是两站共享的 gpt-image-2 上游当前行为。**项目现有 zairouter_client.py 生成的「21:9 封面」实际尺寸不受控**，与 docs/image-generation.md 中的描述（21:9 = 1248x528 实测通过）不符，文档已过时。

## 可行方案

### 方案 A：生成 + 后处理裁剪（推荐，立即可用）

gpt-image-2 生成质量与中文渲染可靠，只是尺寸失控 → 用 PIL 把输出图 center-crop 到目标比例，再 resize 到目标尺寸：

```python
from PIL import Image
def fit(img_path, target_w, target_h, out_path):
    im = Image.open(img_path)
    tw, th = target_w, target_h
    # center-crop 到目标比例
    src_ratio, dst_ratio = im.width / im.height, tw / th
    if src_ratio > dst_ratio:
        new_w = int(im.height * dst_ratio); x = (im.width - new_w) // 2
        im = im.crop((x, 0, x + new_w, im.height))
    else:
        new_h = int(im.width / dst_ratio); y = (im.height - new_h) // 2
        im = im.crop((0, y, im.width, y + new_h))
    im = im.resize((tw, th), Image.LANCZOS)
    im.save(out_path)
```

- 优点：不依赖上游修 bug，1K 图裁 21:9 仍有 1248x528 可用分辨率
- 风险：center-crop 可能切掉构图关键内容 → prompt 必须写「主体居中、四周留白、重要元素避开边缘」；封面文字类 prompt 风险最高（竖版输出裁 21:9 损失大）
- 输出尺寸不可预期（1254x1254 / 1536x1024 / 1024x1536），建议生成后读取实际尺寸再决定裁剪方向

### 方案 B：固定输出规避

既然输出集中在 1254x1254（正方形）与 1024x1536（竖版），可：
- 需要 1:1 时直接接受 1254x1254 并 resize 到 1024x1024（损失极小）
- 需要 3:4 小红书时接受 1024x1536（正好 2:3，接近）
- 需要 21:9 封面时只能用方案 A 裁剪

### 方案 C：向提供商反馈

向 YAI 技术团队反馈「size 参数失效、与官方博客不符」（响应对象的 `size` 字段是服务端写的，说明服务端知道自己输出了什么）。若上游为 OpenAI 官方 gpt-image API，标准尺寸 1024x1024 / 1536x1024 / 1024x1536 应生效——可再次确认。**反馈前先确认计费**：若按请求 size 计费而实际输出 1254x1254，成本核算也会失真。

## 其他模型对比

| 模型 | 结果 |
|------|------|
| gpt-image-2 | ✅ 可用，size 忽略 |
| grok-imagine-image-quality | ⚠️ 可用，传 size 报 400（需去掉 size 参数） |
| qwen-image-plus | ❌ 403 无权限 |
| z-image-turbo | ❌ 403 无权限 |

## 测试方法备忘

```bash
# 关键请求体（curl 风格）
curl -sS https://api.yairouter.com/v1/images/generations \
  -H "Authorization: Bearer $YAI_API_KEY" -H "Content-Type: application/json" \
  -d '{"model":"gpt-image-2","prompt":"...","n":1,"size":"1024x1024","quality":"low","output_format":"png"}'
# 实际尺寸从返回 b64 的 PNG IHDR 读取（偏移 16=宽, 20=高）
```

---

## 补充实测（2026-08-15）

**结论：gpt-image-2 对该 key 的 team 已无权限，项目默认后端自动 fallback 到 grok-imagine-image-quality。**

| 项目 | 结果 |
|------|------|
| gpt-image-2 带 size 参数 | ❌ HTTP 400 `Argument not supported: size`（不再「忽略」，直接拒绝） |
| gpt-image-2 不带 size | ❌ HTTP 404 `model does not exist or your team ... does not have access` |
| zairouter（备选） | ❌ HTTP 401 key 已失效（`authentication token has been invalidated`） |
| grok-imagine-image-quality + `response_format=b64_json` | ✅ HTTP 200，输出 1024x1024 JPEG |
| grok-imagine-image-quality 不带 b64_json | ❌ HTTP 400（Zero Data Retention team 只能用 b64_json） |
| grok-imagine-image-quality 中文渲染 | ✅ 5 张公众号配图验证：标题/标签逐字正确 |
| grok 封面（1280x720） | ⚠️ 输出非 21:9，需 PIL center-crop 到 1280x548 |

**落地改动**（`scripts/yairouter_img.py` 2026-08-15）：
- 请求体按模型分支：gpt-image-2 带 `size`；grok 不带 `size`、带 `response_format="b64_json"`
- gpt-image-2 失败（400/404）自动 fallback grok，无需人工换后端
- 保存时检测 JPEG 字节 + `.png` 扩展名 → 自动转真 PNG（微信上传格式匹配）
- 封面 21:9 裁剪流程见 `docs/image-generation.md`

**教训**：grok 不支持 size，封面需裁剪；裁剪前确认 prompt 已要求「重要元素避开上下边缘」，否则 center-crop 会切掉角落内容（本次 00-cover 左下角小字被裁，可接受）。
