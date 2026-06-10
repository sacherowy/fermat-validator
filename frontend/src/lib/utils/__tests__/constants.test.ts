import { describe, expect, it } from "vitest";
import { getMasteryThreshold } from "@/lib/utils/constants";

describe("getMasteryThreshold", () => {
  it("requires full marks for 2-point tasks", () => {
    // Matches backend progress.py:get_mastery_threshold()
    expect(getMasteryThreshold(2)).toBe(2);
  });

  it("requires max - 1 for 4-point tasks", () => {
    expect(getMasteryThreshold(4)).toBe(3);
  });

  it("requires max - 1 for larger scales", () => {
    expect(getMasteryThreshold(6)).toBe(5);
  });

  it("requires full marks for 1-point tasks", () => {
    expect(getMasteryThreshold(1)).toBe(1);
  });
});
