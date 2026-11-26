import Link from "next/link";
import { JsonLd } from "@/components/JsonLd";
import { absolute, pageMetadata } from "@/lib/seo";
import { CONTACT_EMAIL, SITE_NAME } from "@/lib/site";

export const metadata = pageMetadata({
  title: "Editorial policy: how we verify and write",
  description: "How Patchbeast verifies release dates, patches and requirements, how we use AI to draft briefings, how every item is reviewed, and how to request a correction.",
  path: "/editorial-policy",
  indexable: true,
});

export default function EditorialPolicy() {
  return (
    <article className="prose-pb mx-auto max-w-3xl">
      <JsonLd data={{ "@context": "https://schema.org", "@type": "WebPage", name: "Editorial policy", url: absolute("/editorial-policy"), isPartOf: { "@id": absolute("/#website") }, publisher: { "@id": absolute("/#organization") } }} />
      <h1 className="font-display text-3xl font-bold tracking-tight">Editorial policy</h1>
      <p>{SITE_NAME} is an independent tracker. This page explains how information gets onto the site, so you can judge how much to trust it.</p>

      <h2>1. Sources first</h2>
      <p>Every release date, patch, requirement and news item links to its source. We prefer official feeds and announcements, and we never copy other sites&apos; articles: we store a headline, the link and our own short summary.</p>

      <h2>2. Verification labels</h2>
      <ul>
        <li><strong>Confirmed</strong>: two independent sources (different outlets), or a video.</li>
        <li><strong>Reported</strong>: one linked source.</li>
        <li><strong>Rumour</strong>: unverified. We label it and never run a countdown on it.</li>
      </ul>
      <p>Two pages from the same outlet are not independent. Where sources disagree, we say so.</p>

      <h2>3. What is automated, and what is not</h2>
      <ul>
        <li>Software collects headlines from feeds, removes duplicates and groups related reports.</li>
        <li>Structured facts (dates, patch versions, requirements) may be published automatically only when they carry a source link and pass confidence and conflict checks. A confirmed fact is never overwritten by a single new report.</li>
        <li>Written pieces (briefings, roundups, news) are drafted by an AI assistant from our own summaries of the linked reports, then <strong>checked and approved by a person before they are published</strong>. Drafts must cite their sources; anything that cannot be traced to a source is rejected.</li>
      </ul>

      <h2>4. Independence and money</h2>
      <p>We are not affiliated with any publisher or developer. If advertising or affiliate links are enabled they never influence what we report or how an item is labelled; affiliate links are marked and explained on the <Link href="/affiliate-disclosure">affiliate disclosure</Link> page.</p>

      <h2>5. Corrections</h2>
      <p>If something is wrong, email <a href={`mailto:${CONTACT_EMAIL}`}>{CONTACT_EMAIL}</a> with the page and the correct source. We fix verified errors promptly and note material corrections on the page. See also our <Link href="/contact">contact and takedown</Link> page.</p>

      <h2>6. Update frequency</h2>
      <p>Pages refresh within seconds of a change. Each item shows its date, and the timeline for every game lists what changed and when.</p>
    </article>
  );
}
