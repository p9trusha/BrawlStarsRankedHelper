import os

from dotenv import load_dotenv
from flask import Flask, jsonify, request, send_from_directory

from brawlplanet import TIERS, get_map_entry, get_ranked_maps, stats_rows
from brawlstars_api import get_player_brawlers
from scoring import build_recommendations, league_icon_url, min_power_for

load_dotenv()

app = Flask(__name__, static_folder="static", static_url_path="/static")


def _tier():
    tier = request.args.get("tier", "pl")
    if tier not in TIERS:
        raise ValueError(f"Неизвестный тир: {tier}")
    return tier


@app.get("/api/ranked-maps")
def api_ranked_maps():
    try:
        tier = _tier()
        return jsonify(
            {
                "tier": tier,
                "tierName": TIERS[tier],
                "leagues": [
                    {"value": t, "name": TIERS[t], "icon": league_icon_url(t)}
                    for t in TIERS
                ],
                "maps": get_ranked_maps(tier),
            }
        )
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Brawl Planet: {e}"}), 502


@app.get("/api/map/<slug>/stats")
def api_map_stats(slug):
    try:
        tier = _tier()
        entry = get_map_entry(tier, slug)
        return jsonify(
            {
                "tier": tier,
                "tierName": TIERS[tier],
                "map": entry.get("map"),
                "mode": entry.get("modeFormatted") or entry.get("mode"),
                "matchCount": entry.get("match_count"),
                "individual": stats_rows(entry),
                "teams": entry.get("teams", []),
            }
        )
    except KeyError as e:
        return jsonify({"error": str(e)}), 404
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Brawl Planet: {e}"}), 502


@app.get("/api/player/<tag>")
def api_player(tag):
    try:
        return jsonify(get_player_brawlers(tag))
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Brawl Stars API: {e}"}), 502


@app.get("/api/recommend")
def api_recommend():
    slug = request.args.get("map", "")
    tag = request.args.get("tag", "")
    only_max = request.args.get("onlyMax", "1") != "0"
    if not slug or not tag:
        return jsonify({"error": "Укажи map и tag"}), 400
    try:
        tier = _tier()
        player = get_player_brawlers(tag)
        entry = get_map_entry(tier, slug)
        stats = stats_rows(entry)
        recs = build_recommendations(player["brawlers"], stats, tier, only_max)
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 400
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except KeyError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": f"Источник данных: {e}"}), 502
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
    return jsonify(
        {
            "player": player.get("name"),
            "map": entry.get("map"),
            "mode": entry.get("modeFormatted") or entry.get("mode"),
            "tier": tier,
            "tierName": TIERS[tier],
            "minPower": min_power_for(tier),
            "topWeak": top_weak,
            "recommendations": [{k: r.get(k) for k in keys} for r in recs],
        }
    )


@app.get("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="127.0.0.1", port=port, debug=False)
