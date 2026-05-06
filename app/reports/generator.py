from __future__ import annotations

import datetime as _dt
import html
import json
from pathlib import Path
from typing import Any

from app.models.hardware import FullScan
from app.models.profile import PROFILES, SUPPORTED_GAMES
from app.models.recommendation import Category, Recommendation
from app.recommendations.quality_spec import quality_spec_reference


_PRE_BIOS_CHECKLIST = [
    "Identificar exatamente o modelo da placa-mãe e a versão atual da BIOS.",
    "Ler o changelog oficial e verificar fix relevante para o seu hardware.",
    "Garantir alimentação estável (UPS/no-break ou notebook conectado).",
    "Anotar configurações personalizadas atuais (XMP, fan curves, etc.).",
    "Confirmar que a versão de destino é igual ou mais nova — nunca downgrade.",
]

_POST_BIOS_CHECKLIST = [
    "Carregar 'Optimized Defaults' após o flash.",
    "Reaplicar XMP/EXPO somente se já era estável antes.",
    "Validar boot, POST e estabilidade básica do Windows.",
    "Rodar teste de memória e benchmark curto.",
    "Documentar as alterações.",
]


def build_report_dict(
    scan: FullScan,
    profile_key: str,
    games: list[str],
    recommendations: list[Recommendation],
) -> dict[str, Any]:
    profile = PROFILES.get(profile_key)
    return {
        "generated_at": _dt.datetime.now().isoformat(timespec="seconds"),
        "profile": {
            "key": profile_key,
            "label": profile.label if profile else profile_key,
            "description": profile.description if profile else "",
        },
        "games": [
            {"key": g, "label": SUPPORTED_GAMES.get(g, g)} for g in games or []
        ],
        "system": scan.system.to_dict(),
        "hardware": scan.hardware.to_dict(),
        "bios": scan.bios.to_dict(),
        "updates": scan.updates.to_dict(),
        "collection_errors": list(scan.collection_errors),
        "detection_sources": {
            key: list(values) for key, values in scan.detection_sources.items()
        },
        "recommendation_quality_spec": quality_spec_reference().to_dict(),
        "recommendations": [r.to_dict() for r in recommendations],
        "summary": _build_summary(recommendations),
        "checklists": {
            "before_bios_change": list(_PRE_BIOS_CHECKLIST),
            "after_bios_change": list(_POST_BIOS_CHECKLIST),
        },
        "safety_notice": (
            "Este aplicativo é advisory-first. Nenhuma alteração de BIOS/UEFI, "
            "overclock, undervolt, registro ou driver é aplicada automaticamente. "
            "Quando o firmware não expõe uma configuração, o relatório marca "
            "o dado como não exposto em vez de estimar."
        ),
    }


def _build_summary(recommendations: list[Recommendation]) -> dict[str, Any]:
    by_category: dict[str, int] = {}
    by_priority: dict[str, int] = {}
    by_risk: dict[str, int] = {}
    for r in recommendations:
        by_category[r.category.value] = by_category.get(r.category.value, 0) + 1
        by_priority[r.priority.value] = by_priority.get(r.priority.value, 0) + 1
        by_risk[r.risk.value] = by_risk.get(r.risk.value, 0) + 1
    return {
        "total": len(recommendations),
        "by_category": by_category,
        "by_priority": by_priority,
        "by_risk": by_risk,
    }


def export_json(report: dict[str, Any], destination: Path | str) -> Path:
    path = Path(destination)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def export_html(report: dict[str, Any], destination: Path | str) -> Path:
    path = Path(destination)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_render_html(report), encoding="utf-8")
    return path


