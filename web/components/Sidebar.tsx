"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { BarChart3, Bell, Boxes, LayoutDashboard, LogOut, Plus, Sparkles } from "lucide-react";
import { Logo } from "./Logo";
import { useAuth } from "./AuthProvider";
import { useHealth } from "@/lib/useHealth";
import { useApi } from "@/lib/useApi";

const NAV = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/shipments", label: "Shipments", icon: Boxes },
  { href: "/analytics", label: "Analytics", icon: BarChart3 },
  { href: "/insights", label: "AI Insights", icon: Sparkles },
  { href: "/notifications", label: "Notifications", icon: Bell },
];

const MODE: Record<string, { label: string; cls: string }> = {
  demo: { label: "Demo data", cls: "bg-amber-500/10 text-amber-400" },
  web: { label: "Live · you solve the CAPTCHA", cls: "bg-emerald-500/10 text-emerald-400" },
  api: { label: "Live · Ship24", cls: "bg-emerald-500/10 text-emerald-400" },
};

interface Usage { enabled: boolean; used?: number; limit?: number; unavailable?: boolean }

export function Sidebar() {
  const path = usePathname();
  const { logout } = useAuth();
  const health = useHealth();
  const usage = useApi<Usage>("/tracking/ship24/usage");
  const mode = health ? MODE[health.live_mode] : null;
  const q = usage.data;
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
      <div className="mt-auto space-y-2">
        {mode && (
          <p className={`rounded-lg px-3 py-2 text-xs font-medium ${mode.cls}`}>{mode.label}</p>
        )}
        {q?.enabled && !q.unavailable && q.limit != null && (
          <div className="rounded-lg border border-line px-3 py-2">
            <div className="flex justify-between text-xs text-muted">
              <span>Ship24 this month</span><span>{q.used}/{q.limit}</span>
            </div>
            <div className="mt-1.5 h-1.5 overflow-hidden rounded-full bg-ink">
              <div className="h-full rounded-full bg-sky" style={{ width: `${Math.min(100, ((q.used ?? 0) / q.limit) * 100)}%` }} />
            </div>
            {(q.used ?? 0) >= q.limit && <p className="mt-1.5 text-[11px] text-amber-400">Limit reached — new shipments use the CAPTCHA.</p>}
          </div>
        )}
        <button onClick={logout} className="btn-ghost hidden w-full md:inline-flex"><LogOut size={16} aria-hidden /> Sign out</button>
      </div>
    </aside>
  );
}
