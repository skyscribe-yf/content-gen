import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import process from "node:process";

import {
  cleanSummaryText,
  extractSummaryFromBody,
  extractTitleFromMarkdown,
  parseFrontmatter,
  preprocessMermaidInMarkdown,
  replaceMarkdownImagesWithPlaceholders,
  resolveContentImages,
  serializeFrontmatter,
  stripWrappingQuotes,
} from "baoyu-md";
import { closeRenderer, renderMermaidToPng } from "baoyu-chrome-cdp/mermaid";
import { execFile } from "node:child_process";
import { normalizeWechatLists } from "./wechat-list-safety.ts";
import { loadWechatExtendConfig } from "./wechat-extend-config.ts";

interface ImageInfo {
  placeholder: string;
  localPath: string;
  originalPath: string;
  alt?: string;
}

/**
 * mdnice 代码主题给 <code class="hljs"> 设 display: -webkit-box（旧式 flex），
 * 微信 webview 中会把代码块所有行压成一行。换成 block + white-space: pre 恢复换行。
 */
function normalizeWechatCodeBlocks(html: string): string {
  return html
    // -webkit-box（旧式 flex）在微信 webview 里会把代码块所有行压成一行；
    // 换成 block 后必须补回 pre-wrap，否则 HTML 会把代码缩进当作普通空白折叠掉。
    .replace(/display:\s*-webkit-box/g, "display: block; white-space: pre-wrap; word-break: break-all")
    // 代码块不横向滚动：手机上滚不动，长行会被直接吞掉。改成自动换行。
    .replace(/overflow-x:\s*auto/g, "overflow-x: visible")
    .replace(/white-space:\s*pre(?!-wrap)/g, "white-space: pre-wrap; word-break: break-all")
    // 代码字号 12px 在手机上偏小
    .replace(/font-size:\s*12px/g, "font-size: 13px");
}

/**
 * 紧凑排版（2026-09-18 作者要求）：mdnice scienceBlue 主题在正文外层 section
 * 加了 `padding: 0 10px`，段落又各带 `margin: 10px 10px` 左右外边距——手机上
 * 两侧合计约 20px 留白，正文偏窄（实测 390px 视口：正文区 374px，文字仅 334px）。
 * 这里把主题自带的左右留白收掉，正文/图片铺满内容区；上下节奏（段落间距、
 * 标题上间距）保持不动。
 */
function compactWechatLayout(html: string): string {
  return html
    // 外层容器：去掉左右 10px 内边距
    .replace(/(<section id="nice"[^>]*style="[^"]*?)padding:\s*0 10px/, "$1padding: 0")
    // 段落与列表外层：左右 10px 外边距归零
    .replace(/margin:\s*10px 10px/g, "margin: 10px 0")
    // h2：右边距归零（左边框保留）
    .replace(/margin:\s*20px 10px 0px 0px/g, "margin: 20px 0 0 0");
}

/**
 * 手机微信可读性（2026-10-09，Pi Durable 篇作者反馈）：
 *  1) 正文段落被 mdnice 压在 15px（容器是 16px），手机上偏小 → 抬到 16px；
 *  2) 段落上下间距 10px、行高 1.75 → 14px / 1.85，段与段之间更喘得过气；
 *  3) `ol/ul` 硬编码 `padding-left: 25px`，而 `li` 是 display:block、序号本身是
 *     文字——参考文献比正文多缩进 25px，看着就是「内容与屏幕左侧有一段空白」
 *     → 归零，与正文左边缘对齐；
 *  4) `li` 没有行间距，密集列表贴成一块 → 补 4px。
 */
