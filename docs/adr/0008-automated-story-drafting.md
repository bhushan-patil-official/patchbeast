# ADR 0008: Automated story drafting, human-published
Status: accepted

Context: we want original write-ups ("briefings") that synthesise several reports of the same development, and we want the work automated. Risks: Google's scaled-content-abuse policy, hallucinated facts, republishing source text, and our own rule that prose is reviewed by a person (ADR 0004, ADR 0003).

Decision:
- **Automate the drafting, not the publishing.** A beat job (`llm.build_stories`, every 6 h) clusters similar articles (TF-IDF cosine over *our own* titles + summaries, no ML dependency) and asks the LLM for one briefing per cluster. The result is a `Story` in status `draft`. A person approves it in the review queue (edit / approve / reject, one click). There is no auto-publish path for prose.
- **Inputs are our data only**: our stored summaries plus verified timeline facts. Source page text is never fetched or stored.
- **A cluster needs >= 2 independent outlets** (registrable domains), so a single report is never reworded into a "story".
- **Grounding is enforced in code** (`llm/writer.py`): every paragraph cites valid items and the briefing cites >= 2; every number/version/date must appear in the inputs; no 8-word run copied from an input; no clickbait vocabulary; 80-380 words; one retry with the error fed back, then no draft.
- **Safeguards**: `stories` feature flag, global kill switch, daily LLM spend cap (SpendGuard), `STORY_MAX_PER_DAY` / per-run caps.
- **Transparency**: each page carries a disclosure (AI-drafted from our summaries of the linked reports, approved by a person), numbered citations, a Sources list, and `NewsArticle` JSON-LD with `citation` links, emitted only when the page is indexable.
- Rejecting a story frees its articles; the same cluster is never re-drafted (unique cluster key per game).

Consequences: more useful, citable content at near-zero marginal owner time (one extra queue to clear), without the risk profile of auto-published AI text. Auto-publish of prose remains explicitly out of scope; revisit only with measured accuracy data.
