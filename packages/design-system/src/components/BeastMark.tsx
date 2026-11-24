import * as React from "react";
import { cn } from "../lib/cn";

/** Original Patchbeast mark: three claw slashes breaking a hex frame. Not derived from any game artwork. */
export function BeastMark({ size = 28, className }: { size?: number; className?: string }) {
  return (
    <svg width={size} height={size} viewBox="0 0 32 32" role="img" aria-label="Patchbeast mark" className={className}>
      <defs>
        <linearGradient id="pb-g" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor="#A896FF" />
          <stop offset="1" stopColor="#7C5CFF" />
        </linearGradient>
      </defs>
      <path d="M16 2 28 9v14l-12 7L4 23V9z" fill="none" stroke="url(#pb-g)" strokeWidth="1.6" strokeLinejoin="round" opacity="0.55" />
      <path d="M9 7.5 14.5 25.5l1.2-.5L11.2 8.2z" fill="url(#pb-g)" />
      <path d="M14.4 5.5 20.5 26.4l1.3-.5-5.4-19z" fill="url(#pb-g)" />
      <path d="M19.9 8.2 25 24.5l1.1-.5L21.4 8z" fill="url(#pb-g)" />
    </svg>
  );
}

export function Wordmark({ className, markSize = 26 }: { className?: string; markSize?: number }) {
  return (
    <span className={cn("inline-flex items-center gap-2", className)}>
      <BeastMark size={markSize} />
      <span className="font-display text-xl font-bold lowercase tracking-tight">
        patch<span className="text-accent-text">beast</span>
      </span>
    </span>
  );
}
