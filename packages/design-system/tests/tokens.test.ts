import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import { contrast, parse } from "../src/lib/contrast";
import { breakdown } from "../src/components/Countdown";

const css = readFileSync(new URL("../src/styles/tokens.css", import.meta.url), "utf8");

function theme(selector: string): Record<string, string> {
  const start = css.indexOf(selector);
  const block = css.slice(start, css.indexOf("}", start));
  const out: Record<string, string> = {};
  for (const m of block.matchAll(/--pb-([a-z0-9-]+):\s*(\d+ \d+ \d+);/g)) out[m[1]] = m[2];
  return out;
}

const dark = theme(":root {");
const light = { ...dark, ...theme(':root[data-theme="light"]') };

describe.each([["dark", dark], ["light", light]])("%s theme meets WCAG AA", (_n, t) => {
  const text = ["text", "text-muted", "accent-text", "confirmed", "reported", "rumour", "alert"];
  const surfaces = ["bg", "surface-1", "surface-2", "surface-3"];
  for (const fg of text) {
    for (const bg of surfaces) {
      it(`${fg} on ${bg} >= 4.5:1`, () => {
        expect(contrast(parse(t[fg]), parse(t[bg]))).toBeGreaterThanOrEqual(4.5);
      });
    }
  }
  it("button text on accent-strong >= 4.5:1", () => {
    expect(contrast(parse(t["on-accent"]), parse(t["accent-strong"]))).toBeGreaterThanOrEqual(4.5);
  });
  it("focus ring (accent) vs bg >= 3:1", () => {
    expect(contrast(parse(t["accent"]), parse(t["bg"]))).toBeGreaterThanOrEqual(3);
  });
});

it("dark background is the specified near-black", () => {
  expect(dark["bg"]).toBe("11 13 16"); // #0B0D10
  expect(dark["accent"]).toBe("124 92 255"); // #7C5CFF
  expect([dark["confirmed"], dark["reported"], dark["rumour"], dark["alert"]]).toEqual([
    "46 229 157", "255 176 32", "138 147 166", "255 90 95",
  ]);
});

it("countdown breakdown", () => {
  expect(breakdown(((2 * 24 + 3) * 3600 + 4 * 60 + 5) * 1000)).toEqual({ d: 2, h: 3, m: 4, s: 5 });
  expect(breakdown(-5)).toEqual({ d: 0, h: 0, m: 0, s: 0 });
});
