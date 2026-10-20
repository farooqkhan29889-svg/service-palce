"""Platform overview: KPIs, revenue trend and booking mix."""
import pandas as pd
import streamlit as st

from dashboard_utils.api import ApiError, fetch_bookings, fetch_dashboard, fetch_revenue

token = st.session_state.token

st.subheader("Platform overview")
st.caption("Live figures from the ServeNow API.")

days = st.segmented_control(
    "Revenue window",
    [7, 30, 90],
    default=30,
    label_visibility="collapsed",
)

try:
    dashboard = fetch_dashboard(token)["data"]
    revenue = fetch_revenue(token, days)["data"]
    bookings = fetch_bookings(token, limit=500)["data"]
except ApiError as exc:
    st.error(str(exc))
    st.stop()

users = dashboard["users"]
providers = dashboard["providers"]
booking_stats = dashboard["bookings"]
revenue_stats = dashboard["revenue"]

with st.container(horizontal=True):
    st.metric("Customers", f"{users['total']:,}", border=True)
    st.metric(
        "Providers",
        f"{providers['approved']:,}",
        f"{providers['pending']} pending",
        border=True,
    )
    st.metric("Bookings", f"{booking_stats['total']:,}", f"{booking_stats['active']} active", border=True)
    st.metric("Revenue this month", f"₹{revenue_stats['this_month']:,.0f}", border=True)

with st.container(horizontal=True):
    st.metric("Gross merchandise value", f"₹{revenue_stats['total_gmv']:,.0f}", border=True)
    st.metric("Platform revenue (all time)", f"₹{revenue_stats['total']:,.0f}", border=True)
    st.metric("Completed bookings", f"{booking_stats['completed']:,}", border=True)
    st.metric("Bookings this month", f"{booking_stats['this_month']:,}", border=True)

daily = revenue.get("daily_breakdown", {})
trend = pd.DataFrame(
    [
        {
            "day": day,
            "gmv": values.get("gmv", 0),
            "platform fee": values.get("platform_fee", 0),
            "gst": values.get("gst", 0),
            "revenue": values.get("platform_fee", 0) + values.get("gst", 0),
            "payments": values.get("bookings", 0),
        }
        for day, values in sorted(daily.items())
    ]
)

chart_col, mix_col = st.columns(2)

with chart_col:
    with st.container(border=True):
        st.subheader(f"Revenue over the last {days} days")
        if trend.empty:
            st.info("No completed payments in this window yet.")
        else:
            st.area_chart(
                trend.set_index("day")[["gmv", "revenue"]],
                alt="Gross merchandise value and platform revenue per day",
            )

with mix_col:
    with st.container(border=True):
        st.subheader("Bookings by status")
        if bookings:
            mix = pd.DataFrame(bookings)
            counts = mix["status"].value_counts().rename_axis("status").reset_index(name="bookings")
            st.bar_chart(counts.set_index("status"), alt="Number of bookings per status")
        else:
            st.info("No bookings yet.")

if not trend.empty:
    with st.container(border=True):
        st.subheader("Daily breakdown")
        st.dataframe(
            trend.set_index("day")[["gmv", "platform fee", "gst", "revenue", "payments"]],
            hide_index=True,
            alt="Daily gross merchandise value, fees and payment counts",
        )
