import { TokenAction } from "@/components/TokenAction";
import { noindex } from "@/lib/seo";

export const metadata = { title: "Confirm subscription", ...noindex };
export const dynamic = "force-dynamic";

export default async function Confirm({ searchParams }: { searchParams: Promise<{ token?: string }> }) {
  const { token = "" } = await searchParams;
  return (
    <div className="mx-auto max-w-lg py-10">
      <h1 className="font-display text-2xl font-semibold">Confirm your subscription</h1>
      <p className="my-3 text-fg-muted">One click and the weekly digest of confirmed changes is yours.</p>
      <TokenAction token={token} action="confirm" cta="Confirm subscription" done="You're subscribed. See you on Monday." failed="That link is invalid or expired." />
    </div>
  );
}
