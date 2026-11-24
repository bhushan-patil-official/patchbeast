import { pageMetadata } from "@/lib/seo";

export const metadata = pageMetadata({ title: "Affiliate disclosure", description: "How Patchbeast earns money and how it affects what we show.", path: "/affiliate-disclosure", indexable: true });

export default function Page() {
  return (
    <article className="prose-pb mx-auto max-w-3xl">
      <h1 className="font-display text-3xl font-bold tracking-tight">Affiliate disclosure</h1>

      <p>Some hardware suggestions on Patchbeast contain affiliate links to retailers such as Amazon, Newegg or Best Buy. If you buy through one, we may earn a commission at no extra cost to you.</p>
      <h2>How it affects content</h2>
      <ul>
        <li>Affiliate links never change a verification status, a date or a requirement.</li>
        <li>Links are marked <code>rel=&quot;sponsored&quot;</code> and every block carries a disclosure.</li>
        <li>No affiliate links appear on the site until the program is configured; this page describes the policy in advance.</li>
      </ul>
    </article>
  );
}
