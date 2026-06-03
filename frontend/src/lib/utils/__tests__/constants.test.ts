import { describe, expect, it } from "vitest";
import { getMaxScore, getMasteryThreshold } from "@/lib/utils/constants";

describe("getMaxScore", () => {
  it("returns 3 for etap1", () => {
    expect(getMaxScore("etap1")).toBe(3);
  });

  it("returns 6 for etap2", () => {
    expect(getMaxScore("etap2")).toBe(6);
  });

  it("returns 6 for etap3", () => {
    expect(getMaxScore("etap3")).toBe(6);
  });

  it("returns 6 as default for unknown etap", () => {
    expect(getMaxScore("etap4")).toBe(6);
  });
});

describe("getMasteryThreshold", () => {
  it("returns 2 for etap1", () => {
    // Matches backend progress.py: return 5 if etap in ('etap2', 'etap3') else 2
    expect(getMasteryThreshold("etap1")).toBe(2);
  });

  it("returns 5 for etap2", () => {
    expect(getMasteryThreshold("etap2")).toBe(5);
  });

  it("returns 5 for etap3", () => {
    expect(getMasteryThreshold("etap3")).toBe(5);
  });

  it("returns 5 as default for unknown etap", () => {
    expect(getMasteryThreshold("etap4")).toBe(5);
  });
});
