import assert from "node:assert/strict";
import test from "node:test";

import { normalizeWechatLists } from "./wechat-list-safety.ts";

test("removes empty leading items and writes unordered markers into content", async () => {
  const html = [
    '<ul style="list-style-type: disc;">',
    '<li><section> </section></li>',
    '<li><section>第一项</section></li>',
    '<li><section>第二项</section></li>',
    '</ul>',
  ].join("");

  const result = await normalizeWechatLists(html);

  assert.doesNotMatch(result, /<li[^>]*>\s*<\/li>/i);
  assert.match(result, /<ul[^>]*list-style-type: none/);
  assert.doesNotMatch(result, /list-style-type: disc|list-style-type: decimal/);
  assert.match(result, /<li[^>]*>• 第一项<\/li>/);
  assert.match(result, /<li[^>]*>• 第二项<\/li>/);
});

test("numbers ordered lists from their start value and resets nested lists", async () => {
  const html = [
    '<ol start="3">',
    '<li><section>第三项<ol><li><section>子项</section></li></ol></section></li>',
    '<li><section>第四项</section></li>',
    '</ol>',
  ].join("");

  const result = await normalizeWechatLists(html);

  assert.match(result, /<ol[^>]*list-style-type: none/);
  assert.match(result, /<li[^>]*>3\. 第三项<ol[^>]*list-style-type: none/);
  assert.match(result, /<li[^>]*>1\. 子项<\/li>/);
  assert.match(result, /<li[^>]*>4\. 第四项<\/li>/);
});
