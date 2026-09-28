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
    code=$(curl -s --socks5-hostname 127.0.0.1:9050 --max-time 120 -o "$f" -w '%{http_code}' "$BASE/?page=$i")
    if [ "$code" = "200" ]; then ok=1; break; fi
    if [ "$code" = "404" ]; then ok=404; break; fi
    echo "page $i attempt $try failed (HTTP $code), retrying in 10s..."
    sleep 10
  done
  # Only a 404 means "past the last page". Any other error (5xx, timeout) is retried
  # and, if it persists, reported as a gap rather than mistaken for the end.
  if [ "$ok" = "404" ]; then echo "page $i is 404, reached the end"; rm -f "$f"; break; fi
  if [ "$ok" -ne 1 ]; then echo "page $i failed 3 times, skipping (GAP: re-run later)"; rm -f "$f"; continue; fi

  n=$(grep -c "item_box-title" "$f")
  echo "page $i: $(wc -c < "$f") bytes, $n victims"
  if [ "$n" -eq 0 ]; then
    echo "page $i has no victims, reached the end of the archive"
    rm -f "$f"
    break
  fi
  # Past its last page Qilin keeps serving that page again, with changing counters,
  # so compare the victim titles rather than the raw bytes.
  sig=$(grep -o 'item_box-title[^<]*<[^>]*>[^<]*' "$f" | md5sum | cut -d' ' -f1)
  if [ "$sig" = "${prev_sig:-}" ]; then
    echo "page $i repeats the previous page's victims, reached the end of the archive"
    rm -f "$f"
    break
  fi
  prev_sig="$sig"
  sleep $((3 + RANDOM % 5))
done

echo "done. next: python3 scripts/qilin_parse.py $OUT/*onion_page*.html -o ~/dls/raw/Qilin/qilin.csv"
