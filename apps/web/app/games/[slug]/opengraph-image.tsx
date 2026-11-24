import { ImageResponse } from "next/og";
import { api } from "@/lib/api";

export const alt = "Launch status";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";
export const revalidate = 300;

const COLORS = { confirmed: "#2EE59D", reported: "#FFB020", rumour: "#8A93A6" } as const;

export default async function Image({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const r = await api.hub(slug);
  const name = r.ok ? r.data.game.name : "Launch tracker";
  const rel = r.ok ? r.data.release : null;
  const level = rel?.confidence ?? "rumour";
  const status = rel?.countdown_mode === "live" && rel.date ? `${level.toUpperCase()} · ${rel.date}` : "DATE UNCONFIRMED";
  return new ImageResponse(
    (
      <div style={{ width: "100%", height: "100%", display: "flex", flexDirection: "column", justifyContent: "center", padding: 80, background: "#0B0D10", color: "#ECEEF2" }}>
        <div style={{ fontSize: 28, letterSpacing: 6, color: "#A896FF" }}>PATCHBEAST · PC LAUNCH TRACKER</div>
        <div style={{ fontSize: 80, fontWeight: 800, marginTop: 24, lineHeight: 1.05 }}>{name}</div>
        <div style={{ marginTop: 48, display: "flex" }}>
          <div style={{ border: `3px solid ${COLORS[level]}`, color: COLORS[level], padding: "12px 28px", fontSize: 40, borderRadius: 10 }}>{status}</div>
        </div>
      </div>
    ),
    size,
  );
}
