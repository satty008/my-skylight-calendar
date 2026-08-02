#!/bin/sh
set -e
API_KEY=$(cat /config/.immich_api_key)
BASE_URL="https://immich.bhavibhavan.duckdns.org/api"

ASSET_ID=$(curl -s -H "x-api-key: $API_KEY" -H "Content-Type: application/json" \
  -X POST "$BASE_URL/search/random" -d '{"type":"IMAGE","size":1,"visibility":"timeline"}' \
  | python3 -c "import json,sys; print(json.load(sys.stdin)[0]['id'])")

curl -s -H "x-api-key: $API_KEY" \
  "$BASE_URL/assets/$ASSET_ID/thumbnail?size=preview" \
  -o /config/www/immich_background.jpg.tmp

mv /config/www/immich_background.jpg.tmp /config/www/immich_background.jpg
