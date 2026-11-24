import Link from "next/link";
import { notFound } from "next/navigation";
import type { Metadata } from "next";
import { ChangeLog, Section, SignalMeter, SourceChip } from "@patchbeast/design-system";
import { toEntry, PlaceholderNotice } from "@/components/Cards";
import { Breadcrumbs, GameNav } from "@/components/GameNav";
import { api } from "@/lib/api";
import { platformShort } from "@/lib/platforms";
import { pageMetadata } from "@/lib/seo";

export const revalidate = 300;
type Props = { params: Promise<{ slug: string; platform: string; version: string }> };

const hostOf = (u: string) => { try { return new URL(u).hostname.replace(/^www\./, ""); } catch { return u; } };

const platformName = (g: { platforms: { id: string; name: string }[] }, id: string) =>
  g.platforms.find((p) => p.id === id)?.name ?? id;

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { slug, platform, version } = await params;
  const v = decodeURIComponent(version);
  const r = await api.patch(slug, platform, v);
  if (!r.ok) return { robots: { index: false, follow: false } };
  const { game, patch, seo } = r.data;
  const plat = platformName(game, patch.platform);
  const lead = patch.highlights.length ? patch.highlights.slice(0, 3).join("; ") : patch.our_summary;
  return pageMetadata({
    title: `${game.name} update ${patch.version} (${plat}): patch notes summary`,
    description: `${lead}. Our summary of ${game.name} update ${patch.version} on ${plat}, with sources and verification status.`.slice(0, 300),
    path: `/games/${slug}/patches/${platform}/${encodeURIComponent(v)}`,
    indexable: seo.indexable,
  });
}

export default async function PatchDetail({ params }: Props) {
  const { slug, platform, version } = await params;
  const v = decodeURIComponent(version);
  const r = await api.patch(slug, platform, v);
  if (!r.ok) {
    if (r.status === 404) notFound();
    throw new Error("API unavailable");
  }
  const { game, patch, sources, siblings, changes, seo } = r.data;
  const plat = platformName(game, patch.platform);
  const multi = game.platforms.length > 1;
  return (
    <>
      <PlaceholderNotice show={!seo.indexable} />
      <Breadcrumbs crumbs={[{ name: "Launches", href: "/" }, { name: game.name, href: game.path }, { name: "Patches", href: `/games/${slug}/patches` }, { name: `${patch.version}${multi ? ` (${platformShort(patch.platform)})` : ""}` }]} />
      <h1 className="font-display text-3xl font-bold tracking-tight">{game.name}: update {patch.version}{multi ? ` on ${plat}` : ""}</h1>
      <GameNav game={game} current="patches" />

      <div className="flex flex-wrap items-center gap-2" data-testid="patch-meta">
        <span className="rounded border border-accent/50 bg-accent/10 px-2 py-0.5 font-mono text-sm text-accent-text">v{patch.version}</span>
        {multi && <span className="rounded border border-line px-2 py-0.5 font-mono text-xs uppercase text-fg-muted">{platformShort(patch.platform)}</span>}
        {patch.date && <time dateTime={patch.date} className="font-mono text-sm text-fg-muted">{patch.date}</time>}
        {patch.size_note && <span className="rounded border border-line px-2 py-0.5 font-mono text-xs text-fg-muted">Size: {patch.size_note}</span>}
        <SignalMeter level={patch.verification} sources={patch.source_count} />
      </div>

      {patch.our_summary && <p className="mt-5 max-w-prose text-lg text-fg-muted">{patch.our_summary}</p>}

      {patch.highlights.length > 0 && (
        <Section eyebrow="Our summary" title="What the update reportedly changes" id="highlights">
          <ul className="list-disc space-y-1.5 pl-6 text-fg-muted" data-testid="patch-highlights">
            {patch.highlights.map((h) => <li key={h}>{h}</li>)}
          </ul>
          <p className="mt-3 max-w-prose text-xs text-fg-muted">These are our own short paraphrases of what outlets report, not the publisher&apos;s notes. The linked sources are authoritative.</p>
        </Section>
      )}

      <Section eyebrow="Attribution" title="Sources" id="sources">
        {sources.length ? (
          <div className="space-y-3">
            <div className="flex flex-wrap gap-2" data-testid="patch-sources">
              {sources.map((s) => <SourceChip key={s.domain} url={s.url} />)}
              {/* the stored notes link is just another source unless it is new: never labelled "official" */}
              {patch.notes_url && !sources.some((s) => hostOf(s.url) === hostOf(patch.notes_url)) && <SourceChip url={patch.notes_url} name="Notes link" />}
            </div>
            <p className="max-w-prose text-sm text-fg-muted">
              {patch.verification === "confirmed" ? `Confirmed: reported by ${sources.length} independent source${sources.length === 1 ? "" : "s"}.` : "Reported: one linked source so far. It becomes Confirmed when a second independent source reports it."}
            </p>
          </div>
        ) : <p className="text-sm text-fg-muted">No sources are linked yet, so this page is hidden from search engines.</p>}
      </Section>

      {siblings.length > 0 && (
        <Section title="Same version on other platforms" id="siblings">
          <ul className="flex flex-wrap gap-2">
            {siblings.map((s) => (
              <li key={s.id}><Link className="pb-focus rounded border border-line px-3 py-1 text-sm text-accent-text hover:border-accent" href={`/games/${slug}/patches/${s.platform}/${encodeURIComponent(s.version)}`}>{platformName(game, s.platform)}</Link></li>
            ))}
          </ul>
        </Section>
      )}

      {changes.length > 0 && <Section title="In the timeline" id="timeline"><ChangeLog entries={changes.map(toEntry)} /></Section>}
      <p className="mt-8 text-sm"><Link className="text-accent-text underline" href={`/games/${slug}/patches`}>← All patches &amp; updates</Link></p>
    </>
  );
}
