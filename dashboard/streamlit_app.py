"""ServeNow operations console.

A Streamlit front end for the ServeNow API. The API itself is served by
FastAPI (Render); this console is a read-mostly admin view on top of it.
"""
import streamlit as st

from dashboard_utils.api import ApiError, api_base_url, login, secret
from dashboard_utils.branding import LOGO_SVG

st.set_page_config(
    page_title="ServeNow console",
    page_icon="🛠️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.logo(LOGO_SVG)

if "token" not in st.session_state:
    st.session_state.token = None
if "user" not in st.session_state:
    st.session_state.user = None
if "auth_error" not in st.session_state:
    st.session_state.auth_error = None

with st.sidebar:
    st.markdown("### Connection")
    st.caption(api_base_url())

    if st.session_state.token:
        user = st.session_state.user or {}
        st.success(f"Signed in as {user.get('name', 'admin')}")
        if st.button("Sign out", icon=":material/logout:", width="stretch"):
            st.session_state.token = None
            st.session_state.user = None
            st.rerun()
    else:
        default_phone = secret("SERENOW_ADMIN_PHONE", "")
        with st.form("login_form"):
            phone = st.text_input(
                "Phone", value=default_phone, placeholder="Phone", label_visibility="collapsed"
            )
            password = st.text_input(
                "Password", type="password", placeholder="Password", label_visibility="collapsed"
            )
            submitted = st.form_submit_button("Sign in", icon=":material/login:", width="stretch")

        if submitted:
            try:
                token, user = login(phone, password)
            except ApiError as exc:
                st.session_state.auth_error = str(exc)
            else:
                st.session_state.token = token
                st.session_state.user = user
                st.session_state.auth_error = None
                st.rerun()

        if st.session_state.auth_error:
            st.error(st.session_state.auth_error)

        auto_phone = secret("SERENOW_ADMIN_PHONE")
        auto_password = secret("SERENOW_ADMIN_PASSWORD")
        if auto_phone and auto_password and not st.session_state.token:
            try:
                token, user = login(auto_phone, auto_password)
            except ApiError:
                pass
            else:
                st.session_state.token = token
                st.session_state.user = user
                st.rerun()

if not st.session_state.token:
    st.title("ServeNow console")
    st.info(
        "Sign in with an admin account to view bookings, providers, services and revenue. "
        "The console reads the live API - it does not connect to the database directly."
    )
    st.stop()

pages = [
    st.Page("app_pages/overview.py", title="Overview", icon=":material/dashboard:"),
    st.Page("app_pages/bookings.py", title="Bookings", icon=":material/receipt_long:"),
    st.Page("app_pages/providers.py", title="Providers", icon=":material/storefront:"),
    st.Page("app_pages/services.py", title="Services", icon=":material/home_repair_service:"),
]

page = st.navigation(pages, position="top")
page.run()
