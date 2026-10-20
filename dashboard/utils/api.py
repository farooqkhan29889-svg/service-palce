"""HTTP access to the ServeNow API.

The console never talks to MongoDB directly - it uses the same public REST
surface as the mobile clients, so what the dashboard shows is exactly what an
end user would get.
"""
import os

import requests
import streamlit as st

DEFAULT_BASE_URL = "http://localhost:8000"
TIMEOUT = 30


def secret(name, default=None):
    """Read a value from Streamlit secrets, falling back to a default."""
    try:
        return st.secrets[name]
    except Exception:
        return default


def api_base_url() -> str:
    """Resolve the API base URL.

    Order: Streamlit secret ``API_BASE_URL``, then the ``SERENOW_API_URL``
    environment variable, then the local development server.
    """
    url = secret("API_BASE_URL") or os.environ.get("SERENOW_API_URL") or DEFAULT_BASE_URL
    return str(url).rstrip("/")


class ApiError(RuntimeError):
    """Raised when the API cannot be reached or rejects the request."""


def _request(method, path, token=None, payload=None, params=None):
    url = f"{api_base_url()}{path}"
    headers = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if payload is not None:
        headers["Content-Type"] = "application/json"

    try:
        response = requests.request(
            method,
            url,
            headers=headers,
            json=payload,
            params=params,
            timeout=TIMEOUT,
        )
    except requests.RequestException as exc:
        raise ApiError(f"Could not reach the API at {url}: {exc}") from exc

    if response.status_code >= 400:
        detail = response.text
        try:
            detail = response.json().get("detail", detail)
        except ValueError:
            pass
        raise ApiError(f"{method} {path} failed ({response.status_code}): {detail}")

    return response.json()


def login(phone, password):
    """Sign in and return ``(token, user)``."""
    payload = _request("POST", "/api/auth/login", payload={"phone": phone, "password": password})
    data = payload.get("data", {})
    return data.get("token"), data.get("user", {})


@st.cache_data(ttl=30, show_spinner=False)
def fetch(path, token, params=None):
    """GET a JSON endpoint. Cached for 30s per token."""
    return _request("GET", path, token=token, params=params)


@st.cache_data(ttl=30, show_spinner=False)
def fetch_dashboard(token):
    return _request("GET", "/api/admin/dashboard", token=token)


@st.cache_data(ttl=30, show_spinner=False)
def fetch_revenue(token, days):
    return _request("GET", "/api/admin/revenue", token=token, params={"days": days})


@st.cache_data(ttl=30, show_spinner=False)
def fetch_bookings(token, status_filter=None, limit=200):
    params = {"limit": limit}
    if status_filter:
        params["status_filter"] = status_filter
    return _request("GET", "/api/admin/bookings", token=token, params=params)


@st.cache_data(ttl=30, show_spinner=False)
def fetch_pending_providers(token):
    return _request("GET", "/api/admin/providers/pending", token=token)


@st.cache_data(ttl=30, show_spinner=False)
def fetch_services(token):
    return _request("GET", "/api/services/", token=token)


@st.cache_data(ttl=30, show_spinner=False)
def fetch_providers(token, lat=19.076, lng=72.8777, radius=500):
    params = {"lat": lat, "lng": lng, "radius": radius}
    return _request("GET", "/api/providers/search", token=token, params=params)


def approve_provider(token, provider_id):
    _request("PUT", f"/api/admin/providers/{provider_id}/approve", token=token)


def reject_provider(token, provider_id, reason=None):
    _request(
        "PUT",
        f"/api/admin/providers/{provider_id}/reject",
        token=token,
        params={"reason": reason} if reason else None,
    )


def clear_cache():
    """Drop cached API responses after a write."""
    fetch.clear()
    fetch_dashboard.clear()
    fetch_revenue.clear()
    fetch_bookings.clear()
    fetch_pending_providers.clear()
    fetch_services.clear()
    fetch_providers.clear()
