from __future__ import annotations

import streamlit as st
import streamlit.components.v1 as components


def render_motion_splash() -> None:
    components.html(
        """
        <!DOCTYPE html>
        <html lang="en">
          <head>
            <meta charset="utf-8" />
            <style>
              :root {
                --bg: #0f1022;
                --ink: #ffffff;
                --muted: rgba(255,255,255,0.76);
                --violet: #7d68ff;
                --cyan: #45ddd0;
                --peach: #ff9c7a;
                --panel: rgba(255,255,255,0.08);
              }

              * { box-sizing: border-box; }

              body {
                margin: 0;
                overflow: hidden;
                font-family: "Inter", sans-serif;
                background:
                  radial-gradient(circle at 20% 20%, rgba(125,104,255,0.32), transparent 22%),
                  radial-gradient(circle at 80% 15%, rgba(69,221,208,0.26), transparent 22%),
                  radial-gradient(circle at 60% 70%, rgba(255,156,122,0.22), transparent 24%),
                  linear-gradient(160deg, #0f1022 0%, #171833 52%, #111223 100%);
              }

              .stage {
                position: relative;
                width: 100vw;
                height: 520px;
                overflow: hidden;
                border-radius: 34px;
                background:
                  linear-gradient(180deg, rgba(255,255,255,0.03), rgba(255,255,255,0.00)),
                  linear-gradient(155deg, rgba(125,104,255,0.08), rgba(69,221,208,0.06));
                border: 1px solid rgba(255,255,255,0.08);
                box-shadow: 0 35px 110px rgba(23, 20, 52, 0.45);
                isolation: isolate;
              }

              .grain,
              .orbits,
              .beam,
              .content,
              .cards {
                position: absolute;
                inset: 0;
              }

              .grain {
                background-image:
                  radial-gradient(rgba(255,255,255,0.10) 0.7px, transparent 0.7px);
                background-size: 14px 14px;
                mix-blend-mode: soft-light;
                opacity: 0.22;
              }

              .beam::before,
              .beam::after {
                content: "";
                position: absolute;
                inset: auto;
                filter: blur(18px);
                border-radius: 999px;
                animation: drift 10s ease-in-out infinite;
              }

              .beam::before {
                width: 260px;
                height: 260px;
                top: -50px;
                right: -50px;
                background: radial-gradient(circle, rgba(125,104,255,0.48), transparent 68%);
              }

              .beam::after {
                width: 240px;
                height: 240px;
                bottom: -80px;
                left: -40px;
                background: radial-gradient(circle, rgba(69,221,208,0.38), transparent 70%);
                animation-delay: -4s;
              }

              .ring-wrap {
                position: absolute;
                top: 50%;
                left: 50%;
                width: 180px;
                height: 180px;
                transform: translate(-50%, -50%);
              }

              .ring,
              .ring-two,
              .ring-three {
                position: absolute;
                inset: 0;
                border-radius: 50%;
                border: 1px solid rgba(255,255,255,0.16);
              }

              .ring {
                animation: rotate 7.5s linear infinite;
                border-top-color: rgba(125,104,255,0.92);
                border-right-color: rgba(69,221,208,0.88);
              }

              .ring-two {
                inset: 18px;
                animation: rotateReverse 6s linear infinite;
                border-left-color: rgba(255,156,122,0.88);
                border-bottom-color: rgba(125,104,255,0.55);
              }

              .ring-three {
                inset: 44px;
                background: radial-gradient(circle, rgba(255,255,255,0.96), rgba(232,236,255,0.9));
                border: none;
                box-shadow:
                  0 0 0 14px rgba(125,104,255,0.10),
                  0 0 55px rgba(125,104,255,0.24);
                animation: pulse 3.2s ease-in-out infinite;
              }

              .content {
                display: grid;
                grid-template-columns: 1.2fr 0.8fr;
                gap: 18px;
                align-items: stretch;
                padding: 38px;
                z-index: 3;
              }

              .copy {
                display: flex;
                flex-direction: column;
                justify-content: center;
                transform: translateY(10px);
                opacity: 0;
                animation: reveal 900ms cubic-bezier(.2,.8,.2,1) 300ms forwards;
              }

              .eyebrow {
                display: inline-flex;
                align-items: center;
                gap: 10px;
                width: fit-content;
                padding: 10px 14px;
                border-radius: 999px;
                background: rgba(255,255,255,0.08);
                border: 1px solid rgba(255,255,255,0.10);
                color: var(--muted);
                text-transform: uppercase;
                font-size: 11px;
                letter-spacing: 0.18em;
                font-weight: 700;
              }

              .title {
                margin: 18px 0 14px;
                font-size: clamp(42px, 6vw, 74px);
                line-height: 0.92;
                font-weight: 800;
                letter-spacing: -0.07em;
                color: var(--ink);
              }

              .title span {
                display: block;
                background: linear-gradient(135deg, #8d7bff 0%, #48ddd0 56%, #ffb08a 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
              }

              .subtitle {
                max-width: 610px;
                color: var(--muted);
                line-height: 1.8;
                font-size: 15px;
              }

              .pills {
                display: flex;
                flex-wrap: wrap;
                gap: 10px;
                margin-top: 18px;
              }

              .pill {
                padding: 10px 14px;
                border-radius: 999px;
                background: rgba(255,255,255,0.07);
                border: 1px solid rgba(255,255,255,0.11);
                color: var(--ink);
                font-size: 12px;
                font-weight: 700;
              }

              .cards {
                position: relative;
                z-index: 2;
              }

              .float-card {
                position: absolute;
                border-radius: 26px;
                background:
                  linear-gradient(180deg, rgba(255,255,255,0.18), rgba(255,255,255,0.08));
                border: 1px solid rgba(255,255,255,0.12);
                backdrop-filter: blur(22px);
                box-shadow: 0 28px 70px rgba(8, 10, 24, 0.22);
                color: white;
                padding: 18px;
              }

              .card-main {
                width: 320px;
                height: 220px;
                right: 42px;
                top: 58px;
                transform: rotate(-7deg);
                animation: floatMain 8s ease-in-out infinite;
              }

              .card-small {
                width: 180px;
                height: 110px;
                right: 260px;
                top: 28px;
                transform: rotate(10deg);
                animation: floatSmall 7s ease-in-out infinite;
              }

              .card-mini {
                width: 210px;
                height: 120px;
                right: 86px;
                bottom: 38px;
                transform: rotate(6deg);
                animation: floatMini 9s ease-in-out infinite;
              }

              .card-label {
                font-size: 12px;
                letter-spacing: 0.18em;
                text-transform: uppercase;
                color: rgba(255,255,255,0.72);
                margin-bottom: 8px;
              }

              .card-value {
                font-size: 34px;
                font-weight: 800;
                letter-spacing: -0.05em;
              }

              .bars {
                display: flex;
                align-items: end;
                gap: 8px;
                height: 84px;
                margin-top: 20px;
              }

              .bars span {
                flex: 1;
                border-radius: 999px 999px 18px 18px;
                background: linear-gradient(180deg, rgba(255,255,255,0.95), rgba(255,255,255,0.22));
                animation: bars 2.8s ease-in-out infinite;
              }

              .bars span:nth-child(1) { height: 38%; animation-delay: -.2s; }
              .bars span:nth-child(2) { height: 68%; animation-delay: -.5s; }
              .bars span:nth-child(3) { height: 50%; animation-delay: -.8s; }
              .bars span:nth-child(4) { height: 88%; animation-delay: -1s; }

              .progress {
                margin-top: 16px;
                height: 8px;
                border-radius: 999px;
                background: rgba(255,255,255,0.12);
                overflow: hidden;
              }

              .progress > div {
                height: 100%;
                width: 58%;
                border-radius: inherit;
                background: linear-gradient(90deg, var(--cyan), var(--violet));
                animation: grow 3.8s ease-in-out infinite;
              }

              .screen-wipe {
                position: absolute;
                inset: 0;
                z-index: 4;
                pointer-events: none;
                background: linear-gradient(135deg, rgba(125,104,255,0.22), rgba(69,221,208,0.0) 40%, rgba(255,156,122,0.16));
                transform: translateX(-110%);
                animation: wipe 1.4s cubic-bezier(.2,.8,.2,1) forwards;
              }

              @keyframes rotate {
                from { transform: rotate(0deg); }
                to { transform: rotate(360deg); }
              }

              @keyframes rotateReverse {
                from { transform: rotate(360deg); }
                to { transform: rotate(0deg); }
              }

              @keyframes pulse {
                0%, 100% { transform: scale(1); }
                50% { transform: scale(1.08); }
              }

              @keyframes reveal {
                to { opacity: 1; transform: translateY(0); }
              }

              @keyframes drift {
                0%, 100% { transform: translate3d(0,0,0) scale(1); }
                50% { transform: translate3d(15px, 12px, 0) scale(1.04); }
              }

              @keyframes floatMain {
                0%, 100% { transform: rotate(-7deg) translateY(0); }
                50% { transform: rotate(-4deg) translateY(-10px); }
              }

              @keyframes floatSmall {
                0%, 100% { transform: rotate(10deg) translateY(0); }
                50% { transform: rotate(7deg) translateY(-12px); }
              }

              @keyframes floatMini {
                0%, 100% { transform: rotate(6deg) translateY(0); }
                50% { transform: rotate(9deg) translateY(-8px); }
              }

              @keyframes bars {
                0%, 100% { opacity: .72; transform: translateY(0); }
                50% { opacity: 1; transform: translateY(-4px); }
              }

              @keyframes grow {
                0%, 100% { width: 58%; }
                50% { width: 72%; }
              }

              @keyframes wipe {
                0% { transform: translateX(-110%) skewX(-10deg); opacity: 0.9; }
                65% { transform: translateX(0%) skewX(-10deg); opacity: 1; }
                100% { transform: translateX(115%) skewX(-10deg); opacity: 0; }
              }

              @media (max-width: 920px) {
                .stage { height: 680px; }
                .content {
                  grid-template-columns: 1fr;
                  padding: 28px;
                }
                .cards { min-height: 260px; }
                .card-main { right: 16px; top: 24px; width: 280px; }
                .card-small { left: 18px; right: auto; top: 160px; }
                .card-mini { right: 28px; bottom: 10px; }
              }
            </style>
          </head>
          <body>
            <div class="stage">
              <div class="grain"></div>
              <div class="beam"></div>
              <div class="orbits">
                <div class="ring-wrap">
                  <div class="ring"></div>
                  <div class="ring-two"></div>
                  <div class="ring-three"></div>
                </div>
              </div>
              <div class="content">
                <div class="copy">
                  <div class="eyebrow">BearingPulse Motion Intro</div>
                  <div class="title">Precision motion for <span>price intelligence</span></div>
                  <div class="subtitle">
                    A cinematic brand reveal inspired by futuristic fintech dashboards. The orbiting bearing mark opens the
                    experience and visually transitions into floating analytics cards, gradient motion, and layered glass panels.
                  </div>
                  <div class="pills">
                    <div class="pill">Animated logo reveal</div>
                    <div class="pill">Glass dashboard deck</div>
                    <div class="pill">Scroll-ready visual language</div>
                  </div>
                </div>
                <div class="cards">
                  <div class="float-card card-main">
                    <div class="card-label">Buy Box volatility</div>
                    <div class="card-value">58.1%</div>
                    <div class="bars"><span></span><span></span><span></span><span></span></div>
                  </div>
                  <div class="float-card card-small">
                    <div class="card-label">Spread</div>
                    <div class="card-value">₹228</div>
                  </div>
                  <div class="float-card card-mini">
                    <div class="card-label">Geo drift</div>
                    <div class="card-value">9 PINs</div>
                    <div class="progress"><div></div></div>
                  </div>
                </div>
              </div>
              <div class="screen-wipe"></div>
            </div>
          </body>
        </html>
        """,
        height=520,
    )


