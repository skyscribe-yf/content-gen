#!/usr/bin/env bash
# C3 封面重制（作者反馈：封面文字小且拥挤）——9 字两行、大字号、疏字距、干净背景
cd "$(dirname "$0")"
source ~/.bash_env 2>/dev/null || true
python3 ../../scripts/yairouter_img.py --prompt "A cinematic wide banner, pure dark navy-black gradient background, clean and uncluttered, no light streaks, no extra decorative elements. Two short lines of very large, thick, bold golden Chinese characters centered horizontally across the full width. Line one: 你定的规矩 (five characters, extra large). Line two: 还剩几条？ (four characters plus question mark, extra large). Each character must be huge and chunky, roughly one ninth of the image height per line, with generous clear space above, below and between the two lines. Wide spacing between characters so they never feel cramped. Bright saturated gold fill with a soft glow, very high contrast against the dark background. Absolutely no other text, no letters, no numbers, no watermark, no human figures." --size 21:9 --output-dir . --filename 00-cover.png > /tmp/c3_cover_v2.log 2>&1
echo DONE > /tmp/c3_cover_v2_done
