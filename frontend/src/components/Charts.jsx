import React, { useId, useLayoutEffect, useMemo, useRef, useState } from "react";

export const SERIES_COLORS = ["var(--chart-1)", "var(--chart-2)", "var(--chart-3)", "var(--chart-4)", "var(--chart-5)", "var(--chart-6)"];

function useWidth(fallback = 600) {
  const ref = useRef(null);
  const [width, setWidth] = useState(fallback);
  useLayoutEffect(() => {
    const node = ref.current;
    if (!node) return undefined;
    setWidth(node.clientWidth || fallback);
    if (!("ResizeObserver" in window)) return undefined;
    const observer = new ResizeObserver(([entry]) => setWidth(Math.max(120, entry.contentRect.width)));
    observer.observe(node);
    return () => observer.disconnect();
  }, [fallback]);
  return [ref, width];
}

function niceTicks(min, max, count = 4) {
  if (min === max) {
    const pad = Math.abs(min) * 0.1 || 1;
    min -= pad;
    max += pad;
  }
  const span = max - min;
  const step = Math.pow(10, Math.floor(Math.log10(span / count)));
  const err = (count * step) / span;
  const mult = err <= 0.15 ? 10 : err <= 0.35 ? 5 : err <= 0.75 ? 2 : 1;
  const niceStep = step * mult;
  const start = Math.floor(min / niceStep) * niceStep;
  const end = Math.ceil(max / niceStep) * niceStep;
  const ticks = [];
  for (let value = start; value <= end + niceStep / 2; value += niceStep) ticks.push(Number(value.toFixed(10)));
  return ticks;
}

const PAD = { top: 12, right: 12, bottom: 26, left: 56 };

/**
 * Multi-series time chart.
 * series: [{ key, label, color, dashed, points: [{ x: Date, y: number, meta? }] }]
 */
