import { ImageResponse } from "next/og";

export const alt = "Patchbeast: PC launch tracker";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

export default function Image() {
  return new ImageResponse(
    (
      <div style={{ width: "100%", height: "100%", display: "flex", flexDirection: "column", justifyContent: "center", padding: 80, background: "#0B0D10", color: "#ECEEF2" }}>
        <div style={{ fontSize: 28, letterSpacing: 6, color: "#A896FF", textTransform: "uppercase" }}>Launch control</div>
        <div style={{ display: "flex", fontSize: 96, fontWeight: 800, marginTop: 20 }}><span>patch</span><span style={{ color: "#A896FF" }}>beast</span></div>
        <div style={{ fontSize: 36, color: "#9AA3B2", marginTop: 24, maxWidth: 900 }}>Confirmed dates, patches and requirements. Every item sourced.</div>
        <div style={{ display: "flex", gap: 16, marginTop: 48 }}>
          {[["CONFIRMED", "#2EE59D"], ["REPORTED", "#FFB020"], ["RUMOUR", "#8A93A6"]].map(([t, c]) => (
            <div key={t} style={{ border: `2px solid ${c}`, color: c, padding: "8px 18px", fontSize: 26, borderRadius: 8 }}>{t}</div>
          ))}
        </div>
      </div>
    ),
    size,
  );
}
