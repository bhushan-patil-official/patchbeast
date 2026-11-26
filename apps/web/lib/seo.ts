import type { Metadata } from "next";
import { SITE_NAME, SITE_URL } from "./site";

export const absolute = (path: string) => `${SITE_URL}${path}`;
export const DEFAULT_OG_IMAGE = "/opengraph-image";

/** Cut at a word boundary and add an ellipsis. */
export function clamp(text: string, max: number): string {
  const t = text.replace(/\s+/g, " ").trim();
  if (t.length <= max) return t;
  const cut = t.slice(0, max - 1);
  const sp = cut.lastIndexOf(" ");
  return `${(sp > max * 0.6 ? cut.slice(0, sp) : cut).replace(/[\s,;:.\-–—]+$/, "")}…`;
}

/** ~60 chars is what search results show: keep the page part short, add the brand once. */
export const TITLE_MAX = 48;
export function buildTitle(title: string): string {
  const base = clamp(title, TITLE_MAX);
  return base.toLowerCase().includes(SITE_NAME.toLowerCase()) ? base : `${base} · ${SITE_NAME}`;
}

const DESC_MIN = 110;
const DESC_MAX = 158;
const DESC_PAD = " Every item links its sources and shows how well it is verified.";
export function buildDescription(desc: string): string {
  const d = desc.replace(/\s+/g, " ").trim();
  return clamp(d.length < DESC_MIN ? d + DESC_PAD : d, DESC_MAX);
}

const INDEXABLE = {
  index: true,
  follow: true,
  // allow rich snippets, large image previews and video previews in results/Discover
  googleBot: { index: true, follow: true, "max-image-preview": "large" as const, "max-snippet": -1, "max-video-preview": -1 },
};

export function pageMetadata(opts: {
  title: string;
  description: string;
  path: string;
  indexable: boolean;
  /** og:type (default website). Use "article" for our own written pieces. */
  type?: "website" | "article";
  /** Path or absolute URL of the share image (default: the site-wide image). */
  image?: string;
  /** Use the title exactly as given (home page). */
  exactTitle?: boolean;
  publishedTime?: string | null;
  modifiedTime?: string | null;
}): Metadata {
  const url = absolute(opts.path);
  const title = opts.exactTitle ? opts.title : buildTitle(opts.title);
  const description = buildDescription(opts.description);
  const image = opts.image?.startsWith("http") ? opts.image : absolute(opts.image ?? DEFAULT_OG_IMAGE);
  const og = opts.type === "article"
    ? { type: "article" as const, publishedTime: opts.publishedTime ?? undefined, modifiedTime: opts.modifiedTime ?? undefined }
    : { type: "website" as const };
  return {
    title: { absolute: title },
    description,
    // page-level `alternates` REPLACES the layout one, so the RSS discovery link must be repeated here
    alternates: { canonical: url, types: { "application/rss+xml": [{ url: "/rss.xml", title: `${SITE_NAME}: briefings and updates` }] } },
    robots: opts.indexable ? INDEXABLE : { index: false, follow: false },
    openGraph: { title, description, url, siteName: SITE_NAME, locale: "en_US", images: [{ url: image, width: 1200, height: 630, alt: title }], ...og },
    twitter: { card: "summary_large_image", title, description, images: [image] },
  };
}

export const noindex: Metadata = { robots: { index: false, follow: false } };

export function organizationJsonLd() {
  const sameAs = (process.env.NEXT_PUBLIC_SAME_AS || "").split(",").map((s) => s.trim()).filter(Boolean);
  return {
    "@context": "https://schema.org",
    "@type": "Organization",
    "@id": `${SITE_URL}/#organization`,
    name: SITE_NAME,
    url: SITE_URL,
    logo: absolute("/icon.svg"),
    publishingPrinciples: absolute("/editorial-policy"),
    ...(sameAs.length ? { sameAs } : {}),
  };
}

/** Escape text for XML (RSS). */
export const xml = (s: string) =>
  s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&apos;");
