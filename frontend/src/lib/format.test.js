import { describe, expect, it } from "vitest";

import { discountPct, formatCurrency, formatPercent, formatRelative, parseDate } from "./format";

describe("format helpers", () => {
  it("formats rupees in the Indian grouping", () => {
    expect(formatCurrency(1234567.5)).toBe("₹12,34,567.50");
    expect(formatCurrency(null)).toBe("—");
  });

  it("formats signed percentages", () => {
    expect(formatPercent(-10.014, { signed: true })).toBe("-10.0%");
    expect(formatPercent(4, { signed: true })).toBe("+4.0%");
  });

  it("treats timestamps without an offset as UTC", () => {
    expect(parseDate("2026-01-01 10:00:00").toISOString()).toBe("2026-01-01T10:00:00.000Z");
    expect(parseDate("2026-01-01T10:00:00+05:30").toISOString()).toBe("2026-01-01T04:30:00.000Z");
    expect(parseDate("garbage")).toBeNull();
  });

  it("describes relative times", () => {
    const now = Date.parse("2026-01-01T12:00:00Z");
    expect(formatRelative("2026-01-01T11:59:50Z", now)).toBe("just now");
    expect(formatRelative("2026-01-01T10:00:00Z", now)).toBe("2 hours ago");
    expect(formatRelative(null, now)).toBe("never");
  });

  it("computes discounts only when MRP exceeds price", () => {
    expect(discountPct(80, 100)).toBe(20);
    expect(discountPct(100, 100)).toBeNull();
  });
});
