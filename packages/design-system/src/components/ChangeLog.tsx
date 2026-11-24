import * as React from "react";
import { cn } from "../lib/cn";
import type { Verification } from "../lib/verification";
import { SignalMeter } from "./SignalMeter";
import { SourceChip } from "./SourceChip";

export interface ChangeEntry {
  id: string | number;
  title: string;
  detail?: string;
  versionLabel?: string;
  kind?: string;
  occurredAt: string;
  sourceUrl?: string;
  verification: Verification;
  gameName?: string;
}

/** Renders "a -> b" details as a diff (old struck through, new highlighted). */
function Detail({ text }: { text: string }) {
  const m = text.match(/^(.*?)\s*->\s*(.*)$/);
  if (!m) return <p className="text-sm text-fg-muted">{text}</p>;
  return (
    <p className="font-mono text-sm">
      <span className="text-signal-alert/90 line-through decoration-1">{m[1] || "none"}</span>
      <span className="px-1.5 text-fg-muted" aria-label="changed to">
        →
      </span>
      <span className="text-signal-confirmed">{m[2]}</span>
    </p>
  );
}

const fmt = (iso: string) =>
  new Intl.DateTimeFormat("en", { year: "numeric", month: "short", day: "2-digit", timeZone: "UTC" }).format(new Date(iso));

export function ChangeLog({ entries, className }: { entries: ChangeEntry[]; className?: string }) {
  if (entries.length === 0) {
    return <p className="text-sm text-fg-muted">No changes recorded yet. Nothing is shown without a source.</p>;
  }
  return (
    <ol className={cn("relative space-y-5 border-l border-line pl-6", className)} aria-label="Change log">
      {entries.map((e) => (
        <li key={e.id} className="relative">
          <span
            aria-hidden="true"
            className="absolute -left-[1.85rem] top-1.5 h-2.5 w-2.5 rounded-full border-2 border-bg bg-accent"
          />
          <div className="flex flex-wrap items-center gap-2">
            {e.versionLabel && (
              <span className="rounded border border-accent/50 bg-accent/10 px-1.5 py-0.5 font-mono text-xs text-accent-text">
                v{e.versionLabel}
              </span>
            )}
            <h3 className="font-display text-base font-semibold">{e.title}</h3>
            <time dateTime={e.occurredAt} className="font-mono text-xs text-fg-muted">
              {fmt(e.occurredAt)}
            </time>
          </div>
          {e.detail && <div className="mt-1">{<Detail text={e.detail} />}</div>}
          <div className="mt-2 flex flex-wrap items-center gap-2">
            <SignalMeter level={e.verification} size="sm" />
            {e.sourceUrl && <SourceChip url={e.sourceUrl} />}
          </div>
        </li>
      ))}
    </ol>
  );
}
