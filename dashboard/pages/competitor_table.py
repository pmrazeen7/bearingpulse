from __future__ import annotations

import pandas as pd
import streamlit as st

from dashboard.ui import fetch_json, inject_theme, render_dashboard_intro, render_sidebar_brand, safe_frame


inject_theme()
render_sidebar_brand()
render_dashboard_intro(
    "Competitor Table",
    "A live multi-seller spread view tuned for price wars, FBA detection, and Buy Box deltas.",
    chips=["Sorted by Price", "FBA Flags", "Color-coded"],
)

asins = safe_frame(fetch_json("/asins"))
selected_asin = (
    st.selectbox("ASIN", asins["asin"].tolist(), key="competitor_asin")
    if not asins.empty
    else None
)
if selected_asin:
    df = safe_frame(fetch_json(f"/asins/{selected_asin}/sellers")).sort_values("current_price")
    if not df.empty:
        buy_box_price = (
            df.loc[df["is_buy_box_winner"], "current_price"].min()
            if df["is_buy_box_winner"].any()
            else df["current_price"].min()
        )
        df["vs_buy_box"] = df["current_price"] - buy_box_price
        df["Current Price"] = df["current_price"].map(lambda value: f"INR {value:,.2f}")
        df["INR vs Buy Box"] = df["vs_buy_box"].map(lambda value: f"{value:+.2f}")
        df["FBA"] = df["is_fba"].map({True: "Yes", False: "No"})
        df["Stock"] = df["stock_status"].str.replace("_", " ").str.title()
        df["Last Updated"] = pd.to_datetime(df["scraped_at"]).dt.strftime("%d %b %H:%M")
        df["Seller"] = df["seller_name"]

        def color_price(row):
            min_price = df["current_price"].min()
            max_price = df["current_price"].max()
            if row.current_price == min_price:
                return ["background-color: rgba(56,214,196,0.18)"] * len(row)
            if row.current_price == max_price:
                return ["background-color: rgba(255,143,107,0.18)"] * len(row)
            return [""] * len(row)

        stat1, stat2, stat3 = st.columns(3)
        stat1.metric("Cheapest seller", df.iloc[0]["seller_name"], f"INR {df.iloc[0]['current_price']:.2f}")
        stat2.metric("Most expensive", df.iloc[-1]["seller_name"], f"INR {df.iloc[-1]['current_price']:.2f}")
        stat3.metric("Spread", f"INR {df['current_price'].max() - df['current_price'].min():.2f}")
        view = df[["Seller", "Current Price", "INR vs Buy Box", "FBA", "Stock", "Last Updated"]]
        st.dataframe(view.style.apply(color_price, axis=1), use_container_width=True)
    else:
        st.info("No seller data available yet.")
else:
    st.info("No ASINs are available yet. Run the crawler and refresh the page.")
