import type { MetadataRoute } from "next";
import { api } from "@/lib/api";
import { SITE_URL } from "@/lib/site";

export const revalidate = 3600;

const STATIC = ["/about", "/editorial-policy", "/contact", "/privacy", "/terms", "/affiliate-disclosure"];

/** Only API-declared indexable pages (curated + tool pages). Raw feed and placeholders never appear. */
export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const r = await api.sitemap();
  const dynamic = r.ok ? r.data : [{ path: "/", lastmod: null }];
  return [
    ...dynamic.map((e) => ({ url: e.path === "/" ? SITE_URL : `${SITE_URL}${e.path}`, lastModified: e.lastmod ? new Date(e.lastmod) : undefined })),
    ...STATIC.map((p) => ({ url: `${SITE_URL}${p}` })),
  ];
}
