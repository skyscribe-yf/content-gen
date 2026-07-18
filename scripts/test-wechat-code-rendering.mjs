import assert from "node:assert/strict";

import { renderMarkdownDocument } from "baoyu-md";
import { makeCodeBlocksWechatSafe } from "../.agents/skills/baoyu-post-to-wechat/scripts/wechat-code-blocks.ts";

const { html: renderedHtml } = await renderMarkdownDocument(
  "```python\nq1 = R @ q\nprint(q1.round(2))\n```\n",
  {
    isMacCodeBlock: false,
    theme: "grace",
  },
);
const html = makeCodeBlocksWechatSafe(renderedHtml);

assert.doesNotMatch(
  html,
  /mac-sign|<svg\b/i,
  "WeChat-safe code blocks must not contain a decorative SVG terminal header.",
);
assert.doesNotMatch(
  html,
  /display:\s*-webkit-box|white-space:\s*nowrap/i,
  "WeChat-safe code blocks must preserve their lines with a block layout.",
);
assert.match(html, /<pre\b[^>]*><code\b[^>]*>.*q1.*<\/code><\/pre>/s);
