# ADR 0003: Never republish source text
Status: accepted
Decision: persist only title, source URL, canonical URL, our own 2-3 line summary, tags, and a 64-bit simhash of title+lead (not reversible). The feed lead is passed to the LLM transiently and never stored. The summary prompt demands original wording; the validator rejects summaries with long verbatim overlap with the lead (>= 8 consecutive words).
Consequences: legal/SEO posture of "tracker with attribution"; no scraped-content storage; every item shows source + verification status.
