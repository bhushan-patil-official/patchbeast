import { gameOgImage } from "@/lib/og";

export const revalidate = 3600;

export async function GET(_req: Request, { params }: { params: Promise<{ slug: string }> }) {
  return gameOgImage((await params).slug);
}
