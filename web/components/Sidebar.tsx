"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { BarChart3, Bell, Boxes, LayoutDashboard, LogOut, Plus, Sparkles } from "lucide-react";
import { Logo } from "./Logo";
import { useAuth } from "./AuthProvider";
import { useEffect, useState } from "react";

const NAV = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/shipments", label: "Shipments", icon: Boxes },
  { href: "/analytics", label: "Analytics", icon: BarChart3 },
  { href: "/insights", label: "AI Insights", icon: Sparkles },
  { href: "/notifications", label: "Notifications", icon: Bell },
];

export function Sidebar() {
  const path = usePathname();
  const { logout } = useAuth();
  const [health, setHealth] = useState<{ demo_mode: boolean; tracking_provider: string } | null>(null);
  useEffect(() => {
    // /api/health is not wrapped in the {success,data} envelope, so fetch it directly.
    fetch("/api/health").then((r) => r.json()).then(setHealth).catch(() => setHealth(null));
  }, []);
  return (
    <aside className="flex w-full shrink-0 flex-col gap-4 border-b border-line bg-panel/60 p-4 md:sticky md:top-0 md:h-screen md:w-60 md:border-b-0 md:border-r">
      <Logo href="/dashboard" />
      <Link href="/shipments/new" className="btn-primary"><Plus size={16} aria-hidden /> Add shipment</Link>
      <nav aria-label="Main" className="flex gap-1 overflow-x-auto md:flex-col">
        {NAV.map(({ href, label, icon: Icon }) => {
          const active = path === href || (href !== "/dashboard" && path.startsWith(href) && !(href === "/shipments" && path === "/shipments/new"));
          return (
            <Link key={href} href={href} aria-current={active ? "page" : undefined}
              className={`flex items-center gap-3 whitespace-nowrap rounded-xl px-3 py-2.5 text-sm font-medium transition ${active ? "bg-sky/10 text-sky" : "text-muted hover:bg-panel-2 hover:text-white"}`}>
              <Icon size={18} aria-hidden /> {label}
            </Link>
          );
        })}
      </nav>
      {health && (
        <p className={`rounded-lg px-3 py-2 text-xs font-medium ${health.demo_mode ? "bg-amber-500/10 text-amber-400" : "bg-emerald-500/10 text-emerald-400"}`}>
          {health.demo_mode ? "Demo data — not live tracking" : health.tracking_provider === "web" ? "Live India Post (you solve the CAPTCHA)" : "Live India Post tracking"}
        </p>
      )}
      <button onClick={logout} className="btn-ghost mt-auto hidden md:inline-flex"><LogOut size={16} aria-hidden /> Sign out</button>
    </aside>
  );
}
