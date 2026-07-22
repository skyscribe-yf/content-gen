#!/usr/bin/env python3
"""
知乎公式预处理 — Unicode ↔ LaTeX 双向转换

功能：
  unicode-to-latex : 把 promote/zhihu-*.md 中的 Unicode 数学符号转回 LaTeX
  latex-to-unicode : 把 LaTeX 公式转成 Unicode（备用，供其他方向）
  check             : 扫描文件中的公式格式，报告混合情况

知乎编辑器支持 MathJax，可以直接渲染 $$...$$ LaTeX 公式。
因此知乎版内容不需要 Unicode 转换，反而需要确保公式是 LaTeX 格式。

用法：
  python3 scripts/zhihu-formula.py <input.md> --direction unicode-to-latex
  python3 scripts/zhihu-formula.py <input.md> --direction latex-to-unicode
  python3 scripts/zhihu-formula.py <input.md> --check
"""

import re
import sys

# ── Unicode → LaTeX 映射 ──

# 希腊字母（Unicode → LaTeX）
GREEK_UNICODE_TO_LATEX = {
    'α': r'\alpha', 'β': r'\beta', 'γ': r'\gamma', 'δ': r'\delta',
    'ε': r'\epsilon', 'ζ': r'\zeta', 'η': r'\eta', 'θ': r'\theta',
    'ι': r'\iota', 'κ': r'\kappa', 'λ': r'\lambda', 'μ': r'\mu',
    'ν': r'\nu', 'ξ': r'\xi', 'π': r'\pi',
    'ρ': r'\rho', 'σ': r'\sigma', 'τ': r'\tau', 'υ': r'\upsilon',
    'φ': r'\phi', 'χ': r'\chi', 'ψ': r'\psi', 'ω': r'\omega',
    'Γ': r'\Gamma', 'Δ': r'\Delta', 'Θ': r'\Theta', 'Λ': r'\Lambda',
    'Ξ': r'\Xi', 'Π': r'\Pi', 'Σ': r'\Sigma', 'Φ': r'\Phi',
    'Ψ': r'\Psi', 'Ω': r'\Omega',
    '∇': r'\nabla',
    'ℓ': r'\ell',
}

# 上标 Unicode → LaTeX
SUPERSCRIPT_MAP = {
    '⁰': '^{0}', '¹': '^{1}', '²': '^{2}', '³': '^{3}', '⁴': '^{4}',
    '⁵': '^{5}', '⁶': '^{6}', '⁷': '^{7}', '⁸': '^{8}', '⁹': '^{9}',
    'ⁿ': '^{n}', 'ⁱ': '^{i}', 'ʲ': '^{j}', 'ᵏ': '^{k}', 'ᵗ': '^{t}',
    'ˣ': '^{x}', 'ʸ': '^{y}', 'ᶻ': '^{z}',
    '⁽': '^{(}', '⁾': '^{)}',
    '⁺': '^{+}', '⁻': '^{-}',
}

# 下标 Unicode → LaTeX
SUBSCRIPT_MAP = {
    '₀': '_{0}', '₁': '_{1}', '₂': '_{2}', '₃': '_{3}', '₄': '_{4}',
    '₅': '_{5}', '₆': '_{6}', '₇': '_{7}', '₈': '_{8}', '₉': '_{9}',
    'ₜ': '_{t}', 'ₙ': '_{n}', 'ᵢ': '_{i}', 'ⱼ': '_{j}', 'ₖ': '_{k}',
    'ₗ': '_{l}', 'ₛ': '_{s}', 'ᵣ': '_{r}', 'ₓ': '_{x}', 'ᵧ': '_{y}',
    '₍': '_{(}', '₎': '_{)}',
    '₊': '_{+}', '₋': '_{-}',
}

