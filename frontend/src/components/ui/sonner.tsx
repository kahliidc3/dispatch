"use client";

import { Toaster as Sonner } from "sonner";

export function Toaster() {
  return (
    <Sonner
      position="top-right"
      closeButton
      toastOptions={{
        style: {
          background: "var(--surface)",
          border: "1px solid var(--border)",
          borderRadius: "10px",
          color: "var(--text)",
        },
      }}
    />
  );
}
