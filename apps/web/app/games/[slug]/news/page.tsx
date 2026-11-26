import Link from "next/link";
import { notFound } from "next/navigation";
import type { Metadata } from "next";
import { NewsCard, Degraded, PlaceholderNotice } from "@/components/Cards";
import { StoryCard } from "@/components/StoryCard";
import { Breadcrumbs, GameNav } from "@/components/GameNav";
import { api } from "@/lib/api";
import { pageMetadata } from "@/lib/seo";

export const revalidate = 300;
type Props = { params: Promise<{ slug: string }>; searchParams: Promise<{ page?: string }> };

export async function generateMetadata({ params, searchParams }: Props): Promise<Metadata> {
  const { slug } = await params;
  const { page } = await searchParams;
  const [hub, news] = await Promise.all([api.hub(slug), api.news(1, slug)]);
  if (!hub.ok) return { robots: { index: false } };
  return pageMetadata({
    title: `${hub.data.game.name} news: curated, with sources`,
    description: `Hand-picked ${hub.data.game.name} news. Our own summary plus a link to the original source.`,
    path: `/games/${slug}/news`,
    image: `/og/game/${slug}`,
    indexable: hub.data.seo.indexable && news.ok && news.data.count > 0 && !page,
  });
}

export default async function GameNews({ params, searchParams }: Props) {
  const { slug } = await params;
  const page = Math.max(1, Number((await searchParams).page) || 1);
  const hub = await api.hub(slug);
  if (!hub.ok) {
    if (hub.status === 404) notFound();
    throw new Error("API unavailable");
  }
  const [news, stories] = await Promise.all([api.news(page, slug), api.stories(slug)]);
  const { game, seo } = hub.data;
  return (
    <>
      <PlaceholderNotice show={!seo.indexable} />
      <Breadcrumbs crumbs={[{ name: "Launches", href: "/" }, { name: game.name, href: game.path }, { name: "News" }]} />
      <h1 className="font-display text-3xl font-bold tracking-tight">{game.name}: news</h1>
      <p className="mt-2 max-w-prose text-fg-muted">Curated items only: a person approved each one. We write our own summary and always link the original source.</p>
      <GameNav game={game} current="news" />
      {stories.ok && stories.data.results.length > 0 && (
        <section aria-labelledby="briefings-h" className="mb-8">
          <h2 id="briefings-h" className="font-display text-xl font-semibold">Briefings</h2>
          <p className="mb-3 text-sm text-fg-muted">Our own write-ups, each built from two or more linked sources and reviewed by a person.</p>
          <div className="space-y-3">{stories.data.results.map((s) => <StoryCard key={s.id} s={s} />)}</div>
        </section>
      )}
      <h2 className="mb-3 font-display text-xl font-semibold">Linked news</h2>
      <div className="space-y-4">
        {news.ok ? (
          news.data.results.length ? news.data.results.map((a) => <NewsCard key={a.id} a={a} />) : <p className="text-fg-muted">No curated news for this game yet.</p>
        ) : <Degraded what="News" />}
      </div>
      {news.ok && (news.data.next || news.data.previous) && (
        <nav aria-label="Pagination" className="mt-6 flex gap-4 text-sm">
          {news.data.previous && <Link className="text-accent-text underline" href={page > 2 ? `/games/${slug}/news?page=${page - 1}` : `/games/${slug}/news`}>← Newer</Link>}
          {news.data.next && <Link className="text-accent-text underline" href={`/games/${slug}/news?page=${page + 1}`}>Older →</Link>}
        </nav>
      )}
    </>
  );
}
