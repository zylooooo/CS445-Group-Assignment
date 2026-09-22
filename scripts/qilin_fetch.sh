#!/usr/bin/env bash
# Fetch Qilin DLS listing pages through Tor.
# Usage: ./qilin_fetch.sh "http://YOUR_MIRROR.onion" 60
BASE="${1%/}"
LAST="${2:-60}"
DATE=$(date +%F)
OUT=~/dls/raw/Qilin
mkdir -p "$OUT"

for i in $(seq 1 "$LAST"); do
  f="$OUT/${DATE}_onion_page$(printf '%03d' "$i").html"
  ok=0
  for try in 1 2 3; do
    if curl -s --socks5-hostname 127.0.0.1:9050 --max-time 120 -o "$f" "$BASE/?page=$i"; then
      ok=1; break
    fi
    echo "page $i attempt $try failed, retrying in 10s..."
    sleep 10
  done
  if [ "$ok" -ne 1 ]; then echo "page $i failed 3 times, skipping"; continue; fi

  n=$(grep -c "item_box-title" "$f")
  echo "page $i: $(wc -c < "$f") bytes, $n victims"
  if [ "$n" -eq 0 ]; then
    echo "page $i has no victims, reached the end of the archive"
    rm -f "$f"
    break
  fi
  sleep $((3 + RANDOM % 5))
done

echo "done. next: source ~/dls/venv/bin/activate && python3 qilin_parse.py $OUT/*onion_page*.html -o ~/dls/raw/Qilin/qilin.csv"
