import { TokenAction } from "@/components/TokenAction";
import { noindex } from "@/lib/seo";

export const metadata = { title: "Unsubscribe", ...noindex };
export const dynamic = "force-dynamic";

export default async function Unsub({ searchParams }: { searchParams: Promise<{ token?: string }> }) {
  const { token = "" } = await searchParams;
  return (
    <div className="mx-auto max-w-lg py-10">
      <h1 className="font-display text-2xl font-semibold">Unsubscribe</h1>
      <p className="my-3 text-fg-muted">We&apos;re sorry to see you go. This stops the weekly digest immediately.</p>
      <TokenAction token={token} action="unsubscribe" cta="Unsubscribe" done="You're unsubscribed." failed="That link is invalid." />
    </div>
  );
}
