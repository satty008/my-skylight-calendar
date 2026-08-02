#!/bin/sh
set -e
API_KEY=$(cat /config/.immich_api_key)
BASE_URL="https://immich.bhavibhavan.duckdns.org/api"
EXCLUDED_FILE="/config/.immich_excluded_assets.txt"

ASSET_ID=$(python3 - "$API_KEY" "$BASE_URL" "$EXCLUDED_FILE" <<'PYEOF'
import json
import sys
import urllib.request

api_key, base_url, excluded_file = sys.argv[1:4]

try:
    with open(excluded_file) as f:
        excluded = {line.strip() for line in f if line.strip()}
except FileNotFoundError:
    excluded = set()

for _ in range(3):
    req = urllib.request.Request(
        f"{base_url}/search/random",
        data=json.dumps({"type": "IMAGE", "size": 15, "visibility": "timeline"}).encode(),
        headers={"x-api-key": api_key, "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        candidates = json.load(resp)
    survivors = [a["id"] for a in candidates if a["id"] not in excluded]
    if survivors:
        print(survivors[0])
        break
else:
    # extremely unlikely fallback: accept whatever the last batch had
    if candidates:
        print(candidates[0]["id"])
PYEOF
)

if [ -z "$ASSET_ID" ]; then
  echo "No asset id resolved, aborting" >&2
  exit 1
fi

curl -s -H "x-api-key: $API_KEY" \
  "$BASE_URL/assets/$ASSET_ID/thumbnail?size=preview" \
  -o /config/www/immich_background.jpg.tmp

mv /config/www/immich_background.jpg.tmp /config/www/immich_background.jpg
