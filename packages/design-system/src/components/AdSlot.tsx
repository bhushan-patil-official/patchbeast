import * as React from "react";
import { cn } from "../lib/cn";

export interface AdSlotProps {
  /** Feature flag state. When false (default) NOTHING renders: no placeholder, no layout space. */
  enabled?: boolean;
  /** Reserved height in px so late-loading ads never cause layout shift (CLS). */
  height: number;
  /** The ad unit; only rendered when enabled AND provided. */
  children?: React.ReactNode;
  className?: string;
}

export function AdSlot({ enabled = false, height, children, className }: AdSlotProps) {
  if (!enabled || !children) return null;
  return (
    <aside aria-label="Advertisement" className={cn("my-6", className)}>
      <p className="mb-1 font-mono text-[10px] uppercase tracking-widest text-fg-muted">Advertisement</p>
      <div style={{ minHeight: height }} className="flex items-center justify-center overflow-hidden rounded border border-line/60 bg-surface-1">
        {children}
      </div>
    </aside>
  );
}
