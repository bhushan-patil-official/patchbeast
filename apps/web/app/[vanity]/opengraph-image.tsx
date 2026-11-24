import { api } from "@/lib/api";
import { gameOgImage, OG_SIZE } from "@/lib/og";

export const alt = "Launch status";
export const size = OG_SIZE;
export const contentType = "image/png";
export const revalidate = 300;

export default async function Image({ params }: { params: Promise<{ vanity: string }> }) {
  const { vanity } = await params;
  const games = await api.games();
  const g = games.ok ? games.data.find((x) => x.vanity_path === vanity) : undefined;
  return gameOgImage(g?.slug ?? null);
}
