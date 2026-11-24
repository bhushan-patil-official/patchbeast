import Link from "next/link";
import { NewsCard, Degraded } from "@/components/Cards";
import { api } from "@/lib/api";
import { pageMetadata } from "@/lib/seo";

export const revalidate = 300;

export async function generateMetadata({ searchParams }: { searchParams: Promise<{ page?: string }> }) {
  const { page } = await searchParams;
  const r = await api.news(1);
  // Curated page is indexable only once it has real curated items; paginated pages stay out of the index.
  const has = r.ok && r.data.count > 0;
  return pageMetadata({
    title: "News: curated, with sources",
    description: "Hand-picked launch news. Our own summary plus a link to the original source.",
    path: "/news",
    indexable: has && !page,
  });
}

export default async function News({ searchParams }: { searchParams: Promise<{ page?: string }> }) {
  const page = Math.max(1, Number((await searchParams).page) || 1);
  const r = await api.news(page);
  return (
    <>
      <h1 className="font-display text-3xl font-bold tracking-tight">News</h1>
      <p className="mt-2 max-w-prose text-fg-muted">Curated items only: a human approved each one. We write our own summary and always link the original source.</p>
      <div className="mt-6 space-y-4">
        {r.ok ? (
          r.data.results.length ? r.data.results.map((a) => <NewsCard key={a.id} a={a} />) : <p className="text-fg-muted">No curated news yet.</p>
        ) : <Degraded what="News" />}
      </div>
      {r.ok && (r.data.next || r.data.previous) && (
        <nav aria-label="Pagination" className="mt-6 flex gap-4 text-sm">
          {r.data.previous && <Link className="text-accent-text underline" href={page > 2 ? `/news?page=${page - 1}` : "/news"}>← Newer</Link>}
          {r.data.next && <Link className="text-accent-text underline" href={`/news?page=${page + 1}`}>Older →</Link>}
        </nav>
      )}
    </>
  );
}
