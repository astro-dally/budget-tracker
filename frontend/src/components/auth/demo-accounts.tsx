"use client";

import { useQuery } from "@tanstack/react-query";
import { ArrowRight, Loader2, ShieldCheck } from "lucide-react";
import { UserAvatar } from "@/components/layout/user-avatar";
import { api } from "@/lib/api";
import type { DemoAccount } from "@/lib/types";

/** One-click demo logins, served by the backend when demo data is enabled. */
export function DemoAccounts({
  onPick,
  pending,
}: {
  onPick: (account: DemoAccount) => void;
  pending: string | null;
}) {
  const { data } = useQuery({ queryKey: ["demo-accounts"], queryFn: api.auth.demoAccounts, staleTime: Infinity });
  if (!data || data.length === 0) return null;
  return (
    <section aria-labelledby="demo-heading" className="mt-8">
      <div className="flex items-center gap-3">
        <span className="h-px flex-1 bg-border" />
        <h2 id="demo-heading" className="text-xs text-muted-foreground">
          or jump into a demo account
        </h2>
        <span className="h-px flex-1 bg-border" />
      </div>
      <ul className="mt-4 grid gap-2 sm:grid-cols-2">
        {data.map((account) => (
          <li key={account.email}>
            <button
              type="button"
              onClick={() => onPick(account)}
              disabled={pending !== null}
              className="group flex h-full w-full items-start gap-3 rounded-xl border bg-card p-3 text-left transition-colors outline-none hover:border-primary/50 hover:bg-accent focus-visible:ring-[3px] focus-visible:ring-ring/40 disabled:opacity-60"
            >
              <UserAvatar name={account.name} />
              <span className="min-w-0 flex-1">
                <span className="flex items-center gap-1.5 text-sm font-semibold">
                  {account.name}
                  {account.role === "admin" ? (
                    <ShieldCheck className="size-3.5 text-primary" aria-label="Administrator" />
                  ) : null}
                </span>
                <span className="mt-0.5 line-clamp-2 block text-xs text-muted-foreground">{account.tagline}</span>
              </span>
              {pending === account.email ? (
                <Loader2 className="size-4 animate-spin text-muted-foreground" />
              ) : (
                <ArrowRight className="size-4 text-muted-foreground opacity-0 transition-opacity group-hover:opacity-100" />
              )}
            </button>
          </li>
        ))}
      </ul>
    </section>
  );
}
