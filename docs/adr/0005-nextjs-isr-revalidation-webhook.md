# ADR 0005: Next.js ISR with backend revalidation webhook
Status: accepted
Decision: pages are server-rendered with time-based ISR as a safety net plus tag/path revalidation triggered by the API on publish (`transaction.on_commit` -> Celery `publish` queue -> `POST /internal/revalidate`, shared secret, retried with backoff).
Consequences: fast CDN-cacheable pages, content live within seconds of approval, no client-side data fetching for indexable content.
