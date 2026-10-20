# ServeNow console

A Streamlit admin console for the ServeNow platform. It talks to the ServeNow
REST API over HTTP - it never connects to MongoDB directly, so what it shows
is exactly what a customer or provider would see.

> The API itself is a FastAPI service and is hosted separately (Render). See
> the [root README](../README.md#deployment) for the API deployment. Streamlit
> Cloud cannot serve the FastAPI app or hold WebSocket connections.

## What it shows

| Page | Contents |
|---|---|
| Overview | Customers, providers, bookings and revenue KPIs, daily revenue trend, bookings by status |
| Bookings | Every booking with status filter, and a detail view with pricing and timeline |
| Providers | Approval queue (approve/reject) and the live provider directory with ratings and earnings |
| Services | Service catalog, category mix and pricing |

## Project layout

```
dashboard/
├── streamlit_app.py      # Entry point: sign-in and navigation
├── app_pages/            # One module per page
│   ├── overview.py
│   ├── bookings.py
│   ├── providers.py
│   └── services.py
├── dashboard_utils/
│   └── api.py            # HTTP client and cached endpoint helpers
├── tests/
│   └── test_console.py   # Headless checks via st.testing.v1.AppTest
└── requirements.txt      # Dependencies for Streamlit Cloud
```

The theme lives in `.streamlit/config.toml` at the **repository root**, because
Streamlit loads per-project config from `$CWD/.streamlit/config.toml` and
Streamlit Cloud runs the app from the repository root.

## Run it locally

From the repository root, with the API running on port 8000:

```bash
.venv\Scripts\python -m streamlit run dashboard/streamlit_app.py
```

The console is at http://localhost:8501. Sign in with an admin account.

## Tests

The console has headless tests that render every page in-process:

```bash
.venv\Scripts\python -m pytest dashboard/tests/test_console.py -v
```

They need a reachable API and skip themselves when there is none.

## Deploy to Streamlit Cloud

1. Push the repository to GitHub (the console lives in the same repo).
2. Go to **share.streamlit.io** and choose **New app**.
3. Pick the deployment source:
   - **Repository**: `farooqkhan29889-svg/service-palce`
   - **Branch**: `main`
   - **Main file path**: `dashboard/streamlit_app.py`
4. Open **Advanced settings** and set:
   - **Python version**: `3.13`
   - **Requirements file**: `dashboard/requirements.txt`
5. Under **Secrets**, add:

   ```toml
   API_BASE_URL = "https://servenow-api.onrender.com"
   ```

   Optional - lets the console sign in automatically instead of asking for
   credentials on every visit:

   ```toml
   SERENOW_ADMIN_PHONE = "..."
   SERENOW_ADMIN_PASSWORD = "..."
   ```

6. Click **Deploy**. The console is live at
   `https://<app-name>.streamlit.app`.

### Notes

- Streamlit Cloud's free plan sleeps the app after inactivity and restarts it
  on the next visit, so the first request after a pause is slow.
- The console reads through the API, so it is subject to the same CORS rules
  and the same JWT expiry as any other client.
- Never commit `.streamlit/secrets.toml`; it is already git-ignored.
