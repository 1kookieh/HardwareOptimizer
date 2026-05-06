from app.models import PROFILES, SUPPORTED_GAMES
from app.models.recommendation import Category, Priority, Recommendation, RiskLevel


def test_profiles_present():
    assert {"games", "development", "video_editing", "general",
            "high_performance", "stability", "low_power"} <= PROFILES.keys()


def test_supported_games_present():
    assert {"valorant", "league_of_legends", "cod_warzone",
            "marvel_rivals", "fortnite", "cs2"} <= SUPPORTED_GAMES.keys()


def test_recommendation_to_dict():
    rec = Recommendation(
        title="t",
        category=Category.BIOS,
        priority=Priority.HIGH,
        risk=RiskLevel.REVIEW,
        rationale="r",
        expected_benefit="b",
        expected_impact="i",
    )
    d = rec.to_dict()
    assert d["category"] == "bios"
    assert d["priority"] == "high"
    assert d["risk"] == "review"
