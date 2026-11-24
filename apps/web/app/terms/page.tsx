import { pageMetadata } from "@/lib/seo";

export const metadata = pageMetadata({ title: "Terms of use", description: "Terms for using Patchbeast.", path: "/terms", indexable: true });

export default function Page() {
  return (
    <article className="prose-pb mx-auto max-w-3xl">
      <h1 className="font-display text-3xl font-bold tracking-tight">Terms of use</h1>

      <p>By using Patchbeast you agree to these terms.</p>
      <h2>Information, not advice</h2>
      <p>Content is provided for information. We work hard to label verification status, but dates, patch contents and requirements can change. The &ldquo;can my PC run it&rdquo; checker uses approximate hardware tiers and is not a guarantee.</p>
      <h2>Sources and attribution</h2>
      <p>Third-party material is linked, not reproduced. All trademarks and content belong to their owners.</p>
      <h2>Acceptable use</h2>
      <p>Do not abuse the site, attempt to disrupt it, or scrape it at a rate that harms service.</p>
      <h2>Liability</h2>
      <p>The site is provided &ldquo;as is&rdquo;, without warranties, and to the extent permitted by law we are not liable for losses arising from its use.</p>
    </article>
  );
}
