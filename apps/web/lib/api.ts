import { createApi, type Schemas } from "@patchbeast/api-client";
import { REVALIDATE_SECONDS } from "./site";

export type { Schemas };

/** Server-side base (internal network on a VPS, public API origin on Vercel). */
const SERVER_BASE = process.env.API_INTERNAL_URL || process.env.NEXT_PUBLIC_API_BASE_URL || "";
/** Browser base. Empty = same origin (Caddy routes /api to Django). */
export const BROWSER_API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "";

export type Result<T> = { ok: true; data: T } | { ok: false; status: number };

const withIsr =
  (tags: string[]): typeof fetch =>
  (input, init) =>
    fetch(input, { ...init, next: { revalidate: REVALIDATE_SECONDS, tags } });

const client = (tags: string[]) => createApi(SERVER_BASE, withIsr(tags));

/** Never throws: an unreachable API (e.g. during a build) degrades the page instead of failing it. */
async function call<T>(run: () => Promise<{ data?: T; response: Response }>): Promise<Result<T>> {
  try {
    const { data, response } = await run();
    if (response.ok && data !== undefined) return { ok: true, data };
    return { ok: false, status: response.status };
  } catch {
    return { ok: false, status: 0 };
  }
}

export const api = {
  games: () => call(() => client(["games"]).GET("/api/v1/games/")),
  hub: (slug: string) =>
    call(() => client([`game:${slug}`]).GET("/api/v1/games/{slug}/", { params: { path: { slug } } })),
  patches: (slug: string, platform?: string) =>
    call(() =>
      client([`game:${slug}`]).GET("/api/v1/games/{slug}/patches/", {
        params: { path: { slug }, query: platform ? { platform } : {} },
      }),
    ),
  videos: (slug: string) =>
    call(() => client([`game:${slug}`, "videos"]).GET("/api/v1/games/{slug}/videos/", { params: { path: { slug } } })),
  requirements: (slug: string) =>
    call(() => client([`game:${slug}`]).GET("/api/v1/games/{slug}/requirements/", { params: { path: { slug } } })),
  ticker: () => call(() => client(["ticker"]).GET("/api/v1/ticker/")),
  news: (page = 1, game?: string) =>
    call(() =>
      client(game ? ["news", `game:${game}`] : ["news"]).GET("/api/v1/news/", {
        params: { query: game ? { page, game } : { page } },
      }),
    ),
  patch: (slug: string, platform: string, version: string) =>
    call(() =>
      client([`game:${slug}`]).GET("/api/v1/games/{slug}/patches/{platform}/{version}/", {
        params: { path: { slug, platform, version } },
      }),
    ),
  changes: (slug: string, page = 1) =>
    call(() =>
      client([`game:${slug}`]).GET("/api/v1/games/{slug}/changes/", {
        params: { path: { slug }, query: { page } },
      }),
    ),
  feed: (page = 1) => call(() => client(["feed"]).GET("/api/v1/feed/", { params: { query: { page } } })),
  sitemap: () => call(() => client(["sitemap"]).GET("/api/v1/sitemap/")),
  config: () => call(() => client(["config"]).GET("/api/v1/config/")),
};

export async function flags(): Promise<Record<string, boolean>> {
  const r = await api.config();
  return r.ok ? r.data.flags : {};
}
