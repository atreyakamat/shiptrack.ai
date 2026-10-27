"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { Search } from "lucide-react";
import { Empty, ErrorBox, PageHeader, SkeletonRows } from "@/components/ui";
import { StatusBadge, statusLabel } from "@/components/StatusBadge";
import { useApi } from "@/lib/useApi";
import { formatDate } from "@/lib/format";
import type { Shipment } from "@/lib/types";

const STATUSES = ["BOOKED", "IN_TRANSIT", "OUT_FOR_DELIVERY", "DELIVERED", "EXCEPTION", "UNKNOWN"];

export default function Shipments() {
  const [search, setSearch] = useState("");
  const [debounced, setDebounced] = useState("");
  const [status, setStatus] = useState("");
  const [showDone, setShowDone] = useState(false);

  useEffect(() => {
    const t = setTimeout(() => setDebounced(search.trim()), 300);
    return () => clearTimeout(t);
  }, [search]);

  // The backend ignores the status filter when a search term is present, so filter status client-side.
  const { data, error, loading } = useApi<Shipment[]>(`/shipments${debounced ? `?search=${encodeURIComponent(debounced)}` : ""}`);
  const rows = (data ?? []).filter((s) => (showDone ? s.is_archived : !s.is_archived) && (!status || s.status === status));
  const doneCount = (data ?? []).filter((s) => s.is_archived).length;

  return (
    <>
      <PageHeader title="Shipments" 
        actions={<Link href="/shipments/new" className="btn-primary">Add shipment</Link>} />
      <div className="mb-4 flex flex-wrap gap-3">
        <div className="relative min-w-60 flex-1">
          <Search size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-muted" aria-hidden />
          <input aria-label="Search shipments" className="input pl-10" placeholder="Search shipments" value={search} onChange={(e) => setSearch(e.target.value)} />
        </div>
        <select aria-label="Filter by status" className="input w-auto" value={status} onChange={(e) => setStatus(e.target.value)}>
          <option value="">All statuses</option>
          {STATUSES.map((s) => <option key={s} value={s}>{statusLabel(s)}</option>)}
        </select>
        <button type="button" onClick={() => setShowDone((v) => !v)} aria-pressed={showDone}
          className={showDone ? "btn-primary" : "btn-ghost"}>
          {showDone ? "Showing done" : `Done${doneCount ? ` (${doneCount})` : ""}`}
        </button>
      </div>
      {error && <ErrorBox message={error} />}
      {loading && !data && <SkeletonRows />}
      {data && rows.length === 0 && (
        showDone
          ? <Empty title="Nothing done yet" body="Shipments you mark as done will appear here." />
          : <Empty title="No shipments found" body="Add a tracking number to get started."
              action={<Link href="/shipments/new" className="btn-primary">Add shipment</Link>} />
      )}
      {rows.length > 0 && (
        <div className="card overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-line text-xs uppercase tracking-wide text-muted">
              <tr><th className="px-5 py-3">Tracking #</th><th className="px-5 py-3">Description</th><th className="px-5 py-3">Route</th><th className="px-5 py-3">Updated</th><th className="px-5 py-3">Status</th></tr>
            </thead>
            <tbody className="divide-y divide-line">
              {rows.map((s) => (
                <tr key={s.id} className="transition hover:bg-panel-2">
                  <td className="px-5 py-3.5"><Link href={`/shipments/${s.id}`} className="font-mono font-semibold text-sky hover:underline">{s.tracking_number}</Link></td>
                  <td className="px-5 py-3.5 text-slate-300">{s.description ?? "—"}</td>
                  <td className="px-5 py-3.5 text-muted">{[s.origin, s.destination].filter(Boolean).join(" → ") || "—"}</td>
                  <td className="px-5 py-3.5 text-muted">{formatDate(s.last_updated)}</td>
                  <td className="px-5 py-3.5"><StatusBadge status={s.status} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </>
  );
}
