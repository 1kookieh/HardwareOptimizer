import json
from pathlib import Path

from app.recommendations import generate_recommendations
from app.reports import build_report_dict, export_html, export_json
from tests.fixtures import make_scan


def test_report_dict_has_required_sections():
    scan = make_scan()
    recs = generate_recommendations(scan, "games", games=["valorant"])
    report = build_report_dict(scan, "games", ["valorant"], recs)
    for key in ["generated_at", "profile", "games", "system", "hardware",
                "bios", "recommendations", "summary", "checklists", "safety_notice"]:
        assert key in report
    assert report["summary"]["total"] == len(recs)


def test_export_json(tmp_path: Path):
    scan = make_scan()
    recs = generate_recommendations(scan, "general")
    report = build_report_dict(scan, "general", [], recs)
    out = export_json(report, tmp_path / "r.json")
    assert out.exists()
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["profile"]["key"] == "general"


def test_export_html(tmp_path: Path):
    scan = make_scan()
    recs = generate_recommendations(scan, "stability")
    report = build_report_dict(scan, "stability", [], recs)
    out = export_html(report, tmp_path / "r.html")
    assert out.exists()
    text = out.read_text(encoding="utf-8")
    assert "<html" in text
    assert "Recomendações" in text


def test_report_includes_bios_checklists():
    scan = make_scan()
    report = build_report_dict(scan, "general", [], [])
    assert report["checklists"]["before_bios_change"]
    assert report["checklists"]["after_bios_change"]
