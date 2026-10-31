"""Find providers near you, check their reviews and book them."""
import streamlit as st

from customer_utils.api import (
    ApiError,
    fetch_providers,
    fetch_provider,
    fetch_reviews,
    fetch_services,
)
from customer_utils.ui import avatar_tile, chip_row, inr, stars

token = st.session_state.token

if "provider_profile" not in st.session_state:
    st.session_state.provider_profile = None

st.header("Find a provider", icon=":material/storefront:")
st.caption("Search by location and compare the professionals available right now.")

lat_col, lng_col = st.columns(2)
with lat_col:
    latitude = st.number_input("Latitude", value=19.0760, format="%.4f")
with lng_col:
    longitude = st.number_input("Longitude", value=72.8777, format="%.4f")
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
    name = provider.get("user_name", "Provider")
    average = rating.get("average", 0)
    city = (provider.get("location") or {}).get("city") or "Near you"

    with st.container(border=True):
        avatar_col, info_col, price_col = st.columns(
            [0.6, 3, 1], vertical_alignment="center"
        )
        with avatar_col:
            st.html(avatar_tile(name))
        with info_col:
            st.markdown(f"#### {name} :green[✓]")
            st.html(
                chip_row(
                    [
                        f"★ {average} ({rating.get('count', 0)})",
                        f"📍 {city}",
                        f"🛠 {provider.get('experience_years', 0)} yrs experience",
                        f"✓ {provider.get('total_jobs', 0)} jobs done",
                    ]
                )
            )
        with price_col:
            st.markdown(f"**{inr(provider.get('daily_wage', 0))}**")
            st.caption("per day")

        profile_col, book_col = st.columns(2)
        with profile_col:
            if st.button(
                "View profile",
                key=f"profile_{provider_id}",
                width="stretch",
            ):
                st.session_state.provider_profile = provider_id
        with book_col:
            booked = st.button(
                "Book now",
                key=f"book_{provider_id}",
                type="primary",
                width="stretch",
            )

        with st.expander("Reviews", icon=":material/reviews:"):
            try:
                reviews = fetch_reviews(provider_id, token)["data"]
            except ApiError as exc:
                st.error(str(exc))
            else:
                if not reviews:
                    st.caption("No reviews yet for this provider.")
                for review in reviews:
                    st.markdown(
                        f"**{stars(review.get('rating', 0))}** {review.get('review', '')}"
                    )
                    st.caption(str(review.get("created_at", ""))[:10])

        if booked:
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
            st.subheader(f"{profile.get('user_name', 'Provider')}", icon=":material/account_circle:")
            detail_col, contact_col = st.columns(2)
            with detail_col:
                st.markdown("**Experience**")
                st.write(f"{profile.get('experience_years', 0)} years")
                st.markdown("**Completed jobs**")
                st.write(profile.get("completed_jobs", 0))
                st.markdown("**Earnings to date**")
                st.write(inr((profile.get("earnings", {}) or {}).get("total", 0)))
            with contact_col:
                st.markdown("**Contact**")
                st.write(profile.get("user_phone", ""))
                st.markdown("**Rating**")
                st.write(f"{stars((profile.get('rating', {}) or {}).get('average', 0))} "
                         f"{(profile.get('rating', {}) or {}).get('average', 0)}")
        if st.button("Close profile", icon=":material/close:"):
            st.session_state.provider_profile = None
            st.rerun()
