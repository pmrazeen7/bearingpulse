import React, { Suspense, useEffect, useRef, useState } from "react";
import { NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";
import {
  BarChart3,
  Bell,
  BookOpen,
  ChevronsLeft,
  LayoutDashboard,
  LogOut,
  Menu,
  Moon,
  Package,
  Play,
  Radar,
  Search,
  Settings,
  Store,
  Sun,
  X,
} from "lucide-react";

import { Dropdown, DropdownItem } from "../components/Dropdown";
import { Logo } from "../components/Logo";
import { useToast } from "../components/Toast";
import { Button, Skeleton } from "../components/ui";
import { api, DOCS_URL } from "../lib/api";
import { useAuth } from "../lib/auth";
import { useJobs } from "../lib/jobs";
import JobTray from "../components/JobTray";
import { formatDateTime } from "../lib/format";
import { useTheme } from "../lib/theme";
import { useApi } from "../lib/useApi";

const NAV = [
  { to: "/app", label: "Overview", icon: LayoutDashboard, end: true },
  { to: "/app/products", label: "Products", icon: Package },
  { to: "/app/sellers", label: "Sellers", icon: Store },
  { to: "/app/alerts", label: "Alerts", icon: Bell, badge: "alerts" },
  { to: "/app/analytics", label: "Analytics", icon: BarChart3 },
  { to: "/app/settings", label: "Settings", icon: Settings },
];

const TITLES = [
  ["/app/products/", "Product"],
  ["/app/products", "Products"],
  ["/app/sellers/", "Seller"],
  ["/app/sellers", "Sellers"],
  ["/app/alerts", "Alerts"],
  ["/app/analytics", "Analytics"],
  ["/app/settings", "Settings"],
  ["/app", "Overview"],
];

export const CRAWL_JOBS = [
  { job: "search", label: "Discover products", hint: "Search crawl for configured queries" },
  { job: "asin-detail", label: "Refresh product pages", hint: "Price, MRP, stock and Buy Box" },
  { job: "seller-offers", label: "Sweep seller offers", hint: "All sellers across PIN codes" },
  { job: "alert-check", label: "Run alert check", hint: "Evaluate thresholds now" },
];

function readCollapsed() {
  try {
    return localStorage.getItem("bp.sidebar") === "collapsed";
  } catch {
    return false;
  }
}

function HealthIndicator() {
  const { data, error } = useApi("/health");
  const status = error ? "down" : data?.status;
  const tone = { ok: "", degraded: "is-warning", down: "is-down" }[status] ?? "is-unknown";
  const label = {
    ok: "All systems operational",
    degraded: "Redis unavailable — scheduling paused",
    down: "API or database unavailable",
  }[status] ?? "Checking status…";
  return (
    <span className="health" title={label}>
      <span className={`live-dot ${tone}`} />
      <span className="health-label">{status === "ok" ? "Live" : status === "degraded" ? "Degraded" : status === "down" ? "Offline" : "…"}</span>
    </span>
  );
}

export function useCrawl() {
  const toast = useToast();
  const { startJob } = useJobs();
  return async (job) => {
    const meta = CRAWL_JOBS.find((item) => item.job === job);
    try {
      if (job === "alert-check") {
        const result = await api.post("/alerts/check");
        toast.success("Alert check complete", result.created ? `${result.created} new alert(s) raised.` : "No new alerts.");
        return result;
      }
      const result = await api.post(`/crawl/${job}`);
      startJob({ taskId: result.task_id, job, label: meta.label });
      toast.info(`${meta.label} queued`, "Track its progress in the panel at the bottom of the page.");
      return result;
    } catch (error) {
      toast.error(`Could not start "${meta.label}"`, error.message);
      return null;
    }
  };
}

export default function AppLayout() {
  const [collapsed, setCollapsed] = useState(readCollapsed);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [query, setQuery] = useState("");
  const searchRef = useRef(null);
  const { pathname } = useLocation();
  const navigate = useNavigate();
  const { signOut } = useAuth();
  const { theme, toggle } = useTheme();
  const crawl = useCrawl();
  const { data: overview } = useApi("/analytics/overview");

  const title = TITLES.find(([prefix]) => pathname.startsWith(prefix))?.[1] ?? "BearingPulse";

  useEffect(() => {
    try {
      localStorage.setItem("bp.sidebar", collapsed ? "collapsed" : "expanded");
    } catch {
      // ignore
    }
  }, [collapsed]);

  useEffect(() => setMobileOpen(false), [pathname]);

  useEffect(() => {
    document.title = `${title} · BearingPulse`;
  }, [title]);

  useEffect(() => {
    const onKey = (event) => {
      if (event.key === "/" && !["INPUT", "TEXTAREA", "SELECT"].includes(document.activeElement?.tagName)) {
        event.preventDefault();
        searchRef.current?.focus();
      }
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, []);

  const submitSearch = (event) => {
    event.preventDefault();
    const term = query.trim();
    navigate(term ? `/app/products?q=${encodeURIComponent(term)}` : "/app/products");
    setQuery("");
    searchRef.current?.blur();
  };

  const badges = { alerts: overview?.open_alert_count };

  return (
    <div className={`shell ${collapsed ? "is-collapsed" : ""} ${mobileOpen ? "is-mobile-open" : ""}`}>
      <a href="#main" className="skip-link">
        Skip to content
      </a>
      <aside className="sidebar" aria-label="Primary">
        <div className="sidebar-head">
          <NavLink to="/" className="sidebar-brand" aria-label="BearingPulse home">
            <Logo compact={collapsed} />
          </NavLink>
          <Button variant="ghost" size="sm" icon={X} className="sidebar-close" aria-label="Close menu" onClick={() => setMobileOpen(false)} />
        </div>

        <nav className="sidebar-nav">
          <span className="sidebar-section">Workspace</span>
          {NAV.map((item) => (
            <NavLink key={item.to} to={item.to} end={item.end} className="nav-item" title={collapsed ? item.label : undefined}>
              <item.icon aria-hidden="true" />
              <span className="nav-label">{item.label}</span>
              {item.badge && badges[item.badge] > 0 && <span className="nav-badge num">{badges[item.badge]}</span>}
            </NavLink>
          ))}
        </nav>

        <div className="sidebar-foot">
          <div className="sidebar-card">
            <div className="sidebar-card-row">
              <Radar aria-hidden="true" />
              <span className="nav-label">Last crawl</span>
            </div>
            <div className="sidebar-card-value nav-label">
              {overview ? (
                overview.last_scraped_at ? formatDateTime(overview.last_scraped_at) : "No snapshots yet"
              ) : (
                <Skeleton width={110} height={12} />
              )}
            </div>
          </div>
          {DOCS_URL && (
            <a className="nav-item" href={DOCS_URL} target="_blank" rel="noreferrer" title={collapsed ? "API docs" : undefined}>
              <BookOpen aria-hidden="true" />
              <span className="nav-label">API docs</span>
            </a>
          )}
          <button type="button" className="nav-item" onClick={signOut} title={collapsed ? "Sign out" : undefined}>
            <LogOut aria-hidden="true" />
            <span className="nav-label">Sign out</span>
          </button>
          <button
            type="button"
            className="nav-item collapse-toggle"
            onClick={() => setCollapsed((value) => !value)}
            aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          >
            <ChevronsLeft aria-hidden="true" />
            <span className="nav-label">Collapse</span>
          </button>
        </div>
      </aside>
      <div className="sidebar-scrim" onClick={() => setMobileOpen(false)} aria-hidden="true" />

      <div className="main">
        <header className="topbar">
          <Button variant="ghost" icon={Menu} className="menu-toggle" aria-label="Open menu" onClick={() => setMobileOpen(true)} />
          <h1 className="topbar-title">{title}</h1>
          <form className="topbar-search" onSubmit={submitSearch} role="search">
            <label className="input-group">
              <Search aria-hidden="true" />
              <span className="sr-only">Search products</span>
              <input
                ref={searchRef}
                className="input"
                type="search"
                placeholder="Search ASIN or product…"
                value={query}
                onChange={(event) => setQuery(event.target.value)}
              />
              {!query && <kbd>/</kbd>}
            </label>
          </form>
          <div className="topbar-actions">
            <HealthIndicator />
            <Dropdown
              label="Run crawl"
              trigger={({ toggle: open, ...aria }) => (
                <Button variant="primary" size="sm" icon={Play} onClick={open} {...aria}>
                  <span className="hide-sm">Run</span>
                </Button>
              )}
            >
              {({ close }) => (
                <>
                  <div className="dropdown-label">Start a job</div>
                  {CRAWL_JOBS.map((item) => (
                    <DropdownItem key={item.job} icon={Play} hint={item.hint} close={close} onSelect={() => crawl(item.job)}>
                      {item.label}
                    </DropdownItem>
                  ))}
                </>
              )}
            </Dropdown>
            <Button
              variant="ghost"
              size="sm"
              icon={theme === "dark" ? Sun : Moon}
              aria-label={`Switch to ${theme === "dark" ? "light" : "dark"} theme`}
              onClick={toggle}
            />
          </div>
        </header>

        <main id="main" className="content">
          <div key={pathname} className="page-enter">
            <Suspense fallback={<PageFallback />}>
              <Outlet />
            </Suspense>
          </div>
        </main>
      </div>
      <JobTray />
    </div>
  );
}

export function PageFallback() {
  return (
    <div className="page" aria-busy="true">
      <div className="grid-stats">
        {Array.from({ length: 4 }, (_, index) => (
          <div className="card stat" key={index}>
            <Skeleton width="40%" />
            <Skeleton width="60%" height={26} className="mt-12" />
          </div>
        ))}
      </div>
      <div className="card card-pad">
        <Skeleton height={220} />
      </div>
    </div>
  );
}
