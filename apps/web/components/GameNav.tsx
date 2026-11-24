import Link from "next/link";
import { cn } from "@patchbeast/design-system";
import type { Schemas } from "@/lib/api";
import { JsonLd } from "./JsonLd";
import { absolute } from "@/lib/seo";

export type GameSectionKey = "overview" | "patches" | "news" | "videos" | "requirements" | "timeline";

/** Section tabs shown on every game page: each section has its own page. */
export function GameNav({ game, current }: { game: Schemas["GameCard"]; current: GameSectionKey }) {
  const base = `/games/${game.slug}`;
  const items: { key: GameSectionKey; label: string; href: string }[] = [
    { key: "overview", label: "Overview", href: game.path },
    { key: "patches", label: "Patches & updates", href: `${base}/patches` },
    { key: "news", label: "News", href: `${base}/news` },
    { key: "videos", label: "Videos", href: `${base}/videos` },
    ...(game.platforms.some((p) => p.id === "pc") ? [{ key: "requirements" as const, label: "PC requirements", href: `${base}/requirements` }] : []),
    { key: "timeline", label: "Timeline", href: `${base}/timeline` },
  ];
  return (
    <nav aria-label={`${game.name} sections`} className="-mx-4 my-6 overflow-x-auto px-4" data-testid="game-nav">
      <ul className="flex min-w-max gap-1 border-b border-line">
        {items.map((i) => {
          const active = i.key === current;
          return (
            <li key={i.key}>
              <Link
                href={i.href}
                aria-current={active ? "page" : undefined}
                className={cn(
                  "pb-focus inline-block rounded-t px-3 py-2 text-sm font-medium transition-colors",
                  active ? "border-b-2 border-accent text-fg" : "border-b-2 border-transparent text-fg-muted hover:text-fg",
                )}
              >
                {i.label}
              </Link>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}

export type Crumb = { name: string; href?: string };

/** Visible breadcrumbs + BreadcrumbList JSON-LD (only real, linkable pages). */
export function Breadcrumbs({ crumbs }: { crumbs: Crumb[] }) {
  return (
    <>
      <nav aria-label="Breadcrumb" className="mb-3 text-xs text-fg-muted">
        <ol className="flex flex-wrap items-center gap-1.5">
          {crumbs.map((c, i) => (
            <li key={c.name + i} className="flex items-center gap-1.5">
              {c.href ? <Link href={c.href} className="pb-focus rounded hover:text-fg hover:underline">{c.name}</Link> : <span aria-current="page" className="text-fg">{c.name}</span>}
              {i < crumbs.length - 1 && <span aria-hidden="true">/</span>}
            </li>
          ))}
        </ol>
      </nav>
      <JsonLd
        data={{
          "@context": "https://schema.org",
          "@type": "BreadcrumbList",
          itemListElement: crumbs.map((c, i) => ({
            "@type": "ListItem",
            position: i + 1,
            name: c.name,
            ...(c.href ? { item: absolute(c.href) } : {}),
          })),
        }}
      />
    </>
  );
}
