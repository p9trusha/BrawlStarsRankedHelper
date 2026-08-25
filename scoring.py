from typing import Any

MIN_POWER = {"pl": 9}
WR_SHRINK_K = 8
BAN_WR_WEIGHT = 0.4
BAN_PR_WEIGHT = 0.3
BAN_TP_WEIGHT = 0.2
BAN_LOCKED_BONUS = 25
RANK_ICON_BASE = "https://cdn.brawlify.com/ranked/tiered"
LEAGUE_ENTRY_RANK = {"pl": 10, "pl-m1": 13, "pl-m3": 15, "pl-l1": 16}


def min_power_for(tier: str) -> int:
    return MIN_POWER.get(tier, 11)


def tier_for_rank(rank: Any) -> str:
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


def rank_icon_url(rank: Any) -> str:
    try:
        r = int(rank)
    except (TypeError, ValueError):
        return ""
    return f"{RANK_ICON_BASE}/{58000000 + r - 1}.png" if r >= 1 else ""


def league_icon_url(tier: str) -> str:
    r = LEAGUE_ENTRY_RANK.get(tier)
    if not r:
        return ""
    return f"{RANK_ICON_BASE}/{58000000 + r - 1}.png"


def _norm(v: float, lo: float, hi: float) -> float:
    return (v - lo) / (hi - lo) * 100 if hi > lo else 50.0


def build_recommendations(
    player_brawlers: list[dict],
    stats: list[dict],
    tier: str,
    only_max: bool = True,
) -> list[dict]:
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
    ranges: dict[str, tuple[float, float]] = {}
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


def build_ban_recommendations(
    player_brawlers: list[dict], stats: list[dict], tier: str
) -> list[dict]:
    min_power = min_power_for(tier)
    by_name = {s["brawler"].upper(): s for s in stats}
    tmax = max([b.get("trophies") or 0 for b in player_brawlers] + [1])
    pool = []
    for b in player_brawlers:
        s = by_name.get((b.get("name") or "").upper())
        if not s:
            continue
        wr = s.get("winRate") or 0
        pr = s.get("pickRate") or 0
        locked = (b.get("power") or 0) < min_power
        pool.append(
            {
                **b,
                **s,
                "pickRate": pr,
                "tp": min((b.get("trophies") or 0) / tmax * 100, 100),
                "wrAdj": 50 + (wr - 50) * pr / (pr + WR_SHRINK_K),
                "locked": locked,
            }
        )
    if not pool:
        return []
    ranges: dict[str, tuple[float, float]] = {}
    for key in ("wrAdj", "pickRate", "tp"):
        vals = [r[key] for r in pool]
        ranges[key] = (min(vals), max(vals))
    for r in pool:
        score = (
            BAN_WR_WEIGHT * _norm(r["wrAdj"], *ranges["wrAdj"])
            + BAN_PR_WEIGHT * _norm(r["pickRate"], *ranges["pickRate"])
            - BAN_TP_WEIGHT * _norm(r["tp"], *ranges["tp"])
        )
        if r["locked"]:
            score += BAN_LOCKED_BONUS
        r["score"] = round(max(score, 0.0), 1)
    pool.sort(key=lambda r: r["score"], reverse=True)
    return pool
