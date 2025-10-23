"""
Panel Streamlit que replica la funcionalidad de Descarga_Todo usando data.json
y los scrapers originales.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from html import escape

import streamlit as st
import streamlit.components.v1 as components
from jinja2 import Environment, FileSystemLoader, TemplateNotFound, select_autoescape

PROJECT_ROOT = Path(__file__).resolve().parent
os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", str(PROJECT_ROOT / ".playwright-browsers"))
sys.path.append(str(PROJECT_ROOT / "Descarga_Todo"))
sys.path.append(str(PROJECT_ROOT / "Descarga_Todo" / "muestra_sin_fallos"))

from modules.estudio_scraper import (  # type: ignore  # noqa: E402
    format_ah_as_decimal_string_of,
    generar_analisis_mercado_simplificado,
    obtener_datos_completos_partido,
    obtener_datos_preview_ligero,
)
from app_utils import normalize_handicap_to_half_bucket_str  # type: ignore  # noqa: E402
from Descarga_Todo.muestra_sin_fallos.app import app as flask_app  # type: ignore  # noqa: E402

st.set_page_config(layout="wide", page_title="Analisis de Partidos", page_icon=":soccer:")

flask_app.config["TESTING"] = True

DATA_FILE_CANDIDATES = [
    PROJECT_ROOT / "Descarga_Todo" / "data.json",
    PROJECT_ROOT / "data.json",
]
for candidate in DATA_FILE_CANDIDATES:
    if candidate.exists():
        DATA_FILE = candidate
        break
else:
    DATA_FILE = DATA_FILE_CANDIDATES[0]

SCRAPER_SCRIPT = PROJECT_ROOT / "Descarga_Todo" / "run_scraper.py"
TEMPLATES_DIR = PROJECT_ROOT / "Descarga_Todo" / "muestra_sin_fallos" / "templates"
FUTURE_FALLBACK = datetime.max.replace(tzinfo=timezone.utc)
PAST_FALLBACK = datetime.min.replace(tzinfo=timezone.utc)

JINJA_ENV: Optional[Environment] = None
if TEMPLATES_DIR.exists():
    JINJA_ENV = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=select_autoescape(["html", "xml"]),
    )

HTML_WRAPPER_START = """
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<style>
    :root {
        color-scheme: light;
    }
    body { background-color: #f6f8fc; margin: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; font-size: 0.92rem; }
    .preview-wrapper { padding: 14px 16px; }
    .match-header { display: flex; flex-wrap: wrap; justify-content: space-between; gap: 10px; margin-bottom: 12px; align-items: baseline; }
    .match-header h2 { margin: 0; font-size: 1.18rem; color: #1f2937; font-weight: 600; }
    .match-meta { color: #4b5563; font-size: 0.82rem; }
    .card-grid { display: grid; gap: 12px; margin-bottom: 14px; }
    .grid-4 { grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); }
    .grid-3 { grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); }
    .grid-2 { grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); }
    .preview-card { background-color: #ffffff; border-radius: 10px; border: 1px solid #d9dde5; padding: 14px; box-shadow: 0 1px 2px rgba(15, 23, 42, 0.06); height: 100%; }
    .preview-card h4, .preview-card h5, .preview-card h6 { margin: 0 0 6px 0; color: #0d6efd; font-weight: 600; font-size: 0.95rem; }
    .score { font-size: 1.5rem; font-weight: 700; text-align: center; margin: 4px 0; color: #1f2937; }
    .teams-line { text-align: center; font-weight: 500; margin-bottom: 4px; }
    .meta-line { font-size: 0.82rem; color: #4b5563; margin: 2px 0; }
    .meta-pill { display: inline-block; padding: 2px 6px; background-color: #eef2ff; border-radius: 12px; font-size: 0.72rem; margin-right: 4px; margin-bottom: 4px; }
    .status-cover { font-weight: 600; }
    .status-cover.cover { color: #16a34a; }
    .status-cover.not-cover { color: #dc2626; }
    .status-cover.push { color: #2563eb; }
    .status-cover.neutral { color: #6b7280; }
    .analysis-text { font-size: 0.82rem; color: #374151; margin-top: 6px; line-height: 1.35; }
    table.stat-table { width: 100%; border-collapse: collapse; margin-top: 8px; font-size: 0.78rem; }
    table.stat-table thead th { background-color: #eef2ff; color: #4b5563; padding: 5px; }
    table.stat-table tbody td { padding: 5px; border-top: 1px solid #e5e7eb; text-align: center; }
    table.stat-table tbody td:first-child { text-align: left; }
    table.stat-table tbody td:last-child { text-align: right; }
    .analysis-card { background: linear-gradient(135deg, #1d4ed8 0%, #0ea5e9 100%); color: white; border: none; box-shadow: 0 6px 14px rgba(14, 165, 233, 0.2); }
    .analysis-card h4 { color: white; }
    .analysis-card a { color: #f8fafc; text-decoration: underline; }
    .empty-hint { font-style: italic; color: #6b7280; }
</style>
</head>
<body>
<div class="preview-wrapper">
"""
HTML_WRAPPER_END = "</div></body></html>"

PW_FLAG = PROJECT_ROOT / ".playwright_ready"


GLOBAL_STYLES = """
<style>
:root {
    color-scheme: light;
}
div[data-testid="stAppViewContainer"] {
    background: linear-gradient(180deg, #f2f5fb 0%, #f9fbff 70%);
    font-family: "Segoe UI", -apple-system, BlinkMacSystemFont, sans-serif;
    font-size: 0.85rem;
}
div[data-testid="stHeader"] {
    background: transparent;
}
.match-grid {
    display: flex;
    flex-direction: column;
    gap: 4px;
    margin-top: 2px;
}
.match-row {
    width: 100%;
    display: grid;
    grid-template-columns: 56px minmax(220px, 1fr) 54px 54px 56px;
    gap: 8px;
    align-items: center;
    padding: 6px 8px;
    background: #ffffff;
    border: 1px solid #d5ddeb;
    border-radius: 6px;
    font-size: 0.72rem;
    color: #0f172a;
    box-shadow: 0 2px 6px rgba(15, 23, 42, 0.05);
}
.match-row--finished {
    background: #f3f6ff;
}
.match-row--active {
    border-color: #2563eb;
    box-shadow: 0 0 0 1px #2563eb;
}
.match-row__time {
    font-weight: 600;
    color: #1e293b;
}
.match-row__date {
    font-size: 0.58rem;
    color: #94a3b8;
    margin-top: 1px;
}
.match-row__league {
    font-size: 0.6rem;
    text-transform: uppercase;
    color: #64748b;
    letter-spacing: 0.04em;
    margin-bottom: 2px;
}
.match-row__names {
    display: flex;
    flex-wrap: wrap;
    align-items: baseline;
    gap: 3px;
}
.match-row__team {
    font-weight: 600;
}
.match-row__team--away {
    color: #0f7be5;
}
.match-row__vs {
    font-size: 0.65rem;
    color: #94a3b8;
}
.match-row__meta {
    margin-top: 2px;
    font-size: 0.58rem;
    color: #94a3b8;
    display: flex;
    flex-wrap: wrap;
    gap: 4px;
}
.match-row__metric {
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    gap: 1px;
    font-variant-numeric: tabular-nums;
}
.match-row__metric-label {
    font-size: 0.56rem;
    text-transform: uppercase;
    color: #9aa5bd;
    letter-spacing: 0.04em;
}
.match-row__metric-value {
    font-size: 0.82rem;
    font-weight: 600;
    color: #1d4ed8;
}
.match-row__metric--ou .match-row__metric-value {
    color: #0ea5e9;
}
.match-row__score {
    text-align: right;
    font-size: 0.82rem;
    font-weight: 600;
    color: #0f172a;
}
.match-row__score--placeholder {
    color: #cbd5f5;
}
.match-actions-container {
    display: flex;
    flex-direction: column;
    gap: 4px;
    align-items: stretch;
    justify-content: center;
}
.match-action-link {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 100%;
    padding: 3px 4px;
    border-radius: 4px;
    border: 1px solid #bed4ff;
    background: #eef3ff;
    color: #1d4ed8;
    text-decoration: none;
    font-size: 0.62rem;
    font-weight: 600;
    transition: all 0.15s ease;
}
.match-action-link:hover {
    background: #dbe6ff;
    border-color: #a9c4ff;
}
div[data-testid="stButton"] button {
    padding: 4px 0 !important;
    font-size: 0.62rem !important;
    border-radius: 4px !important;
    height: auto !important;
    background: #f8faff !important;
    border: 1px solid #c8d7ff !important;
    color: #1e3a8a !important;
}
div[data-testid="stButton"] button:hover {
    border-color: #2563eb !important;
    color: #2563eb !important;
}
.preview-spacer {
    height: 4px;
}
</style>
"""


def inject_global_styles() -> None:
    st.markdown(GLOBAL_STYLES, unsafe_allow_html=True)


def safe_text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    return escape(str(value))


def ensure_playwright() -> None:
    if PW_FLAG.exists():
        return
    cmd = [sys.executable, "-m", "playwright", "install", "chromium"]
    if sys.platform.startswith("linux"):
        cmd.insert(-1, "--with-deps")
    try:
        subprocess.run(
            cmd,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except Exception as exc:
        st.warning(f"No se pudo preparar Playwright automaticamente ({exc}). Si hay errores en scraping, instala los navegadores con `playwright install chromium`.")
    else:
        PW_FLAG.touch()

def parse_datetime(value: Any) -> Optional[datetime]:
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if not value:
        return None
    text = str(value).strip()
    if not text:
        return None
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y/%m/%d %H:%M:%S"):
        try:
            return datetime.strptime(text, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    try:
        dt = datetime.fromisoformat(text)
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except ValueError:
        pass
    for fmt in ("%d/%m %H:%M", "%d-%m %H:%M"):
        try:
            dt = datetime.strptime(text, fmt)
            now = datetime.now(timezone.utc)
            return dt.replace(year=now.year, tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


def prepare_matches(raw_matches: List[Any], mode: str) -> List[Dict[str, Any]]:
    prepared: List[Dict[str, Any]] = []
    seen: set[str] = set()
    now_utc = datetime.now(timezone.utc)
    for item in raw_matches:
        if not isinstance(item, dict):
            continue
        match = dict(item)
        match_id = str(match.get("id") or "").strip()
        if not match_id or match_id in seen:
            continue
        seen.add(match_id)
        dt = parse_datetime(
            match.get("time_obj")
            or match.get("match_datetime")
            or (
                f"{match.get('match_date')} {match.get('match_time')}"
                if match.get("match_date") and match.get("match_time")
                else None
            )
        )
        match["id"] = match_id
        match["handicap"] = str(match.get("handicap", "N/A"))
        match["goal_line"] = str(match.get("goal_line", "N/A"))
        match["time_utc"] = dt
        match["_time_sort"] = dt
        if not match.get("time") and dt:
            match["time"] = dt.strftime("%d/%m %H:%M") if mode == "finished" else dt.strftime("%H:%M")
        prepared.append(match)

    if mode == "upcoming":
        prepared = [m for m in prepared if not m.get("time_utc") or m["time_utc"] >= now_utc]
        prepared.sort(key=lambda m: (m.get("_time_sort") is None, m.get("_time_sort") or FUTURE_FALLBACK))
    else:
        prepared.sort(
            key=lambda m: (m.get("_time_sort") is None, m.get("_time_sort") or PAST_FALLBACK),
            reverse=True,
        )
    return prepared


@st.cache_data(show_spinner=False)
def load_data_from_file() -> Dict[str, List[Dict[str, Any]]]:
    if not DATA_FILE.exists():
        return {"upcoming_matches": [], "finished_matches": []}
    try:
        raw = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {"upcoming_matches": [], "finished_matches": []}
    return {
        "upcoming_matches": prepare_matches(raw.get("upcoming_matches", []), "upcoming"),
        "finished_matches": prepare_matches(raw.get("finished_matches", []), "finished"),
    }


def extract_handicap_options(matches: List[Dict[str, Any]]) -> List[str]:
    options: set[str] = set()
    for match in matches:
        normalized = normalize_handicap_to_half_bucket_str(match.get("handicap"))
        if normalized is not None:
            options.add(normalized)
    return sorted(options, key=lambda val: float(val))


def ensure_filter_state(mode: str) -> None:
    filter_key = f"{mode}_handicap_filter_value"
    input_key = f"{mode}_handicap_filter_input"
    if filter_key not in st.session_state:
        st.session_state[filter_key] = ""
    if input_key not in st.session_state:
        st.session_state[input_key] = st.session_state[filter_key]


def apply_handicap_filter(matches: List[Dict[str, Any]], mode: str) -> Tuple[List[Dict[str, Any]], Optional[str]]:
    filter_key = f"{mode}_handicap_filter_value"
    needle = st.session_state.get(filter_key, "").strip()
    if not needle:
        return matches, None
    normalized = normalize_handicap_to_half_bucket_str(needle)
    if normalized is None:
        return matches, f"No se reconoce el handicap '{needle}'."
    filtered = [
        match
        for match in matches
        if normalize_handicap_to_half_bucket_str(match.get("handicap")) == normalized
    ]
    return filtered, None


def format_cover_status(status: Optional[str]) -> str:
    if not status:
        return ""
    value = str(status).upper()
    if value == "CUBIERTO":
        return '<span class="status-cover cover">CUBIERTO</span>'
    if value == "NO CUBIERTO":
        return '<span class="status-cover not-cover">NO CUBIERTO</span>'
    if value in {"NULO", "PUSH"}:
        cls = "push" if value == "PUSH" else "neutral"
        return f'<span class="status-cover {cls}">{value}</span>'
    return f'<span class="status-cover neutral">{value}</span>'


def render_stats_table_html(rows: Optional[List[Dict[str, Any]]]) -> str:
    if not rows:
        return ""
    parts = [
        '<table class="stat-table">',
        "<thead><tr><th>Local</th><th>Estadistica</th><th>Visitante</th></tr></thead>",
        "<tbody>",
    ]
    for row in rows:
        parts.append(
            "<tr>"
            f"<td>{row.get('home', '')}</td>"
            f"<td>{row.get('label', '')}</td>"
            f"<td>{row.get('away', '')}</td>"
            "</tr>"
        )
    parts.append("</tbody></table>")
    return "".join(parts)


def render_recent_card(title: str, block: Optional[Dict[str, Any]]) -> str:
    if not block:
        return ""
    score = block.get("score") or block.get("score_line")
    meta_bits = []
    if block.get("date"):
        meta_bits.append(f'<span class="meta-pill">{block["date"]}</span>')
    if block.get("ah"):
        meta_bits.append(f'<span class="meta-pill">AH: {block["ah"]}</span>')
    if block.get("ou"):
        meta_bits.append(f'<span class="meta-pill">O/U: {block["ou"]}</span>')
    cover_html = format_cover_status(block.get("cover_status"))
    analysis = block.get("analysis")
    teams = ""
    if block.get("home") and block.get("away"):
        teams = f'<div class="teams-line">{block["home"]} vs {block["away"]}</div>'
    html: List[str] = ['<div class="preview-card">', f"<h6>{title}</h6>"]
    if score:
        html.append(f'<div class="score">{score.replace(":", " - ")}</div>')
    if teams:
        html.append(teams)
    if meta_bits:
        html.append(f"<div>{''.join(meta_bits)}</div>")
    if cover_html:
        html.append(f'<div class="meta-line">Estado: {cover_html}</div>')
    stats_html = render_stats_table_html(block.get("stats_rows"))
    if stats_html:
        html.append(stats_html)
    if analysis:
        html.append(f'<div class="analysis-text">{analysis}</div>')
    html.append("</div>")
    return "".join(html)


def render_comparativa_card(
    card: Optional[Dict[str, Any]],
    fallback_title: str,
) -> str:
    title = fallback_title
    html: List[str] = ['<div class="preview-card">']
    if card:
        home_title = safe_text(card.get("title_home_name", ""))
        away_title = safe_text(card.get("title_away_name", ""))
        if home_title or away_title:
            title = f"{home_title or 'Local'} vs. Ult. rival de {away_title or 'Visitante'}"
        html.append(f"<h6>{title}</h6>")
        score = card.get("score")
        if score:
            safe_score = safe_text(score).replace(":", " - ")
            html.append(f'<div class="score">{safe_score}</div>')
        teams = ""
        home_team = card.get("home_team")
        away_team = card.get("away_team")
        if home_team and away_team:
            teams = f'<div class="teams-line">{safe_text(home_team)} vs {safe_text(away_team)}</div>'
        if teams:
            html.append(teams)
        pills = []
        if card.get("localia"):
            pills.append(f'<span class="meta-pill">Localia: {safe_text(card["localia"])}</span>')
        if card.get("ah"):
            pills.append(f'<span class="meta-pill">AH: {safe_text(card["ah"])}</span>')
        if card.get("ou"):
            pills.append(f'<span class="meta-pill">O/U: {safe_text(card["ou"])}</span>')
        if pills:
            html.append(f"<div>{''.join(pills)}</div>")
        cover_html = format_cover_status(card.get("cover_status"))
        if cover_html:
            html.append(f'<div class="meta-line">Estado: {cover_html}</div>')
        stats_html = render_stats_table_html(card.get("stats_rows"))
        if stats_html:
            html.append(stats_html)
        analysis = card.get("analysis")
        if analysis:
            html.append(f'<div class="analysis-text">{safe_text(analysis)}</div>')
    else:
        html.append(f"<h6>{title}</h6>")
        html.append('<p class="empty-hint">Sin datos disponibles para este cruce.</p>')
    html.append("</div>")
    return "".join(html)


def build_analysis_html(payload: Dict[str, Any], match: Dict[str, Any]) -> str:
    home = payload.get("home_team", match.get("home_team", "Local"))
    away = payload.get("away_team", match.get("away_team", "Visitante"))
    match_date = payload.get("match_date") or match.get("match_date") or ""
    match_time = payload.get("match_time") or match.get("match_time") or match.get("time", "")
    final_score = payload.get("final_score") or match.get("score")
    handicap = match.get("handicap") or payload.get("handicap", {}).get("ah_line")
    goal_line = match.get("goal_line")

    parts: List[str] = [HTML_WRAPPER_START]
    header = [
        '<div class="match-header">',
        f"<h2>{home} vs {away}</h2>",
        "<div class=\"match-meta\">",
    ]
    if match_date or match_time:
        header.append(f"{match_date} {match_time}".strip())
    if handicap and handicap != "N/A":
        header.append(f" A AH: {handicap}")
    if goal_line and goal_line != "N/A":
        header.append(f" A O/U: {goal_line}")
    if final_score:
        header.append(f" A Resultado: {final_score}")
    header.append("</div></div>")
    parts.append("".join(header))

    recent = payload.get("recent_indirect_full") or {}
    top_cards: List[str] = []
    top_cards.append(render_recent_card(f"Ultimo {home} (Casa)", recent.get("last_home")))
    top_cards.append(render_recent_card(f"Ultimo {away} (Fuera)", recent.get("last_away")))
    top_cards.append(render_recent_card("Rivales comunes", recent.get("h2h_col3") or recent.get("h2h_general")))
    simplified_html = payload.get("simplified_html")
    if simplified_html:
        top_cards.append(
            '<div class="preview-card analysis-card"><h6>Analisis Mercado vs. H2H</h6>'
            f"{simplified_html}</div>"
        )
    top_cards = [card for card in top_cards if card]
    if top_cards:
        grid_class = "grid-4" if len(top_cards) >= 4 else "grid-3"
        parts.append(f'<div class="card-grid {grid_class}">{"".join(top_cards)}</div>')

    comparativas = payload.get("comparativas_indirectas") or {}
    left_title = f"{home} vs Ult. rival de {away}"
    right_title = f"{away} vs Ult. rival de {home}"
    left_card = render_comparativa_card(comparativas.get("left"), left_title)
    right_card = render_comparativa_card(comparativas.get("right"), right_title)
    parts.append(f'<div class="card-grid grid-2">{left_card}{right_card}</div>')

    if not top_cards and not simplified_html and all(
        "Sin datos disponibles" in card for card in (left_card, right_card)
    ):
        parts.append('<div class="preview-card"><p class="empty-hint">No se encontraron datos para este partido.</p></div>')

    parts.append(HTML_WRAPPER_END)
    return "".join(parts)


def build_light_preview_html(data: Dict[str, Any], match: Dict[str, Any]) -> str:
    home = data.get("home_team", match.get("home_team", "Local"))
    away = data.get("away_team", match.get("away_team", "Visitante"))
    parts: List[str] = [HTML_WRAPPER_START]
    parts.append(
        "<div class='match-header'>"
        f"<h2>{home} vs {away}</h2>"
        "<div class='match-meta'>Vista previa ligera (datos reducidos)</div>"
        "</div>"
    )
    parts.append('<div class="preview-card">')
    recent_form = data.get("recent_form") or {}
    parts.append("<h6>Resumen de forma reciente</h6>")
    parts.append(
        f"<div class='meta-line'>{home}: {recent_form.get('home', {}).get('wins', 0)} victorias / "
        f"{recent_form.get('home', {}).get('total', 0)} partidos</div>"
    )
    parts.append(
        f"<div class='meta-line'>{away}: {recent_form.get('away', {}).get('wins', 0)} victorias / "
        f"{recent_form.get('away', {}).get('total', 0)} partidos</div>"
    )
    recent_indirect = data.get("recent_indirect") or {}
    cards = [
        render_recent_card(f"Ultimo {home} (Casa)", recent_indirect.get("last_home")),
        render_recent_card(f"Ultimo {away} (Fuera)", recent_indirect.get("last_away")),
        render_recent_card("Rivales comunes", recent_indirect.get("h2h_col3")),
    ]
    cards = [card for card in cards if card]
    if cards:
        parts.append("</div>")
        parts.append(f'<div class="card-grid grid-3">{"".join(cards)}</div>')
    else:
        parts.append("<p class='empty-hint'>No hay mis datos disponibles en la vista previa ligera.</p></div>")
    parts.append(HTML_WRAPPER_END)
    return "".join(parts)


@st.cache_data(show_spinner=False, ttl=600)
def get_analysis_payload(match_id: str) -> Dict[str, Any]:
    ensure_playwright()
    with flask_app.app_context():
        with flask_app.test_client() as client:
            response = client.get(f"/api/analisis/{match_id}")
    if response.status_code != 200:
        raise RuntimeError(f"El servidor devolvi {response.status_code}")
    data = response.get_json()
    if not isinstance(data, dict):
        raise RuntimeError("Respuesta inesperada del analizador.")
    return data


@st.cache_data(show_spinner=False, ttl=600)
def get_light_preview_data(match_id: str) -> Dict[str, Any]:
    ensure_playwright()
    return obtener_datos_preview_ligero(str(match_id))


def render_preview_for_match(match: Dict[str, Any]) -> None:
    match_id = str(match["id"])
    try:
        payload = get_analysis_payload(match_id)
        preview_html = build_analysis_html(payload, match)
        height = 900
    except Exception as exc:  # pragma: no cover - fallback defensivo
        st.warning(f"No se pudo generar el analisis avanzado ({exc}). Se muestra la vista previa ligera.")
        fallback = get_light_preview_data(match_id)
        if not fallback or "error" in fallback:
            st.error(f"No se pudo generar ningun analisis: {fallback.get('error', 'sin datos') if isinstance(fallback, dict) else 'Error desconocido'}")
            return
        preview_html = build_light_preview_html(fallback, match)
        height = 520
    components.html(preview_html, height=height, scrolling=True)


def render_filters(matches: List[Dict[str, Any]], mode: str) -> None:
    ensure_filter_state(mode)
    options = extract_handicap_options(matches)
    filter_key = f"{mode}_handicap_filter_value"
    input_key = f"{mode}_handicap_filter_input"
    expanded = bool(st.session_state.get(filter_key))
    with st.expander("Filtrar por handicap", expanded=expanded):
        st.write("Introduce handicaps separados por comas. Ejemplo: `0, 0.25, -0.5`.")
        st.text_input(
            "Valores de handicap",
            key=input_key,
            placeholder="Ej. 0.25, -0.75",
        )
        if options:
            st.caption("Valores detectados en la tabla: " + ", ".join(options))
        action_cols = st.columns(2)
        if action_cols[0].button("Aplicar filtro", key=f"{mode}_apply_filter"):
            st.session_state[filter_key] = st.session_state.get(input_key, "").strip()
            st.rerun()
        if action_cols[1].button("Limpiar filtro", key=f"{mode}_clear_filter"):
            st.session_state[filter_key] = ""
            st.session_state[input_key] = ""
            st.rerun()



def build_match_card_html(match: Dict[str, Any], mode: str, active: bool) -> str:
    home = safe_text(match.get("home_team", "Local"))
    away = safe_text(match.get("away_team", "Visitante"))
    competition = safe_text(match.get("league") or match.get("competition") or match.get("country") or "Partido")

    date_value = ""
    for key in ("match_date", "date", "kickoff_date"):
        raw = match.get(key)
        if raw:
            date_value = safe_text(raw)
            break

    time_value = match.get("time") or match.get("match_time")
    if not time_value:
        time_obj = match.get("time_utc")
        if isinstance(time_obj, datetime):
            time_value = time_obj.strftime("%H:%M")
    time_text = safe_text(time_value) if time_value else "--:--"

    handicap_raw = safe_text(match.get("handicap", "N/A"))
    goal_line_raw = safe_text(match.get("goal_line", "N/A"))
    handicap_value = handicap_raw if handicap_raw and handicap_raw.upper() != "N/A" else "N/A"
    goal_line_value = goal_line_raw if goal_line_raw and goal_line_raw.upper() != "N/A" else "N/A"

    match_id = safe_text(match.get("id"))
    league_round = match.get("round") or match.get("stage")
    venue = match.get("venue") or match.get("stadium")
    meta_parts: List[str] = []
    if match_id:
        meta_parts.append(f"ID {match_id}")
    if league_round:
        meta_parts.append(safe_text(league_round))
    if venue:
        meta_parts.append(safe_text(venue))
    meta_html = f'<div class="match-row__meta">{" &middot; ".join(meta_parts)}</div>' if meta_parts else ""

    score_class = "match-row__score"
    score_text = "--"
    if mode == "finished":
        score_raw = safe_text(match.get("score", "")).strip()
        if score_raw:
            score_text = score_raw.replace(":", " - ")
        else:
            score_class += " match-row__score--placeholder"
    else:
        score_class += " match-row__score--placeholder"

    row_classes = ["match-row"]
    if mode == "finished":
        row_classes.append("match-row--finished")
    if active:
        row_classes.append("match-row--active")

    html_parts: List[str] = [
        f'<div class="{" ".join(row_classes)}">',
        "<div>",
        f'<div class="match-row__time">{time_text}</div>',
    ]
    if date_value:
        html_parts.append(f'<div class="match-row__date">{date_value}</div>')
    html_parts.append("</div>")

    html_parts.append("<div>")
    html_parts.append(f'<div class="match-row__league">{competition}</div>')
    html_parts.append('<div class="match-row__names">')
    html_parts.append(f'<span class="match-row__team">{home}</span>')
    html_parts.append('<span class="match-row__vs">vs</span>')
    html_parts.append(f'<span class="match-row__team match-row__team--away">{away}</span>')
    html_parts.append("</div>")
    if meta_html:
        html_parts.append(meta_html)
    html_parts.append("</div>")

    html_parts.append(
        '<div class="match-row__metric match-row__metric--ah">'
        '<span class="match-row__metric-label">AH</span>'
        f'<span class="match-row__metric-value">{handicap_value}</span>'
        "</div>"
    )
    html_parts.append(
        '<div class="match-row__metric match-row__metric--ou">'
        '<span class="match-row__metric-label">O/U</span>'
        f'<span class="match-row__metric-value">{goal_line_value}</span>'
        "</div>"
    )
    html_parts.append(f'<div class="{score_class}">{score_text}</div>')
    html_parts.append("</div>")
    return "".join(html_parts)

def render_mode_section(matches: List[Dict[str, Any]], mode: str) -> None:
    render_filters(matches, mode)
    filtered_matches, filter_error = apply_handicap_filter(matches, mode)
    if filter_error:
        st.warning(filter_error)
    total = len(matches)
    count = len(filtered_matches)
    st.write(f"Mostrando {count} de {total} partidos")

    if count == 0:
        st.info("No se encontraron partidos con los criterios seleccionados.")
        return

    if "active_preview_ids" not in st.session_state:
        st.session_state["active_preview_ids"] = []
    active_ids = {str(mid) for mid in st.session_state.get("active_preview_ids", [])}

    st.markdown('<div class="match-grid">', unsafe_allow_html=True)
    for idx, match in enumerate(filtered_matches):
        match_id = str(match.get("id", "")).strip()
        is_active = match_id in active_ids
        key_suffix = match_id or f"row_{idx}"

        info_col, estudio_col, preview_col = st.columns([24, 3, 3], gap="small")
        info_col.markdown(build_match_card_html(match, mode, is_active), unsafe_allow_html=True)

        if match_id:
            link_html = (
                f'<div class="match-actions-container"><a class="match-action-link" '
                f'href="?estudio_id={match_id}" target="_blank" title="Abrir estudio completo">Estudio</a></div>'
            )
        else:
            link_html = '<div class="match-actions-container"><span class="match-action-link" style="pointer-events:none; opacity:0.55;">Sin ID</span></div>'
        estudio_col.markdown(link_html, unsafe_allow_html=True)

        with preview_col:
            label = "Ocultar" if is_active else "Previa"
            if st.button(
                label,
                key=f"preview_button_{mode}_{key_suffix}_{idx}",
                help="Mostrar u ocultar esta vista previa dentro del panel",
                use_container_width=True,
            ):
                previews = [str(mid) for mid in st.session_state.get("active_preview_ids", [])]
                if match_id in previews:
                    previews = [mid for mid in previews if mid != match_id]
                else:
                    previews.append(match_id)
                st.session_state["active_preview_ids"] = previews
                st.rerun()

        if is_active:
            with st.container():
                render_preview_for_match(match)
        st.markdown('<div class="preview-spacer"></div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

def render_manual_analysis_form() -> None:
    st.divider()
    st.subheader("Analizar partido finalizado por ID")
    with st.form("manual_analysis_form"):
        match_id = st.text_input("ID del partido", key="manual_analysis_id")
        submitted = st.form_submit_button("Abrir estudio")
        if submitted:
            cleaned = match_id.strip()
            if not cleaned:
                st.warning("Introduce un ID valido.")
            else:
                st.query_params.update({"estudio_id": cleaned})
                st.rerun()


def run_main_page() -> None:
    global DATA_FILE
    data = load_data_from_file()
    upcoming = data.get("upcoming_matches", [])
    finished = data.get("finished_matches", [])

    header_col, action_col = st.columns([3, 1])
    with header_col:
        st.title("Panel Descarga_Todo en Streamlit")
        st.caption("Monitoriza los partidos y actualiza el dataset original cuando lo necesites.")
    with action_col:
        trigger_scraper = st.button("Actualizar datos", key="scraper_button", use_container_width=True)

    if trigger_scraper:
        with st.spinner("Ejecutando run_scraper.py..."):
            ensure_playwright()
            try:
                result = subprocess.run(
                    [sys.executable, str(SCRAPER_SCRIPT)],
                    capture_output=True,
                    text=True,
                    check=True,
                    cwd=str(SCRAPER_SCRIPT.parent),
                )
            except subprocess.CalledProcessError as exc:
                st.error("El scraping fallo. Revisa la salida mostrada.")
                if exc.stdout:
                    st.text_area("Salida del scraping", exc.stdout, height=220)
                if exc.stderr:
                    st.text_area("Errores", exc.stderr, height=220)
            else:
                st.success("Scraping completado. data.json actualizado.")
                if result.stdout.strip():
                    st.text_area("Salida del scraping", result.stdout, height=200)
                desc_data = SCRAPER_SCRIPT.parent / "data.json"
                root_data = PROJECT_ROOT / "data.json"
                if desc_data.exists():
                    DATA_FILE = desc_data
                    try:
                        shutil.copy2(desc_data, root_data)
                    except Exception as copy_exc:
                        st.warning(f"No se pudo sincronizar data.json en la raiz: {copy_exc}")
        st.cache_data.clear()
        st.rerun()

    kpi_cols = st.columns(3)
    kpi_cols[0].metric("Proximos", len(upcoming))
    kpi_cols[1].metric("Finalizados", len(finished))
    try:
        updated_dt = datetime.fromtimestamp(DATA_FILE.stat().st_mtime).astimezone()
        kpi_cols[2].metric("Ultima actualizacion", updated_dt.strftime("%d/%m %H:%M"))
    except FileNotFoundError:
        kpi_cols[2].metric("Ultima actualizacion", "Sin datos")

    st.divider()

    tab_upcoming, tab_finished = st.tabs([
        f"Proximos partidos ({len(upcoming)})",
        f"Resultados finalizados ({len(finished)})",
    ])
    with tab_upcoming:
        render_mode_section(upcoming, "upcoming")
    with tab_finished:
        render_mode_section(finished, "finished")
        render_manual_analysis_form()

def build_estudio_html(datos: Dict[str, Any]) -> Optional[str]:
    if JINJA_ENV is None:
        return None
    try:
        template = JINJA_ENV.get_template("estudio.html")
    except TemplateNotFound:
        return None

    analisis_html = ""
    try:
        main_odds = datos.get("main_match_odds_data")
        h2h_data = datos.get("h2h_data")
        home_name = datos.get("home_name")
        away_name = datos.get("away_name")
        if main_odds and h2h_data and home_name and away_name:
            analisis_html = generar_analisis_mercado_simplificado(main_odds, h2h_data, home_name, away_name)
    except Exception as exc:  # pragma: no cover - defensivo
        print(f"[streamlit_app] Error al generar analisis simplificado: {exc}")

    try:
        return template.render(
            data=datos,
            format_ah=format_ah_as_decimal_string_of,
            analisis_simplificado_html=analisis_html or "",
        )
    except Exception as exc:  # pragma: no cover - defensivo
        print(f"[streamlit_app] Error al renderizar plantilla estudio: {exc}")
        return None


def render_estudio_view(match_id: str) -> None:

    with st.spinner("Cargando estudio completo..."):
        data = obtener_datos_completos_partido(match_id)

    if not data or "error" in data:
        st.error(data.get("error", "No se pudo cargar el estudio."))
        if st.button("Regresar al panel", key="back_button_error"):
            st.query_params.clear()
            st.session_state["active_preview_ids"] = []
            st.rerun()
        return

    estudio_html = build_estudio_html(data)
    if estudio_html:
        components.html(estudio_html, height=1300, scrolling=True)
    else:
        st.info("No fue posible renderizar la plantilla completa. Se muestran los datos sin formato.")
        st.json(data)

    if st.button("Volver al panel principal", key="back_button_bottom"):
        st.query_params.clear()
        st.session_state["active_preview_ids"] = []
        st.rerun()


def main() -> None:
    inject_global_styles()
    if "active_preview_ids" not in st.session_state:
        st.session_state["active_preview_ids"] = []

    query_params = st.query_params
    raw_estudio = query_params.get("estudio_id")
    if isinstance(raw_estudio, list):
        estudio_id = raw_estudio[0] if raw_estudio else None
    else:
        estudio_id = raw_estudio

    if estudio_id:
        render_estudio_view(str(estudio_id))
    else:
        run_main_page()


main()






