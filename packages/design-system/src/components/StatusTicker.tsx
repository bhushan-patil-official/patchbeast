"use client";
import * as React from "react";
import { cn } from "../lib/cn";

export interface TickerItem {
  id: string | number;
  text: string;
  href?: string;
  game?: string;
}

/** Slim top ticker of the latest CONFIRMED changes. Pauses on hover/focus; static + scrollable for reduced motion. */
export function StatusTicker({ items, className }: { items: TickerItem[]; className?: string }) {
  if (items.length === 0) return null;
  const duration = Math.max(30, items.length * 12);
  const row = (dup: boolean) => (
    <ul className={cn("flex shrink-0 items-center gap-8 pr-8", dup && "pb-marquee-dup")} aria-hidden={dup || undefined}>
      {items.map((i) => (
        <li key={`${dup}-${i.id}`} className="flex items-center gap-2 whitespace-nowrap">
          <span className="rounded-sm border border-signal-confirmed/50 px-1 font-mono text-[10px] uppercase tracking-wider text-signal-confirmed">
            Confirmed
          </span>
          {i.game && <span className="font-mono text-xs text-fg-muted">{i.game}</span>}
          {i.href ? (
            <a href={i.href} tabIndex={dup ? -1 : 0} className="pb-focus text-xs text-fg hover:text-accent-text">
              {i.text}
            </a>
          ) : (
            <span className="text-xs text-fg">{i.text}</span>
          )}
        </li>
      ))}
    </ul>
  );
  return (
    <div
      role="region"
      aria-label="Latest confirmed changes"
      className={cn("pb-ticker relative overflow-hidden border-b border-line bg-surface-1", className)}
    >
      <div
        className="pb-marquee flex w-max py-1.5"
        style={{ ["--pb-marquee-duration" as string]: `${duration}s` }}
      >
        {row(false)}
        {row(true)}
      </div>
    </div>
  );
}
