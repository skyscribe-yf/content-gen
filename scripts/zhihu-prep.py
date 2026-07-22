#!/usr/bin/env python3
"""
zhihu-prep.py — 从 weixin.md 直接生成知乎-ready markdown
一步完成全部转换：Unicode→LaTeX、加粗公式→$$、链接处理、引流调整
"""

import re
import sys


# ── 核心转换 ──

SUPERSCRIPT = str.maketrans('⁰¹²³⁴⁵⁶⁷⁸⁹ⁿⁱʲᵏᵗ', '0123456789nijk')
SUBSCRIPT = str.maketrans('₀₁₂₃₄₅₆₇₈₉ₜₙᵢⱼₖₗₛᵣ', '0123456789tnijkl sr')

GREEK = {
    'α': r'\alpha', 'β': r'\beta', 'γ': r'\gamma', 'δ': r'\delta',
    'ε': r'\epsilon', 'ζ': r'\zeta', 'η': r'\eta', 'θ': r'\theta',
    'ι': r'\iota', 'κ': r'\kappa', 'λ': r'\lambda', 'μ': r'\mu',
    'ν': r'\nu', 'ξ': r'\xi', 'π': r'\pi',
    'ρ': r'\rho', 'σ': r'\sigma', 'τ': r'\tau', 'υ': r'\upsilon',
    'φ': r'\phi', 'χ': r'\chi', 'ψ': r'\psi', 'ω': r'\omega',
    'Γ': r'\Gamma', 'Δ': r'\Delta', 'Θ': r'\Theta', 'Λ': r'\Lambda',
    'Ξ': r'\Xi', 'Π': r'\Pi', 'Σ': r'\Sigma', 'Φ': r'\Phi',
    'Ψ': r'\Psi', 'Ω': r'\Omega',
}

OPS = {
    '·': r'\cdot', '×': r'\times',
    '≤': r'\leq', '≥': r'\geq', '≠': r'\neq', '≈': r'\approx',
    '∞': r'\infty', '∂': r'\partial',
    '→': r'\rightarrow', '⇒': r'\Rightarrow',
    '∑': r'\sum', '∏': r'\prod', '∫': r'\int',
    '√': r'\sqrt', '⋯': r'\cdots', '…': r'\ldots',
    '−': '-',
    '⟨': r'\langle', '⟩': r'\rangle',
    '∥': r'\parallel',
    '′': "'",
}

HAT = {'ŷ': 'y', 'ĝ': 'g', 'ĉ': 'c', 'ẑ': 'z'}


def convert_math_fragment(text: str) -> str:
    """转换一段已知是公式的文本"""
    # 先处理帽子变量
    for uni, base in HAT.items():
        text = text.replace(uni, f'\\hat{{{base}}}')
    # 希腊字母
    for uni, latex in GREEK.items():
        text = text.replace(uni, f'\\{latex}')
    # 运算符
    for uni, latex in OPS.items():
        text = text.replace(uni, latex)
    # 上标
    result = ''
    i = 0
    while i < len(text):
        c = text[i]
        if c in SUPERSCRIPT:
            result += '^{' + chr(ord(c) - 0x2000 + ord('0')) + '}'  # approximate
        else:
            result += c
        i += 1
    return result


