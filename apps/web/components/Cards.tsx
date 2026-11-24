import Link from "next/link";
import { Card, Countdown, SignalMeter, SourceChip, type ChangeEntry, type SpecTier } from "@patchbeast/design-system";
import type { Schemas } from "@/lib/api";
import { platformShort } from "@/lib/platforms";
import { PlatformReleases } from "./PlatformReleases";

export const toEntry = (c: Schemas["Change"]): ChangeEntry => ({
  id: c.id,
  title: c.title,
  detail: c.detail,
  versionLabel: c.version_label,
  occurredAt: c.occurred_at,
  sourceUrl: c.source_url || undefined,
  verification: c.verification,
});

export function GameLaunchCard({ g }: { g: Schemas["GameCard"] }) {
  const r = g.release;
  const multi = g.platforms.length > 1;
  return (
    <Card className="group relative flex flex-col p-5 transition-shadow hover:shadow-glow" data-testid="launch-card">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="font-mono text-[11px] uppercase tracking-[0.18em] text-accent-text">{multi ? "Launch · PC first" : "PC launch"}</p>
          <h3 className="font-display text-xl font-semibold">
            {/* stretched link: the whole card is clickable; inner links sit above it (z-10) */}
            <Link href={g.path} className="pb-focus rounded after:absolute after:inset-0 after:content-[''] group-hover:text-accent-text">{g.name}</Link>
          </h3>
          {g.tagline && <p className="mt-1 text-sm text-fg-muted">{g.tagline}</p>}
        </div>
        {r && <SignalMeter level={r.confidence} sources={r.source_count} size="sm" />}
      </div>
      <div className="my-6">
        {multi && r && <p className="mb-2 text-center font-mono text-[10px] uppercase tracking-[0.2em] text-fg-muted">{platformShort(r.platform)} release</p>}
        <Countdown target={r?.date ?? null} mode={r?.countdown_mode ?? "unconfirmed"} />
        {r?.source_url && <div className="relative z-10 mt-3 flex justify-center"><SourceChip url={r.source_url} /></div>}
      </div>
      {multi && <div className="mb-4"><PlatformReleases releases={g.releases} platforms={g.platforms} compact /></div>}
      <div className="mt-auto border-t border-line pt-3">
        <h4 className="font-mono text-[11px] uppercase tracking-[0.18em] text-fg-muted">Latest confirmed changes</h4>
        {g.latest_changes.length ? (
          <ul className="mt-2 space-y-1.5 text-sm">
            {g.latest_changes.map((c) => (
              <li key={c.id} className="flex gap-2"><span className="text-signal-confirmed" aria-hidden="true">●</span><span>{c.title}</span></li>
            ))}
          </ul>
        ) : (
          <p className="mt-2 text-sm text-fg-muted">Nothing confirmed yet. We only list changes with sources.</p>
        )}
        <p className="mt-4 text-sm font-medium text-accent-text">View tracker <span aria-hidden="true">→</span></p>
      </div>
    </Card>
  );
}

export function NewsCard({ a, showStatus }: { a: Schemas["Article"]; showStatus?: boolean }) {
  return (
    <Card className="p-4">
      <div className="flex flex-wrap items-center gap-2">
        <SignalMeter level={a.verification} size="sm" />
        <span className="font-mono text-xs text-fg-muted">{a.game_name}</span>
        {showStatus && <span className="rounded border border-line px-1.5 font-mono text-[10px] uppercase text-fg-muted">{a.status}</span>}
        {a.published_at && <time dateTime={a.published_at} className="font-mono text-xs text-fg-muted">{a.published_at.slice(0, 10)}</time>}
      </div>
      <h3 className="mt-2 font-display text-lg font-semibold">{a.title}</h3>
      {a.our_summary && <p className="mt-1 text-sm text-fg-muted">{a.our_summary}</p>}
      <div className="mt-3 flex flex-wrap items-center gap-2">
        <SourceChip url={a.source_url} name={a.source_name || undefined} nofollow={!!showStatus} />
        {a.tags.map((t) => <span key={t} className="rounded bg-surface-2 px-1.5 py-0.5 font-mono text-[10px] text-fg-muted">#{t}</span>)}
      </div>
    </Card>
  );
}

export function Degraded({ what }: { what: string }) {
  return (
    <p role="status" className="rounded border border-line bg-surface-1 p-4 text-sm text-fg-muted">
      {what} is temporarily unavailable. This page refreshes automatically; please check back soon.
    </p>
  );
}

export function PlaceholderNotice({ show }: { show: boolean }) {
  if (!show) return null;
  return (
    <p role="note" className="mb-6 rounded border border-signal-reported/50 bg-surface-1 p-3 text-sm">
      <strong className="font-semibold text-signal-reported">Placeholder page.</strong>{" "}
      <span className="text-fg-muted">Nothing here has been verified yet, so this page is hidden from search engines until real, sourced content exists.</span>
    </p>
  );
}

export const toTier = (t: Schemas["Requirement"] | undefined): SpecTier | null =>
  t ? { os: t.os, cpu: t.cpu, gpu: t.gpu, ramGb: t.ram_gb, storageGb: t.storage_gb, verification: t.verification, sources: t.source_count, sourceUrl: t.source_url || undefined, placeholder: t.is_placeholder } : null;

