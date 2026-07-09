#!/usr/bin/env bun
/**
 * LaTeX → KaTeX HTML 预处理
 * 把 markdown 中的 $...$ 和 $$...$$ 替换为 KaTeX 渲染的 inline-styled HTML
 * 微信公众号支持内联 CSS，所以 KaTeX 输出可以直接显示
 */

import { readFileSync, writeFileSync } from "fs";
import katex from "katex";

// 读取 KaTeX CSS 并内联到文章头部
const KATEX_CSS = readFileSync(
  require.resolve("katex/dist/katex.min.css"),
  "utf-8"
);

function renderKatex(latex: string, displayMode: boolean): string {
  try {
    return katex.renderToString(latex.trim(), {
      displayMode,
      throwOnError: false,
      strict: false,
      trust: true,
    });
  } catch (e: any) {
    // 渲染失败时保留原文
    return displayMode
      ? `<p style="color:#c00;font-family:monospace;background:#fff3f3;padding:8px;border-radius:4px">${latex}</p>`
      : `<span style="color:#c00;font-family:monospace">${latex}</span>`;
  }
}

function preprocess(filepath: string): string {
  let content = readFileSync(filepath, "utf-8");

  // 分离 YAML 头部
  let yaml = "";
  let body = content;
  if (content.startsWith("---")) {
    const end = content.indexOf("---", 3);
    if (end !== -1) {
      yaml = content.substring(0, end + 3);
      body = content.substring(end + 3);
    }
  }

  // 先处理 $$...$$（独立公式块）
  body = body.replace(/\$\$\s*([\s\S]*?)\s*\$\$/g, (_match, formula: string) => {
    const html = renderKatex(formula, true);
    return `\n\n<div style="text-align:center;margin:1.2em 0;overflow-x:auto">${html}</div>\n\n`;
  });

  // 再处理 $...$（行内公式）
  body = body.replace(/\$\s*(.*?)\s*\$/g, (_match, formula: string) => {
    // 跳过表格分隔线等误匹配
    if (formula.includes("---") || formula.includes("|")) return _match;
    const html = renderKatex(formula, false);
    return html;
  });

  // 在 YAML 头部之后、正文之前插入 KaTeX CSS
  const katexStyleBlock = `\n<style>\n${KATEX_CSS}\n</style>\n`;

  return yaml + katexStyleBlock + body;
}

// ── CLI ──
const filepath = process.argv[2];
if (!filepath) {
  console.error("用法: bun scripts/katex-preprocess.ts <input.md>");
  process.exit(1);
}

const result = preprocess(filepath);

// 输出到同名文件 + .katex.md 后缀
const outPath = filepath.replace(/\.md$/, ".katex.md");
writeFileSync(outPath, result, "utf-8");

// 统计
const formulaCount = (result.match(/katex/g) || []).length;
console.log(`✅ KaTeX 渲染完成: ${formulaCount} 处公式 → ${outPath}`);
