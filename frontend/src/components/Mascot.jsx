import React from "react";

// "Pip" — a ball bearing with a face. Moods map to product states:
// idle (default), happy (success), sleepy (nothing yet), worried (error),
// search (no results).
const MOUTHS = {
  idle: <path d="M52 73 Q60 79 68 73" />,
  happy: <path d="M50 71 Q60 83 70 71 Z" fill="var(--pip-mouth)" />,
  sleepy: <path d="M55 75 Q60 77 65 75" />,
  worried: <ellipse cx="60" cy="75" rx="4" ry="4.6" fill="var(--pip-mouth)" stroke="none" />,
  search: <path d="M54 74 Q60 77 66 74" />,
};

function Eyes({ mood }) {
  if (mood === "sleepy") {
    return (
      <g className="pip-eyes" strokeWidth="2.6">
        <path d="M45 61 Q50 64 55 61" />
        <path d="M65 61 Q70 64 75 61" />
      </g>
    );
  }
  const look = mood === "search" ? 3 : 0;
  return (
    <g className="pip-eyes pip-blink">
      <ellipse cx={50 + look} cy="60" rx="4.2" ry={mood === "worried" ? 5.4 : 5} fill="var(--pip-ink)" stroke="none" />
      <ellipse cx={70 + look} cy="60" rx="4.2" ry={mood === "worried" ? 5.4 : 5} fill="var(--pip-ink)" stroke="none" />
      <circle cx={51.4 + look} cy="58.2" r="1.4" fill="#fff" stroke="none" />
      <circle cx={71.4 + look} cy="58.2" r="1.4" fill="#fff" stroke="none" />
      {mood === "worried" && (
        <>
          <path d="M44 50 L54 52.5" strokeWidth="2.4" />
          <path d="M76 50 L66 52.5" strokeWidth="2.4" />
        </>
      )}
    </g>
  );
}

const BALLS = Array.from({ length: 10 }, (_, index) => {
  const angle = (index / 10) * Math.PI * 2 - Math.PI / 2;
  return { cx: 60 + Math.cos(angle) * 37, cy: 64 + Math.sin(angle) * 37 };
});

export function Mascot({ mood = "idle", size = 120, title, className = "" }) {
  return (
    <svg
      className={`pip pip-${mood} ${className}`}
      width={size}
      height={size}
      viewBox="0 0 120 128"
      role={title ? "img" : undefined}
      aria-hidden={title ? undefined : true}
      aria-label={title}
    >
      <defs>
        <radialGradient id="pip-face" cx="40%" cy="35%" r="70%">
          <stop offset="0%" stopColor="var(--pip-face-hi)" />
          <stop offset="100%" stopColor="var(--pip-face)" />
        </radialGradient>
        <linearGradient id="pip-race" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="var(--pip-race-hi)" />
          <stop offset="100%" stopColor="var(--pip-race)" />
        </linearGradient>
      </defs>
      <ellipse className="pip-shadow" cx="60" cy="121" rx="30" ry="4" fill="var(--pip-shadow)" />
      <g className="pip-body">
        <circle cx="60" cy="64" r="46" fill="url(#pip-race)" />
        <circle cx="60" cy="64" r="41" fill="var(--pip-groove)" />
        <g className="pip-cage">
          {BALLS.map((ball, index) => (
            <circle key={index} cx={ball.cx} cy={ball.cy} r="4.4" fill="var(--pip-ball)" />
          ))}
        </g>
        <circle cx="60" cy="64" r="31" fill="url(#pip-face)" />
        <path d="M40 46 A27 27 0 0 1 62 37" fill="none" stroke="#fff" strokeOpacity="0.35" strokeWidth="3" strokeLinecap="round" />
        <g fill="none" stroke="var(--pip-ink)" strokeWidth="2.6" strokeLinecap="round" strokeLinejoin="round">
          <Eyes mood={mood} />
          {MOUTHS[mood] || MOUTHS.idle}
        </g>
        {mood === "happy" && (
          <>
            <ellipse cx="43" cy="70" rx="4" ry="2.4" fill="var(--accent)" opacity="0.35" />
            <ellipse cx="77" cy="70" rx="4" ry="2.4" fill="var(--accent)" opacity="0.35" />
          </>
        )}
      </g>
      {mood === "sleepy" && (
        <g className="pip-zz" fill="var(--text-3)" fontFamily="var(--font-mono)" fontWeight="600">
          <text x="96" y="26" fontSize="13">z</text>
          <text x="106" y="14" fontSize="9">z</text>
        </g>
      )}
      {mood === "search" && (
        <g className="pip-lens" fill="none" stroke="var(--accent)" strokeWidth="4" strokeLinecap="round">
          <circle cx="94" cy="92" r="11" fill="var(--surface)" fillOpacity="0.6" />
          <path d="M102 100 L112 110" />
        </g>
      )}
      {mood === "worried" && <path className="pip-sweat" d="M92 40 q4 7 0 10 q-4 -3 0 -10 Z" fill="var(--info)" />}
    </svg>
  );
}
