# Patchbeast architecture

Patchbeast is a PC-first launch tracker and tools site. It is a **tracker, not a scraper or republisher**: we store a title, the source URL, our own 2-3 line summary and tags, and always link and attribute the source.

## Style

Modular monolith in a monorepo, strict boundaries, no microservices. Every module is replaceable and testable alone.

```
patchbeast/
  apps/
    api/            Django project (settings split: base/dev/prod/test)
      modules/
        games/      Game, Release, hub config            (domain + services + selectors + api)
        sources/    Source registry, fetchers (adapters)
        ingest/     Fetch -> normalise -> dedupe -> classify -> queue
        content/    Article, Patch, Requirement, Video, Evidence, Change, publish rules
        review/     Review queue + admin views
        newsletter/ Subscribers, double opt-in, digest
        platform/   Kill switch, spend caps, alerts, health, revalidation, feature flags
      llm/          Provider-agnostic LLM port + Anthropic adapter + fake
    web/            Next.js (App Router, TS, ISR)
  packages/
    design-system/  Tokens + UI components + Storybook
    api-client/     Typed client generated from the OpenAPI schema
  infra/            docker/, caddy, scripts
  docs/             ARCHITECTURE.md, adr/, RUNBOOK.md, DESIGN_SYSTEM.md
```

## Layering inside a module

`models` -> `services` (writes, business rules) -> `selectors` (reads) -> `api` (DRF serializers/views).

* Views never contain business logic.
* Cross-module calls go through the other module's `services`/`selectors`/`ports` only. Another module's `models` are never imported into views.
  Foreign keys between models are allowed (they are data, not behaviour); `tests/test_architecture.py` enforces the view rule and the import direction below.
* Allowed dependency direction: `platform` <- everything; `games` <- `sources`, `content`; `content` <- `ingest`, `review`, `newsletter`; `llm` has no Django-model dependencies except via the spend-guard in `platform`.

## Ports and adapters

| Port | Adapters |
|---|---|
| `SourceFetcher` (`modules/sources/ports.py`) | `RssFetcher`, `JsonApiFetcher`, `YouTubeFetcher`, `WebSubFetcher` (receiver) |
| `LLMClient` (`llm/ports.py`) | `AnthropicClient`, `FakeLLMClient` |
| `Notifier` (`modules/platform/notifiers.py`) | `EmailNotifier`, `TelegramNotifier`, `LogNotifier` |
| `Mailer` (`modules/newsletter/mailer.py`) | `DjangoMailer` (SMTP; Mailpit in dev), `MemoryMailer` |

Adding a source type or swapping a provider never touches domain code: register a new class in the registry.

## Game-as-config

A game or launch is data: `Game` + `Source` rows + `hub_config` JSON (tracked platforms, FAQ, SEO copy, sections) + an optional `vanity_path` for a flagship short URL. Page templates are generic and driven by that config. No game name appears in code.

## Pipeline

```
beat (every minute) -> ingest.poll_due_sources -> ingest.fetch_source(source_id)   [queue ingest]
   conditional GET (ETag / If-Modified-Since), robots + ToS aware, per-source backoff
 -> normalise URL -> exact dedupe (canonical_url) -> near-dup (64-bit simhash, hamming <= 3)
 -> Article(status=new) -> ingest.classify_article(article_id)                      [queue llm]
   kill switch + daily spend cap -> LLMClient -> pydantic schema validate (retry once, else review)
 -> publish rules (content.services.apply_publish_rules):
      structured fact + source URL + confidence >= threshold + verification >= reported  -> auto-publish fact
      everything else                                                                   -> status=queued (review)
 -> review (Django admin custom view, keyboard friendly): approve / reject / edit
 -> on publish: transaction.on_commit -> publish.revalidate (Next ISR webhook)           [queue publish]
```

Story drafting (ADR 0008): `llm.build_stories` (beat, every 6 h) -> cluster similar articles (>= 2 independent domains) -> `llm/writer.py` drafts an original, cited briefing from OUR summaries and verified facts -> `Story(status=draft)` -> human approval in the review queue -> publish + revalidation. No auto-publish of prose.

Verification model (`content.services.verification`): **Confirmed** = two independent sources (distinct registrable domains) or a video; **Reported** = one linked source; **Rumour/Unverified** = anything else. Evidence rows are generic (`subject_kind` + `subject_id`), so later tiers attach evidence without schema changes to Phase 1 tables.

## Safeguards

* Global kill switch (`SiteSetting.kill_switch`, `manage.py killswitch on|off`): fetching, LLM and auto-publish stop; the read API keeps serving.
* Daily LLM spend cap enforced before every call (`SpendGuard`); breach alerts once per day.
* Per-source exponential backoff on failures; `Source.health` (ok/degraded/failing); auto-disable after N days failing.
* Alerts through `Notifier` (email and/or Telegram) with cooldown on fetcher failures, spend breach and 5xx rate.
* `/healthz` for uptime monitoring (db + redis + kill switch state).

## Frontend

Next.js App Router, server-rendered with ISR (`revalidate` + tags). The backend calls `POST /internal/revalidate` on publish with a shared secret. The API client is generated from the OpenAPI schema; CI fails on drift. Indexing policy comes from the API (`indexable` per page) so placeholder or raw pages are always `noindex`.

## Runtime topology

`postgres`, `redis`, `api` (gunicorn), `worker` (queues ingest,llm,publish,mail), `beat`, `web` (Next standalone), `caddy` (prod TLS), `mailpit` (dev), `backup` (prod nightly pg_dump). Caddy routes `/api /admin /static /hooks /healthz /metrics` to the API and everything else to Next.

## Extending (Phase 2/3)

New module = new Django app under `modules/` with its own tables (FK to `games.Game` only), its own feature flag (`platform.FeatureFlag`), its own router mounted in `patchbeast/urls.py`. No migrations to Phase 1 tables are required.
