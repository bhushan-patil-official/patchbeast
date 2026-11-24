import Link from "next/link";
import { notFound } from "next/navigation";
import type { Metadata } from "next";
import { Section, SignalMeter, SourceChip } from "@patchbeast/design-system";
import { PlaceholderNotice } from "@/components/Cards";
import { Breadcrumbs, GameNav } from "@/components/GameNav";
import { api } from "@/lib/api";
import { platformShort } from "@/lib/platforms";
import { pageMetadata } from "@/lib/seo";

export const revalidate = 300;

export async function generateStaticParams() {
  const r = await api.games();
  return r.ok ? r.data.map((g) => ({ slug: g.slug })) : [];
}

type Props = { params: Promise<{ slug: string }>; searchParams: Promise<{ platform?: string }> };

export async function generateMetadata({ params, searchParams }: Props): Promise<Metadata> {
  const { slug } = await params;
  const { platform } = await searchParams;
  const r = await api.patches(slug);
  if (!r.ok) return { robots: { index: false } };
  return pageMetadata({
    title: `${r.data.game.name} patch notes tracker`,
    description: `Every ${r.data.game.name} patch by platform with version, date, our short summary and a link to the official notes.`,
    path: `/games/${slug}/patches`,
    indexable: r.data.seo.indexable && !platform, // filtered views are not separate index targets
  });
}

export default async function PatchesPage({ params, searchParams }: Props) {
  const { slug } = await params;
  const { platform } = await searchParams;
  const r = await api.patches(slug, platform);
  if (!r.ok) {
    if (r.status === 404) notFound();
    throw new Error("API unavailable");
  }
  const { game, items, seo, platforms, selected_platform } = r.data;
  const multi = platforms.length > 1;
  const chip = (active: boolean) =>
    `pb-focus rounded-full border px-3 py-1 text-sm ${active ? "border-accent bg-accent/15 text-fg" : "border-line text-fg-muted hover:text-fg"}`;
  return (
    <>
      <PlaceholderNotice show={!seo.indexable} />
      <Breadcrumbs crumbs={[{ name: "Launches", href: "/" }, { name: game.name, href: game.path }, { name: "Patches" }]} />
      <h1 className="font-display text-3xl font-bold tracking-tight">{game.name}: patches &amp; updates</h1>
      <p className="mt-2 max-w-prose text-fg-muted">Our own short summaries. The full notes always live at the linked source. Open an update for highlights, size and sources.</p>
      <GameNav game={game} current="patches" />
      {multi && (
        <nav aria-label="Filter by platform" className="mt-4 flex flex-wrap gap-2">
          <Link href={`/games/${slug}/patches`} className={chip(!selected_platform)} aria-current={!selected_platform ? "true" : undefined}>All</Link>
          {platforms.map((p) => (
            <Link key={p.id} href={`/games/${slug}/patches?platform=${p.id}`} className={chip(selected_platform === p.id)} aria-current={selected_platform === p.id ? "true" : undefined} data-testid={`filter-${p.id}`}>{p.name}</Link>
          ))}
        </nav>
      )}
      <Section title={selected_platform ? `${platformShort(selected_platform)} patches` : "All patches"} id="patches">
        {items.length ? (
          <ol className="space-y-3">
            {items.map((p) => (
              <li key={p.id} className="rounded-lg border border-line bg-surface-1 p-4" data-testid="patch-item" data-platform={p.platform}>
                <div className="flex flex-wrap items-center gap-2">
                  <Link href={`/games/${slug}/patches/${p.platform}/${encodeURIComponent(p.version)}`} className="pb-focus rounded border border-accent/50 bg-accent/10 px-1.5 py-0.5 font-mono text-sm text-accent-text hover:bg-accent/20">v{p.version}</Link>
                  {multi && <span className="rounded border border-line px-1.5 py-0.5 font-mono text-[10px] uppercase text-fg-muted">{platformShort(p.platform)}</span>}
                  {p.date && <time dateTime={p.date} className="font-mono text-xs text-fg-muted">{p.date}</time>}
                  <SignalMeter level={p.verification} sources={p.source_count} size="sm" />
                </div>
                {p.our_summary && <p className="mt-2 text-sm text-fg-muted">{p.our_summary}</p>}
                {p.size_note && <p className="mt-1 font-mono text-xs text-fg-muted">Size: {p.size_note}</p>}
                <p className="mt-2 text-sm"><Link className="text-accent-text underline" href={`/games/${slug}/patches/${p.platform}/${encodeURIComponent(p.version)}`}>Update details →</Link></p>
                {p.notes_url && <div className="mt-2"><SourceChip url={p.notes_url} /></div>}
              </li>
            ))}
          </ol>
        ) : <p className="text-fg-muted">No patches have been published yet{selected_platform ? " for this platform" : ""}.</p>}
      </Section>
    </>
  );
}
