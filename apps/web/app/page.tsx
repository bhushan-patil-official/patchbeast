import Link from "next/link";
import { Section, SignalMeter } from "@patchbeast/design-system";
import { Degraded, GameLaunchCard } from "@/components/Cards";
import { HubAd } from "@/components/Monetization";
import { NewsletterBlock } from "@/components/NewsletterBlock";
import { StoryCard } from "@/components/StoryCard";
import { JsonLd } from "@/components/JsonLd";
import { api } from "@/lib/api";
import { platformShort } from "@/lib/platforms";
import { absolute, organizationJsonLd, pageMetadata } from "@/lib/seo";
import { SITE_NAME, SITE_TAGLINE, SITE_URL } from "@/lib/site";

export const revalidate = 300;
export const metadata = pageMetadata({
  title: "Patchbeast: launch tracker, PC first",
  exactTitle: true,
  description: "PC-first tracker for big game launches: sourced release dates by platform, patch notes and updates, PC requirements and original briefings, each with a verification status.",
  path: "/",
  indexable: true,
});

export default async function Home() {
  const [r, patches, stories] = await Promise.all([api.games(), api.latestPatches(), api.stories()]);
  return (
    <>
      <JsonLd data={{ "@context": "https://schema.org", "@type": "WebSite", "@id": `${SITE_URL}/#website`, name: SITE_NAME, url: SITE_URL, description: SITE_TAGLINE, publisher: { "@id": absolute("/#organization") } }} />
      <JsonLd data={organizationJsonLd()} />
      <section className="py-6">
        <p className="font-mono text-xs uppercase tracking-[0.22em] text-accent-text">Launch control</p>
        <h1 className="mt-2 max-w-3xl font-display text-4xl font-bold tracking-tight sm:text-5xl">
          Every big launch, tracked without the noise. PC first.
        </h1>
        <p className="mt-4 max-w-2xl text-lg text-fg-muted">
          Release dates by platform, patch notes, PC system requirements and videos. Each one carries its source and a
          verification signal, so you can tell a confirmed fact from a rumour at a glance.
        </p>
      </section>

      <Section eyebrow="Now tracking" title="Launches" id="launches">
        {r.ok ? (
          r.data.length ? (
            <div className="grid gap-5 md:grid-cols-2">{r.data.map((g) => <GameLaunchCard key={g.slug} g={g} />)}</div>
          ) : (
            <p className="text-fg-muted">No launches are being tracked yet.</p>
          )
        ) : (
          <Degraded what="The launch list" />
        )}
      </Section>

      {patches.ok && patches.data.length > 0 && (
        <Section eyebrow="Fresh" title="Latest patches and updates" id="latest-updates">
          <ul className="grid gap-3 md:grid-cols-2" data-testid="latest-updates">
            {patches.data.slice(0, 6).map((p) => (
              <li key={p.id} className="rounded-lg border border-line bg-surface-1 p-4">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="font-mono text-xs text-fg-muted">{p.game_name}</span>
                  <span className="rounded border border-line px-1.5 py-0.5 font-mono text-[10px] uppercase text-fg-muted">{platformShort(p.platform)}</span>
                  {p.date && <time dateTime={p.date} className="font-mono text-xs text-fg-muted">{p.date}</time>}
                  <SignalMeter level={p.verification} sources={p.source_count} size="sm" />
                </div>
                <h3 className="mt-2 font-display text-lg font-semibold">
                  <Link className="pb-focus rounded hover:text-accent-text" href={`/games/${p.game_slug}/patches/${p.platform}/${encodeURIComponent(p.version)}`}>
                    {p.game_name} update {p.version}
                  </Link>
                </h3>
                {p.our_summary && <p className="mt-1 text-sm text-fg-muted">{p.our_summary}</p>}
              </li>
            ))}
          </ul>
        </Section>
      )}

      {stories.ok && stories.data.results.length > 0 && (
        <Section eyebrow="Our write-ups" title="Latest briefings" id="latest-briefings" actions={<Link href="/news" className="text-sm text-accent-text underline">All news →</Link>}>
          <div className="grid gap-3 md:grid-cols-2">{stories.data.results.slice(0, 4).map((s) => <StoryCard key={s.id} s={s} />)}</div>
        </Section>
      )}

      <HubAd />

      <Section eyebrow="How we verify" title="Confirmed, Reported, Rumour" id="verify" actions={<Link href="/editorial-policy" className="text-sm text-accent-text underline">Our editorial policy →</Link>}>
        <ul className="grid gap-4 text-sm md:grid-cols-3">
          <li className="rounded-lg border border-signal-confirmed/40 bg-surface-1 p-4"><strong className="text-signal-confirmed">Confirmed</strong><p className="mt-1 text-fg-muted">Two independent sources, or a video. Only these appear in the ticker and the weekly digest.</p></li>
          <li className="rounded-lg border border-signal-reported/40 bg-surface-1 p-4"><strong className="text-signal-reported">Reported</strong><p className="mt-1 text-fg-muted">One linked source. We show it, but we don&apos;t count a clock down on rumours.</p></li>
          <li className="rounded-lg border border-signal-rumour/40 bg-surface-1 p-4"><strong className="text-signal-rumour">Rumour</strong><p className="mt-1 text-fg-muted">Unverified. Labelled as such, never presented as fact.</p></li>
        </ul>
      </Section>

      <NewsletterBlock />
    </>
  );
}
