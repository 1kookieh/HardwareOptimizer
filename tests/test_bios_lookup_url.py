"""Garante que o BIOS lookup nunca caia em buscador externo (Google/Bing/etc.)
e use somente páginas oficiais de suporte do fabricante."""
from __future__ import annotations

import pytest

from app.collectors.updates import _resolve_bios_support_url, enrich_online_update_sources
from app.models.hardware import BiosInfo, HardwareInfo, UpdatesInfo


@pytest.mark.parametrize(
    "vendor,expected_host",
    [
        ("ASUSTeK COMPUTER INC.", "asus.com"),
        ("Gigabyte Technology Co., Ltd.", "gigabyte.com"),
        ("Micro-Star International Co., Ltd.", "msi.com"),
        ("ASRock Inc.", "asrock.com"),
        ("Dell Inc.", "dell.com"),
        ("LENOVO", "lenovo.com"),
        ("HP", "hp.com"),
        ("American Megatrends Inc.", "ami.com"),
    ],
)
def test_known_vendor_resolves_to_official_support(vendor: str, expected_host: str) -> None:
    url = _resolve_bios_support_url(vendor)
    assert url is not None
    assert expected_host in url
    assert "google" not in url
    assert "bing" not in url


def test_unknown_vendor_returns_none() -> None:
    assert _resolve_bios_support_url("Vendor Desconhecido S.A.") is None
    assert _resolve_bios_support_url(None) is None
    assert _resolve_bios_support_url("") is None


def test_enrich_does_not_set_search_engine_url(monkeypatch: pytest.MonkeyPatch) -> None:
    # Bloqueia rede para o teste
    monkeypatch.setattr(
        "app.collectors.updates._url_reachable", lambda url, errors: False
    )
    info = UpdatesInfo()
    hw = HardwareInfo(motherboard_vendor="Vendor Desconhecido")
    bios = BiosInfo(vendor="Vendor Desconhecido")
    enrich_online_update_sources(info, hw, bios, errors=[])
    assert "google" not in (info.bios_lookup_url or "").lower()
    assert "bing" not in (info.bios_lookup_url or "").lower()


def test_enrich_uses_official_url_when_vendor_known(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "app.collectors.updates._url_reachable", lambda url, errors: False
    )
    info = UpdatesInfo()
    hw = HardwareInfo(motherboard_vendor="ASUSTeK COMPUTER INC.")
    bios = BiosInfo(vendor="American Megatrends Inc.")
    enrich_online_update_sources(info, hw, bios, errors=[])
    assert "asus.com" in info.bios_lookup_url
    assert info.bios_lookup_url in info.official_sources
