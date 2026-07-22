---
name: post-zhihu
description: Posts content to Zhihu (知乎) platform — article (专栏) or answer (回答). Handles LaTeX formula preservation, WeChat→Zhihu link replacement, and automated CDP paste into Zhihu WYSIWYG editor. Use when user mentions "发布知乎", "post to zhihu", "知乎专栏", "知乎回答", or "知乎发布".
version: 1.0.0
metadata:
  openclaw:
    homepage: internal
    requires:
      anyBins:
        - bun
        - npx
---

# Post to Zhihu (知乎)

## When to Use

- User asks to publish an article to Zhihu 专栏 or answer a Zhihu question
- User asks to convert WeChat-focused content to Zhihu-friendly format
- User needs to manage Zhihu URL tracking in draft-status.yaml
- User asks about Zhihu image upload, formula handling, or cross-platform link replacement

## Key Facts About Zhihu

1. **Zhihu supports native LaTeX** via MathJax — `$$...$$` displays and `$...$` inline
2. **Zhihu WYSIWYG editor** auto-renders `$$...$$` blocks when pasted as rich text
3. **No external links in answer body** — Zhihu demotes answers with clickable URLs
4. **CTA allowed indirectly** — "完整版发在公众号 XXX" is fine, "关注公众号" is borderline
5. **LaTeX is better than Unicode** — paste LaTeX source, Zhihu renders it natively

## User Input Tools

When this skill prompts the user, follow this tool-selection rule:

1. **Prefer built-in user-input tools** exposed by the current agent runtime
2. **Fallback**: numbered plain-text message
3. **Batch** all applicable questions into a single call

## Script Directory

`{baseDir}` = this SKILL.md's directory. `${BUN_X}` = `bun` if installed, else `npx -y bun`.

| Script | Purpose |
|--------|---------|
| `scripts/zhihu-formula.py` | Unicode → LaTeX 双向转换 |
| `scripts/zhihu-links.py` | 微信链接 → 知乎链接替换 |
| `scripts/zhihu-paste.ts` | CDP 粘贴到知乎编辑器 |

Project-level scripts (in `{root}/scripts/`):
| Script | Purpose |
|--------|---------|
| `scripts/publish-scheduler.py` | 发布调度和状态管理 |

## Preferences (EXTEND.md)

Check these paths in order; first hit wins:

| Path | Scope |
|------|-------|
| `.baoyu-skills/post-zhihu/EXTEND.md` | Project |
| `$HOME/.baoyu-skills/post-zhihu/EXTEND.md` | User home |

**EXTEND.md keys**:

| Key | Default | Description |
|-----|---------|-------------|
| `default_mode` | `article` | 发布模式: `article` (专栏) 或 `answer` (回答) |
| `default_question_url` | empty | 默认回答的问题 URL (mode=answer 时) |
| `zhihu_cdp_profile` | empty | Chrome profile path for Zhihu session |

## Workflow

```
- [ ] Step 0: Determine mode (article vs answer)
- [ ] Step 1: Resolve content source
- [ ] Step 2: Replace WeChat links → Zhihu links
- [ ] Step 3: Convert formulas (Unicode → LaTeX)
- [ ] Step 4: Generate Zhihu-ready HTML (保留 $$...$$ 不渲染)
- [ ] Step 5: Paste content into Zhihu via CDP
- [ ] Step 6: Upload images (串行 + DOM 验证)
- [ ] Step 7: Set cover image
- [ ] Step 8: Preview → Publish → Capture URL → update tracking
```

### Step 0: Determine Mode

| Mode | Target URL format | Content length |
|------|-------------------|----------------|
| `article` (专栏) | `zhuanlan.zhihu.com/p/...` | 2000-5000 字 |
| `answer` (回答) | `www.zhihu.com/question/...` | 500-2000 字 |

If user didn't specify → Ask:

> "发布到知乎 专栏文章 还是 回答已有问题？"

### Step 1: Resolve Content Source

| Source | Detection | Next |
|--------|-----------|------|
| `promote/zhihu-{slug}.md` exists | File exists | Step 2 |
| `promote/zhihu-{slug}.md` missing | Check `draft-status.yaml` | Generate from `content/{slug}/weixin.md` |
| Mode = answer | Need question URL | Ask for question link |

**Content source priority**:
1. `promote/zhihu-{slug}.md` (pre-generated Zhihu version) → use directly
2. `content/{slug}/weixin.md` → adapt for Zhihu

### Step 2: Replace WeChat Links

WeChat links in the content (`mp.weixin.qq.com`) must be replaced with Zhihu links for cross-referencing.

```bash
python3 {root}/scripts/zhihu-links.py <input.md> --mapping templates/zhihu-urls.yaml
```

**Rules**:
- `https://mp.weixin.qq.com/s/XXX` → `https://zhuanlan.zhihu.com/p/YYY` (if mapping exists)
- Fallback: keep URL but annotate `（原文发于公众号數解AI）`
- Series navigation at bottom → ensure all links use Zhihu URLs

