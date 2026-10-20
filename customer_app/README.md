# ServeNow customer app

The customer-facing landing page and booking flow for ServeNow.

This is a separate Streamlit app from the admin console in `dashboard/`, so it
can be published as its own public URL while the console stays behind an admin
login.

> The FastAPI service is hosted separately (Render). See the
> [root README](../README.md#deployment) for the API deployment. Streamlit
> Cloud cannot serve the FastAPI app or hold WebSocket connections.

## Pages

| Page | Contents |
|---|---|
| Home | Landing page: hero, live platform counters, category grid, popular services, how it works, professionals near you |
| Services | Searchable service catalog with a booking form and an itemised price preview |
| Find a provider | Location and radius search, provider profile, reviews and ratings |
| My bookings | Booking status, cancel, leave a review |

Browsing the landing page, the catalog and providers needs no account. Booking,
cancelling and reviewing need a customer sign-in.

## Project layout

```
customer_app/
├── streamlit_app.py      # Entry point: sign in / create account and navigation
├── app_pages/            # One module per page
│   ├── home.py
│   ├── services.py
│   ├── providers.py
│   └── my_bookings.py
├── customer_utils/
│   └── api.py            # HTTP client, cached endpoints, price preview
├── tests/
│   └── test_customer_app.py  # Headless checks via st.testing.v1.AppTest
└── requirements.txt      # Dependencies for Streamlit Cloud
```

The theme lives in `.streamlit/config.toml` at the **repository root**, because
Streamlit loads per-project config from `$CWD/.streamlit/config.toml` and
Streamlit Cloud runs the app from the repository root.

## Run it locally

From the repository root, with the API running on port 8000:

```bash
.venv\Scripts\python -m streamlit run customer_app/streamlit_app.py
```

The app is at http://localhost:8502. Sign in with the seeded customer account
`9876543211` / `customer123`, or create a new account from the sidebar.

## Tests

```bash
.venv\Scripts\python -m pytest customer_app/tests/test_customer_app.py -v
```

They cover the landing page without a login, the sign-in flow, every page
rendering, and a full booking submitted through the form. They need a
reachable API and skip themselves when there is none.

## Deploy to Streamlit Cloud

1. Push the repository to GitHub.
2. Go to **share.streamlit.io** and choose **New app**.
3. Deployment source:
   - **Repository**: `farooqkhan29889-svg/service-palce`
   - **Branch**: `main`
   - **Main file path**: `customer_app/streamlit_app.py`
4. Open **Advanced settings**:
   - **Python version**: `3.13`
   - **Requirements file**: `customer_app/requirements.txt`
5. Under **Secrets**, add:

   ```toml
   API_BASE_URL = "https://servenow-api.onrender.com"
   ```

6. Click **Deploy**.

The customer app and the admin console are separate deployments, so each gets
its own URL.

### Notes

- Streamlit Cloud's free plan sleeps the app after inactivity and restarts it
  on the next visit, so the first request after a pause is slow.
- The app is a client of the API, so it is subject to the same CORS rules and
  JWT expiry as any other client.
- Never commit `.streamlit/secrets.toml`; it is already git-ignored.
