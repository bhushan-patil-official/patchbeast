import { ImageResponse } from "next/og";
import { api } from "@/lib/api";
import { platformShort } from "@/lib/platforms";

export const OG_SIZE = { width: 1200, height: 630 };
const COLORS = { confirmed: "#2EE59D", reported: "#FFB020", rumour: "#8A93A6" } as const;
type Level = keyof typeof COLORS;

const CACHE = { "Cache-Control": "public, max-age=3600, s-maxage=86400, stale-while-revalidate=604800" };

/** One share-card layout for every page type: kicker, big title, status badge. Original design, no game artwork. */
export function ogCard(opts: { kicker: string; title: string; badge: string; level?: Level }) {
  const color = COLORS[opts.level ?? "rumour"];
  const size = opts.title.length > 70 ? 52 : opts.title.length > 40 ? 66 : 80;
  return new ImageResponse(
    (
      <div style={{ width: "100%", height: "100%", display: "flex", flexDirection: "column", justifyContent: "center", padding: 80, background: "#0B0D10", color: "#ECEEF2" }}>
        <div style={{ fontSize: 28, letterSpacing: 6, color: "#A896FF", textTransform: "uppercase" }}>{opts.kicker}</div>
        <div style={{ fontSize: size, fontWeight: 800, marginTop: 24, lineHeight: 1.08 }}>{opts.title}</div>
        <div style={{ marginTop: 44, display: "flex", alignItems: "center", gap: 20 }}>
          <div style={{ display: "flex", border: `3px solid ${color}`, color, padding: "10px 26px", fontSize: 34, borderRadius: 10, textTransform: "uppercase" }}>{opts.badge}</div>
          <div style={{ display: "flex", fontSize: 30, fontWeight: 700, color: "#9AA3B2" }}>patchbeast</div>
        </div>
      </div>
    ),
    { ...OG_SIZE, headers: CACHE },
  );
}

export async function gameOgImage(slug: string) {
  const r = await api.hub(slug);
  const name = r.ok ? r.data.game.name : "Launch tracker";
  const rel = r.ok ? r.data.release : null;
  const level = (rel?.confidence ?? "rumour") as Level;
  const live = rel?.countdown_mode === "live" && rel.date;
  return ogCard({
    kicker: "Patchbeast · Launch tracker",
    title: name,
    badge: live ? `${platformShort(rel!.platform)} · ${level} · ${rel!.date}` : "Date unconfirmed",
    level: live ? level : "rumour",
  });
}

export async function patchOgImage(slug: string, platform: string, version: string) {
  const r = await api.patch(slug, platform, version);
  if (!r.ok) return ogCard({ kicker: "Patchbeast", title: "Patches & updates", badge: "Tracker" });
  const { game, patch } = r.data;
  return ogCard({
    kicker: `${game.name} · Update`,
    title: `Update ${patch.version}`,
    badge: `${platformShort(patch.platform)} · ${patch.verification} · ${patch.source_count} source${patch.source_count === 1 ? "" : "s"}`,
    level: patch.verification,
  });
}

export async function storyOgImage(slug: string, story: string) {
  const r = await api.story(slug, story);
  if (!r.ok) return ogCard({ kicker: "Patchbeast", title: "News and briefings", badge: "Briefing" });
  const { game, story: s } = r.data;
  return ogCard({
    kicker: `${game.name} · ${s.kind === "roundup" ? "Roundup" : "Briefing"}`,
    title: s.title,
    badge: `${s.verification} · ${s.source_count} sources`,
    level: s.verification,
  });
}
