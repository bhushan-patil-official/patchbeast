export const dynamic = "force-dynamic";

/** IndexNow ownership file: contains the key set in INDEXNOW_KEY (404 when IndexNow is not configured). */
export function GET() {
  const key = process.env.INDEXNOW_KEY;
  if (!key) return new Response("Not found", { status: 404 });
  return new Response(key, { headers: { "Content-Type": "text/plain; charset=utf-8" } });
}
