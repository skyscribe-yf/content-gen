# 微信公众号草稿发布失败记录

日期：2026-07-16
文章：猜下一个字，为什么能学会写文章？预训练全过程

## 错误信息

```
Error: Publish failed 45166: invalid content hint
```

## 尝试过的错误方向

1. **链接数超限** — 以为是 `mp.weixin.qq.com/s/` 链接超过 5 个导致。精简正文+尾部链接后仍然失败。实际上 BPE 文章有 8+ 链接也能发布，这个方向是错误的。

2. **图片路径带 `images/` 前缀** — 改为去掉前缀把图片放到根目录。图片上传成功了但错误依旧。上述两个修改都是必要但不充分的条件。

## 真正的根因

**图片必须放在 weixin.md 的同一级目录下，不能放在 `images/` 子目录中。**

baoyu-post-to-wechat 的 `wechat-api.ts` 脚本：
- 解析 markdown 中的 `![](path)` 时，将 path 视为相对文章所在目录
- 生成 HTML 后通过 `<img>` 标签的 src 路径解析本地文件
- 如果图片在 `images/` 子目录但 markdown 写的是 `![](00-cover.png)` → 在文章目录找不到 → 上传失败 → 残留 `WECHATIMGPH_*` 占位符 → 公众号 API 返回 45166

## 正确做法

```
article-dir/
├── weixin.md          ← 文章
├── 00-cover.png       ← 封面图（同级）
├── 01-xxx.png         ← 正文图（同级）
├── 02-xxx.png
└── ...
```

- `weixin.md` 中引用：`![alt](00-cover.png)`（不带 `images/` 前缀）
- frontmatter `cover: 00-cover.png`（不带 `images/` 前缀）
- 如果图片在 `images/` 子目录，需要 `cp images/*.png .` 复制到同级

## 发布命令

```bash
cd /home/skyscribe/srcs/content-gen
bun .agents/skills/baoyu-post-to-wechat/scripts/wechat-api.ts \
  "content/2026-07-27-预训练/weixin.md" \
  --theme grace --color blue --remote
```

文章发布成功 media_id: `kOcXH4SytIYksTGfHvAVQnweWRNss2Vy4pTQ6uGj3l-JHFnuHobUG6Ul4fNC`
