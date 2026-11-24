import { pageMetadata } from "@/lib/seo";
import { CONTACT_EMAIL } from "@/lib/site";

export const metadata = pageMetadata({ title: "About Patchbeast", description: "What Patchbeast is, how we verify information, and how our bot behaves.", path: "/about", indexable: true });

export default function Page() {
  return (
    <article className="prose-pb mx-auto max-w-3xl">
      <h1 className="font-display text-3xl font-bold tracking-tight">About Patchbeast</h1>

      <p>Patchbeast is a tracker and a set of tools for people watching huge PC game launches. We keep release dates, patch notes, system requirements and videos in one place, and label every item with where it came from and how well it is verified.</p>
      <h2>What we do and do not do</h2>
      <ul>
        <li>We store a headline, a link to the original source and our own short summary. We do not copy or republish other sites&apos; articles.</li>
        <li>Facts such as release dates, patch versions and requirements are published automatically only when they carry a source link and pass our confidence checks. Everything written, like news, is reviewed by a person first.</li>
        <li>We never show a countdown for a rumoured date. The clock shows &ldquo;Date unconfirmed&rdquo; until a date is reported or confirmed.</li>
      </ul>
      <h2>Verification</h2>
      <p><strong>Confirmed</strong> means two independent sources, or a video. <strong>Reported</strong> means one linked source. <strong>Rumour</strong> means unverified.</p>
      <h2 id="bot">Our bot</h2>
      <p>We read official RSS feeds and APIs using the user agent <code>PatchbeastBot/1.0</code>, with conditional requests (ETag / If-Modified-Since), low frequency, and respect for robots.txt. If you run a source and want us to stop, email <a href={`mailto:${CONTACT_EMAIL}`}>{CONTACT_EMAIL}</a>.</p>
      <h2>Independence</h2>
      <p>Patchbeast is not affiliated with, endorsed by or sponsored by any game publisher or developer. Game titles are trademarks of their owners and are used only to describe what is being tracked.</p>
    </article>
  );
}
