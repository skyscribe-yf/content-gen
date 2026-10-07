# 素材底稿：Rysana C++ 复刻 TypeScript 编译器（正题 + Anders 对照 + 非孤例链）

采集：2026-10-07（当晚多次更新）· 状态：grill 已过、outline.md 已成稿 · 来源均为公开网络，链接原样保留

---

## 一、正题：Rysana CEO John (@jrysana) 的 TS C++ 移植

- **Rysana 背景**：rysana.com——"世界最快 AI"公司，V2 模型（2026-07 checkpoint）自称生成速度最高 10,000× 于常规 API、1000× 能效；主打结构化输出（schemas/grammars/programs）与 agent 场景。John 任 CEO，X 粉丝 12.3K，公司无公开仓库代码（rysana-ai org 为空）。
- **时间线（全部 @jrysana，自 9-27 起）**：
  | 日期 | 推文 | 数据 |
  |---|---|---|
  | 09-27 | "I'm porting TypeScript to C++ and so far it's looking ~1000x faster than v6" | 57.7K 阅 / 548 赞 · [链接](https://x.com/jrysana/status/2104105677937320391) |
  | 09-28 | "C++ rewrite of TypeScript is progressing well, seems certain it will end up on the order of ten times faster than the Go version and \*probably\* with a dramatically smaller codebase." | 26.9K 阅 / 379 赞 · [链接](https://x.com/jrysana/status/2104661080727314570) |
  | 09-29 | "My C++ port of TypeScript now passes more of TS6's own tests than TS7 does :') still >>10x faster than TS7 (Go) in most measurements" | 24K 阅 / 369 赞 · [链接](https://x.com/jrysana/status/2104921420522270767) |
  | 09-30 | "TS port in C++ is getting very close to full 1:1 support now (already beyond TS7 in terms of TS6 parity), and \*still\* often 100x faster than TS7 (Go) end to end; Always substantially smaller RSS; In the worst comparisons, still ~10x faster" | 14.4K 阅 / 271 赞 · [链接](https://x.com/jrysana/status/2105311118168301790) |
  | 09-30 | "I think we can publish this pretty soon, maybe this week or next" | [链接](https://x.com/jrysana/status/2105311256437752192) |
  | 10-01 | "My C++ port of TypeScript is now exactly 66,536 lines of code... damn, 1000 away from the coolest coincidence." | 5.4K 阅 · [链接](https://x.com/jrysana/status/2105578557271368023) |
  | 10-02 | "I've spent something like $10,000 of inference on the TS C++ port in the past few days... it's apparently 95% done now, and would've taken a human team of experts \*years\*, and (b) it took me very little time." | 9.1K 阅 / 110 赞 · [链接](https://x.com/jrysana/status/2105840360484389052) |
  | 10-03 | "My TS C++ port is nearly feature-complete: Matches ts6.x.x exactly on every interaction with 98% of TS's real tests as well as almost all of the 20 big projects I'm comparing (Zod, Claude Code, Drizzle, Tailwind, etc.) Now that it's close, the 100-1000x speedup\* seems certain." | 20.4K 阅 / 239 赞 · [链接](https://x.com/jrysana/status/2106450812079677754) |
  | 10-03 | "Clarity on speed so far... ~30-1000+ times faster than ts6 on big to small code; ~6-150+ times faster than ts7 on big to small code. **The smaller, faster end will benefit high-speed AI coding agents tremendously, I hope.**" | [链接](https://x.com/jrysana/status/2106450813564416112) |
  | ~10-05 | "98.3% done TS C++ port. Passing all 20 of my real-project comparisons perfectly too (Zod, Effect, Claude Code, Drizzle ORM, Tailwind, etc.) Can you guys ..."（截断） | [链接](https://x.com/jrysana/status/2106775342467661921) |
- **100% 推文（2026-10-07，约 15 小时前；作者提供原文，链接待补）**——推文全文：
  > C++ port of TypeScript (targeting TS6) is now 100% at parity.
  > It's 25-750x faster and 5-20x lower RSS.
  > Matches TS6 1:1 on every test, every diagnostic is identical given the same inputs, and it is identical on all of the dozens of popular TS projects we compare on.
- **数字链（均本人自称，口径滚动）**：09-27 ~1000× → 09-28 "order of ten times faster than the Go version" → 09-30 常 100×/最差 ~10× vs TS7 → 10-01 66,536 行 → **10-02 "$10,000 of inference、95% done（人类专家团队要花好几年）"** → 10-03 30-1000× vs ts6、6-150× vs ts7 → 10-05 98.3% → **10-06/07 100% at parity、25-750× faster、RSS 低 5-20×（基线未明说，应为 TS6）；10-07 跟进：~100K 行 C++、30,000+ tests 100.00% 全过**。写稿用最终版数字并标注"他自称/未独立验证"。
- **要点**：单人 + C++（当年 Anders 团队明确排除的选项之一）；输出是 tsc 行为 1:1（"matches exactly on every interaction"，对应中文「像素级复刻」）；~10 万行 C++（10-07 自述）≈ 原版 50 万行量级的 1/5；对标对象是微软官方 Go 版 TS7。
- **动机（他自己的原话）**：把编译器提速到"benefit high-speed AI coding agents"——为 agent 的秒级反馈循环服务。
- **AI 编写证据（10-07 升级为本人自述）**：10-02 推文——"$10,000 of inference"、95% done、"would've taken a human team of experts *years*"、"took me very little time"。旁证保留：网友 09-29 反问 "Are you letting AI to do the measuring?"；另一推 "One of my agents has been going for literally 15 hours…"（日期未确认）。
- **ts-rust（10-07 跟进的对比对象；作者提供）**：github.com/arun-murali0/ts-rust——"a native Rust reimplementation of TypeScript"（高保真语义分析起步，MIT，218 commits，1 star）。John 自述对比：ts-rust ~750K 行 Rust vs 他 ~100K 行 C++，并调侃 "Is this just Rust being so much more verbose?"。⚠️ 项目体量小、行数对比为其个人说法；文章如用只作一句色彩，不撑论点。
- ✅ **立论归属（作者 2026-10-07 确认；同日证据升级）**：「AI 写代码能力魔幻 / 语言选型逻辑被改写」是**作者自己的判断**。**10-07 捕获一手来源：10-02 推文 John 自述 "I've spent something like $10,000 of inference on the TS C++ port"、95% done、"would've taken a human team of experts \*years\*"、"took me very little time"**——正文可按「他自述」引用 AI 编写，不再回避；数字仍标「自称、未独立验证」。AI 写代码的案例链（Copilot/Bun/ArtCraft）保留。

---

## 二、对照事件：Anders Hejlsberg 的 TypeScript Go 移植（2025–2026）

### 事件本体
- **2025-03-11 官宣博客《A 10x Faster TypeScript》**（作者 Anders）
  https://devblogs.microsoft.com/typescript/typescript-native-port/
  - 明确是 **port（移植）不是 rewrite（重写）**：保留现有代码结构与语义，代号 Corsa，最终产品 TypeScript 7.0；JS 版沿 6.x（Strada）继续维护。
  - 首批数字：VS Code 1.5M LoC 77.8s→7.5s（10.4×）；Playwright 356K 11.1s→1.1s（10.1×）；TypeORM 270K 17.5s→1.3s（13.5×)；date-fns 104K 6.5s→0.7s（9.5×）；tRPC 18K 5.5s→0.6s（9.1×）；rxjs 2.1K 1.1s→0.1s（11×）。
  - 编辑器：VS Code 工程加载 9.6s→1.2s（8×）；整体内存约减半。
- **为什么选 Go（官方论证，2025-03 多轮）**
  - Anders 原话：Go 是"我们能达到的最低层语言：全平台优化原生码、对数据布局的强控制、支持循环数据结构、GC 自动内存管理、并发支持"。转述见 [TheNewStack 2025-03-18](https://thenewstack.io/microsoft-typescript-devs-explain-why-they-chose-go-over-rust-c/)。
  - **C#**：bytecode-first；AOT 不全平台；编译器核心"没有任何 class"（纯 functions + data structures），迁 C# 要扳成 OOP——"摩擦更大"。
  - **Rust**：dev lead Ryan Cavanaugh——试过 "tons of approaches"，全被不可接受的权衡挡住（性能/人体工学），或"退化成自己写 GC 的策略"，常需大量 unsafe；摆在面前的只有两条路：Rust 从零重写（"could take years"，且语义不兼容）vs Go 移植（"usable in a year or so"，语义兼容）。
  - "Idiomatic Go looked just like our existing codebase, so the port was greatly simplified."；"this was not a green field — it's a port of an existing codebase with **100 man-years of investment**"。
  - Anders 收尾金句："You can't argue with a 10x outcome!"
- **Anders 谈 AI 做移植（2026-01 devclass 访谈）** — 关键反差弹药
  https://www.devclass.com/ai-ml/2026/01/28/typescript-inventor-anders-hejlsberg-ai-is-a-big-regurgitator-of-stuff-someone-has-done/4079582
  - "We tried AI"（拿来把 TS 翻译成 Go）："**That went not so great** … we want a very deterministic outcome here. We want to port **half a million lines of code** and know that they do exactly what the old lines of code did. If you ask AI to translate them, it might **hallucinate** a little bit here and there, and now you've got to go carefully examine every line of code."
  - 他认可的替代用法："ask AI to generate a program that helps you do the port"（跑确定性程序）；后期用 AI 迁移新 PR 到 Go，"fairly successfully"。
  - 对 AI 的总体评价："a big regurgitator of stuff someone has done, with some extrapolation on top"。
  - 相关近作：Ryan Peterman 访谈《10x Faster Typescript, Why AI Won't Replace SWEs》（约 2026-09）。
- **结果**：TS 7.0 [RC 2026-06-18](https://visualstudiomagazine.com/articles/2026/06/22/typescript-7-0-rc-moves-microsofts-go-rewrite-into-the-mainline-compiler.aspx) → [GA 2026-07-08](https://devblogs.microsoft.com/typescript/announcing-typescript-7-0/)（8–12×）；`microsoft/typescript-go` 仓库 2026-09 永久归档（staging 使命完成）。
- **官方对比图数字（TS6 vs TS7，GA 贴）**：VS Code 2.3M LoC 125.7s→10.6s（11.9×）；Sentry 1.9M 139.8→15.7（8.9×）；Bluesky 628K 24.3→2.8（8.7×）；Playwright 528K 12.8→1.47（8.7×）；tldraw 345K 11.2→1.46（7.7×）。
- **官方内存图**：VS Code 5.2→4.2GB（-18%）；Sentry 4.9→4.6（-6%）；Bluesky 1.8→1.3（-26%）；Playwright 1.0→0.9（-11%）；tldraw 0.6→0.5（-15%）。

### 图片清单（已下载到本目录）
| 文件 | 内容 | 源 |
|---|---|---|
| `ts7-0-stable-1-1.png` | "Announcing TypeScript 7.0" 蓝底官宣图 | devblogs TS7.0 帖 |
| `7-0-speedup-chart-2.png` | TS6↔TS7 编译耗时对比条形图（VS Code 11.9× 等，英文） | 同上 |
| `7-0-mem-chart-2.png` | TS6↔TS7 内存对比条形图（英文） | 同上 |
| `native-preview-enable-202505.png` | 2025-05 原生预览版启用截图（VS Code 插件） | devblogs native previews 帖 |
| `native-preview-use-tsgo-202505-1.png` | 2025-05 `tsgo` 使用示例截图 | 同上 |
| `anders-github-avatar.png` | Anders GitHub 头像（460px） | github.com/ahejlsberg |
| `8fa3-*.png` / `c524-*.png` / `3488-*.png` | 快科技报道截图（ArtCraft 全家桶映射表、对应关系表） | 新浪财经转载快科技 |

## 三、非孤例链（"不是孤例"的证据池）

1. **ArtCraft「Crafting Apps」复刻 Adobe 全家桶（2026-10-06/07，今日）**
   - 7 个开源免费平替（纯 Rust、原生、非 Electron、MIT/Apache，源码在 GitHub `storytold` 组织）：
     PhotoCraft=Photoshop｜VectorCraft=Illustrator｜FilmCraft=Premiere Pro｜LightCraft=Lightroom｜PrintCraft=Acrobat/PDF｜EffectCraft=After Effects｜DesignCraft=InDesign。
   - 附加：CLI / JSON 控制通道 / MCP server（"Agent-ready"）；部分应用可编译 WebAssembly 上浏览器；商业模式=免费的软件 + ArtCraft AI Studio（AI 图片/视频，免费试用+付费算力）。
   - 自称 "clean-room reimplementation"；"Every Crafting App is written from scratch in Rust"；仓库带 `AGENTS.md`、`CLAUDE.md`（agent 开发痕迹）；vectorcraft 1.6k stars / 584 forks / 717 commits。
   - 状态：early alpha / in development，安装包已就绪（mac/win/linux）；快科技明说"AI 时代靠传统古法编程基本没可能…AI 写代码复刻 Adobe 全家桶的功能已经不是难事"；平替程度网友评价褒贬不一（"后者的评价应该更准一点"）。
   - 中文报道：https://finance.sina.com.cn/tech/discovery/2026-10-07/doc-iniukxhe5920739.shtml （快科技，10-07 16:36）
2. **GitHub Copilot runtime → Rust（2026-09-19，微软官方博客）**：AI agents 干了大部分移植；430K 行 TS→800K 行 Rust；约 $120K token + ~3 人周；135 次发布 / 14.5 周；基准 7.55→120 会话/秒（15.9×）；内存 1383MB→126MB；Stephen Toub："would have taken years and cost millions if done by hand"；几十处回归，"if it compiles, it's correct" 只是笑话。
   https://www.devclass.com/devops/2026/09/19/microsoft-agentically-ports-copilot-runtime-to-rust-for-120k/5297592
3. **Bun：Zig→Rust，几乎全靠 Claude agents**：~535K 行；截至 7-30 通过 99.8% 测试；$165K tokens；Zig 作者称其为 "unreviewed slop"（争议面，可作"泼冷水"素材）。
4. **Anthropic：16 个 Claude agents 造 C 编译器（2026-02）**：约 $20K API 成本、两周、10 万行、过 GCC torture test 99%。（本库是否写过待查。）
5. 旁证：pnpm recast in Rust（2026-09-05 devclass）。

## 四、反差框架（事实层速查）

| 维度 | 2025 Anders / TS 团队 | 2026 John / Rysana |
|---|---|---|
| 量级 | 100 man-years 存量、~50 万行、整个团队、一年半 | 单人、C++、~10 万行（10-07）、公开推文约 10 天窗口、$10K 推理 |
| 语言 | Go（C++/Rust **被排除**：无 GC、无循环结构支持、内存管理负担、"要自己写 GC"） | C++——正是当年被排除的选项 |
| AI | "We tried AI... went not so great"（幻觉、需逐行审查，半百万行要确定性） | 自述 $10,000 inference、"human team of experts would take years"、动机=为 agent 提速 |
| 目标 | 语义 100% 兼容的确定性移植，官方 8–12× | 自称 1:1 行为匹配（每个诊断都一致）、比 TS6 快 25–750×、RSS 低 5–20× |

## 五、风险与待决

- [x] John 的 AI 编写出处：**10-07 已捕获一手来源**（10-02 "$10,000 of inference" 推文 + "human team would take years"）；正文按「他自述」引用，数字标「自称」
- [ ] 数字口径混乱（1000x / 10x / 30-1000x / 6-150x / 25-750x，均为本人自称且仍在浮动），引用时必须给范围并标"他自称/未独立验证"
- [ ] 「像素级复刻」原文 = "Matches ts6.x.x exactly on every interaction" / "full 1:1 support"（勿直译为像素）
- [x] 篇幅：**~2000 字**（作者 2026-10-07 放宽，与项目默认一致）
- [x] 轨道：**文章轨**（作者拍板 A）；目标发布 **2026-10-08 20:00**
- [ ] TS7 已于 2026-07 GA，写作时注意"官方 Go 版已发布"的时态
