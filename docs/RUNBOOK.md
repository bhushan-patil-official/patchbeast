# Patchbeast runbook

Owner time budget: **2-4 hours/week**. Everything runs unattended; you review, check health and ship one social post.

## 0. What runs where

| Piece | Default | Notes |
|---|---|---|
| api, worker, beat, postgres, redis, caddy, backup | one small VPS (Hetzner CX22 ≈ $5-7/mo) | `docker-compose.prod.yml` |
| web (Next.js) | same VPS (Docker) **or** Vercel | see §7 |
| Email | Resend (or any SMTP provider) | `EMAIL_*` |
| LLM | Anthropic, Claude Haiku 5.5 | daily cap default $1 (≈ pennies in practice) |

## 1. First deploy (VPS)

1. Create the VPS (Ubuntu 24.04), add your SSH key, enable the provider firewall for ports 22, 80, 443.
2. Install Docker + compose plugin: `curl -fsSL https://get.docker.com | sh`.
3. Point DNS: `A` (and `AAAA`) for your domain to the VPS IP.
4. `git clone <repo> /opt/patchbeast && cd /opt/patchbeast`
5. `cp .env.example .env` and set at least:
   - `DJANGO_ENV=prod`, `DJANGO_SECRET_KEY` (`openssl rand -base64 48`), `DJANGO_ALLOWED_HOSTS=yourdomain,api`,
     `DJANGO_CSRF_TRUSTED_ORIGINS=https://yourdomain`
   - `SITE_URL` / `NEXT_PUBLIC_SITE_URL=https://yourdomain`, `DOMAIN=yourdomain`, `ACME_EMAIL`
   - `POSTGRES_PASSWORD` **and** the same password inside `DATABASE_URL`
   - `NEXT_PUBLIC_API_BASE_URL=` (empty: Caddy serves `/api` on the same origin)
   - `REVALIDATE_SECRET` (random), `ANTHROPIC_API_KEY`, `EMAIL_*`, `ALERT_EMAIL_TO` (and optionally Telegram)
   - optional: `YOUTUBE_API_KEY`, `SENTRY_DSN`, `METRICS_TOKEN`, `NEXT_PUBLIC_PLAUSIBLE_DOMAIN`, `NEXT_PUBLIC_GSC_VERIFICATION`
6. `make prod-up` (builds images, runs migrations on api start, starts Caddy with automatic TLS).
7. `docker compose -f docker-compose.yml -f docker-compose.prod.yml exec api python manage.py createsuperuser`
8. `docker compose -f docker-compose.yml -f docker-compose.prod.yml exec api python manage.py seed` (placeholder anchor + flags)
9. Sign in at `https://yourdomain/admin/`.
10. Uptime monitor (UptimeRobot/Better Stack, free): check `https://yourdomain/healthz` (expects 200, 503 on db/redis failure).
11. Search Console: add the property, put the token in `NEXT_PUBLIC_GSC_VERIFICATION`, `make prod-up`, verify, submit `https://yourdomain/sitemap.xml`.

### Add real sources (the seed ships disabled placeholders)

