"""Service catalog."""
import pandas as pd
import streamlit as st

from utils.api import ApiError, fetch_services

token = st.session_state.token

st.subheader("Services")
st.caption("The catalog customers browse and book against.")

try:
    services = fetch_services(token).get("data", [])
except ApiError as exc:
    st.error(str(exc))
    st.stop()

if not services:
    st.info("No services are published yet.")
    st.stop()

rows = [
    {
        "service": service.get("name"),
        "category": service.get("category"),
        "base price": service.get("base_price"),
        "duration (min)": service.get("duration"),
        "active": service.get("is_active"),
        "description": service.get("description"),
    }
    for service in services
]

table = pd.DataFrame(rows)

total_col, category_col, price_col = st.columns(3)
with total_col:
    st.metric("Services", f"{len(table):,}", border=True)
with category_col:
    st.metric("Categories", f"{table['category'].nunique():,}", border=True)
with price_col:
    st.metric(
        "Average base price",
        f"₹{table['base price'].mean():,.0f}" if not table.empty else "₹0",
        border=True,
    )

st.dataframe(table, hide_index=True, alt="Service catalog with category, price and duration")

by_category = (
    table.groupby("category", as_index=False)["base price"]
    .agg(["count", "mean"])
    .reset_index()
    .rename(columns={"count": "services", "mean": "average base price"})
)

chart_col, list_col = st.columns(2)
with chart_col:
    with st.container(border=True):
        st.subheader("Services per category")
        st.bar_chart(
            by_category.set_index("category")[["services"]],
            alt="Number of services in each category",
        )
with list_col:
    with st.container(border=True):
        st.subheader("Category mix")
        st.dataframe(
            by_category,
            hide_index=True,
            alt="Services and average base price per category",
        )
