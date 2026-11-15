import { cn } from "@/lib/utils";

const GRADIENTS = [
  "from-emerald-400 to-teal-600",
  "from-amber-300 to-orange-500",
  "from-sky-400 to-indigo-500",
  "from-fuchsia-400 to-rose-500",
  "from-lime-300 to-emerald-500",
  "from-violet-400 to-purple-600",
];

export function initials(name: string): string {
  const parts = name.trim().split(/\s+/);
  return ((parts[0]?.[0] ?? "") + (parts.length > 1 ? (parts.at(-1)?.[0] ?? "") : "")).toUpperCase();
}

/** Initials on a gradient picked deterministically from the name. */
export function UserAvatar({ name, className }: { name: string; className?: string }) {
  const hash = [...name].reduce((sum, char) => sum + char.charCodeAt(0), 0);
  return (
    <span
      aria-hidden="true"
      className={cn(
        "inline-flex size-8 shrink-0 items-center justify-center rounded-full bg-gradient-to-br text-xs font-semibold text-white",
        GRADIENTS[hash % GRADIENTS.length],
        className,
      )}
    >
      {initials(name)}
    </span>
  );
}
