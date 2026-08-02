#!/usr/local/bin/python3
"""Rebuilds /config/.immich_excluded_assets.txt: one asset ID per line, for
every asset belonging to any album whose (normalized) name matches the
blacklist below. Run periodically since album membership changes over time.
"""
import json
import re
import urllib.request

BASE_URL = "https://immich.bhavibhavan.duckdns.org/api"
with open("/config/.immich_api_key") as f:
    API_KEY = f.read().strip()

BLACKLIST = [
    "Mental Health", "Camera", "Screenshots", "Priya Doctor",
    "Fitness & Nutrition", "Relatives", "Doggo Walking", "Docs",
    "Whatsapp Images", "ID_Certificate", "Medical", "Satty Doc", "Reddit",
    "Work", "Whatsapp", "Body Pics", "Amarante_6_1202", "Nike Run Club",
    "WhatsApp Business", "Haircut", "AdobeLightroom", "Sent", "Private",
    "Documents", "Amma", "Splendid Logo Maker", "Whatsapp Video", "Temp",
]


def normalize(name):
    # strip emoji/symbols, collapse whitespace, lowercase - so cosmetic
    # differences like "Doggo Walking \U0001F415" or a trailing space still match
    stripped = re.sub(r"[^\w &]+", "", name, flags=re.UNICODE)
    return re.sub(r"\s+", " ", stripped).strip().lower()


NORMALIZED_BLACKLIST = {normalize(n) for n in BLACKLIST}


def api_get(path):
    req = urllib.request.Request(f"{BASE_URL}{path}", headers={"x-api-key": API_KEY})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def api_post(path, body):
    req = urllib.request.Request(
        f"{BASE_URL}{path}",
        data=json.dumps(body).encode(),
        headers={"x-api-key": API_KEY, "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def is_blacklisted(album_name):
    normalized = normalize(album_name)
    return any(normalized.startswith(term) for term in NORMALIZED_BLACKLIST)


def album_asset_ids(album_id):
    ids = set()
    page = 1
    while page is not None:
        result = api_post(
            "/search/metadata", {"albumIds": [album_id], "size": 1000, "page": page}
        )["assets"]
        ids |= {a["id"] for a in result["items"]}
        page = result.get("nextPage")
    return ids


def main():
    albums = api_get("/albums")
    matched = [a for a in albums if is_blacklisted(a["albumName"])]

    matched_normalized_prefixes = set()
    for a in matched:
        n = normalize(a["albumName"])
        matched_normalized_prefixes |= {t for t in NORMALIZED_BLACKLIST if n.startswith(t)}
    unmatched = NORMALIZED_BLACKLIST - matched_normalized_prefixes
    if unmatched:
        print(f"WARNING: no album matched for: {unmatched}")

    excluded_ids = set()
    for album in matched:
        ids = album_asset_ids(album["id"])
        excluded_ids |= ids
        print(f"{album['albumName']}: {len(ids)} assets")

    with open("/config/.immich_excluded_assets.txt", "w") as f:
        f.write("\n".join(sorted(excluded_ids)))

    print(f"Total excluded: {len(excluded_ids)} assets from {len(matched)} albums")


if __name__ == "__main__":
    main()
