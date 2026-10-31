"""Customer landing page."""
import streamlit as st

from customer_utils.api import ApiError, fetch_categories, fetch_providers, fetch_services
from customer_utils.ui import (
    avatar_tile,
    category_icon,
    chip_row,
    hero_banner,
    icon_tile,
    inr,
    service_icon,
    warranty_band,
)

token = st.session_state.token

services, categories, nearby = [], [], []
api_error = None
try:
    services = fetch_services(token)["data"]
    categories = fetch_categories(token)["data"]
    nearby = fetch_providers(token, radius=25)["data"]
except ApiError as exc:
    # The landing page should still render if the API is unreachable, so the
    # customer sees the service rather than a wall of error text.
    api_error = str(exc)

st.html(
    hero_banner(
        "★ Trusted by 10,000+ homes across Mumbai",
        "Book trusted local experts in minutes",
        "Electricians, plumbers, cleaners and repair professionals near you - "
        "transparent pricing, verified specialists, live tracking and a job "
        "that gets done right.",
    )
)

if api_error:
    st.warning(
        "We could not load live listings just now. The services below will "
        "appear as soon as the platform is reachable.",
        icon=":material/cloud_off:",
    )

st.space("small")

action_col, action_col2 = st.columns(2)

with action_col:
    if st.button(
        "Browse services",
        icon=":material/handyman:",
        type="primary",
        width="stretch",
    ):
        st.switch_page("app_pages/services.py")

with action_col2:
    if st.button(
        "Find a provider",
        icon=":material/storefront:",
        width="stretch",
    ):
        st.switch_page("app_pages/providers.py")

st.caption(
    ":material/verified: Background-checked professionals  ·  "
    ":material/payments: Pay only when the job is done"
)

st.space("medium")

st.html(
    warranty_band(
        "Every job",
        "Verified pros, 30-day warranty",
        "Pay only after the work is done.",
    )
)

st.space("medium")

with st.container(border=True):
    with st.container(horizontal=True):
        stats = (
            ("—", "—", "—", "—")
            if api_error
            else (f"{len(services):,}", f"{len(categories):,}", f"{len(nearby):,}", "4.8 ★")
        )
        st.metric("Services", stats[0], border=False)
        st.metric("Categories", stats[1], border=False)
        st.metric("Pros online", stats[2], border=False)
        st.metric("Rating", stats[3], border=False)

st.space("medium")

if categories:
    st.header("Browse by category", icon=":material/grid_view:")
    st.caption("Pick a category and see what is available near you.")

    category_columns = st.columns(2)
    for index, category in enumerate(categories):
        with category_columns[index % 2]:
            with st.container(border=True):
                st.html(icon_tile(category_icon(category)))
                st.markdown(f"**{category}**")
                count = sum(1 for s in services if s.get("category") == category)
                st.caption(f"{count} service{'s' if count != 1 else ''}")
                if st.button(
                    "Explore",
                    key=f"home_category_{category}",
                    width="stretch",
                ):
                    st.session_state.service_category = category
                    st.switch_page("app_pages/services.py")

    st.space("medium")

if services:
    st.header("Popular services", icon=":material/local_fire_department:")
    st.caption("Transparent pricing before you book. No hidden charges.")

    featured = sorted(services, key=lambda s: s.get("base_price", 0))[:4]

    for service in featured:
        with st.container(border=True):
            icon_col, name_col, price_col = st.columns(
                [0.5, 2.1, 0.95], vertical_alignment="center"
            )
            with icon_col:
                st.html(icon_tile(service_icon(service), size=46))
            with name_col:
                st.markdown(f"**{service.get('name')}**")
                st.caption(service.get("category", "General"))
            with price_col:
                st.markdown(f"**{inr(service.get('base_price', 0))}**")
                st.caption("starting at")
            st.caption(service.get("description", ""))
            st.html(
                chip_row(
                    [
                        f"⏱ {service.get('duration', 0)} min typical",
                        "✓ Visit charge included",
                    ]
                )
            )
            if st.button(
                "Book now",
                key=f"home_book_{service.get('_id')}",
                type="primary",
                width="stretch",
            ):
                st.session_state.selected_service = service.get("_id")
                st.switch_page("app_pages/services.py")

st.space("medium")

st.header("How it works", icon=":material/auto_awesome:")
st.caption("Three steps, no phone tag.")

steps = [
    (
        "search",
        "1. Choose a service",
        "Browse the catalog and see the full price up front - service charge, "
        "platform fee and GST, itemised.",
    ),
    (
        "storefront",
        "2. Pick a professional",
        "Compare verified specialists near you, read their reviews and see "
        "their rating before you decide.",
    ),
    (
        "near_me",
        "3. Track and pay",
        "Follow the professional live on the map, then pay once the job is "
        "done. Cancel free before it starts.",
    ),
]

for icon, heading, body in steps:
    with st.container(border=True):
        step_icon, step_text = st.columns([0.42, 2.6], vertical_alignment="center")
        with step_icon:
            st.html(icon_tile(icon, size=44))
        with step_text:
            st.markdown(f"**{heading}**")
            st.caption(body)

st.space("medium")

if nearby:
    st.header("Professionals near you", icon=":material/groups:")
    st.caption("Online right now and available to take jobs today.")

    for provider in nearby[:4]:
        with st.container(border=True):
            provider_avatar, provider_info = st.columns(
                [0.42, 2.6], vertical_alignment="center"
            )
            name = provider.get("user_name", "Provider")
            rating = provider.get("rating", {}) or {}
            with provider_avatar:
                st.html(avatar_tile(name, size=44))
            with provider_info:
                st.markdown(f"**{name}**")
                st.html(
                    chip_row(
                        [
                            f"★ {rating.get('average', 0)} ({rating.get('count', 0)})",
                            f"✓ {provider.get('total_jobs', 0)} jobs",
                            f"🛠 {provider.get('experience_years', 0)} yrs",
                        ]
                    )
                )
                st.caption(f"From {inr(provider.get('daily_wage', 0))} per day")
