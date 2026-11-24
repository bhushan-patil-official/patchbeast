"use client";
import { useMemo, useState } from "react";
import { Card, SignalMeter } from "@patchbeast/design-system";
import { CPUS, GPUS, RAM_OPTIONS } from "@/data/hardware";
import { compareTier, OVERALL_COPY, overall, type PartStatus } from "@/lib/checker";
import type { Schemas } from "@/lib/api";

const ICON: Record<PartStatus, string> = { pass: "✓ Pass", fail: "✗ Below", unknown: "? Unknown" };
const COLOR: Record<PartStatus, string> = { pass: "text-signal-confirmed", fail: "text-signal-alert", unknown: "text-fg-muted" };

const selectCls = "h-10 w-full rounded border border-line bg-surface-2 px-3 text-sm text-fg";

export function RequirementsChecker({ min, rec }: { min?: Schemas["Requirement"]; rec?: Schemas["Requirement"] }) {
  const [cpu, setCpu] = useState("");
  const [gpu, setGpu] = useState("");
  const [ram, setRam] = useState("");
  const published = !!(min && !min.is_placeholder) || !!(rec && !rec.is_placeholder);

  const result = useMemo(() => {
    const pc = { cpu: cpu || undefined, gpu: gpu || undefined, ramGb: ram ? Number(ram) : undefined };
    const m = compareTier(pc, min && !min.is_placeholder ? min : undefined);
    const r = compareTier(pc, rec && !rec.is_placeholder ? rec : undefined);
    return { m, r, o: overall(m, r) };
  }, [cpu, gpu, ram, min, rec]);

  if (!published) {
    return (
      <Card className="p-5 text-sm text-fg-muted" data-testid="checker-unavailable">
        System requirements have not been published, so there is nothing to compare against yet. We won&apos;t guess.
      </Card>
    );
  }

  return (
    <Card className="p-5" data-testid="checker">
      <form className="grid gap-4 sm:grid-cols-3" onSubmit={(e) => e.preventDefault()}>
        <label className="text-sm">CPU
          <select className={selectCls} value={cpu} onChange={(e) => setCpu(e.target.value)} data-testid="cpu">
            <option value="">Select your CPU…</option>
            {CPUS.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
            <option value="">Not listed</option>
          </select>
        </label>
        <label className="text-sm">GPU
          <select className={selectCls} value={gpu} onChange={(e) => setGpu(e.target.value)} data-testid="gpu">
            <option value="">Select your GPU…</option>
            {GPUS.map((g) => <option key={g.id} value={g.id}>{g.name}</option>)}
            <option value="">Not listed</option>
          </select>
        </label>
        <label className="text-sm">Memory (RAM)
          <select className={selectCls} value={ram} onChange={(e) => setRam(e.target.value)} data-testid="ram">
            <option value="">Select…</option>
            {RAM_OPTIONS.map((n) => <option key={n} value={n}>{n} GB</option>)}
          </select>
        </label>
      </form>

      <div className="mt-5 rounded border border-line bg-surface-2 p-4" aria-live="polite" data-testid="checker-result">
        <p className="font-display text-lg font-semibold">{OVERALL_COPY[result.o].title}</p>
        <p className="text-sm text-fg-muted">{OVERALL_COPY[result.o].body}</p>
        <div className="mt-4 grid gap-4 md:grid-cols-2">
          {([["Minimum", result.m, min], ["Recommended", result.r, rec]] as const).map(([name, t, req]) => (
            <div key={name}>
              <div className="flex items-center gap-2"><h3 className="font-mono text-xs uppercase tracking-wider text-fg-muted">{name}</h3>{req && <SignalMeter level={req.verification} size="sm" />}</div>
              <ul className="mt-2 space-y-1 text-sm">
                {t.parts.length === 0 && <li className="text-fg-muted">Not published.</li>}
                {t.parts.map((p) => (
                  <li key={p.part}><span className={`font-mono text-xs ${COLOR[p.status]}`}>{ICON[p.status]}</span> <strong>{p.part}</strong> <span className="text-fg-muted">{p.detail}</span></li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </div>

      <div className="mt-4 text-xs text-fg-muted">
        <p><strong>Caveats.</strong> This compares coarse hardware tiers we maintain by hand. They are approximate, not benchmarks.
        Requirements describe a target experience (resolution, frame rate, settings) that publishers don&apos;t always define, and real performance also depends on VRAM, storage speed, drivers and cooling.
        Treat this as a first filter, not a guarantee. Everything runs in your browser; nothing you select is sent anywhere.</p>
      </div>
    </Card>
  );
}
