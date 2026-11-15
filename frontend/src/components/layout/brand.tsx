import Link from "next/link";

/** Wordmark: a small ledger-ruled mark and the product name. */
export function Brand({ href = "/app" }: { href?: string }) {
  return (
    <Link
      href={href}
      className="flex items-center gap-2.5 rounded-md outline-none focus-visible:ring-[3px] focus-visible:ring-ring/40"
    >
      <span
        aria-hidden="true"
        className="flex size-8 flex-col justify-center gap-[3px] rounded-lg bg-primary px-[7px]"
      >
        <span className="h-[2px] w-full rounded-full bg-primary-foreground" />
        <span className="h-[2px] w-3/4 rounded-full bg-primary-foreground/80" />
        <span className="h-[2px] w-1/2 rounded-full bg-primary-foreground/60" />
      </span>
      <span className="text-[15px] font-semibold tracking-tight">Budget Tracker</span>
    </Link>
  );
}
