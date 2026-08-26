import gzip
import json
import os
import threading
import time
import urllib.parse
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from icons import get_mode_icon_map
from upstream import head_ok_image, session

GCS_BASE = "https://storage.googleapis.com/brawlanalyzer-public"
CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache")
CACHE_TTL = 24 * 3600
IMAGE_WORKERS = 8

TIERS = {
    "pl": "Diamond I+",
    "pl-m1": "Mythic I+",
    "pl-m3": "Mythic III+",
    "pl-l1": "Legendary I+",
}

_file_locks: dict[str, threading.Lock] = {}
_locks_guard = threading.Lock()


def _lock_for(path: str) -> threading.Lock:
    with _locks_guard:
        lock = _file_locks.get(path)
        if lock is None:
            lock = threading.Lock()
            _file_locks[path] = lock
    return lock


def _read_json_cache(path: str) -> dict | None:
    try:
        age = time.time() - os.path.getmtime(path)
    except OSError:
        return None
    if age >= CACHE_TTL:
        return None
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def _write_json_atomic(path: str, data: Any) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
    os.replace(tmp, path)


def _fetch_tier_data(tier: str) -> dict:
    url = f"{GCS_BASE}/{tier}-results.json.gz"
    resp = session.get(url, timeout=30)
    resp.raise_for_status()
    try:
        data = json.loads(resp.content)
    except json.JSONDecodeError:
        data = json.loads(gzip.decompress(resp.content))
    return data


def fetch_tier_results(tier: str = "pl") -> dict:
    if tier not in TIERS:
        raise ValueError(f"Неизвестный тир: {tier}")
    path = os.path.join(CACHE_DIR, f"{tier}-results.json")
    with _lock_for(path):
        cached = _read_json_cache(path)
        if cached is not None:
            return cached
        data = _fetch_tier_data(tier)
        _write_json_atomic(path, data)
        return data


def _image_ok_path(tier: str) -> str:
    return os.path.join(CACHE_DIR, f"{tier}-images.json")


def _image_ok_map(tier: str) -> dict[str, bool]:
    cached = _read_json_cache(_image_ok_path(tier))
    return cached if isinstance(cached, dict) else {}


def _save_image_ok_map(tier: str, ok: dict[str, bool]) -> None:
    path = _image_ok_path(tier)
    with _lock_for(path):
        _write_json_atomic(path, ok)


def get_ranked_maps(tier: str = "pl") -> list[dict]:
    results = fetch_tier_results(tier)
    mode_icons = get_mode_icon_map()
    img_ok = _image_ok_map(tier)

    image_keys: list[str] = []
    for slug, entry in results.items():
        if entry.get("active"):
            image_key = slug.rsplit("_", 1)[0]
            if image_key not in image_keys:
                image_keys.append(image_key)

    def check(key: str) -> tuple[str, bool]:
        return key, head_ok_image(
            f"{GCS_BASE}/map_images/{urllib.parse.quote(key)}.png"
        )

    missing = [k for k in image_keys if k not in img_ok]
    changed = False
    if missing:
        with ThreadPoolExecutor(max_workers=IMAGE_WORKERS) as pool:
            for key, ok in pool.map(check, missing):
                img_ok[key] = ok
                changed = True

    maps = []
    for slug, entry in results.items():
        if not entry.get("active"):
            continue
        image_key = slug.rsplit("_", 1)[0]
        if not img_ok.get(image_key):
            continue
        mode_slug = entry.get("mode")
        maps.append(
            {
                "name": entry.get("map"),
                "mode": entry.get("modeFormatted") or mode_slug,
                "modeSlug": mode_slug,
                "modeIcon": mode_icons.get(mode_slug, ""),
                "slug": slug,
                "image": f"{GCS_BASE}/map_images/{urllib.parse.quote(image_key)}.png",
                "matchCount": entry.get("match_count"),
            }
        )
    if changed:
        _save_image_ok_map(tier, img_ok)
    maps.sort(key=lambda m: (m["mode"] or "", m["name"] or ""))
    return maps


def get_map_entry(tier: str, slug: str) -> dict:
    results = fetch_tier_results(tier)
    entry = results.get(slug)
    if not isinstance(entry, dict):
        raise KeyError(f"Карта {slug} не найдена в тире {TIERS[tier]}")
    return entry


def stats_rows(entry: dict) -> list[dict]:
    return [
        {
            "brawler": r["brawler"],
            "winRate": r["wr"],
            "pickRate": r["ur"],
            "starRate": r["sr"],
        }
        for r in entry.get("individual", [])
    ]
