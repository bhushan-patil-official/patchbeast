# SEO

Nobody can promise a #1 ranking. What we control is: a technically clean site, pages that deserve to rank, and a steady stream of fresh, sourced, original content. This document says what is built, what to do, and how to measure.

## What is built (technical + on-page)

| Area | What |
|---|---|
| Crawlability | `sitemap.xml` lists **only indexable** pages (real, sourced content), with `lastmod`; `robots.txt` blocks `/feed`, `/api`, `/admin`, `/newsletter`; placeholder/filtered/paginated/raw pages are `noindex`. A spec crawls the sitemap on every CI run. |
| Metadata | Unique title (<= ~60 chars incl. brand), description (110-158), self-canonical, Open Graph + Twitter card **with a share image on every page** (`/og/game`, `/og/patch`, `/og/story`). Metadata is in the initial `<head>` for **every** crawler (`htmlLimitedBots`), not streamed into the body. |
| Rich results | `Organization` + `WebSite` (home), `VideoGame`, `FAQPage`, `BreadcrumbList`, `Article` (patch pages), `NewsArticle` (briefings, with `citation`), `CollectionPage`/`ItemList` (news), `VideoObject` (videos). Emitted only when the page is indexable and backed by data. Snippet directives allow large images/snippets. |
| Content structure | One H1 per page, section pages per game (overview, patches & updates with **a page per update**, news, videos, PC requirements, timeline), breadcrumbs, a section tab bar, "latest updates/briefings" on the home page for internal links and freshness. |
| Trust (E-E-A-T) | Sources on every item, verification labels, `/editorial-policy` (how we verify, AI drafting with human approval, corrections), About/Contact/Privacy/Terms, AI-assistance disclosure on briefings. |
| Freshness signals | Pages refresh within seconds of a publish (signal-driven revalidation); `lastmod`; RSS feed `/rss.xml` of our own briefings and updates (indexable pages only); **IndexNow** pings Bing/Yandex/etc. for changed indexable pages (`INDEXNOW_KEY`). |
| Performance | ~141 kB first-load JS on game pages, self-hosted fonts, inlined CSS, no layout shift, click-to-load video. Lighthouse (mobile, lab): SEO 100, accessibility 100, best-practices 100, performance 94-96. |
| Canonical host | `www` -> apex 301 in Caddy; HTTP -> HTTPS automatic; `/games/<slug>` -> short URL 308. |

## What actually moves rankings (and is up to you)

1. **Be the most accurate, fastest sourced source for narrow questions.** Head terms ("GTA 6") belong to big publishers. Winnable queries are specific: "<game> PC release date", "<game> update 01.002.002 patch notes", "<game> PC requirements", "<game> patch notes PS5". Every update gets its own page; publish within minutes of an announcement, with sources.
2. **Original value.** Briefings, roundups, the verification label, the timeline and the PC checker are what make the pages more than aggregation. Keep human review tight; never publish unverified claims. Thin or duplicated pages are noindexed by design.
3. **Links from real places.** Earn them: share confirmed updates with attribution on social and in communities where it is welcome and allowed, let outlets cite your timeline/verification page, publish useful tools (the checker). Do not buy links, run link schemes, or spam forums.
4. **Consistency.** Check the review queue and sources weekly. A site that is fresh every day beats one that is perfect once.
5. **Don'ts**: no auto-published AI text, no copied articles, no cloaking, no keyword stuffing, no hidden text, no fake urgency. These risk manual actions and are against the site's own policy.

## Launch checklist (once, after deploying)

1. DNS: apex `A` record, plus a `www` `CNAME` to the apex (Caddy redirects www to the apex).
2. Google Search Console: add the **Domain** property (DNS TXT) or the URL-prefix property with `NEXT_PUBLIC_GSC_VERIFICATION`; submit `https://<domain>/sitemap.xml`; inspect the home page and one patch page with *URL Inspection -> Request indexing*.
3. Bing Webmaster Tools: *Import from Google Search Console* (or set `NEXT_PUBLIC_BING_VERIFICATION`), submit the sitemap.
4. IndexNow: `openssl rand -hex 16` -> `INDEXNOW_KEY` in `.env` (api + web), `make prod-up`, open `https://<domain>/indexnow.txt` (shows the key).
5. `NEXT_PUBLIC_SAME_AS`: official profile URLs (X, YouTube, GitHub...) once they exist, for Organization markup.
6. Analytics: set `NEXT_PUBLIC_PLAUSIBLE_DOMAIN`.
7. Run PageSpeed Insights on the home page, a game hub and a patch page (field data appears after real traffic). Targets: LCP < 2.5 s, CLS < 0.1, INP < 200 ms.
8. Validate markup once with Google's Rich Results Test on a patch page and a briefing.
9. Make sure real content exists before asking Google to index: placeholder games stay `noindex` until a sourced date/patch/requirement exists.

## Weekly (10-15 minutes, part of the RUNBOOK checklist)

* Search Console: *Pages* (is only the sitemap set indexed? any "Crawled - currently not indexed" patterns?), *Performance* (new queries -> make or improve the matching page), *Core Web Vitals*, *Manual actions*.
* Add the game spellings people actually search to `Game.aliases` and the FAQ in `hub_config`.
* Publish/approve the briefing drafts; each is a fresh, citable page.

## Measuring

Search Console (impressions, clicks, average position per query/page), Bing Webmaster Tools, Plausible (landing pages, referrers), PageSpeed Insights/CrUX (real-user Core Web Vitals). Expect a lag of days to weeks before new pages rank; rankings for competitive terms take months and depend on links and demonstrated accuracy.

## Automated checks

`apps/web/e2e/seo.spec.ts` (Playwright) crawls every sitemap URL and asserts: 200, title/description length, self-canonical, no `noindex`, OG/Twitter tags, share images resolve, exactly one H1, valid and honest JSON-LD (types allow-listed, required fields, citations), metadata inside `<head>` for a non-bot user agent, no sitemap entry blocked by robots.txt, RSS valid and only listing sitemap pages, real 404s. `apps/web/tests/seo.test.ts` unit-tests the title/description rules.
