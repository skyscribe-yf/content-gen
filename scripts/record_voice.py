#!/usr/bin/env python3
"""口播录音：麦克风探测 + ffmpeg 录音 + 逐段核对。

解决三个坑（2026-08-15 RLHF 视频）：
  1. 用错麦克风（用户提醒"应该使用CM40"）→ 录音前自动探测有信号的设备
  2. 录音窗口不够，最后一句被截断（S2）→ 窗口 = 预估时长 + 余量
  3. 手敲 ffmpeg 命令易错 → 封装成脚本

用法:
  python3 scripts/record_voice.py content/<日期>-<主题>/shipinhao --seg S1 --dur 40
  python3 scripts/record_voice.py content/<日期>-<主题>/shipinhao --probe   # 只探测麦克风

参数:
  --seg S1..S8   要录的段（默认 S1）
  --dur 秒       录音窗口时长（默认 40s，建议 = 预估时长 + 10-15s 余量）
  --probe        只探测可用麦克风，不录音
  --card N       指定 ALSA 设备号（默认自动探测有信号的）
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path


def run(cmd: list[str], check: bool = True, timeout: int | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, check=check, capture_output=True, text=True, timeout=timeout)


def list_cards() -> list[dict]:
    """列出可用录音源（优先 PipeWire Audio/Source 节点，fallback ALSA）。"""
    try:
        out = run(["pw-dump"], check=False).stdout
        import json as _json
        sources = []
        for obj in _json.loads(out):
            info = obj.get("info", {}).get("props", {})
            if info.get("media.class") == "Audio/Source" and "monitor" not in info.get("node.name", ""):
                sources.append({"card": 1000 + len(sources), "device": info["node.name"],
                                "name": info.get("node.description", info["node.name"]), "desc": "PipeWire"})
        if sources:
            return sources
    except Exception:
        pass
    out = run(["arecord", "-l"], check=False).stdout + run(["arecord", "-l"], check=False).stderr
    cards = []
    for m in re.finditer(r"card (\d+): (\S+) \[([^\]]+)\], device (\d+): ([^\[]+) \[([^\]]+)\]", out):
        cards.append({"card": int(m.group(1)), "name": m.group(3), "device": int(m.group(4)), "desc": m.group(6)})
    return cards


def probe_signal(card: int, device: int) -> float:
    """录 2s 采样，返回 max_volume（dB）。有信号 = max_volume > -40dB。"""
    tmp = f"/tmp/probe_c{card}.wav"
    if card >= 1000:  # PipeWire 节点
        run(["timeout", "4", "pw-record", "--target", str(device), "--rate", "48000",
             "--channels", "2", "--volume", "1.0", tmp], check=False)
    else:
        run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-f", "alsa",
             "-i", f"hw:{card},{device}", "-t", "2", "-y", tmp], check=False)
    out = run(["ffmpeg", "-hide_banner", "-i", tmp, "-af", "volumedetect", "-f", "null", "-"], check=False).stderr
    m = re.search(r"max_volume: (-?[0-9.]+) dB", out)
    return float(m.group(1)) if m else -99.0


def pick_mic() -> tuple[int, int]:
    """自动探测有信号的麦克风。"""
    cards = list_cards()
    if not cards:
        sys.exit("未找到录音设备")
    print("可用录音设备:")
    for c in cards:
        print(f"  [{c['card']}] {c['name']} ({c['desc']})")
    # 探测每个设备信号
    for c in cards:
        vol = probe_signal(c["card"], c["device"])
        print(f"  [{c['card']}] 信号: {vol:.1f}dB {'✅ 可用' if vol > -40 else '❌ 无信号'}")
        if vol > -40:
            return c["card"], c["device"]
    sys.exit("所有设备均无信号，请检查麦克风连接")


def record(card: int, device: int, seg: str, dur: int, out_dir: Path) -> None:
    """用 ffmpeg/pw-record 录音。"""
    out = out_dir / f"{seg.lower()}.wav"
    print(f"录音 {seg} → {out}（{dur}s）")
    print("请现在开始念！")
    if card >= 1000:  # PipeWire 节点（pw-record 无时长参数，用 timeout 终止）
        run(["timeout", str(dur + 5), "pw-record", "--target", str(device), "--rate", "48000",
             "--channels", "2", "--volume", "1.0", str(out)], check=False, timeout=dur + 30)
    else:
        run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-f", "alsa",
             "-i", f"hw:{card},{device}", "-t", str(dur), "-ar", "48000", "-ac", "2",
             "-y", str(out)])
    print(f"录音完成: {out}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("workdir", help="shipinhao 工作目录")
    ap.add_argument("--seg", default="S1", help="要录的段（S1..S8）")
    ap.add_argument("--dur", type=int, default=40, help="录音窗口秒数")
    ap.add_argument("--probe", action="store_true", help="只探测麦克风")
    ap.add_argument("--card", type=int, default=None, help="指定 ALSA 设备号")
    args = ap.parse_args()

    wd = Path(args.workdir)
    rec_dir = wd / "recordings"
    rec_dir.mkdir(exist_ok=True)

    if args.probe:
        pick_mic()
        return

    if args.card is not None:
        if args.card >= 1000:  # PipeWire 节点：按索引取节点名
            cards = list_cards()
            node = next((c for c in cards if c["card"] == args.card), None)
            if node is None:
                sys.exit(f"未找到 PipeWire 节点 #{args.card}")
            card, device = node["card"], node["device"]
        else:
            card, device = args.card, 0
    else:
        card, device = pick_mic()
    record(card, device, args.seg, args.dur, rec_dir)


if __name__ == "__main__":
    main()
