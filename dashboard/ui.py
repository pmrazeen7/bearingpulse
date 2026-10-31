from __future__ import annotations

from typing import Any

import httpx
import pandas as pd
import streamlit as st

from config.settings import get_settings


settings = get_settings()


PIN_OPTIONS = ["All", "600001", "600002", "600017", "600028", "600040", "641001", "641002", "560001", "500001"]


def api_headers() -> dict[str, str]:
    return {"X-API-Key": settings.api_key}


def fetch_json(path: str, params: dict[str, Any] | None = None) -> Any:
    url = f"{settings.dashboard_api_base.rstrip('/')}/{path.lstrip('/')}"
    response = httpx.get(url, headers=api_headers(), params=params, timeout=20)
    response.raise_for_status()
    return response.json()


def post_json(path: str, payload: dict[str, Any]) -> Any:
    url = f"{settings.dashboard_api_base.rstrip('/')}/{path.lstrip('/')}"
    response = httpx.post(url, headers=api_headers(), json=payload, timeout=20)
    response.raise_for_status()
    return response.json()


def render_logo(mark: str = "full", scale: str = "regular") -> str:
    label = (
        '<div class="brand-wordmark"><span class="brand-wordmark-main">Bearing</span>'
        '<span class="brand-wordmark-accent">Pulse</span></div>'
    )
    return f"""
    <div class="brand-lockup brand-lockup-{scale}">
      <div class="brand-orbit-shell">
        <div class="brand-orbit-ring"></div>
        <div class="brand-core"></div>
        <div class="brand-dot brand-dot-one"></div>
        <div class="brand-dot brand-dot-two"></div>
        <div class="brand-notch"></div>
      </div>
      {label if mark == "full" else ""}
    </div>
    """


