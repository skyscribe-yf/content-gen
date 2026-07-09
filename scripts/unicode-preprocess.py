#!/usr/bin/env python3
"""LaTeX → Unicode + 排版样式 预处理
把 $...$ 和 $$...$$ 转成微信原生支持的 Unicode 符号 + 内联样式 HTML
"""

import re, sys

# ── Unicode 映射 ──
GREEK = {
    r'\alpha': 'α', r'\beta': 'β', r'\gamma': 'γ', r'\delta': 'δ',
    r'\epsilon': 'ε', r'\varepsilon': 'ε', r'\zeta': 'ζ', r'\eta': 'η',
    r'\theta': 'θ', r'\iota': 'ι', r'\kappa': 'κ', r'\lambda': 'λ',
    r'\mu': 'μ', r'\nu': 'ν', r'\xi': 'ξ', r'\pi': 'π',
    r'\rho': 'ρ', r'\sigma': 'σ', r'\tau': 'τ', r'\upsilon': 'υ',
    r'\phi': 'φ', r'\chi': 'χ', r'\psi': 'ψ', r'\omega': 'ω',
    r'\Gamma': 'Γ', r'\Delta': 'Δ', r'\Theta': 'Θ', r'\Lambda': 'Λ',
    r'\Xi': 'Ξ', r'\Pi': 'Π', r'\Sigma': 'Σ', r'\Phi': 'Φ',
    r'\Psi': 'Ψ', r'\Omega': 'Ω',
    r'\nabla': '∇',
}

OPS = {
    r'\cdot': '·', r'\times': '×', r'\div': '÷',
    r'\leq': '≤', r'\geq': '≥', r'\neq': '≠', r'\approx': '≈',
    r'\infty': '∞', r'\partial': '∂',
    r'\rightarrow': '→', r'\Rightarrow': '⇒',
    r'\sum': 'Σ', r'\prod': '∏', r'\int': '∫',
    r'\sqrt': '√',
    r'\vdots': '⋮', r'\cdots': '⋯', r'\ldots': '…',
    r'\forall': '∀', r'\exists': '∃',
}

SUBSCRIPTS = str.maketrans('0123456789nijkltsr', '₀₁₂₃₄₅₆₇₈₉ₙᵢⱼₖₗₜₛᵣ')
SUPERSCRIPTS = str.maketrans('0123456789nijkt', '⁰¹²³⁴⁵⁶⁷⁸⁹ⁿⁱʲᵏᵗ')

def sub(s):
    """转下标"""
    return s.translate(SUBSCRIPTS)

def sup(s):
    """转上标"""
    return s.translate(SUPERSCRIPTS)

