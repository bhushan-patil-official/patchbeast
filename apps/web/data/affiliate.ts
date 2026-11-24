/**
 * Affiliate hardware suggestions. EMPTY by default: nothing renders until BOTH the `affiliate`
 * feature flag is on AND items exist here. Add real tracking links from your approved programs.
 */
export interface AffiliateItem {
  category: "gpu" | "cpu" | "ssd" | "ram";
  title: string;
  blurb: string;
  merchant: string; // e.g. "Amazon", "Newegg", "Best Buy"
  href: string;
  price?: string;
}
export const AFFILIATE_ITEMS: AffiliateItem[] = [];
