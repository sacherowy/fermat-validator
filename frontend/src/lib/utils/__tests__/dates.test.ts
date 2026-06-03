import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { formatDate, formatDateShort, formatRelativeTime } from "@/lib/utils/dates";

// Fixed reference time: 2024-06-15T12:00:00Z
const NOW = new Date("2024-06-15T12:00:00Z");

function msAgo(ms: number): string {
  return new Date(NOW.getTime() - ms).toISOString();
}
function daysAgo(days: number): string {
  return msAgo(days * 24 * 60 * 60 * 1000);
}

describe("formatDate", () => {
  it("returns a formatted date string for a valid ISO timestamp", () => {
    const result = formatDate("2024-01-15T14:30:00+00:00");
    // Polish locale formatting — date and time present
    expect(result).toMatch(/\d{2}\.\d{2}\.\d{4}/);
  });

  it("returns the input unchanged for an invalid date string", () => {
    expect(formatDate("not-a-date")).toBe("not-a-date");
  });
});

describe("formatDateShort", () => {
  it("returns a date-only string for a valid ISO timestamp", () => {
    const result = formatDateShort("2024-01-15T14:30:00+00:00");
    expect(result).toMatch(/\d{2}\.\d{2}\.\d{4}/);
  });

  it("returns the input unchanged for an invalid date string", () => {
    expect(formatDateShort("not-a-date")).toBe("not-a-date");
  });
});

describe("formatRelativeTime", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.setSystemTime(NOW);
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("returns 'przed chwilą' for 30 seconds ago", () => {
    expect(formatRelativeTime(msAgo(30_000))).toBe("przed chwilą");
  });

  it("returns 'przed chwilą' for exactly 59 seconds ago", () => {
    expect(formatRelativeTime(msAgo(59_000))).toBe("przed chwilą");
  });

  it("returns 'X min temu' for 1 minute ago", () => {
    // 61 seconds → diffSec=61 → diffMin=1
    expect(formatRelativeTime(msAgo(61_000))).toBe("1 min temu");
  });

  it("returns 'X min temu' for 59 minutes ago", () => {
    expect(formatRelativeTime(msAgo(59 * 60 * 1000))).toBe("59 min temu");
  });

  it("returns 'X godz. temu' for 1 hour ago", () => {
    // 61 minutes → diffMin=61 → diffHours=1
    expect(formatRelativeTime(msAgo(61 * 60 * 1000))).toBe("1 godz. temu");
  });

  it("returns 'X godz. temu' for 23 hours ago", () => {
    expect(formatRelativeTime(msAgo(23 * 60 * 60 * 1000))).toBe("23 godz. temu");
  });

  it("returns 'wczoraj' for exactly 1 day ago", () => {
    expect(formatRelativeTime(daysAgo(1))).toBe("wczoraj");
  });

  it("returns 'X dni temu' for 3 days ago", () => {
    expect(formatRelativeTime(daysAgo(3))).toBe("3 dni temu");
  });

  it("returns 'X dni temu' for 6 days ago", () => {
    expect(formatRelativeTime(daysAgo(6))).toBe("6 dni temu");
  });

  it("falls back to formatDate for 7 days ago (not 'X dni temu')", () => {
    const result = formatRelativeTime(daysAgo(7));
    // Should be a formatted date, not "7 dni temu"
    expect(result).not.toBe("7 dni temu");
    expect(result).toMatch(/\d{2}\.\d{2}\.\d{4}/);
  });

  it("falls back to formatDate for dates older than a week", () => {
    const result = formatRelativeTime(daysAgo(30));
    expect(result).toMatch(/\d{2}\.\d{2}\.\d{4}/);
  });

  it("returns the input unchanged for an invalid date string", () => {
    expect(formatRelativeTime("not-a-date")).toBe("not-a-date");
  });
});
