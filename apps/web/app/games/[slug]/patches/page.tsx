import { notFound } from "next/navigation";
import type { Metadata } from "next";
import { Section, SignalMeter, SourceChip } from "@patchbeast/design-system";
import { PlaceholderNotice } from "@/components/Cards";
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
  const r = await api.patches(slug);
  if (!r.ok) return { robots: { index: false } };
  return pageMetadata({
    title: `${r.data.game.name} patch notes tracker`,
    description: `Every ${r.data.game.name} patch on PC with version, date, our short summary and a link to the official notes.`,
    path: `/games/${slug}/patches`,
    indexable: r.data.seo.indexable,
  });
}

export default async function PatchesPage({ params }: Props) {
  const { slug } = await params;
  const r = await api.patches(slug);
  if (!r.ok) {
    if (r.status === 404) notFound();
    throw new Error("API unavailable");
  }
  const { game, items, seo } = r.data;
  return (
    <>
      <PlaceholderNotice show={!seo.indexable} />
      <h1 className="font-display text-3xl font-bold tracking-tight">{game.name}: patch notes tracker</h1>
      <p className="mt-2 max-w-prose text-fg-muted">Our own short summaries. The full notes always live at the linked source.</p>
      <Section title="All patches" id="patches">
        {items.length ? (
          <ol className="space-y-3">
            {items.map((p) => (
              <li key={p.id} className="rounded-lg border border-line bg-surface-1 p-4">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="rounded border border-accent/50 bg-accent/10 px-1.5 py-0.5 font-mono text-sm text-accent-text">v{p.version}</span>
                  {p.date && <time dateTime={p.date} className="font-mono text-xs text-fg-muted">{p.date}</time>}
                  <SignalMeter level={p.verification} sources={p.source_count} size="sm" />
                </div>
                {p.our_summary && <p className="mt-2 text-sm text-fg-muted">{p.our_summary}</p>}
                {p.notes_url && <div className="mt-2"><SourceChip url={p.notes_url} /></div>}
              </li>
            ))}
          </ol>
        ) : <p className="text-fg-muted">No patches have been published yet.</p>}
      </Section>
    </>
  );
}
