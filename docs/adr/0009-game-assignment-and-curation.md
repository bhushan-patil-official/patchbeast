# ADR 0009: Game assignment rules and volume curation
Status: accepted

Context: many articles arrive; some could not be attached to a game ("model could not assign a game"). Cause: the classifier's `game_slug` was treated as authoritative, so an unsure (`null`) or disagreeing answer overrode what the source already told us and queued the item. There was no way to assign a game in review, and a feed covering several games could not be modelled.

Decision:
- **Order of trust** (`ingest.services.resolve_game`): model + name match agree > the source's own game > the model alone > a single clear name match > unassigned. A `null` model answer never overrides the source. A model that disagrees with the source *without* name evidence keeps the source's game and leaves a note.
- **Names**: `Game.aliases` (+ the game name, minus a "(PC)" suffix) are matched as whole words, counting distinct mentions. Aliases are also sent to the model in the prompt.
- **General feeds**: `Source.game` and `Article.game` are nullable. A general source's items are attached by name at ingest; ambiguous or unmatched items stay *unassigned* and are fixed with a game picker in review. Approving requires a game. Exact-URL dedupe is global.
- **Relevance**: the classifier also returns `relevant`. A confident (>= `RELEVANCE_REJECT_THRESHOLD`) "not about a tracked game" with no name match is auto-rejected (kept, never deleted).
- **Curation at volume**: the review queue filters by game / unassigned and has bulk actions (reject, approve as linked news, merge selected into ONE briefing). Leftover articles that no briefing covers become at most one weekly *roundup* per game. Publishing stays human (ADR 0008).
- **Public**: `/news` shows briefings/roundups first, then linked news, filterable by game; filtered views are `noindex`.

Consequences: fewer items stuck in review for the wrong reason; one consolidated post per game per development or week; a one-off `manage.py reassign_games` repairs an existing backlog.