def convert_formula(latex, display=False):
    """把 LaTeX 公式转成 Unicode + HTML"""
    s = latex.strip()

    # 1. 替换 Greek 和运算符（长的先替换避免部分匹配）
    for cmd, sym in sorted(GREEK.items(), key=lambda x: -len(x[0])):
        s = s.replace(cmd, sym)
    for cmd, sym in sorted(OPS.items(), key=lambda x: -len(x[0])):
        s = s.replace(cmd, sym)

    # 2. \frac{A}{B} → A/B
    def frac_repl(m):
        num = convert_inner(m.group(1))
        den = convert_inner(m.group(2))
        return f"{num}/{den}"
    s = re.sub(r'\\frac\{([^}]*)\}\{([^}]*)\}', frac_repl, s)

    # 3. _{...} 下标
    def sub_repl(m):
        inner = m.group(1)
        return sub(inner)
    s = re.sub(r'_\{([^}]*)\}', sub_repl, s)
    # 单字符下标: _x
    s = re.sub(r'_([a-zA-Z0-9])', lambda m: sub(m.group(1)), s)

    # 4. ^{...} 上标
    def sup_repl(m):
        inner = m.group(1)
        return sup(inner)
    s = re.sub(r'\^\{([^}]*)\}', sup_repl, s)
    # 单字符上标: ^2
    s = re.sub(r'\^([a-zA-Z0-9])', lambda m: sup(m.group(1)), s)

    # 5. \text{...} → 普通文字
    s = re.sub(r'\\text\{([^}]*)\}', r'\1', s)
    s = re.sub(r'\\mathrm\{([^}]*)\}', r'\1', s)
    s = re.sub(r'\\mathbb\{([^}]*)\}', r'\1', s)
    s = re.sub(r'\\mathbf\{([^}]*)\}', r'\1', s)
    s = re.sub(r'\\operatorname\{([^}]*)\}', r'\1', s)

    # 6. \left \right 括号
    s = s.replace(r'\left(', '(').replace(r'\right)', ')')
    s = s.replace(r'\left[', '[').replace(r'\right]', ']')
    s = s.replace(r'\left\{', '{').replace(r'\right\}', '}')
    s = s.replace(r'\left|', '|').replace(r'\right|', '|')

    # 7. \begin{bmatrix} ... \end{bmatrix} → 用换行排列
    s = re.sub(r'\\begin\{bmatrix\}', '', s)
    s = re.sub(r'\\end\{bmatrix\}', '', s)
    s = re.sub(r'\\\\', '  ', s)  # 行分隔

    # 8. 清理残留命令
    s = re.sub(r'\\[a-zA-Z]+', '', s)  # 未识别的命令删除
    s = s.replace(r'\,', ' ')   # thin space
    s = s.replace(r'\;', ' ')   # medium space
    s = s.replace(r'\!', '')    # negative thin space
    s = s.replace(r'\\', '')    # 残留反斜杠
    s = s.replace('{', '').replace('}', '')  # 残留花括号

    # 9. 清理多余空格
    s = re.sub(r'\s+', ' ', s).strip()

    # 10. 包装成 HTML
    if display:
        return f'<p style="text-align:center;font-size:17px;font-weight:600;color:#1a1a2e;margin:1.2em 0;padding:12px;background:#f8f9ff;border-radius:6px">{s}</p>'
    else:
        return f'<span style="font-weight:600;color:#0F4C81">{s}</span>'

def convert_inner(s):
    """frac 内部用的简化转换"""
    for cmd, sym in sorted(GREEK.items(), key=lambda x: -len(x[0])):
        s = s.replace(cmd, sym)
    for cmd, sym in sorted(OPS.items(), key=lambda x: -len(x[0])):
        s = s.replace(cmd, sym)
    s = re.sub(r'_\{([^}]*)\}', lambda m: sub(m.group(1)), s)
    s = re.sub(r'_([a-zA-Z0-9])', lambda m: sub(m.group(1)), s)
    s = re.sub(r'\^\{([^}]*)\}', lambda m: sup(m.group(1)), s)
    s = re.sub(r'\^([a-zA-Z0-9])', lambda m: sup(m.group(1)), s)
    s = s.replace('{', '').replace('}', '')
    s = re.sub(r'\\[a-zA-Z]+', '', s)
    return s.strip()

def preprocess(filepath):
    with open(filepath, encoding="utf-8") as f:
        content = f.read()

    # 分离 YAML 头部
    yaml = ""
    body = content
    if content.startswith("---"):
        end = content.find("---", 3)
        if end != -1:
            yaml = content[:end + 3]
            body = content[end + 3:]

    # 先处理 $$...$$（独立公式）
    body = re.sub(
        r'\$\$\s*([\s\S]*?)\s*\$\$',
        lambda m: convert_formula(m.group(1), display=True),
        body,
    )

    # 再处理 $...$（行内公式）
    body = re.sub(
        r'\$\s*(.*?)\s*\$',
        lambda m: convert_formula(m.group(1), display=False),
        body,
    )

    return yaml + body


if __name__ == "__main__":
    filepath = sys.argv[1] if len(sys.argv) > 1 else None
    if not filepath:
        print("用法: python3 scripts/unicode-preprocess.py <input.md>")
        sys.exit(1)

    result = preprocess(filepath)
    outpath = filepath.replace(".md", ".unicode.md")
    with open(outpath, "w", encoding="utf-8") as f:
        f.write(result)

    # 统计
    count = result.count('color:#0F4C81') + result.count('color:#1a1a2e')
    print(f"✅ Unicode 渲染完成: {count} 处公式 → {outpath}")