def _render_html(report: dict[str, Any]) -> str:
    esc = html.escape
    sys_rows = "".join(
        f"<tr><th>{esc(str(k))}</th><td>{esc(str(v))}</td></tr>"
        for k, v in report["system"].items()
    )
    hw_rows = "".join(
        f"<tr><th>{esc(str(k))}</th><td>{esc(str(v))}</td></tr>"
        for k, v in report["hardware"].items()
        if k != "storage"
    )
    bios_rows = "".join(
        f"<tr><th>{esc(str(k))}</th><td>{esc(str(v))}</td></tr>"
        for k, v in report["bios"].items()
    )
    updates_rows = "".join(
        f"<tr><th>{esc(str(k))}</th><td>{esc(str(v))}</td></tr>"
        for k, v in report.get("updates", {}).items()
        if k != "outdated_drivers"
    )
    source_rows = "".join(
        f"<tr><th>{esc(str(k))}</th><td>{esc(', '.join(v))}</td></tr>"
        for k, v in report.get("detection_sources", {}).items()
    )
    rec_blocks = []
    for rec in report["recommendations"]:
        steps = "".join(f"<li>{esc(s)}</li>" for s in rec.get("manual_steps", []))
        evidence = "".join(f"<li><code>{esc(e)}</code></li>" for e in rec.get("evidence", []))
        rec_blocks.append(
            f"""
            <article class="rec rec-{esc(rec['risk'])}">
              <header>
                <h3>{esc(rec['title'])}</h3>
                <span class="badge cat">{esc(rec['category'])}</span>
                <span class="badge prio">{esc(rec['priority'])}</span>
                <span class="badge risk">{esc(rec['risk'])}</span>
              </header>
              <dl>
                <dt>Estado atual</dt><dd>{esc(rec.get('current_state', ''))}</dd>
                <dt>Estado recomendado</dt><dd>{esc(rec.get('recommended_state', ''))}</dd>
                <dt>Justificativa</dt><dd>{esc(rec.get('rationale', ''))}</dd>
                <dt>Benefício esperado</dt><dd>{esc(rec.get('expected_benefit', ''))}</dd>
                <dt>Quando não aplicar</dt><dd>{esc(rec.get('when_not_to_apply', ''))}</dd>
                <dt>Como validar</dt><dd>{esc(rec.get('how_to_validate', ''))}</dd>
                <dt>Segurança</dt><dd>{esc(rec.get('safety_note', ''))}</dd>
                <dt>Rollback</dt><dd>{esc(rec.get('rollback', ''))}</dd>
              </dl>
              {f"<h4>Passos manuais</h4><ol>{steps}</ol>" if steps else ""}
              {f"<h4>Evidência</h4><ul>{evidence}</ul>" if evidence else ""}
            </article>
            """
        )
    pre = "".join(f"<li>{esc(x)}</li>" for x in report["checklists"]["before_bios_change"])
    post = "".join(f"<li>{esc(x)}</li>" for x in report["checklists"]["after_bios_change"])
    games_html = ", ".join(esc(g["label"]) for g in report.get("games", [])) or "—"

    return f"""<!doctype html>
<html lang="pt-BR"><head>
<meta charset="utf-8">
<title>HardwareOptimizer — Relatório</title>
<style>
  body {{ font-family: 'Segoe UI', Inter, Arial, sans-serif; background:#0B1120; color:#E5E7EB; margin:0; padding:24px; }}
  h1,h2,h3,h4 {{ color:#F8FAFC; }}
  table {{ border-collapse: collapse; width:100%; margin-bottom:16px; }}
  th, td {{ text-align:left; padding:6px 10px; border-bottom:1px solid #334155; }}
  .rec {{ background:#111827; border:1px solid #334155; border-radius:8px; padding:16px; margin-bottom:12px; }}
  .rec header {{ display:flex; gap:8px; align-items:center; flex-wrap:wrap; }}
  .badge {{ font-size:12px; padding:2px 6px; border-radius:4px; background:#1F2937; color:#E5E7EB; }}
  .rec-safe {{ border-left:4px solid #22C55E; }}
  .rec-review {{ border-left:4px solid #F59E0B; }}
  .rec-risky {{ border-left:4px solid #EF4444; }}
  .rec-blocked {{ border-left:4px solid #DC2626; }}
  dl {{ display:grid; grid-template-columns: 200px 1fr; gap:4px 12px; }}
  dt {{ color:#9CA3AF; }}
  code {{ font-family: Consolas, monospace; }}
  .notice {{ background:#1F2937; padding:12px; border-left:4px solid #38BDF8; margin-bottom:16px; border-radius:4px; }}
</style></head><body>
<h1>HardwareOptimizer — Relatório</h1>
<p>Gerado em: {esc(report['generated_at'])}</p>
<p>Perfil: <strong>{esc(report['profile']['label'])}</strong> — Jogos: {games_html}</p>
<div class="notice">{esc(report['safety_notice'])}</div>
<h2>Sistema</h2><table>{sys_rows}</table>
<h2>Hardware</h2><table>{hw_rows}</table>
<h2>BIOS</h2><table>{bios_rows}</table>
<h2>Atualizações</h2><table>{updates_rows}</table>
<h2>Fontes de detecção</h2><table>{source_rows}</table>
<h2>Recomendações ({report['summary']['total']})</h2>
{''.join(rec_blocks) or '<p>Sem recomendações.</p>'}
<h2>Checklist — antes de alterar BIOS/UEFI</h2><ul>{pre}</ul>
<h2>Checklist — depois de alterar BIOS/UEFI</h2><ul>{post}</ul>
</body></html>"""
