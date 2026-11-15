import { OctagonAlert, TriangleAlert } from "lucide-react";
import type { AlertLevel } from "@/lib/types";
import { cn } from "@/lib/utils";

export function AlertLevelIcon({ level, className }: { level: AlertLevel; className?: string }) {
  const critical = level === "critical";
  const Icon = critical ? OctagonAlert : TriangleAlert;
  return (
    <span
      className={cn(
        "flex size-8 shrink-0 items-center justify-center rounded-lg",
        critical ? "bg-danger/12 text-danger" : "bg-warning/12 text-warning",
        className,
      )}
    >
      <Icon className="size-4" aria-hidden="true" />
      <span className="sr-only">{critical ? "Over budget" : "Warning"}</span>
    </span>
  );
}
