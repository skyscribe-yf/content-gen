import katex from "katex";
import katexCss from "./katexCss";

// --- Types ------------------------------------------------------------

export interface MathSnippet {
  id: string;
  tex: string;
  displayMode: boolean;
}

interface CssRule {
  selector: string;
  parts: string[];        // e.g. ".katex .mord" → [".katex", ".mord"]
  styles: Record<string, string>;
}

// --- Step 1: extract LaTeX from markdown ------------------------------

let idCounter = 0;
function nextId(): string { return `__KATEX_${idCounter++}__`; }

const BLOCK_RX = /\$\$[ \t]*\n?([\s\S]+?)\n?\$\$/g;
const INLINE_RX = /\$(?!\$)(.+?)\$(?!\$)/g;

/** Extract all $...$ and $$...$$ formulas, replace with placeholders. */
export function extractMath(markdown: string): {
  markdown: string;
  snippets: MathSnippet[];
} {
  idCounter = 0;
  const snippets: MathSnippet[] = [];

  // Extract display math first ($$...$$) to avoid conflict with inline
  let result = markdown.replace(BLOCK_RX, (_full: string, tex: string) => {
    const id = nextId();
    snippets.push({ id, tex: tex.trim(), displayMode: true });
    return `\n\n<div data-katex="${id}"></div>\n\n`;
  });

  // Then inline math ($...$)
  result = result.replace(INLINE_RX, (_full: string, tex: string) => {
    const id = nextId();
    snippets.push({ id, tex: tex.trim(), displayMode: false });
    return `<span data-katex="${id}"></span>`;
  });

  return { markdown: result, snippets };
}

// --- Step 2: inject KaTeX into rendered HTML --------------------------

/**
 * Replace data-katex placeholders inside rendered HTML with
 * KaTeX output whose classes have been inlined as style attributes.
 */
export function injectMath(html: string, snippets: MathSnippet[]): string {
  if (snippets.length === 0) return html;

  const rules = parseCss(String(katexCss));

  let result = html;

  for (const { id, tex, displayMode } of snippets) {
    const placeholderRx = new RegExp(
      `<${displayMode ? "div" : "span"}\\s+data-katex="${escapeRx(id)}"[^>]*><\\/${displayMode ? "div" : "span"}>`,
      "g",
    );

    try {
      const rendered = katex.renderToString(tex, {
        throwOnError: false,
        displayMode,
        strict: false,
        output: "html",
        trust: false,
      });
      const cleaned = removeMathMl(rendered);
      const inlined = inlineStylesRegex(cleaned, rules);
      const wrapper = displayMode
        ? `<section style="text-align:center;margin:1em 0;">${inlined}</section>`
        : inlined;
      result = result.replace(placeholderRx, wrapper);
    } catch {
      const fallback = displayMode
        ? `<pre style="background:#f5f5f5;padding:12px;border-radius:6px;overflow-x:auto;text-align:center;font-style:italic;">${escapeHtml(tex)}</pre>`
        : `<code style="background:#f5f5f5;padding:2px 5px;border-radius:3px;font-style:italic;">${escapeHtml(tex)}</code>`;
      result = result.replace(placeholderRx, fallback);
    }
  }

  return result;
}

// --- CSS inlining -----------------------------------------------------

/** Remove .katex-mathml — duplicates formula text, hidden only by CSS. */
function removeMathMl(html: string): string {
  return html.replace(/<span class="katex-mathml"[^>]*>[\s\S]*?<\/span>/g, "");
}

