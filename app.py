import os

from dotenv import load_dotenv
from flask import Flask, jsonify, request, send_from_directory

from brawlplanet import TIERS, get_map_entry, get_ranked_maps, stats_rows
from brawlstars_api import get_player_brawlers

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
            {"tier": tier, "tierName": TIERS[tier], "maps": get_ranked_maps(tier)}
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
    if not slug or not tag:
        return jsonify({"error": "Укажи map и tag"}), 400
    try:
        tier = _tier()
        player = get_player_brawlers(tag)
        entry = get_map_entry(tier, slug)
        stats = stats_rows(entry)
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 400
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 502
    by_name = {s["brawler"].upper(): s for s in stats}
    recommendations = []
    for b in player["brawlers"]:
        s = by_name.get(b["name"].upper())
        if s:
            recommendations.append({**b, **s})
    recommendations.sort(key=lambda r: r["winRate"], reverse=True)
    return jsonify(
        {
            "player": player["name"],
            "map": slug,
            "tier": tier,
            "tierName": TIERS[tier],
            "recommendations": recommendations,
        }
    )


@app.get("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="127.0.0.1", port=port, debug=False)