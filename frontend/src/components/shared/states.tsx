import { AlertCircle, RotateCw, type LucideIcon } from "lucide-react";
import type { ReactNode } from "react";
import { Button } from "@/components/ui/button";
import { errorMessage } from "@/lib/api";
import { cn } from "@/lib/utils";

export function EmptyState({
  icon: Icon,
  title,
  description,
  action,
  className,
}: {
  icon: LucideIcon;
  title: string;
  description: string;
  action?: ReactNode;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center gap-3 px-6 py-12 text-center",
        className,
      )}
    >
      <span className="flex size-11 items-center justify-center rounded-xl bg-muted text-muted-foreground">
        <Icon className="size-5" aria-hidden="true" />
      </span>
      <div className="max-w-sm">
        <p className="font-medium">{title}</p>
        <p className="mt-1 text-sm text-muted-foreground">{description}</p>
      </div>
      {action}
    </div>
  );
}

export function ErrorState({
  error,
  onRetry,
  className,
}: {
  error: unknown;
  onRetry?: () => void;
  className?: string;
}) {
  return (
    <div
      role="alert"
      className={cn(
        "flex flex-col items-center justify-center gap-3 px-6 py-10 text-center",
        className,
      )}
    >
      <span className="flex size-11 items-center justify-center rounded-xl bg-danger/10 text-danger">
        <AlertCircle className="size-5" aria-hidden="true" />
      </span>
      <div className="max-w-md">
        <p className="font-medium">This section didn&apos;t load</p>
        <p className="mt-1 text-sm text-muted-foreground">{errorMessage(error)}</p>
      </div>
      {onRetry ? (
        <Button variant="outline" size="sm" onClick={onRetry}>
          <RotateCw /> Try again
        </Button>
      ) : null}
    </div>
  );
}
