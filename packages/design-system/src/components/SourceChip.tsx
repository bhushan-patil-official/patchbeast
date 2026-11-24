import * as React from "react";
import { cn } from "../lib/cn";

export function hostname(url: string): string {
  try {
    return new URL(url).hostname.replace(/^www\./, "");
  } catch {
    return url;
  }
}

export interface SourceChipProps {
  url: string;
  name?: string;
  nofollow?: boolean;
  className?: string;
}

/** Attribution link: every item shows where it came from. */
export function SourceChip({ url, name, nofollow, className }: SourceChipProps) {
  return (
    <a
      href={url}
      target="_blank"
      rel={cn("noopener noreferrer", nofollow && "nofollow")}
      className={cn(
        "pb-focus inline-flex max-w-full items-center gap-1.5 rounded-full border border-line bg-surface-2 px-2.5 py-0.5 text-xs text-fg-muted transition-colors hover:border-line-strong hover:text-fg",
        className,
      )}
    >
      <span className="font-mono uppercase tracking-wider text-[10px] text-accent-text">src</span>
      <span className="truncate">{name ? `${name} · ${hostname(url)}` : hostname(url)}</span>
      <svg width="10" height="10" viewBox="0 0 12 12" aria-hidden="true" className="shrink-0">
        <path d="M4 2h6v6M10 2 3 9" fill="none" stroke="currentColor" strokeWidth="1.5" />
      </svg>
      <span className="sr-only">(opens source in a new tab)</span>
    </a>
  );
}
