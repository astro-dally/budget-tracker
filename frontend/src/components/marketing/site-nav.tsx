"use client";

import Link from "next/link";
import { Brand } from "@/components/layout/brand";
import { ThemeToggle } from "@/components/layout/theme-toggle";
import { Button } from "@/components/ui/button";
import { homeFor, useAuth } from "@/lib/auth";

export function SiteNav() {
  const { status, user } = useAuth();
  return (
    <header className="sticky top-0 z-40 border-b border-transparent bg-background/75 backdrop-blur-md">
      <div className="mx-auto flex h-16 max-w-6xl items-center gap-6 px-4 sm:px-6">
        <Brand href="/" />
        <nav aria-label="Site" className="hidden items-center gap-6 text-sm text-muted-foreground md:flex">
          <a href="#features" className="hover:text-foreground">Features</a>
          <a href="#how" className="hover:text-foreground">How it works</a>
        </nav>
        <div className="ml-auto flex items-center gap-2">
          <ThemeToggle />
          {status === "authenticated" && user ? (
            <Button asChild>
              <Link href={homeFor(user)}>Open my dashboard</Link>
            </Button>
          ) : (
            <>
              <Button asChild variant="ghost" className="hidden sm:inline-flex">
                <Link href="/login">Sign in</Link>
              </Button>
              <Button asChild>
                <Link href="/signup">Start free</Link>
              </Button>
            </>
          )}
        </div>
      </div>
    </header>
  );
}
