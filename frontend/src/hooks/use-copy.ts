"use client";

import { useState } from "react";

export function useCopy(timeout = 1200) {
  const [copied, setCopied] = useState(false);

  async function copy(value: string) {
    await navigator.clipboard.writeText(value);
    setCopied(true);
    window.setTimeout(() => setCopied(false), timeout);
  }

  return { copied, copy };
}
