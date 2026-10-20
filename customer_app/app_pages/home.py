"""Customer landing page."""
import streamlit as st

from customer_utils.api import ApiError, fetch_categories, fetch_providers, fetch_services

token = st.session_state.token

try:
    services = fetch_services(token)["data"]
    categories = fetch_categories(token)["data"]
    nearby = fetch_providers(token, radius=25)["data"]
except ApiError as exc:
    st.error(str(exc))
    st.stop()

hero_left, hero_right = st.columns([3, 2], vertical_alignment="center")

with hero_left:
    st.title("Local services, booked in minutes")
    st.markdown(
        "Electricians, plumbers, cleaners and repair experts near you - "
        "transparent pricing, verified professionals and live tracking."
    )
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

with hero_right:
    with st.container(border=True):
        st.subheader("Right now on ServeNow")
        with st.container(horizontal=True):
            st.metric("Services", f"{len(services):,}", border=True)
            st.metric("Categories", f"{len(categories):,}", border=True)
            st.metric("Providers online", f"{len(nearby):,}", border=True)

st.divider()

st.subheader("Browse by category")
category_cols = st.columns(4)
for index, category in enumerate(categories):
    with category_cols[index % 4]:
        with st.container(border=True):
            st.markdown(f"**{category}**")
            st.caption(
                f"{sum(1 for s in services if s.get('category') == category)} services"
            )

st.subheader("Popular services")
featured = sorted(services, key=lambda s: s.get("base_price", 0))[:6]
service_cols = st.columns(3)
for index, service in enumerate(featured):
    with service_cols[index % 3]:
        with st.container(border=True):
            st.markdown(f"### {service.get('icon', '🛠️')} {service.get('name')}")
            st.caption(service.get("description", ""))
            price_col, duration_col = st.columns(2)
            with price_col:
                st.metric("From", f"₹{service.get('base_price', 0):,.0f}")
            with duration_col:
                st.metric("Duration", f"{service.get('duration', 0)} min")
            if st.button(
                "Book now",
                key=f"home_book_{service.get('_id')}",
                icon=":material/calendar_month:",
                width="stretch",
            ):
                st.session_state.selected_service = service.get("_id")
                st.switch_page("app_pages/services.py")

st.subheader("How it works")
step_cols = st.columns(3)
steps = [
    ("1. Choose a service", "Pick what you need and see the full price up front."),
    ("2. Pick a provider", "Compare verified professionals near you and their ratings."),
    ("3. Track and pay", "Follow the provider live and settle once the job is done."),
]
for column, (heading, body) in zip(step_cols, steps):
    with column:
        with st.container(border=True):
            st.markdown(f"**{heading}**")
            st.caption(body)

if nearby:
    st.subheader("Professionals near you")
    preview = st.columns(4)
    for index, provider in enumerate(nearby[:4]):
        with preview[index % 4]:
            with st.container(border=True):
                rating = provider.get("rating", {}) or {}
                st.markdown(f"**{provider.get('user_name', 'Provider')}**")
                st.caption(
                    f"⭐ {rating.get('average', 0)} · "
                    f"{provider.get('total_jobs', 0)} jobs · "
                    f"₹{provider.get('daily_wage', 0):,.0f}/day"
                )
