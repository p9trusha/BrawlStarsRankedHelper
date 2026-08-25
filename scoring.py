MIN_POWER = {"pl": 9}
WR_SHRINK_K = 8


def min_power_for(tier):
    return MIN_POWER.get(tier, 11)


def tier_for_rank(rank):
    try:
        r = int(rank)
    except (TypeError, ValueError):
        r = 0
    if r >= 16:
        return "pl-l1"
    if r == 15:
        return "pl-m3"
    if r >= 13:
        return "pl-m1"
    return "pl"


def _norm(v, lo, hi):
    return (v - lo) / (hi - lo) * 100 if hi > lo else 50.0


def build_recommendations(player_brawlers, stats, tier, only_max=True):
    min_power = min_power_for(tier)
    by_name = {s["brawler"].upper(): s for s in stats}
    tmax = max([b.get("trophies") or 0 for b in player_brawlers] + [1])
    pool = []
    for b in player_brawlers:
        if only_max and (b.get("power") or 0) < min_power:
            continue
        s = by_name.get((b.get("name") or "").upper())
        if not s:
            continue
        wr = s.get("winRate") or 0
        pr = s.get("pickRate") or 0
        pool.append(
            {
                **b,
                **s,
                "tp": min((b.get("trophies") or 0) / tmax * 100, 100),
                "wrAdj": 50 + (wr - 50) * pr / (pr + WR_SHRINK_K),
            }
        )
    if not pool:
        return []
    ranges = {}
    for key in ("wrAdj", "tp"):
        vals = [r[key] for r in pool]
        ranges[key] = (min(vals), max(vals))
    for r in pool:
        r["score"] = round(
            0.7 * _norm(r["wrAdj"], *ranges["wrAdj"])
            + 0.3 * _norm(r["tp"], *ranges["tp"]),
            1,
        )
    pool.sort(key=lambda r: r["score"], reverse=True)
    return pool
