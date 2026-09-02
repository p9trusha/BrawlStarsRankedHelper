import os
import threading
import urllib.parse
from typing import Any

from cachetools import TTLCache
from cachetools.keys import hashkey

from icons import get_icon_map
from scoring import rank_icon_url, tier_for_rank
from upstream import get_json

BASE = "https://api.brawlstars.com/v1"
PLAYER_TTL = 10 * 60
PLAYER_CACHE_MAXSIZE = 512

_PLAYER_CACHE: TTLCache[str, dict] = TTLCache(
    maxsize=PLAYER_CACHE_MAXSIZE, ttl=PLAYER_TTL
)
_CACHE_LOCK = threading.Lock()

TAG_ALPHABET = frozenset("0289OPYLQGRJCUV")


def normalize_tag(tag: str) -> str:
    clean = tag.strip().lstrip("#").replace(" ", "").upper()
    if not clean:
        raise RuntimeError("Укажи тег игрока, например #2PR8J29GL")
    if not (3 <= len(clean) <= 12):
        raise RuntimeError("Тег игрока должен быть длиной 3–12 символов.")
    invalid = set(clean) - TAG_ALPHABET
    if invalid:
        raise RuntimeError(
            "В теле тега недопустимые символы: "
            + ", ".join(sorted(invalid))
            + ". Разрешены только 0289PYLQGRJCUV."
        )
    return clean


def _cache_key(clean: str) -> Any:
    return hashkey(clean)


def get_player_brawlers(tag: str) -> dict:
    token = os.environ.get("BRAWL_STARS_TOKEN", "").strip()
    if not token:
        raise RuntimeError("BRAWL_STARS_TOKEN не задан. Впиши токен в файл .env")
    clean = normalize_tag(tag)
    with _CACHE_LOCK:
        cached = _PLAYER_CACHE.get(clean)
    if cached is not None:
        return cached
    url = BASE + "/players/" + urllib.parse.quote("#" + clean)
    auth = {"Authorization": "Bearer " + token}
    try:
        data = get_json(url, headers=auth)
    except Exception as e:
        status = getattr(getattr(e, "response", None), "status_code", None)
        if status == 404:
            raise RuntimeError("Игрок не найден. Проверь тег.") from e
        if status == 403:
            raise RuntimeError("Неверный или просроченный API-токен.") from e
        raise
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
    result: dict[str, Any] = {
        "name": data.get("name"),
        "tag": data.get("tag"),
        "brawlers": brawlers,
        "ranked": {
            "rank": data.get("rankedRank"),
            "name": data.get("rankedRankName"),
            "elo": data.get("rankedElo"),
            "icon": rank_icon_url(data.get("rankedRank")),
        },
        "recommendedTier": tier_for_rank(data.get("rankedRank")),
    }
    with _CACHE_LOCK:
        _PLAYER_CACHE[clean] = result
    return result
