"use client";
import Link from "next/link";
import { useState } from "react";
import { Sparkles } from "lucide-react";
import { ErrorBox, Loading, PageHeader, Stat } from "@/components/ui";
import { post } from "@/lib/api";
import { useApi } from "@/lib/useApi";
import type { Insights } from "@/lib/types";

export default function InsightsPage() {
  const { data, error, loading, reload } = useApi<Insights>("/ai/insights");
  const [busy, setBusy] = useState(false);

  async function regenerate() {
    setBusy(true);
    try { await post("/ai/insights"); await reload(); } finally { setBusy(false); }
  }

  if (loading && !data) return <Loading />;
  if (error || !data) return <ErrorBox message={error ?? "No insights"} />;

  return (
    <>
      <PageHeader title="AI Insights" subtitle="Across all shipments"
        actions={<button className="btn-primary" onClick={regenerate} disabled={busy}><Sparkles size={16} aria-hidden /> {busy ? "Generating…" : "Regenerate"}</button>} />
      <div className="card border-indigo/30 p-6"><p className="text-lg">{data.summary}</p></div>
      <div className="mt-6 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <Stat label="Healthy" value={data.normal_count} /><Stat label="Delivered" value={data.delivered_count} />
        <Stat label="Watch" value={data.watch_count} /><Stat label="Delayed" value={data.delayed_count} />
      </div>
      {data.recommendations.length > 0 && (
        <div className="card mt-6 p-6"><h2 className="mb-3 font-display text-lg font-semibold">Recommendations</h2>
          <ul className="list-inside list-disc space-y-1 text-sm text-slate-300">{data.recommendations.map((r) => <li key={r}>{r}</li>)}</ul></div>
      )}
      {data.delayed_shipments.length > 0 && (
        <div className="card mt-6 divide-y divide-line">
          <h2 className="px-6 py-4 font-display text-lg font-semibold">Needs attention</h2>
          {data.delayed_shipments.map((s) => (
            <Link key={s.id} href={`/shipments/${s.id}`} className="flex justify-between px-6 py-3 text-sm hover:bg-panel-2">
              <span className="font-mono font-semibold">{s.tracking_number}</span><span className="text-muted">{s.current_location ?? "—"}</span>
            </Link>
          ))}
        </div>
      )}
    </>
  );
}
