# 公众号图片路径规则

> 硬性规则。违反会导致 `45166: invalid content hint` 发布失败。

## 规则

`wechat-api.ts` 把 markdown 中的图片路径解析为**相对文章文件所在目录**。图片必须与 `weixin.md` 同级，否则发布会报错 `45166: invalid content hint`（图片上传失败后残留 `WECHATIMGPH_*` 占位符）。

## 目录结构

```
✅ 正确结构：                 ❌ 错误结构：
article-dir/                 article-dir/
├── weixin.md                ├── weixin.md
├── 00-cover.png  ← 同级     └── images/
├── 01-xxx.png               ├── 00-cover.png  ← 子目录找不到
└── ...                      └── ...
```

## 引用方式

- **markdown**：`![alt](00-cover.png)`（不带 `images/` 前缀）
- **frontmatter**：`cover: 00-cover.png`（不带 `images/` 前缀）

## 发布前操作

配图生成通常在 `images/` 子目录，发布前必须：

```bash
cp images/*.png .
```

复制到文章根目录。

## 踩坑记录

详见 [`docs/wechat-publish-2026-07-16-debug.md`](wechat-publish-2026-07-16-debug.md)。
