"""Customer landing page."""
import streamlit as st

from customer_utils.api import ApiError, fetch_categories, fetch_providers, fetch_services
from customer_utils.ui import (
    category_icon,
    hero_banner,
    inr,
    service_icon,
    stars,
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

action_col, action_col2, action_col3 = st.columns([1.1, 1.1, 2])

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

with action_col3:
    st.caption(
        ":material/verified: Background-checked professionals  ·  "
        ":material/payments: Pay only when the job is done"
    )

st.space("medium")

with st.container(border=True):
    with st.container(horizontal=True):
        if api_error:
            st.metric("Services on the platform", "—", border=False)
            st.metric("Service categories", "—", border=False)
            st.metric("Professionals online now", "—", border=False)
            st.metric("Average rating", "—", border=False)
        else:
            st.metric("Services on the platform", f"{len(services):,}", border=False)
            st.metric("Service categories", f"{len(categories):,}", border=False)
            st.metric("Professionals online now", f"{len(nearby):,}", border=False)
            st.metric("Average rating", "4.8 ★", border=False)

st.space("medium")

if categories:
    st.header("Browse by category", icon=":material/grid_view:")
    st.caption("Pick a category and see what is available near you.")

    category_columns = st.columns(4)
    for index, category in enumerate(categories):
        with category_columns[index % 4]:
            with st.container(border=True):
                st.markdown(f"#### :material/{category_icon(category)}: {category}")
                count = sum(1 for s in services if s.get("category") == category)
                st.caption(f"{count} service{'s' if count != 1 else ''}")
                if st.button(
                    "Explore",
                    key=f"home_category_{category}",
                    icon=":material/arrow_forward:",
                    width="stretch",
                ):
                    st.session_state.service_category = category
                    st.switch_page("app_pages/services.py")

    st.space("medium")

if services:
    st.header("Popular services", icon=":material/local_fire_department:")
    st.caption("Transparent pricing before you book. No hidden charges.")

    featured = sorted(services, key=lambda s: s.get("base_price", 0))[:6]
    service_columns = st.columns(3)

    for index, service in enumerate(featured):
        with service_columns[index % 3]:
            with st.container(border=True):
                st.markdown(f"#### :material/{service_icon(service)}: {service.get('name')}")
                st.caption(service.get("description", ""))
                st.caption(f":material/location_on: {service.get('category', 'General')}")

                price_col, duration_col = st.columns(2)
                with price_col:
                    st.metric("Starting at", inr(service.get("base_price", 0)))
                with duration_col:
                    st.metric("Typical time", f"{service.get('duration', 0)} min")

                if st.button(
                    "Book now",
                    key=f"home_book_{service.get('_id')}",
                    icon=":material/calendar_month:",
                    width="stretch",
                ):
                    st.session_state.selected_service = service.get("_id")
                    st.switch_page("app_pages/services.py")

st.space("medium")

st.header("How it works", icon=":material/auto_awesome:")
st.caption("Three steps, no phone tag.")

step_columns = st.columns(3)
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

for column, (icon, heading, body) in zip(step_columns, steps):
    with column:
        with st.container(border=True):
            st.markdown(f"#### :material/{icon}:")
            st.markdown(f"**{heading}**")
            st.caption(body)

st.space("medium")

if nearby:
    st.header("Professionals near you", icon=":material/groups:")
    st.caption("Online right now and available to take jobs today.")

    provider_columns = st.columns(4)
    for index, provider in enumerate(nearby[:4]):
        with provider_columns[index % 4]:
            with st.container(border=True):
                rating = provider.get("rating", {}) or {}
                st.markdown(f"#### :material/account_circle: {provider.get('user_name', 'Provider')}")
                st.caption(
                    f"{stars(rating.get('average', 0))} "
                    f"{rating.get('average', 0)} "
                    f"({rating.get('count', 0)} reviews)"
                )
                stat_col, job_col = st.columns(2)
                with stat_col:
                    st.metric("Jobs done", f"{provider.get('total_jobs', 0):,}")
                with job_col:
                    st.metric("Experience", f"{provider.get('experience_years', 0)} yrs")
                st.caption(f"From {inr(provider.get('daily_wage', 0))} per day")
