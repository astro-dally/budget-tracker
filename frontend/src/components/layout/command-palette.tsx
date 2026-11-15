"use client";

import { LogOut, Moon, Plus, Search, Sun, type LucideIcon } from "lucide-react";
import { useTheme } from "next-themes";
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useRef, useState } from "react";
import { ADMIN_NAV_ITEMS, NAV_ITEMS } from "@/components/layout/nav-items";
import { Dialog, DialogContent, DialogDescription, DialogTitle } from "@/components/ui/dialog";
import { useAuth } from "@/lib/auth";
import { cn } from "@/lib/utils";

interface Command {
  id: string;
  label: string;
  group: string;
  icon: LucideIcon;
  run: () => void;
}

export const NEW_TRANSACTION_HASH = "#new";

/** ⌘K / Ctrl+K: jump anywhere or run an action from the keyboard. */
export function CommandPalette() {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [index, setIndex] = useState(0);
  const router = useRouter();
  const { user, logout } = useAuth();
  const { resolvedTheme, setTheme } = useTheme();
  const listRef = useRef<HTMLUListElement>(null);

  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        setOpen((value) => !value);
      }
    };
    const onOpen = () => setOpen(true);
    window.addEventListener("keydown", onKey);
    window.addEventListener("open-command-palette", onOpen);
    return () => {
      window.removeEventListener("keydown", onKey);
      window.removeEventListener("open-command-palette", onOpen);
    };
  }, []);

  const commands = useMemo<Command[]>(() => {
    const go = (href: string) => () => router.push(href);
    const pages = [...NAV_ITEMS, ...(user?.role === "admin" ? ADMIN_NAV_ITEMS : [])].map((item) => ({
      id: item.href,
      label: item.label === "Platform" ? "Admin: platform" : item.label === "Users" ? "Admin: users" : item.label,
      group: "Go to",
      icon: item.icon,
      run: go(item.href),
    }));
    return [
      { id: "new", label: "Add transaction", group: "Actions", icon: Plus, run: go(`/app/transactions${NEW_TRANSACTION_HASH}`) },
      {
        id: "theme",
        label: resolvedTheme === "dark" ? "Switch to light mode" : "Switch to dark mode",
        group: "Actions",
        icon: resolvedTheme === "dark" ? Sun : Moon,
        run: () => setTheme(resolvedTheme === "dark" ? "light" : "dark"),
      },
      ...pages,
      { id: "logout", label: "Sign out", group: "Account", icon: LogOut, run: logout },
    ];
  }, [router, user, resolvedTheme, setTheme, logout]);

  const results = commands.filter((c) => c.label.toLowerCase().includes(query.trim().toLowerCase()));
  const active = Math.min(index, Math.max(0, results.length - 1));

  const run = (command: Command | undefined) => {
    if (!command) return;
    setOpen(false);
    setQuery("");
    command.run();
  };

  return (
    <Dialog
      open={open}
      onOpenChange={(value) => {
        setOpen(value);
        if (!value) setQuery("");
      }}
    >
      <DialogContent className="top-[20%] translate-y-0 gap-0 overflow-hidden p-0 sm:max-w-xl [&>button:last-child]:hidden">
        <DialogTitle className="sr-only">Command palette</DialogTitle>
        <DialogDescription className="sr-only">Type to search pages and actions</DialogDescription>
        <div className="flex items-center gap-3 border-b px-4">
          <Search className="size-4 text-muted-foreground" aria-hidden="true" />
          <input
            autoFocus
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setIndex(0);
            }}
            onKeyDown={(e) => {
              if (e.key === "ArrowDown") {
                e.preventDefault();
                setIndex((i) => Math.min(i + 1, results.length - 1));
              } else if (e.key === "ArrowUp") {
                e.preventDefault();
                setIndex((i) => Math.max(i - 1, 0));
              } else if (e.key === "Enter") {
                e.preventDefault();
                run(results[active]);
              }
            }}
            placeholder="Search pages and actions…"
            aria-label="Search commands"
            aria-controls="command-results"
            aria-activedescendant={results[active] ? `cmd-${results[active].id}` : undefined}
            className="h-14 flex-1 bg-transparent text-base outline-none placeholder:text-muted-foreground"
          />
          <kbd className="rounded border bg-muted px-1.5 py-0.5 text-[11px] text-muted-foreground">Esc</kbd>
        </div>
        <ul id="command-results" ref={listRef} role="listbox" className="max-h-80 overflow-y-auto p-2">
          {results.length === 0 ? (
            <li className="px-3 py-8 text-center text-sm text-muted-foreground">Nothing matches “{query}”.</li>
          ) : (
            results.map((command, i) => {
              const showGroup = i === 0 || results[i - 1]?.group !== command.group;
              const Icon = command.icon;
              return (
                <li key={command.id} role="presentation">
                  {showGroup ? (
                    <p className="px-3 pt-2 pb-1 text-xs text-muted-foreground">{command.group}</p>
                  ) : null}
                  <button
                    type="button"
                    id={`cmd-${command.id}`}
                    role="option"
                    aria-selected={i === active}
                    onMouseEnter={() => setIndex(i)}
                    onClick={() => run(command)}
                    className={cn(
                      "flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-left text-sm outline-none",
                      i === active && "bg-primary text-primary-foreground",
                    )}
                  >
                    <Icon className="size-4" aria-hidden="true" />
                    {command.label}
                  </button>
                </li>
              );
            })
          )}
        </ul>
      </DialogContent>
    </Dialog>
  );
}
