import React from "react";
import { AlertTriangle, ChevronLeft, ChevronRight, Info, RotateCw, Search, X } from "lucide-react";
import { Link } from "react-router-dom";


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

// The focusable, screen-reader-visible way into a table row. The row itself is also clickable for
// pointer users, so stop the click here to avoid navigating twice.
export function RowLink({ to, children, className = "", ...props }) {
  return (
    <Link to={to} className={`row-link ${className}`} onClick={(event) => event.stopPropagation()} {...props}>
      {children}
    </Link>
  );
}

// Where the latest price sits between the lowest and highest price ever seen.
export function RangeBar({ value, min, max, format }) {
  if (value == null || min == null || max == null) return <span className="subtle">—</span>;
  const span = max - min;
  const position = span > 0 ? Math.min(100, Math.max(0, ((value - min) / span) * 100)) : 50;
  const where = span <= 0 ? "unchanged" : position <= 25 ? "near its lowest" : position >= 75 ? "near its highest" : "mid-range";
  return (
    <div className="range">
      <div className="range-text num nowrap">
        {format(min)} – {format(max)}
      </div>
      <div className="range-bar" role="img" aria-label={`Latest price is ${where}: ${format(value)} between ${format(min)} and ${format(max)}`}>
        <span style={{ left: `${position}%` }} />
      </div>
    </div>
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

// `mood` is accepted for older call sites and ignored.
export function EmptyState({ title, children, actions, compact = false }) {
  return (
    <div className={`empty ${compact ? "empty-compact" : ""}`}>
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

// Numbers render as they are. (Kept as a component so callers can pass a formatter.)
export function AnimatedNumber({ value, format = (v) => Math.round(v).toLocaleString("en-IN") }) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "—";
  return format(Number(value));
}

export function CloseButton({ onClick, label = "Close" }) {
  return <Button variant="ghost" size="sm" icon={X} aria-label={label} onClick={onClick} />;
}
