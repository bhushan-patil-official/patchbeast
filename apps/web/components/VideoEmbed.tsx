"use client";
import { useState } from "react";

/** Click-to-load YouTube (privacy-enhanced domain). No iframe/JS cost until the user asks for it. */
export function VideoEmbed({ id, title }: { id: string; title: string }) {
  const [on, setOn] = useState(false);
  return (
    <div className="relative aspect-video w-full overflow-hidden rounded-lg border border-line bg-surface-2">
      {on ? (
        <iframe
          className="absolute inset-0 h-full w-full"
          src={`https://www.youtube-nocookie.com/embed/${encodeURIComponent(id)}?autoplay=1&rel=0`}
          title={title}
          allow="autoplay; encrypted-media; picture-in-picture"
          allowFullScreen
        />
      ) : (
        <button type="button" onClick={() => setOn(true)} className="pb-focus group absolute inset-0 h-full w-full" aria-label={`Play video: ${title}`}>
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={`https://i.ytimg.com/vi/${encodeURIComponent(id)}/hqdefault.jpg`} alt="" width={480} height={360} loading="lazy" className="h-full w-full object-cover opacity-80 transition group-hover:opacity-100" />
          <span className="absolute inset-0 grid place-items-center">
            <span className="grid h-14 w-14 place-items-center rounded-full bg-accent-strong text-accent-on shadow-glow" aria-hidden="true">▶</span>
          </span>
        </button>
      )}
    </div>
  );
}
