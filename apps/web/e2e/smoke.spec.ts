import { expect, test } from "@playwright/test";

const robots = async (page: import("@playwright/test").Page) =>
  (await page.locator('meta[name="robots"]').getAttribute("content")) ?? "";

test("home: launch cards, one h1, skip link, indexable", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { level: 1 })).toHaveCount(1);
  await expect(page.getByRole("link", { name: "Skip to content" })).toBeAttached();
  await expect(page.getByRole("heading", { name: /Grand Theft Auto VI/ })).toBeVisible();
  await expect(page.getByRole("heading", { level: 1 })).toContainText("PC first");
  expect(await robots(page)).toContain("index");
  expect(await robots(page)).not.toContain("noindex");
  await expect(page.locator('link[rel="canonical"]')).toHaveAttribute("href", /^https?:\/\/[^/]+\/?$/);
});

test("whole launch card is clickable and the long URL redirects to the flagship short URL", async ({ page }) => {
  await page.goto("/");
  await page.getByTestId("launch-card").first().getByTestId("countdown").click({ force: true }); // lands on the card-wide link overlay, not the title
  await expect(page).toHaveURL(/\/gta-6-pc$/);
  const res = await page.request.get("/games/gta-6-pc", { maxRedirects: 0 });
  expect(res.status()).toBe(308);
  expect(res.headers()["location"]).toContain("/gta-6-pc");
});

test("flagship page: per-platform rows, known/unknown, pinned FAQ, per-game signup", async ({ page }) => {
  await page.goto("/gta-6-pc");
  for (const p of ["pc", "ps5", "xbox_series"]) {
    await expect(page.getByTestId(`platform-release-${p}`)).toContainText("Date unconfirmed");
  }
  const ku = page.getByTestId("known-unknown");
  await expect(ku).toContainText("Not known yet");
  await expect(ku).toContainText("PlayStation 5");
  await expect(page.getByRole("heading", { name: "FAQ" })).toBeVisible();
  await expect(page.getByRole("heading", { name: /Get .* changes by email/ })).toBeVisible();
  // the page title is config-driven (hub_config.seo_title)
  await expect(page).toHaveTitle(/GTA VI release dates, patches & PC requirements · Patchbeast/);
  await expect(page.locator('link[rel="canonical"]')).toHaveAttribute("href", /\/gta-6-pc$/);
});

test("per-game newsletter signup sends the game slug", async ({ page }) => {
  let body: Record<string, string> = {};
  await page.route("**/api/v1/newsletter/subscribe/", async (r) => {
    body = r.request().postDataJSON();
    await r.fulfill({ json: { ok: true } });
  });
  await page.goto("/gta-6-pc");
  await page.getByLabel("Email address").fill("fan@example.com");
  await page.getByRole("button", { name: /weekly digest/i }).click();
  await expect(page.getByRole("status")).toContainText("confirmation link");
  expect(body.game).toBe("gta-6-pc");
});

test("placeholder anchor: honest 'Date unconfirmed', noindex, placeholder notice", async ({ page }) => {
  await page.goto("/gta-6-pc");
  await expect(page.getByTestId("countdown")).toHaveAttribute("data-mode", "unconfirmed");
  await expect(page.getByTestId("countdown").getByText("Date unconfirmed")).toBeVisible();
  await expect(page.getByText("Placeholder page.")).toBeVisible();
  expect(await robots(page)).toContain("noindex");
});

test("demo hub: live countdown, platform rows, signal meter, changelog, sources", async ({ page }) => {
  await page.goto("/games/demo-launch");
  await expect(page.getByTestId("platform-release-ps5")).not.toContainText("Date unconfirmed");
  await expect(page.getByTestId("countdown")).toHaveAttribute("data-mode", "live");
  await expect(page.locator('[data-level="reported"]').first()).toBeVisible();
  await expect(page.getByRole("list", { name: "Change log" })).toBeVisible();
  await expect(page.getByRole("link", { name: /example\.com/ }).first()).toBeVisible();
  expect(await robots(page)).toContain("noindex"); // demo is allow_index=false
});

test("patches page filters by platform", async ({ page }) => {
  await page.goto("/games/demo-launch/patches");
  const all = await page.getByTestId("patch-item").count();
  expect(all).toBeGreaterThanOrEqual(3);
  await page.getByTestId("filter-ps5").click();
  await expect(page).toHaveURL(/platform=ps5/);
  const items = page.getByTestId("patch-item");
  await expect(items).toHaveCount(1);
  await expect(items.first()).toHaveAttribute("data-platform", "ps5");
});

test("requirements checker compares client-side and states caveats", async ({ page }) => {
  await page.goto("/games/demo-launch/requirements");
  await page.getByTestId("cpu").selectOption("amd-ryzen-5-5600");
  await page.getByTestId("gpu").selectOption("nvidia-rtx-3070");
  await page.getByTestId("ram").selectOption("16");
  await expect(page.getByTestId("checker-result")).toContainText("Meets recommended");
  await page.getByTestId("gpu").selectOption("nvidia-gtx-1050-ti");
  await expect(page.getByTestId("checker-result")).toContainText("Below minimum");
  await expect(page.getByText(/not benchmarks/)).toBeVisible();
});

