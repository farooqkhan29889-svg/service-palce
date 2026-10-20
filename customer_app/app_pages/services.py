"""Browse the service catalog and request a booking."""
from datetime import date

import streamlit as st

from customer_utils.api import (
    ApiError,
    clear_cache,
    create_booking,
    fetch_categories,
    fetch_providers,
    fetch_services,
    price_preview,
)

token = st.session_state.token

try:
    services = fetch_services(token)["data"]
    categories = fetch_categories(token)["data"]
except ApiError as exc:
    st.error(str(exc))
    st.stop()

if "booking_service" not in st.session_state:
    st.session_state.booking_service = st.session_state.pop("selected_service", None)
if "booking_result" not in st.session_state:
    st.session_state.booking_result = None

filter_col, category_col = st.columns([2, 1])

with filter_col:
    search = st.text_input("Search services", placeholder="Search by name", label_visibility="collapsed")
with category_col:
    chosen_category = st.selectbox(
        "Category", ["All"] + list(categories), label_visibility="collapsed"
    )

visible = [
    service
    for service in services
    if (chosen_category == "All" or service.get("category") == chosen_category)
    and (not search or search.lower() in service.get("name", "").lower())
]

st.caption(f"{len(visible)} service{'s' if len(visible) != 1 else ''} available")

if not visible:
    st.info("No services match that search.")
    st.stop()

grid = st.columns(3)
for index, service in enumerate(visible):
    with grid[index % 3]:
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
                key=f"service_book_{service.get('_id')}",
                icon=":material/calendar_month:",
                width="stretch",
            ):
                st.session_state.booking_service = service.get("_id")
                st.session_state.booking_result = None

booking_id = st.session_state.booking_service
if not booking_id:
    st.stop()

service = next((s for s in visible if s.get("_id") == booking_id), None)
if service is None:
    st.session_state.booking_service = None
    st.stop()

st.divider()
st.subheader(f"Book {service.get('name')}")

if not st.session_state.token:
    st.warning("Sign in from the sidebar to request this booking.")
    st.stop()

try:
    providers = fetch_providers(token, service_id=booking_id, radius=50)["data"]
except ApiError as exc:
    st.error(str(exc))
    st.stop()

if not providers:
    st.info("No provider currently offers this service. Please try again later.")
    st.stop()

provider_names = {p["_id"]: p.get("user_name", "Provider") for p in providers}

with st.form("booking_form"):
    provider_col, date_col = st.columns(2)
    with provider_col:
        chosen_provider = st.selectbox(
            "Provider", list(provider_names), format_func=lambda pid: provider_names[pid]
        )
    with date_col:
        service_date = st.date_input("Date", value=date.today())
        service_time = st.text_input("Time", value="10:00 AM", placeholder="10:00 AM")

    address_col, city_col = st.columns([2, 1])
    with address_col:
        address = st.text_input("Address", placeholder="Flat, street, landmark")
    with city_col:
        city = st.text_input("City", value="Mumbai")

    issue = st.text_area("Describe the issue (optional)", placeholder="What needs to be done?")

    preview = price_preview(service.get("base_price", 0))
    preview_col, submit_col = st.columns([2, 1], vertical_alignment="center")
    with preview_col:
        st.caption(
            f"Service ₹{preview['service_charge']:,.0f} · "
            f"GST ₹{preview['gst']:,.0f} · "
            f"Total ₹{preview['total_amount']:,.0f}"
        )
    with submit_col:
        submitted = st.form_submit_button(
            "Request booking", icon=":material/check_circle:", type="primary", width="stretch"
        )

if submitted:
    payload = {
        "provider_id": chosen_provider,
        "service_id": booking_id,
        "service_date": service_date.isoformat(),
        "service_time": service_time,
        "address": address,
        "city": city,
        "payment_method": "upi",
    }
    if issue:
        payload["issue_description"] = issue

    try:
        booking = create_booking(token, payload)
    except ApiError as exc:
        st.error(str(exc))
    else:
        clear_cache()
        st.session_state.booking_result = booking
        st.session_state.booking_service = None
        st.rerun()

result = st.session_state.booking_result
if result:
    data = result.get("data", result)
    with st.container(border=True):
        st.success(f"Booking request sent - reference {data.get('booking_id')}")
        st.json(data.get("pricing", {}))
        if st.button("View my bookings", icon=":material/receipt_long:", width="stretch"):
            st.switch_page("app_pages/my_bookings.py")
