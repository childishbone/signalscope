"use client";

import { useCallback, useState } from "react";

/**
 * Keeps the admin key in memory only (never localStorage). Lost on refresh,
 * which is the point: this is a convenience for the one person maintaining
 * the watchlist, not an auth system.
 */
export function useAdminKey() {
  const [adminKey, setAdminKey] = useState<string | null>(null);

  const ensureAdminKey = useCallback((): string | null => {
    if (adminKey) return adminKey;
    const entered = window.prompt(
      "Enter the admin key to modify the watchlist:",
    );
    if (!entered) return null;
    setAdminKey(entered);
    return entered;
  }, [adminKey]);

  return { adminKey, ensureAdminKey, clearAdminKey: () => setAdminKey(null) };
}
