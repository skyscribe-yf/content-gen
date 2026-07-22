# 知乎 CDP 粘贴自动化

## 前置条件

1. Chrome 浏览器已登录知乎账号（CDP Session 保持）
2. agent-browser 工具可用
3. `promote/zhihu-{slug}.html` 已生成

## 专栏文章 (zhuanlan.zhihu.com) 发布流程

### Step 1: 打开编辑器

```
agent-browser open https://zhuanlan.zhihu.com/publish
```

等待页面加载完全（编辑器出现）。

### Step 2: 填写标题

```
agent-browser fill @title-input "文章标题"
```

知乎专栏标题自动从 H1 提取，也可手动填写。

### Step 3: 清空编辑器

```
agent-browser click @editor
agent-browser press Control+a
agent-browser press Delete
```

### Step 4: 粘贴 HTML 内容

由于知乎是富文本编辑器，需要把 HTML 粘贴为富文本格式。

**方案 A**: 通过 baoyu-markdown-to-html 生成自包含 HTML → 浏览器打开 → Ctrl+A → Ctrl+C → 切到知乎编辑器 → Ctrl+V

```bash
# 1. 生成 HTML
bun {baoyu-base}/scripts/main.ts promote/zhihu-adam.zhihu.md --theme simple

# 2. 在浏览器中打开并复制
agent-browser open file:///path/to/promote/zhihu-adam.zhihu.html
agent-browser wait 2000
agent-browser press Control+a
agent-browser press Control+c

# 3. 切到知乎编辑器粘贴
agent-browser open https://zhuanlan.zhihu.com/publish
agent-browser wait 3000
agent-browser click @editor
agent-browser press Control+v
```

**方案 B**: 使用 `innerHTML` 直接写入（需要 evaluate）

```javascript
// 通过 agent-browser eval 写入编辑器
const editor = document.querySelector('[contenteditable="true"]');
editor.innerHTML = `{HTML_CONTENT}`;
// 触发 input 事件让 Draft.js 识别
editor.dispatchEvent(new Event('input', {bubbles: true}));
```

### Step 5: 逐张上传图片

按 `references/图片上传.md` 的串行上传顺序逐一插入。

```python
# 伪代码（通过 CDP）
for image_path in images:
    # 点击图片上传按钮
    page.locator('.toolbar [data-testid="image-upload"], button:has-text("图片")').click()
    # 等待文件选择器
    file_input = page.locator('input[type="file"]')
    file_input.set_input_files(image_path)
    # 等待上传完成
    page.wait_for_selector(f'src*="//pic.zhihu.com"')
```

### Step 6: 预览验证

```
agent-browser click @preview-button
agent-browser wait 3000
```

检查：
- 所有公式是否渲染为矢量图（不是乱码）
- 图片是否正确显示
- 排版是否错乱
- 系列导航是否正确

### Step 7: 发布

```
agent-browser click @publish-button
agent-browser wait 5000
```

获取 URL：`https://zhuanlan.zhihu.com/p/XXXXXXX`

### Step 8: 回填 URL

```bash
# 更新 draft-status.yaml
python3 scripts/publish-scheduler.py publish <topic> zhihu
# 手动填写 zhihu_url
```

## 回答 (question/{id}/answer) 发布流程

```bash
# 1. 打开问题页面
agent-browser open https://www.zhihu.com/question/{id}/write

# 2. 等待编辑器加载
agent-browser wait 3000

# 3. 粘贴内容（同专栏流程）
agent-browser click @answer-editor
agent-browser press Control+v

# 4. 预览 + 发布
agent-browser click @submit-answer
```

## 常见问题

| 问题 | 原因 | 解决 |
|------|------|------|
| `$$...$$` 显示为纯文本 | 粘贴为纯文本 | 重新以 HTML 格式粘贴 |
| 图片不显示 | 外部图床 | 重新上传到知乎 CDN |
| 多图丢失 | Draft.js race | 串行上传，逐张验证 |
| 编辑器无响应 | 内容过大 | 分批粘贴 |
| 粘贴后格式丢失 | HTML 标签被过滤 | 仅保留 `<p> <h1-h6> <ul> <ol> <li> <blockquote> <strong> <em> <a> <img> <hr>` |

## 安全间隔

- 同一知乎账号发布间隔 ≥ 3 分钟
- 每次发布前检查 Cookie 有效性
- 发布后立即获取 URL，防止丢失
