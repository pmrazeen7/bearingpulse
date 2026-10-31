from __future__ import annotations

import pandas as pd
import streamlit as st

from dashboard.ui import fetch_json, inject_theme, post_json, render_dashboard_intro, render_sidebar_brand, safe_frame


inject_theme()
render_sidebar_brand()
render_dashboard_intro(
    "Alerts",
    "Review recent threshold events, buy box changes, and stock disruptions with a more polished control panel.",
    chips=["CSV Export", "Threshold Config", "Severity View"],
)

alert_type = st.selectbox("Alert Type", ["", "price_drop", "buybox_change", "stock_spike"])
params = {"type": alert_type} if alert_type else {}
df = safe_frame(fetch_json("/alerts", params=params))
if not df.empty:
    df["severity"] = df.apply(
        lambda row: "high" if row["alert_type"] == "price_drop" else "medium",
        axis=1,
    )
    df["triggered_at"] = pd.to_datetime(df["triggered_at"]).dt.strftime("%d %b %Y %H:%M")
    severity_colors = {"high": "rgba(255,143,107,0.2)", "medium": "rgba(109,94,251,0.14)"}

    def highlight_severity(row):
        color = severity_colors.get(row["severity"], "")
        return [f"background-color: {color}"] * len(row)

    st.dataframe(df.style.apply(highlight_severity, axis=1), use_container_width=True)
    st.download_button("Export CSV", df.to_csv(index=False), file_name="alerts.csv")
else:
    st.info("No alerts available.")

with st.form("alert-config"):
    asin_id = st.text_input("ASIN ID override (optional)")
    threshold_pct = st.number_input("Threshold %", min_value=1.0, max_value=100.0, value=5.0)
    submitted = st.form_submit_button("Save threshold")
    if submitted:
        response = post_json("/alerts/config", {"threshold_pct": threshold_pct, "asin_id": asin_id or None})
        st.success(response["status"])
