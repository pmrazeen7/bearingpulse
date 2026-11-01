import React, { useEffect, useRef } from "react";
import { Link } from "react-router-dom";
import {
  ArrowRight,
  BellRing,
  Braces,
  Crown,
  LineChart as LineIcon,
  MapPin,
  Radar,
  ScanSearch,
  ShieldCheck,
  Store,
  Zap,
} from "lucide-react";

import { Logo, LogoMark } from "../components/Logo";
import { Mascot } from "../components/Mascot";
import { Reveal } from "../components/ui";
import { DOCS_URL } from "../lib/api";
import { useAuth } from "../lib/auth";
import { prefersReducedMotion } from "../lib/theme";
import { useApi } from "../lib/useApi";

const FACTS = [
  { value: "9", label: "PIN codes probed per listing" },
  { value: "30 min", label: "Seller offer sweep cadence" },
  { value: "3", label: "Alert types: drop, Buy Box, stock" },
  { value: "REST", label: "Every metric exposed via API" },
];

const FEATURES = [
  {
    icon: LineIcon,
    title: "Price history per seller",
    text: "Every snapshot is stored as a time series, so you can see who moved first, by how much and when — over 7, 30 or 90 days.",
    wide: true,
    art: "chart",
  },
  {
    icon: Crown,
    title: "Buy Box ownership",
    text: "Know who holds the Buy Box right now and how often it changes hands.",
    art: "crown",
  },
  {
    icon: MapPin,
    title: "Location-aware offers",
    text: "Offers are sampled across Tamil Nadu and metro PIN codes to surface regional price drift.",
    art: "map",
  },
  {
    icon: Store,
    title: "Seller radar",
    text: "Every competing seller, their FBA status, best price and how many of your SKUs they touch.",
  },
  {
    icon: BellRing,
    title: "Alerts that matter",
    text: "Per-ASIN thresholds, email or webhook delivery, acknowledgement workflow and CSV export.",
  },
  {
    icon: Braces,
    title: "Open API",
    text: "FastAPI with OpenAPI docs. Pipe the same data into BI tools or your ERP.",
  },
];

const STEPS = [
  { icon: ScanSearch, title: "Discover", text: "Search crawls find every listing for the bearing models you track." },
  { icon: Radar, title: "Monitor", text: "Product pages and seller offers are refreshed on a schedule via Celery." },
  { icon: Zap, title: "Detect", text: "The alert engine compares Buy Box observations against your thresholds." },
  { icon: ShieldCheck, title: "Act", text: "Get notified, review the evidence, and reprice with confidence." },
];

const SIGNALS = [
  { label: "Buy Box shift detected", tone: "accent", style: { top: "12%", left: "-6%" }, depth: 1.6 },
  { label: "New seller on listing", tone: "info", style: { top: "30%", right: "-10%" }, depth: 2.4 },
  { label: "Competitor undercut", tone: "danger", style: { bottom: "22%", left: "-12%" }, depth: 2 },
  { label: "Back in stock", tone: "success", style: { bottom: "6%", right: "-2%" }, depth: 1.2 },
];

function useLandingMotion(rootRef) {
  useEffect(() => {
    const root = rootRef.current;
    if (!root || prefersReducedMotion()) return undefined;
    let frame = 0;
    const onScroll = () => {
      cancelAnimationFrame(frame);
      frame = requestAnimationFrame(() => root.style.setProperty("--scroll", String(window.scrollY)));
    };
    const onPointer = (event) => {
      const x = event.clientX / window.innerWidth - 0.5;
      const y = event.clientY / window.innerHeight - 0.5;
      root.style.setProperty("--px", x.toFixed(3));
      root.style.setProperty("--py", y.toFixed(3));
    };
    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("pointermove", onPointer, { passive: true });
    return () => {
      cancelAnimationFrame(frame);
      window.removeEventListener("scroll", onScroll);
      window.removeEventListener("pointermove", onPointer);
    };
  }, [rootRef]);
}