/** Parse KaTeX CSS into an array of simple rules. */
function parseCss(cssText: string): CssRule[] {
  const rules: CssRule[] = [];
  const cleaned = cssText.replace(/\/\*[\s\S]*?\*\//g, "");
  const blocks = cleaned.split("}");

  for (const block of blocks) {
    const braceIdx = block.indexOf("{");
    if (braceIdx === -1) continue;
    const selectorText = block.slice(0, braceIdx).trim();
    const declarationsText = block.slice(braceIdx + 1);

    const selectors = selectorText.split(",").map(s => s.trim()).filter(Boolean);

    const styles: Record<string, string> = {};
    for (const prop of declarationsText.split(";")) {
      const colonIdx = prop.indexOf(":");
      if (colonIdx === -1) continue;
      const key = prop.slice(0, colonIdx).trim();
      const value = prop.slice(colonIdx + 1).trim();
      if (key && value) styles[key] = value;
    }
    if (Object.keys(styles).length === 0) continue;

    for (const sel of selectors) {
      // Split by whitespace for descendant selectors
      const parts = sel.split(/\s+/).filter(Boolean);
      rules.push({ selector: sel, parts, styles: { ...styles } });
    }
  }

  // Sort: single-class rules first, descendant later (so more specific overrides)
  rules.sort((a, b) => a.parts.length - b.parts.length);
  return rules;
}

/** Simple selector matching: class-only, handles descendant combinator. */
function selectorMatches(el: ElementInfo, rule: CssRule, ancestors: ElementInfo[]): boolean {
  const parts = rule.parts;
  if (parts.length === 0) return false;

  // Last part must match the element itself
  if (!elementMatchesParts(el, parts[parts.length - 1]!)) return false;

  // Earlier parts match ancestors (innermost → outermost reversal)
  if (parts.length > 1) {
    let ancestorIdx = ancestors.length - 1;
    for (let i = parts.length - 2; i >= 0; i--) {
      while (ancestorIdx >= 0 && !elementMatchesParts(ancestors[ancestorIdx]!, parts[i]!)) {
        ancestorIdx--;
      }
      if (ancestorIdx < 0) return false;
      ancestorIdx--;
    }
  }

  return true;
}

function elementMatchesParts(el: ElementInfo, part: string): boolean {
  // part is like ".katex-display" or ".mord.mathdefault"
  const classes = part.split(".").filter(Boolean);
  return classes.every(c => el.classes.has(c));
}

interface ElementInfo {
  tag: string;
  classes: Set<string>;
}

/** Inline CSS styles into each element that matches a parsed rule. */
function inlineStylesRegex(html: string, rules: CssRule[]): string {
  // Collect all elements with their classes, track ancestry
  const elementRx = /<(\w+)([^>]*)>/g;
  const elements: { match: string; tag: string; attrs: string; info: ElementInfo; start: number; end: number }[] = [];
  let m: RegExpExecArray | null;
  while ((m = elementRx.exec(html)) !== null) {
    const tag = m[1]!;
    const attrs = m[2]!;
    const classM = attrs.match(/class="([^"]*)"/);
    const classes = new Set(classM ? classM[1]!.split(/\s+/) : []);
    elements.push({ match: m[0], tag, attrs, info: { tag, classes }, start: m.index, end: m.index + m[0].length });
  }

  // For each element, find matching CSS rules
  const ancestors: { info: ElementInfo; start: number }[] = [];
  const replacements: { start: number; end: number; replacement: string }[] = [];

  for (const el of elements) {
    const inlineStyles: Record<string, string> = {};
    for (const rule of rules) {
      if (selectorMatches(el.info, rule, ancestors.map(a => a.info))) {
        Object.assign(inlineStyles, rule.styles);
      }
    }

    if (Object.keys(inlineStyles).length > 0) {
      const styleStr = Object.entries(inlineStyles)
        .map(([k, v]) => `${k}:${v}`)
        .join(";");

      // Remove class attribute, add/update style attribute
      let newAttrs = el.attrs.replace(/class="[^"]*"/, "").trim();
      const existingStyle = newAttrs.match(/style="([^"]*)"/);
      if (existingStyle) {
        newAttrs = newAttrs.replace(/style="[^"]*"/, `style="${styleStr};${existingStyle[1]}"`);
      } else {
        newAttrs += ` style="${styleStr}"`;
      }
      const replacement = `<${el.tag}${newAttrs ? " " + newAttrs : ""}>`;
      replacements.push({ start: el.start, end: el.end, replacement });
    }

    // Track open/close for ancestry
    if (!el.attrs.endsWith("/")) {
      // Not self-closing — push onto ancestor stack
      // We track by looking at the raw text for the closing tag later
      ancestors.push({ info: el.info, start: el.start });
    }
  }

  // Apply replacements in reverse order
  replacements.sort((a, b) => b.start - a.start);
  let result = html;
  for (const r of replacements) {
    result = result.slice(0, r.start) + r.replacement + result.slice(r.end);
  }

  // Remove class attributes that we didn't inline (clean slate)
  result = result.replace(/\s+class="[^"]*"/g, "");

  return result;
}

// --- Helpers ----------------------------------------------------------

function escapeRx(s: string): string {
  return s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function escapeHtml(s: string): string {
  return s
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}
