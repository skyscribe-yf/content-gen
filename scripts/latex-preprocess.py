#!/usr/bin/env python3
"""LaTeX 预处理：把 $...$ 和 $$...$$ 替换为 CodeCogs 图片（微信兼容）"""

import re, sys, urllib.parse

CODECOGS = "https://latex.codecogs.com/png.latex"

def render_latex(formula, display=False):
    """返回 CodeCogs 图片 URL"""
    # 清理公式
    formula = formula.strip()
    # URL encode
    encoded = urllib.parse.quote(formula)
    bg = "white"  # 白底
    dpi = 200 if display else 150
    size = "\\huge " if display else ""
    return f"{CODECOGS}?\\{bg}&dpi={dpi}&{size}{encoded}"

def preprocess(filepath):
    with open(filepath, encoding="utf-8") as f:
        content = f.read()

    # 先处理 $$...$$（独立公式）
    def replace_display(m):
        formula = m.group(1)
        url = render_latex(formula, display=True)
        return f'\n\n<img src="{url}" style="max-width:100%;display:block;margin:15px auto"/>\n\n'

    content = re.sub(r'\$\$\s*(.*?)\s*\$\$', replace_display, content, flags=re.DOTALL)

    # 再处理 $...$（行内公式）
    def replace_inline(m):
        formula = m.group(1)
        url = render_latex(formula, display=False)
        return f'<img src="{url}" style="height:1.2em;vertical-align:middle;display:inline"/>'

    content = re.sub(r'\$\s*(.*?)\s*\$', replace_inline, content)

    return content

if __name__ == "__main__":
    filepath = sys.argv[1]
    result = preprocess(filepath)
    # 输出到 stdout
    print(result)
