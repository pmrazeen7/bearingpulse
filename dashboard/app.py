from __future__ import annotations

import pandas as pd
import streamlit as st

from dashboard.landing_components import render_motion_bridge_note, render_motion_splash, render_scroll_gallery
from dashboard.ui import fetch_json, inject_theme, render_dashboard_intro, render_logo, render_sidebar_brand, safe_frame


st.set_page_config(
    page_title="BearingPulse",
    page_icon="BP",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_theme()
render_sidebar_brand()


def _render_hero() -> None:
    render_motion_splash()
    st.markdown(
        f"""
        <section class="hero-shell">
          <div class="top-ribbon">
            <div class="ribbon-pill">{render_logo(mark="full", scale="compact")}</div>
            <div class="ribbon-pill">Amazon India | Seller Intelligence | Tamil Nadu Geo Simulation</div>
          </div>
          <div class="hero-grid">
            <div class="hero-copy">
              <div class="eyebrow">Realtime Bearing Intelligence</div>
              <h1 class="hero-title">Monitor the <span>Buy Box battle</span> before your competitors see it.</h1>
              <p class="hero-subtitle">
                Inspired by premium fintech dashboards, BearingPulse turns Amazon India bearing monitoring into a cinematic
                command center with price velocity, seller undercuts, pincode-aware offer shifts, and motion-rich storytelling.
              </p>
              <div class="hero-cta-row">
                <a class="hero-button" href="#dashboard-core">Launch analytics</a>
                <a class="ghost-button" href="#story-core">See motion story</a>
              </div>
              <div class="metric-band">
                <div class="glass-stat">
                  <div class="label">Tracked queries</div>
                  <div class="value">6</div>
                  <div class="delta">Auto-refreshing every cycle</div>
                </div>
                <div class="glass-stat">
                  <div class="label">Offer surveillance</div>
                  <div class="value">9 PINs</div>
                  <div class="delta">Buy Box location drift</div>
                </div>
                <div class="glass-stat">
                  <div class="label">Alerting cadence</div>
                  <div class="value">15m</div>
                  <div class="delta">Threshold and stock events</div>
                </div>
                <div class="glass-stat">
                  <div class="label">Visual language</div>
                  <div class="value">Glass+</div>
                  <div class="delta">Gradient motion transitions</div>
                </div>
              </div>
            </div>
            <div class="hero-visual">
              <div class="floating-dashboard">
                <div class="dashboard-plane">
                  <div class="plane-topbar">
                    <div class="plane-dots"><span></span><span></span><span></span></div>
                    <div class="table-chip">Pulse Board</div>
                  </div>
                  <div class="plane-nav">
                    <div class="chip">Price Trends</div>
                    <div class="chip">Seller Radar</div>
                    <div class="chip">Buy Box Drift</div>
                    <div class="chip">Alerts</div>
                  </div>
                  <div class="plane-grid">
                    <div class="menu-stack">
                      <div class="mini-panel">
                        <div class="section-kicker">Live spread</div>
                        <div class="feature-metric">INR 228</div>
                        <div class="section-copy">Fastest undercut window across tracked seller offers.</div>
                      </div>
                      <div class="mini-panel">
                        <div class="section-kicker">Coverage</div>
                        <div class="section-copy">Search discovery, PDP refresh, seller listing surveillance and alerting in one loop.</div>
                      </div>
                    </div>
                    <div class="chart-stack">
                      <div class="big-panel">
                        <div class="section-kicker">Animated Buy Box overview</div>
                        <div class="feature-metric">58.1%</div>
                        <div class="bar-row"><span></span><span></span><span></span><span></span></div>
                      </div>
                      <div class="stat-strip">
                        <div class="mini-panel"><div class="section-kicker">Leader</div><div class="feature-metric">SKF 6205</div></div>
                        <div class="mini-panel"><div class="section-kicker">Shift</div><div class="feature-metric">4 sellers</div></div>
                        <div class="mini-panel"><div class="section-kicker">Delta</div><div class="feature-metric">-7.2%</div></div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def _render_story() -> None:
    st.markdown(
        """
        <div id="story-core" class="section-card">
          <div class="section-kicker">Reference-inspired motion system</div>
          <h2 class="section-title">Soft glass, floating surfaces, and dashboard depth tuned for industrial intelligence.</h2>
          <p class="section-copy">
            The references pointed toward a hybrid of futuristic fintech and premium analytics. This landing page translates
            that into bearing-distributor workflows with stacked glass cards, candy gradients, oversized typography, and
            layered motion that feels alive while still leaving room for dense data.
          </p>
          <div class="story-grid">
            <div class="info-card">
              <div class="section-kicker">Surface language</div>
              <h3 class="section-title" style="font-size:1.45rem;">Glass command cards</h3>
              <p class="section-copy">Rounded translucent modules echo the banking-dashboard references while keeping serious B2B analytics legible.</p>
              <div class="feature-metric">01</div>
            </div>
            <div class="info-card">
              <div class="section-kicker">Motion rhythm</div>
              <h3 class="section-title" style="font-size:1.45rem;">Logo-to-interface transition</h3>
              <p class="section-copy">The custom orbit logo animates like a bearing race and visually flows into the rotating analytics deck.</p>
              <div class="feature-metric">02</div>
            </div>
            <div class="info-card">
              <div class="section-kicker">Scroll story</div>
              <h3 class="section-title" style="font-size:1.45rem;">Sticky visual spine</h3>
              <p class="section-copy">A persistent logo halo on scroll anchors the experience while the narrative panels move past it like a product reveal.</p>
              <div class="feature-metric">03</div>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    render_motion_bridge_note()
    render_scroll_gallery()

    st.markdown(
        f"""
        <div class="scroll-river">
          <div class="sticky-logo">{render_logo(mark="full", scale="hero")}</div>
          <div>
            <div class="insight-panel">
              <div class="section-kicker">Transition concept</div>
              <h4>The logo behaves like a precision bearing race.</h4>
              <p class="section-copy">Concentric orbital rings, rotating accents, and a central core communicate movement, stability, and competitive rotation. That same circular geometry repeats in charts, alert chips, and hover states so the whole product feels tied back to the brand mark.</p>
            </div>
            <div class="insight-panel">
              <div class="section-kicker">Landing page arc</div>
              <h4>From cinematic intro to operations console.</h4>
              <p class="section-copy">The first screen sells the system. As you scroll down, the vibe compresses into tighter glass cards and operational metrics, mirroring the move from strategy view into live monitoring.</p>
            </div>
            <div class="insight-panel">
              <div class="section-kicker">UI attitude</div>
              <h4>Premium, not generic.</h4>
              <p class="section-copy">Instead of a plain Streamlit utility layout, the dashboard now leans into expressive type, layered gradients, soft shadows, and intentional spacing. It keeps the analytics useful while giving the product a real market-facing personality.</p>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_snapshot() -> None:
    try:
        asins = safe_frame(fetch_json("/asins"))
        alerts = safe_frame(fetch_json("/alerts"))
        sellers = safe_frame(fetch_json("/sellers"))
    except Exception:
        asins = pd.DataFrame()
        alerts = pd.DataFrame()
        sellers = pd.DataFrame()

    render_dashboard_intro(
        "Mission control at a glance",
        "A quick executive snapshot that bridges the landing experience into the page-level analytics modules.",
        chips=["Animated", "Glass UI", "API-backed"],
    )

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Tracked ASINs", int(len(asins.index)), "+ discovery loop")
    with col2:
        st.metric("Known sellers", int(len(sellers.index)), "+ live coverage")
    with col3:
        active_alerts = int(len(alerts.index))
        st.metric("Recent alerts", active_alerts, "price and Buy Box")
    with col4:
        buybox_winners = int(asins["latest_seller"].nunique()) if not asins.empty and "latest_seller" in asins else 0
        st.metric("Latest leaders", buybox_winners, "seller spread")

    left, right = st.columns([1.3, 0.7])
    with left:
        st.markdown(
            """
            <div id="dashboard-core" class="section-card">
              <div class="section-kicker">Dashboard sections</div>
              <h3 class="section-title">Scroll, then move into the analytics pages from the sidebar.</h3>
              <p class="section-copy">
                Each page below the landing experience inherits the same design language: softened chart containers, branded
                filters, richer tables, and stronger information hierarchy for price competition workflows.
              </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with right:
        st.markdown(
            """
            <div class="section-card">
              <div class="section-kicker">What changed</div>
              <p class="section-copy">Landing page, custom logo, animated glass visuals, premium stat cards, and upgraded analytics presentation.</p>
              <div class="footer-note">Use the sidebar pages to explore trends, competitor spreads, Buy Box history, and alerts.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


_render_hero()
_render_story()
_render_snapshot()
