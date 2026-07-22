#!/usr/bin/env python3
"""
知乎 Markdown 后处理
修复 zhihu-formula.py 的转换余留问题，然后：
  - bold 公式 → `$$...$$` (block)
  - 行内 ∂L/∂x 型分数 → `\frac{\partial L}{\partial x}`
  - 修复多余的 `$` （中文文本中的 `$...$`）
  - 修复 `\rightarrow` → `→` （行内文本中保留 Unicode 更紧凑）
  - 移除代码块中错误的公式替换
"""

import re
import sys


def fix_fractions(content: str) -> str:
    """修复 ∂X/∂Y 型分数（已被转为 \partialX/\partialY）→ \frac{\partial X}{\partial Y}"""
    # \partialX/\partialY → \frac{\partial X}{\partial Y}
    content = re.sub(
        r'\\partial\s*(\w)\\partial\s*(\w)',
        r'\\frac{\partial \1}{\partial \2}',
        content
    )
    # 处理带分隔的：\frac{\partial X}{\partial Y}...? No, we need \frac{\partial X}{...
    # 实际上是 \partialL/\partialw → 应该为 \frac{\partial L}{\partial w}
    # 上一步没处理好，重新来：
    # 如果还有 \partial 后紧跟单个字符 + /
    content = re.sub(
        r'\\partial(\w)/\\partial(\w)',
        r'\\frac{\partial \1}{\partial \2}',
        content
    )
    return content


def fix_bold_formulas(content: str) -> str:
    """加粗的独立公式行 → $$...$$ (block math)"""
    lines = content.split('\n')
    result = []
    for line in lines:
        stripped = line.strip()
        # 独立的加粗行，包含 \frac, \cdot, \sum 等特征，转为 block math
        if stripped.startswith('> **') and stripped.endswith('**'):
            formula_text = stripped[4:-2]  # 去掉 > ** 和 **
            # 已经有 $ 了就不重复
            if '$' not in formula_text and any(
                cmd in formula_text
                for cmd in ['\\frac', '\\cdot', '\\sum', '\\partial', '\\eta', '\\sigma', '\\delta', '\\alpha', '\\beta', '\\hat', '\\rightarrow', '\\times']
            ):
                result.append(f'\n$$\n{formula_text}\n$$\n')
                continue
        result.append(line)
    return '\n'.join(result)


def fix_inline_math_around_chinese(content: str) -> str:
    """修复中文前面错误出现的 $a$ 型数学"""
    # 模式：$单个latex命令$紧跟中文 → 该命令本身
    content = re.sub(r'\$\\(\w+)\$([\u4e00-\u9fff])', r'\1\2', content)
    return content


def remove_math_in_code_blocks(content: str) -> str:
    """移除代码块内的 $...$$ 标记（代码不渲染公式）"""
    lines = content.split('\n')
    result = []
    in_code = False
    for line in lines:
        if line.strip().startswith('```'):
            in_code = not in_code
            result.append(line)
            continue
        if in_code:
            # 移除行内 $
            line = re.sub(r'\$(?!\$)(.*?)\$(?!\$)', r'\1', line)
        result.append(line)
    return '\n'.join(result)


def fix_table_formulas(content: str) -> str:
    """表格中的单变量转为行内数学: ŷ → $\hat{y}$, ∂L/∂ŷ → $\frac{\partial L}{\partial \hat{y}}$"""
    lines = content.split('\n')
    result = []
    in_table = False
    for line in lines:
        if line.strip().startswith('|') and '---' in line:
            in_table = True
            result.append(line)
            continue
        if in_table:
            # 表格行: | xxx | yyy | → 对含希腊字母的单元格加 $
            pass
        result.append(line)
    return '\n'.join(result)


def fix_specific_formulas(content: str) -> str:
    """修复一些已知公式的格式"""
    fixes = [
        # ∂L/∂w 相关
        (r'\\frac\{\\partial L\}\{\\partial w\}', r'\\frac{\\partial L}{\\partial w}'),
        (r'\\frac\{\\partial L\}\{\\partial ŷ\}', r'\\frac{\\partial L}{\\partial \\hat{y}}'),
        (r'\\frac\{\\partial L\}\{\\partial \\hat\{y\}\}', r'\\frac{\\partial L}{\\partial \\hat{y}}'),
        (r'\\frac\{\\partial ĝ\}\{\\partial z\}', r'\\frac{\\partial \\hat{y}}{\\partial z}'),
        (r'\\frac\{\\partial ẑ\}\{\\partial w\}', r'\\frac{\\partial z}{\\partial w}'),
        # 普通格式修复
        (r'\\partialL', r'\\partial L'),
        (r'\\partialw', r'\\partial w'),
        (r'\\partialŷ', r'\\partial \\hat{y}'),
        (r'\\partialz', r'\\partial z'),
        (r'\\partialb', r'\\partial b'),
        (r'/\\partial', r'\\partial'),
        # 修复 \sigma
        (r'\\sigma(\w)', r'\\sigma(\1)'),
        # 行内单变量
        (r'→', r'\\rightarrow'),
        (r'(?<![\w\\])ŷ', r'\\hat{y}'),
    ]
    for pattern, replacement in fixes:
        content = re.sub(pattern, replacement, content)
    return content


def postprocess_file(filepath: str) -> str:
    with open(filepath, encoding='utf-8') as f:
        content = f.read()

    # 分离 YAML
    yaml = ""
    body = content
    if content.startswith('---'):
        end = content.find('---', 3)
        if end != -1:
            yaml = content[:end + 3]
            body = content[end + 3:]

    # 依次后处理
    body = fix_fractions(body)
    body = fix_specific_formulas(body)
    body = fix_inline_math_around_chinese(body)
    body = remove_math_in_code_blocks(body)
    body = fix_bold_formulas(body)

    result = yaml + body
    outpath = filepath.replace('.zhihu.md', '.zhihu-final.md')
    with open(outpath, 'w', encoding='utf-8') as f:
        f.write(result)

    print(f"✅ 后处理完成 → {outpath}")
    return outpath


if __name__ == '__main__':
    filepath = sys.argv[1] if len(sys.argv) > 1 else None
    if not filepath:
        print("用法: python3 scripts/zhihu-markdown-post.py <input.zhihu.md>")
        sys.exit(1)
    postprocess_file(filepath)
