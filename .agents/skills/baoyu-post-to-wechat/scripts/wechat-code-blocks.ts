/** Remove code-block markup and styles that WeChat's editor does not preserve. */
export function makeCodeBlocksWechatSafe(html: string): string {
  return html
    .replace(/<span class="mac-sign"[^>]*>[\s\S]*?<\/span>/gi, "")
    .replace(
      /(<code\b[^>]*class="[^"]*language-[^"]*"[^>]*style="[^"]*)display:\s*-webkit-box;/gi,
      "$1display: block;",
    )
    .replace(
      /(<code\b[^>]*class="[^"]*language-[^"]*"[^>]*style="[^"]*)white-space:\s*nowrap;/gi,
      "$1white-space: pre;",
    );
}
