import Link from "next/link";
import { notFound } from "next/navigation";
import type { Metadata } from "next";
import { ChangeLog } from "@patchbeast/design-system";
import { Degraded, PlaceholderNotice, toEntry } from "@/components/Cards";
import { Breadcrumbs, GameNav } from "@/components/GameNav";
import { api } from "@/lib/api";
import { pageMetadata } from "@/lib/seo";

export const revalidate = 300;
type Props = { params: Promise<{ slug: string }>; searchParams: Promise<{ page?: string }> };

export async function generateMetadata({ params, searchParams }: Props): Promise<Metadata> {
  const { slug } = await params;
  const { page } = await searchParams;
  const [hub, ch] = await Promise.all([api.hub(slug), api.changes(slug, 1)]);
  if (!hub.ok) return { robots: { index: false } };
  return pageMetadata({
    title: `${hub.data.game.name} timeline: every change, with sources`,
    description: `The full change log for ${hub.data.game.name}: release dates, patches and updates, newest first. Every entry shows its source and verification status.`,
    path: `/games/${slug}/timeline`,
    indexable: hub.data.seo.indexable && ch.ok && ch.data.count > 0 && !page,
  });
}

export default async function Timeline({ params, searchParams }: Props) {
  const { slug } = await params;
  const page = Math.max(1, Number((await searchParams).page) || 1);
  const hub = await api.hub(slug);
  if (!hub.ok) {
    if (hub.status === 404) notFound();
    throw new Error("API unavailable");
  }
  const ch = await api.changes(slug, page);
  const { game, seo } = hub.data;
  return (
    <>
      <PlaceholderNotice show={!seo.indexable} />
      <Breadcrumbs crumbs={[{ name: "Launches", href: "/" }, { name: game.name, href: game.path }, { name: "Timeline" }]} />
      <h1 className="font-display text-3xl font-bold tracking-tight">{game.name}: timeline</h1>
      <p className="mt-2 max-w-prose text-fg-muted">Every release-date, patch and update entry, newest first.</p>
      <GameNav game={game} current="timeline" />
      {ch.ok ? <ChangeLog entries={ch.data.results.map(toEntry)} /> : <Degraded what="The timeline" />}
      {ch.ok && (ch.data.next || ch.data.previous) && (
        <nav aria-label="Pagination" className="mt-6 flex gap-4 text-sm">
          {ch.data.previous && <Link className="text-accent-text underline" href={page > 2 ? `/games/${slug}/timeline?page=${page - 1}` : `/games/${slug}/timeline`}>← Newer</Link>}
          {ch.data.next && <Link className="text-accent-text underline" href={`/games/${slug}/timeline?page=${page + 1}`}>Older →</Link>}
        </nav>
      )}
    </>
  );
}
