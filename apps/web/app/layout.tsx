import type { Metadata, Viewport } from "next";
import Script from "next/script";
import { themeInitScript } from "@patchbeast/design-system";
import { SiteFooter, SiteHeader, Ticker } from "@/components/SiteChrome";
import { SITE_NAME, SITE_TAGLINE, SITE_URL } from "@/lib/site";
import { body, display, mono } from "./fonts";
import "./globals.css";

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: { default: `${SITE_NAME}: PC launch tracker`, template: `%s · ${SITE_NAME}` },
  description: SITE_TAGLINE,
  applicationName: SITE_NAME,
  alternates: { canonical: "/" },
  verification: process.env.NEXT_PUBLIC_GSC_VERIFICATION ? { google: process.env.NEXT_PUBLIC_GSC_VERIFICATION } : undefined,
  openGraph: { siteName: SITE_NAME, type: "website" },
};
export const viewport: Viewport = { themeColor: "#0B0D10", colorScheme: "dark light" };

const PLAUSIBLE_DOMAIN = process.env.NEXT_PUBLIC_PLAUSIBLE_DOMAIN;
const PLAUSIBLE_SRC = process.env.NEXT_PUBLIC_PLAUSIBLE_SRC || "https://plausible.io/js/script.js";

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" data-theme="dark" suppressHydrationWarning className={`${display.variable} ${body.variable} ${mono.variable}`}>
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeInitScript }} />
      </head>
      <body className="min-h-screen font-sans">
        <a href="#main" className="skip-link">Skip to content</a>
        <Ticker />
        <SiteHeader />
        <main id="main" className="mx-auto max-w-6xl px-4 py-8">{children}</main>
        <SiteFooter />
        {PLAUSIBLE_DOMAIN && <Script defer data-domain={PLAUSIBLE_DOMAIN} src={PLAUSIBLE_SRC} strategy="afterInteractive" />}
      </body>
    </html>
  );
}