export function LineChart({ series, height = 280, yFormat = (v) => v, xFormat, tooltipTitle, ariaLabel }) {
  const [ref, width] = useWidth();
  const uid = useId().replace(/[^a-zA-Z0-9_-]/g, "");
  const [hidden, setHidden] = useState(() => new Set());
  const [hover, setHover] = useState(null);
  const [focused, setFocused] = useState(null); // legend hover/focus dims the other series
  const visible = series.filter((item) => !hidden.has(item.key) && item.points.length);

  const geometry = useMemo(() => {
    const all = visible.flatMap((item) => item.points);
    if (!all.length) return null;
    const xs = all.map((point) => point.x.getTime());
    const ys = all.map((point) => point.y);
    let xMin = Math.min(...xs);
    let xMax = Math.max(...xs);
    if (xMin === xMax) {
      xMin -= 3600_000;
      xMax += 3600_000;
    }
    const ticks = niceTicks(Math.min(...ys), Math.max(...ys));
    const yMin = ticks[0];
    const yMax = ticks[ticks.length - 1];
    const innerW = Math.max(10, width - PAD.left - PAD.right);
    const innerH = height - PAD.top - PAD.bottom;
    const sx = (t) => PAD.left + ((t - xMin) / (xMax - xMin)) * innerW;
    const sy = (v) => PAD.top + innerH - ((v - yMin) / (yMax - yMin || 1)) * innerH;
    const xTickCount = Math.max(2, Math.min(6, Math.floor(innerW / 110)));
    const xTicks = Array.from({ length: xTickCount }, (_, i) => xMin + ((xMax - xMin) * i) / (xTickCount - 1));
    return { sx, sy, ticks, xTicks, xMin, xMax, innerW, innerH };
  }, [visible, width, height]);

  const onMove = (event) => {
    if (!geometry) return;
    const rect = event.currentTarget.getBoundingClientRect();
    const px = event.clientX - rect.left;
    const t = geometry.xMin + ((px - PAD.left) / geometry.innerW) * (geometry.xMax - geometry.xMin);
    const rows = visible
      .map((item) => {
        let best = item.points[0];
        for (const point of item.points) {
          if (Math.abs(point.x - t) < Math.abs(best.x - t)) best = point;
        }
        return { item, point: best };
      })
      .sort((a, b) => a.point.y - b.point.y);
    const anchor = rows.reduce((best, row) => (Math.abs(row.point.x - t) < Math.abs(best.point.x - t) ? row : best), rows[0]);
    setHover({ x: geometry.sx(anchor.point.x.getTime()), rows, at: anchor.point.x });
  };

  const toggle = (key) =>
    setHidden((current) => {
      const next = new Set(current);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });

  return (
    <div className="chart" ref={ref}>
      {geometry ? (
        <svg
          width={width}
          height={height}
          role="img"
          aria-label={ariaLabel}
          onPointerMove={onMove}
          onPointerDown={onMove}
          onPointerLeave={() => setHover(null)}
        >
          <g className="chart-grid">
            {geometry.ticks.map((tick) => (
              <line key={tick} x1={PAD.left} x2={width - PAD.right} y1={geometry.sy(tick)} y2={geometry.sy(tick)} />
            ))}
          </g>
          <g className="chart-axis">
            {geometry.ticks.map((tick) => (
              <text key={tick} x={PAD.left - 10} y={geometry.sy(tick) + 3.5} textAnchor="end">
                {yFormat(tick)}
              </text>
            ))}
            {geometry.xTicks.map((tick, index) => (
              <text
                key={tick}
                x={geometry.sx(tick)}
                y={height - 6}
                textAnchor={index === 0 ? "start" : index === geometry.xTicks.length - 1 ? "end" : "middle"}
              >
                {xFormat ? xFormat(new Date(tick)) : new Date(tick).toLocaleDateString()}
              </text>
            ))}
          </g>
          {visible.map((item, index) => {
            const d = item.points
              .map((point, i) => `${i ? "L" : "M"}${geometry.sx(point.x.getTime()).toFixed(1)},${geometry.sy(point.y).toFixed(1)}`)
              .join(" ");
            const areaD = `${d} L${geometry.sx(item.points.at(-1).x.getTime()).toFixed(1)},${PAD.top + geometry.innerH} L${geometry
              .sx(item.points[0].x.getTime())
              .toFixed(1)},${PAD.top + geometry.innerH} Z`;
            return (
              <g
                key={`${item.key}-${hidden.size}`}
                style={{ opacity: focused && focused !== item.key ? 0.16 : 1, transition: "opacity 160ms ease" }}
              >
                {index === 0 && !item.dashed && (
                  <>
                    <defs>
                      <linearGradient id={`area-${uid}`} x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor={item.color} stopOpacity="0.22" />
                        <stop offset="100%" stopColor={item.color} stopOpacity="0" />
                      </linearGradient>
                    </defs>
                    <path className="chart-area" d={areaD} fill={`url(#area-${uid})`} />
                  </>
                )}
                <path
                  className={item.dashed ? "chart-line-dashed" : "chart-line"}
                  d={d}
                  pathLength={item.dashed ? undefined : 1}
                  stroke={item.color}
                  style={{ animationDelay: `${index * 120}ms` }}
                />
                {item.points.length <= 40 &&
                  item.points.map((point, i) => (
                    <circle
                      key={i}
                      className="chart-point"
                      cx={geometry.sx(point.x.getTime())}
                      cy={geometry.sy(point.y)}
                      r={point.meta?.highlight ? 3.6 : 2.4}
                      fill={point.meta?.highlight ? item.color : "var(--surface)"}
                      stroke={item.color}
                      strokeWidth="1.6"
                    />
                  ))}
              </g>
            );
          })}
          {hover && (
            <g>
              <line className="chart-crosshair" x1={hover.x} x2={hover.x} y1={PAD.top} y2={PAD.top + geometry.innerH} />
              {hover.rows.map(({ item, point }) => (
                <circle
                  key={item.key}
                  cx={geometry.sx(point.x.getTime())}
                  cy={geometry.sy(point.y)}
                  r="4.5"
                  fill={item.color}
                  stroke="var(--surface)"
                  strokeWidth="2"
                />
              ))}
            </g>
          )}
        </svg>
      ) : (
        <div style={{ height }} />
      )}
      {hover && geometry && (
        <div
          className="chart-tooltip is-side"
          style={{ left: hover.x, top: PAD.top + 4, transform: `translate(${hover.x > width * 0.55 ? "calc(-100% - 14px)" : "14px"}, 0)` }}
        >
          <div className="chart-tooltip-title">{tooltipTitle ? tooltipTitle(hover.at) : hover.at.toLocaleString()}</div>
          {hover.rows.map(({ item, point }) => (
            <div className="chart-tooltip-row" key={item.key}>
              <span className="legend-item">
                <span className="swatch" style={{ background: item.color }} />
                {item.label}
              </span>
              <strong className="num">{yFormat(point.y)}</strong>
            </div>
          ))}
        </div>
      )}
      {series.length > 1 && (
        <div className="legend" style={{ marginTop: 12 }}>
          {series.map((item) => (
            <button
              type="button"
              key={item.key}
              className="legend-item"
              aria-pressed={!hidden.has(item.key)}
              onClick={() => toggle(item.key)}
              onPointerEnter={() => setFocused(item.key)}
              onPointerLeave={() => setFocused(null)}
              onFocus={() => setFocused(item.key)}
              onBlur={() => setFocused(null)}
            >
              <span className="swatch" style={{ background: item.color }} />
              {item.label}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

/** Vertical bars. data: [{ label, value, title? }] */
export function BarChart({ data, height = 180, color = "var(--chart-1)", format = (v) => v, labelEvery = 1, ariaLabel }) {
  const [ref, width] = useWidth();
  const [hover, setHover] = useState(null);
  const max = Math.max(1, ...data.map((item) => item.value));
  const pad = { top: 8, bottom: 22 };
  const innerH = height - pad.top - pad.bottom;
  const slot = width / Math.max(1, data.length);
  const barW = Math.max(4, Math.min(28, slot * 0.62));

  return (
    <div className="chart" ref={ref}>
      <svg width={width} height={height} role="img" aria-label={ariaLabel} onPointerLeave={() => setHover(null)}>
        <line className="chart-baseline" x1="0" x2={width} y1={pad.top + innerH} y2={pad.top + innerH} stroke="var(--border)" />
        {data.map((item, index) => {
          const h = item.value ? Math.max(3, (item.value / max) * innerH) : 2;
          const x = index * slot + (slot - barW) / 2;
          const active = hover === index;
          return (
            <g key={item.label} onPointerEnter={() => setHover(index)} onPointerDown={() => setHover(index)}>
              <rect x={index * slot} y={0} width={slot} height={height} fill="transparent" />
              <rect
                className="chart-bar"
                x={x}
                y={pad.top + innerH - h}
                width={barW}
                height={h}
                rx={Math.min(5, barW / 3)}
                fill={item.value ? color : "var(--surface-3)"}
                opacity={hover === null || active ? 1 : 0.45}
                style={{ animationDelay: `${index * 28}ms` }}
              />
              {index % labelEvery === 0 && (
                <text
                  className="chart-axis-label"
                  x={index * slot + slot / 2}
                  y={height - 6}
                  textAnchor="middle"
                  fill="var(--text-3)"
                  fontSize="10.5"
                  fontFamily="var(--font-mono)"
                >
                  {item.label}
                </text>
              )}
            </g>
          );
        })}
      </svg>
      {hover !== null && data[hover] && (
        <div
          className="chart-tooltip"
          style={{
            left: Math.min(Math.max(hover * slot + slot / 2, 80), width - 80),
            top: pad.top + innerH - Math.max(3, (data[hover].value / max) * innerH),
          }}
        >
          <div className="chart-tooltip-title">{data[hover].title || data[hover].label}</div>
          <strong className="num">{format(data[hover].value)}</strong>
        </div>
      )}
    </div>
  );
}

/** Ring chart. segments: [{ label, value, color }] */
export function Donut({ segments, size = 168, thickness = 16, center }) {
  const total = segments.reduce((sum, item) => sum + item.value, 0);
  const radius = (size - thickness) / 2;
  const circumference = 2 * Math.PI * radius;
  let offset = 0;
  return (
    <div className="chart" style={{ width: size, height: size }}>
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} role="img" aria-label="Breakdown">
        <circle cx={size / 2} cy={size / 2} r={radius} fill="none" stroke="var(--surface-3)" strokeWidth={thickness} />
        {total > 0 &&
          segments.map((item, index) => {
            const length = (item.value / total) * circumference;
            const gap = segments.filter((s) => s.value).length > 1 ? 3 : 0;
            const circle = (
              <circle
                key={item.label}
                className="donut-seg"
                cx={size / 2}
                cy={size / 2}
                r={radius}
                fill="none"
                stroke={item.color}
                strokeWidth={thickness}
                strokeLinecap="butt"
                strokeDasharray={`${Math.max(0, length - gap)} ${circumference}`}
                strokeDashoffset={-offset}
                transform={`rotate(-90 ${size / 2} ${size / 2})`}
                style={{ animationDelay: `${index * 120}ms` }}
              />
            );
            offset += length;
            return circle;
          })}
      </svg>
      {center && <div className="donut-center">{center}</div>}
    </div>
  );
}

/** Horizontal bar list rendered with HTML so labels wrap naturally. */
export function BarList({ rows, format = (v) => v, color = "var(--accent-fill)" }) {
  const max = Math.max(1, ...rows.map((row) => row.value));
  return (
    <ul className="bar-list">
      {rows.map((row, index) => (
        <li key={row.key || row.label} className="bar-list-row">
          <div className="bar-list-fill" style={{ "--w": `${(row.value / max) * 100}%`, "--c": row.color || color, animationDelay: `${index * 60}ms` }} />
          <div className="bar-list-label">
            <span>{row.label}</span>
            {row.sub && <small>{row.sub}</small>}
          </div>
          <span className="bar-list-value num">{format(row.value)}</span>
        </li>
      ))}
    </ul>
  );
}

export function Sparkline({ values, width = 96, height = 28, color = "var(--accent-fill)" }) {
  if (!values?.length) return null;
  const max = Math.max(1, ...values);
  const step = values.length > 1 ? width / (values.length - 1) : width;
  const points = values.map((value, index) => `${(index * step).toFixed(1)},${(height - 2 - (value / max) * (height - 4)).toFixed(1)}`);
  return (
    <svg className="sparkline" width={width} height={height} viewBox={`0 0 ${width} ${height}`} aria-hidden="true">
      <polyline className="chart-line" pathLength="1" points={points.join(" ")} fill="none" stroke={color} strokeWidth="1.6" />
    </svg>
  );
}
