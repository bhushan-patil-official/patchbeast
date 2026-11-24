# Patchbeast

**patchbeast.com**: a PC-first launch tracker and tools site for huge game launches (first anchor: Grand Theft Auto VI on PC).
It is a **tracker and tools site, not a scraper or republisher**: we store a title, the source URL, *our own* 2-3 line summary and tags, and always link and attribute the source.

* Verification you can see: **Confirmed** (two independent sources or a video) · **Reported** (one source) · **Rumour**.
* Release status **per platform** (PC first, plus PS5 / Xbox Series), patches per platform, PC-only requirements and checker.
* Each game has its own pages: overview, patches & updates (a page per update, with highlights, size and sources), news, videos, PC requirements and a full timeline.
* **Curation at volume**: reliable game assignment (aliases, general feeds, relevance filter), a review queue filtered by game with bulk actions, weekly roundups, and a `/news` page filterable by game.
* **Briefings**: similar reports are grouped automatically and an original, cited write-up is drafted for you to approve in one click (never auto-published).
* A flagship page per game with a short URL (e.g. `/gta-6-pc`): countdown, per-platform dates, "what we know / what we don't", FAQ, per-game email signup.
* A countdown that never lies: it freezes to *Date unconfirmed* for rumours and placeholders.
* Raw feeds and placeholder pages are `noindex`; only curated and tool pages are indexable.
* Built to run unattended (2-4 h/week owner time): review queue, alerts, daily LLM spend cap, kill switch, nightly backups.

## Quickstart

```bash
cp .env.example .env
make dev            # postgres, redis, api, worker, beat, web (hot reload), mailpit
make seed           # placeholder anchor + flags   (make seed-demo adds clearly-labelled DEMO content)
make createsuperuser
```

* Site <http://localhost:3000> · API <http://localhost:8000/api/v1/> · OpenAPI <http://localhost:8000/api/schema/> · Admin <http://localhost:8000/admin/> (review queue at `/admin/review/`) · Mailpit <http://localhost:8025>
* `make test` (pytest + tsc + vitest in containers) · `make lint` · `make e2e` (Playwright) · `make schema` (regenerate OpenAPI + typed client; CI fails on drift)
* `npm run storybook` for the design system. Production: `make prod-up` (see [docs/RUNBOOK.md](docs/RUNBOOK.md)).

## Documentation

| Doc | What |
|---|---|
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) + [docs/adr/](docs/adr) | modules, layering, ports/adapters, pipeline, safeguards |
| [docs/RUNBOOK.md](docs/RUNBOOK.md) | first deploy, updates, rollback, backups/restore, kill switch, **weekly 2-4 h checklist**, Vercel option |
| [docs/DESIGN_SYSTEM.md](docs/DESIGN_SYSTEM.md) | tokens, components, motion, accessibility, budgets |
| [DECISIONS.md](DECISIONS.md) | autonomous decisions and assumptions |

## Layout

`apps/api` Django modular monolith (`modules/{games,sources,ingest,content,review,newsletter,platform}`, `llm/`) ·
`apps/web` Next.js App Router (ISR) · `packages/design-system` · `packages/api-client` (generated) · `infra/` · `docs/`.

## What needs your keys / credentials (all in `.env.example`)

| Variable | Needed for |
|---|---|
| `ANTHROPIC_API_KEY` (+ `LLM_DAILY_CAP_USD`) | classification + summaries. Without it everything is queued for human review. |
| `YOUTUBE_API_KEY` | YouTube sources (optional; 1 quota unit per poll, never `search`) |
| `EMAIL_*`, `DEFAULT_FROM_EMAIL` | newsletter + alert emails (Mailpit in dev) |
| `ALERT_EMAIL_TO`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` | alerts |
| `DJANGO_SECRET_KEY`, `POSTGRES_PASSWORD`, `REVALIDATE_SECRET`, `DOMAIN`, `ACME_EMAIL`, `SITE_URL` | production |
| `NEXT_PUBLIC_PLAUSIBLE_DOMAIN`, `NEXT_PUBLIC_GSC_VERIFICATION` | analytics / Search Console |
| `NEXT_PUBLIC_ADSENSE_CLIENT`/`SLOT` + flag `ads`; `apps/web/data/affiliate.ts` + flag `affiliate` | monetisation (nothing is live until configured) |
| `SENTRY_DSN`, `METRICS_TOKEN` | optional observability |

Real source feeds (official RSS/APIs/YouTube channel ids) must be entered by you in Admin → Sources; the seed contains disabled placeholders only.

## Status and known gaps

See the final report in the PR / session notes, and "Known gaps" below.

**Verified in the build sandbox:** backend (89 pytest tests, ruff, black, mypy), design system (typecheck, 62 WCAG token tests, Storybook build), web (eslint, tsc, vitest, production build with the API both reachable and unreachable), 11 Playwright smoke tests against a native Django + Next stack, a real Celery worker + RSS fetch through the pipeline, ISR revalidation webhook, `docker compose config` for dev and prod.

**Known gaps**
* The sandbox had no Docker daemon: **images were not built and `make dev` / `make prod-up` were not run here.** Compose files and Dockerfiles are validated statically (`docker compose config`) and mirror the natively-tested stack; CI (`.github/workflows/ci.yml`) builds the images and runs a compose + Playwright smoke job. Expect to fix small first-run issues.
* LLM calls were tested only through the fake adapter and a mocked SDK path; run one real classification with your key (RUNBOOK) before trusting auto-publish.
* The hardware tier catalogue is hand-maintained and approximate (clearly caveated in the UI); requirement rows need `cpu_ref`/`gpu_ref` mapped in admin for automatic comparison.
* No real sources, requirements or release dates are shipped (by design: placeholders only).
* OG images use the default system font; legal pages are templates needing legal review.
* Lighthouse/Core Web Vitals were not measured in the sandbox (first-load JS on the hub is ~141 KB by build output).
