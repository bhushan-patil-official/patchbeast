import { gameOgImage, OG_SIZE } from "@/lib/og";

export const alt = "Launch status";
export const size = OG_SIZE;
export const contentType = "image/png";
export const revalidate = 300;

export default async function Image({ params }: { params: Promise<{ slug: string }> }) {
  return gameOgImage((await params).slug);
}
