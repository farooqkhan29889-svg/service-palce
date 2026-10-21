"""Headless checks for the ServeNow customer app.

Runs the Streamlit app in-process with ``st.testing.v1.AppTest``. The landing
page must work without an account; the booking pages need a customer login.

    .venv\\Scripts\\python -m pytest customer_app/tests/test_customer_app.py -v
"""
import os
import sys
from pathlib import Path

import pytest
import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

APP_PATH = Path(__file__).resolve().parents[1] / "streamlit_app.py"
API_URL = os.environ.get("SERENOW_API_URL", "http://localhost:8000")
CUSTOMER_PHONE = os.environ.get("SERENOW_CUSTOMER_PHONE", "9876543211")
CUSTOMER_PASSWORD = os.environ.get("SERENOW_CUSTOMER_PASSWORD", "customer123")


def _api_reachable():
    try:
        response = requests.get(f"{API_URL}/health", timeout=10)
    except requests.RequestException:
        return False
    return response.status_code == 200


def _by_label(widgets, label):
    """Find a widget index by label.

    AppTest orders widgets by their position in the DOM, where the sidebar
    comes after the main area - so the sign-in button is not at index 0.
    """
    for index, widget in enumerate(widgets):
        if widget.label == label:
            return index
    raise AssertionError(f"no widget labelled {label!r}")


pytestmark = pytest.mark.skipif(
    not _api_reachable(), reason=f"no API reachable at {API_URL}"
)


@pytest.fixture(scope="module")
def guest():
    """An AppTest instance that has not signed in."""
    from streamlit.testing.v1 import AppTest

    app = AppTest.from_file(str(APP_PATH), default_timeout=60)
    app.run()
    return app


@pytest.fixture(scope="module")
def signed_in():
    """An AppTest instance that has signed in as a customer."""
    from streamlit.testing.v1 import AppTest

    app = AppTest.from_file(str(APP_PATH), default_timeout=60)
    app.run()
    app.text_input[_by_label(app.text_input, "Phone")].set_value(CUSTOMER_PHONE)
    app.text_input[_by_label(app.text_input, "Password")].set_value(CUSTOMER_PASSWORD)
    app.button[_by_label(app.button, "Sign in")].click().run()
    return app


def test_landing_page_works_without_login(guest):
    assert not guest.exception
    # The hero is a gradient banner rendered with st.html, so the landing
    # page has no st.title. Its calls to action are the real signal.
    labels = [button.label for button in guest.button]
    assert "Browse services" in labels, labels
    assert "Find a provider" in labels, labels


def test_sign_in_succeeds(signed_in):
    assert not signed_in.exception
    assert signed_in.session_state["token"], "sign in did not store a token"


@pytest.mark.parametrize("page", ["home", "services", "providers", "my_bookings"])
def test_page_renders(signed_in, page):
    signed_in.switch_page(f"app_pages/{page}.py")
    signed_in.run()
    assert not signed_in.exception, [str(e.value) for e in signed_in.exception]


def test_booking_flow_creates_a_booking(signed_in):
    """Pick a service, complete the form and submit it."""
    signed_in.switch_page("app_pages/services.py")
    signed_in.run()

    signed_in.button[_by_label(signed_in.button, "Book now")].click().run()
    assert not signed_in.exception, [str(e.value) for e in signed_in.exception]

    signed_in.text_input[_by_label(signed_in.text_input, "Address")].set_value("12 Test Road")
    signed_in.text_input[_by_label(signed_in.text_input, "City")].set_value("Mumbai")
    signed_in.button[_by_label(signed_in.button, "Request booking")].click().run()

    assert not signed_in.exception, [str(e.value) for e in signed_in.exception]
    assert signed_in.success, "no success message after booking"
