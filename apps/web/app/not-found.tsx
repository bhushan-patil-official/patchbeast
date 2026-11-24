import Link from "next/link";
import { noindex } from "@/lib/seo";

export const metadata = { title: "Not found", ...noindex };

export default function NotFound() {
  return (
    <div className="py-16 text-center">
      <p className="font-mono text-sm uppercase tracking-[0.2em] text-accent-text">404</p>
      <h1 className="mt-2 font-display text-3xl font-semibold">Nothing tracked here</h1>
      <p className="mt-2 text-fg-muted">That page doesn&apos;t exist (or hasn&apos;t been verified yet).</p>
      <Link href="/" className="mt-6 inline-block text-accent-text underline">Back to launches</Link>
    </div>
  );
}
