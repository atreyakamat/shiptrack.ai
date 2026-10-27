"use client";
import Link from "next/link";
import { useState } from "react";
import { RefreshCw } from "lucide-react";
import { Empty, ErrorBox, Loading, PageHeader, Stat } from "@/components/ui";
import { StatusBadge } from "@/components/StatusBadge";
import { post } from "@/lib/api";
import { useApi } from "@/lib/useApi";
import { formatDate } from "@/lib/format";
import type { Analytics, Insights, Shipment } from "@/lib/types";

export default function Dashboard() {
  const stats = useApi<Analytics>("/analytics");
  const ships = useApi<Shipment[]>("/shipments");
  const insights = useApi<Insights>("/ai/insights");
  const [refreshing, setRefreshing] = useState(false);
  const [refreshError, setRefreshError] = useState<string | null>(null);

  async function refreshAll() {
    setRefreshing(true);
    setRefreshError(null);
    try {
      await post("/shipments/refresh-all");
      await Promise.all([stats.reload(), ships.reload(), insights.reload()]);
    } catch (e) {
      setRefreshError(e instanceof Error ? e.message : "Refresh failed");
    } finally {
      setRefreshing(false);
    }
  }

  const error = stats.error ?? ships.error;
  const o = stats.data?.overview;
  const recent = (ships.data ?? []).filter((s) => !s.is_archived).slice(0, 6);

  return (
    <>
      <PageHeader title="Dashboard" subtitle="Your shipments at a glance"
        actions={<button className="btn-ghost" onClick={refreshAll} disabled={refreshing}><RefreshCw size={16} className={refreshing ? "animate-spin" : ""} aria-hidden /> Refresh all</button>} />
      {error && <ErrorBox message={error} />}
      {refreshError && <ErrorBox message={refreshError} />}
      {(stats.loading || ships.loading) && !o && <Loading />}
      {o && (
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <Stat label="Total" value={o.total} />
          <Stat label="In transit" value={o.in_transit} />
          <Stat label="Delivered" value={o.delivered} hint={`${o.delivery_rate}% delivery rate`} />
          <Stat label="Needs attention" value={o.delayed} />
        </div>
      )}

      {insights.data && (
        <div className="card mt-6 border-indigo/30 p-5">
          <p className="text-xs font-semibold uppercase tracking-wide text-indigo">AI insight</p>
          <p className="mt-2">{insights.data.summary}</p>
          {insights.data.recommendations[0] && <p className="mt-1 text-sm text-muted">{insights.data.recommendations[0]}</p>}
        </div>
      )}

      <h2 className="mb-3 mt-8 font-display text-lg font-semibold">Recent shipments</h2>
      {ships.data && recent.length === 0 ? (
        <Empty title="No shipments yet" body="Add your first tracking number to get started." action={<Link href="/shipments/new" className="btn-primary">Add shipment</Link>} />
      ) : (
        <div className="card divide-y divide-line">
          {recent.map((s) => (
            <Link key={s.id} href={`/shipments/${s.id}`} className="flex flex-wrap items-center justify-between gap-3 px-5 py-4 transition hover:bg-panel-2">
              <div>
                <p className="font-mono text-sm font-semibold">{s.tracking_number}</p>
                <p className="text-sm text-muted">{s.description ?? "No description"}</p>
              </div>
              <p className="hidden text-sm text-muted sm:block">{s.current_location ?? "—"}</p>
              <p className="hidden text-sm text-muted md:block">{formatDate(s.last_updated)}</p>
              <StatusBadge status={s.status} />
            </Link>
          ))}
        </div>
      )}
    </>
  );
}
