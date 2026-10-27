"use client";
import { useEffect, useState } from "react";

export interface Health {
  demo_mode: boolean;
  live_mode: "demo" | "web" | "api";
  tracking_provider: string;
}

// /api/health is not wrapped in the {success,data} envelope, so fetch it directly.
export function useHealth() {
  const [health, setHealth] = useState<Health | null>(null);
  useEffect(() => {
    fetch("/api/health").then((r) => r.json()).then(setHealth).catch(() => setHealth(null));
  }, []);
  return health;
}