function relaxWechatReadability(html: string): string {
  return html
    .replace(
      /(<p\s[^>]*style="[^"]*?)font-size:\s*15px/g,
      "$1font-size: 16px",
    )
    .replace(
      /(<p\s[^>]*style="[^"]*?)line-height:\s*1\.75/g,
      "$1line-height: 1.85",
    )
    .replace(
      /(<p\s[^>]*style="[^"]*?)margin:\s*10px 0/g,
      "$1margin: 14px 0",
    )
    .replace(/(<(?:ol|ul)[^>]*style="[^"]*?)padding-left:\s*25px/g, "$1padding-left: 0")
    .replace(
      /(<li\s[^>]*style="[^"]*?)display:\s*block/g,
      "$1display: block; margin: 4px 0",
    );
}

interface ParsedResult {
  title: string;
  author: string;
  summary: string;
  htmlPath: string;
  contentImages: ImageInfo[];
}

export async function convertMarkdown(
  markdownPath: string,
  options?: { title?: string; theme?: string; color?: string; citeStatus?: boolean },
): Promise<ParsedResult> {
  const baseDir = path.dirname(markdownPath);
  const content = fs.readFileSync(markdownPath, "utf-8");
  const citeStatus = options?.citeStatus ?? true;

  const { frontmatter, body } = parseFrontmatter(content);

  let title = stripWrappingQuotes(options?.title ?? "")
    || stripWrappingQuotes(frontmatter.title ?? "")
    || extractTitleFromMarkdown(body);
  if (!title) {
    title = path.basename(markdownPath, path.extname(markdownPath));
  }

  const author = stripWrappingQuotes(frontmatter.author ?? "");
  const frontmatterSummary = stripWrappingQuotes(frontmatter.description ?? "")
    || stripWrappingQuotes(frontmatter.summary ?? "");
  let summary = cleanSummaryText(frontmatterSummary);
  if (!summary) {
    summary = extractSummaryFromBody(body, 120);
  }

  const { markdown: mermaidProcessedBody, images: mermaidImages } =
    await preprocessMermaidInMarkdown(body, {
      baseDir,
      renderFn: renderMermaidToPng,
      onError: (error, block) => {
        const message = error instanceof Error ? error.message : String(error);
        console.error(
          `[md-to-wechat] mermaid render failed (${block.code.slice(0, 40).replace(/\s+/g, " ")}…): ${message}`,
        );
      },
    });

  if (mermaidImages.length > 0) {
    const fresh = mermaidImages.filter((image) => !image.cached).length;
    console.error(
      `[md-to-wechat] mermaid: ${mermaidImages.length} block(s), ${fresh} rendered, ${mermaidImages.length - fresh} cached`,
    );
  }

  const { images, markdown: rewrittenBody } = replaceMarkdownImagesWithPlaceholders(
    mermaidProcessedBody,
    "WECHATIMGPH_",
  );
  // mdnice doesn't understand YAML frontmatter — pass body only
  const rewrittenMarkdown = rewrittenBody;

  const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), "wechat-article-images-"));
  const htmlPath = path.join(tempDir, "temp-article.html");

  // Map baoyu-md theme names to mdnice theme names
  const mdniceThemeMap: Record<string, string> = {
    grace: "scienceBlue",
    simple: "simple",
    modern: "geekBlack",
    default: "normal",
  };
  const mdniceTheme = mdniceThemeMap[options?.theme ?? "default"] ?? "scienceBlue";

  console.error(
    `[md-to-wechat] Rendering markdown with mdnice theme: ${mdniceTheme}`,
  );

  const renderedHtml = await renderWithMdnice(rewrittenMarkdown, mdniceTheme, tempDir);
  const html = relaxWechatReadability(
    compactWechatLayout(normalizeWechatCodeBlocks(await normalizeWechatLists(renderedHtml))),
  );

  fs.writeFileSync(htmlPath, html, "utf-8");

  const contentImages = await resolveContentImages(images, baseDir, tempDir, "md-to-wechat");

  return {
    title,
    author,
    summary,
    htmlPath,
    contentImages,
  };
}

