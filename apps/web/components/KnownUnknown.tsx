import { SignalMeter, Section } from "@patchbeast/design-system";
import type { Schemas } from "@/lib/api";

type Item = { key: string; text: string; level?: Schemas["VerificationEnum"] };

/**
 * "What we know / what we don't": derived ONLY from sourced data in the hub payload.
 * It never states anything we can't source; gaps are shown openly.
 */
export function KnownUnknown({ h }: { h: Schemas["Hub"] }) {
  const known: Item[] = [];
  const unknown: Item[] = [];
  const multi = h.platforms.length > 1;

  for (const p of h.platforms) {
    const r = h.releases.find((x) => x.platform === p.id);
    const label = multi ? `${p.name} release date` : "Release date";
    if (r && r.countdown_mode === "live" && r.date) known.push({ key: `rel-${p.id}`, text: `${label}: ${r.date}`, level: r.confidence });
    else unknown.push({ key: `rel-${p.id}`, text: label });
  }

  const realReqs = h.requirements.filter((x) => !x.is_placeholder && (x.cpu || x.gpu));
  if (h.checker_enabled || realReqs.length) {
    if (realReqs.length) known.push({ key: "req", text: `PC system requirements (${realReqs.map((x) => (x.tier === "min" ? "minimum" : "recommended")).join(" + ")})`, level: realReqs.every((x) => x.verification === "confirmed") ? "confirmed" : "reported" });
    else unknown.push({ key: "req", text: "PC system requirements" });
  }

  const patches = h.patches.filter((p) => !p.is_placeholder);
  if (patches.length) known.push({ key: "patch", text: `${patches.length}${h.patches.length >= 6 ? "+" : ""} patch${patches.length === 1 ? "" : "es"} tracked`, level: patches[0].verification });
  else unknown.push({ key: "patch", text: "Patch notes (none released or tracked yet)" });

  if (h.videos.length) known.push({ key: "vid", text: `${h.videos.length} video${h.videos.length === 1 ? "" : "s"} linked`, level: "confirmed" });
  else unknown.push({ key: "vid", text: "Official trailers or videos" });

  return (
    <Section eyebrow="At a glance" title="What we know, and what we don't" id="glance">
      <div className="grid gap-4 md:grid-cols-2" data-testid="known-unknown">
        <div className="rounded-lg border border-line bg-surface-1 p-4">
          <h3 className="font-mono text-xs uppercase tracking-[0.18em] text-signal-confirmed">Known (with sources)</h3>
          {known.length ? (
            <ul className="mt-3 space-y-2 text-sm">
              {known.map((i) => (
                <li key={i.key} className="flex flex-wrap items-center gap-2">
                  <span>{i.text}</span>
                  {i.level && <SignalMeter level={i.level} size="sm" />}
                </li>
              ))}
            </ul>
          ) : (
            <p className="mt-3 text-sm text-fg-muted">Nothing verified yet. We only list what has a source.</p>
          )}
        </div>
        <div className="rounded-lg border border-line bg-surface-1 p-4">
          <h3 className="font-mono text-xs uppercase tracking-[0.18em] text-signal-rumour">Not known yet</h3>
          {unknown.length ? (
            <ul className="mt-3 space-y-2 text-sm text-fg-muted">
              {unknown.map((i) => (
                <li key={i.key} className="flex gap-2"><span aria-hidden="true">○</span><span>{i.text}</span></li>
              ))}
            </ul>
          ) : (
            <p className="mt-3 text-sm text-fg-muted">Everything we track has a sourced answer.</p>
          )}
        </div>
      </div>
    </Section>
  );
}
