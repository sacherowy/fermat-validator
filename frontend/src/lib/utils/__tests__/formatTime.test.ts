import { describe, expect, it } from "vitest";
import { formatTime } from "@/lib/utils/formatTime";

describe("formatTime", () => {
  it("returns 00:00:00 for zero milliseconds", () => {
    expect(formatTime(0)).toBe("00:00:00");
  });

  it("returns 00:00:00 for negative milliseconds", () => {
    expect(formatTime(-1000)).toBe("00:00:00");
  });

  it("formats 1 second", () => {
    expect(formatTime(1000)).toBe("00:00:01");
  });

  it("formats 59 seconds", () => {
    expect(formatTime(59_000)).toBe("00:00:59");
  });

  it("formats 1 minute exactly", () => {
    expect(formatTime(60_000)).toBe("00:01:00");
  });

  it("formats 59 minutes 59 seconds", () => {
    expect(formatTime(3_599_000)).toBe("00:59:59");
  });

  it("formats 1 hour exactly", () => {
    expect(formatTime(3_600_000)).toBe("01:00:00");
  });

  it("formats 3 hours — the practice timer duration", () => {
    expect(formatTime(10_800_000)).toBe("03:00:00");
  });

  it("floors fractional seconds", () => {
    expect(formatTime(10_800_999)).toBe("03:00:00");
  });

  it("pads single-digit hours", () => {
    expect(formatTime(3_661_000)).toBe("01:01:01");
  });

  it("formats multi-digit hours", () => {
    expect(formatTime(36_000_000)).toBe("10:00:00");
  });
});
