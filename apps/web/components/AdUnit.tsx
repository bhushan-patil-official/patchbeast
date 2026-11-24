"use client";
import Script from "next/script";
import { useEffect } from "react";

declare global {
  interface Window { adsbygoogle?: unknown[] }
}

/** Only rendered inside <AdSlot enabled> when the ads flag AND an AdSense client id are configured. */
export function AdUnit({ client, slot }: { client: string; slot: string }) {
  useEffect(() => {
    try { (window.adsbygoogle = window.adsbygoogle || []).push({}); } catch { /* blocked by an ad blocker */ }
  }, []);
  return (
    <>
      <Script async src={`https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=${client}`} crossOrigin="anonymous" strategy="afterInteractive" />
      <ins className="adsbygoogle" style={{ display: "block", width: "100%" }} data-ad-client={client} data-ad-slot={slot} data-ad-format="auto" data-full-width-responsive="true" />
    </>
  );
}
