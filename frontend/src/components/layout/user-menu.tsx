"use client";

import { LayoutDashboard, LogOut, ShieldCheck } from "lucide-react";
import Link from "next/link";
import { UserAvatar } from "@/components/layout/user-avatar";
import { Badge } from "@/components/ui/badge";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useAuth } from "@/lib/auth";

export function UserMenu() {
  const { user, logout } = useAuth();
  if (!user) return null;
  return (
    <DropdownMenu>
      <DropdownMenuTrigger
        className="rounded-full outline-none focus-visible:ring-[3px] focus-visible:ring-ring/40"
        aria-label={`Account menu for ${user.name}`}
      >
        <UserAvatar name={user.name} />
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-64">
        <DropdownMenuLabel className="flex items-center gap-3 py-2 font-normal">
          <UserAvatar name={user.name} className="size-9" />
          <span className="min-w-0">
            <span className="block truncate text-sm font-semibold">{user.name}</span>
            <span className="block truncate text-xs text-muted-foreground">{user.email}</span>
          </span>
        </DropdownMenuLabel>
        {user.role === "admin" ? (
          <>
            <div className="px-2 pb-2">
              <Badge variant="default">Administrator</Badge>
            </div>
            <DropdownMenuSeparator />
            <DropdownMenuItem asChild>
              <Link href="/admin">
                <ShieldCheck /> Admin console
              </Link>
            </DropdownMenuItem>
            <DropdownMenuItem asChild>
              <Link href="/app">
                <LayoutDashboard /> My budget
              </Link>
            </DropdownMenuItem>
          </>
        ) : null}
        <DropdownMenuSeparator />
        <DropdownMenuItem onSelect={logout}>
          <LogOut /> Sign out
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