async function renderWithMdnice(
  markdown: string,
  theme: string,
  tempDir: string,
): Promise<string> {
  // Write markdown to a temp file (mdnice reads from file)
  const mdPath = path.join(tempDir, "input.md");
  fs.writeFileSync(mdPath, markdown, "utf-8");

  const scriptPath = path.resolve(
    __dirname,
    "../../../../scripts/mdnice-render.py",
  );
  const venvPython = path.resolve(
    __dirname,
    "../../../../.venv-mdnice/bin/python",
  );

  const htmlOutPath = path.join(tempDir, "mdnice-output.html");

  return new Promise<string>((resolve, reject) => {
    execFile(
      venvPython,
      [scriptPath, mdPath, "--theme", theme, "--output", htmlOutPath],
      { timeout: 120_000, maxBuffer: 50 * 1024 * 1024 },
      (error, stdout, stderr) => {
        if (error) {
          console.error(`[md-to-wechat] mdnice stderr:`, stderr);
          reject(new Error(`mdnice render failed: ${error.message}`));
          return;
        }
        if (stderr) {
          // mdnice prints progress to stderr, log it
          console.error(stderr);
        }
        const html = fs.readFileSync(htmlOutPath, "utf-8");
        resolve(html);
      },
    );
  });
}

function printUsage(): never {
  console.log(`Convert Markdown to WeChat-ready HTML with image placeholders

Usage:
  npx -y bun md-to-wechat.ts <markdown_file> [options]

Options:
  --title <title>     Override title
  --theme <name>      Theme name (default, grace, simple, modern)
  --color <name|hex>  Primary color (blue, green, vermilion, etc. or hex)
  --no-cite           Disable bottom citations for ordinary external links
  --help              Show this help

Output JSON format:
{
  "title": "Article Title",
  "htmlPath": "/tmp/wechat-article-images/temp-article.html",
  "contentImages": [
    {
      "placeholder": "WECHATIMGPH_1",
      "localPath": "/tmp/wechat-image/img.png",
      "originalPath": "imgs/image.png"
    }
  ]
}

Example:
  npx -y bun md-to-wechat.ts article.md
  npx -y bun md-to-wechat.ts article.md --theme grace
  npx -y bun md-to-wechat.ts article.md --theme modern --color blue
  npx -y bun md-to-wechat.ts article.md --no-cite
`);
  process.exit(0);
}

async function main(): Promise<void> {
  const args = process.argv.slice(2);
  if (args.length === 0 || args.includes("--help") || args.includes("-h")) {
    printUsage();
  }

  let markdownPath: string | undefined;
  let title: string | undefined;
  let theme: string | undefined;
  let color: string | undefined;
  let citeStatus = true;

  for (let i = 0; i < args.length; i++) {
    const arg = args[i]!;
    if (arg === "--title" && args[i + 1]) {
      title = args[++i];
    } else if (arg === "--theme" && args[i + 1]) {
      theme = args[++i];
    } else if (arg === "--color" && args[i + 1]) {
      color = args[++i];
    } else if (arg === "--cite") {
      citeStatus = true;
    } else if (arg === "--no-cite") {
      citeStatus = false;
    } else if (!arg.startsWith("-")) {
      markdownPath = arg;
    }
  }

  if (!markdownPath) {
    console.error("Error: Markdown file path is required");
    process.exit(1);
  }

  if (!fs.existsSync(markdownPath)) {
    console.error(`Error: File not found: ${markdownPath}`);
    process.exit(1);
  }

  // 读取 EXTEND.md 的默认主题/配色——CLI 未显式指定时回退到这里，
  // 否则发布管线会一直用 mdnice "normal" 主题，丢掉 grace/scienceBlue 风格。
  if (!theme || !color) {
    const ext = loadWechatExtendConfig();
    if (!theme && ext.default_theme) theme = ext.default_theme;
    if (!color && ext.default_color) color = ext.default_color;
  }

  const result = await convertMarkdown(markdownPath, { title, theme, color, citeStatus });
  console.log(JSON.stringify(result, null, 2));
}

try {
  await main();
} catch (error) {
  console.error(`Error: ${error instanceof Error ? error.message : String(error)}`);
  process.exitCode = 1;
} finally {
  await closeRenderer();
}
