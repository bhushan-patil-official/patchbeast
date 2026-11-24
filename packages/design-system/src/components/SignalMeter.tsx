import * as React from "react";
import { cn } from "../lib/cn";
import { plural, VERIFICATION, type Verification } from "../lib/verification";

export interface SignalMeterProps {
  level: Verification;
  sources?: number;
  size?: "sm" | "md";
  className?: string;
}

const heights = { sm: ["h-1.5", "h-2.5", "h-3.5"], md: ["h-2", "h-3.5", "h-5"] };

/** 3-bar confidence meter (server-safe). Never colour-only: bar count + text label + source count. */
export function SignalMeter({ level, sources, size = "md", className }: SignalMeterProps) {
  const v = VERIFICATION[level];
  const label = sources !== undefined ? `${v.label} · ${plural(sources, "source")}` : v.label;
  return (
    <span
      className={cn("inline-flex items-center gap-2 rounded border bg-surface-2 px-2 py-1", v.ring, className)}
      role="img"
      aria-label={`${label}. ${v.help}`}
      data-level={level}
    >
      <span className="flex items-end gap-0.5" aria-hidden="true">
        {[0, 1, 2].map((i) => (
          <span
            key={i}
            className={cn("w-1 rounded-[1px]", heights[size][i], i < v.bars ? v.bar : "bg-line-strong/60")}
          />
        ))}
      </span>
      <span className={cn("font-mono uppercase tracking-wider", size === "sm" ? "text-[10px]" : "text-xs", v.text)}>
        {label}
      </span>
    </span>
  );
}
