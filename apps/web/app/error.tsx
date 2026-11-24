"use client";
import { Button } from "@patchbeast/design-system";

export default function Error({ reset }: { error: Error; reset: () => void }) {
  return (
    <div className="py-16 text-center">
      <h1 className="font-display text-2xl font-semibold">Something went wrong</h1>
      <p className="mt-2 text-fg-muted">The data service didn&apos;t answer. Try again in a moment.</p>
      <Button className="mt-6" onClick={reset}>Retry</Button>
    </div>
  );
}
