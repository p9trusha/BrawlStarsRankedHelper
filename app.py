import logging
import os
from collections.abc import Callable
from typing import Any

from dotenv import load_dotenv
from flask import Flask, jsonify, request, send_from_directory
from werkzeug.exceptions import HTTPException

from brawlplanet import TIERS, get_map_entry, get_ranked_maps, stats_rows
from brawlstars_api import get_player_brawlers
from ratelimit import rate_limited
from scoring import (
    build_ban_recommendations,
    build_recommendations,
    league_icon_url,
    min_power_for,
)

load_dotenv()

STATIC_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "static"
)
app = Flask(__name__, static_folder=STATIC_DIR, static_url_path="/static")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
log = logging.getLogger("bsh")


class ApiError(Exception):
    def __init__(self, message: str, status: int = 400) -> None:
        super().__init__(message)
        self.status = status


def _tier() -> str:
    tier = request.args.get("tier", "pl")
    if tier not in TIERS:
        raise ValueError(f"Неизвестный тир: {tier}")
    return tier


def guarded(source: str, fn: Callable[[], Any]) -> Any:
    try:
        return fn()
    except (HTTPException, ValueError, RuntimeError, KeyError):
        raise
    except Exception as e:
        raise ApiError(f"{source}: {e}", 502) from e


@app.errorhandler(ApiError)
def handle_api_error(e: ApiError):
    if e.status >= 500:
        log.error("upstream error: %s", e)
    return jsonify({"error": str(e)}), e.status


@app.errorhandler(ValueError)
def handle_value_error(e: ValueError):
    return jsonify({"error": str(e)}), 400


@app.errorhandler(RuntimeError)
def handle_runtime_error(e: RuntimeError):
    return jsonify({"error": str(e)}), 400


@app.errorhandler(KeyError)
def handle_key_error(e: KeyError):
    return jsonify({"error": str(e).strip("'")}), 404


@app.errorhandler(HTTPException)
def handle_http_exception(e: HTTPException):
    return jsonify({"error": e.description}), e.code


@app.errorhandler(Exception)
def handle_unexpected(e: Exception):
    log.exception("unhandled error")
    return jsonify({"error": "Внутренняя ошибка сервера."}), 500


@app.get("/api/ranked-maps")
@rate_limited
def api_ranked_maps():
    tier = _tier()

    def compute() -> dict:
        return {
            "tier": tier,
            "tierName": TIERS[tier],
            "leagues": [
                {"value": t, "name": TIERS[t], "icon": league_icon_url(t)}
                for t in TIERS
            ],
            "maps": get_ranked_maps(tier),
        }

    return jsonify(guarded("Brawl Planet", compute))


@app.get("/api/map/<slug>/stats")
@rate_limited
def api_map_stats(slug: str):
    tier = _tier()

    def compute() -> dict:
        entry = get_map_entry(tier, slug)
        return {
            "tier": tier,
            "tierName": TIERS[tier],
            "map": entry.get("map"),
            "mode": entry.get("modeFormatted") or entry.get("mode"),
            "matchCount": entry.get("match_count"),
            "individual": stats_rows(entry),
            "teams": entry.get("teams", []),
        }

    return jsonify(guarded("Brawl Planet", compute))


@app.get("/api/player/<tag>")
@rate_limited
def api_player(tag: str):
    return jsonify(guarded("Brawl Stars API", lambda: get_player_brawlers(tag)))


@app.get("/api/recommend")
@rate_limited
def api_recommend():
    slug = request.args.get("map", "")
    tag = request.args.get("tag", "")
    only_max = request.args.get("onlyMax", "1") != "0"
    if not slug or not tag:
        return jsonify({"error": "Укажи map и tag"}), 400
    tier = _tier()

    def compute() -> dict:
        player = get_player_brawlers(tag)
        entry = get_map_entry(tier, slug)
        stats = stats_rows(entry)
        recs = build_recommendations(player["brawlers"], stats, tier, only_max)
        top_weak = bool(recs) and (recs[0].get("winRate") or 0) < 50
        keys = (
            "name",
            "icon",
            "power",
            "rank",
            "trophies",
            "winRate",
            "pickRate",
            "starRate",
            "score",
        )
        return {
            "player": player.get("name"),
            "map": entry.get("map"),
            "mode": entry.get("modeFormatted") or entry.get("mode"),
            "tier": tier,
            "tierName": TIERS[tier],
            "minPower": min_power_for(tier),
            "topWeak": top_weak,
            "recommendations": [{k: r.get(k) for k in keys} for r in recs],
        }

    return jsonify(guarded("Источник данных", compute))


@app.get("/api/ban-recommend")
@rate_limited
def api_ban_recommend():
    slug = request.args.get("map", "")
    tag = request.args.get("tag", "")
    if not slug or not tag:
        return jsonify({"error": "Укажи map и tag"}), 400
    tier = _tier()

    def compute() -> dict:
        player = get_player_brawlers(tag)
        entry = get_map_entry(tier, slug)
        stats = stats_rows(entry)
        recs = build_ban_recommendations(player["brawlers"], stats, tier)
        keys = (
            "name",
            "icon",
            "power",
            "trophies",
            "winRate",
            "pickRate",
            "score",
            "locked",
        )
        return {
            "player": player.get("name"),
            "map": entry.get("map"),
            "mode": entry.get("modeFormatted") or entry.get("mode"),
            "tier": tier,
            "tierName": TIERS[tier],
            "minPower": min_power_for(tier),
            "recommendations": [{k: r.get(k) for k in keys} for r in recs],
        }

    return jsonify(guarded("Источник данных", compute))


@app.get("/")
def index():
    return send_from_directory(STATIC_DIR, "index.html")


@app.get("/health")
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="127.0.0.1", port=port, debug=False)
