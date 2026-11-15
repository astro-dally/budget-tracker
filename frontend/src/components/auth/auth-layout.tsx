import { OctagonAlert, TriangleAlert } from "lucide-react";
import type { ReactNode } from "react";
import { Brand } from "@/components/layout/brand";
import { ThemeToggle } from "@/components/layout/theme-toggle";

/** Split layout: the form on the left, a live-looking ledger panel on the right. */
export function AuthLayout({ children }: { children: ReactNode }) {
  return (
    <div className="grid min-h-dvh lg:grid-cols-[1fr_1.05fr]">
      <div className="flex flex-col px-5 py-6 sm:px-10">
        <div className="flex items-center justify-between">
          <Brand href="/" />
          <ThemeToggle />
        </div>
        <main id="main" className="mx-auto flex w-full max-w-md flex-1 flex-col justify-center py-10">
          {children}
        </main>
      </div>

      <aside
        aria-hidden="true"
        className="relative hidden overflow-hidden bg-gradient-to-br from-ledger to-ledger-2 p-12 text-white lg:flex lg:flex-col lg:justify-between"
      >
        <div className="ledger-grid absolute inset-0" />
        <div className="pointer-events-none absolute -top-32 -right-24 size-[28rem] rounded-full bg-lime/25 blur-3xl" />
        <div className="relative">
          <p className="text-sm text-white/60">This month, so far</p>
          <p className="mt-3 font-display text-7xl font-semibold tracking-[-0.04em] tabular">₹14,290</p>
          <p className="mt-2 text-white/70">left to spend, 17 days to go</p>
          <div className="relative mt-10 h-4 max-w-md rounded-full bg-white/10 ring-1 ring-white/10">
            <div className="absolute inset-y-0 left-0 w-[77%] rounded-full bg-gradient-to-r from-emerald-300 to-gold" />
            <div className="absolute -top-2 -bottom-2 left-[43%] w-0.5 bg-white">
              <span className="absolute bottom-full left-1/2 mb-1.5 -translate-x-1/2 rounded-full bg-white px-2 py-0.5 text-[11px] font-semibold text-ledger">
                Today
              </span>
            </div>
          </div>
        </div>

        <div className="relative grid max-w-sm gap-3">
          <div className="flex animate-float items-start gap-3 rounded-2xl bg-white p-4 text-ledger shadow-2xl">
            <span className="flex size-9 items-center justify-center rounded-xl bg-amber-100 text-amber-700">
              <TriangleAlert className="size-4" />
            </span>
            <span className="text-sm">
              <span className="block font-semibold">Budget warning</span>
              Food & Dining passed 80% of its budget.
            </span>
          </div>
          <div className="ml-10 flex animate-float items-start gap-3 rounded-2xl bg-white p-4 text-ledger shadow-2xl [animation-delay:1.5s]">
            <span className="flex size-9 items-center justify-center rounded-xl bg-red-100 text-red-700">
              <OctagonAlert className="size-4" />
            </span>
            <span className="text-sm">
              <span className="block font-semibold">Over budget</span>
              Entertainment is ₹280 over this month.
            </span>
          </div>
          <p className="mt-6 font-display text-3xl leading-tight font-semibold tracking-tight">
            Warned at 80%, not surprised at 100%.
          </p>
        </div>
      </aside>
    </div>
  );
}
