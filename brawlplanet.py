import gzip
import json
import os
import time
import urllib.parse

import requests

GCS_BASE = "https://storage.googleapis.com/brawlanalyzer-public"
CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache")
CACHE_TTL = 24 * 3600
HEADERS = {"User-Agent": "Mozilla/5.0 (BrawlStarsHelper/1.0)"}

TIERS = {
    "pl": "Diamond I+",
    "pl-m1": "Mythic I+",
    "pl-m3": "Mythic III+",
    "pl-l1": "Legendary I+",
}


def fetch_tier_results(tier="pl"):
    if tier not in TIERS:
        raise ValueError(f"Неизвестный тир: {tier}")
    path = os.path.join(CACHE_DIR, f"{tier}-results.json")
    if os.path.exists(path) and time.time() - os.path.getmtime(path) < CACHE_TTL:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    url = f"{GCS_BASE}/{tier}-results.json.gz"
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    try:
        data = json.loads(resp.content)
    except json.JSONDecodeError:
        data = json.loads(gzip.decompress(resp.content))
    os.makedirs(CACHE_DIR, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
    return data


def get_ranked_maps(tier="pl"):
    results = fetch_tier_results(tier)
    maps = []
    for slug, entry in results.items():
        if not entry.get("active"):
            continue
        image_key = slug.rsplit("_", 1)[0]
        maps.append(
            {
                "name": entry.get("map"),
                "mode": entry.get("modeFormatted") or entry.get("mode"),
                "slug": slug,
                "image": f"{GCS_BASE}/map_images/{urllib.parse.quote(image_key)}.png",
                "matchCount": entry.get("match_count"),
            }
        )
    maps.sort(key=lambda m: (m["mode"] or "", m["name"] or ""))
    return maps


def get_map_entry(tier, slug):
    results = fetch_tier_results(tier)
    entry = results.get(slug)
    if not entry:
        raise KeyError(f"Карта {slug} не найдена в тире {TIERS[tier]}")
    return entry


def stats_rows(entry):
    return [
        {"brawler": r["brawler"], "winRate": r["wr"], "pickRate": r["ur"], "starRate": r["sr"]}
        for r in entry.get("individual", [])
    ]