#!/usr/bin/env python3
"""
把 baoyu-markdown-to-html 的输出再处理：
1. 用知乎兼容 CSS 替换微信样式
2. 确保公式保持 $$...$$ 不被 KaTeX/MathJax 渲染
3. 输出可直接浏览器打开 Ctrl+A+C 粘贴到知乎的 HTML
"""

import re
import sys

ZHIHU_CSS = """
body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
  font-size: 16px; line-height: 1.8; color: #1a1a1a;
  max-width: 720px; margin: 40px auto; padding: 0 20px;
}
h1 { font-size: 24px; font-weight: 700; margin: 32px 0 16px; }
h2 { font-size: 20px; font-weight: 700; margin: 28px 0 12px; padding-bottom: 6px; border-bottom: 1px solid #eee; }
h3 { font-size: 17px; font-weight: 700; margin: 24px 0 10px; }
p { margin: 14px 0; }
blockquote {
  margin: 16px 0; padding: 12px 16px;
  background: #f6f8fa; border-left: 4px solid #1a6dd4;
  border-radius: 0 4px 4px 0;
}
table { border-collapse: collapse; width: 100%; margin: 16px 0; font-size: 15px; }
th, td { border: 1px solid #ddd; padding: 10px 14px; text-align: left; }
th { background: #f4f6f8; font-weight: 600; }
code { background: #f4f6f8; padding: 2px 6px; border-radius: 4px; font-size: 90%; }
pre { background: #f6f8fa; padding: 16px; border-radius: 8px; overflow-x: auto; font-size: 90%; line-height: 1.6; }
pre code { background: none; padding: 0; }
hr { border: none; border-top: 1px solid #e8e8e8; margin: 32px 0; }
ul, ol { padding-left: 24px; margin: 10px 0; }
li { margin: 6px 0; }
a { color: #1a6dd4; text-decoration: none; }
a:hover { text-decoration: underline; }
.cta {
  background: #f0f7ff; border: 1px solid #b8d8ff;
  padding: 16px 20px; border-radius: 8px; margin: 20px 0;
}
img { max-width: 100%; display: block; margin: 20px auto; border-radius: 4px; }
strong { color: #000; }
"""


def process_html(inpath: str, outpath: str):
    with open(inpath, encoding='utf-8') as f:
        html = f.read()

    # 提取 body 内容
    body_match = re.search(r'<body[^>]*>(.*?)</body>', html, re.DOTALL)
    if not body_match:
        print("❌ 无法找到 body 内容")
        return
    body_content = body_match.group(1)

    # 移除图片上的微信风格（data-local-path 等）
    body_content = re.sub(r'\s+data-local-path="[^"]*"', '', body_content)
    body_content = re.sub(r'\s+data-original-path="[^"]*"', '', body_content)

    # 输出干净的 HTML
    result = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>反向传播是什么？</title>
<style>{ZHIHU_CSS}
</style>
</head>
<body>
{body_content}
</body>
</html>"""

    with open(outpath, 'w', encoding='utf-8') as f:
        f.write(result)

    print(f"✅ 知乎风格 HTML 生成 → {outpath}")


if __name__ == '__main__':
    fp = sys.argv[1] if len(sys.argv) > 1 else None
    if not fp:
        print("用法: python3 scripts/zhihu-html-gen.py <baoyu-output.html> [output.html]")
        sys.exit(1)
    out = sys.argv[2] if len(sys.argv) > 2 else fp.replace('.html', '.zhihu.html')
    process_html(fp, out)