test("checker refuses to guess when requirements are placeholders", async ({ page }) => {
  await page.goto("/games/gta-6-pc/requirements");
  await expect(page.getByTestId("checker-unavailable")).toBeVisible();
});

test("/feed is noindex,nofollow and /news is curated", async ({ page, request }) => {
  await page.goto("/feed");
  expect(await robots(page)).toMatch(/noindex/);
  expect(await robots(page)).toMatch(/nofollow/);
  const res = await request.get("/feed");
  expect(res.headers()["x-robots-tag"]).toContain("noindex");
  await page.goto("/news");
  await expect(page.getByRole("heading", { level: 1, name: "News" })).toBeVisible();
});

test("sitemap and robots.txt exclude raw feed and placeholders", async ({ request }) => {
  const sm = await (await request.get("/sitemap.xml")).text();
  expect(sm).not.toContain("/feed");
  expect(sm).not.toContain("gta-6-pc"); // placeholder: not in sitemap
  expect(sm).not.toContain("demo-launch");
  expect(sm).toContain("/about");
  const rb = await (await request.get("/robots.txt")).text();
  expect(rb).toContain("Disallow: /feed");
  expect(rb).toMatch(/Sitemap: .*sitemap\.xml/);
});

test("newsletter signup (double opt-in message)", async ({ page }) => {
  await page.route("**/api/v1/newsletter/subscribe/", (r) => r.fulfill({ json: { ok: true } }));
  await page.goto("/");
  await page.getByLabel("Email address").fill("fan@example.com");
  await page.getByRole("button", { name: /weekly digest/i }).click();
  await expect(page.getByRole("status")).toContainText("confirmation link");
});

test("legal pages exist; revalidate endpoint is protected", async ({ page, request }) => {
  for (const p of ["/about", "/privacy", "/terms", "/affiliate-disclosure", "/contact"]) {
    const r = await page.goto(p);
    expect(r?.status(), p).toBe(200);
  }
  const res = await request.post("/internal/revalidate", { data: { tags: ["x"] } });
  expect(res.status()).toBe(401);
});

test("theme toggle switches to light and persists", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("button", { name: /theme, switch to/ }).click();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "light");
  await page.reload();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "light");
});

test("no ads or affiliate blocks while flags are off", async ({ page }) => {
  await page.goto("/games/demo-launch");
  await expect(page.getByLabel("Advertisement")).toHaveCount(0);
  await expect(page.getByText("Affiliate link")).toHaveCount(0);
});

test("footer sticks to the bottom of the viewport on short pages (desktop)", async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 1100 });
  await page.goto("/contact"); // short page: content is far shorter than the viewport
  const box = await page.locator("footer").boundingBox();
  expect(box).not.toBeNull();
  expect(Math.round(box!.y + box!.height)).toBeGreaterThanOrEqual(1100 - 1);
  expect(await page.evaluate(() => document.documentElement.scrollHeight)).toBeLessThanOrEqual(1100);
});

test("every game page has section navigation; each section has its own page", async ({ page }) => {
  await page.goto("/games/demo-launch");
  const nav = page.getByTestId("game-nav");
  for (const label of ["Overview", "Patches & updates", "News", "Videos", "PC requirements", "Timeline"]) {
    await expect(nav.getByRole("link", { name: label })).toBeVisible();
  }
  for (const [label, url] of [["Patches & updates", /\/patches$/], ["News", /\/news$/], ["Timeline", /\/timeline$/], ["Videos", /\/videos$/]] as const) {
    await page.goto("/games/demo-launch");
    await page.getByTestId("game-nav").getByRole("link", { name: label }).click();
    await expect(page).toHaveURL(url);
    await expect(page.getByTestId("game-nav").getByRole("link", { name: label })).toHaveAttribute("aria-current", "page");
    await expect(page.getByRole("navigation", { name: "Breadcrumb" })).toBeVisible();
  }
});

test("patch detail page: highlights, size, two sources, sibling platform, back link", async ({ page }) => {
  await page.goto("/games/demo-launch/patches?platform=ps5");
  await page.getByRole("link", { name: "Update details →" }).first().click();
  await expect(page).toHaveURL(/\/patches\/ps5\/0\.9\.1$/);
  await expect(page.getByRole("heading", { level: 1 })).toContainText("update 0.9.1");
  await expect(page.getByTestId("patch-highlights").locator("li")).toHaveCount(3);
  await expect(page.getByTestId("patch-meta")).toContainText("Size: DEMO 1.2 GB");
  await expect(page.getByTestId("patch-sources").getByRole("link")).toHaveCount(2); // 2 independent sources; the notes link is the same site, so not repeated
  await expect(page.getByText("Official notes")).toHaveCount(0); // never claim "official" without knowing
  await expect(page.getByText("Confirmed: reported by 2 independent sources")).toBeVisible();
  await page.getByRole("link", { name: "PC", exact: true }).click(); // same version on another platform
  await expect(page).toHaveURL(/\/patches\/pc\/0\.9\.1$/);
  await expect(page.locator('meta[name="robots"]')).toHaveAttribute("content", /noindex/); // demo game
  await expect(page.getByRole("link", { name: "← All patches & updates" })).toBeVisible();
});

