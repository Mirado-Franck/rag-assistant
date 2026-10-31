"""
theme.py — Design system de DocuClassif AI (partie B1).

Style « ChatGPT-like » : fond blanc, gris très clair pour la sidebar,
cartes à bordure fine, coins arrondis, typographie système, zéro emoji
décoratif. Tout est inline : aucune ressource externe (le projet doit
rester 100 % offline).
"""

from __future__ import annotations

import base64

import streamlit as st

# ---------------------------------------------------------------------------
# Palette
# ---------------------------------------------------------------------------
INK = "#0d0d0d"
MUTED = "#5d5d6b"
FAINT = "#8e8e9a"
BG = "#ffffff"
BG_SOFT = "#f9f9f9"
BORDER = "#e6e6e6"
HOVER = "#ececec"
GREEN = "#10a37f"
AMBER = "#c98a00"
RED = "#d93025"

# Accent principal (boutons primaires, liens, logo) et teintes par ton.
# Chaque ton = (couleur vive, fond doux) : utilisé pour les icônes, puces,
# barres et graphiques. Les 5 catégories ont chacune leur ton fixe.
ACCENT = "#4f46e5"
ACCENT_SOFT = "#eef2ff"
TONES = {
    "indigo": ("#4f46e5", "#eef2ff"),
    "teal": ("#0d9488", "#f0fdfa"),
    "orange": ("#ea580c", "#fff7ed"),
    "blue": ("#2563eb", "#eff6ff"),
    "pink": ("#db2777", "#fdf2f8"),
    "green": ("#059669", "#ecfdf5"),
}
# Correspondance catégorie -> ton. Clés en minuscules et sans accents, pour
# accepter les libellés courts de la maquette ET les libellés complets de l'API.
_CATEGORY_TONE_KEYS = {
    "reglements": "indigo",
    "guides pratiques": "teal",
    "procedures": "orange",
    "organisation": "blue",
    "formulaires": "pink",
}


def _fold(value: str) -> str:
    import unicodedata

    value = unicodedata.normalize("NFKD", value.casefold())
    return "".join(c for c in value if not unicodedata.combining(c)).strip()


def category_tone(label: str) -> tuple[str, str]:
    """Renvoie (couleur, fond doux) d'une catégorie ; repli sur l'accent."""
    key = _fold(label)
    for prefix, tone in _CATEGORY_TONE_KEYS.items():
        if key.startswith(prefix):
            return TONES[tone]
    return TONES["indigo"]


def category_color(label: str) -> str:
    return category_tone(label)[0]

# ---------------------------------------------------------------------------
# Icônes (SVG inline, stroke = hérite de la couleur du texte)
# ---------------------------------------------------------------------------
_PATHS = {
    "upload": '<path d="M12 16V4m0 0L8 8m4-4 4 4"/><path d="M4 16v2a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-2"/>',
    "chat": '<path d="M21 12a8 8 0 0 1-8 8H7l-4 3V12a8 8 0 0 1 8-8h2a8 8 0 0 1 8 8Z"/><path d="M9 11h6M9 15h3"/>',
    "chart": '<path d="M4 20V10m5 10V4m5 16v-7m5 7V8"/>',
    "shield": '<path d="M12 3 5 6v6c0 4.4 3 7.6 7 9 4-1.4 7-4.6 7-9V6l-7-3Z"/><path d="m9 12 2 2 4-4"/>',
    "search": '<circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/>',
    "file": '<path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8l-5-5Z"/><path d="M14 3v5h5"/>',
    "check": '<path d="m4 12 5 5L20 6"/>',
    "clock": '<circle cx="12" cy="12" r="8"/><path d="M12 8v4l3 2"/>',
    "layers": '<path d="m12 3 9 5-9 5-9-5 9-5Z"/><path d="m3 13 9 5 9-5"/>',
    "scale": '<path d="M12 4v16M7 20h10M6 8h12M6 8 3 15h6L6 8Zm12 0-3 7h6l-3-7Z"/>',
    "book": '<path d="M4 5a2 2 0 0 1 2-2h5v18H6a2 2 0 0 1-2-2V5Z"/><path d="M20 5a2 2 0 0 0-2-2h-5v18h5a2 2 0 0 0 2-2V5Z"/>',
    "flow": '<rect x="9" y="3" width="6" height="5" rx="1.5"/><rect x="2" y="16" width="6" height="5" rx="1.5"/><rect x="16" y="16" width="6" height="5" rx="1.5"/><path d="M12 8v4M5 16v-2h14v2"/>',
    "calendar": '<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M8 3v4m8-4v4M3 11h18"/>',
    "form": '<rect x="4" y="3" width="16" height="18" rx="2"/><path d="M8 8h8M8 12h8M8 16h4"/>',
    "sparkle": '<path d="M12 3l1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8L12 3Z"/>',
    "arrow": '<path d="M5 12h14m0 0-5-5m5 5-5 5"/>',
}


