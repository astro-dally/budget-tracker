"use client";

import { ArrowLeft, Command, Menu } from "lucide-react";
import Link from "next/link";
import { useState, type ReactNode } from "react";
import { AlertBell } from "@/components/layout/alert-bell";
import { Brand } from "@/components/layout/brand";
import { CommandPalette } from "@/components/layout/command-palette";
import type { NavItem } from "@/components/layout/nav-items";
import { SidebarNav } from "@/components/layout/sidebar-nav";
import { ThemeToggle } from "@/components/layout/theme-toggle";
import { UserMenu } from "@/components/layout/user-menu";
import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetDescription, SheetTitle, SheetTrigger } from "@/components/ui/sheet";

function SidebarFooter({ variant }: { variant: "app" | "admin" }) {
  return variant === "admin" ? (
    <Link
      href="/app"
      className="flex items-center gap-2 rounded-lg px-3 py-2 text-sm text-muted-foreground hover:bg-accent hover:text-foreground"
    >
      <ArrowLeft className="size-4" /> Back to my budget
    </Link>
  ) : (
    <button
      type="button"
      onClick={() => window.dispatchEvent(new Event("open-command-palette"))}
      className="flex w-full items-center gap-2 rounded-lg border border-dashed px-3 py-2 text-left text-sm text-muted-foreground hover:bg-accent hover:text-foreground"
    >
      <Command className="size-4" />
      <span className="flex-1">Quick actions</span>
      <kbd className="rounded border bg-card px-1.5 text-[11px]">⌘K</kbd>
    </button>
  );
}

export function AppShell({
  children,
  nav,
  variant = "app",
}: {
  children: ReactNode;
  nav: NavItem[];
  variant?: "app" | "admin";
}) {
  const [menuOpen, setMenuOpen] = useState(false);
  const home = variant === "admin" ? "/admin" : "/app";
  return (
    <div className="min-h-dvh lg:grid lg:grid-cols-[15rem_1fr]">
      <a
        href="#main"
        className="sr-only focus:not-sr-only focus:fixed focus:top-3 focus:left-3 focus:z-[60] focus:rounded-md focus:bg-card focus:px-3 focus:py-2 focus:shadow"
      >
        Skip to content
      </a>

      <aside className="sticky top-0 hidden h-dvh flex-col gap-8 px-4 py-6 lg:flex">
        <div className="flex items-center justify-between px-2">
          <Brand href={home} />
          {variant === "admin" ? (
            <span className="rounded-md bg-foreground px-1.5 py-0.5 text-[10px] font-semibold text-background">
              Admin
            </span>
          ) : null}
        </div>
        <SidebarNav items={nav} />
        <div className="mt-auto">
          <SidebarFooter variant={variant} />
        </div>
      </aside>

      <div className="flex min-w-0 flex-col">
        <header className="sticky top-0 z-40 flex h-14 items-center gap-2 border-b bg-background/85 px-4 backdrop-blur sm:px-6 lg:border-transparent lg:bg-background/70">
          <Sheet open={menuOpen} onOpenChange={setMenuOpen}>
            <SheetTrigger asChild>
              <Button variant="ghost" size="icon" className="lg:hidden" aria-label="Open menu">
                <Menu />
              </Button>
            </SheetTrigger>
            <SheetContent className="gap-8 px-4 py-6">
              <SheetTitle className="px-2">
                <Brand href={home} />
              </SheetTitle>
              <SheetDescription className="sr-only">Main navigation</SheetDescription>
              <SidebarNav items={nav} onNavigate={() => setMenuOpen(false)} />
              <div className="mt-auto">
                <SidebarFooter variant={variant} />
              </div>
            </SheetContent>
          </Sheet>
          <div className="lg:hidden">
            <Brand href={home} />
          </div>
          <div className="ml-auto flex items-center gap-1.5">
            {variant === "app" ? <AlertBell /> : null}
            <ThemeToggle />
            <span className="mx-1 h-6 w-px bg-border" aria-hidden="true" />
            <UserMenu />
          </div>
        </header>
        <main id="main" className="mx-auto w-full max-w-6xl flex-1 px-4 pt-4 pb-16 sm:px-6 lg:px-8">
          {children}
        </main>
      </div>
      <CommandPalette />
    </div>
  );
}
