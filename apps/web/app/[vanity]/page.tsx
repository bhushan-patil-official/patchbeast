import { notFound } from "next/navigation";
import type { Metadata } from "next";
import { GameHubView, hubMetadata } from "@/components/GameHubView";
import { api } from "@/lib/api";

export const revalidate = 300;
export const dynamicParams = true;

export async function generateStaticParams() {
  const r = await api.games();
  return r.ok ? r.data.flatMap((g) => (g.vanity_path ? [{ vanity: g.vanity_path }] : [])) : [];
}

type Props = { params: Promise<{ vanity: string }> };

/** Resolve a short URL (e.g. /gta-6-pc) to its game, config-driven: no game is named in code. */
async function resolve(vanity: string) {
  const games = await api.games();
  if (!games.ok) throw new Error("API unavailable");
  const game = games.data.find((g) => g.vanity_path === vanity);
  if (!game) notFound();
  const hub = await api.hub(game.slug);
  if (!hub.ok) {
    if (hub.status === 404) notFound();
    throw new Error("API unavailable");
  }
  return hub.data;
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { vanity } = await params;
  try {
    return hubMetadata(await resolve(vanity));
  } catch {
    return { robots: { index: false, follow: false } };
  }
}

export default async function VanityHub({ params }: Props) {
  const { vanity } = await params;
  return <GameHubView h={await resolve(vanity)} />;
}
