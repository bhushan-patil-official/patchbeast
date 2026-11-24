import { ImageResponse } from "next/og";
import { api } from "@/lib/api";
import { platformShort } from "@/lib/platforms";

export const OG_SIZE = { width: 1200, height: 630 };
const COLORS = { confirmed: "#2EE59D", reported: "#FFB020", rumour: "#8A93A6" } as const;

export async function gameOgImage(slug: string | null) {
  const r = slug ? await api.hub(slug) : null;
  const name = r?.ok ? r.data.game.name : "Launch tracker";
  const rel = r?.ok ? r.data.release : null;
  const level = rel?.confidence ?? "rumour";
  const status = rel?.countdown_mode === "live" && rel.date ? `${platformShort(rel.platform)} · ${level.toUpperCase()} · ${rel.date}` : "DATE UNCONFIRMED";
  return new ImageResponse(
    (
      <div style={{ width: "100%", height: "100%", display: "flex", flexDirection: "column", justifyContent: "center", padding: 80, background: "#0B0D10", color: "#ECEEF2" }}>
        <div style={{ fontSize: 28, letterSpacing: 6, color: "#A896FF" }}>PATCHBEAST · LAUNCH TRACKER</div>
        <div style={{ fontSize: 80, fontWeight: 800, marginTop: 24, lineHeight: 1.05 }}>{name}</div>
        <div style={{ marginTop: 48, display: "flex" }}>
          <div style={{ display: "flex", border: `3px solid ${COLORS[level]}`, color: COLORS[level], padding: "12px 28px", fontSize: 40, borderRadius: 10 }}>{status}</div>
        </div>
      </div>
    ),
    OG_SIZE,
  );
}
