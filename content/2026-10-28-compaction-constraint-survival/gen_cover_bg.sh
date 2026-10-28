#!/usr/bin/env bash
# C3 封面底图（无字）：深色干净背景，文字一律脚本叠
cd "$(dirname "$0")"
source ~/.bash_env 2>/dev/null || true
python3 ../../scripts/yairouter_img.py --prompt "A cinematic wide banner background, deep dark navy-blue gradient fading to near black at the edges, clean and uncluttered. Subtle faint server rack silhouettes and thin circuit line patterns in the distance, very dim, receding behind pure empty negative space in the center. No text, no letters, no numbers, no watermark, no human figures, no light streaks across the middle. The center of the frame must stay almost entirely empty dark space for a title overlay." --size 21:9 --output-dir . --filename 00-cover-bg.png > /tmp/c3_cover_bg.log 2>&1
echo DONE > /tmp/c3_cover_bg_done
