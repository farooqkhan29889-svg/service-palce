"""Presentation helpers for the customer app.

Icons, initials, the colour palette and formatting shared across the pages.
Keeping them here means the pages stay focused on layout.

The customer app deliberately does not change the repository theme file
(``theme/servenow-brand.toml``), because the admin console shares it. Instead
``brand_css`` returns one stylesheet that the entry point injects, so the
customer look can differ from the console without a second deployment config.
"""
import streamlit as st

# The MistriHub-style palette: warm amber on charcoal and cream.
PALETTE = {
    "amber": "#F5A524",
    "amber-deep": "#E08600",
    "ink": "#1B1B1B",
    "ink-soft": "#2A2724",
    "cream": "#FBF6EE",
    "card": "#FFFFFF",
    "border": "#EFE3D0",
    "muted": "#6B6257",
    "green": "#16A34A",
}

# Inline SVG mark - a house on charcoal with an amber roofline. Inline keeps
# the app free of binary assets and lets Streamlit serve it straight from the
# page.
LOGO_SVG = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="64" height="64">
  <defs>
    <linearGradient id="sn" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#F5A524"/>
      <stop offset="100%" stop-color="#E08600"/>
    </linearGradient>
  </defs>
  <rect x="2" y="2" width="60" height="60" rx="17" fill="#1B1B1B"/>
  <path d="M32 15 L48 29 H41 V47 H36.5 V35.5 H27.5 V47 H23 V29 H16 Z" fill="url(#sn)"/>
</svg>
"""

# Material Symbols names, matched on the service or category name.
SERVICE_ICONS = {
    "electric": "electric_bolt",
    "plumb": "plumbing",
    "carpent": "carpenter",
    "paint": "format_paint",
    "ac ": "ac_unit",
    "air condition": "ac_unit",
    "refrigerat": "ac_unit",
    "clean": "cleaning_services",
    "pest": "pest_control",
    "labour": "construction",
    "labor": "construction",
    "appliance": "home_repair_service",
    "roof": "roofing",
    "garden": "local_florist",
    "beauty": "auto_awesome",
    "salon": "auto_awesome",
    "furniture": "chair",
    "moving": "local_shipping",
    "water": "water_drop",
    "sanit": "water_drop",
}

CATEGORY_ICONS = {
    "home": "home",
    "appliance": "build",
    "labour": "engineering",
    "clean": "cleaning_services",
    "pest": "pest_control",
    "garden": "local_florist",
    "beauty": "auto_awesome",
    "carpenter": "carpenter",
    "electrical": "electric_bolt",
    "repair": "handyman",
}

DEFAULT_SERVICE_ICON = "handyman"
DEFAULT_CATEGORY_ICON = "category"


def service_icon(service):
    """Pick a Material Symbol for a service, based on its name."""
    haystack = f"{service.get('name', '')} {service.get('category', '')}".lower()
    for keyword, icon in SERVICE_ICONS.items():
        if keyword in haystack:
            return icon
    return DEFAULT_SERVICE_ICON


def category_icon(category):
    """Pick a Material Symbol for a service category."""
    haystack = str(category or "").lower()
    for keyword, icon in CATEGORY_ICONS.items():
        if keyword in haystack:
            return icon
    return DEFAULT_CATEGORY_ICON


def initials(name):
    """Up to two uppercase initials from a display name."""
    parts = [part for part in str(name or "").split() if part]
    if not parts:
        return "?"
    if len(parts) == 1:
        return parts[0][:2].upper()
    return (parts[0][0] + parts[-1][0]).upper()


def avatar_tile(name, size=54):
    """An initials circle, as used on the provider cards."""
    return f"""
<div style="
  width:{size}px;
  height:{size}px;
  border-radius:50%;
  background:#FFF1D6;
  border:1px solid #F3DFB8;
  color:#B25E00;
  display:flex;
  align-items:center;
  justify-content:center;
  font-family:'Plus Jakarta Sans',sans-serif;
  font-weight:800;
  font-size:{int(size * 0.36)}px;
