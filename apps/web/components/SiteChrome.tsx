import Link from "next/link";
import { StatusTicker, ThemeToggle, Wordmark } from "@patchbeast/design-system";
import { api } from "@/lib/api";
import { CONTACT_EMAIL } from "@/lib/site";

export async function Ticker() {
  const r = await api.ticker();
  if (!r.ok) return null;
  return (
    <StatusTicker
      items={r.data.map((c) => ({
        id: c.id,
        game: c.game_name,
        text: c.title + (c.detail ? ` · ${c.detail}` : ""),
        href: `/games/${c.game_slug}`,
      }))}
    />
  );
}

export function SiteHeader() {
  const link = "pb-focus rounded px-2 py-1 text-sm text-fg-muted hover:text-fg";
  return (
    <header className="border-b border-line bg-bg/90">
      <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-4 py-3">
        <Link href="/" className="pb-focus rounded" aria-label="Patchbeast home">
          <Wordmark />
        </Link>
        <nav aria-label="Main" className="flex items-center gap-1">
          <Link href="/" className={link}>Launches</Link>
          <Link href="/news" className={link}>News</Link>
          <Link href="/about" className={link}>About</Link>
          <ThemeToggle className="ml-2" />
        </nav>
      </div>
    </header>
  );
}

export function SiteFooter() {
  const link = "pb-focus rounded hover:text-fg underline-offset-2 hover:underline";
  return (
    <footer className="mt-16 border-t border-line bg-surface-1">
      <div className="mx-auto grid max-w-6xl gap-8 px-4 py-10 text-sm text-fg-muted md:grid-cols-3">
        <div>
          <Wordmark markSize={22} />
          <p className="mt-3 max-w-xs">
            An independent tracker. Every item links to its source and shows how well it is verified. We
            never republish other sites&apos; articles.
          </p>
        </div>
        <nav aria-label="Footer" className="grid grid-cols-2 gap-2">
          <Link className={link} href="/about">About</Link>
          <Link className={link} href="/editorial-policy">Editorial policy</Link>
          <Link className={link} href="/privacy">Privacy</Link>
          <Link className={link} href="/terms">Terms</Link>
          <Link className={link} href="/affiliate-disclosure">Affiliate disclosure</Link>
          <Link className={link} href="/contact">Contact &amp; takedowns</Link>
          <Link className={link} href="/news">News</Link>
        </nav>
        <p className="text-xs">
          Patchbeast is not affiliated with, endorsed by, or sponsored by any game publisher or developer.
          Game titles are trademarks of their respective owners and are used here only to describe what is
          being tracked. Contact: <a className="underline" href={`mailto:${CONTACT_EMAIL}`}>{CONTACT_EMAIL}</a>
        </p>
      </div>
    </footer>
  );
}
