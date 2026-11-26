import { expect, test, type APIRequestContext } from "@playwright/test";

/**
 * SEO consistency: crawl the sitemap like a search engine would and check every listed page.
 * Run it twice in CI: with the default seed, and with DEMO_INDEXABLE=1 (adds indexable demo pages:
 * patch page, briefing, videos...) so the deeper templates are covered too.
 */
const UA = { "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) Chrome/120 Safari/537.36" }; // NOT a known bot: worst case for metadata placement
const KNOWN_LD = new Set(["WebSite", "Organization", "VideoGame", "BreadcrumbList", "FAQPage", "Article", "NewsArticle", "CollectionPage", "WebPage", "VideoObject"]);

const pathOf = (u: string) => new URL(u).pathname + new URL(u).search;

async function sitemapPaths(request: APIRequestContext): Promise<string[]> {
  const xml = await (await request.get("/sitemap.xml")).text();
  return [...xml.matchAll(/<loc>([^<]+)<\/loc>/g)].map((m) => pathOf(m[1].replace(/&amp;/g, "&")));
}

const meta = (head: string, key: string) => head.match(new RegExp(`<meta[^>]+(?:name|property)="${key}"[^>]+content="([^"]*)"`, "i"))?.[1] ?? "";

test("every sitemap URL is a healthy, indexable, well-formed page", async ({ request }) => {
  const paths = await sitemapPaths(request);
  expect(paths.length).toBeGreaterThan(5);
  expect(new Set(paths).size).toBe(paths.length); // no duplicates
  for (const p of paths) {
    const res = await request.get(p, { headers: UA });
    expect(res.status(), p).toBe(200);
    const html = await res.text();
    const headEnd = html.indexOf("</head>");
    const head = html.slice(0, headEnd);

    // everything search engines read must be in the initial <head>, even for a non-bot user agent
    const title = head.match(/<title>([^<]*)<\/title>/)?.[1] ?? "";
    expect(title.length, `${p} title "${title}"`).toBeGreaterThanOrEqual(10);
    expect(title.length, `${p} title too long: "${title}"`).toBeLessThanOrEqual(65);
    const desc = meta(head, "description");
    expect(desc.length, `${p} description`).toBeGreaterThanOrEqual(70);
    expect(desc.length, `${p} description too long`).toBeLessThanOrEqual(165);
    const canonical = head.match(/<link rel="canonical" href="([^"]+)"/)?.[1] ?? "";
    expect(pathOf(canonical).replace(/\/$/, "") || "/", `${p} canonical`).toBe(p === "/" ? "/" : p);
    expect(meta(head, "robots"), `${p} robots`).not.toMatch(/noindex/);
    for (const k of ["og:title", "og:description", "og:url", "og:image", "twitter:card", "twitter:image"]) expect(meta(head, k), `${p} ${k}`).not.toBe("");
    expect(head, `${p} html lang`).toBeDefined();
    expect(html).toMatch(/<html[^>]+lang="en"/);

    // exactly one h1, and a sane amount of text
    expect((html.match(/<h1[\s>]/g) ?? []).length, `${p} h1 count`).toBe(1);
    expect(html.replace(/<script[\s\S]*?<\/script>|<style[\s\S]*?<\/style>|<[^>]+>/g, " ").split(/\s+/).length, `${p} text`).toBeGreaterThan(120);

    // structured data parses and is honest-looking
    for (const m of html.matchAll(/<script type="application\/ld\+json">([\s\S]*?)<\/script>/g)) {
      const j = JSON.parse(m[1].replace(/\\u003c/g, "<"));
      const nodes = (j["@graph"] ?? [j]) as Record<string, unknown>[];
      for (const n of nodes) {
        expect(KNOWN_LD.has(n["@type"] as string), `${p} unexpected @type ${String(n["@type"])}`).toBe(true);
        if (n["@type"] === "Article" || n["@type"] === "NewsArticle") {
          for (const f of ["headline", "image", "author", "publisher", "mainEntityOfPage"]) expect(n[f], `${p} ${String(n["@type"])}.${f}`).toBeTruthy();
          expect(String(n.image)).toMatch(/^https?:\/\//);
          expect((n.citation as string[] | undefined)?.length ?? 0, `${p} citations`).toBeGreaterThan(0);
        }
        if (n["@type"] === "BreadcrumbList") (n.itemListElement as { position: number }[]).forEach((it, i) => expect(it.position).toBe(i + 1));
        if (n["@type"] === "FAQPage") expect((n.mainEntity as unknown[]).length).toBeGreaterThan(0);
        if (n["@type"] === "VideoObject") for (const f of ["name", "thumbnailUrl", "uploadDate", "embedUrl"]) expect(n[f], `${p} VideoObject.${f}`).toBeTruthy();
      }
    }

    // internal links must not point at pages that are not indexable-by-design (raw feed)
    expect(html, `${p} links to /feed`).not.toMatch(/href="\/feed"/);
  }
});

