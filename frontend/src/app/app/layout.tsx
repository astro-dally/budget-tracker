"use client";

import type { ReactNode } from "react";
import { AuthGuard } from "@/components/auth-guard";
import { AppShell } from "@/components/layout/app-shell";
import { NAV_ITEMS } from "@/components/layout/nav-items";
import { MonthProvider } from "@/components/month-context";
import { useAlertStream } from "@/hooks/use-alert-stream";

function AlertStream() {
  useAlertStream();
  return null;
}

export default function AppLayout({ children }: { children: ReactNode }) {
  return (
    <AuthGuard>
      <MonthProvider>
        <AlertStream />
        <AppShell nav={NAV_ITEMS}>{children}</AppShell>
      </MonthProvider>
    </AuthGuard>
  );
}
