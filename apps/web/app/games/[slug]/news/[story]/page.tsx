import Link from "next/link";
import { notFound } from "next/navigation";
import type { Metadata } from "next";
import { SignalMeter, SourceChip } from "@patchbeast/design-system";
import { PlaceholderNotice } from "@/components/Cards";
import { Breadcrumbs, GameNav } from "@/components/GameNav";
import { JsonLd } from "@/components/JsonLd";
import { api } from "@/lib/api";
import { absolute, pageMetadata } from "@/lib/seo";
import { SITE_NAME } from "@/lib/site";

export const revalidate = 300;
type Props = { params: Promise<{ slug: string; story: string }> };

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { slug, story } = await params;
  const r = await api.story(slug, story);
  if (!r.ok) return { robots: { index: false, follow: false } };
  return pageMetadata({
    title: r.data.story.title,
    description: r.data.story.dek || r.data.story.title,
    path: `/games/${slug}/news/${story}`,
    indexable: r.data.seo.indexable,
  });
}

export default async function StoryPage({ params }: Props) {
  const { slug, story } = await params;
  const r = await api.story(slug, story);
  if (!r.ok) {
    if (r.status === 404) notFound();
    throw new Error("API unavailable");
  }
  const { game, story: s, blocks, key_points, sources, seo } = r.data;
  const path = `/games/${slug}/news/${story}`;
  return (
    <>
      {seo.indexable && (
        <JsonLd
          data={{
            "@context": "https://schema.org",
            "@type": "NewsArticle",
            headline: s.title,
            description: s.dek,
            datePublished: s.published_at,
            mainEntityOfPage: absolute(path),
            author: { "@type": "Organization", name: SITE_NAME },
            publisher: { "@type": "Organization", name: SITE_NAME },
            about: { "@type": "VideoGame", name: game.name },
            citation: sources.map((x) => x.url),
          }}
        />
      )}
      <PlaceholderNotice show={!seo.indexable} />
      <Breadcrumbs crumbs={[{ name: "Launches", href: "/" }, { name: game.name, href: game.path }, { name: "News", href: `/games/${slug}/news` }, { name: s.title }]} />
      <GameNav game={game} current="news" />
      <article className="mx-auto max-w-3xl" data-testid="story">
        <div className="flex flex-wrap items-center gap-2">
          <span className="rounded border border-accent/50 bg-accent/10 px-1.5 py-0.5 font-mono text-[10px] uppercase tracking-wider text-accent-text">{s.kind === "roundup" ? "Roundup" : "Briefing"}</span>
          <SignalMeter level={s.verification} sources={s.source_count} size="sm" />
          {s.published_at && <time dateTime={s.published_at} className="font-mono text-xs text-fg-muted">{s.published_at.slice(0, 10)}</time>}
        </div>
        <h1 className="mt-3 font-display text-3xl font-bold tracking-tight">{s.title}</h1>
        {s.dek && <p className="mt-3 text-lg text-fg-muted">{s.dek}</p>}

        {key_points.length > 0 && (
          <aside aria-label="Key points" className="my-6 rounded-lg border border-line bg-surface-1 p-4">
            <h2 className="font-mono text-xs uppercase tracking-[0.18em] text-accent-text">Key points</h2>
            <ul className="mt-2 list-disc space-y-1 pl-5 text-sm">{key_points.map((k) => <li key={k}>{k}</li>)}</ul>
          </aside>
        )}

        <div className="space-y-4 text-fg" data-testid="story-body">
          {blocks.map((b, i) => (
            <p key={i} className="leading-relaxed">
              {b.text}{" "}
              <sup className="font-mono text-[11px]">
                {b.sources.map((n) => (
                  <a key={n} href={`#src-${n + 1}`} className="pb-focus mr-0.5 rounded text-accent-text hover:underline" aria-label={`Source ${n + 1}`}>[{n + 1}]</a>
                ))}
              </sup>
            </p>
          ))}
        </div>

        <section aria-labelledby="src-h" className="mt-10">
          <h2 id="src-h" className="font-display text-xl font-semibold">Sources</h2>
          <ol className="mt-3 space-y-2 text-sm" data-testid="story-sources">
            {sources.map((x, i) => (
              <li key={x.article_id} id={`src-${i + 1}`} className="flex flex-wrap items-center gap-2">
                <span className="font-mono text-xs text-fg-muted">[{i + 1}]</span>
                <SourceChip url={x.url} name={x.name || undefined} />
                <span className="text-fg-muted">{x.title}</span>
              </li>
            ))}
          </ol>
        </section>

        <p className="mt-8 rounded border border-line bg-surface-1 p-3 text-xs text-fg-muted" data-testid="story-disclosure">
          This {s.kind === "roundup" ? "roundup" : "briefing"} was drafted by an AI assistant from our own short summaries of the linked reports, then
          checked and approved by a person at {SITE_NAME} before publishing. The linked sources are authoritative:
          if something looks wrong, <Link className="text-accent-text underline" href="/contact">tell us</Link>.
        </p>
      </article>
    </>
  );
}
