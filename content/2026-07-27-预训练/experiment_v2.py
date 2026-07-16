#!/usr/bin/env python3
"""射雕预训练实验 v2 — PyTorch CPU 版
4层 transformer + 100字词表 + 16字上下文 + 8000步

注意：目前脚本使用 CPU 运行。如果你的 AMD GPU 支持 ROCm，
安装 rocm-pytorch 后会自动加速（需改 device 为 'hip'）。
"""
import numpy as np
import time
import json

import torch
import torch.nn as nn
import torch.nn.functional as F

# ── 设备 ────────────────────────────────────────────────
# AMD GPU 若支持 ROCm 可改为 device = torch.device("hip")
device = torch.device("cpu")
print(f"设备: {device}（若需 GPU 加速，请安装 ROCm PyTorch）")

# ── 文本 ────────────────────────────────────────────────
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
丘处机道这孩子根骨不凡贫道要收他为徒郭靖天道长肯收小儿为徒那是天大的福分
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

# ── Tokenizer ────────────────────────────────────────────
class Tokenizer:
    def __init__(self, text, max_vocab=100):
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

# ── 数据集 ──────────────────────────────────────────────
class NextTokenDataset:
    def __init__(self, data, ctx_len):
        self.data = data
        self.ctx = ctx_len

    def __len__(self):
        return len(self.data) - self.ctx

    def __getitem__(self, idx):
        x = self.data[idx:idx + self.ctx]
        y = self.data[idx + self.ctx]
        return torch.tensor(x, dtype=torch.long), torch.tensor(y, dtype=torch.long)

# ── 模型 ────────────────────────────────────────────────
class TinyTransformer(nn.Module):
    def __init__(self, V, emb=128, nhead=4, hidden=512, nlayer=4, ctx=16, drop=0.1):
        super().__init__()
        self.ctx = ctx
        self.token_emb = nn.Embedding(V, emb)
        self.pos_emb = nn.Embedding(ctx, emb)
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=emb, nhead=nhead, dim_feedforward=hidden,
            dropout=drop, batch_first=True, activation="gelu"
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=nlayer)
        self.norm = nn.LayerNorm(emb)
        self.head = nn.Linear(emb, V)
        self.register_buffer("mask", torch.triu(torch.ones(ctx, ctx), diagonal=1).bool())

    def forward(self, x):
        B, T = x.shape
        tok = self.token_emb(x)
        pos = self.pos_emb(torch.arange(T, device=x.device))
        h = self.transformer(tok + pos.unsqueeze(0), mask=self.mask[:T, :T])
        h = self.norm(h)
        return self.head(h[:, -1, :])

    @torch.no_grad()
    def generate(self, prompt_ids, max_len=50, temp=0.8):
        self.eval()
        ids = list(prompt_ids)
        for _ in range(max_len):
            ctx = ids[-self.ctx:]
            x = torch.tensor([ctx], dtype=torch.long, device=next(self.parameters()).device)
            logits = self(x)[0]
            probs = F.softmax(logits / max(temp, 0.01), dim=-1)
            next_id = torch.multinomial(probs, 1).item()
            ids.append(next_id)
        self.train()
        return ids

# ── 训练 ────────────────────────────────────────────────
def main():
    print("=" * 60)
    print("  射雕 · 预训练实验 v2（PyTorch CPU）")
    print("  4层 Transformer | emb=128 | head=4 | hidden=512")
    print("=" * 60)

    text = (SHEDIAO * 40)
    tok = Tokenizer(text, max_vocab=100)
    data = tok.encode(text)
    print(f"文本: {len(text):,}字 | 词表: {tok.V} | token: {len(data):,}")

    ctx_len = 16
    n = len(data) - ctx_len
    split = int(n * 0.9)
    train_data = np.array(data[:split + ctx_len], dtype=np.int64)
    val_data = np.array(data[split:], dtype=np.int64)

    train_ds = NextTokenDataset(train_data, ctx_len)
    val_ds = NextTokenDataset(val_data, ctx_len)
    train_loader = torch.utils.data.DataLoader(
        train_ds, batch_size=64, shuffle=True, drop_last=True, num_workers=0
    )

    m = TinyTransformer(tok.V, emb=128, nhead=4, hidden=512, nlayer=4, ctx=ctx_len).to(device)
    np_params = sum(p.numel() for p in m.parameters())
    print(f"参数: {np_params:,}")

    steps = 8000
    opt = torch.optim.AdamW(m.parameters(), lr=3e-4, weight_decay=0.01)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=steps, eta_min=3e-5)

    t0 = time.time()
    losses, val_losses = [], []
    ckpts = {}
    prompts = ["郭靖道", "丘处机", "江南七怪"]

    step = 0
    epoch = 0
    while step < steps:
        epoch += 1
        for xb, yb in train_loader:
            xb, yb = xb.to(device), yb.to(device)
            logits = m(xb)
            loss = F.cross_entropy(logits, yb)
            opt.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(m.parameters(), 1.0)
            opt.step()
            sched.step()
            step += 1
            losses.append(float(loss.item()))

            if step % 1000 == 0 or step == 1:
                m.eval()
                with torch.no_grad():
                    # 用 200 个 val 样本估计 val loss
                    vx_list, vy_list = [], []
                    for i in range(min(200, len(val_ds))):
                        vx_i, vy_i = val_ds[i]
                        vx_list.append(vx_i)
                        vy_list.append(vy_i)
                    vx = torch.stack(vx_list).to(device)
                    vy = torch.tensor(vy_list, dtype=torch.long).to(device)
                    vloss = F.cross_entropy(m(vx), vy).item()
                m.train()
                val_losses.append(vloss)
                print(f"  {step:5d} | train {loss.item():.4f} | val {vloss:.4f} | "
                      f"ppl {np.exp(loss.item()):.1f} → {np.exp(vloss):.1f}")

            if step in (1, 1000, 2000, 4000, 8000):
                ckpts[step] = {k: v.clone() for k, v in m.state_dict().items()}
            if step >= steps:
                break

    elapsed = time.time() - t0
    print(f"\n耗时: {elapsed:.1f}s ({elapsed/60:.1f}分)")
    print(f"轮数: {epoch}")
    print(f"loss: {losses[0]:.4f} → {losses[-1]:.4f}")
    print(f"ppl:  {np.exp(losses[0]):.0f} → {np.exp(losses[-1]):.0f}")

    # 生成
    print("\n" + "=" * 60)
    print("三阶段生成对比")
    print("=" * 60)
    results = {}
    for prompt in prompts:
        pids = tok.encode(prompt)
        results[prompt] = {}
        for k in sorted(ckpts.keys()):
            m.load_state_dict(ckpts[k])
            # 多采样 3 次取最优（更能体现模型能力）
            outs = [tok.decode(m.generate(pids, max_len=50, temp=0.8)) for _ in range(3)]
            results[prompt][k] = outs[0]
            # 显示
            ppl_val = np.exp(losses[min(k-1, len(losses)-1)])
            print(f"\n[{prompt}] step={k} (ppl≈{ppl_val:.0f})")
            for i, o in enumerate(outs):
                print(f"  → {o}")

    out_data = {
        "losses": losses, "val_losses": val_losses,
        "results": results, "params": np_params,
        "elapsed": elapsed, "epochs": epoch, "device": str(device),
    }
    with open("loss_data_v2.json", "w") as f:
        json.dump(out_data, f, ensure_ascii=False, indent=2)
    print("\nloss_data_v2.json saved")

if __name__ == "__main__":
    main()
