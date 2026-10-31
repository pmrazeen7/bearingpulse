import React, { useEffect, useRef, useState } from "react";
import { AlertTriangle, ChevronLeft, ChevronRight, Info, RotateCw, Search, X } from "lucide-react";

import { prefersReducedMotion } from "../lib/theme";
import { Mascot } from "./Mascot";

export function Button({ variant = "secondary", size, icon: Icon, iconRight: IconRight, loading, className = "", children, ...props }) {
  const classes = ["btn", variant !== "secondary" && `btn-${variant}`, size && `btn-${size}`, !children && "btn-icon", className]
    .filter(Boolean)
    .join(" ");
  return (
    <button type="button" className={classes} disabled={loading || props.disabled} {...props}>
      {loading ? <span className="spinner" aria-hidden="true" /> : Icon ? <Icon aria-hidden="true" /> : null}
      {children}
      {IconRight && <IconRight aria-hidden="true" />}
    </button>
  );
}

export function Badge({ tone, dot, children, className = "" }) {
  return <span className={`badge ${tone ? `badge-${tone}` : ""} ${dot ? "badge-dot" : ""} ${className}`}>{children}</span>;
}

export function Card({ title, subtitle, actions, children, className = "", bodyClassName = "", flush = false }) {
  return (
    <section className={`card ${className}`}>
      {(title || actions) && (
        <header className="card-header">
          <div>
            {title && <h2 className="card-title">{title}</h2>}
            {subtitle && <p className="card-subtitle">{subtitle}</p>}
          </div>
          {actions && <div className="card-actions">{actions}</div>}
        </header>
      )}
      <div className={flush ? bodyClassName : `card-body ${bodyClassName}`}>{children}</div>
    </section>
  );
}

export function Skeleton({ width = "100%", height = 14, radius, className = "" }) {
  return <span className={`skeleton ${className}`} style={{ width, height, borderRadius: radius }} aria-hidden="true" />;
}

export function SkeletonRows({ rows = 6, columns = 5 }) {
  return (
    <div className="skeleton-table" role="status" aria-label="Loading">
      {Array.from({ length: rows }, (_, row) => (
        <div className="skeleton-row" key={row} style={{ animationDelay: `${row * 60}ms` }}>
          {Array.from({ length: columns }, (_, col) => (
            <Skeleton key={col} width={col === 1 ? "38%" : `${14 + ((row + col) % 3) * 4}%`} height={12} />
          ))}
        </div>
      ))}
    </div>
  );
}

export function EmptyState({ mood = "sleepy", title, children, actions, compact = false }) {
  return (
    <div className={`empty ${compact ? "empty-compact" : ""}`}>
      <Mascot mood={mood} size={compact ? 84 : 112} />
      <h3 className="empty-title">{title}</h3>
      {children && <p className="empty-text">{children}</p>}
      {actions && <div className="empty-actions">{actions}</div>}
    </div>
  );
}

export function ErrorState({ error, onRetry, compact }) {
  const offline = error?.status === 0;
  return (
    <EmptyState
      mood="worried"
      compact={compact}
      title={offline ? "The API is unreachable" : "Something went wrong"}
      actions={onRetry && <Button icon={RotateCw} onClick={onRetry}>Try again</Button>}
    >
      {error?.message || "An unexpected error occurred."}
    </EmptyState>
  );
}

export function Notice({ tone = "info", icon: Icon = tone === "info" ? Info : AlertTriangle, children }) {
  return (
    <div className={`notice notice-${tone}`} role={tone === "danger" ? "alert" : "status"}>
      <Icon aria-hidden="true" />
      <div>{children}</div>
    </div>
  );
}

export function SearchInput({ value, onChange, placeholder = "Search…", inputRef, shortcut, ...props }) {
  return (
    <label className="input-group">
      <Search aria-hidden="true" />
      <span className="sr-only">{placeholder}</span>
      <input
        ref={inputRef}
        className="input"
        type="search"
        value={value}
        placeholder={placeholder}
        onChange={(event) => onChange(event.target.value)}
        {...props}
      />
      {shortcut && !value && <kbd>{shortcut}</kbd>}
    </label>
  );
}

export function Segmented({ options, value, onChange, label }) {
  return (
    <div className="segmented" role="group" aria-label={label}>
      {options.map((option) => (
        <button key={option.value} type="button" aria-pressed={value === option.value} onClick={() => onChange(option.value)}>
          {option.label}
        </button>
      ))}
    </div>
  );
}

export function Pagination({ page, pageSize, total, onPage }) {
  if (total === null || total === undefined) return null;
  const pages = Math.max(1, Math.ceil(total / pageSize));
  const from = total === 0 ? 0 : page * pageSize + 1;
  const to = Math.min(total, (page + 1) * pageSize);
  return (
    <div className="pagination">
      <span>
        <span className="num">{from}</span>–<span className="num">{to}</span> of <span className="num">{total}</span>
      </span>
      <div className="pagination-controls">
        <Button size="sm" icon={ChevronLeft} aria-label="Previous page" disabled={page === 0} onClick={() => onPage(page - 1)} />
        <span className="num">
          {page + 1} / {pages}
        </span>
        <Button
          size="sm"
          icon={ChevronRight}
          aria-label="Next page"
          disabled={page + 1 >= pages}
          onClick={() => onPage(page + 1)}
        />
      </div>
    </div>
  );
}

export function Field({ label, hint, error, children, htmlFor }) {
  return (
    <div className="field">
      {label && (
        <label className="field-label" htmlFor={htmlFor}>
          {label}
        </label>
      )}
      {children}
      {error ? <span className="field-error">{error}</span> : hint ? <span className="field-hint">{hint}</span> : null}
    </div>
  );
}

// Counts up to the target value when it first renders or changes.
export function AnimatedNumber({ value, format = (v) => Math.round(v).toLocaleString("en-IN"), duration = 900 }) {
  const [display, setDisplay] = useState(() => (prefersReducedMotion() ? value : 0));
  const fromRef = useRef(0);

  useEffect(() => {
    if (value === null || value === undefined || Number.isNaN(Number(value))) return undefined;
    if (prefersReducedMotion()) {
      setDisplay(value);
      return undefined;
    }
    const from = fromRef.current;
    const start = performance.now();
    let frame;
    const tick = (now) => {
      const progress = Math.min(1, (now - start) / duration);
      const eased = 1 - Math.pow(1 - progress, 3);
      setDisplay(from + (value - from) * eased);
      if (progress < 1) frame = requestAnimationFrame(tick);
      else fromRef.current = value;
    };
    frame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frame);
  }, [value, duration]);

  if (value === null || value === undefined) return "—";
  return format(display);
}

// Adds .is-visible when the element scrolls into view.
export function Reveal({ as: Tag = "div", delay = 0, className = "", children, ...props }) {
  const ref = useRef(null);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const node = ref.current;
    if (!node) return undefined;
    if (!("IntersectionObserver" in window) || prefersReducedMotion()) {
      setVisible(true);
      return undefined;
    }
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setVisible(true);
          observer.disconnect();
        }
      },
      { rootMargin: "0px 0px -10% 0px", threshold: 0.12 },
    );
    observer.observe(node);
    return () => observer.disconnect();
  }, []);

  return (
    <Tag
      ref={ref}
      className={`reveal ${visible ? "is-visible" : ""} ${className}`}
      style={{ "--reveal-delay": `${delay}ms` }}
      {...props}
    >
      {children}
    </Tag>
  );
}

export function CloseButton({ onClick, label = "Close" }) {
  return <Button variant="ghost" size="sm" icon={X} aria-label={label} onClick={onClick} />;
}
