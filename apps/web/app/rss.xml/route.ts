import { api } from "@/lib/api";
import { absolute, xml } from "@/lib/seo";
import { SITE_NAME, SITE_TAGLINE } from "@/lib/site";

export const revalidate = 600;

type Item = { title: string; link: string; date: string; description: string };

/** RSS 2.0 of OUR content only: briefings, roundups and sourced patch updates (never other sites' articles). */
export async function GET() {
  const [stories, patches] = await Promise.all([api.stories(), api.latestPatches()]);
  const items: Item[] = [];
  if (stories.ok)
    for (const s of stories.data.results)
      if (s.published_at && s.indexable) items.push({ title: s.title, link: absolute(`/games/${s.game_slug}/news/${s.slug}`), date: s.published_at, description: s.dek });
  if (patches.ok)
    for (const p of patches.data)
      if (p.date) items.push({
        title: `${p.game_name} update ${p.version} (${p.platform})`,
        link: absolute(`/games/${p.game_slug}/patches/${p.platform}/${encodeURIComponent(p.version)}`),
        date: `${p.date}T12:00:00Z`,
        description: p.our_summary || `Our summary of ${p.game_name} update ${p.version}.`,
      });
  items.sort((a, b) => +new Date(b.date) - +new Date(a.date));
  const last = items[0]?.date ?? new Date().toISOString();
  const body = `<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
<channel>
<title>${xml(SITE_NAME)}: briefings and updates</title>
<link>${xml(absolute("/"))}</link>
<description>${xml(SITE_TAGLINE)}</description>
<language>en</language>
<lastBuildDate>${new Date(last).toUTCString()}</lastBuildDate>
<atom:link href="${xml(absolute("/rss.xml"))}" rel="self" type="application/rss+xml"/>
${items
  .slice(0, 30)
  .map((i) => `<item><title>${xml(i.title)}</title><link>${xml(i.link)}</link><guid isPermaLink="true">${xml(i.link)}</guid><pubDate>${new Date(i.date).toUTCString()}</pubDate><description>${xml(i.description)}</description></item>`)
  .join("\n")}
</channel>
</rss>`;
  return new Response(body, { headers: { "Content-Type": "application/rss+xml; charset=utf-8", "Cache-Control": "public, s-maxage=600, stale-while-revalidate=86400" } });
}
