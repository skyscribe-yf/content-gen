# 数学公式渲染规则

## 写作禁区（踩过的坑）

- **禁止在公式里写裸 `<`**：`$x_{<t}$` 中的 `<` 会在 Markdown→HTML 阶段被当作标签吞掉，
  整条公式消失（2026-09-03 MLE 篇有 3 个独立公式 + 2 处内联公式整条丢失）。
  统一用 `\lt`：`x_{\lt t}`（2026-08-29 大数定律篇已验证）。`>` 同理用 `\gt`。
- **禁止用 `\text{}` 包中文**：MathJax 对 CJK 走 `<text>` 分支，SVG 化后在微信端丢字/错位。
  中文流程链（如「参数 → logit → 概率 → NLL」）直接写正文，不要塞进 `$$...$$`。
- **改完公式必须回查渲染结果**：用 `.venv-mdnice/bin/python scripts/mdnice-render.py <md> --output /tmp/x.html`
  渲染后检查 `merror` 计数为 0、SVG 数量与公式数量一致；再把 SVG 的 `data-c` 码点还原成字符核对内容。

## 格式

- 使用 LaTeX 语法：内联 `$...$`，独立 `$$...$$`
- 禁用 Unicode 公式（`𝜇`、`²` 等），可读性和可维护性都不如 LaTeX

## 微信公众号渲染方案

使用 Python `mdnice` 包（Playwright 自动化 mdnice.com），公式渲染与 mdnice.com 网页完全一致。

| 公式类型 | 渲染方式 | 原因 |
|----------|---------|------|
| 内联 `$...$` | SVG 内联（MathJax `matrix(1 0 0 -1)` 变换） | mdnice 的 MathJax 输出使用矩阵变换而非 `scale(1,-1)`，微信编辑器兼容 |
| 独立 `$$...$$` | SVG 内联（`<section class="block-equation">`） | 同上，mdnice 的渲染在微信编辑器中无镜像/模糊问题 |

### 技术实现

1. **`scripts/mdnice-render.py`**：
   - 调用 `mdnice.to_wechat()` 将 Markdown 转为微信 HTML
   - 主题映射：grace → scienceBlue，modern → geekBlack 等
   - 输出 HTML 包含内联 SVG 公式 + 内联样式

2. **`md-to-wechat.ts` 集成**：
   - `renderWithMdnice()` 调用 Python 脚本，传入预处理后的 Markdown
   - 图片先用 `WECHATIMGPH_N` 占位符替换，mdnice 渲染后占位符保留在 HTML 文本中
   - `resolveContentImages` + wechat-api 上传图片到微信 CDN

3. **Python 环境**：
   - venv: `.venv-mdnice/`
   - 依赖: `mdnice` (0.0.3), `playwright`, `requests`
   - Playwright Chromium: `~/.cache/ms-playwright/`

### 与旧方案的区别

旧方案（已废弃）：patch `baoyu-md` dist + `mathjax-full` + `sharp` SVG→PNG 转换
- 问题：`npm install` 覆盖补丁，`scale(1,-1)` 导致微信镜像，需手动维护多个补丁
- 新方案用 mdnice.com 的渲染引擎，零补丁，公式渲染与网站完全一致

### 注意事项

- `mdnice` Python 包每次调用启动 Playwright 浏览器，约 10-30 秒
- mdnice.com 如遇网络问题，可通过 `editor_url` 参数指向自部署实例
- `pip install mdnice` 后需额外安装 `requests`（包的 setup.py 漏了依赖声明）
