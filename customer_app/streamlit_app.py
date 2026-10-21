"""ServeNow customer app.

The customer-facing landing page and booking flow. It reads the public parts
of the ServeNow API without an account, and needs a customer login to book.
"""
import streamlit as st

from customer_utils.api import ApiError, api_base_url, login, register
from customer_utils.ui import LOGO_SVG

st.set_page_config(
    page_title="ServeNow - local services at your doorstep",
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


def sign_in(phone, password):
    try:
        token, user = login(phone, password)
    except ApiError as exc:
        st.session_state.auth_error = str(exc)
        return False
    st.session_state.token = token
    st.session_state.user = user
    st.session_state.auth_error = None
    return True


def sign_up(name, phone, email, password):
    try:
        token, user = register(name, phone, email, password)
    except ApiError as exc:
        st.session_state.auth_error = str(exc)
        return False
    st.session_state.token = token
    st.session_state.user = user
    st.session_state.auth_error = None
    return True


with st.sidebar:
    st.markdown("### ServeNow")
    st.caption("Trusted local experts, booked in minutes.")
    if st.session_state.token:
        user = st.session_state.user or {}
        st.success(f"Signed in as {user.get('name', 'customer')}")
        if st.button("Sign out", icon=":material/logout:", width="stretch"):
            st.session_state.token = None
            st.session_state.user = None
            st.rerun()
    else:
        sign_in_tab, sign_up_tab = st.tabs(["Sign in", "Create account"])

        with sign_in_tab:
            with st.form("signin_form"):
                phone = st.text_input("Phone", placeholder="9876543211")
                password = st.text_input("Password", type="password", placeholder="Password")
                submitted = st.form_submit_button(
                    "Sign in", icon=":material/login:", width="stretch"
                )

            if submitted and sign_in(phone, password):
                st.rerun()

            if st.button("Use the demo account", icon=":material/science:", width="stretch"):
                if sign_in("9876543211", "customer123"):
                    st.rerun()

        with sign_up_tab:
            with st.form("signup_form"):
                name = st.text_input("Full name", placeholder="Your name")
                new_phone = st.text_input("Phone", placeholder="9876543211")
                email = st.text_input("Email", placeholder="you@example.com")
                new_password = st.text_input("Password", type="password", placeholder="Password")
                created = st.form_submit_button(
                    "Create account", icon=":material/person_add:", width="stretch"
                )

            if created and sign_up(name, new_phone, email, new_password):
                st.rerun()

        if st.session_state.auth_error:
            st.error(st.session_state.auth_error)

pages = [
    st.Page("app_pages/home.py", title="Home", icon=":material/home:"),
    st.Page("app_pages/services.py", title="Services", icon=":material/handyman:"),
    st.Page("app_pages/providers.py", title="Find a provider", icon=":material/storefront:"),
    st.Page("app_pages/my_bookings.py", title="My bookings", icon=":material/receipt_long:"),
]

page = st.navigation(pages, position="top")
page.run()