function StatusPill() {
  const { data, error, loading } = useApi("/health");
  const status = error ? "down" : data?.status;
  const text = loading
    ? "Checking system status…"
    : status === "ok"
      ? `All systems live · API v${data.version}`
      : status === "degraded"
        ? "API live · task queue offline"
        : "API offline — start the backend";
  const tone = status === "ok" ? "" : status === "degraded" ? "is-warning" : loading ? "is-unknown" : "is-down";
  return (
    <span className="hero-pill">
      <span className={`live-dot ${tone}`} />
      {text}
    </span>
  );
}

function BearingVisual() {
  const balls = Array.from({ length: 12 }, (_, index) => {
    const angle = (index / 12) * Math.PI * 2;
    return { cx: 200 + Math.cos(angle) * 118, cy: 200 + Math.sin(angle) * 118 };
  });
  return (
    <div className="hero-visual" aria-hidden="true">
      <div className="hero-orbit hero-orbit-1" />
      <div className="hero-orbit hero-orbit-2" />
      <div className="hero-bearing">
        <svg viewBox="0 0 400 400">
          <defs>
            <linearGradient id="race" x1="0" y1="0" x2="1" y2="1">
              <stop offset="0%" stopColor="var(--hero-steel-hi)" />
              <stop offset="55%" stopColor="var(--hero-steel)" />
              <stop offset="100%" stopColor="var(--hero-steel-lo)" />
            </linearGradient>
            <radialGradient id="ball" cx="35%" cy="30%" r="75%">
              <stop offset="0%" stopColor="#ffffff" />
              <stop offset="45%" stopColor="var(--hero-steel-hi)" />
              <stop offset="100%" stopColor="var(--hero-steel-lo)" />
            </radialGradient>
            <radialGradient id="core-glow" cx="50%" cy="50%" r="50%">
              <stop offset="0%" stopColor="var(--accent-fill)" stopOpacity="0.55" />
              <stop offset="100%" stopColor="var(--accent-fill)" stopOpacity="0" />
            </radialGradient>
          </defs>
          <circle cx="200" cy="200" r="170" fill="none" stroke="url(#race)" strokeWidth="34" />
          <circle cx="200" cy="200" r="186" fill="none" stroke="var(--hero-edge)" strokeWidth="1" />
          <circle cx="200" cy="200" r="118" fill="none" stroke="var(--hero-groove)" strokeWidth="40" />
          <g className="hero-cage">
            <circle cx="200" cy="200" r="118" fill="none" stroke="var(--hero-cage)" strokeWidth="6" strokeDasharray="4 57.8" />
            {balls.map((ball, index) => (
              <circle key={index} cx={ball.cx} cy={ball.cy} r="17" fill="url(#ball)" />
            ))}
          </g>
          <g className="hero-inner">
            <circle cx="200" cy="200" r="76" fill="none" stroke="url(#race)" strokeWidth="26" />
            <circle cx="200" cy="200" r="62" fill="none" stroke="var(--hero-edge)" strokeWidth="1" />
            <path d="M200 124 a76 76 0 0 1 64 36" fill="none" stroke="#fff" strokeOpacity="0.4" strokeWidth="3" strokeLinecap="round" />
          </g>
          <circle cx="200" cy="200" r="60" fill="url(#core-glow)" className="hero-core-glow" />
          <circle cx="200" cy="200" r="9" fill="var(--accent-fill)" className="hero-core" />
        </svg>
        <svg className="hero-pulse-line" viewBox="0 0 400 400">
          <path d="M70 200 H150 l12 -26 l16 52 l14 -40 l10 14 H330" fill="none" stroke="var(--accent-fill)" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" pathLength="1" />
        </svg>
      </div>
      {SIGNALS.map((signal, index) => (
        <div
          key={signal.label}
          className={`signal-card signal-${signal.tone}`}
          style={{ ...signal.style, "--depth": signal.depth, animationDelay: `${600 + index * 160}ms, ${index * -1.3}s` }}
        >
          <span className="signal-dot" />
          {signal.label}
        </div>
      ))}
    </div>
  );
}

