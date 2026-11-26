import { storyOgImage } from "@/lib/og";

export const revalidate = 3600;

export async function GET(_req: Request, { params }: { params: Promise<{ slug: string; story: string }> }) {
  const { slug, story } = await params;
  return storyOgImage(slug, story);
}
