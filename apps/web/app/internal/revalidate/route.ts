import { revalidatePath, revalidateTag } from "next/cache";
import { timingSafeEqual } from "node:crypto";

export const dynamic = "force-dynamic";

function safeEqual(a: string, b: string) {
  const x = Buffer.from(a), y = Buffer.from(b);
  return x.length === y.length && timingSafeEqual(x, y);
}

/** Called by the Django API after content is published. Shared-secret protected. */
export async function POST(req: Request) {
  const secret = process.env.REVALIDATE_SECRET;
  const given = req.headers.get("x-revalidate-secret") ?? "";
  if (!secret || !safeEqual(secret, given)) return Response.json({ ok: false }, { status: 401 });
  const body = (await req.json().catch(() => ({}))) as { tags?: string[]; paths?: string[] };
  const tags = (body.tags ?? []).filter((t) => typeof t === "string").slice(0, 50);
  const paths = (body.paths ?? []).filter((p) => typeof p === "string" && p.startsWith("/")).slice(0, 50);
  tags.forEach((t) => revalidateTag(t));
  paths.forEach((p) => revalidatePath(p));
  return Response.json({ ok: true, tags, paths });
}
