"""Your bookings: track status, cancel, and leave a review."""
import streamlit as st

from customer_utils.api import (
    ApiError,
    cancel_booking,
    clear_cache,
    create_review,
    fetch_my_bookings,
)
from customer_utils.ui import inr, stars

token = st.session_state.token

if not token:
    st.info("Sign in from the sidebar to see your bookings.")
    st.stop()

st.header("My bookings", icon=":material/receipt_long:")
st.caption("Track every job you have booked and pay only when it is done.")

try:
    bookings = fetch_my_bookings(token)["data"]
except ApiError as exc:
    st.error(str(exc))
    st.stop()

st.caption(f"{len(bookings)} booking{'s' if len(bookings) != 1 else ''} on your account")

if not bookings:
    st.info("You have no bookings yet.")
    st.stop()

STATUS_COLORS = {
    "pending": "orange",
    "confirmed": "blue",
    "in_progress": "violet",
    "completed": "green",
    "cancelled": "gray",
}

for booking in bookings:
    # The API resolves bookings by their MongoDB id, not the SN-xxxx reference.
    mongo_id = booking.get("_id")
    status = booking.get("status", "unknown")
    pricing = booking.get("pricing", {})
    timeline = booking.get("timeline", {}) or {}
    rated = bool(booking.get("customer_rating"))

    with st.container(border=True):
        head, status_col = st.columns([3, 1], vertical_alignment="center")
        with head:
            st.markdown(f"#### {booking.get('service_name', 'Service')}")
            st.caption(
                f"Reference {booking.get('booking_id')} · "
                f"{str(booking.get('service_date', ''))[:16]} · "
                f"{booking.get('service_time', '')}"
            )
            st.caption(f":material/location_on: {booking.get('address')}, {booking.get('city')}")
        with status_col:
            st.badge(
                status.replace("_", " ").title(),
                color=STATUS_COLORS.get(status, "gray"),
            )

        price_col, created_col = st.columns(2)
        with price_col:
            st.markdown("**Total paid**")
            st.write(inr(pricing.get("total_amount", 0)))
        with created_col:
            st.markdown("**Booked on**")
            st.write(str(timeline.get("created_at", ""))[:16])

        cancel_col, review_col = st.columns(2)
        with cancel_col:
            if status in ("pending", "confirmed", "in_progress"):
                if st.button(
                    "Cancel booking",
                    key=f"cancel_{mongo_id}",
                    icon=":material/cancel:",
                    width="stretch",
                ):
                    try:
                        cancel_booking(token, mongo_id)
                    except ApiError as exc:
                        st.error(str(exc))
                    else:
                        clear_cache()
                        st.rerun()

        with review_col:
            if status == "completed" and not rated:
                with st.popover("Leave a review", icon=":material/star:"):
                    with st.form(f"review_{mongo_id}"):
                        rating = st.slider("Rating", 1, 5, 5)
                        comment = st.text_area("Comment", placeholder="How did it go?")
                        submitted = st.form_submit_button(
                            "Submit review", icon=":material/send:", width="stretch"
                        )
                    if submitted:
                        try:
                            create_review(
                                token,
                                {
                                    "booking_id": mongo_id,
                                    "rating": rating,
                                    "review": comment,
                                },
                            )
                        except ApiError as exc:
                            st.error(str(exc))
                        else:
                            clear_cache()
                            st.rerun()

        with st.expander("Timeline"):
            st.json(timeline)

        if rated:
            customer_rating = booking["customer_rating"]
            st.caption(
                f"You rated this job {customer_rating.get('rating')}★ - "
                f"\"{customer_rating.get('review', '')}\""
            )
