/**
 * Normalize mdnice lists for the WeChat article editor.
 *
 * WeChat may rebuild native list markers while sanitizing article HTML. With
 * mdnice's `<li><section>...</section></li>` output that can leave an empty
 * first list item. Put the marker in the item content and disable native
 * markers so the editor no longer has to reconstruct the list numbering.
 */
export async function normalizeWechatLists(html: string): Promise<string> {
  // Remove empty items before numbering so an ordered list always starts at
  // the first visible item. mdnice emits empty <li> or empty <section> items
  // for some list edge cases.
  const withoutEmptyItems = html.replace(
    /<li\b[^>]*>(?:\s|<(?:section|p|div)\b[^>]*>\s*<\/(?:section|p|div)>)*<\/li>/gi,
    "",
  );

  const listStack: ListState[] = [];
  const rewriter = new HTMLRewriter()
    .on("ul", {
      element(element) {
        listStack.push({ ordered: false, next: 1 });
        element.setAttribute(
          "style",
          setStyle(element.getAttribute("style"), ["list-style", "list-style-type"], LIST_STYLE),
        );
        element.onEndTag(() => {
          listStack.pop();
        });
      },
    })
    .on("ol", {
      element(element) {
        const parsedStart = Number.parseInt(element.getAttribute("start") ?? "1", 10);
        listStack.push({
          ordered: true,
          next: Number.isFinite(parsedStart) ? parsedStart : 1,
        });
        element.setAttribute(
          "style",
          setStyle(element.getAttribute("style"), ["list-style", "list-style-type"], LIST_STYLE),
        );
        element.onEndTag(() => {
          listStack.pop();
        });
      },
    })
    .on("li", {
      element(element) {
        const list = listStack[listStack.length - 1];
        if (!list) return;

        const marker = list.ordered ? `${list.next++}. ` : "• ";
        element.prepend(marker, { html: false });
        element.setAttribute(
          "style",
          setStyle(element.getAttribute("style"), ["display", "list-style"], ITEM_STYLE),
        );
      },
    })
    // mdnice wraps each item in a section. Keeping the text but removing the
    // wrapper avoids the extra block boundary that triggers WeChat's blank
    // first-item behavior.
    .on("li > section", {
      element(element) {
        element.removeAndKeepContent();
      },
    })
    .on("li > p", {
      element(element) {
        element.removeAndKeepContent();
      },
    });

  return rewriter.transform(new Response(withoutEmptyItems)).text();
}

interface ListState {
  ordered: boolean;
  next: number;
}

const LIST_STYLE = "list-style: none; list-style-type: none;";
const ITEM_STYLE = "display: block; list-style: none;";

function setStyle(existing: string | null, propertiesToReplace: string[], addition: string): string {
  const properties = new Set(propertiesToReplace);
  const base = (existing ?? "")
    .split(";")
    .map((declaration) => declaration.trim())
    .filter((declaration) => {
      if (!declaration) return false;
      const colonIndex = declaration.indexOf(":");
      if (colonIndex < 0) return true;
      return !properties.has(declaration.slice(0, colonIndex).trim().toLowerCase());
    })
    .join("; ");
  return base ? `${base}; ${addition}` : addition;
}