def icon(name: str, size: int = 18, color: str = INK, stroke: float = 1.6) -> str:
    """
    Renvoie une icône SVG sous forme de data-URI (<img>).

    Pourquoi pas du <svg> inline ? Le sanitizer de `st.html` supprime les
    balises <svg> injectées en HTML brut ; une image data-URI passe et
    s'affiche dans tous les navigateurs, sans aucune requête réseau.
    """
    paths = _PATHS.get(name, _PATHS["file"])
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="{size}" '
        f'height="{size}" fill="none" stroke="{color}" stroke-width="{stroke}" '
        f'stroke-linecap="round" stroke-linejoin="round">{paths}</svg>'
    )
    b64 = base64.b64encode(svg.encode("utf-8")).decode("ascii")
    return (
        f'<img alt="" src="data:image/svg+xml;base64,{b64}" width="{size}" height="{size}" '
        f'style="display:inline-block;vertical-align:-3px;flex:none;width:{size}px;height:{size}px" />'
    )


# ---------------------------------------------------------------------------
# CSS global (source : interface/assets/style.css)
# ---------------------------------------------------------------------------
from pathlib import Path

_CSS_PATH = Path(__file__).resolve().parent / "assets" / "style.css"


def load_css() -> str:
    """Lit le CSS du design system. Repli silencieux si le fichier manque."""
    try:
        return f"<style>{_CSS_PATH.read_text(encoding='utf-8')}</style>"
    except OSError:
        return "<style></style>"


CSS = ""


def html(markup: str) -> None:
    """
    Rend du HTML brut de façon compatible entre versions de Streamlit.
    `st.html` (>=1.33) évite le parsing Markdown qui casse les blocs indentés ;
    repli sur st.markdown(unsafe_allow_html=True) pour les versions plus anciennes.
    """
    markup = " ".join(line.strip() for line in markup.strip().splitlines())
    try:
        st.html(markup)
    except AttributeError:
        st.markdown(markup, unsafe_allow_html=True)


