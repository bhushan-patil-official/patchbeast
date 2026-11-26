import { patchOgImage } from "@/lib/og";

export const revalidate = 3600;

export async function GET(_req: Request, { params }: { params: Promise<{ slug: string; platform: string; version: string }> }) {
  const { slug, platform, version } = await params;
  return patchOgImage(slug, platform, decodeURIComponent(version));
}
