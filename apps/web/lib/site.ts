export const SITE_URL = (process.env.NEXT_PUBLIC_SITE_URL || "http://localhost:3000").replace(/\/$/, "");
export const SITE_NAME = "Patchbeast";
export const SITE_TAGLINE = "PC-first launch tracker: confirmed dates, patches and requirements, with sources.";
export const CONTACT_EMAIL = process.env.NEXT_PUBLIC_CONTACT_EMAIL || "hello@patchbeast.com";
/** ISR safety-net window; publishes also trigger tag revalidation immediately. */
export const REVALIDATE_SECONDS = 300;
