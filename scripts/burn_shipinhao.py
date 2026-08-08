#!/usr/bin/env python3
"""Gemini Notebook 视频 → 视频号成品一键烧录（去 logo + 锐化 + 字幕 + 片尾关注卡）

用法（推荐，全自动检测 logo 和片尾）:
    python3 scripts/burn_shipinhao.py video.mp4 sub.srt \
        --auto-logo --auto-end-cut \
        --out "content/2026-XX-XX-主题/shipinhao/成品.mp4"

手动指定（检测失败时兜底）:
    python3 scripts/burn_shipinhao.py video.mp4 sub.srt \
        --logo-x 1105 --logo-y 658 --logo-w 130 --logo-h 24 \
        --end-cut 487 --out 成品.mp4

要点（踩坑固化）:
- 滤镜顺序必须是 delogo → unsharp → subtitles（delogo 在字幕前，否则会模糊字幕）
- delogo 区域必须精确覆盖 logo（过大产生插值涂抹）
- Noto Sans CJK 字体度量使 libass 字号放大 ~1.7x，FontSize=13 ≈ 实际 21px
- --end-cut 必须早于 Gemini 品牌页淡入点，否则品牌页闪现
- 静态内容 x264 拒绝高码率，用 CRF 11 + slow + tune grain + qpmin=0 + unsharp
"""
import argparse
import io
import subprocess
import sys

import numpy as np
from PIL import Image

FONT = subprocess.run(["fc-match", "-f", "%{file}", "Noto Sans CJK SC"],
                      capture_output=True, text=True).stdout.strip()
STYLE = ("FontName=Noto Sans CJK SC,FontSize=13,PrimaryColour=&H0000FFFF,"
         "OutlineColour=&H00000000,BorderStyle=1,Outline=2,MarginV=8")
# (文字, 字号, 颜色, y) —— 1280x720 布局
CARD_TEXT = [
    ("关注「数解AI」", 76, "white", 270),
    ("公众号 · 视频号 同步更新", 42, "0xE8C547", 390),
    ("训练回路系列 · 持续更新", 30, "0x9AA5B1", 470),
]
PAD_X, PAD_Y = 7, 4   # delogo 区域相对文字 bbox 的 padding


def grab(video, t):
    p = subprocess.run(["ffmpeg", "-loglevel", "error", "-ss", str(t), "-i", video,
                        "-vframes", "1", "-f", "image2pipe", "-vcodec", "png", "-"],
                       capture_output=True)
    if p.returncode != 0 or not p.stdout:
        return None
    return np.array(Image.open(io.BytesIO(p.stdout)).convert("L")).astype(int)


def detect_logo(video, samples=(0.2, 0.5, 0.8)):
    """右下角水印检测：抽 3 帧多数投票（水印位置固定，插图各帧不同被剔除），
    再以中位数阈值剥离点阵网格噪点，返回 delogo 区域（含 padding）"""
    import subprocess as sp
    dur = float(sp.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "csv=p=0", video], capture_output=True, text=True).stdout)
    regs, h, w = [], 0, 0
    for frac in samples:
        im = grab(video, dur * frac)
        if im is None:
            sys.exit(f"自动检测 logo 失败：t={dur * frac:.1f}s 抽帧失败")
        h, w = im.shape
        # 右下角候选区（排除右缘 UI 竖条、底部边缘线）
        regs.append(im[h - 95:h - 3, w - 300:w - 20])
    # 多数投票：水印位置固定但部分页面形状不同（Gemini/HunYuan），
    # 严格交集会失败；取 ≥2 帧同位置暗像素即可保留公共水印主体
    common = sum((r < 180).astype(int) for r in regs) >= 2
    # 行投影：网格点每行只有几个孤立暗点，水印行显著更多；中位数即网格基线
    rowsum = common.sum(axis=1)
    med = float(np.median(rowsum))
    rows = np.where(rowsum > med * 2 + 5)[0]
    if len(rows) == 0:
        sys.exit("自动检测 logo 失败：交集后无文字行，请手动 --logo-x/y/w/h")
    groups, s = [], rows[0]
    for i in range(1, len(rows)):
        if rows[i] - rows[i - 1] > 2:
            groups.append((s, rows[i - 1])); s = rows[i]
    groups.append((s, rows[-1]))
    # 取暗像素最多的连续带（水印主体；插图残留/竖条是次要带）
    y0, y1 = max(groups, key=lambda g: rowsum[g[0]:g[1] + 1].sum())
    colsum = common[y0:y1 + 1, :].sum(axis=0)
    medc = float(np.median(colsum))
    # 列检测：阈值已滤掉网格噪点，取 min..max（文字笔画间隙无需分组）
    cols = np.where(colsum > medc * 2 + 5)[0]
    if len(cols) == 0:
        sys.exit("自动检测 logo 失败：交集后无文字列，请手动 --logo-x/y/w/h")
    x0, x1 = cols.min(), cols.max()
    return int(w - 300 + x0 - PAD_X), int(h - 95 + y0 - PAD_Y), \
           int(x1 - x0 + 1 + 2 * PAD_X), int(y1 - y0 + 1 + 2 * PAD_Y)


