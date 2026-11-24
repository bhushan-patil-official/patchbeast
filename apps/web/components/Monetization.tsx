import { AdSlot, HardwareCard } from "@patchbeast/design-system";
import { AFFILIATE_ITEMS } from "@/data/affiliate";
import { flags } from "@/lib/api";
import { AdUnit } from "./AdUnit";

const ADS_CLIENT = process.env.NEXT_PUBLIC_ADSENSE_CLIENT || "";
const ADS_SLOT = process.env.NEXT_PUBLIC_ADSENSE_SLOT || "";

/** Nothing renders until the flag is on AND the integration is configured. */
export async function HubAd({ height = 280 }: { height?: number }) {
  const f = await flags();
  const ready = !!f.ads && !!ADS_CLIENT && !!ADS_SLOT;
  return (
    <AdSlot enabled={ready} height={height}>
      {ready ? <AdUnit client={ADS_CLIENT} slot={ADS_SLOT} /> : null}
    </AdSlot>
  );
}

export async function HardwareBlock({ categories }: { categories: string[] }) {
  const f = await flags();
  const items = AFFILIATE_ITEMS.filter((i) => categories.includes(i.category));
  if (!f.affiliate || items.length === 0) return null;
  return (
    <section aria-labelledby="hw-h" className="py-8">
      <h2 id="hw-h" className="font-display text-2xl font-semibold">Upgrade picks</h2>
      <p className="mt-1 text-sm text-fg-muted">Hardware that commonly helps on launch day. These are affiliate links.</p>
      <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {items.map((i) => (
          <HardwareCard key={i.href} category={i.category.toUpperCase()} title={i.title} blurb={i.blurb} merchant={i.merchant} href={i.href} price={i.price} />
        ))}
      </div>
    </section>
  );
}
