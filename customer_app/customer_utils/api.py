"""HTTP access to the ServeNow API for the customer app.

Self-contained on purpose: this app is deployed separately from the admin
console, so it must not depend on the other app's modules.
"""
import os

import requests
import streamlit as st

DEFAULT_BASE_URL = "http://localhost:8000"
TIMEOUT = 30

PLATFORM_COMMISSION_RATE = 0.10
GST_RATE = 0.18


def secret(name, default=None):
    """Read a value from Streamlit secrets, falling back to a default."""
    try:
        return st.secrets[name]
    except Exception:
        return default


def api_base_url() -> str:
    """Resolve the API base URL.

    Order: Streamlit secret ``API_BASE_URL``, then ``SERENOW_API_URL``, then
    the local development server.
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


def register(name, phone, email, password):
    """Create a customer account and return ``(token, user)``."""
    body = {"name": name, "phone": phone, "password": password, "role": "customer"}
    if email:
        body["email"] = email
    payload = _request("POST", "/api/auth/register", payload=body)
    data = payload.get("data", {})
    return data.get("token"), data.get("user", {})


def price_preview(service_charge):
    """Mirror of the API's pricing calculation, for display only."""
    platform_fee = round(service_charge * PLATFORM_COMMISSION_RATE)
    gst = round(platform_fee * GST_RATE)
    return {
        "service_charge": service_charge,
        "platform_fee": platform_fee,
        "gst": gst,
        "total_amount": service_charge + gst,
    }


@st.cache_data(ttl=60, show_spinner=False)
def fetch_services(token=None):
    return _request("GET", "/api/services/", token=token)


@st.cache_data(ttl=60, show_spinner=False)
def fetch_categories(token=None):
    return _request("GET", "/api/services/categories", token=token)


@st.cache_data(ttl=60, show_spinner=False)
def fetch_providers(token=None, service_id=None, lat=None, lng=None, radius=25):
    params = {"radius": radius}
    if service_id:
        params["service_id"] = service_id
    if lat is not None and lng is not None:
        params["lat"] = lat
        params["lng"] = lng
    return _request("GET", "/api/providers/search", token=token, params=params)


@st.cache_data(ttl=60, show_spinner=False)
def fetch_provider(provider_id, token=None):
    return _request("GET", f"/api/providers/{provider_id}", token=token)


@st.cache_data(ttl=60, show_spinner=False)
def fetch_reviews(provider_id, token=None):
    return _request("GET", f"/api/reviews/provider/{provider_id}", token=token)


@st.cache_data(ttl=30, show_spinner=False)
def fetch_my_bookings(token):
    return _request("GET", "/api/bookings/", token=token)


def create_booking(token, payload):
    return _request("POST", "/api/bookings/", token=token, payload=payload)


def cancel_booking(token, booking_id):
    return _request("PUT", f"/api/bookings/{booking_id}/cancel", token=token)


def create_review(token, payload):
    return _request("POST", "/api/reviews/", token=token, payload=payload)


def clear_cache():
    """Drop cached API responses after a write."""
    fetch_services.clear()
    fetch_categories.clear()
    fetch_providers.clear()
    fetch_provider.clear()
    fetch_reviews.clear()
    fetch_my_bookings.clear()
