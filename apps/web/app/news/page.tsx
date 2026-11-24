import Link from "next/link";
import { NewsCard, Degraded } from "@/components/Cards";
import { StoryCard } from "@/components/StoryCard";
import { api } from "@/lib/api";
import { pageMetadata } from "@/lib/seo";

export const revalidate = 300;
type Props = { searchParams: Promise<{ page?: string; game?: string }> };

export async function generateMetadata({ searchParams }: Props) {
  const { page, game } = await searchParams;
  const [r, s] = await Promise.all([api.news(1), api.stories()]);
  // Only the unfiltered first page is an index target; filtered/paginated views are navigation aids.
  const has = (r.ok && r.data.count > 0) || (s.ok && s.data.count > 0);
  return pageMetadata({
    title: "News and briefings: curated, with sources",
    description: "Our own briefings and roundups plus hand-picked links, filterable by game. Every item shows its sources and verification status.",
    path: "/news",
    indexable: has && !page && !game,
  });
}

export default async function News({ searchParams }: Props) {
  const sp = await searchParams;
  const page = Math.max(1, Number(sp.page) || 1);
  const games = await api.games();
  const slugs = games.ok ? games.data.map((g) => g.slug) : [];
  const game = sp.game && slugs.includes(sp.game) ? sp.game : undefined;
  const [r, stories] = await Promise.all([api.news(page, game), api.stories(game)]);
  const current = games.ok ? games.data.find((g) => g.slug === game) : undefined;

  const href = (g?: string, p?: number) => {
    const q = new URLSearchParams();
    if (g) q.set("game", g);
    if (p && p > 1) q.set("page", String(p));
    const s = q.toString();
    return s ? `/news?${s}` : "/news";
  };
  const chip = (active: boolean) =>
    `pb-focus rounded-full border px-3 py-1 text-sm ${active ? "border-accent bg-accent/15 text-fg" : "border-line text-fg-muted hover:text-fg"}`;

  return (
    <>
      <h1 className="font-display text-3xl font-bold tracking-tight">{current ? `${current.name}: news` : "News"}</h1>
      <p className="mt-2 max-w-prose text-fg-muted">
        Briefings and roundups we write from several linked sources, plus hand-picked links. A person approves every item.
      </p>

      {games.ok && games.data.length > 1 && (
        <nav aria-label="Filter by game" className="mt-4 flex flex-wrap gap-2" data-testid="game-filter">
          <Link href="/news" className={chip(!game)} aria-current={!game ? "true" : undefined}>All games</Link>
          {games.data.map((g) => (
            <Link key={g.slug} href={href(g.slug)} className={chip(game === g.slug)} aria-current={game === g.slug ? "true" : undefined} data-testid={`filter-${g.slug}`}>{g.name}</Link>
          ))}
        </nav>
      )}

      {stories.ok && stories.data.results.length > 0 && (
        <section aria-labelledby="briefings-h" className="mt-8">
          <h2 id="briefings-h" className="font-display text-xl font-semibold">Briefings and roundups</h2>
          <div className="mt-3 space-y-3">{stories.data.results.map((s) => <StoryCard key={s.id} s={s} />)}</div>
        </section>
      )}

      <h2 className="mt-8 font-display text-xl font-semibold">Linked news</h2>
      <div className="mt-3 space-y-4">
        {r.ok ? (
          r.data.results.length ? r.data.results.map((a) => <NewsCard key={a.id} a={a} />) : <p className="text-fg-muted" data-testid="no-linked">No curated news{current ? ` for ${current.name}` : ""} yet.</p>
        ) : <Degraded what="News" />}
      </div>
      {r.ok && (r.data.next || r.data.previous) && (
        <nav aria-label="Pagination" className="mt-6 flex gap-4 text-sm">
          {r.data.previous && <Link className="text-accent-text underline" href={href(game, page - 1)}>← Newer</Link>}
          {r.data.next && <Link className="text-accent-text underline" href={href(game, page + 1)}>Older →</Link>}
        </nav>
      )}
    </>
  );
}
