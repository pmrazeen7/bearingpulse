import React from "react";

import { AnimatedNumber, Skeleton } from "./ui";

const TONES = {
  accent: { color: "var(--accent)", tint: "var(--accent-soft)" },
  info: { color: "var(--info)", tint: "var(--info-soft)" },
  success: { color: "var(--success)", tint: "var(--success-soft)" },
  danger: { color: "var(--danger)", tint: "var(--danger-soft)" },
  warning: { color: "var(--warning)", tint: "var(--warning-soft)" },
};

export function StatCard({ label, value, icon: Icon, tone = "accent", foot, format, loading, children }) {
  const palette = TONES[tone];
  return (
    <div
      className="card stat card-interactive"
      style={{ "--stat-color": palette.color, "--stat-tint": palette.tint, "--stat-glow": palette.tint }}
    >
      <div className="stat-top">
        <span>{label}</span>
        {Icon && (
          <span className="stat-icon">
            <Icon aria-hidden="true" />
          </span>
        )}
      </div>
      <div className={`stat-value ${typeof value === "string" && value.length > 11 ? "is-text" : ""}`}>
        {loading ? <Skeleton width="55%" height={26} /> : typeof value === "number" ? <AnimatedNumber value={value} format={format} /> : value}
      </div>
      <div className="stat-foot">{loading ? <Skeleton width="70%" height={11} /> : foot}</div>
      {children}
    </div>
  );
}

export function PageHeader({ title, subtitle, actions, eyebrow }) {
  return (
    <div className="page-header">
      <div>
        {eyebrow && <div className="page-eyebrow">{eyebrow}</div>}
        <h2 className="page-title">{title}</h2>
        {subtitle && <p className="page-sub">{subtitle}</p>}
      </div>
      {actions && <div className="page-actions">{actions}</div>}
    </div>
  );
}
