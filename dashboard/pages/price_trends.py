from __future__ import annotations

import pandas as pd
import streamlit as st

from dashboard.charts import price_trend_chart
from dashboard.ui import fetch_json, inject_theme, render_dashboard_intro, render_sidebar_brand, safe_frame


inject_theme()
render_sidebar_brand()
render_dashboard_intro(
    "Price Trends",
    "Track seller-by-seller price movement with a richer visual system, Buy Box emphasis, and MRP reference overlays.",
    chips=["Plotly", "Buy Box Focus", "Date Windows"],
)

asins = safe_frame(fetch_json("/asins"))
asin_options = asins["asin"].tolist() if not asins.empty else []
filters_col, summary_col = st.columns([1.2, 0.8])
with filters_col:
    selected_asin = st.selectbox("ASIN", asin_options) if asin_options else None
with summary_col:
    days = st.selectbox("Date Range", [7, 30, 90], index=0)

if selected_asin:
    df = safe_frame(fetch_json(f"/asins/{selected_asin}/prices", params={"days": days}))
    if not df.empty:
        df["scraped_at"] = pd.to_datetime(df["scraped_at"])
        df["buybox_label"] = df["is_buy_box_winner"].map({True: "Buy Box", False: "Standard"})
        latest = df.sort_values("scraped_at").iloc[-1]
        metric1, metric2, metric3 = st.columns(3)
        metric1.metric("Latest price", f"INR {latest['price']:.2f}")
        metric2.metric("Buy Box seller", latest["seller_name"])
        metric3.metric("MRP reference", f"INR {latest['mrp']:.2f}" if pd.notna(latest["mrp"]) else "N/A")
        st.plotly_chart(price_trend_chart(df), use_container_width=True)

        seller_summary = (
            df.groupby("seller_name", as_index=False)
            .agg(current_price=("price", "last"), observations=("price", "count"))
            .sort_values("current_price")
        )
        st.dataframe(seller_summary, use_container_width=True)
    else:
        st.info("No data available yet.")
else:
    st.info("No ASINs are available yet. Run the crawler and refresh the page.")
