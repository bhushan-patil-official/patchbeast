import { Section } from "@patchbeast/design-system";
import { Degraded, GameLaunchCard } from "@/components/Cards";
import { HubAd } from "@/components/Monetization";
import { NewsletterBlock } from "@/components/NewsletterBlock";
import { JsonLd } from "@/components/JsonLd";
import { api } from "@/lib/api";
import { pageMetadata } from "@/lib/seo";
import { SITE_NAME, SITE_TAGLINE, SITE_URL } from "@/lib/site";

export const revalidate = 300;
export const metadata = pageMetadata({
  title: "Launch tracker, PC first: confirmed dates, patches and requirements",
  description: SITE_TAGLINE,
  path: "/",
  indexable: true,
});

export default async function Home() {
  const r = await api.games();
  return (
    <>
      <JsonLd data={{ "@context": "https://schema.org", "@type": "WebSite", name: SITE_NAME, url: SITE_URL, description: SITE_TAGLINE }} />
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

      <HubAd />

      <Section eyebrow="How we verify" title="Confirmed, Reported, Rumour" id="verify">
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
