import Link from "next/link";
import type { Metadata } from "next";
import { ChangeLog, Countdown, ExplainedSignalMeter, Section, SignalMeter, SourceChip, SpecCompare } from "@patchbeast/design-system";
import { NewsCard, PlaceholderNotice, toEntry, toTier } from "@/components/Cards";
import { JsonLd } from "@/components/JsonLd";
import { KnownUnknown } from "@/components/KnownUnknown";
import { HardwareBlock, HubAd } from "@/components/Monetization";
import { NewsletterBlock } from "@/components/NewsletterBlock";
import { PlatformReleases } from "@/components/PlatformReleases";
import { VideoEmbed } from "@/components/VideoEmbed";
import type { Schemas } from "@/lib/api";
import { platformShort, SCHEMA_PLATFORM } from "@/lib/platforms";
import { absolute, pageMetadata } from "@/lib/seo";

export function hubMetadata(h: Schemas["Hub"]): Metadata {
  const { game } = h;
  const multi = h.platforms.length > 1;
  return pageMetadata({
    title: h.seo_title || `${game.name}: release date${multi ? "s by platform" : ""}, patches & requirements`,
    description:
      h.seo_description ||
      `Sourced release status${multi ? " per platform" : ""}, patch notes, PC requirements and videos for ${game.name}. Every item links to its source and shows how well it is verified.`,
    path: game.path,
    indexable: h.seo.indexable,
  });
}

export function GameHubView({ h }: { h: Schemas["Hub"] }) {
  const slug = h.game.slug;
  const rel = h.release;
  const min = h.requirements.find((x) => x.tier === "min");
  const rec = h.requirements.find((x) => x.tier === "rec");
  const multi = h.platforms.length > 1;
  const show = (s: string) => h.sections.includes(s);

  // JSON-LD only claims what is sourced: platforms/dates appear only for Reported/Confirmed dates.
  const live = h.releases.filter((r) => r.countdown_mode === "live" && r.date);
  const earliest = live.map((r) => r.date!).sort()[0];
  const ld: Record<string, unknown> = {
    "@context": "https://schema.org",
    "@type": "VideoGame",
    name: h.game.name,
    url: absolute(h.game.path),
    ...(live.length ? { gamePlatform: live.map((r) => SCHEMA_PLATFORM[r.platform] ?? r.platform) } : {}),
    ...(earliest ? { datePublished: earliest } : {}),
  };

  return (
    <>
      <JsonLd data={ld} />
      {h.seo.indexable && h.faq.length > 0 && (
        <JsonLd data={{ "@context": "https://schema.org", "@type": "FAQPage", mainEntity: h.faq.map((f) => ({ "@type": "Question", name: f.q, acceptedAnswer: { "@type": "Answer", text: f.a } })) }} />
      )}
      <PlaceholderNotice show={!h.seo.indexable} />

      <header className="rounded-lg border border-line bg-surface-1 p-6 shadow-1 sm:p-10">
        <p className="font-mono text-xs uppercase tracking-[0.22em] text-accent-text">{multi ? "Launch tracker · PC first" : "PC launch tracker"}</p>
        <h1 className="mt-2 font-display text-3xl font-bold tracking-tight sm:text-4xl">{h.game.name}</h1>
        {h.game.tagline && <p className="mt-2 max-w-2xl text-fg-muted">{h.game.tagline}</p>}
        {multi && rel && <p className="mt-6 text-center font-mono text-xs uppercase tracking-[0.2em] text-fg-muted">{platformShort(rel.platform)} release</p>}
        <div className={multi ? "mb-8 mt-2" : "my-8"}><Countdown target={rel?.date ?? null} mode={rel?.countdown_mode ?? "unconfirmed"} /></div>
        <div className="flex flex-wrap items-center justify-center gap-3">
          {rel ? <ExplainedSignalMeter level={rel.confidence} sources={rel.source_count} /> : <SignalMeter level="rumour" />}
          {rel?.source_url && <SourceChip url={rel.source_url} />}
        </div>
        {rel?.note && <p className="mt-3 text-center text-xs text-fg-muted">{rel.note}</p>}
        {multi && <div className="mx-auto mt-8 max-w-2xl"><PlatformReleases releases={h.releases} platforms={h.platforms} /></div>}
      </header>

      <KnownUnknown h={h} />

      {h.faq.length > 0 && (
        <Section title="FAQ" id="faq">
          <div className="space-y-2">
            {h.faq.map((f) => (
              <details key={f.q} className="rounded-lg border border-line bg-surface-1 p-4"><summary className="cursor-pointer font-medium">{f.q}</summary><p className="mt-2 text-sm text-fg-muted">{f.a}</p></details>
            ))}
          </div>
        </Section>
      )}

      <HubAd />
      <NewsletterBlock game={{ slug, name: h.game.name }} />

      {show("release") && (
        <Section eyebrow="Timeline" title="Change log" id="changes">
          <ChangeLog entries={h.changes.map(toEntry)} />
        </Section>
      )}

      {show("requirements") && (
        <Section eyebrow="PC specs" title="PC system requirements" id="requirements" actions={h.checker_enabled ? <Link href={`/games/${slug}/requirements`} className="text-sm text-accent-text underline">Can my PC run it? →</Link> : undefined}>
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
                    {multi && <span className="rounded border border-line px-1.5 py-0.5 font-mono text-[10px] uppercase text-fg-muted">{platformShort(p.platform)}</span>}
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
          {h.news.length ? <div className="grid gap-4 md:grid-cols-2">{h.news.map((a) => <NewsCard key={a.id} a={a} />)}</div> : <p className="text-sm text-fg-muted">No curated news yet. Items appear here once a person has reviewed them.</p>}
        </Section>
      )}

      <HardwareBlock categories={h.affiliate_categories} />
    </>
  );
}