def process_file(inpath: str, outpath: str):
    with open(inpath, encoding='utf-8') as f:
        content = f.read()

    # 分离 frontmatter
    yaml = ''
    body = content
    if content.startswith('---'):
        end = content.find('---', 3)
        if end >= 0:
            yaml = content[:end + 3]
            body = content[end + 3:]

    # 处理 frontmatter 中的链接
    wechat_url = 'https://mp.weixin.qq.com/s/oYj_qpwF4tZG84ImOn977g'
    zhihu_url_placeholder = '（待发布）'
    yaml = yaml.replace(wechat_url, zhihu_url_placeholder)

    # 按行处理 body
    lines = body.split('\n')
    out_lines = []
    in_code = False
    in_table = False

    for line in lines:
        stripped = line.strip()

        # 代码块
        if stripped.startswith('```'):
            in_code = not in_code
            out_lines.append(line)
            continue
        if in_code:
            out_lines.append(line)
            continue

        # 表格分隔
        if stripped.startswith('|') and '---' in stripped:
            in_table = True
            out_lines.append(line)
            continue
        if in_table and stripped.startswith('|'):
            out_lines.append(fix_table_row(line))
            continue
        else:
            in_table = False

        # 引用块中的加粗公式行
        if stripped.startswith('> **') and stripped.endswith('**'):
            formula = stripped[4:-2].strip()
            if is_formula(formula):
                out_lines.append('')
                out_lines.append(f'$$')
                out_lines.append(convert_full_formula(formula))
                out_lines.append(f'$$')
                out_lines.append('')
                continue

        # 标题行（含 Unicode 数学）
        if stripped.startswith('#'):
            out_lines.append(fix_heading(line))
            continue

        # 普通行（含行内公式）
        out_lines.append(fix_inline_text(line))

    result = yaml + '\n'.join(out_lines)

    # 后处理：修复链接和引流
    result = fix_links_and_cta(result)

    with open(outpath, 'w', encoding='utf-8') as f:
        f.write(result)
    print(f"✅ → {outpath}")


def is_formula(text: str) -> bool:
    """判断一行是否是公式（含运算符/希腊字母/∂/→ 等）"""
    formula_chars = set('∂→⇒∑∏√·×≤≥≠≈∞ψως∂→←↑↓↔↕∝∠∫∬∭∮')
    latex_commands = ['\\rightarrow', '\\cdot', '\\frac', '\\sum', '\\sigma', '\\hat', '\\partial', '\\eta', '\\alpha', '\\beta', '\\delta']
    if any(cmd in text for cmd in latex_commands):
        return True
    count = sum(1 for c in text if c in formula_chars or c in SUPERSCRIPT.values() or c in SUBSCRIPT.values())
    return count >= 2


def convert_full_formula(text: str) -> str:
    """转换完整公式行"""
    result = text
    # 帽子
    for uni, base in HAT.items():
        result = result.replace(uni, f'\\hat{{{base}}}')
    # 希腊字母（长的先替换）
    for uni, latex in sorted(GREEK.items(), key=lambda x: -len(x[0])):
        result = result.replace(uni, latex)
    # 运算符
    for uni, latex in OPS.items():
        result = result.replace(uni, latex)
    return result


def fix_inline_text(line: str) -> str:
    """修复行内文本中的公式部分"""
    result = line
    # 修复引用链接中的微信 URL
    result = result.replace(
        'https://mp.weixin.qq.com/s/V6mGvCVFpTvmC51pNtxiTw',
        '（待发布）'
    )
    result = result.replace(
        'https://mp.weixin.qq.com/s/zIWqYqYVzEaF1e8P6fcTfw',
        '（待发布）'
    )
    result = result.replace(
        'https://mp.weixin.qq.com/s/oYj_qpwF4tZG84ImOn977g',
        '（待发布）'
    )
    # 修复普通行中像偏导分数：∂L/∂w 等
    result = re.sub(r'∂(\w+)/∂(\w+)', r'\\frac{\partial \1}{\partial \2}', result)

    # 行内加法公式：找到已知模式
    # 行尾的 "链式法则说：**把每一步的偏导数乘起来**" 这种不用动
    # 行内的 "ŷ = σ(w·x + b)" 模式转换
    return result


def fix_table_row(line: str) -> str:
    # 表格行中的特殊字符单独处理
    result = line
    # → 在表格中保留为文字更紧凑
    result = result.replace('→', '\\rightarrow')
    # ∂ 相关不动
    return result


def fix_heading(line: str) -> str:
    """修复标题中的 Unicode"""
    result = line
    for uni, latex in GREEK.items():
        if uni in result:
            result = result.replace(uni, f'${latex}$')
    return result


def fix_links_and_cta(content: str) -> str:
    """修复链接和引流"""
    # 系列导航占位
    return content


if __name__ == '__main__':
    fp = sys.argv[1] if len(sys.argv) > 1 else None
    if not fp:
        print("用法: python3 scripts/zhihu-prep.py <input.md> [output.md]")
        sys.exit(1)
    out = sys.argv[2] if len(sys.argv) > 2 else fp.replace('.md', '.zhihu.md')
    process_file(fp, out)
