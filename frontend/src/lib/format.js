const inr = new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 2 });
const inrCompact = new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 0 });
const number = new Intl.NumberFormat("en-IN");

export function formatCurrency(value, { compact = false } = {}) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "—";
  return (compact ? inrCompact : inr).format(Number(value));
}

export function formatNumber(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "—";
  return number.format(Number(value));
}

export function formatPercent(value, { signed = false, digits = 1 } = {}) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "—";
  const fixed = Number(value).toFixed(digits);
  return `${signed && Number(value) > 0 ? "+" : ""}${fixed}%`;
}

// The API returns ISO strings; SQLite-backed dev databases return them without
// an offset. Snapshots are always written in UTC, so treat bare values as UTC.
export function parseDate(value) {
  if (!value) return null;
  if (value instanceof Date) return value;
  const text = String(value);
  const hasZone = /[zZ]|[+-]\d\d:?\d\d$/.test(text);
  const date = new Date(hasZone ? text : `${text.replace(" ", "T")}Z`);
  return Number.isNaN(date.getTime()) ? null : date;
}

export function formatDateTime(value) {
  const date = parseDate(value);
  if (!date) return "—";
  return date.toLocaleString("en-IN", { day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit" });
}

export function formatDate(value) {
  const date = parseDate(value);
  if (!date) return "—";
  return date.toLocaleDateString("en-IN", { day: "2-digit", month: "short" });
}

const rtf = new Intl.RelativeTimeFormat("en", { numeric: "auto" });

export function formatRelative(value, now = Date.now()) {
  const date = parseDate(value);
  if (!date) return "never";
  const seconds = Math.round((date.getTime() - now) / 1000);
  const abs = Math.abs(seconds);
  if (abs < 45) return "just now";
  if (abs < 3600) return rtf.format(Math.round(seconds / 60), "minute");
  if (abs < 86400) return rtf.format(Math.round(seconds / 3600), "hour");
  if (abs < 86400 * 30) return rtf.format(Math.round(seconds / 86400), "day");
  return formatDate(date);
}

export const ALERT_TYPES = {
  price_drop: { label: "Price drop", tone: "danger" },
  buybox_change: { label: "Buy Box change", tone: "accent" },
  stock_spike: { label: "Out of stock", tone: "warning" },
};

export const STOCK = {
  in_stock: { label: "In stock", tone: "success" },
  low_stock: { label: "Low stock", tone: "warning" },
  out_of_stock: { label: "Out of stock", tone: "danger" },
};

export function discountPct(price, mrp) {
  if (!price || !mrp || mrp <= price) return null;
  return ((mrp - price) / mrp) * 100;
}

export const ASIN_PATTERN = /^[A-Z0-9]{10}$/;
