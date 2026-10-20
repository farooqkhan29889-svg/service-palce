"""Booking list with status filtering and per-booking detail."""
import pandas as pd
import streamlit as st

from utils.api import ApiError, fetch_bookings

token = st.session_state.token

st.subheader("Bookings")
st.caption("Every booking on the platform, newest first.")

status = st.selectbox(
    "Status",
    ["All", "pending", "confirmed", "in_progress", "completed", "cancelled"],
    label_visibility="collapsed",
)

try:
    payload = fetch_bookings(
        token, status_filter=None if status == "All" else status, limit=500
    )
except ApiError as exc:
    st.error(str(exc))
    st.stop()

bookings = payload.get("data", [])

if not bookings:
    st.info("No bookings match this filter.")
    st.stop()

rows = []
for booking in bookings:
    pricing = booking.get("pricing", {})
    rows.append(
        {
            "booking id": booking.get("booking_id"),
            "service": booking.get("service_name"),
            "status": booking.get("status"),
            "city": booking.get("city"),
            "service date": str(booking.get("service_date", ""))[:16],
            "total": pricing.get("total_amount"),
            "platform fee": pricing.get("platform_fee"),
            "payment": booking.get("payment", {}).get("status"),
        }
    )

table = pd.DataFrame(rows)
st.dataframe(table, hide_index=True, alt="Bookings with status, price and payment state")

with st.container(border=True):
    st.subheader("Booking detail")
    selected = st.selectbox("Booking", table["booking id"].tolist(), label_visibility="collapsed")
    booking = next(b for b in bookings if b.get("booking_id") == selected)

    detail_col, pricing_col = st.columns(2)
    with detail_col:
        st.markdown("**Service**")
        st.write(booking.get("service_name"))
        st.markdown("**Status**")
        st.write(booking.get("status"))
        st.markdown("**Address**")
        st.write(f"{booking.get('address')}, {booking.get('city')}")
        st.markdown("**Timeline**")
        st.json(booking.get("timeline", {}))
    with pricing_col:
        st.markdown("**Pricing**")
        st.json(booking.get("pricing", {}))
        st.markdown("**Payment**")
        st.json(booking.get("payment", {}))
