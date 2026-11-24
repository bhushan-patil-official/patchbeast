import { SignalMeter, SourceChip } from "@patchbeast/design-system";
import type { Schemas } from "@/lib/api";

const fmt = (d: string) =>
  new Intl.DateTimeFormat("en", { year: "numeric", month: "short", day: "2-digit", timeZone: "UTC" }).format(new Date(`${d}T00:00:00Z`));

/** One row per tracked platform (PC first). A date is only shown when it is Reported/Confirmed and sourced. */
export function PlatformReleases({
  releases,
  platforms,
  compact,
}: {
  releases: Schemas["Release"][];
  platforms: Schemas["Platform"][];
  compact?: boolean;
}) {
  if (platforms.length <= 1) return null;
  return (
    <ul className={compact ? "space-y-1.5" : "divide-y divide-line rounded-lg border border-line bg-surface-1"} aria-label="Release status by platform">
      {platforms.map((p) => {
        const r = releases.find((x) => x.platform === p.id);
        const live = r?.countdown_mode === "live" && r.date;
        return (
          <li
            key={p.id}
            data-testid={`platform-release-${p.id}`}
            className={compact ? "flex items-center justify-between gap-2 text-sm" : "flex flex-wrap items-center justify-between gap-3 px-4 py-3"}
          >
            <span className="font-display font-medium">{p.name}</span>
            <span className="flex flex-wrap items-center gap-2">
              {live ? (
                <time dateTime={r!.date!} className="font-mono text-sm">{fmt(r!.date!)}</time>
              ) : (
                <span className="font-mono text-xs uppercase tracking-wider text-signal-rumour">Date unconfirmed</span>
              )}
              <SignalMeter level={r?.confidence ?? "rumour"} sources={compact ? undefined : r?.source_count} size="sm" />
              {!compact && r?.source_url && <SourceChip url={r.source_url} />}
            </span>
          </li>
        );
      })}
    </ul>
  );
}
