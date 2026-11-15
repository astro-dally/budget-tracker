"use client";

import type { ReactNode } from "react";
import { AuthGuard } from "@/components/auth-guard";
import { AppShell } from "@/components/layout/app-shell";
import { ADMIN_NAV_ITEMS } from "@/components/layout/nav-items";

export default function AdminLayout({ children }: { children: ReactNode }) {
  return (
    <AuthGuard admin>
      <AppShell nav={ADMIN_NAV_ITEMS} variant="admin">
        {children}
      </AppShell>
    </AuthGuard>
  );
}