def render_scroll_gallery() -> None:
    components.html(
        """
        <!DOCTYPE html>
        <html lang="en">
          <head>
            <meta charset="utf-8" />
            <style>
              * { box-sizing: border-box; }
              body {
                margin: 0;
                font-family: "Inter", sans-serif;
                background: transparent;
                color: #17142a;
              }

              .gallery {
                display: grid;
                grid-template-columns: 0.9fr 1.1fr;
                gap: 18px;
                min-height: 760px;
              }

              .visual-column {
                position: sticky;
                top: 18px;
                height: 680px;
                border-radius: 32px;
                overflow: hidden;
                background:
                  radial-gradient(circle at 30% 20%, rgba(125,104,255,0.22), transparent 24%),
                  radial-gradient(circle at 70% 72%, rgba(69,221,208,0.20), transparent 24%),
                  linear-gradient(160deg, rgba(255,255,255,0.85), rgba(239,243,255,0.72));
                border: 1px solid rgba(109,94,251,0.10);
                box-shadow: 0 30px 85px rgba(86, 73, 171, 0.16);
              }

              .visual-shell {
                position: absolute;
                inset: 0;
                display: grid;
                place-items: center;
                perspective: 1200px;
              }

              .stack {
                position: relative;
                width: 82%;
                height: 78%;
              }

              .panel {
                position: absolute;
                inset: auto;
                width: 100%;
                height: 74%;
                left: 0;
                border-radius: 28px;
                background: linear-gradient(180deg, rgba(255,255,255,0.96), rgba(244,247,255,0.88));
                border: 1px solid rgba(109,94,251,0.12);
                box-shadow: 0 28px 70px rgba(88, 74, 180, 0.14);
                transform-style: preserve-3d;
                transition: transform 400ms ease, opacity 400ms ease;
              }

              .panel-one { top: 0; transform: rotate(-8deg) translateY(22px); opacity: 0.46; }
              .panel-two { top: 52px; transform: rotate(6deg) translateY(14px); opacity: 0.62; }
              .panel-three { top: 102px; transform: rotate(-3deg) translateY(0); opacity: 1; }

              .panel-content {
                padding: 22px;
              }

              .panel-top {
                display: flex;
                justify-content: space-between;
                align-items: center;
              }

              .chip {
                padding: 8px 12px;
                border-radius: 999px;
                background: rgba(109,94,251,0.10);
                color: #6d5efb;
                font-size: 11px;
                font-weight: 800;
                text-transform: uppercase;
                letter-spacing: 0.12em;
              }

              .metric {
                margin-top: 20px;
                font-size: 48px;
                font-weight: 800;
                letter-spacing: -0.06em;
              }

              .line {
                margin-top: 22px;
                height: 120px;
                width: 100%;
                position: relative;
                overflow: hidden;
              }

              .line svg {
                position: absolute;
                inset: 0;
                width: 100%;
                height: 100%;
              }

              .story-column {
                display: grid;
                gap: 18px;
              }

              .story-card {
                min-height: 220px;
                padding: 24px;
                border-radius: 28px;
                background: linear-gradient(180deg, rgba(255,255,255,0.78), rgba(247,249,255,0.70));
                border: 1px solid rgba(109,94,251,0.10);
                box-shadow: 0 24px 65px rgba(86, 73, 171, 0.12);
                transform: translateY(24px);
                opacity: 0;
                transition: transform 700ms cubic-bezier(.2,.8,.2,1), opacity 700ms ease;
              }

              .story-card.visible {
                transform: translateY(0);
                opacity: 1;
              }

              .eyebrow {
                color: #6d5efb;
                font-size: 11px;
                letter-spacing: 0.16em;
                text-transform: uppercase;
                font-weight: 800;
              }

              h3 {
                margin: 12px 0 10px;
                font-size: 32px;
                line-height: 1.02;
                letter-spacing: -0.05em;
              }

              p {
                margin: 0;
                line-height: 1.8;
                color: #726d94;
              }

              @media (max-width: 920px) {
                .gallery { grid-template-columns: 1fr; }
                .visual-column {
                  position: relative;
                  top: 0;
                  height: 480px;
                }
              }
            </style>
          </head>
          <body>
            <div class="gallery">
              <div class="visual-column">
                <div class="visual-shell">
                  <div class="stack">
                    <div class="panel panel-one">
                      <div class="panel-content">
                        <div class="panel-top"><div class="chip">Seller Radar</div><div>01</div></div>
                        <div class="metric">₹ 1,234</div>
                      </div>
                    </div>
                    <div class="panel panel-two">
                      <div class="panel-content">
                        <div class="panel-top"><div class="chip">Pincode Shift</div><div>02</div></div>
                        <div class="metric">600028</div>
                      </div>
                    </div>
                    <div class="panel panel-three">
                      <div class="panel-content">
                        <div class="panel-top"><div class="chip">Price Momentum</div><div>03</div></div>
                        <div class="metric">-7.2%</div>
                        <div class="line">
                          <svg viewBox="0 0 400 120" preserveAspectRatio="none">
                            <defs>
                              <linearGradient id="g" x1="0%" y1="0%" x2="100%" y2="0%">
                                <stop offset="0%" stop-color="#6d5efb" />
                                <stop offset="100%" stop-color="#38d6c4" />
                              </linearGradient>
                            </defs>
                            <path d="M0,90 C45,60 80,20 130,38 C172,54 202,100 240,72 C286,40 332,20 400,16"
                                  fill="none" stroke="url(#g)" stroke-width="10" stroke-linecap="round"/>
                          </svg>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              <div class="story-column">
                <div class="story-card">
                  <div class="eyebrow">Section 01</div>
                  <h3>Scroll-driven reveal without losing the dashboard feel.</h3>
                  <p>The left-side card stack behaves like a hero mockup while the right column reveals product story panels. It gives the page more of a launch-site rhythm while staying native to the data product.</p>
                </div>
                <div class="story-card">
                  <div class="eyebrow">Section 02</div>
                  <h3>Logo language cascades into the interface.</h3>
                  <p>Rounded corners, orbital motion, and violet-cyan gradients continue from the hero mark into cards, charts, chips, and panel stacking for a more coherent brand system.</p>
                </div>
                <div class="story-card">
                  <div class="eyebrow">Section 03</div>
                  <h3>Closer to a custom front end, still easy to run.</h3>
                  <p>This approach keeps the existing Streamlit architecture intact while adding a more ambitious visual layer through embedded motion components and scroll-triggered presentation.</p>
                </div>
              </div>
            </div>
            <script>
              const cards = Array.from(document.querySelectorAll('.story-card'));
              const observer = new IntersectionObserver((entries) => {
                entries.forEach((entry) => {
                  if (entry.isIntersecting) {
                    entry.target.classList.add('visible');
                  }
                });
              }, { threshold: 0.2 });
              cards.forEach((card, index) => {
                card.style.transitionDelay = `${index * 120}ms`;
                observer.observe(card);
              });
            </script>
          </body>
        </html>
        """,
        height=760,
        scrolling=False,
    )


def render_motion_bridge_note() -> None:
    st.markdown(
        """
        <div class="section-card">
          <div class="section-kicker">Front-end pass</div>
          <div class="section-title">The dashboard now opens like a branded product reveal.</div>
          <div class="section-copy">
            This motion layer creates the “transition out of the logo” effect you asked for: the logo reveals first, the
            interface blooms around it, then the experience collapses into the operational dashboard below.
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
