import {
  ArrowLeftRight,
  Bell,
  ChartColumn,
  LayoutDashboard,
  Repeat,
  ShieldCheck,
  Target,
  Users,
  type LucideIcon,
} from "lucide-react";

export interface NavItem {
  href: string;
  label: string;
  icon: LucideIcon;
  badge?: "alerts";
}

export const NAV_ITEMS: NavItem[] = [
  { href: "/app", label: "Overview", icon: LayoutDashboard },
  { href: "/app/transactions", label: "Transactions", icon: ArrowLeftRight },
  { href: "/app/budgets", label: "Budgets", icon: Target },
  { href: "/app/recurring", label: "Recurring", icon: Repeat },
  { href: "/app/reports", label: "Reports", icon: ChartColumn },
  { href: "/app/alerts", label: "Alerts", icon: Bell, badge: "alerts" },
];

export const ADMIN_NAV_ITEMS: NavItem[] = [
  { href: "/admin", label: "Platform", icon: ShieldCheck },
  { href: "/admin/users", label: "Users", icon: Users },
];

export function isActive(pathname: string, href: string): boolean {
  return href === "/app" || href === "/admin" ? pathname === href : pathname.startsWith(href);
}
