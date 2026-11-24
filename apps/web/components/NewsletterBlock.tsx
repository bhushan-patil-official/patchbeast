import { Card } from "@patchbeast/design-system";
import { flags } from "@/lib/api";
import { NewsletterForm } from "./NewsletterForm";

export async function NewsletterBlock() {
  const f = await flags();
  if (f.newsletter === false) return null;
  return (
    <Card className="p-6">
      <h2 className="font-display text-xl font-semibold">Weekly digest of confirmed changes</h2>
      <p className="mt-1 max-w-prose text-sm text-fg-muted">
        Only confirmed dates, patches and requirements, each with its source. Double opt-in, one email a
        week, one-click unsubscribe.
      </p>
      <div className="mt-4 max-w-xl"><NewsletterForm /></div>
    </Card>
  );
}
