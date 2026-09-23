# 便宜不再是国产专属，Luna 牌价压过了 Flash

> 2026-09-23 贴图草稿。未发布。数字截至 2026-09-23 官方牌价，见同目录 `sources.md`。
> 图 1 `01.png`：同一天砍价，牌价梯子。图 2 `02.png`：冷启动、缓存、能力三张账单。

## 手敲文本（digest）

9 月 22 日这一天，两家前后脚砍价。

先是 Claude Opus 5.5。牌价从 Opus 5 的 5 美元 / 25 美元，降到 4 / 20，每百万 token。看着只降了两成。狠的是缓存读取，0.50 降到 0.20，砍了六成。Anthropic 自己说，默认设置下典型负载会比 Opus 5 便宜 40%，因为 token 也用得少。输出还快了三成以上。

公开报道说，大约一个半小时后，OpenAI 放出 GPT-6 Sol 和 Luna。Sol 是 2 / 10，Luna 是 0.10 / 0.50。官方口径：相对 GPT-5.6 正在生效的促销价，再降 50%。Luna 输出从 1.20 到 0.50，其实比五成还深，标题仍写成 50%。旗舰 Astra 还是 10 / 50，9 月 3 日就在了。22 日补的不是更强的旗舰，是把便宜档压下来。

看完两边公告，刺眼的不是 Opus，是 Luna。

DeepSeek V4.1 Flash 闲时 0.15 进、0.60 出。Luna 是 0.10 和 0.50。输入低三分之一，输出低大约 17%。忙时 Flash 翻倍，0.30 / 1.20，Luna 的输入是它的三分之一，输出大约四成。OpenAI 的走量档，牌价上压过了 DeepSeek 的走量档。

别顺着这句往下滑。GLM-5.3-Flash 官方 0.8 元进、2.8 元出。按 7.2 粗算，输入和 Luna 几乎打平，Luna 还略低一点，输出仍是 GLM 更低。便宜档没有被一家通吃。

旗舰这边，DeepSeek V4 Pro 闲时 0.66 / 1.98，仍大约是 Sol 的三分之一输入、五分之一输出。GLM-5.3 是 8 元 / 28 元，折下来仍明显低于 Sol。通义 Qwen3.7-Max 国内刊例 12 元 / 36 元，输入已经贴近 Sol，输出大约还有一半的空间。被掀的不是 Pro 的单价，是那句老口号。Astra 对 Pro，输入大约 15 倍，输出大约 25 倍。换成 Sol，收成大约 3 倍和 5 倍。「便宜一个数量级」，今天不好再说了。

更别扭的是 Kimi K3。国内站，缓存未命中 20 元，输出 100 元。同一汇率下大约 2.8 / 13.9 美元，输入输出都比 Sol 贵约四成。国产旗舰里，这轮牌价上最被动的是 K3。

缓存才是 agent 的真账单。Flash 闲时缓存命中 0.003，Luna 是 0.01，Sol 和 Opus 5.5 都是 0.20。前缀不动的长上下文，DeepSeek 还守得住。Kimi 缓存命中 2 元，GLM-5.3 也是 2 元，折下来大约 0.28，已经比 Opus 5.5 的缓存读取贵。不是每家国产都还有缓存优势。

能力别看混榜。OpenAI 说，Sol 在他们的 AutomationBench 上，xhigh 拿到 33.2%，单任务 0.27 美元，Opus 5 拉满是它的 11.1 倍成本。表里没有 Opus 5.5。Anthropic 的表打的是 Astra 和 GPT-5.6 Sol，也没有 GPT-6 Sol。两张家榜，都没打到同一天的对手。网络安全那类请求，Opus 5.5 大多还会路由回 Opus 4.8，那一栏不能当成纯 5.5 的分。

X 上 Box 的 Aaron Levie 说，该看单任务成本。token 一便宜，agent 能铺的活就暴涨。也有人觉得 Sol 就是量化过的 Astra，降价大于升级。牌价是实的。榜还没对齐。

话说回来，被打到的是叙事，不是 DeepSeek Pro 的单价。冷启动、走量、免费用户能摸到的那一档，Luna 已经坐进来了。ChatGPT 的 Free 和 Go，桌面端就能用 Luna。Claude 加了 5 小时额度，限流重置可以存着以后用。国产订阅再拿「包含多少旗舰 token」说话，得重新算。

Sonnet 5.5 和 Haiku 5.5，Anthropic 说随后几周就到。这轮还没砍完。

你现在的默认模型，是按牌价换，还是按自己仓库里那一下的账单换？

<a class="wx_topic_link" data-topic="1" style="color: #576b95;">#大模型价格战</a>  <a class="wx_topic_link" data-topic="1" style="color: #576b95;">#GPT-6</a>  <a class="wx_topic_link" data-topic="1" style="color: #576b95;">#Claude</a>  <a class="wx_topic_link" data-topic="1" style="color: #576b95;">#国产大模型</a>  <a class="wx_topic_link" data-topic="1" style="color: #576b95;">#数解AI</a>
