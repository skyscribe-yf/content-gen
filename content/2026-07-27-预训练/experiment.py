#!/usr/bin/env python3
"""射雕预训练实验 v4 - 最终版
策略：小词表(120字) + 两步 MLP + 2000 步 → loss从~4.8降到~1.5
目的：清晰展示随机→语法→知识的三个阶段
"""
import numpy as np
import time

SHEDIAO = """
第一回风雪惊变钱塘江浩浩江水日日夜夜无穷无休的从临安牛家村边绕过东流入海
江畔一排数十株乌桕树叶子似火烧般红正是八月天时村前村后的野草刚起始变黄
一抹斜阳映照之下更增了几分萧索两株大松树下围着一堆村民男男女女和十几个小孩
正自聚精会神的听着一个瘦削的老者说话那说话人五十来岁年纪一件青布长袍早洗得褪成了蓝灰色
只听他两片梨花木板碰了几下左手中竹棒在一面小羯鼓上敲起得得连声
小桃无主自开花烟草茫茫带晚鸦几处败垣围故井向来一一是人家
郭靖的父亲郭啸天是个猎户生的身材魁梧浓眉大眼他和妻子李萍住在牛家村
郭啸天的父亲原是山东人氏因避金兵之乱逃难来到临安府
杨铁心的娘子包惜弱性情温柔会绣花也会做些家常药
丘处机道长路过牛家村在这大雪夜里收了郭靖为徒
丘处机道这孩子根骨不凡贫道要收他为徒郭啸天道道长肯收小儿为徒那是天大的福分
杨铁心笑道大哥这孩子日后在江湖上闯荡说不定比我们出息呢
江南七怪柯镇恶朱聪韩宝驹南希仁张阿生全金发韩小莹
韩小莹道这孩子学得慢但学得扎实柯镇恶道我柯镇恶教徒弟不怕笨就怕懒
全金发拈须微笑我看这孩子日后必成大器
郭靖向六位师父磕了头回到茅屋中李萍早已备好了晚饭青菜豆腐咸菜窝窝头
郭啸天斟了一碗酒与杨铁心对饮火光里两个汉子的脸膛都被烈酒烧得红通通的
郭靖一边吃饭一边听父亲和杨叔叔谈论打猎的收获
饭后他在院子里打了一趟拳法虽然姿势笨拙但每一拳都打得虎虎生风
星光下他那矮墩墩的身影被茅屋的灯火拉得老长
""".replace("\n", "")

# ============================================================
class Tokenizer:
    def __init__(self, text, max_vocab=120):
        from collections import Counter
        counts = Counter(text)
        top = [ch for ch, _ in counts.most_common(max_vocab)]
        self.itos = {i: c for i, c in enumerate(top)}
        self.stoi = {c: i for i, c in enumerate(top)}
        self.V = len(top)

    def encode(self, s):
        return [self.stoi.get(c, 0) for c in s]

    def decode(self, ids):
        return "".join(self.itos.get(i, "?") for i in ids)

# ============================================================
class MLP_LM:
    def __init__(self, V, emb_dim=64, hidden=256, ctx=8):
        self.V = V; self.D = emb_dim; self.H = hidden; self.ctx = ctx
        self.E = np.random.randn(V, emb_dim) * 0.02
        self.W1 = np.random.randn(ctx * emb_dim, hidden) * 0.1
        self.b1 = np.zeros(hidden)
        self.W2 = np.random.randn(hidden, hidden) * 0.1
        self.b2 = np.zeros(hidden)
        self.Wo = np.random.randn(hidden, V) * 0.1
        self.bo = np.zeros(V)

    def forward(self, x):
        B = len(x)
        emb = self.E[x].reshape(B, -1)  # [B, ctx*D]
        h1 = np.tanh(emb @ self.W1 + self.b1)  # tanh 比 ReLU 更好
        h2 = np.tanh(h1 @ self.W2 + self.b2)
        return h2 @ self.Wo + self.bo, (emb, h1, h2)

    def gen(self, prompt, max_len=60, temp=0.8):
        ids = list(prompt)
        for _ in range(max_len):
            ctx_ids = ids[-self.ctx:] if len(ids) >= self.ctx else [0]*(self.ctx-len(ids)) + ids
            logits, _ = self.forward(np.array([ctx_ids]))
            p = np.exp((logits[0] - logits[0].max()) / max(temp, 0.01))
            p /= p.sum()
            ids.append(np.random.choice(self.V, p=p))
        return ids

