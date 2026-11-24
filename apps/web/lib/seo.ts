import type { Metadata } from "next";
import { SITE_NAME, SITE_URL } from "./site";

export function pageMetadata(opts: {
  title: string;
  description: string;
  path: string;
  indexable: boolean;
}): Metadata {
  const url = `${SITE_URL}${opts.path}`;
  return {
    title: opts.title,
    description: opts.description,
    alternates: { canonical: url },
    robots: opts.indexable ? { index: true, follow: true } : { index: false, follow: false },
    openGraph: { title: opts.title, description: opts.description, url, siteName: SITE_NAME, type: "website" },
    twitter: { card: "summary_large_image", title: opts.title, description: opts.description },
  };
}

export const noindex: Metadata = { robots: { index: false, follow: false } };

export const absolute = (path: string) => `${SITE_URL}${path}`;