# 运算符 Unicode →_LATEX
OPS_UNICODE_TO_LATEX = {
    '·': r'\cdot', '×': r'\times', '÷': r'\div',
    '≤': r'\leq', '≥': r'\geq', '≠': r'\neq', '≈': r'\approx',
    '∞': r'\infty', '∂': r'\partial',
    '→': r'\rightarrow', '⇒': r'\Rightarrow',
    '←': r'\leftarrow', '⇐': r'\Leftarrow',
    '↔': r'\leftrightarrow',
    '∑': r'\sum', '∏': r'\prod', '∫': r'\int',
    '√': r'\sqrt', '∛': r'\sqrt[3]',
    '⋮': r'\vdots', '⋯': r'\cdots', '…': r'\ldots',
    '∀': r'\forall', '∃': r'\exists', '∈': r'\in', '∉': r'\notin',
    '⊂': r'\subset', '⊆': r'\subseteq',
    '∪': r'\cup', '∩': r'\cap',
    '∅': r'\emptyset',
    '∧': r'\land', '∨': r'\lor', '¬': r'\neg',
    '≡': r'\equiv',
    '±': r'\pm', '∓': r'\mp',
    '⟨': r'\langle', '⟩': r'\rangle',
    '∥': r'\parallel', '⊥': r'\perp',
    '≪': r'\ll', '≫': r'\gg',
    '—': r'{-}',
    '′': r"'",
    '″': r"''",
}

# 修饰符（帽子等）
HAT_MAP = {
    '̂': r'\hat',
    '̃': r'\tilde',
    '̄': r'\bar',
    '̇': r'\dot',
    '̈': r'\ddot',
    '⃗': r'\vec',
}


def _convert_superscripts(text: str) -> str:
    """把上标 Unicode 转为 LaTeX ^{...}"""
    result = text
    for char, replacement in SUPERSCRIPT_MAP.items():
        result = result.replace(char, replacement)
    return result


def _convert_subscripts(text: str) -> str:
    """把下标 Unicode 转为 LaTeX _{...}"""
    result = text
    for char, replacement in SUBSCRIPT_MAP.items():
        result = result.replace(char, replacement)
    return result


def _convert_greek(text: str) -> str:
    """把希腊字母 Unicode 转为 LaTeX 命令"""
    result = text
    for char, latex in GREEK_UNICODE_TO_LATEX.items():
        result = result.replace(char, latex)
    return result


def _convert_ops(text: str) -> str:
    """把运算符 Unicode 转为 LaTeX 命令"""
    result = text
    for char, latex in OPS_UNICODE_TO_LATEX.items():
        result = result.replace(char, latex)
    return result


def _remove_combining_hats(text: str) -> str:
    """处理组合用帽子符号 (如 m̂ₜ → \hat{m}_{t})"""
    # m̂ 形式: 基础字符 + U+0302 (COMBINING CIRCUMFLEX ACCENT)
    # 转为 \hat{m}
    result = text
    combining_map = {
        '\u0302': r'\hat',
        '\u0303': r'\tilde',
        '\u0304': r'\bar',
        '\u0307': r'\dot',
        '\u0308': r'\ddot',
        '\u20d7': r'\vec',
    }
    for combining_cmd, latex_cmd in combining_map.items():
        if combining_cmd in result:
            # 模式: X\u0302 → \hat{X}
            result = re.sub(
                r'([a-zA-Z])' + combining_cmd,
                latex_cmd + r'{\1}',
                result
            )
    return result


def unicode_to_latex(text: str) -> str:
    """把一行中出现的所有 Unicode 数学符号转回 LaTeX"""
    # 跳过已经是 LaTeX 的行（含有 $ 或 \command）
    if '$' in text or re.search(r'\\[a-zA-Z]+\{', text):
        return text
    
    # 跳过纯文本行
    has_math = any(
        ord(c) > 0x2000 for c in text
    ) or any(c in 'αβγδεζηθικλμνξπρστυφχψωΓΔΘΛΞΠΣΦΨΩ' for c in text)
    
    if not has_math:
        return text

    # 按顺序转换
    result = text
    result = _remove_combining_hats(result)
    result = _convert_superscripts(result)
    result = _convert_subscripts(result)
    result = _convert_greek(result)
    result = _convert_ops(result)
    
    return result


