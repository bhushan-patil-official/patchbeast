import { notFound } from "next/navigation";
import type { Metadata } from "next";
import { Section } from "@patchbeast/design-system";
import { PlaceholderNotice } from "@/components/Cards";
import { VideoEmbed } from "@/components/VideoEmbed";
import { api } from "@/lib/api";
import { pageMetadata } from "@/lib/seo";

export const revalidate = 300;

export async function generateStaticParams() {
  const r = await api.games();
  return r.ok ? r.data.map((g) => ({ slug: g.slug })) : [];
}
type Props = { params: Promise<{ slug: string }> };

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { slug } = await params;
  const r = await api.videos(slug);
  if (!r.ok) return { robots: { index: false } };
  return pageMetadata({
    title: `${r.data.game.name} trailers and videos`,
    description: `Official trailers and videos for ${r.data.game.name}, linked from their original channels.`,
    path: `/games/${slug}/videos`,
    indexable: r.data.seo.indexable,
  });
}

export default async function VideosPage({ params }: Props) {
  const { slug } = await params;
  const r = await api.videos(slug);
  if (!r.ok) {
    if (r.status === 404) notFound();
    throw new Error("API unavailable");
  }
  const { game, items, seo } = r.data;
  return (
    <>
      <PlaceholderNotice show={!seo.indexable} />
      <h1 className="font-display text-3xl font-bold tracking-tight">{game.name}: trailers &amp; videos</h1>
      <Section title="Videos" id="videos">
        {items.length ? (
          <div className="grid gap-5 md:grid-cols-2">
            {items.map((v) => (
              <figure key={v.id}>
                <VideoEmbed id={v.youtube_id} title={v.title} />
                <figcaption className="mt-2 text-sm"><span className="text-fg">{v.title}</span> <span className="text-fg-muted">· {v.channel}</span>{" "}
                  <a className="text-accent-text underline" href={`https://www.youtube.com/watch?v=${v.youtube_id}`} target="_blank" rel="noopener noreferrer">Watch on YouTube</a></figcaption>
              </figure>
            ))}
          </div>
        ) : <p className="text-fg-muted">No videos have been approved yet.</p>}
      </Section>
    </>
  );
}
