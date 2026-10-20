"""Find providers near you, check their reviews and book them."""
import streamlit as st

from customer_utils.api import (
    ApiError,
    fetch_providers,
    fetch_provider,
    fetch_reviews,
    fetch_services,
)

token = st.session_state.token

if "provider_profile" not in st.session_state:
    st.session_state.provider_profile = None

lat_col, lng_col, radius_col = st.columns([1, 1, 1])
with lat_col:
    latitude = st.number_input("Latitude", value=19.0760, format="%.4f")
with lng_col:
    longitude = st.number_input("Longitude", value=72.8777, format="%.4f")
with radius_col:
    radius = st.slider("Search radius (km)", min_value=1, max_value=50, value=25)

try:
    providers = fetch_providers(token, lat=latitude, lng=longitude, radius=radius)["data"]
except ApiError as exc:
    st.error(str(exc))
    st.stop()

st.caption(f"{len(providers)} provider{'s' if len(providers) != 1 else ''} available nearby")

if not providers:
    st.info("No providers found in this area. Try a larger radius.")
    st.stop()

for provider in providers:
    provider_id = provider.get("_id")
    rating = provider.get("rating", {}) or {}
    skills = provider.get("skills") or []

    with st.container(border=True):
        head, action = st.columns([3, 1], vertical_alignment="center")
        with head:
            st.markdown(f"### {provider.get('user_name', 'Provider')}")
            st.caption(
                f"⭐ {rating.get('average', 0)} from {rating.get('count', 0)} reviews · "
                f"{provider.get('total_jobs', 0)} jobs · "
                f"{provider.get('experience_years', 0)} years experience · "
                f"₹{provider.get('daily_wage', 0):,.0f}/day"
            )
            if skills:
                st.caption("Skills: " + ", ".join(skills))
        with action:
            if st.button(
                "View profile",
                key=f"profile_{provider_id}",
                icon=":material/person:",
                width="stretch",
            ):
                st.session_state.provider_profile = provider_id

        with st.expander("Reviews"):
            try:
                reviews = fetch_reviews(provider_id, token)["data"]
            except ApiError as exc:
                st.error(str(exc))
            else:
                if not reviews:
                    st.caption("No reviews yet for this provider.")
                for review in reviews:
                    st.markdown(
                        f"**{'⭐' * int(review.get('rating', 0))}** "
                        f"{review.get('review', '')}"
                    )
                    st.caption(str(review.get("created_at", ""))[:10])

        if st.button(
            "Book this provider",
            key=f"book_{provider_id}",
            icon=":material/calendar_month:",
            width="stretch",
        ):
            try:
                services = fetch_services(token)["data"]
            except ApiError:
                services = []
            offered = [s for s in services if s.get("_id") in (provider.get("services") or [])]
            if offered:
                st.session_state.selected_service = offered[0]["_id"]
                st.switch_page("app_pages/services.py")
            else:
                st.info("This provider has no published services yet.")

profile_id = st.session_state.provider_profile
if profile_id:
    try:
        profile = fetch_provider(profile_id, token)["data"]
    except ApiError as exc:
        st.error(str(exc))
    else:
        with st.container(border=True):
            st.subheader(f"Profile: {profile.get('user_name', 'Provider')}")
            detail_col, contact_col = st.columns(2)
            with detail_col:
                st.markdown("**Experience**")
                st.write(f"{profile.get('experience_years', 0)} years")
                st.markdown("**Completed jobs**")
                st.write(profile.get("completed_jobs", 0))
                st.markdown("**Earnings to date**")
                st.write(f"₹{(profile.get('earnings', {}) or {}).get('total', 0):,.0f}")
            with contact_col:
                st.markdown("**Contact**")
                st.write(profile.get("user_phone", ""))
                st.markdown("**Rating**")
                st.write((profile.get("rating", {}) or {}).get("average", 0))
        if st.button("Close profile", icon=":material/close:"):
            st.session_state.provider_profile = None
            st.rerun()
