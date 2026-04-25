"use client";

import { startTransition, useDeferredValue, useEffect, useMemo, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { Search } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { getCommandPaletteItems } from "@/lib/navigation";
import { cn } from "@/lib/utils";
import type { UserRole } from "@/types/api";

type CommandPaletteProps = {
  role: UserRole;
};

export function CommandPalette({ role }: CommandPaletteProps) {
  const pathname = usePathname();
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [activeIndex, setActiveIndex] = useState(0);
  const deferredQuery = useDeferredValue(query);
  const items = useMemo(() => getCommandPaletteItems(role), [role]);
  const filteredItems = useMemo(() => {
    const normalizedQuery = deferredQuery.trim().toLowerCase();

    if (!normalizedQuery) {
      return items;
    }

    return items.filter((item) => item.searchText.includes(normalizedQuery));
  }, [deferredQuery, items]);

  useEffect(() => {
    function onKeyDown(event: KeyboardEvent) {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        setOpen((previous) => !previous);
      }
    }

    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, []);

  function navigate(href: string) {
    setOpen(false);
    setQuery("");
    setActiveIndex(0);
    startTransition(() => {
      router.push(href);
    });
  }

  return (
    <>
      <Button type="button" variant="outline" onClick={() => setOpen(true)}>
        <Search className="h-4 w-4" />
        Jump to
        <span className="mono text-xs text-text-muted">Ctrl+K</span>
      </Button>
      <Dialog
        open={open}
        onOpenChange={(nextOpen) => {
          setOpen(nextOpen);
          if (!nextOpen) {
            setQuery("");
            setActiveIndex(0);
          }
        }}
      >
        <DialogContent className="max-w-xl p-0">
          <DialogHeader className="border-b border-border px-5 py-4">
            <DialogTitle>Command palette</DialogTitle>
            <DialogDescription>
              Search the current shell routes and navigate without leaving the keyboard.
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 p-5">
            <Input
              aria-label="Search routes"
              placeholder="Search campaigns, domains, reputation..."
              value={query}
              onChange={(event) => {
                setQuery(event.target.value);
                setActiveIndex(0);
              }}
              onKeyDown={(event) => {
                if (event.key === "ArrowDown") {
                  event.preventDefault();
                  setActiveIndex((current) =>
                    Math.min(current + 1, Math.max(filteredItems.length - 1, 0)),
                  );
                }

                if (event.key === "ArrowUp") {
                  event.preventDefault();
                  setActiveIndex((current) => Math.max(current - 1, 0));
                }

                if (event.key === "Enter" && filteredItems[activeIndex]) {
                  event.preventDefault();
                  navigate(filteredItems[activeIndex].href);
                }
              }}
            />
            <div className="grid gap-1" role="listbox" aria-label="Route results">
              {filteredItems.length > 0 ? (
                filteredItems.map((item, index) => {
                  const active = index === activeIndex;

                  return (
                    <button
                      key={item.href}
                      type="button"
                      role="option"
                      aria-selected={active}
                      onMouseEnter={() => setActiveIndex(index)}
                      onClick={() => navigate(item.href)}
                      className={cn(
                        "command-palette-item",
                        active && "command-palette-item-active",
                      )}
                    >
                      <div className="grid gap-1 text-left">
                        <div className="flex flex-wrap items-center gap-2">
                          <span className="font-medium">{item.label}</span>
                          {pathname === item.href ? (
                            <span className="mono text-xs text-text-muted">current</span>
                          ) : null}
                        </div>
                        <p className="text-sm text-text-muted">{item.description}</p>
                      </div>
                      <span className="mono text-xs text-text-muted">{item.section}</span>
                    </button>
                  );
                })
              ) : (
                <div className="surface-panel-muted px-4 py-5 text-sm text-text-muted">
                  No routes match this search.
                </div>
              )}
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
}
