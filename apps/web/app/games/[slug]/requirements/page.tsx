import { notFound } from "next/navigation";
import type { Metadata } from "next";
import { Section, SpecCompare } from "@patchbeast/design-system";
import { RequirementsChecker } from "@/components/RequirementsChecker";
import { PlaceholderNotice, toTier } from "@/components/Cards";
import { Breadcrumbs, GameNav } from "@/components/GameNav";
import { HardwareBlock } from "@/components/Monetization";
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
  const r = await api.requirements(slug);
  if (!r.ok) return { robots: { index: false } };
  return pageMetadata({
    title: `${r.data.game.name} PC requirements and "can my PC run it" checker`,
    description: `Minimum vs recommended PC requirements for ${r.data.game.name}, with a client-side checker. Nothing you pick leaves your browser.`,
    path: `/games/${slug}/requirements`,
    image: `/og/game/${slug}`,
    indexable: r.data.seo.indexable,
  });
}

export default async function RequirementsPage({ params }: Props) {
  const { slug } = await params;
  const r = await api.requirements(slug);
  if (!r.ok) {
    if (r.status === 404) notFound();
    throw new Error("API unavailable");
  }
  const { game, items, seo } = r.data;
  const min = items.find((x) => x.tier === "min");
  const rec = items.find((x) => x.tier === "rec");
  return (
    <>
      <PlaceholderNotice show={!seo.indexable} />
      <Breadcrumbs crumbs={[{ name: "Launches", href: "/" }, { name: game.name, href: game.path }, { name: "PC requirements" }]} />
      <h1 className="font-display text-3xl font-bold tracking-tight">{game.name}: PC requirements</h1>
      <GameNav game={game} current="requirements" />
      <Section title="Minimum vs recommended" id="specs"><SpecCompare min={toTier(min)} rec={toTier(rec)} /></Section>
      <Section eyebrow="Client-side tool" title="Can my PC run it?" id="checker">
        <RequirementsChecker min={min} rec={rec} />
      </Section>
      <HardwareBlock categories={["gpu", "cpu", "ssd", "ram"]} />
    </>
  );
}
