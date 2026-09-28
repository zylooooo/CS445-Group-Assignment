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
seen_hashes=" "

for i in $(seq 1 "$LAST"); do
  url="${TEMPLATE//\{page\}/$i}"
  f="$OUT/${DATE}_page$(printf '%03d' "$i").html"
  ok=0
  for try in 1 2 3; do
    code=$(curl -s -L -c "$OUT/cookies.txt" -b "$OUT/cookies.txt" \
         --socks5-hostname 127.0.0.1:9050 --max-time 120 -o "$f" -w '%{http_code}' "$url")
    if [ "$code" = "200" ]; then ok=1; break; fi
    if [ "$code" = "404" ]; then ok=404; break; fi
    echo "page $i attempt $try failed (HTTP $code), retrying in 10s..."
    sleep 10
  done
  # Only a 404 means "past the last page". Any other error (5xx, timeout) is retried
  # and, if it persists, reported as a gap rather than mistaken for the end.
  if [ "$ok" = "404" ]; then echo "page $i is 404, reached the end"; rm -f "$f"; break; fi
  [ "$ok" -ne 1 ] && { echo "page $i failed 3 times, skipping (GAP: re-run later)"; rm -f "$f"; continue; }

  # Hash the marker lines only, so changing counters or timestamps elsewhere on the
  # page don't hide a repeat.
  if [ -n "$MARKER" ]; then
    hash=$(grep -F -A2 "$MARKER" "$f" | md5sum | cut -d' ' -f1)
  else
    hash=$(md5sum "$f" | cut -d' ' -f1)
  fi
  # Compare against every earlier page, not just the previous one: some sites wrap
  # back to page 1 past their last page.
  if [[ "$seen_hashes" == *" $hash "* ]]; then
    echo "page $i repeats an earlier page, reached the end"
    rm -f "$f"
    break
  fi
  seen_hashes+="$hash "

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
