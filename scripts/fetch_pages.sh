#!/usr/bin/env bash
# Generic paged fetcher through Tor, with cookie jar, polite pauses, and
# repeat detection so it stops when a site recycles content past its last page.
# Usage: fetch_pages.sh "URL_TEMPLATE_CONTAINING_{page}" OUTDIR MAXPAGES MARKER
#
# The URL template must point at a CURRENT mirror, which you must source yourself:
# leak sites rotate mirrors constantly, so none is shipped with this repository.
# See the "Finding a working mirror" section of the README.
#
# Examples:
#   fetch_pages.sh "http://<mirror>.onion/index.php?page={page}" ~/dls/raw/Play 40 "viewtopic("
#   fetch_pages.sh "http://<mirror>.onion/?page={page}" ~/dls/raw/SafePay 120 "card-title"
TEMPLATE="$1"
OUT="${2:?output dir required}"
LAST="${3:-60}"
MARKER="${4:-}"
DATE=$(date +%F)
mkdir -p "$OUT"
prev=""

for i in $(seq 1 "$LAST"); do
  url="${TEMPLATE//\{page\}/$i}"
  f="$OUT/${DATE}_page$(printf '%03d' "$i").html"
  ok=0
  for try in 1 2 3; do
    if curl -s -L -c "$OUT/cookies.txt" -b "$OUT/cookies.txt" \
         --socks5-hostname 127.0.0.1:9050 --max-time 120 -o "$f" "$url"; then
      ok=1; break
    fi
    echo "page $i attempt $try failed, retrying in 10s..."
    sleep 10
  done
  [ "$ok" -ne 1 ] && { echo "page $i failed 3 times, skipping"; continue; }

  hash=$(md5sum "$f" | cut -d' ' -f1)
  if [ "$hash" = "$prev" ]; then
    echo "page $i is identical to the previous page, reached the end"
    rm -f "$f"
    break
  fi
  prev="$hash"

  if [ -n "$MARKER" ]; then
    n=$(grep -c "$MARKER" "$f")
    echo "page $i: $(wc -c < "$f") bytes, $n entries"
    if [ "$n" -eq 0 ]; then
      echo "page $i has no entries, reached the end"
      rm -f "$f"
      break
    fi
  else
    echo "page $i: $(wc -c < "$f") bytes"
  fi
  sleep $((3 + RANDOM % 5))
done
echo "done."
