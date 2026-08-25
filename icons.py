import json
import os
import threading
import time

from upstream import get_json

BRAWLERS_URL = "https://api.brawlapi.com/v1/brawlers"
MODES_URL = "https://api.brawlapi.com/v1/gamemodes"
CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache")
CACHE_PATH = os.path.join(CACHE_DIR, "brawlers.json")
MODES_CACHE_PATH = os.path.join(CACHE_DIR, "modes.json")
TTL = 7 * 24 * 3600

_locks = {"brawlers": threading.Lock(), "modes": threading.Lock()}


def _load_cache(path: str) -> dict | None:
    if not os.path.exists(path):
        return None
    try:
        age = time.time() - os.path.getmtime(path)
    except OSError:
        return None
    if age >= TTL:
        return None
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def _save_cache_atomic(path: str, data: dict) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f)
    os.replace(tmp, path)


def _fetch_icon_map(url: str, name_key: str, url_key: str, list_key: str) -> dict:
    data = get_json(url)
    return {
        item[name_key].upper(): item[url_key] for item in data.get(list_key, [])
    }


def get_icon_map() -> dict[str, str]:
    with _locks["brawlers"]:
        cached: dict | None = _load_cache(CACHE_PATH)
        if cached is not None:
            return cached
        icon_map = _fetch_icon_map(BRAWLERS_URL, "name", "imageUrl2", "list")
        _save_cache_atomic(CACHE_PATH, icon_map)
        return icon_map


def get_mode_icon_map() -> dict[str, str]:
    with _locks["modes"]:
        cached: dict | None = _load_cache(MODES_CACHE_PATH)
        if cached is not None:
            return cached
        data = get_json(MODES_URL)
        icon_map = {m["scHash"]: m["imageUrl"] for m in data.get("list", [])}
        _save_cache_atomic(MODES_CACHE_PATH, icon_map)
        return icon_map
