import { expect, test } from "@playwright/test";

const robots = async (page: import("@playwright/test").Page) =>
  (await page.locator('meta[name="robots"]').getAttribute("content")) ?? "";

test("home: launch cards, one h1, skip link, indexable", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { level: 1 })).toHaveCount(1);
  await expect(page.getByRole("link", { name: "Skip to content" })).toBeAttached();
  await expect(page.getByRole("heading", { name: /Grand Theft Auto VI/ })).toBeVisible();
  expect(await robots(page)).toContain("index");
  expect(await robots(page)).not.toContain("noindex");
  await expect(page.locator('link[rel="canonical"]')).toHaveAttribute("href", /^https?:\/\/[^/]+\/?$/);
});

test("placeholder anchor: honest 'Date unconfirmed', noindex, placeholder notice", async ({ page }) => {
  await page.goto("/games/gta-6-pc");
  await expect(page.getByTestId("countdown")).toHaveAttribute("data-mode", "unconfirmed");
  await expect(page.getByTestId("countdown").getByText("Date unconfirmed")).toBeVisible();
  await expect(page.getByText("Placeholder page.")).toBeVisible();
  expect(await robots(page)).toContain("noindex");
});

test("demo hub: live countdown, signal meter, changelog, sources", async ({ page }) => {
  await page.goto("/games/demo-launch");
  await expect(page.getByTestId("countdown")).toHaveAttribute("data-mode", "live");
  await expect(page.locator('[data-level="reported"]').first()).toBeVisible();
  await expect(page.getByRole("list", { name: "Change log" })).toBeVisible();
  await expect(page.getByRole("link", { name: /example\.com/ }).first()).toBeVisible();
  expect(await robots(page)).toContain("noindex"); // demo is allow_index=false
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
  expect(sm).not.toContain("gta-6-pc");
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
  await page.getByRole("button", { name: "Light theme" }).click();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "light");
  await page.reload();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "light");
});

test("no ads or affiliate blocks while flags are off", async ({ page }) => {
  await page.goto("/games/demo-launch");
  await expect(page.getByLabel("Advertisement")).toHaveCount(0);
  await expect(page.getByText("Affiliate link")).toHaveCount(0);
});
