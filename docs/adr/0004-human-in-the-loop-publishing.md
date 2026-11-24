# ADR 0004: Auto-publish structured facts only
Status: accepted
Decision: only release dates, patch versions and requirements with a source URL, confidence >= threshold and verification >= Reported are auto-published. All prose (news) is reviewed by a human. Raw aggregate (`/feed`) is `noindex,nofollow`; placeholders are `noindex` until real content exists.
Consequences: avoids Google scaled-content-abuse risk; owner time is spent on a review queue (target: clear weekly).
