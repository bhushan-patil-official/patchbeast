import localFont from "next/font/local";

// Self-hosted (no runtime request to Google), swap + size-adjusted fallbacks => no layout shift.
export const display = localFont({
  src: "../../../packages/design-system/fonts/space-grotesk-latin-wght-normal.woff2",
  variable: "--font-display",
  weight: "300 700",
  display: "swap",
});
export const body = localFont({
  src: "../../../packages/design-system/fonts/inter-latin-wght-normal.woff2",
  variable: "--font-body",
  weight: "100 900",
  display: "swap",
});
export const mono = localFont({
  src: "../../../packages/design-system/fonts/jetbrains-mono-latin-wght-normal.woff2",
  variable: "--font-mono",
  weight: "100 800",
  display: "swap",
  preload: false, // only small data text uses it: do not compete with the fonts the hero needs
});
