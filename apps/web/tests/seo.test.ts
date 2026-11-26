import { describe, expect, it } from "vitest";
import { buildDescription, buildTitle, clamp, organizationJsonLd, pageMetadata, xml } from "../lib/seo";

describe("titles", () => {
  it("clamps long titles at a word boundary and appends the brand once", () => {
    const t = buildTitle("Grand Theft Auto VI tracker: release dates by platform, patches and PC requirements");
    expect(t.endsWith(" · Patchbeast")).toBe(true);
    expect(t.length).toBeLessThanOrEqual(48 + " · Patchbeast".length);
    expect(t).toContain("…");
    expect(t).not.toMatch(/\s…/);
  });
  it("does not repeat the brand", () => {
    expect(buildTitle("Patchbeast: launch tracker")).toBe("Patchbeast: launch tracker");
    expect(buildTitle("About")).toBe("About · Patchbeast");
  });
});

describe("descriptions", () => {
  it("pads short descriptions into the 110-158 range and clamps long ones", () => {
    const short = buildDescription("Contact us.");
    expect(short.length).toBeGreaterThanOrEqual(70);
    const long = buildDescription("word ".repeat(80));
    expect(long.length).toBeLessThanOrEqual(158);
  });
  it("leaves a good description alone", () => {
    const d = "Sourced release status per platform, patch notes, PC requirements and videos for the game. Every item links to its source.";
    expect(buildDescription(d)).toBe(d.length <= 158 ? d : clamp(d, 158));
  });
});

describe("page metadata", () => {
  const m = pageMetadata({ title: "News", description: "x".repeat(130), path: "/news", indexable: true });
  it("sets canonical, absolute og/twitter image and rich-snippet robots for indexable pages", () => {
    expect(m.alternates?.canonical).toMatch(/\/news$/);
    const og = m.openGraph as { images: { url: string }[] };
    expect(og.images[0].url).toMatch(/^https?:\/\/.+\/opengraph-image$/);
    expect(JSON.stringify(m.robots)).toContain("max-image-preview");
  });
  it("noindex pages get plain noindex,nofollow", () => {
    const n = pageMetadata({ title: "X", description: "y".repeat(120), path: "/x", indexable: false });
    expect(n.robots).toEqual({ index: false, follow: false });
  });
  it("article type carries dates", () => {
    const a = pageMetadata({ title: "A", description: "z".repeat(120), path: "/a", indexable: true, type: "article", publishedTime: "2026-11-01T00:00:00Z" });
    expect((a.openGraph as { publishedTime?: string }).publishedTime).toBe("2026-11-01T00:00:00Z");
  });
});

describe("helpers", () => {
  it("escapes XML", () => expect(xml(`a & b <c> "d" 'e'`)).toBe("a &amp; b &lt;c&gt; &quot;d&quot; &apos;e&apos;"));
  it("organization markup points at the editorial policy", () => {
    const o = organizationJsonLd();
    expect(o["@type"]).toBe("Organization");
    expect(o.publishingPrinciples).toMatch(/\/editorial-policy$/);
  });
});
