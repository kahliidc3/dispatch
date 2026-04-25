"use client";

import { useState } from "react";
import { LogOut } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { apiEndpoints } from "@/lib/api/endpoints";
import { clientJson } from "@/lib/api/client";
import { ApiError } from "@/lib/api/errors";
import type { SessionResponse, SessionUser } from "@/types/api";

type SessionMenuProps = {
  session: SessionUser;
  source: SessionResponse["source"];
};

export function SessionMenu({ session, source }: SessionMenuProps) {
  const [isSigningOut, setIsSigningOut] = useState(false);

  async function handleSignOut() {
    setIsSigningOut(true);

    try {
      await clientJson(apiEndpoints.internal.session, {
        method: "DELETE",
        redirectOnUnauthorized: false,
      });

      window.location.assign("/login");
    } catch (error) {
      toast.error(
        error instanceof ApiError ? error.message : "Failed to clear the current session.",
      );
    } finally {
      setIsSigningOut(false);
    }
  }

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button type="button" variant="outline">
          {session.name}
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-64">
        <DropdownMenuLabel className="grid gap-1">
          <span className="font-medium">{session.name}</span>
          <span className="text-xs font-normal text-text-muted">
            {session.email}
          </span>
          <span className="text-xs font-normal text-text-muted">
            {source === "dev" ? "Local development session" : "Authenticated session"}
          </span>
        </DropdownMenuLabel>
        <DropdownMenuSeparator />
        <DropdownMenuItem
          disabled={isSigningOut}
          onSelect={(event) => {
            event.preventDefault();
            void handleSignOut();
          }}
        >
          <LogOut className="mr-2 h-4 w-4" />
          {isSigningOut ? "Signing out..." : "Sign out"}
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
