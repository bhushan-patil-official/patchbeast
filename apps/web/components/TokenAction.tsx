"use client";
import { useState } from "react";
import { Button } from "@patchbeast/design-system";
import { BROWSER_API_BASE } from "@/lib/api";

export function TokenAction({ token, action, cta, done, failed }: { token: string; action: "confirm" | "unsubscribe"; cta: string; done: string; failed: string }) {
  const [state, setState] = useState<"idle" | "loading" | "ok" | "bad">("idle");
  async function go() {
    setState("loading");
    try {
      const r = await fetch(`${BROWSER_API_BASE}/api/v1/newsletter/${action}/`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ token }) });
      setState(r.ok ? "ok" : "bad");
    } catch { setState("bad"); }
  }
  if (!token) return <p role="alert">This link is missing its token.</p>;
  if (state === "ok") return <p role="status" className="text-signal-confirmed">{done}</p>;
  return (
    <div>
      <Button onClick={go} disabled={state === "loading"}>{cta}</Button>
      {state === "bad" && <p role="alert" className="mt-3 text-signal-alert">{failed}</p>}
    </div>
  );
}
