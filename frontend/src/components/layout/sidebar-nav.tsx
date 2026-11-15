"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { isActive, type NavItem } from "@/components/layout/nav-items";
import { useUnreadCount } from "@/lib/queries";
import { cn } from "@/lib/utils";

function AlertsBadge() {
  const unread = useUnreadCount().data?.count ?? 0;
  if (unread === 0) return null;
  return (
    <span className="rounded-full bg-danger px-1.5 py-px text-[11px] font-semibold text-white tabular">
      {unread}
      <span className="sr-only"> unread</span>
    </span>
  );
}

export function SidebarNav({ items, onNavigate }: { items: NavItem[]; onNavigate?: () => void }) {
  const pathname = usePathname();
  return (
    <nav aria-label="Main" className="grid gap-0.5">
      {items.map(({ href, label, icon: Icon, badge }) => {
        const active = isActive(pathname, href);
        return (
          <Link
            key={href}
            href={href}
            onClick={onNavigate}
            aria-current={active ? "page" : undefined}
            className={cn(
              "group flex h-9 items-center gap-3 rounded-lg px-3 text-sm font-medium text-muted-foreground transition-colors outline-none hover:bg-accent hover:text-foreground focus-visible:ring-[3px] focus-visible:ring-ring/40",
              active && "bg-card text-foreground shadow-[0_1px_2px_rgb(16_32_24/0.06)] ring-1 ring-border",
            )}
          >
            <Icon className={cn("size-4", active && "text-primary")} aria-hidden="true" />
            <span className="flex-1">{label}</span>
            {badge === "alerts" ? <AlertsBadge /> : null}
          </Link>
        );
      })}
    </nav>
  );
}
