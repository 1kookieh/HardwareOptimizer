from pathlib import Path

from app.recommendations import generate_recommendations
from app.reports import build_report_dict
from app.storage import HistoryStore
from tests.fixtures import make_scan


def test_save_and_list(tmp_path: Path):
    store = HistoryStore(tmp_path / "h.sqlite")
    scan = make_scan()
    recs = generate_recommendations(scan, "games", games=["valorant"])
    report = build_report_dict(scan, "games", ["valorant"], recs)
    sid = store.save_scan("games", ["valorant"], scan.to_dict(), report["recommendations"])
    assert sid > 0
    items = store.list_scans()
    assert items and items[0]["id"] == sid
    assert items[0]["games"] == ["valorant"]


def test_status_update(tmp_path: Path):
    store = HistoryStore(tmp_path / "h.sqlite")
    scan = make_scan()
    recs = generate_recommendations(scan, "general")
    report = build_report_dict(scan, "general", [], recs)
    sid = store.save_scan("general", [], scan.to_dict(), report["recommendations"])
    title = report["recommendations"][0]["title"]
    store.update_status(sid, title, "applied")
