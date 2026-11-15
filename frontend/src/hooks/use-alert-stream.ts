"use client";

import { useQueryClient } from "@tanstack/react-query";
import { useEffect } from "react";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { session } from "@/lib/session";
import type { Alert } from "@/lib/types";

/**
 * Subscribe to the signed-in user's Server-Sent Events stream. Each alert shows a
 * toast and refreshes the views it affects. EventSource reconnects on its own.
 */
export function useAlertStream(): void {
  const client = useQueryClient();

  useEffect(() => {
    const token = session.getToken();
    if (!token) return;
    const source = new EventSource(api.alerts.streamUrl(token));

    const onAlert = (event: MessageEvent<string>) => {
      const alert = JSON.parse(event.data) as Alert;
      const notify = alert.level === "critical" ? toast.error : toast.warning;
      notify(alert.level === "critical" ? "Over budget" : "Budget warning", {
        description: alert.message,
        action: { label: "View", onClick: () => window.location.assign("/app/alerts") },
      });
      void client.invalidateQueries({ queryKey: ["alerts"] });
      void client.invalidateQueries({ queryKey: ["dashboard"] });
      void client.invalidateQueries({ queryKey: ["budgets"] });
    };

    source.addEventListener("alert", onAlert);
    return () => {
      source.removeEventListener("alert", onAlert);
      source.close();
    };
  }, [client]);
}