test("per-game news and timeline pages", async ({ page }) => {
  await page.goto("/games/demo-launch/news");
  await expect(page.getByRole("heading", { level: 1 })).toContainText("news");
  await expect(page.getByRole("heading", { name: /DEMO headline/ })).toHaveCount(2);
  await page.goto("/games/demo-launch/timeline");
  await expect(page.getByRole("list", { name: "Change log" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Patch 0.9.1" })).toBeVisible();
});

test("unknown patch is a 404 and breadcrumbs carry JSON-LD", async ({ page }) => {
  const r = await page.goto("/games/demo-launch/patches/pc/9.9.9");
  expect(r?.status()).toBe(404);
  await page.goto("/games/demo-launch/news");
  const ld = await page.locator('script[type="application/ld+json"]').allTextContents();
  expect(ld.some((t) => t.includes("BreadcrumbList"))).toBe(true);
});

test("countdown switches to 'Released' once the date has passed", async ({ page }) => {
  await page.clock.install({ time: new Date(Date.now() + 400 * 86_400_000) });
  await page.goto("/games/demo-launch");
  await expect(page.getByTestId("countdown")).toHaveAttribute("data-mode", "released");
  await expect(page.getByTestId("countdown")).toContainText("Released");
});

test("briefings: listed on news pages and hub, detail has citations, sources and AI disclosure", async ({ page }) => {
  await page.goto("/games/demo-launch/news");
  await expect(page.getByRole("heading", { name: "Briefings" })).toBeVisible();
  const card = page.getByTestId("story-card").filter({ hasText: "DEMO briefing" });
  await expect(card).toContainText("Briefing");
  await expect(card).toContainText("Confirmed");
  await card.getByRole("heading").click({ force: true }); // card-wide link
  await expect(page).toHaveURL(/\/games\/demo-launch\/news\/demo-briefing-sample$/);
  await expect(page.getByRole("heading", { level: 1 })).toContainText("DEMO briefing");
  const body = page.getByTestId("story-body");
  await expect(body.locator("p")).toHaveCount(2);
  await expect(body.getByRole("link", { name: "Source 2" }).first()).toHaveAttribute("href", "#src-2");
  await expect(page.getByTestId("story-sources").locator("li")).toHaveCount(2);
  await expect(page.getByTestId("story-disclosure")).toContainText("drafted by an AI assistant");
  await expect(page.getByTestId("story-disclosure")).toContainText("approved by a person");
  await expect(page.locator('meta[name="robots"]')).toHaveAttribute("content", /noindex/); // demo game
  await page.goto("/news");
  await expect(page.getByRole("heading", { name: "Briefings" })).toBeVisible();
  await page.goto("/games/demo-launch");
  await expect(page.getByTestId("story-card")).toHaveCount(2); // the briefing and the roundup
});

test("unknown briefing is a 404", async ({ page }) => {
  expect((await page.goto("/games/demo-launch/news/does-not-exist"))?.status()).toBe(404);
});

test("news page filters by game, keeps the filter, labels briefings vs roundups", async ({ page }) => {
  await page.goto("/news");
  const filter = page.getByTestId("game-filter");
  await expect(filter.getByRole("link", { name: "All games" })).toHaveAttribute("aria-current", "true");
  await expect(page.getByTestId("story-card").first()).toBeVisible();
  await expect(page.getByTestId("story-card").filter({ hasText: "Roundup" })).toHaveCount(1);
  await expect(page.getByTestId("story-card").filter({ hasText: "Briefing" })).toHaveCount(1);

  await filter.getByTestId("filter-gta-6-pc").click();
  await expect(page).toHaveURL(/\/news\?game=gta-6-pc$/);
  await expect(page.getByRole("heading", { level: 1 })).toContainText("Grand Theft Auto VI");
  await expect(page.getByTestId("story-card")).toHaveCount(0);
  await expect(page.getByTestId("no-linked")).toContainText("No curated news for Grand Theft Auto VI");
  await expect(page.locator('meta[name="robots"]')).toHaveAttribute("content", /noindex/); // filtered view is not an index target

  await page.getByTestId("game-filter").getByTestId("filter-demo-launch").click();
  await expect(page).toHaveURL(/game=demo-launch/);
  await expect(page.getByTestId("story-card")).toHaveCount(2);
  await expect(page.getByRole("heading", { name: /DEMO headline/ })).toHaveCount(2);

  await page.goto("/news?game=not-a-game"); // unknown filter falls back to all games
  await expect(page.getByTestId("game-filter").getByRole("link", { name: "All games" })).toHaveAttribute("aria-current", "true");
});
