import json
import os
import time

import requests

BRAWLERS_URL = "https://api.brawlapi.com/v1/brawlers"
MODES_URL = "https://api.brawlapi.com/v1/gamemodes"
CACHE_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "cache", "brawlers.json"
)
MODES_CACHE_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "cache", "modes.json"
)
TTL = 7 * 24 * 3600
HEADERS = {"User-Agent": "Mozilla/5.0 (BrawlStarsHelper/1.0)"}


def get_icon_map():
    if os.path.exists(CACHE_PATH) and time.time() - os.path.getmtime(CACHE_PATH) < TTL:
        with open(CACHE_PATH, encoding="utf-8") as f:
            return json.load(f)
    resp = requests.get(BRAWLERS_URL, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    icon_map = {b["name"].upper(): b["imageUrl2"] for b in data.get("list", [])}
    os.makedirs(os.path.dirname(CACHE_PATH), exist_ok=True)
    with open(CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(icon_map, f)
    return icon_map


def get_mode_icon_map():
    if (
        os.path.exists(MODES_CACHE_PATH)
        and time.time() - os.path.getmtime(MODES_CACHE_PATH) < TTL
    ):
        with open(MODES_CACHE_PATH, encoding="utf-8") as f:
            return json.load(f)
    resp = requests.get(MODES_URL, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    icon_map = {m["scHash"]: m["imageUrl"] for m in data.get("list", [])}
    os.makedirs(os.path.dirname(MODES_CACHE_PATH), exist_ok=True)
    with open(MODES_CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(icon_map, f)
    return icon_map