def inject_theme() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;700&family=Manrope:wght@400;500;600;700;800&display=swap');

        :root {
          --bg: #f5f7ff;
          --paper: rgba(255, 255, 255, 0.72);
          --paper-strong: rgba(255, 255, 255, 0.92);
          --border: rgba(108, 93, 211, 0.14);
          --ink: #17142a;
          --muted: #726d94;
          --accent: #6d5efb;
          --accent-2: #38d6c4;
          --accent-3: #ff8f6b;
          --shadow: 0 30px 80px rgba(86, 73, 171, 0.18);
        }

        html, body, [class*="css"] {
          font-family: 'Manrope', sans-serif;
          color: var(--ink);
          background:
            radial-gradient(circle at top left, rgba(115, 108, 255, 0.20), transparent 30%),
            radial-gradient(circle at top right, rgba(56, 214, 196, 0.18), transparent 26%),
            linear-gradient(180deg, #fbfbff 0%, #eef2ff 100%);
        }

        .stApp {
          background:
            radial-gradient(circle at 10% 10%, rgba(147, 129, 255, 0.26), transparent 22%),
            radial-gradient(circle at 90% 0%, rgba(69, 225, 201, 0.22), transparent 22%),
            linear-gradient(180deg, #fafbff 0%, #edf1ff 100%);
        }

        .block-container {
          padding-top: 1.25rem;
          padding-bottom: 4rem;
          max-width: 1280px;
        }

        [data-testid="stHeader"] {
          background: rgba(255, 255, 255, 0.0);
        }

        [data-testid="stSidebar"] {
          background: linear-gradient(180deg, rgba(255,255,255,0.92), rgba(245,247,255,0.88));
          border-right: 1px solid rgba(109, 94, 251, 0.10);
        }

        [data-testid="stSidebar"] * {
          font-family: 'Manrope', sans-serif;
        }

        .hero-shell {
          position: relative;
          overflow: hidden;
          padding: 1.5rem;
          border-radius: 36px;
          background: linear-gradient(145deg, rgba(255,255,255,0.82), rgba(245,246,255,0.62));
          border: 1px solid var(--border);
          box-shadow: var(--shadow);
          backdrop-filter: blur(22px);
          isolation: isolate;
          margin-bottom: 1.25rem;
        }

        .hero-shell::before,
        .hero-shell::after {
          content: "";
          position: absolute;
          inset: auto;
          border-radius: 999px;
          filter: blur(4px);
          animation: blobFloat 12s ease-in-out infinite;
        }

        .hero-shell::before {
          width: 280px;
          height: 280px;
          right: -60px;
          top: -70px;
          background: radial-gradient(circle, rgba(109,94,251,0.34), transparent 70%);
        }

        .hero-shell::after {
          width: 240px;
          height: 240px;
          left: -50px;
          bottom: -80px;
          background: radial-gradient(circle, rgba(56,214,196,0.28), transparent 68%);
          animation-delay: -5s;
        }

        .top-ribbon {
          display: flex;
          justify-content: space-between;
          align-items: center;
          gap: 1rem;
          margin-bottom: 1rem;
        }

        .ribbon-pill {
          display: inline-flex;
          align-items: center;
          gap: 0.5rem;
          padding: 0.7rem 1rem;
          border-radius: 999px;
          background: rgba(255,255,255,0.72);
          border: 1px solid rgba(109,94,251,0.12);
          box-shadow: 0 18px 40px rgba(108,93,211,0.10);
          font-size: 0.86rem;
          color: var(--muted);
        }

        .hero-grid {
          display: grid;
          grid-template-columns: 1.2fr 0.8fr;
          gap: 1.25rem;
          align-items: stretch;
        }

        .hero-copy {
          position: relative;
          z-index: 2;
          padding: 0.8rem 0.4rem 0.6rem;
        }

        .eyebrow {
          display: inline-flex;
          align-items: center;
          gap: 0.55rem;
          padding: 0.4rem 0.8rem;
          border-radius: 999px;
          color: var(--accent);
          background: rgba(109,94,251,0.10);
          font-size: 0.85rem;
          font-weight: 800;
          letter-spacing: 0.04em;
          text-transform: uppercase;
        }

        .hero-title {
          font-family: 'Space Grotesk', sans-serif;
          font-size: clamp(2.8rem, 6vw, 5.3rem);
          line-height: 0.95;
          letter-spacing: -0.06em;
          margin: 1rem 0 1rem;
        }

        .hero-title span {
          background: linear-gradient(135deg, #6d5efb 0%, #46d9d4 55%, #ff9a70 100%);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
        }

        .hero-subtitle {
          max-width: 40rem;
          font-size: 1.05rem;
          line-height: 1.8;
          color: var(--muted);
        }

        .hero-cta-row {
          display: flex;
          flex-wrap: wrap;
          gap: 0.8rem;
          margin-top: 1.4rem;
        }

        .hero-button,
        .ghost-button {
          display: inline-flex;
          align-items: center;
          gap: 0.55rem;
          text-decoration: none;
          padding: 0.95rem 1.25rem;
          border-radius: 18px;
          font-weight: 800;
          transition: transform 180ms ease, box-shadow 180ms ease, background 180ms ease;
        }

        .hero-button {
          color: white;
          background: linear-gradient(135deg, #6d5efb 0%, #4a7cff 100%);
          box-shadow: 0 18px 40px rgba(94, 87, 247, 0.26);
        }

        .ghost-button {
          color: var(--ink);
          background: rgba(255,255,255,0.76);
          border: 1px solid rgba(109,94,251,0.14);
        }

        .hero-button:hover,
        .ghost-button:hover {
          transform: translateY(-3px);
        }

        .hero-visual {
          position: relative;
          min-height: 430px;
          border-radius: 28px;
          overflow: hidden;
          padding: 1rem;
          background:
            linear-gradient(145deg, rgba(255,255,255,0.66), rgba(239,241,255,0.56)),
            radial-gradient(circle at top right, rgba(143,132,255,0.20), transparent 32%);
          border: 1px solid rgba(109,94,251,0.12);
          backdrop-filter: blur(22px);
        }

        .floating-dashboard {
          position: absolute;
          inset: 0;
          display: grid;
          place-items: center;
          perspective: 1400px;
        }

        .dashboard-plane {
          width: 92%;
          height: 86%;
          border-radius: 30px;
          padding: 1rem;
          transform: rotateX(12deg) rotateY(-16deg) translateY(0px);
          transform-style: preserve-3d;
          background: linear-gradient(180deg, rgba(255,255,255,0.96), rgba(242,245,255,0.90));
          border: 1px solid rgba(109,94,251,0.12);
          box-shadow: 0 36px 80px rgba(89, 77, 170, 0.22);
          animation: dashboardFloat 8s ease-in-out infinite;
        }

        .plane-topbar {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 0.85rem;
        }

        .plane-dots {
          display: flex;
          gap: 0.4rem;
        }

        .plane-dots span {
          width: 10px;
          height: 10px;
          border-radius: 50%;
          background: rgba(109,94,251,0.25);
        }

        .plane-dots span:first-child { background: #ff8f6b; }
        .plane-dots span:nth-child(2) { background: #ffd56b; }
        .plane-dots span:nth-child(3) { background: #46d9d4; }

        .plane-nav {
          display: flex;
          gap: 0.5rem;
          flex-wrap: wrap;
          margin-bottom: 0.9rem;
        }

        .plane-nav .chip {
          padding: 0.45rem 0.8rem;
          border-radius: 999px;
          background: rgba(109,94,251,0.10);
          color: #6758f6;
          font-size: 0.75rem;
          font-weight: 800;
        }

        .plane-grid {
          display: grid;
          grid-template-columns: 0.95fr 1.2fr;
          gap: 0.85rem;
          height: calc(100% - 82px);
        }

        .menu-stack,
        .chart-stack {
          display: grid;
          gap: 0.8rem;
        }

        .mini-panel,
        .big-panel {
          border-radius: 22px;
          background: linear-gradient(180deg, rgba(255,255,255,0.96), rgba(245,246,255,0.88));
          border: 1px solid rgba(109,94,251,0.12);
          box-shadow: inset 0 1px 0 rgba(255,255,255,0.8);
          padding: 1rem;
          position: relative;
          overflow: hidden;
        }

        .big-panel::after {
          content: "";
          position: absolute;
          inset: auto -15% -50% auto;
          width: 220px;
          height: 220px;
          border-radius: 50%;
          background: radial-gradient(circle, rgba(109,94,251,0.20), transparent 65%);
        }

        .bar-row {
          display: flex;
          gap: 0.55rem;
          align-items: end;
          height: 145px;
          margin-top: 1.1rem;
        }

        .bar-row span {
          flex: 1;
          border-radius: 18px 18px 8px 8px;
          background: linear-gradient(180deg, rgba(109,94,251,0.88), rgba(171,164,255,0.22));
          animation: pulseBar 3.6s ease-in-out infinite;
        }

        .bar-row span:nth-child(1) { height: 50%; animation-delay: -0.2s; }
        .bar-row span:nth-child(2) { height: 72%; animation-delay: -0.5s; }
        .bar-row span:nth-child(3) { height: 34%; animation-delay: -0.8s; }
        .bar-row span:nth-child(4) { height: 88%; animation-delay: -1.0s; }

        .stat-strip {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: 0.8rem;
          margin-top: 1rem;
        }

        .glass-stat,
        .info-card,
        .section-card,
        .insight-panel {
          background: var(--paper);
          border: 1px solid var(--border);
          box-shadow: var(--shadow);
          backdrop-filter: blur(22px);
        }

        .glass-stat {
          border-radius: 24px;
          padding: 1rem;
          overflow: hidden;
        }

        .glass-stat .label {
          color: var(--muted);
          font-size: 0.82rem;
        }

        .glass-stat .value {
          font-family: 'Space Grotesk', sans-serif;
          font-size: 1.9rem;
          font-weight: 700;
          margin-top: 0.25rem;
        }

        .glass-stat .delta {
          color: #1bb790;
          font-weight: 800;
          font-size: 0.88rem;
        }

        .section-card {
          border-radius: 30px;
          padding: 1.35rem;
          margin: 1rem 0;
        }

        .section-title {
          font-family: 'Space Grotesk', sans-serif;
          font-size: 1.65rem;
          margin: 0;
          letter-spacing: -0.04em;
        }

        .section-kicker {
          display: inline-block;
          margin-bottom: 0.5rem;
          color: var(--accent);
          font-size: 0.8rem;
          letter-spacing: 0.12em;
          text-transform: uppercase;
          font-weight: 800;
        }

        .section-copy {
          color: var(--muted);
          line-height: 1.75;
          max-width: 48rem;
        }

        .story-grid {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: 1rem;
          margin-top: 1rem;
        }

        .info-card {
          border-radius: 26px;
          padding: 1.2rem;
          min-height: 190px;
          position: relative;
          overflow: hidden;
        }

        .info-card::before {
          content: "";
          position: absolute;
          inset: auto auto -35% -15%;
          width: 180px;
          height: 180px;
          border-radius: 50%;
          background: radial-gradient(circle, rgba(109,94,251,0.18), transparent 70%);
        }

        .feature-metric {
          font-family: 'Space Grotesk', sans-serif;
          font-size: 2.2rem;
          font-weight: 700;
          margin-top: 1rem;
        }

        .scroll-river {
          display: grid;
          grid-template-columns: 0.8fr 1.2fr;
          gap: 1rem;
          margin-top: 1.4rem;
          align-items: start;
        }

        .sticky-logo {
          position: sticky;
          top: 5rem;
          border-radius: 30px;
          min-height: 420px;
          display: flex;
          align-items: center;
          justify-content: center;
          background: linear-gradient(145deg, rgba(109,94,251,0.12), rgba(56,214,196,0.10));
          border: 1px solid rgba(109,94,251,0.12);
          overflow: hidden;
        }

        .sticky-logo::before {
          content: "";
          position: absolute;
          width: 340px;
          height: 340px;
          border-radius: 50%;
          background: conic-gradient(from 120deg, rgba(109,94,251,0.24), rgba(56,214,196,0.10), rgba(255,143,107,0.22), rgba(109,94,251,0.24));
          animation: logoHalo 8s linear infinite;
        }

        .insight-panel {
          border-radius: 28px;
          padding: 1.2rem;
          margin-bottom: 1rem;
        }

        .insight-panel h4 {
          margin: 0;
          font-family: 'Space Grotesk', sans-serif;
          font-size: 1.2rem;
        }

        .insight-panel p,
        .insight-panel li,
        .brand-wordmark,
        .brand-wordmark-main,
        .brand-wordmark-accent {
          position: relative;
          z-index: 1;
        }

        .brand-lockup {
          display: inline-flex;
          align-items: center;
          gap: 1rem;
        }

        .brand-lockup-hero {
          gap: 1.2rem;
          animation: logoIntro 1.5s cubic-bezier(.2,.8,.2,1);
        }

        .brand-lockup-compact {
          gap: 0.65rem;
        }

        .brand-orbit-shell {
          width: 72px;
          height: 72px;
          border-radius: 24px;
          position: relative;
          display: grid;
          place-items: center;
          background: linear-gradient(180deg, rgba(255,255,255,0.88), rgba(239,242,255,0.76));
          border: 1px solid rgba(109,94,251,0.16);
          box-shadow: 0 20px 45px rgba(90, 77, 180, 0.20);
          overflow: hidden;
        }

        .brand-lockup-hero .brand-orbit-shell {
          width: 92px;
          height: 92px;
          border-radius: 30px;
        }

        .brand-orbit-ring {
          position: absolute;
          width: 54%;
          height: 54%;
          border: 7px solid rgba(109,94,251,0.84);
          border-right-color: rgba(56,214,196,0.82);
          border-top-color: rgba(255,143,107,0.82);
          border-radius: 50%;
          animation: spinLogo 6.5s linear infinite;
        }

        .brand-core {
          width: 18px;
          height: 18px;
          border-radius: 50%;
          background: linear-gradient(135deg, #17142a 0%, #6d5efb 100%);
          box-shadow: 0 0 0 10px rgba(109,94,251,0.08);
        }

        .brand-dot,
        .brand-notch {
          position: absolute;
          border-radius: 999px;
        }

        .brand-dot {
          width: 10px;
          height: 10px;
          background: white;
          box-shadow: 0 0 0 4px rgba(109,94,251,0.18);
        }

        .brand-dot-one { top: 18px; right: 20px; }
        .brand-dot-two { bottom: 16px; left: 18px; background: #46d9d4; }

        .brand-notch {
          width: 28px;
          height: 10px;
          background: linear-gradient(90deg, rgba(255,255,255,0.0), rgba(109,94,251,0.55));
          transform: rotate(-32deg);
          right: 8px;
          bottom: 16px;
        }

        .brand-wordmark {
          display: flex;
          flex-direction: column;
          line-height: 0.88;
          font-family: 'Space Grotesk', sans-serif;
        }

        .brand-wordmark-main,
        .brand-wordmark-accent {
          font-size: 1.45rem;
          font-weight: 700;
          letter-spacing: -0.06em;
        }

        .brand-wordmark-accent {
          color: var(--accent);
        }

        .metric-band {
          display: grid;
          grid-template-columns: repeat(4, 1fr);
          gap: 0.85rem;
          margin-top: 1rem;
        }

        .dashboard-section-title {
          font-family: 'Space Grotesk', sans-serif;
          font-size: 2rem;
          letter-spacing: -0.05em;
          margin-bottom: 0.3rem;
        }

        .dashboard-section-copy {
          color: var(--muted);
          max-width: 42rem;
        }

        .table-chip {
          display: inline-flex;
          align-items: center;
          padding: 0.35rem 0.7rem;
          border-radius: 999px;
          font-size: 0.75rem;
          font-weight: 800;
          background: rgba(109,94,251,0.10);
          color: var(--accent);
        }

        .footer-note {
          margin-top: 1rem;
          color: var(--muted);
          font-size: 0.9rem;
        }

        .stTabs [data-baseweb="tab-list"] {
          gap: 0.65rem;
          background: rgba(255,255,255,0.45);
          padding: 0.45rem;
          border-radius: 20px;
          border: 1px solid rgba(109,94,251,0.10);
        }

        .stTabs [data-baseweb="tab"] {
          border-radius: 16px;
          height: 48px;
          padding: 0 1rem;
          background: transparent;
          color: var(--muted);
          font-weight: 800;
        }

        .stTabs [aria-selected="true"] {
          background: linear-gradient(135deg, rgba(109,94,251,0.16), rgba(70,217,212,0.12)) !important;
          color: var(--ink) !important;
        }

        .stSelectbox > div > div,
        .stTextInput > div > div > input,
        .stNumberInput input {
          border-radius: 18px !important;
          border: 1px solid rgba(109,94,251,0.14) !important;
          background: rgba(255,255,255,0.82) !important;
        }

        .stButton button,
        .stDownloadButton button,
        .stFormSubmitButton button {
          border-radius: 18px !important;
          border: none !important;
          background: linear-gradient(135deg, #6d5efb 0%, #4a7cff 100%) !important;
          color: white !important;
          font-weight: 800 !important;
          box-shadow: 0 18px 36px rgba(96, 88, 244, 0.24);
        }

        div[data-testid="stMetric"] {
          background: rgba(255,255,255,0.72);
          border-radius: 22px;
          padding: 1rem;
          border: 1px solid rgba(109,94,251,0.12);
          box-shadow: 0 18px 44px rgba(86, 73, 171, 0.12);
        }

        div[data-testid="stDataFrame"] {
          border-radius: 24px;
          overflow: hidden;
          border: 1px solid rgba(109,94,251,0.12);
          box-shadow: 0 18px 44px rgba(86, 73, 171, 0.12);
        }

        @keyframes spinLogo {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }

        @keyframes blobFloat {
          0%, 100% { transform: translate3d(0, 0, 0) scale(1); }
          50% { transform: translate3d(10px, 12px, 0) scale(1.05); }
        }

        @keyframes logoIntro {
          0% { opacity: 0; transform: translateY(20px) scale(0.88); }
          100% { opacity: 1; transform: translateY(0) scale(1); }
        }

        @keyframes dashboardFloat {
          0%, 100% { transform: rotateX(12deg) rotateY(-16deg) translateY(0px); }
          50% { transform: rotateX(10deg) rotateY(-12deg) translateY(-12px); }
        }

        @keyframes pulseBar {
          0%, 100% { opacity: 0.78; transform: translateY(0); }
          50% { opacity: 1; transform: translateY(-6px); }
        }

        @keyframes logoHalo {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }

        @media (max-width: 1024px) {
          .hero-grid,
          .story-grid,
          .metric-band,
          .scroll-river,
          .plane-grid,
          .stat-strip {
            grid-template-columns: 1fr;
          }

          .hero-visual {
            min-height: 340px;
          }

          .sticky-logo {
            position: relative;
            top: auto;
            min-height: 260px;
          }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_dashboard_intro(title: str, subtitle: str, chips: list[str] | None = None) -> None:
    chip_markup = "".join(f'<span class="table-chip">{chip}</span>' for chip in (chips or []))
    st.markdown(
        f"""
        <div class="section-card">
          <div style="display:flex; justify-content:space-between; gap:1rem; align-items:flex-start; flex-wrap:wrap;">
            <div>
              <div class="section-kicker">Live Control Surface</div>
              <div class="dashboard-section-title">{title}</div>
              <div class="dashboard-section-copy">{subtitle}</div>
            </div>
            <div style="display:flex; gap:0.5rem; flex-wrap:wrap;">{chip_markup}</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar_brand() -> None:
    with st.sidebar:
        st.markdown(
            f"""
            <div style="padding:0.5rem 0 1rem 0;">
              <div class="section-kicker">BearingPulse</div>
              {render_logo(mark="full", scale="compact")}
              <div class="footer-note" style="margin-top:0.8rem;">
                Amazon India bearing pricing, seller shifts, Buy Box control, and alert intelligence.
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def safe_frame(records: list[dict[str, Any]]) -> pd.DataFrame:
    return pd.DataFrame(records) if records else pd.DataFrame()