def inject() -> None:
    """Injecte le CSS du design system (à appeler une seule fois par rerun)."""
    css = load_css()
    try:
        st.html(css)
    except AttributeError:
        st.markdown(css, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Composants HTML
# ---------------------------------------------------------------------------
def page_header(title: str, subtitle: str, eyebrow: str = "") -> None:
    html(
        f"""<div class="dc-page">
        <div class="dc-accent"></div>
        {f'<div class="dc-eyebrow">{eyebrow}</div>' if eyebrow else ''}
        <div class="dc-title">{title}</div>
        <p class="dc-subtitle">{subtitle}</p>
        </div>"""
    )


def section(title: str, hint: str = "") -> None:
    html(
        f'<div class="dc-section"><h4>{title}</h4>'
        f'{f"<span>{hint}</span>" if hint else ""}</div>'
    )


def card(title: str, body: str, ico: str = "file", tone: str = "indigo") -> str:
    color, soft = TONES.get(tone, TONES["indigo"])
    return (
        f'<div class="dc-card"><div class="dc-card-icon" '
        f'style="background:{soft};border-color:transparent;color:{color}">{icon(ico, 16, color)}</div>'
        f"<h5>{title}</h5><p>{body}</p></div>"
    )


def card_grid(items: list[tuple], per_row: int = 2) -> None:
    """Affiche une grille de cartes (title, body, icon[, tone])."""
    rows = [items[i : i + per_row] for i in range(0, len(items), per_row)]
    for row in rows:
        cols = st.columns(len(row), gap="small")
        for col, item in zip(cols, row):
            title, body, ico = item[:3]
            tone = item[3] if len(item) > 3 else "indigo"
            with col:
                html(card(title, body, ico, tone))


def stat_cards(items: list[dict]) -> None:
    """items = [{'label','value','delta'(opt),'muted'(bool),'tone'(opt)}]"""
    cols = st.columns(len(items), gap="small")
    for col, it in zip(cols, items):
        delta = it.get("delta", "")
        color, soft = TONES.get(it.get("tone", "indigo"), TONES["indigo"])
        cls = "dc-stat-delta muted" if it.get("muted") else "dc-stat-delta"
        style = "" if it.get("muted") else f' style="color:{color}"'
        delta_html = f'<div class="{cls}"{style}>{delta}</div>' if delta else ""
        with col:
            html(
                f'<div class="dc-stat" style="border-top:3px solid {color}">'
                f'<div class="dc-stat-label">{it["label"]}</div>'
                f'<div class="dc-stat-value">{it["value"]}</div>'
                f"{delta_html}</div>"
            )


def badge(text: str, warn: bool = False) -> str:
    cls = "dc-badge warn" if warn else "dc-badge"
    return f'<span class="{cls}"><span class="dot"></span>{text}</span>'


def chips(items: list[tuple[str, str, str]]) -> None:
    """items = [(label, count, icon)] — la couleur suit la catégorie du libellé."""
    parts = []
    for label, count, i in items:
        color, soft = category_tone(label)
        parts.append(
            f'<span class="dc-chip" style="background:{soft};border-color:{soft}">'
            f'<span class="dc-chip-ico" style="background:#fff;color:{color}">{icon(i, 12, color)}</span>'
            f'<b style="color:{color}">{label}</b> {count}</span>'
        )
    html(f"<div>{''.join(parts)}</div>")


def kv(items: list[tuple[str, str]]) -> None:
    markup = "".join(f"<span>{k} <b>{v}</b></span>" for k, v in items)
    html(f'<div class="dc-kv">{markup}</div>')


def divider() -> None:
    html('<div class="dc-divider"></div>')


def sidebar_brand(name: str, version: str) -> None:
    html(
        f"""<div class="dc-side-brand">
        <div class="logo">{icon("sparkle", 17, "#ffffff")}</div>
        <div><div class="name">{name}</div><div class="ver">{version}</div></div>
        </div>"""
    )


def sidebar_label(text: str) -> None:
    html(f'<div class="dc-side-label">{text}</div>')


def sidebar_system(rows: list[tuple[str, str]], note: str) -> None:
    lines = "".join(f'<div class="line"><span>{k}</span><b>{v}</b></div>' for k, v in rows)
    html(f'<div class="dc-side-box">{lines}</div>')
    html(f'<div class="dc-side-foot">{note}</div>')


# ---------------------------------------------------------------------------
# Helpers compatibles entre versions de Streamlit (API `width=` récente)
# ---------------------------------------------------------------------------
def button(label: str, *, key: str | None = None, primary: bool = False,
           full: bool = False, help: str | None = None) -> bool:
    base: dict = {}
    if key:
        base["key"] = key
    if help:
        base["help"] = help
    if primary:
        base["type"] = "primary"
    variants = ({"width": "stretch"}, {"use_container_width": True}) if full else ({},)
    for extra in variants:
        try:
            return st.button(label, **base, **extra)
        except TypeError:
            continue
    return st.button(label, **base)


def dataframe(data, **kwargs):
    try:
        return st.dataframe(data, width="stretch", **kwargs)
    except TypeError:
        return st.dataframe(data, use_container_width=True, **kwargs)


def chart(fig, key: str | None = None):
    """Affiche un graphique Altair en pleine largeur (API compatible)."""
    for extra in ({"width": "stretch"}, {"use_container_width": True}):
        try:
            return st.altair_chart(fig, theme=None, **extra)
        except TypeError:
            continue
    return st.altair_chart(fig, theme=None)
