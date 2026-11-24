import Link from "next/link";
import { notFound } from "next/navigation";
import type { Metadata } from "next";
import { ChangeLog, Countdown, ExplainedSignalMeter, Section, SignalMeter, SourceChip, SpecCompare } from "@patchbeast/design-system";
import { Degraded, NewsCard, PlaceholderNotice, toEntry, toTier } from "@/components/Cards";
import { JsonLd } from "@/components/JsonLd";
import { HardwareBlock, HubAd } from "@/components/Monetization";
import { NewsletterBlock } from "@/components/NewsletterBlock";
import { VideoEmbed } from "@/components/VideoEmbed";
import { api } from "@/lib/api";
import { absolute, pageMetadata } from "@/lib/seo";

export const revalidate = 300;
export const dynamicParams = true;

export async function generateStaticParams() {
  const r = await api.games();
  return r.ok ? r.data.map((g) => ({ slug: g.slug })) : [];
}

type Props = { params: Promise<{ slug: string }> };

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { slug } = await params;
  const r = await api.hub(slug);
  if (!r.ok) return { robots: { index: false, follow: false } };
  const { game, release, seo } = r.data;
  const date = release?.countdown_mode === "live" && release.date ? ` · ${release.confidence} ${release.date}` : "";
  return pageMetadata({
    title: `${game.name}: release date, patches & requirements${date}`,
    description: `Verified release status, patch notes, PC requirements and videos for ${game.name}. Every item links to its source.`,
    path: `/games/${slug}`,
    indexable: seo.indexable,
  });
}

export default async function GameHub({ params }: Props) {
  const { slug } = await params;
  const r = await api.hub(slug);
  if (!r.ok) {
    if (r.status === 404) notFound();
    throw new Error("API unavailable");
  }
  const h = r.data;
  const rel = h.release;
  const min = h.requirements.find((x) => x.tier === "min");
  const rec = h.requirements.find((x) => x.tier === "rec");
  const live = rel?.countdown_mode === "live" && rel.date;
  const show = (s: string) => h.sections.includes(s);

  const ld: Record<string, unknown> = {
    "@context": "https://schema.org",
    "@type": "VideoGame",
    name: h.game.name,
    url: absolute(`/games/${slug}`),
    gamePlatform: "PC",
    ...(live ? { datePublished: rel!.date } : {}), // only when Reported/Confirmed: never a rumour
  };

  return (
    <>
      <JsonLd data={ld} />
      {h.seo.indexable && h.faq.length > 0 && (
        <JsonLd data={{ "@context": "https://schema.org", "@type": "FAQPage", mainEntity: h.faq.map((f) => ({ "@type": "Question", name: f.q, acceptedAnswer: { "@type": "Answer", text: f.a } })) }} />
      )}
      <PlaceholderNotice show={!h.seo.indexable} />

      <header className="rounded-lg border border-line bg-surface-1 p-6 shadow-1 sm:p-10">
        <p className="font-mono text-xs uppercase tracking-[0.22em] text-accent-text">PC launch tracker</p>
        <h1 className="mt-2 font-display text-3xl font-bold tracking-tight sm:text-4xl">{h.game.name}</h1>
        {h.game.tagline && <p className="mt-2 max-w-2xl text-fg-muted">{h.game.tagline}</p>}
        <div className="my-8"><Countdown target={rel?.date ?? null} mode={rel?.countdown_mode ?? "unconfirmed"} /></div>
        <div className="flex flex-wrap items-center justify-center gap-3">
          {rel ? <ExplainedSignalMeter level={rel.confidence} sources={rel.source_count} /> : <SignalMeter level="rumour" />}
          {rel?.source_url && <SourceChip url={rel.source_url} />}
        </div>
        {rel?.note && <p className="mt-3 text-center text-xs text-fg-muted">{rel.note}</p>}
      </header>

      <HubAd />

      {show("release") && (
        <Section eyebrow="Timeline" title="Change log" id="changes">
          <ChangeLog entries={h.changes.map(toEntry)} />
        </Section>
      )}

      {show("requirements") && (
        <Section eyebrow="PC specs" title="System requirements" id="requirements" actions={h.checker_enabled ? <Link href={`/games/${slug}/requirements`} className="text-sm text-accent-text underline">Can my PC run it? →</Link> : undefined}>
          <SpecCompare min={toTier(min)} rec={toTier(rec)} />
        </Section>
      )}

      {show("patches") && (
        <Section eyebrow="Patch notes" title="Latest patches" id="patches" actions={<Link href={`/games/${slug}/patches`} className="text-sm text-accent-text underline">All patches →</Link>}>
          {h.patches.length ? (
            <ul className="space-y-3">
              {h.patches.map((p) => (
                <li key={p.id} className="rounded-lg border border-line bg-surface-1 p-4">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="rounded border border-accent/50 bg-accent/10 px-1.5 py-0.5 font-mono text-xs text-accent-text">v{p.version}</span>
                    {p.date && <time dateTime={p.date} className="font-mono text-xs text-fg-muted">{p.date}</time>}
                    <SignalMeter level={p.verification} sources={p.source_count} size="sm" />
                  </div>
                  {p.our_summary && <p className="mt-2 text-sm text-fg-muted">{p.our_summary}</p>}
                  {p.notes_url && <div className="mt-2"><SourceChip url={p.notes_url} /></div>}
                </li>
              ))}
            </ul>
          ) : <p className="text-sm text-fg-muted">No patches yet.</p>}
        </Section>
      )}

      {show("videos") && h.videos.length > 0 && (
        <Section eyebrow="Trailers & video" title="Videos" id="videos" actions={<Link href={`/games/${slug}/videos`} className="text-sm text-accent-text underline">All videos →</Link>}>
          <div className="grid gap-4 md:grid-cols-3">
            {h.videos.slice(0, 3).map((v) => (
              <figure key={v.id}><VideoEmbed id={v.youtube_id} title={v.title} /><figcaption className="mt-2 text-sm text-fg-muted">{v.title}</figcaption></figure>
            ))}
          </div>
        </Section>
      )}

      {show("news") && (
        <Section eyebrow="Curated" title="News" id="news" actions={<Link href="/news" className="text-sm text-accent-text underline">All news →</Link>}>
          {h.news.length ? <div className="grid gap-4 md:grid-cols-2">{h.news.map((a) => <NewsCard key={a.id} a={a} />)}</div> : <Degraded what="Curated news" />}
        </Section>
      )}

      {h.faq.length > 0 && (
        <Section title="FAQ" id="faq">
          <div className="space-y-2">
            {h.faq.map((f) => (
              <details key={f.q} className="rounded-lg border border-line bg-surface-1 p-4"><summary className="cursor-pointer font-medium">{f.q}</summary><p className="mt-2 text-sm text-fg-muted">{f.a}</p></details>
            ))}
          </div>
        </Section>
      )}

      <HardwareBlock categories={h.affiliate_categories} />
      <NewsletterBlock />
    </>
  );
}
