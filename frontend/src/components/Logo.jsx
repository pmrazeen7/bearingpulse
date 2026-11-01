import React from "react";

const BALLS = Array.from({ length: 8 }, (_, index) => {
  const angle = (index / 8) * Math.PI * 2;
  return { cx: 16 + Math.cos(angle) * 10.2, cy: 16 + Math.sin(angle) * 10.2 };
});

// A deep-groove bearing seen face-on: outer race, rolling elements, inner race.
export function LogoMark({ size = 28, spinning = false, className = "" }) {
  return (
    <svg
      className={`logo-mark ${spinning ? "is-spinning" : ""} ${className}`}
      width={size}
      height={size}
      viewBox="0 0 32 32"
      fill="none"
      aria-hidden="true"
    >
      <circle cx="16" cy="16" r="14.4" stroke="currentColor" strokeOpacity="0.9" strokeWidth="2.2" />
      <g className="logo-cage">
        {BALLS.map((ball, index) => (
          <circle key={index} cx={ball.cx} cy={ball.cy} r="2.05" fill="currentColor" />
        ))}
      </g>
      <circle cx="16" cy="16" r="6.1" stroke="currentColor" strokeOpacity="0.9" strokeWidth="2.2" />
      <circle className="logo-pulse" cx="16" cy="16" r="2.1" fill="var(--accent-fill)" />
    </svg>
  );
}

export function Logo({ compact = false, spinning = false }) {
  return (
    <span className={`logo ${compact ? "logo-compact" : ""}`}>
      <LogoMark spinning={spinning} />
      {!compact && (
        <span className="logo-word">
          Bearing<span>Pulse</span>
        </span>
      )}
    </span>
  );
}
