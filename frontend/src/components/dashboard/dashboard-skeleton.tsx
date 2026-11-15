import { Skeleton } from "@/components/ui/skeleton";

export function DashboardSkeleton() {
  return (
    <div className="grid gap-6" aria-busy="true" aria-label="Loading overview">
      <Skeleton className="h-56 rounded-2xl" />
      <Skeleton className="h-32 rounded-xl" />
      <div className="grid gap-6 lg:grid-cols-5">
        <Skeleton className="h-80 rounded-xl lg:col-span-3" />
        <Skeleton className="h-80 rounded-xl lg:col-span-2" />
      </div>
    </div>
  );
}
