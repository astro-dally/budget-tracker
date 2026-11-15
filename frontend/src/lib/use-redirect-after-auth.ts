"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { useCallback } from "react";
import { homeFor } from "@/lib/auth";
import type { User } from "@/lib/types";

/** Go to ?next= if it is a safe in-app path, otherwise to the user's home. */
export function useRedirectAfterAuth(): (user: User) => void {
  const router = useRouter();
  const params = useSearchParams();
  return useCallback(
    (user: User) => {
      const next = params.get("next");
      const safe = next && next.startsWith("/") && !next.startsWith("//") && !next.startsWith("/login");
      const allowed = safe && (user.role === "admin" || !next.startsWith("/admin"));
      router.replace(allowed ? next : homeFor(user));
    },
    [params, router],
  );
}