See `references/链接替换.md` for full mapping mechanism.

### Step 3: Formulas — Unicode → LaTeX

**Zhihu natively supports LaTeX via MathJax.** Content currently uses Unicode formulas must be converted back to LaTeX for Zhihu.

```bash
python3 {root}/scripts/zhihu-formula.py <input.md> --direction unicode-to-latex
```

**Conversion rules**:
- `θₜ₊₁` → `\theta_{t+1}`
- `gₜ` → `g_{t}`
- `η` → `\eta`
- `m̂ₜ` → `\hat{m}_{t}`
- `√v̂ₜ` → `\sqrt{\hat{v}_{t}}`
- `x²` → `x^{2}`
- Already LaTeX (`$$...$$` or `$...$`) → pass through unchanged
- Complex multi-char subscripts/superscripts → require LaTeX `_{...}` `^{...}`

Post-conversion verification:
```bash
python3 {root}/scripts/zhihu-formula.py <input.md> --check
```

See `references/公式处理.md` for full mapping table.

### Step 4: Generate Zhihu-Ready HTML

**Option A: Use baoyu-markdown-to-html with LaTeX passthrough**

```bash
${BUN_X} {baoyu-md-html-base}/scripts/main.ts <input.md> --theme simple
```

**Important**: The HTML must contain raw `$$...$$` LaTeX for Zhihu to render.
If baoyu's converter escapes or modifies `$$...$$`, use the `--no-math` flag or post-process.

**Check**: Open output HTML in browser → formulas should appear as raw `$...$` or `$$...$$` (not KaTeX rendered).

**Option B: Markdown → textarea paste (if HTML paste loses latex)**

Use CDP to paste raw markdown into Zhihu's markdown mode (if available), or use the input helper:
- Zhihu editor has a "公式" button for each `$$` block

### Step 5: Paste into Zhihu (CDP Automation)

Use agent-browser to paste formatted HTML into Zhihu editor.

**For 专栏文章 (article)**:
1. Open `https://zhuanlan.zhihu.com/publish` in Chrome (CDP connected)
2. Wait for editor to load
3. Set title
4. Clear editor
5. Paste HTML content (retaining `$$...$$` formulas)
6. Preview → verify formulas render
7. Submit

**For 回答 (answer)**:
1. Open question page in Chrome
2. Click "写回答"
3. Wait for editor
4. Clear, paste, preview, submit

**CDP Details**: See `references/cdp-粘贴.md` for full automation flow with agent-browser.

### Step 6: Capture URL & Update Tracking

After successful publish:

1. Get Zhihu URL from browser:
   - Article: `https://zhuanlan.zhihu.com/p/XXXXXXX`
   - Answer: `https://www.zhihu.com/question/.../answer/XXXXXXX`

2. Update `draft-status.yaml`:
   ```yaml
   - slug: "2026-07-10-优化器"
     ...
     zhihu_url: "https://zhuanlan.zhihu.com/p/XXXXXXX"
   ```

3. Update `templates/zhihu-urls.yaml` mapping (for future cross-ref).

4. Update `publish-schedule.yaml` if needed.

## Naming Convention

```
promote/zhihu-{slug}.md    # 知乎版内容源
promote/zhihu-{slug}.html  # 知乎粘贴版 HTML
```

## Self-Check — Before Publishing

- [ ] All `$$...$$` formulas render correctly in Zhihu preview?
- [ ] No bare WeChat URLs in article body (replaced or annotated)?
- [ ] CTA uses indirect wording ("完整版发在公众号數解AI")?
- [ ] At least 3 引流钩子 embedded?
- [ ] Content stands alone (valuable without reading WeChat original)?
- [ ] Title ≤ 40 chars, ends with question or insight hook?
- [ ] `zhihu_url` will be recorded after publish?

## Troubleshoot

| Issue | Fix |
|-------|-----|
| `$$...$$` shows as raw text | Zhihu editor not in rich-text paste mode; re-paste as HTML |
| LaTeX render error in preview | Check for unescaped `_` or `{}` outside math mode |
| Formula too long for inline | Convert `$...$` to `$$...$$` (display mode) |
| Image not showing | Upload to Zhihu image bed via editor first |
| Paste loses formatting | Use agent-browser `fill` with innerHTML instead of ctrl+v |
| "内容包含外部链接" warning | Remove all URLs except Zhihu-internal ones |

## References

| File | Content |
|------|--------|
| `references/公式处理.md` | Unicode↔LaTeX 映射表和转换规则 |
| `references/链接替换.md` | 微信链接→知乎链接映射机制 |
| `references/图片上传.md` | 串行上传策略和 Draft.js race condition 规避 |
| `references/cdp-粘贴.md` | agent-browser 知乎编辑器自动化 |

## Templates

| File | Content |
|------|--------|
| `templates/zhihu-urls.yaml` | 已发布文章的知乎 URL 映射表 |
