# DeepSeek V4.1 Flash：安全实测追平前沿，价格打到 0.03x

> 素材：@pilvar222 网络安全基准实测（3 图）+ @MaxForAI 元宝折扣（1 图）

## 手敲文本（digest）

DeepSeek V4.1 Flash 的预览版，被一个做网络安全的人拉出来实测了。

结果有点意思。

单次运行，能重新发现 65.6% 的近期 CVE，旧版是 55.2%。pass@3 直接到 84.4%，超过 Grok 4.6、Opus 5、GPT-5.6-Sol 这些前沿模型。精确率 73.8% → 78.9%，误报更少。

他还说这模型「更肯干活」：在给定范围内找不到漏洞，会主动去别处找，而不是停下来。每轮工具使用 1.7 → 1.79，虽然离 Astra 的 4.67 还有距离。

成本呢？单任务比前沿模型低 50 倍。

同一天，腾讯 Workbuddy 跟进 DeepSeek 调价，给 V4.1 Flash 挂了个限时折扣：9 月 10 日到 23 日，0.03x，无峰谷限制，比 V4 Flash 首发时还便宜。同屏对比：GLM-5.3-Flash 0.06x，GLM-5.3 0.79x。

评论区已经在猜：DeepSeek 降价 + 云厂商竞争，国产模型价格战是不是要开打了。

说句公道话：这是第三方独立测试，不是官方基准；而且测的是预览版（expires-on-0910），正式版可能更好。

性能追平前沿、价格打到地板，这俩事撞在同一天，挺有戏剧性的。

你觉得国产模型价格战会真打起来吗？评论区聊聊。

<a class="wx_topic_link" data-topic="1" style="color: #576b95;">#DeepSeek</a>  <a class="wx_topic_link" data-topic="1" style="color: #576b95;">#V4.1Flash</a>  <a class="wx_topic_link" data-topic="1" style="color: #576b95;">#大模型降价</a>  <a class="wx_topic_link" data-topic="1" style="color: #576b95;">#数解AI</a>
