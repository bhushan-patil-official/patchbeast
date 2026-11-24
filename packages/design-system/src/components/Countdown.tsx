"use client";
import * as React from "react";
import { cn } from "../lib/cn";

export interface CountdownProps {
  /** ISO date or datetime of release (treated as 00:00 UTC if a plain date). */
  target: string | null;
  /** "live" ticks; "unconfirmed" freezes honestly (rumour / no date / placeholder). */
  mode: "live" | "unconfirmed";
  className?: string;
}

const pad = (n: number) => String(Math.max(0, n)).padStart(2, "0");

export function breakdown(ms: number) {
  const s = Math.max(0, Math.floor(ms / 1000));
  return { d: Math.floor(s / 86400), h: Math.floor((s % 86400) / 3600), m: Math.floor((s % 3600) / 60), s: s % 60 };
}

const toDate = (t: string) => new Date(/^\d{4}-\d{2}-\d{2}$/.test(t) ? `${t}T00:00:00Z` : t);

export function Countdown({ target, mode, className }: CountdownProps) {
  const [now, setNow] = React.useState<number | null>(null);
  const live = mode === "live" && !!target;

  React.useEffect(() => {
    if (!live) return;
    setNow(Date.now());
    const id = window.setInterval(() => setNow(Date.now()), 1000);
    return () => window.clearInterval(id);
  }, [live]);

  if (!live) {
    return (
      <div className={cn("text-center", className)} data-testid="countdown" data-mode="unconfirmed">
        <p className="font-mono text-3xl font-semibold tracking-tight text-fg-muted sm:text-5xl" aria-hidden="true">
          --:--:--:--
        </p>
        <p className="mt-2 font-mono text-sm uppercase tracking-[0.2em] text-signal-rumour">Date unconfirmed</p>
      </div>
    );
  }

  const end = toDate(target!).getTime();
  const diff = now === null ? null : end - now;
  const released = diff !== null && diff <= 0;
  const b = diff === null ? null : breakdown(diff);
  const units: [string, string][] = b
    ? [[pad(b.d), "days"], [pad(b.h), "hrs"], [pad(b.m), "min"], [pad(b.s), "sec"]]
    : [["--", "days"], ["--", "hrs"], ["--", "min"], ["--", "sec"]];
  if (released) {
    return (
      <div className={cn("text-center", className)} data-testid="countdown" data-mode="released">
        <p className="font-mono text-3xl font-semibold tracking-tight text-signal-confirmed sm:text-5xl">Released</p>
        <time dateTime={target!} className="mt-2 block font-mono text-sm uppercase tracking-[0.2em] text-fg-muted">
          {new Intl.DateTimeFormat("en", { year: "numeric", month: "short", day: "2-digit", timeZone: "UTC" }).format(toDate(target!))}
        </time>
      </div>
    );
  }
  const sr = b
    ? released
      ? "Release date has passed."
      : `Releases in ${b.d} days, ${b.h} hours, ${b.m} minutes.`
    : "";

  return (
    <div className={cn("text-center", className)} data-testid="countdown" data-mode="live">
      {/* accessible alternative: updates once a minute, not every second */}
      <p className="sr-only" role="timer" aria-live="off">
        {sr}
      </p>
      <time dateTime={target!} className="block" aria-hidden="true">
        <div className="flex justify-center gap-3 sm:gap-5">
          {units.map(([v, u], i) => (
            <div key={u} className="min-w-[3.2ch] sm:min-w-[4ch]">
              <div
                key={i === 3 ? v : u}
                className={cn(
                  "font-mono text-4xl font-semibold tabular-nums leading-none sm:text-6xl",
                  i === 3 && "pb-tick text-accent-text",
                )}
              >
                {v}
              </div>
              <div className="mt-2 font-mono text-[10px] uppercase tracking-[0.2em] text-fg-muted">{u}</div>
            </div>
          ))}
        </div>
      </time>
    </div>
  );
}
