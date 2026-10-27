"use client";
import { createContext, useContext, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { clearToken, getToken } from "@/lib/api";

const Ctx = createContext<{ logout: () => void }>({ logout: () => {} });
export const useAuth = () => useContext(Ctx);

export function AuthGate({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [ready, setReady] = useState(false);

  useEffect(() => {
    if (!getToken()) router.replace("/login");
    else setReady(true);
  }, [router]);

  const logout = () => {
    clearToken();
    router.replace("/login");
  };

  if (!ready) return <div className="grid min-h-screen place-items-center text-muted">Loading…</div>;
  return <Ctx.Provider value={{ logout }}>{children}</Ctx.Provider>;
}