def detect_end_cut(video):
    """片尾品牌页探测：从尾部向前找最后一个非品牌页帧（品牌页=纯白屏+中央小 logo）"""
    import subprocess as sp
    dur = float(sp.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "csv=p=0", video], capture_output=True, text=True).stdout)
    last_content = None
    t = dur - 0.4
    while t > dur - 15 and t > 0:          # 只查最后 15 秒
        im = grab(video, t)
        if im is None:
            t -= 0.2
            continue
        white = (im > 230).mean()
        center = (im[300:420, 500:780] < 150).sum()
        if white < 0.95:                   # 内容页（品牌页白屏 >0.97）
            last_content = t
            break
        t -= 0.2
    if last_content is None:
        sys.exit("自动探测片尾失败：尾部 15 秒全是白屏（无内容页），请手动 --end-cut 或 --end-cut 0")
    return round(last_content - 0.3, 1)   # 回退 0.3s 保险，避免 -ss 抽帧误差把淡入帧算进内容


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video", help="Gemini Notebook 下载的视频")
    ap.add_argument("srt", help="校对后的 SRT（路径避免冒号/逗号）")
    ap.add_argument("--out", required=True)
    ap.add_argument("--auto-logo", action="store_true", help="自动检测右下角 Gemini logo")
    ap.add_argument("--logo-x", type=int, default=0, help="手动：logo 区域 x")
    ap.add_argument("--logo-y", type=int, default=0, help="手动：logo 区域 y")
    ap.add_argument("--logo-w", type=int, default=0, help="手动：logo 区域宽")
    ap.add_argument("--logo-h", type=int, default=0, help="手动：logo 区域高")
    ap.add_argument("--auto-end-cut", action="store_true", help="自动探测片尾品牌页起点")
    ap.add_argument("--end-cut", type=float, default=0,
                    help="手动：片尾截断点（秒），早于品牌页淡入点；0=不替换片尾")
    ap.add_argument("--end-card", type=float, default=3.0, help="关注卡时长（秒）")
    ap.add_argument("--crf", type=int, default=11)
    ap.add_argument("--preset", default="slow")
    args = ap.parse_args()

    if args.auto_logo:
        lx, ly, lw, lh = detect_logo(args.video)
        print(f"自动检测 logo: x={lx} y={ly} w={lw} h={lh}")
    elif args.logo_w > 0:
        lx, ly, lw, lh = args.logo_x, args.logo_y, args.logo_w, args.logo_h
    else:
        sys.exit("必须提供 --auto-logo 或 --logo-x/y/w/h")

    if args.auto_end_cut:
        cut = detect_end_cut(args.video)
        print(f"自动探测片尾: 品牌页从 {cut}s 开始，截断点取 {cut}s")
    else:
        cut = args.end_cut

    vf = (f"delogo=x={lx}:y={ly}:w={lw}:h={lh},"
          f"unsharp=5:5:0.4:5:5:0.0,"
          f"subtitles={args.srt}:force_style='{STYLE}'")

    vcodec = ["-c:v", "libx264", "-crf", str(args.crf), "-preset", args.preset,
              "-x264-params", "qpmin=0", "-tune", "grain"]

    if cut > 0:
        draws = ",".join(
            f"drawtext=fontfile={FONT}:text='{t}':fontsize={s}:fontcolor={c}:x=(w-text_w)/2:y={y}"
            for t, s, c, y in CARD_TEXT)
        fc = (f"[0:v]{vf},trim=end={cut},setpts=PTS-STARTPTS[v0];"
              f"[0:a]atrim=end={cut},asetpts=PTS-STARTPTS[a0];"
              f"[1:v]{draws}[v1];"
              f"[v0][a0][v1][2:a]concat=n=2:v=1:a=1[v][a]")
        cmd = ["ffmpeg", "-y", "-loglevel", "error", "-i", args.video,
               "-f", "lavfi", "-i", f"color=c=0x16213E:s=1280x720:r=24:d={args.end_card}",
               "-f", "lavfi", "-i", f"anullsrc=r=44100:cl=mono:d={args.end_card}",
               "-filter_complex", fc, "-map", "[v]", "-map", "[a]",
               *vcodec, "-c:a", "aac", "-b:a", "128k", args.out]
    else:
        cmd = ["ffmpeg", "-y", "-loglevel", "error", "-i", args.video, "-vf", vf,
               *vcodec, "-c:a", "copy", args.out]

    subprocess.run(cmd, check=True)
    print(f"完成: {args.out}")


if __name__ == "__main__":
    main()
