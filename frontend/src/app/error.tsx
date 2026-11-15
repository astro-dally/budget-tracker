"use client";

import { ErrorState } from "@/components/shared/states";

export default function GlobalError({ error, reset }: { error: Error; reset: () => void }) {
  return <ErrorState error={error} onRetry={reset} className="py-24" />;
}
