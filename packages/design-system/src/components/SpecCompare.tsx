import * as React from "react";
import { cn } from "../lib/cn";
import type { Verification } from "../lib/verification";
import { SignalMeter } from "./SignalMeter";
import { SourceChip } from "./SourceChip";

export interface SpecTier {
  os?: string;
  cpu?: string;
  gpu?: string;
  ramGb?: number | null;
  storageGb?: number | null;
  notes?: string;
  verification: Verification;
  sources?: number;
  sourceUrl?: string;
  placeholder?: boolean;
}

const rows: { key: string; label: string; get: (t: SpecTier) => string }[] = [
  { key: "os", label: "OS", get: (t) => t.os || "" },
  { key: "cpu", label: "CPU", get: (t) => t.cpu || "" },
  { key: "gpu", label: "GPU", get: (t) => t.gpu || "" },
  { key: "ram", label: "Memory", get: (t) => (t.ramGb ? `${t.ramGb} GB` : "") },
  { key: "storage", label: "Storage", get: (t) => (t.storageGb ? `${t.storageGb} GB` : "") },
];

/** Minimum vs Recommended. Empty cells say "Not published", never a guess. */
export function SpecCompare({ min, rec, className }: { min?: SpecTier | null; rec?: SpecTier | null; className?: string }) {
  const cell = (t: SpecTier | null | undefined, get: (t: SpecTier) => string) => {
    const v = t ? get(t) : "";
    return v ? <span>{v}</span> : <span className="text-fg-muted">Not published</span>;
  };
  return (
    <div className={cn("overflow-x-auto rounded-lg border border-line", className)}>
      <table className="w-full min-w-[34rem] border-collapse text-left text-sm">
        <caption className="sr-only">PC system requirements: minimum versus recommended</caption>
        <thead>
          <tr className="bg-surface-2">
            <th scope="col" className="w-28 px-4 py-3 font-mono text-xs uppercase tracking-wider text-fg-muted">
              Spec
            </th>
            {([["Minimum", min], ["Recommended", rec]] as const).map(([name, t]) => (
              <th key={name} scope="col" className="px-4 py-3 align-top">
                <div className="font-display text-base font-semibold">{name}</div>
                {t && !t.placeholder ? (
                  <div className="mt-1 flex flex-wrap items-center gap-2">
                    <SignalMeter level={t.verification} sources={t.sources} size="sm" />
                    {t.sourceUrl && <SourceChip url={t.sourceUrl} />}
                  </div>
                ) : (
                  <div className="mt-1">
                    <SignalMeter level="rumour" size="sm" />
                  </div>
                )}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.key} className="border-t border-line">
              <th scope="row" className="px-4 py-3 font-mono text-xs uppercase tracking-wider text-fg-muted">
                {r.label}
              </th>
              <td className="px-4 py-3">{cell(min, r.get)}</td>
              <td className="px-4 py-3">{cell(rec, r.get)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
