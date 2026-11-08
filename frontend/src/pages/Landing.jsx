import React, { useEffect } from "react";
import { Link } from "react-router-dom";

import { Logo } from "../components/Logo";
import { DOCS_URL } from "../lib/api";
import { useAuth } from "../lib/auth";
import { useApi } from "../lib/useApi";

const RECORDS = [
  ["Price and MRP", "Latest price and discount for each product, with history over 7, 30 or 90 days."],
  ["Buy Box seller", "Who holds the Buy Box now, and how often it has changed hands."],
  ["Stock", "In stock, low stock or out of stock at each reading."],
  ["Sellers", "Every seller seen on your listings, whether Amazon fulfils for them, and their best price."],
  ["Alerts", "A price drop past your threshold, a Buy Box change, or a product going out of stock. Email or webhook delivery is optional."],
  ["Data access", "A REST API with OpenAPI docs, and CSV export for alerts."],
];

const STEPS = [
  ["Find listings", "Search crawls look up the bearing models you track, such as SKF 6205, and add the listings they find."],
  ["Read each page", "A Celery worker opens every tracked product page every two hours and records price, MRP, stock and the Buy Box seller."],
  ["Keep every reading", "Each reading is stored as a new row in PostgreSQL. Nothing is overwritten, so the history stays complete."],
  ["Check for changes", "Every 15 minutes the alert check compares the two latest Buy Box readings with your thresholds."],
];

const LIMITS = [
  "Amazon changes its pages and can block crawlers, so a refresh may skip some pages.",
  "Offers from every seller are not collected yet. The Buy Box seller is.",
  "Sign-in uses one shared API key. There are no user accounts.",
];

function ApiStatus() {
  const { data, error, loading } = useApi("/health");
  let text = "Checking the API";
  if (!loading) {
    if (error) text = "API not reachable";
    else if (data?.status === "ok") text = `API running, version ${data.version}`;
    else if (data?.status === "degraded") text = "API running, task queue offline";
    else text = "API reports a problem";
  }
  const tone = loading ? "is-unknown" : error ? "is-down" : data?.status === "ok" ? "" : "is-warning";
  return (
    <p className="home-status">
      <span className={`live-dot ${tone}`} aria-hidden="true" />
      {text}
    </p>
  );
}

export default function Landing() {
  const { isAuthenticated } = useAuth();

  useEffect(() => {
    document.title = "BearingPulse · Amazon India price tracking for bearings";
  }, []);

  return (
    <div className="home">
      <header className="home-nav">
        <Link to="/" aria-label="BearingPulse home">
          <Logo />
        </Link>
        <nav aria-label="Sections">
          <a href="#records">What it records</a>
          <a href="#how">How it works</a>
          <Link to={isAuthenticated ? "/app" : "/login"} className="btn btn-sm">
            {isAuthenticated ? "Dashboard" : "Sign in"}
          </Link>
        </nav>
      </header>

      <main>
        <section className="home-hero">
          <h1>Track competitor prices and Buy Box changes on Amazon India</h1>
          <p>
            BearingPulse reads the product pages of the bearings you sell, keeps every price, stock and Buy Box reading, and
            alerts you when a competitor undercuts you.
          </p>
          <div className="home-actions">
            <Link to={isAuthenticated ? "/app" : "/login"} className="btn btn-primary btn-lg">
              {isAuthenticated ? "Open the dashboard" : "Sign in"}
            </Link>
            {DOCS_URL && (
              <a className="btn btn-lg" href={DOCS_URL} target="_blank" rel="noreferrer">
                API docs
              </a>
            )}
          </div>
          <ApiStatus />
        </section>

        <section className="home-section" id="records">
          <h2>What it records</h2>
          <dl className="records">
            {RECORDS.map(([term, text]) => (
              <div className="records-row" key={term}>
                <dt>{term}</dt>
                <dd>{text}</dd>
              </div>
            ))}
          </dl>
        </section>

        <section className="home-section" id="how">
          <h2>How it works</h2>
          <ol className="steps">
            {STEPS.map(([title, text], index) => (
              <li key={title}>
                <span className="steps-n num">{index + 1}</span>
                <div>
                  <h3>{title}</h3>
                  <p>{text}</p>
                </div>
              </li>
            ))}
          </ol>
        </section>

        <section className="home-section">
          <h2>Known limits</h2>
          <ul className="limits">
            {LIMITS.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </section>
      </main>

      <footer className="home-footer">
        <span>BearingPulse</span>
        <span className="subtle">Built with FastAPI, Scrapy, Celery, PostgreSQL and React.</span>
      </footer>
    </div>
  );
}
