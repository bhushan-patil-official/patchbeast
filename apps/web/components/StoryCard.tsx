import Link from "next/link";
import { Card, SignalMeter } from "@patchbeast/design-system";
import type { Schemas } from "@/lib/api";

/** A briefing we wrote from 2+ linked sources (human-reviewed). */
export function StoryCard({ s }: { s: Schemas["StoryCard"] }) {
  return (
    <Card className="group relative p-4 transition-shadow hover:shadow-glow" data-testid="story-card">
      <div className="flex flex-wrap items-center gap-2">
        <span className="rounded border border-accent/50 bg-accent/10 px-1.5 py-0.5 font-mono text-[10px] uppercase tracking-wider text-accent-text">{s.kind === "roundup" ? "Roundup" : "Briefing"}</span>
        <SignalMeter level={s.verification} sources={s.source_count} size="sm" />
        <span className="font-mono text-xs text-fg-muted">{s.game_name}</span>
        {s.published_at && <time dateTime={s.published_at} className="font-mono text-xs text-fg-muted">{s.published_at.slice(0, 10)}</time>}
      </div>
      <h3 className="mt-2 font-display text-lg font-semibold">
        <Link href={`/games/${s.game_slug}/news/${s.slug}`} className="pb-focus rounded after:absolute after:inset-0 after:content-[''] group-hover:text-accent-text">{s.title}</Link>
      </h3>
      {s.dek && <p className="mt-1 text-sm text-fg-muted">{s.dek}</p>}
    </Card>
  );
}
