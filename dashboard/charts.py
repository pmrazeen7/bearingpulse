from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def price_trend_chart(df: pd.DataFrame):
    color_sequence = ["#6D5EFB", "#38D6C4", "#FF8F6B", "#182039", "#8C82FF", "#22BFA8"]
    fig = px.line(
        df,
        x="scraped_at",
        y="price",
        color="seller_name",
        markers=True,
        line_dash="buybox_label",
        color_discrete_sequence=color_sequence,
    )
    if "mrp" in df and df["mrp"].notna().any():
        fig.add_trace(
            go.Scatter(
                x=df["scraped_at"],
                y=df["mrp"],
                mode="lines",
                name="MRP",
                line={"dash": "dash", "color": "#666666"},
            )
        )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(255,255,255,0)",
        margin={"l": 10, "r": 10, "t": 10, "b": 10},
        legend_title_text="Seller",
        font={"family": "Manrope, sans-serif", "color": "#17142A"},
        xaxis={"showgrid": False, "title": ""},
        yaxis={"gridcolor": "rgba(109,94,251,0.10)", "title": "Price (INR)"},
    )
    fig.update_traces(line={"width": 3}, marker={"size": 8})
    return fig


def buybox_timeline_chart(df: pd.DataFrame):
    fig = px.bar(
        df,
        x="hour",
        y="value",
        color="seller_name",
        barmode="stack",
        color_discrete_sequence=["#6D5EFB", "#38D6C4", "#FF8F6B", "#182039", "#8C82FF"],
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(255,255,255,0)",
        margin={"l": 10, "r": 10, "t": 10, "b": 10},
        font={"family": "Manrope, sans-serif", "color": "#17142A"},
        xaxis={"title": ""},
        yaxis={"gridcolor": "rgba(109,94,251,0.10)", "title": "Buy Box hours"},
    )
    return fig
