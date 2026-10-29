#!/bin/bash
# 编码成片：逐帧 JPEG + 音轨 → H.264 MP4
# 用法：bash encode.sh <帧目录> <音轨> <输出.mp4> [fps]
set -e
DIR="${1:-frames}"
AUD="${2:-assets/mix.m4a}"
OUT="${3:-成片.mp4}"
FPS="${4:-30}"

N=$(ls "$DIR"/*.jpg 2>/dev/null | wc -l)
echo "frames: $N"
[ "$N" -lt 10 ] && { echo "帧数不足"; exit 2; }

ffmpeg -y -hide_banner -loglevel warning -stats \
  -framerate "$FPS" -i "$DIR/f_%05d.jpg" \
  -i "$AUD" \
  -c:v libx264 -preset slow -crf 17 \
  -pix_fmt yuv420p -profile:v high -level 4.2 \
  -x264-params "keyint=60:min-keyint=30:scenecut=0" \
  -color_primaries bt709 -color_trc bt709 -colorspace bt709 \
  -c:a aac -b:a 192k -ar 48000 \
  -shortest -movflags +faststart \
  "$OUT"

ffprobe -v error -show_entries format=duration,size,bit_rate -of default=nw=1 "$OUT"

# 换轨（不重渲画面）：两分钟
# ffmpeg -y -i old.mp4 -i new-mix.m4a -map 0:v -map 1:a \
#   -c:v copy -c:a aac -b:a 192k -ar 48000 -shortest -movflags +faststart out.mp4
