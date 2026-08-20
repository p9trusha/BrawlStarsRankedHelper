import os
import urllib.parse

import requests

from icons import get_icon_map

BASE = "https://api.brawlstars.com/v1"


def get_player_brawlers(tag):
    token = os.environ.get("BRAWL_STARS_TOKEN", "").strip()
    if not token:
        raise RuntimeError("BRAWL_STARS_TOKEN не задан. Впиши токен в файл .env")
    clean = tag.strip().lstrip("#").replace(" ", "")
    if not clean:
        raise RuntimeError("Укажи тег игрока, например #8L2P9Q")
    url = BASE + "/players/" + urllib.parse.quote("#" + clean)
    resp = requests.get(url, headers={"Authorization": "Bearer " + token}, timeout=30)
    if resp.status_code == 404:
        raise RuntimeError("Игрок не найден. Проверь тег.")
    if resp.status_code == 403:
        raise RuntimeError("Неверный или просроченный API-токен.")
    resp.raise_for_status()
    data = resp.json()
    icon_map = get_icon_map()
    brawlers = []
    for b in data.get("brawlers", []):
        brawlers.append(
            {
                "name": b["name"],
                "power": b.get("power", 0),
                "trophies": b.get("trophies", 0),
                "rank": b.get("rank", 0),
                "icon": icon_map.get(b["name"].upper(), ""),
            }
        )
    return {"name": data.get("name"), "tag": data.get("tag"), "brawlers": brawlers}