function FeatureArt({ kind }) {
  if (kind === "chart") {
    return (
      <svg className="feature-art feature-art-chart" viewBox="0 0 320 110" aria-hidden="true" preserveAspectRatio="none">
        <path className="art-line art-line-1" pathLength="1" d="M0 80 C30 74 46 40 80 46 S130 86 162 70 S214 22 248 30 S296 52 320 40" />
        <path className="art-line art-line-2" pathLength="1" d="M0 92 C40 90 60 70 96 74 S150 96 186 84 S236 58 268 62 S304 74 320 66" />
        <path className="art-line art-line-3" pathLength="1" d="M0 60 C34 66 64 82 100 72 S150 40 190 48 S240 80 276 72 S306 58 320 60" />
      </svg>
    );
  }
  if (kind === "crown") {
    return (
      <div className="feature-art feature-art-share" aria-hidden="true">
        {[64, 22, 14].map((width, index) => (
          <span key={index} style={{ "--w": `${width}%`, animationDelay: `${index * 120}ms` }} />
        ))}
      </div>
    );
  }
  if (kind === "map") {
    return (
      <div className="feature-art feature-art-pins" aria-hidden="true">
        {[
          [18, 30],
          [42, 62],
          [64, 26],
          [78, 58],
          [30, 74],
        ].map(([x, y], index) => (
          <span key={index} style={{ left: `${x}%`, top: `${y}%`, animationDelay: `${index * 0.5}s` }} />
        ))}
      </div>
    );
  }
  return null;
}

function HowItWorks() {
  const ref = useRef(null);
  useEffect(() => {
    const node = ref.current;
    if (!node) return undefined;
    if (prefersReducedMotion()) {
      node.style.setProperty("--progress", "1");
      return undefined;
    }
    let frame = 0;
    const update = () => {
      const rect = node.getBoundingClientRect();
      const viewport = window.innerHeight;
      const progress = Math.min(1, Math.max(0, (viewport * 0.75 - rect.top) / (rect.height + viewport * 0.1)));
      node.style.setProperty("--progress", progress.toFixed(3));
    };
    const onScroll = () => {
      cancelAnimationFrame(frame);
      frame = requestAnimationFrame(update);
    };
    update();
    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("resize", onScroll);
    return () => {
      cancelAnimationFrame(frame);
      window.removeEventListener("scroll", onScroll);
      window.removeEventListener("resize", onScroll);
    };
  }, []);

  return (
    <section className="landing-section" id="how">
      <Reveal className="section-head">
        <span className="section-eyebrow">How it works</span>
        <h2>
          From shelf to signal in <em>four</em> steps.
        </h2>
      </Reveal>
      <div className="steps" ref={ref}>
        <div className="steps-track" aria-hidden="true">
          <span />
        </div>
        {STEPS.map((step, index) => (
          <Reveal key={step.title} className="step" delay={index * 90}>
            <span className="step-icon">
              <step.icon aria-hidden="true" />
            </span>
            <span className="step-index num">0{index + 1}</span>
            <h3>{step.title}</h3>
            <p>{step.text}</p>
          </Reveal>
        ))}
      </div>
    </section>
  );
}

