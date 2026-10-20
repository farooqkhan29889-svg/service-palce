"""Headless checks for the ServeNow console.

Runs the Streamlit app in-process with ``st.testing.v1.AppTest`` and asserts
that every page renders without raising. A live API is required for the
sign-in and data assertions.

    .venv\\Scripts\\python -m pytest dashboard/tests/test_console.py -v
"""
import os
import sys
from pathlib import Path

import pytest
import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

APP_PATH = Path(__file__).resolve().parents[1] / "streamlit_app.py"
API_URL = os.environ.get("SERENOW_API_URL", "http://localhost:8000")
ADMIN_PHONE = os.environ.get("SERENOW_ADMIN_PHONE", "9999999999")
ADMIN_PASSWORD = os.environ.get("SERENOW_ADMIN_PASSWORD", "admin123")


def _api_reachable():
    try:
        response = requests.get(f"{API_URL}/health", timeout=10)
    except requests.RequestException:
        return False
    return response.status_code == 200


pytestmark = pytest.mark.skipif(
    not _api_reachable(), reason=f"no API reachable at {API_URL}"
)


@pytest.fixture(scope="module")
def signed_in():
    """An AppTest instance that has completed the sign-in form."""
    from streamlit.testing.v1 import AppTest

    app = AppTest.from_file(str(APP_PATH), default_timeout=60)
    app.run()
    app.text_input[0].set_value(ADMIN_PHONE)
    app.text_input[1].set_value(ADMIN_PASSWORD)
    app.button[0].click().run()
    return app


def test_login_succeeds(signed_in):
    assert not signed_in.exception
    assert signed_in.session_state["token"], "sign in did not store a token"


@pytest.mark.parametrize("page", ["overview", "bookings", "providers", "services"])
def test_page_renders(signed_in, page):
    signed_in.switch_page(f"app_pages/{page}.py")
    signed_in.run()
    assert not signed_in.exception, [str(e.value) for e in signed_in.exception]
