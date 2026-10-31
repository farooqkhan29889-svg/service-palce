"""ServeNow customer app.

The customer-facing landing page and booking flow. It reads the public parts
of the ServeNow API without an account, and needs a customer login to book.
"""
import streamlit as st

from customer_utils.api import (
    ApiError,
    api_base_url,
    fetch_me,
    login,
    register,
    send_otp,
    verify_otp,
)
from customer_utils.ui import LOGO_SVG, brand_css

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
if "pending_user" not in st.session_state:
    st.session_state.pending_user = None


def send_verification_otp(phone):
    try:
        send_otp(phone)
    except ApiError as exc:
        st.session_state.auth_error = str(exc)
        return False
    st.session_state.auth_error = None
    return True


def finish_sign_in(token, user):
    """Store a usable session, or route unverified accounts to OTP check."""
    try:
        me = fetch_me(token)
    except ApiError:
        # /me rejects unverified accounts - that is exactly the signal to
        # send an OTP instead of signing in.
        st.session_state.pending_user = {"phone": user.get("phone"), "name": user.get("name")}
        st.session_state.token = None
        st.session_state.user = None
        if not send_verification_otp(user.get("phone", "")):
            return False
        return True
    st.session_state.token = token
    st.session_state.user = me or user
    st.session_state.pending_user = None
    return True


def sign_in(phone, password):
    try:
        token, user = login(phone, password)
    except ApiError as exc:
        st.session_state.auth_error = str(exc)
        return False
    return finish_sign_in(token, user)


def sign_up(name, phone, email, password):
    try:
        token, user = register(name, phone, email, password)
    except ApiError as exc:
        st.session_state.auth_error = str(exc)
        return False
    st.session_state.pending_user = {"phone": phone, "name": name}
    st.session_state.token = None
    st.session_state.user = None
    return send_verification_otp(phone)


def verify_phone(phone, code):
    try:
        token, user = verify_otp(phone, code)
    except ApiError as exc:
        st.session_state.auth_error = str(exc)
        return False
    st.session_state.token = token
    st.session_state.user = user
    st.session_state.pending_user = None
    st.session_state.auth_error = None
    return True


with st.sidebar:
    st.markdown("### ServeNow")
    st.caption("Trusted local experts, booked in minutes.")
    if st.session_state.pending_user:
        pending = st.session_state.pending_user
        st.info("Enter the code shown in the API server terminal to activate your account.")
        with st.form("otp_form"):
            code = st.text_input("Verification code", placeholder="6 digits")
            submitted = st.form_submit_button(
                "Verify phone", icon=":material/verified:", width="stretch"
            )
            resend = st.form_submit_button(
                "Resend code", icon=":material/refresh:", width="stretch"
            )

        if submitted and verify_phone(pending.get("phone", ""), code):
            st.rerun()
        if resend:
            send_verification_otp(pending.get("phone", ""))
            st.rerun()
        if st.button("Back to sign in", icon=":material/arrow_back:", width="stretch"):
            st.session_state.pending_user = None
            st.rerun()
    elif st.session_state.token:
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

TABS = [
    ("app_pages/home.py", "Home", ":material/home:"),
    ("app_pages/services.py", "Services", ":material/handyman:"),
    ("app_pages/providers.py", "Nearby", ":material/storefront:"),
    ("app_pages/my_bookings.py", "Bookings", ":material/receipt_long:"),
]

pages = [st.Page(path, title=label, icon=icon) for path, label, icon in TABS]
# Streamlit only renders navigation in the sidebar or at the top, so the app
# hides it and draws its own tab bar below.
page = st.navigation(pages, position="hidden")

# Injected here, right before the tab bar, rather than next to st.logo: the
# style block has to land in the main container, where the browser actually
# mounts it.
st.markdown(brand_css(), unsafe_allow_html=True)

with st.container(key="sn_tabbar", horizontal=True):
    for candidate, (_path, label, icon) in zip(pages, TABS):
        if st.button(
            label,
            key=f"tab_{label}",
            icon=icon,
            width="stretch",
            type="primary" if candidate is page else "secondary",
        ):
            st.switch_page(candidate)

page.run()