export default function Landing() {
  const rootRef = useRef(null);
  const { isAuthenticated } = useAuth();
  useLandingMotion(rootRef);

  useEffect(() => {
    document.title = "BearingPulse — Amazon India price intelligence for bearing distributors";
  }, []);

  const primaryCta = isAuthenticated ? { to: "/app", label: "Open dashboard" } : { to: "/login", label: "Sign in to dashboard" };

  return (
    <div className="landing" ref={rootRef}>
      <div className="landing-bg" aria-hidden="true">
        <div className="landing-grid" />
        <div className="blob blob-1" />
        <div className="blob blob-2" />
        <div className="blob blob-3" />
      </div>

      <header className="landing-nav">
        <Link to="/" aria-label="BearingPulse home">
          <Logo />
        </Link>
        <nav className="landing-links" aria-label="Sections">
          <a href="#features">Features</a>
          <a href="#how">How it works</a>
          {DOCS_URL && (
            <a href={DOCS_URL} target="_blank" rel="noreferrer">
              API
            </a>
          )}
        </nav>
        <Link to={primaryCta.to} className="btn btn-sm landing-nav-cta">
          {isAuthenticated ? "Dashboard" : "Sign in"}
        </Link>
      </header>

      <main>
        <section className="hero">
          <div className="hero-copy">
            <StatusPill />
            <h1>
              Know every price move <em>before</em> your competitors do.
            </h1>
            <p className="hero-sub">
              BearingPulse watches Amazon India listings for your bearing catalogue — tracking seller offers, Buy Box
              ownership and stock across PIN codes, and alerting you the moment a rival undercuts.
            </p>
            <div className="hero-ctas">
              <Link to={primaryCta.to} className="btn btn-primary btn-lg btn-arrow">
                {primaryCta.label}
                <ArrowRight aria-hidden="true" />
              </Link>
              <a href="#features" className="btn btn-lg btn-ghost">
                See what it tracks
              </a>
            </div>
          </div>
          <BearingVisual />
        </section>

        <Reveal as="section" className="facts" aria-label="Capabilities">
          {FACTS.map((fact) => (
            <div className="fact" key={fact.label}>
              <strong className="num">{fact.value}</strong>
              <span>{fact.label}</span>
            </div>
          ))}
        </Reveal>

        <section className="landing-section" id="features">
          <Reveal className="section-head">
            <span className="section-eyebrow">Features</span>
            <h2>
              Built for the way distributors <em>actually</em> compete.
            </h2>
            <p>One pipeline from crawler to dashboard, with nothing hidden behind a spreadsheet.</p>
          </Reveal>
          <div className="bento">
            {FEATURES.map((feature, index) => (
              <Reveal key={feature.title} className={`bento-card ${feature.wide ? "is-wide" : ""}`} delay={(index % 3) * 80}>
                <span className="bento-icon">
                  <feature.icon aria-hidden="true" />
                </span>
                <h3>{feature.title}</h3>
                <p>{feature.text}</p>
                {feature.art && <FeatureArt kind={feature.art} />}
              </Reveal>
            ))}
          </div>
        </section>

        <HowItWorks />

        <section className="landing-section meet">
          <div className="meet-card">
            <div className="meet-orbit" aria-hidden="true">
              <LogoMark size={340} spinning />
            </div>
            <Reveal className="meet-mascot">
              <Mascot mood="happy" size={180} title="Pip, the BearingPulse mascot" />
            </Reveal>
            <Reveal className="meet-copy" delay={120}>
              <span className="section-eyebrow">Meet Pip</span>
              <h2>
                It keeps an eye on the shelf <em>while you sleep.</em>
              </h2>
              <p>
                Scheduled crawls run every few hours, offer sweeps every thirty minutes, and alert checks every fifteen.
                Wake up to evidence, not surprises.
              </p>
              <Link to={primaryCta.to} className="btn btn-primary btn-arrow">
                {primaryCta.label}
                <ArrowRight aria-hidden="true" />
              </Link>
            </Reveal>
          </div>
        </section>
      </main>

      <footer className="landing-footer">
        <Logo />
        <span className="subtle">Real-time price intelligence for bearing distributors on Amazon India.</span>
        <div className="row">
          {DOCS_URL && (
            <a className="link" href={DOCS_URL} target="_blank" rel="noreferrer">
              API docs
            </a>
          )}
          <Link className="link" to="/login">
            Sign in
          </Link>
        </div>
      </footer>
    </div>
  );
}
