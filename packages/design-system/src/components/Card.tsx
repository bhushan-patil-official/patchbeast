import * as React from "react";
import { cn } from "../lib/cn";

export function Card({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("rounded-lg border border-line bg-surface-1 shadow-1", className)} {...props} />;
}

export function Section({
  title,
  eyebrow,
  actions,
  children,
  id,
  className,
}: {
  title: string;
  eyebrow?: string;
  actions?: React.ReactNode;
  children: React.ReactNode;
  id?: string;
  className?: string;
}) {
  return (
    <section aria-labelledby={id ? `${id}-h` : undefined} id={id} className={cn("py-8", className)}>
      <div className="mb-4 flex items-end justify-between gap-4">
        <div>
          {eyebrow && (
            <p className="font-mono text-xs uppercase tracking-[0.18em] text-accent-text">{eyebrow}</p>
          )}
          <h2 id={id ? `${id}-h` : undefined} className="font-display text-2xl font-semibold tracking-tight">
            {title}
          </h2>
        </div>
        {actions}
      </div>
      {children}
    </section>
  );
}
