# ADR 0007: Single VPS for everything; optional Vercel for the web app
Status: accepted
Decision: default deployment is one small VPS (Docker Compose + Caddy). The Next.js app can alternatively be deployed to Vercel (`vercel.json`) while the API/worker/beat stay on the VPS; in that mode `API_INTERNAL_URL` / `NEXT_PUBLIC_API_BASE_URL` point at the public API origin and `REVALIDATE_URL` at the Vercel deployment.
