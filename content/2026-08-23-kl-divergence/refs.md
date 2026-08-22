# refs.md — 引用素材（AI 联网查证，2026-08-22）

## 主引用源：KL is All You Need

- **标题**: KL is All You Need
- **作者**: Alexander A. Alemi（Google DeepMind 研究员）
- **链接**: https://blog.alexalemi.com/kl-is-all-you-need.html
- **日期**: 2024-01-08（源自 NeurIPS 2024 InfoCog Workshop 演讲）
- **核心论点**: 现代机器学习几乎所有著名目标函数都是同一个「万能配方」：
  1. 画出真实世界的因果图 P
  2. 在真实世界上加你想要的东西（增强）
  3. 画出梦想世界 Q（成功长什么样）
  4. 最小化两者间的 KL 散度
- **文中推导覆盖**: 密度估计 → 监督学习 → VAE（D+R≥L≥H）→ VIB → 半监督 VAE → 扩散 → 变分贝叶斯推断 → Bayes By Backprop → TherML
- **关键解读视角**: KL = expected weight of evidence（期望证据权重）；非负性 = 「世界不会骗我们」；不对称性由此自然解释
- **已引用其图片**（refs-img/，成稿时标注图源）：
  - `kl-elephant.png` — 盲人科学家摸大象：「It's Diffusion / It's a VAE / It's Bayesian Inference…」（房间里的 elephant 就是 KL）
  - `vae.png` — World P（world we have）vs World Q（world we want）因果图
  - `diffusion.png` — World P/Q 马尔可夫链：前向加噪链 vs 反向去噪链

## 配套前作（同作者）

- **Why KL?** (2020-08-07): https://blog.alexalemi.com/kl.html
  - 公理化唯一推出 KL 形式；贝叶斯定理是「最小 KL 更新」的推论
  - **双头硬币例子出处**（本文实测段采用）：公平硬币 vs 双头硬币——正向 KL=∞（迟早见到反面，q(反面)=0）；反向每回合 1 bit 证据，连出 5 个正面 ≈ 15 dB ≈ 97% 置信是双头

## 新增引用源：From GAN to WGAN

- **标题**: From GAN to WGAN
- **作者**: Lilian Weng（OpenAI 前 VP Research / Thinking Machines 联合创始人）
- **链接**: https://lilianweng.github.io/posts/2017-08-20-gan/
- **日期**: 2017-08-20（2018 更新）
- **可引用要点**（已索引知识库 source: lilianweng-gan-wgan）:
  - GAN 原始训练准则在最优判别器下 ≈ 最小化 JSD（Goodfellow 2014）
  - KL 不对称的坑：「p(x) 接近零而 q(x) 显著非零时，q 的效果被无视」
  - **不重叠分布对比实验**（支撑「JS 没解决完整问题」）：两分布不相交时 D_KL(p‖q)=D_KL(q‖p)=+∞，D_JS=log 2（θ≠0 时恒定、θ=0 处跳变不可微），唯 W(P,Q)=|θ| 处处平滑——梯度下降需要平滑度量
  - Mode collapse：生成器塌缩到只产出同样输出（图 mode_collapse.png，备用未下载）
- **已引用其图片**: `KL_JS_divergence.png` — 四联图：p/q 高斯 → 正向 KL → 反向 KL → JS 对称曲线；`EM_distance_discrete.png`（推土机搬土离散示意，备用）

## 辅助源（备选）

- Six and a half intuitions for KL divergence — Callum McDougall, 2022: https://www.perfectlynormal.co.uk/blog-kl-divergence
- KL Divergence Demystified — Naoki Shibuya, 2018: https://naokishibuya.github.io/blog/2018-11-06-kl-divergence-demystified/

## 成稿参考资料清单（拟进 weixin.md 尾部，按 TRPO 篇格式）

1. Alemi, A. A., [KL is All You Need](https://blog.alexalemi.com/kl-is-all-you-need.html), 2024. 万能配方与本文图 1/3/4 来源。
2. Weng, L., [From GAN to WGAN](https://lilianweng.github.io/posts/2017-08-20-gan/), 2017. KL/JS/Wasserstein 对比与本文 JS 图来源。
3. Kingma, D. P., & Welling, M., [Auto-Encoding Variational Bayes](https://arxiv.org/abs/1312.6114), ICLR 2014. VAE 原文。
4. Ho, J., Jain, A., & Abbeel, P., [Denoising Diffusion Probabilistic Models](https://arxiv.org/abs/2006.11239), NeurIPS 2020. DDPM 原文。
5. Goodfellow, I., et al., [Generative Adversarial Nets](https://arxiv.org/abs/1406.2661), NIPS 2014. GAN 与 JS 散度渊源。
6. Arjovsky, M., Chintala, S., & Bottou, L., [Wasserstein GAN](https://arxiv.org/abs/1701.07875), 2017. 推土机距离落地 GAN。

系列内互链（正文用微信 URL）：多维高斯篇、TRPO 篇、预训练篇（交叉熵）、随机变量篇（数学期望）。
