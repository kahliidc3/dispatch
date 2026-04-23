"use client";

import { useCallback, useState } from "react";

export function useQueryState(key: string, initialValue = "") {
  const [value, setValue] = useState(initialValue);

  const update = useCallback(
    (nextValue: string) => {
      setValue(nextValue);

      const params = new URLSearchParams(window.location.search);

      if (nextValue) {
        params.set(key, nextValue);
      } else {
        params.delete(key);
      }

      const nextQuery = params.toString();
      const nextUrl = nextQuery ? `?${nextQuery}` : window.location.pathname;

      window.history.replaceState(null, "", nextUrl);
    },
    [key],
  );

  return [value, update] as const;
}
