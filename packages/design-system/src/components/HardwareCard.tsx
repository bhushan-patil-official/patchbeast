import * as React from "react";
import { cn } from "../lib/cn";
import { Card } from "./Card";

export interface HardwareCardProps {
  title: string;
  blurb: string;
  merchant: string;
  href: string;
  category?: string;
  price?: string;
  disclosureHref?: string;
  className?: string;
}

/** Affiliate hardware suggestion. The disclosure is part of the component and cannot be removed. */
export function HardwareCard({ title, blurb, merchant, href, category, price, disclosureHref = "/affiliate-disclosure", className }: HardwareCardProps) {
  return (
    <Card className={cn("flex h-full flex-col p-4", className)}>
      {category && <p className="font-mono text-[10px] uppercase tracking-[0.18em] text-accent-text">{category}</p>}
      <h3 className="mt-1 font-display text-base font-semibold">{title}</h3>
      <p className="mt-1 flex-1 text-sm text-fg-muted">{blurb}</p>
      <div className="mt-3 flex items-center justify-between gap-2">
        <a
          href={href}
          target="_blank"
          rel="sponsored noopener noreferrer"
          className="pb-focus inline-flex h-9 items-center rounded bg-accent-strong px-3 text-sm font-medium text-accent-on hover:bg-accent-strong/90"
        >
          View at {merchant}
          <span className="sr-only"> (affiliate link, opens in a new tab)</span>
        </a>
        {price && <span className="font-mono text-sm text-fg">{price}</span>}
      </div>
      <p className="mt-3 border-t border-line pt-2 text-[11px] text-fg-muted">
        Affiliate link: we may earn a commission at no cost to you.{" "}
        <a className="underline hover:text-fg" href={disclosureHref}>
          Disclosure
        </a>
      </p>
    </Card>
  );
}
