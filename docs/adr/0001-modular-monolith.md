# ADR 0001: Modular monolith in a monorepo
Status: accepted
Context: one owner, 2-4 h/week, ~$15/month budget. Operational surface must be tiny.
Decision: one Django project with strictly layered modules, one Next.js app, shared packages. No microservices, no message bus beyond Celery/Redis.
Consequences: simple deploys (one compose file); boundaries enforced by convention + an architecture test, not by network.
