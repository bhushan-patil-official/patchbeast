import { pageMetadata } from "@/lib/seo";
import { CONTACT_EMAIL } from "@/lib/site";

export const metadata = pageMetadata({ title: "Contact and takedowns", description: "Contact Patchbeast, report an error, or send a DMCA / takedown request.", path: "/contact", indexable: true });

export default function Page() {
  return (
    <article className="prose-pb mx-auto max-w-3xl">
      <h1 className="font-display text-3xl font-bold tracking-tight">Contact and takedowns</h1>

      <p>Email <a href={`mailto:${CONTACT_EMAIL}`}>{CONTACT_EMAIL}</a>.</p>
      <h2>Corrections</h2>
      <p>If something is wrong, tell us which page and which source is correct. We fix verified errors quickly and note material corrections.</p>
      <h2>DMCA / takedown</h2>
      <p>We store only titles, links and our own summaries, but if you believe something on Patchbeast infringes your rights, email the address above with: the URL on Patchbeast, the work you believe is infringed, your contact details, and a statement made in good faith. We aim to respond within two business days and will remove material that is validly challenged.</p>
      <h2>Source owners</h2>
      <p>If you operate a feed we read and want us to stop or slow down, email us and we will do so promptly.</p>
    </article>
  );
}
