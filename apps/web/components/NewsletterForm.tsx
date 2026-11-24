"use client";
import { useState } from "react";
import { Button } from "@patchbeast/design-system";
import { BROWSER_API_BASE } from "@/lib/api";

export function NewsletterForm({ game }: { game?: string }) {
  const [state, setState] = useState<"idle" | "loading" | "done" | "error">("idle");

  async function onSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const fd = new FormData(e.currentTarget);
    setState("loading");
    try {
      const r = await fetch(`${BROWSER_API_BASE}/api/v1/newsletter/subscribe/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: fd.get("email"), website: fd.get("website") ?? "", ...(game ? { game } : {}) }),
      });
      setState(r.ok ? "done" : "error");
    } catch {
      setState("error");
    }
  }

  if (state === "done")
    return (
      <p role="status" className="rounded border border-signal-confirmed/50 bg-surface-2 p-3 text-sm">
        Check your inbox: we sent a confirmation link. Nothing is sent until you confirm.
      </p>
    );

  return (
    <form onSubmit={onSubmit} className="flex flex-col gap-2 sm:flex-row" aria-describedby="nl-note">
      <label htmlFor="nl-email" className="sr-only">Email address</label>
      <input
        id="nl-email" name="email" type="email" required autoComplete="email" placeholder="you@example.com"
        className="h-10 flex-1 rounded border border-line bg-surface-2 px-3 text-sm text-fg placeholder:text-fg-muted"
      />
      {/* honeypot: real people never see or fill this */}
      <div aria-hidden="true" className="absolute -left-[9999px]">
        <label>Website<input name="website" tabIndex={-1} autoComplete="off" /></label>
      </div>
      <Button type="submit" disabled={state === "loading"}>{state === "loading" ? "Sending…" : "Get the weekly digest"}</Button>
      <p id="nl-note" className="text-xs text-fg-muted sm:hidden">Double opt-in. One email a week. Unsubscribe any time.</p>
      {state === "error" && <p role="alert" className="text-sm text-signal-alert">Could not subscribe right now. Please try again later.</p>}
    </form>
  );
}