Admin → Sources → edit/add (always prefer official RSS/APIs; see each site's terms):

* **RSS/Atom**: type `rss`, URL = feed URL. Tick *official feed* only for feeds meant for machines (skips robots.txt check).
* **JSON API**: type `api`, config `{"items_path": "data.items", "title_field": "title", "url_field": "url", "date_field": "published", "lead_field": "summary"}`.
* **YouTube**: type `youtube`, config `{"channel_id": "UC…", "trusted_channel": false}`. Costs 1 quota unit per poll (search is never used). Set `trusted_channel: true` only for an official channel you trust to auto-publish videos.
* Untick *is placeholder*, tick *enabled*. Use the **Fetch now** action to test. Health shows in the list.

### Platforms, flagship page and per-game settings

* Admin → Games → *Hub config* (JSON): `{"platforms": ["pc", "ps5", "xbox_series"], "seo_title": "...", "seo_description": "...", "faq": [...]}`. Allowed platform ids: `pc`, `ps5`, `xbox_series`, `switch2`. PC always shows first. Add a *Release* row per platform (or let sourced facts create them).
* *Vanity path* (e.g. `gta-6-pc`) makes `/gta-6-pc` the canonical page; `/games/<slug>` redirects to it.
* Requirements and the PC checker stay PC-only. Console patches are tracked per platform (Admin → Patches → *platform*).
* After updating a running server: `git pull && make prod-up` (applies migrations), then `... exec api python manage.py seed` once to create the per-platform placeholder rows for the anchor (it overwrites the anchor's hub config).

### Load starter content (patches, release dates, news) from a content pack

A pack is a JSON file of sourced items (`apps/api/content_packs/`). The bundled `gta6` pack holds the launch releases, three reported updates (01.002.000 / .001 / .002) and two news items, every one linking its sources.

```bash
C="docker compose -f docker-compose.yml -f docker-compose.prod.yml"
$C exec api python manage.py load_pack gta6 --dry-run   # shows what it would create; saves nothing
$C exec api python manage.py load_pack gta6             # loads it (idempotent)
```

**Verify first.** The pack was compiled from search-result snippets; open each source and check dates, versions, sizes and wording (and the publisher's own support page for official notes) before loading. Afterwards edit or delete anything wrong in Admin → Patches / Releases / Articles. A page becomes indexable automatically once it has real, sourced content. To add your own pack, copy `gta6.json` and follow its structure.

### Game assignment, general feeds and curating a high volume

* **Aliases**: Admin -> Games -> *Aliases* (JSON list), e.g. `["GTA 6", "GTA VI", "Grand Theft Auto 6"]`. Add every spelling headlines use; they drive name matching and are sent to the model. (The `seed` command sets them for the anchor game.)
* **Game-specific feed**: set the Source's *game*. The source's game is trusted unless the model AND a name match point elsewhere.
* **General feed** (covers several games): leave the Source's *game* **empty**. Items are attached by name; unmatched/ambiguous ones show in the review queue under **Unassigned** with a game picker.
* **Review queue** (`/admin/review/`): filter chips per game (with counts) and *Unassigned*; pick/change the game on a card and approve in one click; tick cards (or `x`) and use **Merge into one briefing** (same game, 2+ outlets), **Approve as linked news**, or **Reject**.
* **Noise**: items the model is sure are not about a tracked game are rejected automatically (`RELEVANCE_REJECT_THRESHOLD`); they are kept in Admin -> Articles (filter *status = rejected*) if you need to check.
* **Roundups**: leftovers become one weekly roundup draft per game; clear it in the same queue under *Story drafts*.
* **Fix an existing backlog** (items stuck with "model could not assign a game"): `docker compose -f docker-compose.yml -f docker-compose.prod.yml exec api python manage.py reassign_games --dry-run`, then without `--dry-run`.
* **Posts page**: `/news` lists briefings/roundups then linked news, with a game filter.

### Automated briefings (story drafts)

Every 6 hours the system groups similar articles about the same development (needs two independent outlets) and drafts a short, cited briefing for your review. Nothing is published until you approve it.

* Turn off: Admin → Feature flags → `stories` (or `FEATURE_STORIES=false`). The kill switch and the daily LLM cap also stop it.
* Tune: `STORY_MAX_PER_DAY` (default 5), `STORY_SIMILARITY` (higher = stricter grouping), `STORY_WINDOW_DAYS`.
* Needs `ANTHROPIC_API_KEY` and articles that already have our summary (i.e. classified or edited items in the queue/published).
* Rejecting a draft frees its articles; the same group is not drafted again.

### Game sections

Each game has its own pages: Overview, Patches & updates (a page per update), News, Videos, PC requirements, Timeline. Patch highlights/size are edited in Admin → Patches. A patch page stays `noindex` until it has at least one source and a summary or highlights.

### Make a page indexable (placeholder → real)

Pages are `noindex` until they have real, sourced content. A hub becomes indexable automatically when it has a non-placeholder, Reported/Confirmed release date, requirements, patches, published videos or published news. Force noindex with *Game → allow index = off*.

### Email with Resend (newsletter + alerts)

1. Create a Resend account, **add and verify your domain** (it gives you SPF/DKIM DNS records; add them at your DNS provider and wait until Resend shows *Verified*). Add a DMARC `TXT` record at `_dmarc` too.
2. Create an API key (sending access) in Resend.
3. In `.env` on the server:
   ```
   EMAIL_HOST=smtp.resend.com
   EMAIL_PORT=587
   EMAIL_USE_TLS=true
   EMAIL_USE_SSL=false
   EMAIL_HOST_USER=resend
   EMAIL_HOST_PASSWORD=<your re_... API key>
   DEFAULT_FROM_EMAIL=Patchbeast <hello@yourdomain>
   ```
   (Implicit TLS alternative: `EMAIL_PORT=465`, `EMAIL_USE_TLS=false`, `EMAIL_USE_SSL=true`. Use 465 if your host blocks 587.)
4. `make prod-up`, then test: `docker compose -f docker-compose.yml -f docker-compose.prod.yml exec api python manage.py sendtestemail you@example.com`.
5. Check Resend's current plan limits (daily/monthly sends, rate): the digest sends one email per subscriber and is throttled to 60/min by the worker.

The `From` address must belong to the verified domain, otherwise Resend rejects the message. Mailpit remains the **dev-only** mail catcher (`docker-compose.dev.yml`); the prod stack has no Mailpit.

## 2. Updating

```bash
cd /opt/patchbeast && git pull && make prod-up   # rebuilds changed images, migrates, restarts
```

Check `docker compose ... ps` (all healthy) and `/healthz`.

## 3. Rollback

```bash
git log --oneline -n 10                 # pick the last good commit/tag
git checkout <good-sha> && make prod-up
```

Migrations are additive; if a bad migration ran, restore the nightly backup (§4) *then* check out the matching code.

## 4. Backups and restore

* A `backup` container runs `pg_dump | gzip` nightly (03:15 UTC) into `./backups/` and keeps `BACKUP_RETENTION_DAYS` (default 14).
* Manual dump: `make backup`.
* **Offsite copy (do this once):** install rclone on the host, `rclone config` a bucket (Backblaze B2 / Cloudflare R2 are cents per month), then add a host cron:
  `30 3 * * * rclone copy /opt/patchbeast/backups remote:patchbeast-backups --max-age 3d`
* **Restore:** `make restore FILE=backups/patchbeast-<timestamp>.sql.gz` (asks for `yes`, stops app services, loads the dump, restarts).
* Test a restore on a scratch VPS once per quarter.

## 5. Kill switch and alerts

* **Pause everything** (fetching, LLM calls, auto-publish): Admin → Site settings → *Kill switch*, or
  `make killswitch-on` / `make killswitch-off`. The site keeps serving existing content.
* Alerts arrive by email (`ALERT_EMAIL_TO`) and Telegram (`TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHAT_ID`), de-duplicated by `ALERT_COOLDOWN_MINUTES`:
  fetcher failing (and auto-disabled), LLM spend ≥ 90%/breach, 5xx spike, revalidation failing, task dead-letters.
* Admin → Alert events shows history. Optional Prometheus-style `/metrics` with `Authorization: Bearer $METRICS_TOKEN`.

## 6. Weekly checklist (2-4 h)

1. **Review queue (30-90 min)**: `/admin/review/` (articles, **story drafts**, videos). For each story draft open the numbered sources and check every claim against them; edit paragraphs freely (citations stay attached); reject anything you can't verify. Keys: `j/k` move, `e` edit, `a` approve, `r` reject, `s` save. Write/keep *our* summary only. Check the "why queued" reason. Reject duplicates and rumours you can't source.
2. **Fetcher health (10 min)**: Admin → Sources, sort by health. Fix/replace failing feeds. Admin → Fetch logs for anomalies.
3. **Spend (5 min)**: Admin → Site settings and LLM usage. Raise/lower `daily_llm_cap` if needed.
4. **Alerts (5 min)**: skim Alert events; clear root causes.
5. **Facts (10 min)**: Admin → Releases/Patches/Requirements: anything auto-published looks right? Add Evidence rows for items that deserve *Confirmed*; map `cpu_ref`/`gpu_ref` on requirements so the checker can compare.
6. **Search Console (15 min)**: coverage (are only curated/tool pages indexed?), queries, Core Web Vitals report, manual actions.
7. **Weekly digest**: sent automatically Monday 08:00 UTC (only if there were confirmed changes). Check Admin → Digest runs.
8. **One social update (15 min)**: post the biggest confirmed change with its source link.
9. **Backups (2 min)**: confirm a fresh file exists in `backups/` and the offsite copy ran.

## 7. Optional: web on Vercel

Keep api/worker/beat/postgres/redis on the VPS; deploy only the Next.js app to Vercel.

1. Import the repo in Vercel. Either:
   * **Root Directory = repo root** (uses `/vercel.json`: install `npm ci`, build `npm run build -w apps/web`, output `apps/web/.next`), or
   * **Root Directory = `apps/web`** with *Include source files outside of the Root Directory* enabled (uses `apps/web/vercel.json`).
2. Environment variables (Production): `NEXT_PUBLIC_API_BASE_URL=https://api.yourdomain` (public API origin; also used server-side), `NEXT_PUBLIC_SITE_URL=https://yourdomain`, `REVALIDATE_SECRET` (same as the API), plus the optional `NEXT_PUBLIC_*` analytics/GSC vars. **Do not** set `BUILD_STANDALONE`.
3. On the VPS set `REVALIDATE_URL=https://yourdomain/internal/revalidate` and `CORS_ALLOWED_ORIGINS=https://yourdomain`, and expose the API host (add a Caddy site block for `api.yourdomain` → `api:8000`).
4. The first build works even if the API is unreachable (pages show a "temporarily unavailable" state and refresh via ISR).

## 8. Troubleshooting

| Symptom | Check |
|---|---|
| Items stuck in "new" | worker unhealthy or kill switch on; `ingest.requeue_stuck` moves them to review after 30 min |
| Everything lands in review with "LLM unavailable" | `ANTHROPIC_API_KEY` missing, spend cap reached, or kill switch on |
| Publish doesn't show on site | worker `publish` queue; `REVALIDATE_URL`/`REVALIDATE_SECRET` mismatch (alert fires after retries); pages self-heal within 5 min anyway |
| 502 from Caddy | `docker compose ps`; api healthcheck; `logs api` (JSON logs carry `request_id`) |
| Source "failing" | Admin → Sources → *last error*; 404/410 auto-disables after two tries |
