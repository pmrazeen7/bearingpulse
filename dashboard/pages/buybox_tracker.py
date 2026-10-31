from __future__ import annotations

import pandas as pd
import streamlit as st

from dashboard.charts import buybox_timeline_chart
from dashboard.ui import PIN_OPTIONS, fetch_json, inject_theme, render_dashboard_intro, render_sidebar_brand, safe_frame


inject_theme()
render_sidebar_brand()
render_dashboard_intro(
    "Buy Box Tracker",
    "Visualize which seller owns the Buy Box over time, and compare location-sensitive winner shifts by PIN code.",
    chips=["Timeline", "Location-aware", "7-day view"],
)

asins = safe_frame(fetch_json("/asins"))
filter_left, filter_right = st.columns([1, 1])
with filter_left:
    selected_asin = st.selectbox("ASIN", asins["asin"].tolist(), key="buybox_asin") if not asins.empty else None
with filter_right:
    location = st.selectbox("Simulated PIN code", PIN_OPTIONS, index=0)
if selected_asin:
    df = safe_frame(fetch_json(f"/asins/{selected_asin}/buybox-history"))
    if not df.empty:
        df["scraped_at"] = pd.to_datetime(df["scraped_at"])
        if location != "All":
            df = df[df["simulated_pincode"] == location]
        timeline = (
            df.assign(hour=df["scraped_at"].dt.floor("h"), value=1)
            .groupby(["hour", "seller_name"], as_index=False)["value"]
            .sum()
        )
        stats = (
            df.groupby("seller_name")
            .size()
            .reset_index(name="count")
            .assign(percent=lambda frame: frame["count"] / frame["count"].sum() * 100)
        )
        stat1, stat2 = st.columns(2)
        stat1.metric("Tracked winner changes", int(df.shape[0]))
        stat2.metric("Distinct Buy Box holders", int(df["seller_name"].nunique()))
        st.plotly_chart(buybox_timeline_chart(timeline), use_container_width=True)
        st.dataframe(
            stats.rename(columns={"seller_name": "Seller", "count": "Hours as winner", "percent": "% time as winner"}),
            use_container_width=True,
        )
    else:
        st.info("No Buy Box history available yet.")
else:
    st.info("No ASINs are available yet. Run the crawler and refresh the page.")
