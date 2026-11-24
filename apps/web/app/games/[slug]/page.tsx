import { notFound, permanentRedirect } from "next/navigation";
import type { Metadata } from "next";
import { GameHubView, hubMetadata } from "@/components/GameHubView";
import { api } from "@/lib/api";

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
  return hubMetadata(r.data); // canonical = vanity path when the game has one
}

export default async function GameHub({ params }: Props) {
  const { slug } = await params;
  const r = await api.hub(slug);
  if (!r.ok) {
    if (r.status === 404) notFound();
    throw new Error("API unavailable");
  }
  // Flagship games live at their short URL; the long URL redirects (308) to it.
  if (r.data.game.vanity_path) permanentRedirect(r.data.game.path);
  return <GameHubView h={r.data} />;
}
