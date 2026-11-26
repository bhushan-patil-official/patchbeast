import Link from "next/link";
import { pageMetadata } from "@/lib/seo";
import { CONTACT_EMAIL } from "@/lib/site";

export const metadata = pageMetadata({ title: "Privacy policy", description: "How Patchbeast handles data: cookieless analytics, the double opt-in newsletter, short-lived server logs, and third parties such as YouTube.", path: "/privacy", indexable: true });

export default function Page() {
  return (
    <article className="prose-pb mx-auto max-w-3xl">
      <h1 className="font-display text-3xl font-bold tracking-tight">Privacy policy</h1>

      <p>We collect as little as we can.</p>
      <h2>Analytics</h2>
      <p>If enabled, we use a privacy-friendly, cookieless analytics service (Plausible or Umami) that records aggregate page views without personal profiles.</p>
      <h2>Newsletter</h2>
      <p>If you subscribe we store your email address and the time you confirmed. We use it only to send the weekly digest. Subscription is double opt-in, and every email has an unsubscribe link. Unsubscribing stops all sending; you can ask us to delete your address at any time.</p>
      <h2>Server logs</h2>
      <p>Our servers keep short-lived technical logs (IP address, request path, status) for security and debugging, and delete them on a rolling basis.</p>
      <h2>Third parties</h2>
      <p>Videos load from YouTube (privacy-enhanced mode) only after you press play. If advertising or affiliate links are enabled, those partners may set their own cookies; we will say so here and on the <Link href="/affiliate-disclosure">affiliate disclosure</Link> page.</p>
      <h2>Contact</h2>
      <p>Questions or deletion requests: <a href={`mailto:${CONTACT_EMAIL}`}>{CONTACT_EMAIL}</a>.</p>
    </article>
  );
}
