#!/usr/bin/env bash
# mass_check.sh
# Usage: bash mass_check.sh domains.txt
# domains.txt should contain one URL per line (you provided list)

set -euo pipefail
DOMFILE=${1:-domains.txt}
OUTDIR="scans"
mkdir -p "$OUTDIR"

# helper to extract host from URL
host_from_url() {
  url="$1"
  # remove protocol
  h=${url#*://}
  # cut after first slash
  h=${h%%/*}
  echo "$h"
}

while IFS= read -r url || [ -n "$url" ]; do
  [ -z "$url" ] && continue
  host=$(host_from_url "$url")
  echo ">> Scanning $host"
  ddir="$OUTDIR/$host"
  mkdir -p "$ddir"

  # dig A
  echo ">>> dig A @8.8.8.8" > "$ddir/dig_A.txt"
  dig @8.8.8.8 "$host" A +noall +answer >> "$ddir/dig_A.txt" 2>&1 || true

  # dig CNAME
  echo ">>> dig CNAME @1.1.1.1" > "$ddir/dig_CNAME.txt"
  dig @1.1.1.1 "$host" CNAME +noall +answer >> "$ddir/dig_CNAME.txt" 2>&1 || true

  # dig +trace (may be verbose)
  echo ">>> dig +trace" > "$ddir/dig_trace.txt"
  dig +trace "$host" >> "$ddir/dig_trace.txt" 2>&1 || true

  # curl headers HTTP/1.1 (with timeout)
  echo ">>> curl -I --http1.1 -vk" > "$ddir/curl_headers.txt"
  timeout 15 curl -I --http1.1 -vk "https://$host/" >> "$ddir/curl_headers.txt" 2>&1 || true

  # openssl s_client (brief)
  echo ">>> openssl s_client -servername" > "$ddir/openssl.txt"
  timeout 10 bash -c "echo | openssl s_client -connect $host:443 -servername $host 2>&1 | sed -n '1,120p'" >> "$ddir/openssl.txt" || true

  # Optional: websocat test (only if websocat installed)
  if command -v websocat >/dev/null 2>&1; then
    echo ">>> websocat test (10s attempt)" > "$ddir/websocat.txt"
    timeout 10 websocat -v -H="Origin: https://gitlab.com" "wss://$host/" >> "$ddir/websocat.txt" 2>&1 || true
  fi

  echo ">> Done $host"
done < "$DOMFILE"

echo "All scans saved under $OUTDIR/"
