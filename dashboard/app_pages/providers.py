"""Provider directory and the approval queue."""
import pandas as pd
import streamlit as st

from utils.api import (
    ApiError,
    approve_provider,
    clear_cache,
    fetch_pending_providers,
    fetch_providers,
    reject_provider,
)

token = st.session_state.token

st.subheader("Providers")
st.caption("Approvals and the live provider directory.")

tab_pending, tab_directory = st.tabs(["Approvals", "Directory"])

with tab_pending:
    try:
        pending = fetch_pending_providers(token).get("data", [])
    except ApiError as exc:
        st.error(str(exc))
        st.stop()

    if not pending:
        st.success("No providers are waiting for approval.")
    else:
        for provider in pending:
            aadhaar = str(provider.get("aadhaar_number", ""))
            masked = f"XXXX XXXX {aadhaar[-4:]}" if len(aadhaar) >= 4 else "hidden"
            with st.container(border=True):
                head, action = st.columns([3, 1], vertical_alignment="center")
                with head:
                    st.markdown(f"**{provider.get('user_name', 'Unknown')}**")
                    st.caption(
                        f"{provider.get('user_phone', 'Unknown')} · "
                        f"{provider.get('experience_years', 0)} yrs · "
                        f"₹{provider.get('daily_wage', 0):,.0f}/day · aadhaar {masked}"
                    )
                    skills = provider.get("skills") or []
                    if skills:
                        st.caption("Skills: " + ", ".join(skills))
                with action:
                    approve_col, reject_col = st.columns(2)
                    with approve_col:
                        if st.button(
                            "Approve",
                            key=f"approve_{provider.get('_id')}",
                            icon=":material/check_circle:",
                            width="stretch",
                        ):
                            try:
                                approve_provider(token, provider.get("_id"))
                            except ApiError as exc:
                                st.error(str(exc))
                            else:
                                clear_cache()
                                st.rerun()
                    with reject_col:
                        if st.button(
                            "Reject",
                            key=f"reject_{provider.get('_id')}",
                            icon=":material/cancel:",
                            width="stretch",
                        ):
                            try:
                                reject_provider(token, provider.get("_id"))
                            except ApiError as exc:
                                st.error(str(exc))
                            else:
                                clear_cache()
                                st.rerun()

with tab_directory:
    try:
        providers = fetch_providers(token).get("data", [])
    except ApiError as exc:
        st.error(str(exc))
        st.stop()

    if not providers:
        st.info("No approved providers are listed for this location.")
    else:
        rows = []
        for provider in providers:
            rating = provider.get("rating", {}) or {}
            rows.append(
                {
                    "name": provider.get("user_name"),
                    "phone": provider.get("user_phone"),
                    "approved": provider.get("is_approved"),
                    "online": provider.get("is_online"),
                    "rating": rating.get("average", 0),
                    "reviews": rating.get("count", 0),
                    "jobs": provider.get("total_jobs", 0),
                    "completed": provider.get("completed_jobs", 0),
                    "earnings": (provider.get("earnings", {}) or {}).get("total", 0),
                    "experience": f"{provider.get('experience_years', 0)} yrs",
                }
            )
        st.dataframe(
            pd.DataFrame(rows),
            hide_index=True,
            alt="Approved providers with rating, job count and earnings",
        )
