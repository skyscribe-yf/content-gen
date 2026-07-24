import fs from "node:fs";
import path from "node:path";

const src = path.resolve(import.meta.dirname!, "node_modules/katex/dist/katex.min.css");
const outDir = path.resolve(import.meta.dirname!, ".");
const outFile = path.join(outDir, "katexCss.ts");

let css = fs.readFileSync(src, "utf-8");

// Strip @font-face blocks — we don't ship font files, system fonts suffice
css = css.replace(/@font-face\s*\{[^}]*\}/g, "");

// Escape for JS template literal
const escaped = css
  .replace(/\\/g, "\\\\")
  .replace(/`/g, "\\`")
  .replace(/\$/g, "\\$");

const content = `// Auto-generated from node_modules/katex/dist/katex.min.css
// Run \`bun generate-katex-css.ts\` to regenerate after upgrading katex.
// @font-face rules are stripped — system fonts are used instead.

const katexCss: string = \`${escaped}\`;
export default katexCss;
`;

fs.writeFileSync(outFile, content, "utf-8");
console.error(`[katex-css] Generated ${outFile} (${content.length} bytes)`);
