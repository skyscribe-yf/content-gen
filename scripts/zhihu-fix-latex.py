#!/usr/bin/env python3
"""
zhihu-fix-latex.py — 精确修复 zhihu-formula.py 转换后的 LaTeX 公式

问题修复：
1. \partialX/\partialY → \frac{\partial X}{\partial Y}
2. ŷ → \hat{y}
3. \cdotx → \cdot x, \cdotb → \cdot b
4. 独立加粗公式行 → $$...$$
5. 文本中多余的 $ 修复
6. 表格中的希腊字母加 $
"""

import re
import sys


def fix_frac(content: str) -> str:
    """∂L/∂ŷ → \frac{\partial L}{\partial \hat{y}}"""
    # 匹配 \partial<单字符>/<单字符> 或 \partial<单字符>\/... 形式
    def frac_repl(m):
        num_var = m.group(1).strip()
        den_var = m.group(2).strip()
        return f'\\frac{{\\partial {num_var}}}{{\\partial {den_var}}}'
    
    content = re.sub(
        r'\\partial(\w[\w}]]?)\\s*/\\s*\\partial(\w[\w}]]?)',
        frac_repl,
        content
    )
    # 剩余的 \partial紧挨字符，分开
    content = re.sub(r'\\partial(\w)', r'\\partial \1', content)
    return content


def fix_subscripts(content: str) -> str:
    """修复下标变量名连在一起的问题"""
    # w\cdotx → w \cdot x
    content = re.sub(r'\\cdot(\w)', r'\\cdot \1', content)
    # 一般的 \command<无括号> 名词
    return content


def fix_hat(content: str) -> str:
    """ŷ → \hat{y}, ĝ → \hat{g}, ĉ → \hat{c}"""
    hat_map = {'ŷ': 'y', 'ĝ': 'g', 'ĉ': 'c', 'ẑ': 'z', 'ň': 'n'}
    for uni, ascii_base in hat_map.items():
        content = content.replace(uni, f'\\hat{{{ascii_base}}}')
    return content


def fix_table_cells(content: str) -> str:
    """表格行的公式项加 $ 包裹，如 | −1/ŷ | → | $-1/\hat{y}$ |"""
    lines = content.split('\n')
    result = []
    for line in lines:
        if line.strip().startswith('|') and '---' not in line:
            # 找到分隔的单元格
            cells = line.split('|')
            new_cells = []
            for cell in cells:
                stripped = cell.strip()
                # 含 LaTeX 命令但无 $ 的单元格
                if stripped and ('\\' in stripped or 'ŷ' in stripped or '→' in stripped or '·' in stripped or '−' in stripped):
                    if not stripped.startswith('$'):
                        # 检查是否需要包裹
                        stripped = f'${stripped}$'
                new_cells.append(stripped if stripped else '')
            # 重建表格行
            result.append('| ' + ' | '.join(new_cells) + ' |')
        else:
            result.append(line)
    return '\n'.join(result)


def fix_bold_display_formulas(content: str) -> str:
    """独立加粗行（行内只有公式）→ block math"""
    lines = content.split('\n')
    result = []
    for line in lines:
        stripped = line.strip()
        # 引用块中的加粗行
        if stripped.startswith('> **') and stripped.endswith('**'):
            formula = stripped[4:-2].strip()
            # 检查是否包含 block-level 命令
            if any(c in formula for c in ['\\frac', '\\sum', '\\partial', '\\rightarrow']):
                result.append(f'\n$$\n{formula}\n$$\n')
                continue
        result.append(line)
    return '\n'.join(result)


def fix_specific_cases(content: str) -> str:
    """特定修复"""
    # 行内增量符号
    content = content.replace('ΔL', '\\Delta L')
    content = content.replace('Δ', '\\Delta')
    
    # 修复 ẑ, ĉ 等 hat
    content = re.sub(r'ẑ', '\\hat{z}', content)
    content = re.sub(r'ĉ', '\\hat{c}', content)
    
    # 修复 \eta z 这种连写 
    content = content.replace('\\eta z', '\\eta \\cdot z')
    
    # 修复 around \rightarrow
    content = content.replace('\\rightarrow', '\\rightarrow')
    
    return content


def postprocess(filepath: str) -> str:
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

    body = fix_frac(body)
    body = fix_hat(body)
    body = fix_subscripts(body)
    body = fix_specific_cases(body)
    body = fix_table_cells(body)
    body = fix_bold_display_formulas(body)

    result = yaml + body
    outpath = filepath.replace('.zhihu.md', '.zhihu-clean.md')
    with open(outpath, 'w', encoding='utf-8') as f:
        f.write(result)

    print(f"✅ LaTeX 清理完成 → {outpath}")
    return outpath


if __name__ == '__main__':
    fp = sys.argv[1] if len(sys.argv) > 1 else None
    if not fp:
        print("用法: python3 scripts/zhihu-fix-latex.py <input.zhihu.md>")
        sys.exit(1)
    postprocess(fp)
