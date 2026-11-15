"use client";

import { usePathname, useRouter } from "next/navigation";
import { useEffect, type ReactNode } from "react";
import { useAuth } from "@/lib/auth";

function FullScreenLoader() {
  return (
    <div className="flex min-h-dvh items-center justify-center" aria-busy="true" aria-label="Loading">
      <div className="size-10 animate-spin rounded-full border-[3px] border-primary/20 border-t-primary" />
    </div>
  );
}

/** Renders children only for signed-in users (and admins, when `admin` is set). */
export function AuthGuard({ children, admin = false }: { children: ReactNode; admin?: boolean }) {
  const { status, user, signedOut } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    if (status === "anonymous") {
      router.replace(signedOut ? "/login" : `/login?next=${encodeURIComponent(pathname)}`);
    } else if (status === "authenticated" && admin && user?.role !== "admin") {
      router.replace("/app");
    }
  }, [status, user, signedOut, admin, router, pathname]);

  if (status !== "authenticated" || (admin && user?.role !== "admin")) {
    return <FullScreenLoader />;
  }
  return <>{children}</>;
}
