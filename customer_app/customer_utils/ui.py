"""Presentation helpers for the customer app.

Icons, initials and formatting shared across the pages. Keeping them here
means the pages stay focused on layout.
"""

# Inline SVG mark - a house on the brand gradient. Inline keeps the app free
# of binary assets and lets Streamlit serve it straight from the page.
LOGO_SVG = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="64" height="64">
  <defs>
    <linearGradient id="sn" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#4F46E5"/>
      <stop offset="100%" stop-color="#0EA5E9"/>
    </linearGradient>
  </defs>
  <rect x="2" y="2" width="60" height="60" rx="15" fill="url(#sn)"/>
  <path d="M32 15 L48 29 H41 V47 H36.5 V35.5 H27.5 V47 H23 V29 H16 Z" fill="#ffffff"/>
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


def hero_banner(eyebrow, headline, subline):
    """A gradient hero panel.

    Streamlit has no native element for a full-width gradient banner, so this
    is the one place the app uses custom markup. It styles a single container
    and never targets Streamlit's own classes.
    """
    return f"""
<div style="
  background:linear-gradient(135deg,#4F46E5 0%,#0EA5E9 55%,#6366F1 100%);
  border-radius:0.75rem;
  padding:2.5rem 2.25rem;
  color:#ffffff;
  box-shadow:0 18px 40px -20px rgba(79,70,229,0.55);
">
  <div style="
    display:inline-block;
    background:rgba(255,255,255,0.16);
    border:1px solid rgba(255,255,255,0.32);
    border-radius:999px;
    padding:0.35rem 0.9rem;
    font-size:0.82rem;
    font-weight:600;
    margin-bottom:1.1rem;
  ">{eyebrow}</div>
  <div style="
    font-family:'Plus Jakarta Sans',sans-serif;
    font-size:2.55rem;
    line-height:1.12;
    font-weight:800;
    letter-spacing:-0.02em;
    max-width:22ch;
  ">{headline}</div>
  <div style="
    margin-top:0.85rem;
    max-width:44ch;
    font-size:1.03rem;
    line-height:1.65;
    color:rgba(255,255,255,0.88);
  ">{subline}</div>
</div>
"""
