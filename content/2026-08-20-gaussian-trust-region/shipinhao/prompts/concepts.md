# 概念图 Prompt（视频号内嵌插图，3 张）

统一风格前缀（每张 prompt 前都要带）：

> 扁平科技教育插画，深海军蓝背景（#16213E 系），金黄/青/绿点缀，柔和辉光、微距质感、电影级光影、干净无噪点。风格：3Blue1Brown 式极简、几何化，**画面中不出现任何文字、数字、年份或公式**。关键视觉元素居中，四周留 15% 留白。

生成命令（`source ~/.bash_env` 后再跑）：

```bash
python3 scripts/yairouter_img.py \
  --prompt "<前缀 + 下方画面描述>" --size 1024x1024 --quality high \
  --output-dir content/2026-08-20-gaussian-trust-region/shipinhao/img --filename <slug>.png
python3 scripts/make_round_logo.py content/2026-08-20-gaussian-trust-region/shipinhao/img/<slug>.png \
  --out content/2026-08-20-gaussian-trust-region/shipinhao/img/<slug>-round.png
```

---

## s1-cloud.png — 云形策略（S1 页2）

画面主体：一个漂浮在深空中的半透明发光椭圆云团，由成千上万颗细密金点组成，云团中心略空、边缘最密（壳状），旁边悬浮一把极简金属直尺，直尺贴到云团边缘却量不出长度、显得格格不入、微微弯曲失效。云团有柔和金色内发光。

标注（画面内文字一律不要）。

## s2-ellipse.png — 一个窄一个宽，拼成椭圆（S2 页2，可选）

画面主体：一个被纵向压扁的发光椭圆环悬浮在深空中，椭圆的长轴方向用一条青色柔光丝带轻轻拉长、短轴方向用一条金色柔光丝带轻轻压短，两条丝带在椭圆的中心交叉成一个十字，整团云是壳状空心的。冷青与暖金对峙，几何感极强。

## s5-narrow.png — 窄云经不起推（S5 页2）

画面主体：一团被压得很扁、非常窄的发光金色云，一根细小的白色指针从外部轻轻一碰，云团立刻像玻璃一样向四周炸开细密的裂纹与光屑；指针本身很小、动作很轻，与云的剧烈反应形成强烈反差。背景深蓝近黑，云碎屑是画面里最亮的部分。
