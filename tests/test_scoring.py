from scoring import (
    _norm,
    build_ban_recommendations,
    build_recommendations,
    league_icon_url,
    min_power_for,
    rank_icon_url,
    tier_for_rank,
)


def brawler(name="Shelly", power=11, trophies=1000, rank=20):
    return {"name": name, "power": power, "trophies": trophies, "rank": rank}


def stat(name="Shelly", wr=60.0, ur=10.0, sr=5.0):
    return {"brawler": name, "winRate": wr, "pickRate": ur, "starRate": sr}


class TestMinPower:
    def test_pl_is_9(self):
        assert min_power_for("pl") == 9

    def test_unknown_tier_defaults_11(self):
        assert min_power_for("pl-l1") == 11
        assert min_power_for("unknown") == 11


class TestTierForRank:
    def test_legendary(self):
        assert tier_for_rank(16) == "pl-l1"
        assert tier_for_rank(20) == "pl-l1"

    def test_mythic3(self):
        assert tier_for_rank(15) == "pl-m3"

    def test_mythic1(self):
        assert tier_for_rank(13) == "pl-m1"
        assert tier_for_rank(14) == "pl-m1"

    def test_below(self):
        assert tier_for_rank(12) == "pl"
        assert tier_for_rank(0) == "pl"

    def test_garbage(self):
        assert tier_for_rank(None) == "pl"
        assert tier_for_rank("abc") == "pl"


class TestRankIconUrl:
    def test_rank_1(self):
        assert rank_icon_url(1).endswith("/58000000.png")

    def test_rank_16(self):
        assert rank_icon_url(16).endswith("/58000015.png")

    def test_zero_and_negative(self):
        assert rank_icon_url(0) == ""
        assert rank_icon_url(-1) == ""

    def test_garbage(self):
        assert rank_icon_url(None) == ""
        assert rank_icon_url("x") == ""


class TestLeagueIconUrl:
    def test_known_tiers(self):
        assert league_icon_url("pl").endswith("/58000009.png")
        assert league_icon_url("pl-l1").endswith("/58000015.png")

    def test_unknown_tier(self):
        assert league_icon_url("nope") == ""


class TestNorm:
    def test_midpoint(self):
        assert _norm(50, 0, 100) == 50.0

    def test_bounds(self):
        assert _norm(0, 0, 100) == 0.0
        assert _norm(100, 0, 100) == 100.0

    def test_degenerate_range_returns_50(self):
        assert _norm(42, 42, 42) == 50.0


class TestBuildRecommendations:
    def test_empty_pool_when_no_matching_stats(self):
        result = build_recommendations([brawler()], [], "pl")
        assert result == []

    def test_filters_low_power_when_only_max(self):
        stats = [stat(wr=80, ur=50)]
        result = build_recommendations(
            [brawler(power=8)], stats, "pl", only_max=True
        )
        assert result == []
        result = build_recommendations(
            [brawler(power=8)], stats, "pl", only_max=False
        )
        assert len(result) == 1

    def test_min_power_boundary_passes(self):
        stats = [stat(wr=80, ur=50)]
        result = build_recommendations(
            [brawler(power=9)], stats, "pl", only_max=True
        )
        assert len(result) == 1

    def test_higher_winrate_wins(self):
        stats = [stat("Shelly", wr=40), stat("Spike", wr=90)]
        players = [brawler("Shelly"), brawler("Spike")]
        result = build_recommendations(players, stats, "pl")
        assert result[0]["name"] == "Spike"
        assert result[0]["score"] >= result[1]["score"]

    def test_scores_are_sorted_descending(self):
        stats = [
            stat("A", wr=30),
            stat("B", wr=55),
            stat("C", wr=70),
            stat("D", wr=45),
        ]
        players = [brawler(n) for n in ("A", "B", "C", "D")]
        scores = [r["score"] for r in build_recommendations(players, stats, "pl")]
        assert scores == sorted(scores, reverse=True)

    def test_shrinking_pulls_rare_picks_toward_50(self):
        common = 50 + (80 - 50) * 50 / (50 + 8)
        rare = 50 + (80 - 50) * 1 / (1 + 8)
        assert rare < common < 80

    def test_single_entry_gets_neutral_score(self):
        result = build_recommendations(
            [brawler()], [stat(wr=99, ur=99)], "pl"
        )
        assert len(result) == 1
        assert result[0]["score"] == 50.0


class TestBuildBanRecommendations:
    def test_empty_pool(self):
        assert build_ban_recommendations([brawler()], [], "pl") == []

    def test_locked_brawler_gets_bonus(self):
        stats = [stat("Weak", wr=50, ur=50), stat("Strong", wr=50, ur=50)]
        players = [brawler("Weak", power=1), brawler("Strong", power=11)]
        result = build_ban_recommendations(players, stats, "pl")
        assert result[0]["name"] == "Weak"
        assert result[0]["locked"] is True
        assert result[1]["locked"] is False

    def test_high_winrate_high_pickrate_banned_first(self):
        stats = [stat("Bad", wr=90, ur=80), stat("Fine", wr=45, ur=20)]
        players = [brawler("Bad"), brawler("Fine")]
        result = build_ban_recommendations(players, stats, "pl")
        assert result[0]["name"] == "Bad"

    def test_score_never_negative(self):
        stats = [stat("X", wr=100, ur=100)]
        players = [brawler("X", trophies=50000)]
        result = build_ban_recommendations(players, stats, "pl")
        assert result[0]["score"] >= 0

    def test_locked_flag_present_on_all(self):
        stats = [stat("A"), stat("B")]
        players = [brawler("A", power=9), brawler("B", power=10)]
        result = build_ban_recommendations(players, stats, "pl")
        assert all("locked" in r for r in result)