def preprocess_file(filepath: str, output_suffix: str = '.zhihu.md') -> str:
    """处理整个 markdown 文件"""
    with open(filepath, encoding='utf-8') as f:
        content = f.read()

    # 分离 YAML 头部
    yaml = ""
    body = content
    if content.startswith('---'):
        end = content.find('---', 3)
        if end != -1:
            yaml = content[:end + 3]
            body = content[end + 3:]

    # 按行转换
    lines = body.split('\n')
    converted = []
    for line in lines:
        converted.append(unicode_to_latex(line))

    result = yaml + '\n'.join(converted)
    outpath = filepath.replace('.md', output_suffix)
    with open(outpath, 'w', encoding='utf-8') as f:
        f.write(result)

    # 统计
    changed = sum(1 for a, b in zip(lines, converted) if a != b)
    print(f"✅ Unicode→LaTeX 转换完成: {changed} 行被转换 → {outpath}")
    return outpath


def check_formulas(filepath: str) -> dict:
    """扫描文件中公式的格式分布"""
    with open(filepath, encoding='utf-8') as f:
        content = f.read()

    stats = {
        'latex_display': len(re.findall(r'\$\$', content)) // 2,
        'latex_inline': len(re.findall(r'(?<!\$)\$(?!\$)', content)),
        'unicode_greek': len(re.findall(r'[α-ωΑ-Ω]', content)),
        'unicode_sub': len(re.findall(r'[₀-₉ₜₙᵢⱼₖₗₛᵣₓᵧ]+', content)),
        'unicode_sup': len(re.findall(r'[⁰-⁹ⁿⁱʲᵏᵗˣʸᶻ]+', content)),
        'unicode_ops': len(re.findall(r'[·×÷≤≥≠≈∞∂→⇒∑∏√⋮⋯…]', content)),
    }

    print(f"📊 {filepath} 公式统计:")
    print(f"    LaTeX 块级 formula:    {stats['latex_display']} 个")
    print(f"    LaTeX 行内 formula:    {stats['latex_inline']} 个")
    print(f"    Unicode 希腊字母:      {stats['unicode_greek']} 次")
    print(f"    Unicode 下标:          {stats['unicode_sub']} 次")
    print(f"    Unicode 上标:          {stats['unicode_sup']} 次")
    print(f"    Unicode 运算符:        {stats['unicode_ops']} 次")

    if stats['latex_display'] + stats['latex_inline'] > 0 and (
        stats['unicode_greek'] + stats['unicode_sub'] + stats['unicode_ops']
    ) > 0:
        print("  ⚠️  混合格式：部分 LaTeX + 部分 Unicode，需要统一")
    elif stats['latex_display'] + stats['latex_inline'] > 0:
        print("  ✅ 已统一为 LaTeX 格式")
    elif stats['unicode_greek'] + stats['unicode_sub'] + stats['unicode_ops'] > 0:
        print("  ⚠️  全 Unicode 格式，需转换为 LaTeX")
    else:
        print("  ℹ️  未检测到公式")

    return stats


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='知乎公式预处理工具')
    parser.add_argument('input', help='输入 markdown 文件路径')
    parser.add_argument(
        '--direction', '-d',
        choices=['unicode-to-latex', 'latex-to-unicode'],
        default='unicode-to-latex',
        help='转换方向 (默认: unicode-to-latex)'
    )
    parser.add_argument('--check', '-c', action='store_true',
                        help='扫描统计公式格式')
    args = parser.parse_args()

    if args.check:
        check_formulas(args.input)
    elif args.direction == 'unicode-to-latex':
        preprocess_file(args.input)
    elif args.direction == 'latex-to-unicode':
        print("❌ latex-to-unicode 暂不支持（知乎不需要 Unicode）")
        sys.exit(1)