test("share images resolve for every sitemap page", async ({ request }) => {
  const seen = new Set<string>();
  for (const p of await sitemapPaths(request)) {
    const html = await (await request.get(p, { headers: UA })).text();
    const img = meta(html.slice(0, html.indexOf("</head>")), "og:image");
    if (!img || seen.has(img)) continue;
    seen.add(img);
    const r = await request.get(pathOf(img));
    expect(r.status(), img).toBe(200);
    expect(r.headers()["content-type"], img).toMatch(/^image\//);
  }
});

test("noindex-by-design pages are not in the sitemap and say so", async ({ request }) => {
  const paths = await sitemapPaths(request);
  for (const p of ["/feed", "/newsletter/confirm", "/newsletter/unsubscribe", "/internal/health"]) expect(paths).not.toContain(p);
  const feed = await (await request.get("/feed", { headers: UA })).text();
  expect(meta(feed, "robots")).toMatch(/noindex/);
});

test("robots.txt points at the sitemap and does not block indexable sections", async ({ request }) => {
  const txt = await (await request.get("/robots.txt")).text();
  expect(txt).toMatch(/Sitemap: https?:\/\/.+\/sitemap\.xml/);
  expect(txt).toContain("Disallow: /feed");
  for (const p of await sitemapPaths(request)) {
    for (const line of txt.split("\n").filter((l) => l.startsWith("Disallow:"))) {
      const rule = line.replace("Disallow:", "").trim();
      if (rule && rule !== "/") expect(p.startsWith(rule), `${p} is blocked by "${rule}" but listed in the sitemap`).toBe(false);
    }
  }
});

test("RSS is valid, advertised, and lists only sitemap pages", async ({ request, page }) => {
  const res = await request.get("/rss.xml");
  expect(res.status()).toBe(200);
  expect(res.headers()["content-type"]).toContain("application/rss+xml");
  const xml = await res.text();
  expect(xml.startsWith("<?xml")).toBe(true);
  const ok = await page.evaluate((x) => !new DOMParser().parseFromString(x, "application/xml").querySelector("parsererror"), xml);
  expect(ok).toBe(true);
  const sitemap = new Set(await sitemapPaths(request));
  for (const m of xml.matchAll(/<item>[\s\S]*?<link>([^<]+)<\/link>/g)) expect(sitemap.has(pathOf(m[1])), `RSS item ${m[1]} is not in the sitemap`).toBe(true);
  await page.goto("/");
  await expect(page.locator('link[rel="alternate"][type="application/rss+xml"]')).toHaveAttribute("href", /rss\.xml$/);
});

test("home page exposes Organization markup with a publishing-principles link and internal links to deep pages", async ({ page }) => {
  await page.goto("/");
  const ld = (await page.locator('script[type="application/ld+json"]').allTextContents()).map((t) => JSON.parse(t));
  const org = ld.find((n) => n["@type"] === "Organization");
  expect(org?.publishingPrinciples).toMatch(/\/editorial-policy$/);
  expect(org?.logo).toMatch(/^https?:\/\//);
  await expect(page.getByRole("link", { name: "Editorial policy" }).first()).toBeVisible();
  expect((await page.locator("main a[href^='/']").count())).toBeGreaterThan(3);
});

test("editorial policy page exists and discloses AI-assisted drafting with human approval", async ({ page }) => {
  await page.goto("/editorial-policy");
  await expect(page.getByRole("heading", { level: 1 })).toContainText("Editorial policy");
  await expect(page.getByText(/approved by a person before they are published/)).toBeVisible();
});

test("unknown pages return a real 404 (not a soft 404)", async ({ request }) => {
  for (const p of ["/does-not-exist", "/games/nope", "/games/demo-launch/patches/pc/9.9.9"]) expect((await request.get(p)).status(), p).toBe(404);
});

test("IndexNow key file is served only when configured", async ({ request }) => {
  const r = await request.get("/indexnow.txt");
  expect([200, 404]).toContain(r.status());
  if (r.status() === 200) expect((await r.text()).trim().length).toBeGreaterThanOrEqual(8);
});