">{initials(name)}</div>
"""


def chip_row(labels):
    """A wrapped row of small pill chips for ratings, location and experience."""
    style = (
        "display:inline-flex;align-items:center;background:#FFF7E8;"
        "border:1px solid #F1E2C6;color:#6B6257;border-radius:999px;"
        "padding:0.2rem 0.62rem;font-size:0.78rem;font-weight:600;white-space:nowrap;"
    )
    pills = "".join(f'<span style="{style}">{label}</span>' for label in labels)
    return f'<div style="display:flex;flex-wrap:wrap;gap:0.4rem;">{pills}</div>'


def inr(amount):
    """Format a number as Indian rupees."""
    return f"₹{float(amount or 0):,.0f}"


def stars(rating):
    """A five star string for a numeric rating."""
    try:
        value = float(rating or 0)
    except (TypeError, ValueError):
        value = 0
    filled = max(0, min(5, round(value)))
    return "★" * filled + "☆" * (5 - filled)


def icon_tile(icon, size=52):
    """A rounded amber tile holding a Material Symbols glyph.

    Streamlit loads the Material Symbols Rounded font for its own icons, so
    the glyph can be reused inside custom markup.
    """
    return f"""
<div style="
  width:{size}px;
  height:{size}px;
  border-radius:16px;
  background:linear-gradient(150deg,#FFF6E2,#FFEAC4);
  border:1px solid #F3DFB8;
  box-shadow:0 8px 16px -12px rgba(224,134,0,0.55);
  display:flex;
  align-items:center;
  justify-content:center;
">
  <span style="
    font-family:'Material Symbols Rounded';
    font-size:{int(size * 0.5)}px;
    line-height:1;
    color:#B25E00;
  ">{icon}</span>
</div>
"""


def warranty_band(badge, headline, subline, icon="verified_user"):
    """A charcoal trust band with an amber headline and a shield tile."""
    return f"""
<div style="
  background:#1B1B1B;
  border-radius:18px;
  padding:1.1rem 1.15rem;
  display:flex;
  align-items:center;
  justify-content:space-between;
  gap:0.9rem;
">
  <div>
    <div style="
      color:rgba(251,246,238,0.65);
      font-size:0.72rem;
      font-weight:700;
      letter-spacing:0.12em;
      text-transform:uppercase;
    ">{badge}</div>
    <div style="
      font-family:'Plus Jakarta Sans',sans-serif;
      color:#F5A524;
      font-size:1.12rem;
      font-weight:800;
      line-height:1.25;
      margin-top:0.25rem;
    ">{headline}</div>
    <div style="color:rgba(251,246,238,0.72);font-size:0.9rem;margin-top:0.3rem;">{subline}</div>
  </div>
  <div style="
    width:56px;
    height:56px;
    flex:0 0 56px;
    border-radius:18px;
    background:rgba(245,165,36,0.14);
    border:1px solid rgba(245,165,36,0.35);
    display:flex;
    align-items:center;
    justify-content:center;
  ">
    <span style="
      font-family:'Material Symbols Rounded';
      font-size:28px;
      line-height:1;
      color:#F5A524;
    ">{icon}</span>
  </div>
</div>
"""


def choice_row(label, labels, values, key):
    """A row of pill buttons used as a single-choice picker.

    Streamlit's own pickers (radio, pills, segmented control) paint their
    selected state with the theme's primary colour, which the customer app
    cannot change without affecting the admin console. Buttons are already
    styled by the brand layer, so the app uses them instead. The caller must
    place this outside a form: buttons inside a form only report a click when
    the form is submitted.
    """
    st.markdown(f"**{label}**")
    selected = st.session_state.get(key)
    if selected not in values:
        selected = values[0]
        st.session_state[key] = selected

    with st.container(horizontal=True):
        for option_label, value in zip(labels, values):
            picked = st.button(
                option_label,
                key=f"{key}_{value}",
                type="primary" if value == selected else "secondary",
            )
            if picked and value != selected:
                st.session_state[key] = value
                st.rerun()

    return st.session_state[key]


def hero_banner(eyebrow, headline, subline):
    """A warm gradient hero panel.

    Streamlit has no native element for a full-width gradient banner, so this
    is the one place the app uses custom markup. It styles a single container
    and never targets Streamlit's own classes.
    """
    return f"""
<div style="
  position:relative;
  overflow:hidden;
  background:linear-gradient(135deg,#FFC078 0%,#F5A524 45%,#E08600 100%);
  border-radius:22px;
  padding:1.6rem 1.25rem;
  color:#1B1B1B;
  box-shadow:0 22px 48px -24px rgba(224,134,0,0.6);
">
  <div style="
    position:absolute;
    top:-55%;
    right:-12%;
    width:420px;
    height:420px;
    border-radius:50%;
    background:radial-gradient(circle,rgba(255,255,255,0.42),transparent 62%);
    pointer-events:none;
  "></div>
  <div style="position:relative;">
    <div style="
      display:inline-block;
      background:#1B1B1B;
      border-radius:999px;
      padding:0.35rem 0.95rem;
      font-size:0.78rem;
      font-weight:700;
      letter-spacing:0.04em;
      color:#F5A524;
      margin-bottom:1.1rem;
      box-shadow:0 8px 18px -12px rgba(27,27,27,0.9);
    ">{eyebrow}</div>
    <div style="
      font-family:'Plus Jakarta Sans',sans-serif;
      font-size:1.8rem;
      line-height:1.15;
      font-weight:800;
      letter-spacing:-0.025em;
    ">{headline}</div>
    <div style="
      margin-top:0.7rem;
      font-size:0.95rem;
      line-height:1.6;
      color:rgba(27,27,27,0.78);
    ">{subline}</div>
  </div>
</div>
"""


_BRAND_CSS = """
:root {
%VARS%
}

/* ---------- canvas ---------- */
/* Two soft amber glows over warm cream, so the page never reads as flat grey.
   background-attachment keeps the glows pinned while the page scrolls. */
[data-testid="stAppViewContainer"] {
  background:
    radial-gradient(1100px 620px at 88% -8%, rgba(245, 165, 36, 0.20), transparent 62%),
    radial-gradient(900px 560px at -6% 24%, rgba(224, 134, 0, 0.10), transparent 60%),
    linear-gradient(180deg, #FFFCF6 0%, var(--sn-cream) 46%, #F6EEDF 100%);
  background-attachment: fixed;
  color: var(--sn-ink);
}
/* The header is sticky, so a fully transparent one lets cards scroll straight
   under the logo and menu controls. A translucent cream veil keeps the app-bar
   readable without a hard edge. */
[data-testid="stHeader"] {
  background: rgba(251, 246, 238, 0.82);
  backdrop-filter: blur(8px);
}
[data-testid="stAppDeployButton"],
[data-testid="stToolbarActions"] { display: none; }
/* Phone column: the app is a mobile UI, so the content sits in a single
   centred strip the width of a large handset instead of a wide web page. */
[data-testid="stMainBlockContainer"] {
  padding: 1.15rem 1.05rem 6.5rem;
  max-width: 560px;
  margin-left: auto;
  margin-right: auto;
}
[data-testid="stMain"] h1 { font-size: 1.5rem !important; }
[data-testid="stMain"] h2 { font-size: 1.3rem !important; }
[data-testid="stMain"] h3 { font-size: 1.1rem !important; }
[data-testid="stMain"] h4 { font-size: 1rem !important; }
/* 16px input text keeps iOS from zooming the page when a field is focused. */
[data-testid="stTextInput"] input,
[data-testid="stTextArea"] textarea,
[data-testid="stNumberInput"] input { font-size: 1rem !important; }
::selection { background: rgba(245, 165, 36, 0.35); }
::-webkit-scrollbar { width: 10px; height: 10px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb {
  background: #E4D5BC;
  border-radius: 999px;
  border: 2px solid transparent;
  background-clip: content-box;
}
::-webkit-scrollbar-thumb:hover { background: var(--sn-amber); background-clip: content-box; }

/* ---------- type ---------- */
h1, h2, h3, h4, h5 {
  color: var(--sn-ink) !important;
  letter-spacing: -0.02em;
  font-family: 'Plus Jakarta Sans', sans-serif;
}
/* Main-area headings get a small amber bar, which gives every section a
   consistent start without editing each page. */
[data-testid="stMain"] h2,
[data-testid="stMain"] h3 {
  position: relative;
  padding-left: 0.95rem;
}
[data-testid="stMain"] h2::before,
[data-testid="stMain"] h3::before {
  content: "";
  position: absolute;
  left: 0;
  top: 0.18em;
  width: 5px;
  height: 0.95em;
  border-radius: 999px;
  background: linear-gradient(180deg, var(--sn-amber), var(--sn-amber-deep));
}
[data-testid="stCaptionContainer"],
[data-testid="stMarkdownContainer"] p { color: var(--sn-muted); }
a { color: var(--sn-amber-deep); }
hr { border-color: var(--sn-border); }

/* ---------- cards ---------- */
/* Only st.container(border=True) renders as a vertical block directly under a
   layout wrapper, which is what this selector matches. */
[data-testid="stLayoutWrapper"] > [data-testid="stVerticalBlock"] {
  background: rgba(255, 255, 255, 0.92);
  backdrop-filter: blur(6px);
  border: 1px solid var(--sn-border) !important;
  border-radius: 18px !important;
  padding: 0.9rem 0.95rem !important;
  box-shadow: 0 14px 30px -26px rgba(27, 27, 27, 0.45);
  transition: box-shadow 0.18s ease, transform 0.18s ease, border-color 0.18s ease;
}
[data-testid="stLayoutWrapper"] > [data-testid="stVerticalBlock"]:hover {
  transform: translateY(-3px);
  border-color: #F0D6A6 !important;
  box-shadow: 0 26px 44px -28px rgba(224, 134, 0, 0.55);
}

/* ---------- touch targets ---------- */
/* Minimum 44px so the app is usable with a thumb, which is the one thing a
   desktop-designed Streamlit page always gets wrong. */
[data-testid="stMain"] button,
[data-testid="stMain"] [role="button"],
[data-testid="stSidebar"] [data-testid="stSidebarNavLink"] {
  min-height: 44px;
}
[data-testid="stMain"] [data-testid="stHorizontalBlock"] { gap: 0.55rem !important; }
/* Streamlit lets column rows wrap, which on a phone width breaks a card's
   icon / name / price row onto three separate lines. st.columns() renders as a
   horizontal block whose direct children are stColumn elements, so that is the
   row we pin. st.container(horizontal=True) has no stColumn children and is
   left free to wrap, which is what the stat row wants. (:has() is used
   standalone here - it cannot be nested.) */
[data-testid="stMain"] [data-testid="stHorizontalBlock"]:has(> [data-testid="stColumn"]) {
  flex-wrap: nowrap !important;
}
[data-testid="stMain"] [data-testid="stColumn"],
[data-testid="stMain"] [data-testid="stColumn"] > * {
  min-width: 0 !important;
}

/* ---------- buttons as pills ---------- */
[data-testid="stBaseButton-primary"] {
  background: linear-gradient(135deg, #FFBB4A 0%, var(--sn-amber) 55%, var(--sn-amber-deep) 100%) !important;
  color: var(--sn-ink) !important;
  border: none !important;
  border-radius: 999px !important;
  font-weight: 700;
  letter-spacing: -0.01em;
  box-shadow: 0 10px 20px -12px rgba(245, 165, 36, 0.95);
  transition: transform 0.14s ease, box-shadow 0.14s ease, filter 0.14s ease;
}
[data-testid="stBaseButton-primary"]:hover {
  filter: saturate(1.08);
  transform: translateY(-1px);
  box-shadow: 0 16px 26px -14px rgba(224, 134, 0, 0.95);
}
[data-testid="stBaseButton-primary"]:active { transform: translateY(1px); }
[data-testid="stBaseButton-secondary"],
[data-testid="stBaseButton-secondaryFormSubmit"] {
  background: var(--sn-card) !important;
  color: var(--sn-ink) !important;
  border: 1px solid var(--sn-border) !important;
  border-radius: 999px !important;
  font-weight: 600;
  transition: transform 0.14s ease, box-shadow 0.14s ease, border-color 0.14s ease;
}
[data-testid="stBaseButton-secondary"]:hover,
[data-testid="stBaseButton-secondaryFormSubmit"]:hover {
  border-color: var(--sn-amber) !important;
  background: #FFF7E8 !important;
  transform: translateY(-1px);
  box-shadow: 0 10px 18px -14px rgba(224, 134, 0, 0.7);
}
[kind="primary"]:focus-visible,
[kind="secondary"]:focus-visible {
  outline: 3px solid rgba(245, 165, 36, 0.35) !important;
  outline-offset: 2px;
}

/* ---------- inputs ---------- */
[data-testid="stTextInputRootElement"],
[data-testid="stTextAreaRootElement"] {
  background: var(--sn-card);
  border: 1px solid var(--sn-border);
  border-radius: 14px !important;
  transition: border-color 0.16s ease, box-shadow 0.16s ease;
}
[data-testid="stTextInputRootElement"]:focus-within,
[data-testid="stTextAreaRootElement"]:focus-within {
  border-color: var(--sn-amber) !important;
  box-shadow: 0 0 0 4px rgba(245, 165, 36, 0.18);
}
[data-testid="stTextInput"] input,
[data-testid="stTextArea"] textarea { color: var(--sn-ink) !important; }
[data-testid="stTextInput"] input::placeholder,
[data-testid="stTextArea"] textarea::placeholder { color: #B4A891; }
[data-testid="stWidgetLabel"] p {
  color: var(--sn-ink) !important;
  font-weight: 700;
  letter-spacing: -0.01em;
}

/* ---------- metrics as stat cards ---------- */
[data-testid="stMetric"] {
  background: linear-gradient(180deg, #FFFDF9, #FDF6E9);
  border: 1px solid var(--sn-border);
  border-radius: 18px;
  padding: 0.85rem 1rem;
}
[data-testid="stMetricValue"] {
  color: var(--sn-ink) !important;
  font-family: 'Plus Jakarta Sans', sans-serif;
  font-weight: 800;
}
[data-testid="stMetricLabel"] {
  color: var(--sn-muted) !important;
  text-transform: uppercase;
  letter-spacing: 0.07em;
  font-size: 0.72rem !important;
  font-weight: 600;
}

/* ---------- range slider ---------- */
/* The track and the thumb are painted with the theme's primary colour and
   carry no test ids. The thumb is the parent of stSliderThumbValue; the track
   is the first child of the thumb's parent. (:has() cannot be nested, so the
   parent is matched with a descendant path.) */
[data-testid="stSlider"] div:has(> div > [data-testid="stSliderThumbValue"]) > div:first-child {
  background: var(--sn-border) !important;
  background-image: none !important;
}
[data-testid="stSlider"] div:has(> [data-testid="stSliderThumbValue"]) {
  background: var(--sn-amber) !important;
}
[data-testid="stSlider"] [data-testid="stSliderThumbValue"] {
  color: var(--sn-amber-deep) !important;
}

/* ---------- select and number controls ---------- */
[data-baseweb="select"] > div {
  background: var(--sn-card) !important;
  border-color: var(--sn-border) !important;
  border-radius: 14px !important;
}
[data-testid="stNumberInput"] input { background: var(--sn-card) !important; }
[data-testid="stNumberInputContainer"] { border-color: var(--sn-border) !important; }

/* ---------- callouts (st.success / info / warning / error) ---------- */
[data-testid="stAlert"] {
  border-radius: 16px !important;
  border-width: 1px !important;
  font-weight: 500;
  box-shadow: 0 12px 24px -24px rgba(27, 27, 27, 0.5);
}
[data-testid="stAlert"]:has([data-testid="stAlertContentSuccess"]) {
  background: #F1FBF4 !important;
  border-color: #BBE7C9 !important;
}
[data-testid="stAlert"]:has([data-testid="stAlertContentInfo"]) {
  background: #FFFBF2 !important;
  border-color: #F1E2C6 !important;
}
[data-testid="stAlert"]:has([data-testid="stAlertContentWarning"]) {
  background: #FFF6E6 !important;
  border-color: #F0D08A !important;
}
[data-testid="stAlert"]:has([data-testid="stAlertContentError"]) {
  background: #FDF1F0 !important;
  border-color: #F2C4BF !important;
}

/* ---------- expanders ---------- */
[data-testid="stExpander"] {
  background: var(--sn-card);
  border: 1px solid var(--sn-border) !important;
  border-radius: 18px !important;
  overflow: hidden;
}
[data-testid="stExpander"] summary { font-weight: 700; color: var(--sn-ink); }
[data-testid="stExpander"] summary:hover { color: var(--sn-amber-deep); }

/* ---------- forms ---------- */
[data-testid="stForm"] {
  background: rgba(255, 255, 255, 0.9) !important;
  border: 1px solid var(--sn-border) !important;
  border-radius: 22px !important;
  box-shadow: 0 18px 34px -30px rgba(27, 27, 27, 0.5);
}

/* ---------- tables and codes ---------- */
[data-testid="stDataFrame"] {
  border: 1px solid var(--sn-border);
  border-radius: 18px;
  overflow: hidden;
}
[data-testid="stCode"] {
  background: #221F1B !important;
  border-radius: 14px !important;
}

/* ---------- progress ---------- */
[data-testid="stProgress"] > div > div:first-child {
  background: var(--sn-border) !important;
}
[data-testid="stProgress"] > div > div:last-child > div {
  background: linear-gradient(90deg, var(--sn-amber), var(--sn-amber-deep)) !important;
}

/* ---------- sidebar as a charcoal nav rail ---------- */
[data-testid="stSidebar"],
[data-testid="stSidebarContent"] {
  background:
    radial-gradient(420px 260px at 100% 0%, rgba(245, 165, 36, 0.16), transparent 65%),
    linear-gradient(165deg, var(--sn-ink) 0%, #17161A 55%, var(--sn-ink-soft) 100%);
  color: var(--sn-cream);
  border-right: 1px solid rgba(255, 255, 255, 0.08);
}
[data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
  backdrop-filter: none !important;
}
[data-testid="stSidebar"] [data-testid="stVerticalBlock"]:hover {
  transform: none !important;
  box-shadow: none !important;
}
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 { color: var(--sn-cream) !important; }
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p {
  color: rgba(251, 246, 238, 0.82) !important;
}
[data-testid="stSidebarNavLink"] {
  border-radius: 999px !important;
  color: rgba(251, 246, 238, 0.72) !important;
  font-weight: 600;
  padding: 0.5rem 0.95rem !important;
  transition: background 0.15s ease, color 0.15s ease, transform 0.15s ease;
}
[data-testid="stSidebarNavLink"]:hover {
  background: rgba(255, 255, 255, 0.10) !important;
  color: var(--sn-cream) !important;
  transform: translateX(2px);
}
[data-testid="stSidebarNavLink"][aria-current="page"] {
  background: linear-gradient(135deg, #FFBB4A, var(--sn-amber-deep)) !important;
  color: var(--sn-ink) !important;
  font-weight: 800;
  box-shadow: 0 10px 22px -12px rgba(245, 165, 36, 0.9);
  transform: none;
}
[data-testid="stSidebar"] [data-testid="stTextInputRootElement"] {
  background: var(--sn-ink-soft);
  border-color: rgba(255, 255, 255, 0.14);
}
[data-testid="stSidebar"] [data-testid="stTextInput"] input { color: var(--sn-cream) !important; }
[data-testid="stSidebar"] [data-testid="stForm"] {
  background: transparent;
  border-color: rgba(255, 255, 255, 0.12) !important;
}
[data-testid="stSidebar"] [data-testid="stTab"] { color: rgba(251, 246, 238, 0.65) !important; }
[data-testid="stSidebar"] [data-testid="stTab"][aria-selected="true"] {
  color: var(--sn-amber) !important;
}
/* The tab underline is an absolutely positioned child div that inherits the
   theme's sidebar primary colour. The label is stMarkdownContainer. */
[data-testid="stSidebar"] [data-testid="stTab"] > div:not([data-testid="stMarkdownContainer"]) {
  background: var(--sn-amber) !important;
}

/* ---------- bottom tab bar ---------- */
/* The page script builds the bar in a keyed container, which Streamlit
   exposes as a .st-key-<name> class. It is lifted out of the document flow and
   pinned to the bottom edge, phone style, with the safe-area inset for phones
   that have a home indicator. */
.st-key-sn_tabbar {
  position: fixed;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  z-index: 1000;
  width: min(100%, 560px);
  gap: 0.2rem !important;
  padding: 0.35rem 0.5rem calc(0.35rem + env(safe-area-inset-bottom, 0px)) !important;
  background: rgba(24, 23, 22, 0.97) !important;
  backdrop-filter: blur(12px);
  border-top: 1px solid rgba(245, 165, 36, 0.3);
  box-shadow: 0 -16px 34px -24px rgba(0, 0, 0, 0.75);
}
.st-key-sn_tabbar button {
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
  color: rgba(251, 246, 238, 0.6) !important;
  border-radius: 14px !important;
  min-height: 54px;
  padding: 0.3rem 0.15rem !important;
  font-size: 0.7rem;
  font-weight: 700;
  letter-spacing: 0;
  transition: color 0.15s ease, background 0.15s ease;
}
.st-key-sn_tabbar button > div {
  flex-direction: column;
  gap: 0.05rem;
  max-width: 100%;
}
/* The button's font-size also shrinks Streamlit's Material icon, so the glyph
   is set back to a thumb-readable size and the label kept small. */
.st-key-sn_tabbar [data-testid="stIconMaterial"] {
  font-size: 21px !important;
  line-height: 1;
}
.st-key-sn_tabbar [data-testid="stMarkdownContainer"] p {
  font-size: 0.68rem !important;
  line-height: 1.2;
}
.st-key-sn_tabbar button:hover {
  color: var(--sn-cream) !important;
  background: rgba(255, 255, 255, 0.07) !important;
  transform: none;
}
/* The active tab keeps a flat look - only the glyph and label light up. */
.st-key-sn_tabbar button[kind="primary"] {
  background: transparent !important;
  color: var(--sn-amber) !important;
}
.st-key-sn_tabbar button[kind="primary"]:hover {
  color: var(--sn-amber) !important;
  background: rgba(245, 165, 36, 0.12) !important;
}
"""


def brand_css():
    """The customer app stylesheet, wrapped for ``st.html``.

    Colour values come from :data:`PALETTE` and are emitted as custom
    properties, so a palette edit lands everywhere at once.
    """
    variables = "\n".join(f"  --sn-{name}: {value};" for name, value in PALETTE.items())
    return f"<style>{_BRAND_CSS.replace('%VARS%', variables)}</style>"
