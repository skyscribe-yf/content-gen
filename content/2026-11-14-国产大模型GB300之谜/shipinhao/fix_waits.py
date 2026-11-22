#!/usr/bin/env python3
""" scenes.py 时间轴帧精确精修 v3：
Manim 对每个 play/wait 的时长向上取整到整帧（ceil(d*30)/30），累计取整会越过
at_clip 锚点 → 渲染时 at_strict 回退报错。本脚本按帧量化模拟整场时间轴：
  - wait 值取整帧倍数，落点为「下一锚点前 1 帧」（at() 再取整 1 帧恰好落在锚点上）；
  - 放不下的 play/emphasize 等 run_time 缩到间隔内的整帧值；
  - at_clip 不可达（锚点太密）报出手动。
反复运行至无手动项，再 check_manim_scene.py --strict 复核。
"""
import ast
import json
import math
import re
import sys
from pathlib import Path

SCENES = Path("content/2026-11-14-国产大模型GB300之谜/shipinhao/scenes.py")
SB = json.loads(Path("content/2026-11-14-国产大模型GB300之谜/shipinhao/tts/sentence-boundaries.json").read_text())
CLIPS = {s["id"]: {c["id"]: c["start"] for c in s["clips"]} for s in SB["segments"]}
FPS = 30

sys.path.insert(0, "scripts")
import manim_timeline as mt


def q_up(d: float) -> float:
    """Manim 的帧向上取整（np.arange(0,d,1/30) 帧数）。"""
    return math.ceil(d * FPS - 1e-9) / FPS


def q_down(d: float) -> float:
    return math.floor(d * FPS + 1e-9) / FPS


def main() -> None:
    src = SCENES.read_text(encoding="utf-8")
    tree = ast.parse(src)
    constructs = dict(mt._constructs(tree))
    lines = src.split("\n")
    wait_patch: dict[int, float] = {}
    run_patch: dict[int, float] = {}
    manual: list[str] = []

    for scene_name, fn in constructs.items():
        events = mt._events(fn)
        clip_starts = CLIPS.get(scene_name, {})
        elapsed = 0.0
        for i, e in enumerate(events):
            if e.kind == "clip":
                target = clip_starts.get(e.label)
                if target is None:
                    manual.append(f"{scene_name} L{e.line}: at_clip({e.label}) 不在时间轴")
                    continue
                if target < elapsed - 1e-6:
                    manual.append(f"{scene_name} L{e.line}: at_clip({e.label}={target:.3f}) 不可达（当前 {elapsed:.3f}）——去掉该锚点或缩短前面动作")
                # at() 内部 wait 也按帧取整
                elapsed = elapsed + q_up(max(0.0, target - elapsed))
            elif e.kind == "action" and e.duration is not None:
                dur = e.duration
                nxt = None
                nxt_label = ""
                for fut in events[i + 1:]:
                    if fut.kind == "clip":
                        nxt = clip_starts.get(fut.label)
                        nxt_label = fut.label
                        break
                    if fut.kind == "at":
                        nxt = fut.value
                        nxt_label = "self.at"
                        break
                if nxt is None:
                    elapsed += q_up(dur)
                    continue
                if e.label == "self.wait":
                    # 本 wait 之后到下一锚点前的动作（帧量化）总时长
                    tail = 0.0
                    for fut in events[i + 1:1:]:
                        pass
                    for fut in events[i + 1:]:
                        if fut.kind in {"clip", "at"}:
                            break
                        if fut.kind == "action" and fut.duration is not None:
                            tail += q_up(fut.duration)
                    # 目标：elapsed + wait_q + tail_q + at取整1帧 <= nxt
                    # => wait_q <= nxt - elapsed - tail - 1帧
                    room = nxt - elapsed - tail - 2.0 / FPS
                    if room < 1.0 / FPS:
                        manual.append(f"{scene_name} L{e.line}: 锚点 {nxt_label}({nxt:.3f}) 前放不下（余 {room:.3f}s，后续 {tail:.3f}s）——缩短后续动作或去掉锚点")
                        room = 1.0 / FPS
                    wait_patch[e.line] = round(q_down(room), 4)
                    elapsed += q_down(room)
                else:
                    qd = q_up(dur)
                    if elapsed + qd > nxt + 1e-9:
                        room = nxt - elapsed
                        if room >= 1.0 / FPS:
                            run_patch[e.line] = round(q_down(room - 0.5 / FPS), 4)
                            manual.append(f"{scene_name} L{e.line}: {e.label} run_time {dur}→{q_down(room - 0.5 / FPS):.4f}（锚点 {nxt_label} {nxt:.3f} 前）")
                            qd = q_down(room - 0.5 / FPS)
                        else:
                            manual.append(f"{scene_name} L{e.line}: {e.label} 间隔仅 {room:.3f}s（锚点 {nxt_label} {nxt:.3f}）——去掉锚点或前移动作")
                    elapsed += qd

    # 应用 run_time 补丁
    run_re = re.compile(r"run_time=([0-9]+\.?[0-9]*)")
    for ln, val in sorted(run_patch.items()):
        idx = ln - 1
        if "run_time=" in lines[idx]:
            lines[idx] = run_re.sub(f"run_time={val:.4f}", lines[idx], count=1)
    # 应用 wait 补丁
    wait_re = re.compile(r"self\.wait\(([0-9]+\.?[0-9]*)\)")
    for ln, val in sorted(wait_patch.items()):
        idx = ln - 1
        m = wait_re.search(lines[idx])
        if m:
            lines[idx] = lines[idx][: m.start()] + f"self.wait({val:.4f})" + lines[idx][m.end():]
    SCENES.write_text("\n".join(lines), encoding="utf-8")
    print(f"run_time 补丁 {len(run_patch)} 处 · wait 补丁 {len(wait_patch)} 处")
    print("—— 需手动处理 ——" if manual else "无手动项")
    for m_ in manual:
        print(" ", m_)


if __name__ == "__main__":
    main()