def copy_model(m):
    n = MLP_LM(m.V, m.D, m.H, m.ctx)
    for a in ["E","W1","b1","W2","b2","Wo","bo"]:
        setattr(n, a, getattr(m, a).copy())
    return n

def train(model, data, steps=2000, bs=256, lr=0.02):
    n = len(data) - model.ctx
    losses = []
    ckpts = {}
    for s in range(steps):
        ix = np.random.randint(0, n, size=bs)
        x = np.array([[data[i+t] for t in range(model.ctx)] for i in ix])
        y = np.array([data[i+model.ctx] for i in ix])

        logits, (emb, h1, h2) = model.forward(x)
        # softmax + loss
        mx = logits.max(1, keepdims=True)
        probs = np.exp(logits - mx); probs /= probs.sum(1, keepdims=True)
        loss = -np.mean(np.log(probs[np.arange(bs), y] + 1e-10))

        # backward
        dp = probs.copy(); dp[np.arange(bs), y] -= 1; dp /= bs
        dWo = h2.T @ dp; dbo = dp.sum(0)
        dh2 = (dp @ model.Wo.T) * (1 - h2**2)  # tanh'
        dW2 = h1.T @ dh2; db2 = dh2.sum(0)
        dh1 = (dh2 @ model.W2.T) * (1 - h1**2)
        dW1 = emb.T @ dh1; db1 = dh1.sum(0)
        demb = (dh1 @ model.W1.T).reshape(bs, model.ctx, model.D)
        dE = np.zeros_like(model.E)
        for i in range(bs):
            for t in range(model.ctx):
                dE[x[i,t]] += demb[i,t]

        for p, g, r in [(model.E, dE, lr), (model.W1, dW1, lr*0.5),
                         (model.b1, db1, lr), (model.W2, dW2, lr*0.5),
                         (model.b2, db2, lr), (model.Wo, dWo, lr*0.5),
                         (model.bo, dbo, lr)]:
            p -= r * g

        losses.append(float(loss))
        if s % 500 == 0: print(f"  {s:4d} | loss {loss:.4f} | ppl {np.exp(loss):.0f}")
        if s == 0: ckpts[0] = copy_model(model)
        elif s == 499: ckpts[500] = copy_model(model)
    ckpts[steps] = copy_model(model)
    return losses, ckpts

def main():
    print("="*55)
    print("  射雕 · 预训练实验")
    print("  MLP(ctx=8, emb=64, hidden=256)×2 → tanh → softmax")
    print("="*55)

    text = (SHEDIAO + SHEDIAO + SHEDIAO) * 20  # ~80K chars
    tok = Tokenizer(text, max_vocab=250)
    data = np.array(tok.encode(text), dtype=np.int32)
    print(f"文本: {len(text):,}字 | 词表: {tok.V} | token: {len(data):,}")

    m = MLP_LM(tok.V, ctx=8)
    print(f"参数: {sum(v.size for v in [m.E,m.W1,m.b1,m.W2,m.b2,m.Wo,m.bo]):,}")

    t0 = time.time()
    losses, ckpts = train(m, data, steps=3000, bs=256, lr=0.02)
    print(f"\n耗时: {time.time()-t0:.1f}s")
    print(f"loss: {losses[0]:.2f} → {losses[499]:.2f} → {losses[-1]:.2f}")
    print(f"ppl:  {np.exp(losses[0]):.0f} → {np.exp(losses[499]):.0f} → {np.exp(losses[-1]):.0f}")

    # 三阶段生成
    print("\n" + "="*55)
    print("三阶段生成对比")
    print("="*55)
    prompts = ["郭靖道", "丘处机", "江南七怪"]
    for prompt in prompts:
        pids = tok.encode(prompt)
        print(f"\n[{prompt}]")
        for label, k in [("随机 init",0),("中期 500步",500),("收敛 3000步",3000)]:
            out = tok.decode(ckpts[k].gen(pids, max_len=40, temp=1.0))
            print(f"  {label:12s}: {out}")

    return losses, ckpts, tok

if __name__ == "__main__":
    losses, ckpts, tok = main()
    # 保存 loss 数据供文章使用
    import json
    out = {"losses": losses}
    with open("loss_data.json", "w") as f:
        json.dump(out, f)
    print("\nloss_data.json saved")
