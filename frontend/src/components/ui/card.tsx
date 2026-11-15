import type * as React from "react";
import { cn } from "@/lib/utils";

function Card({ className, ...props }: React.ComponentProps<"div">) {
  return (
    <div
      className={cn(
        "rounded-xl border bg-card text-card-foreground shadow-[0_1px_2px_rgb(16_32_24/0.04)]",
        className,
      )}
      {...props}
    />
  );
}

function CardHeader({ className, ...props }: React.ComponentProps<"div">) {
  return (
    <div
      className={cn("flex items-start justify-between gap-4 px-5 pt-5 sm:px-6 sm:pt-6", className)}
      {...props}
    />
  );
}

function CardTitle({ className, ...props }: React.ComponentProps<"h2">) {
  return <h2 className={cn("text-base font-semibold tracking-tight", className)} {...props} />;
}

function CardDescription({ className, ...props }: React.ComponentProps<"p">) {
  return <p className={cn("mt-1 text-sm text-muted-foreground", className)} {...props} />;
}

function CardContent({ className, ...props }: React.ComponentProps<"div">) {
  return <div className={cn("px-5 py-5 sm:px-6", className)} {...props} />;
}

export { Card, CardContent, CardDescription, CardHeader, CardTitle };
