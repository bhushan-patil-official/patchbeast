import type { Metadata } from "next";
import { NewsCard, Degraded } from "@/components/Cards";
import { api } from "@/lib/api";

export const revalidate = 120;
// Raw aggregate: never indexable (scaled-content-abuse risk) and links are not endorsed.
export const metadata: Metadata = {
  title: "Raw feed",
  robots: { index: false, follow: false, nocache: true },
};

export default async function Feed() {
  const r = await api.feed(1);
  return (
    <>
      <h1 className="font-display text-3xl font-bold tracking-tight">Raw feed</h1>
      <p className="mt-2 max-w-prose text-fg-muted">
        Everything our pipeline has seen, including items not yet reviewed. Unreviewed items may be wrong. For vetted
        items see <a className="text-accent-text underline" href="/news">News</a>.
      </p>
      <div className="mt-6 space-y-3">
        {r.ok ? r.data.results.map((a) => <NewsCard key={a.id} a={a} showStatus />) : <Degraded what="The feed" />}
      </div>
    </>
  );
}
