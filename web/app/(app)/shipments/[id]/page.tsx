"use client";
import { use, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowLeft, Check, RefreshCw, Sparkles, Trash2 } from "lucide-react";
import { ErrorBox, Loading } from "@/components/ui";
import { StatusBadge } from "@/components/StatusBadge";
import { Timeline } from "@/components/Timeline";
import { CaptchaModal } from "@/components/CaptchaModal";
import { ConfirmDialog } from "@/components/ConfirmDialog";
import { useToast } from "@/components/Toast";
import { ApiError, api, post } from "@/lib/api";
import { useApi } from "@/lib/useApi";
import { useHealth } from "@/lib/useHealth";
import { formatDate, formatDateTime } from "@/lib/format";
import type { AiSummary, Shipment } from "@/lib/types";

export default function ShipmentDetail({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const router = useRouter();
  const toast = useToast();
  const { data: s, error, loading, reload } = useApi<Shipment>(`/shipments/${id}`);
  const health = useHealth();
  const [ai, setAi] = useState<AiSummary | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [captcha, setCaptcha] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(false);

  useEffect(() => {
    api<AiSummary>(`/ai/${id}/summary`).then(setAi).catch(() => setAi(null));
  }, [id]);

  async function run(name: string, fn: () => Promise<unknown>) {
    setBusy(name);
    setActionError(null);
    try { await fn(); } catch (e) {
      const msg = e instanceof Error ? e.message : "Action failed";
      setActionError(msg);
      toast(msg, "error");
    }
    finally { setBusy(null); }
  }

  // In web mode India Post needs an in-app CAPTCHA; otherwise refresh is a direct call.
  // If Ship24's monthly quota is spent, fall back to the CAPTCHA relay.
  const refresh = () => {
    if (health?.live_mode === "web") { setCaptcha(true); return; }
    run("refresh", async () => {
      try { await post(`/shipments/${id}/refresh`); await reload(); toast("Tracking refreshed", "success"); }
      catch (e) {
        if (e instanceof ApiError && e.code === "PROVIDER_QUOTA") { setCaptcha(true); return; }
        throw e;
      }
    });
  };
  const generate = () => run("ai", async () => { setAi(await post<AiSummary>(`/ai/${id}/generate`)); toast("Summary updated", "success"); });
  const markDone = () => run("done", async () => { await post(`/shipments/${id}/done`); toast("Saved and marked done", "success"); router.push("/shipments"); });
  const doDelete = () => run("delete", async () => { await api(`/shipments/${id}`, { method: "DELETE" }); toast("Shipment deleted", "success"); router.push("/shipments"); });

  if (loading && !s) return <Loading />;
  if (error || !s) return <ErrorBox message={error ?? "Shipment not found"} />;

  const fields: [string, string | null][] = [
    ["Carrier", s.carrier], ["Type", s.article_type], ["Origin", s.origin], ["Destination", s.destination],
    ["Current location", s.current_location], ["Expected delivery", s.expected_delivery ? formatDate(s.expected_delivery) : null],
    ["Last synced", s.last_successful_sync ? formatDateTime(s.last_successful_sync) : null],
  ];

  return (
    <>
      {captcha && (
        <CaptchaModal
          trackingNumber={s.tracking_number}
          shipmentId={Number(id)}
          onClose={() => setCaptcha(false)}
          onSolved={async () => { setCaptcha(false); await reload(); toast("Tracking updated", "success"); }}
        />
      )}
      {confirmDelete && (
        <ConfirmDialog title="Delete shipment?" body="This permanently removes the shipment and its history. This can't be undone."
          confirmLabel="Delete" danger busy={busy === "delete"} onConfirm={doDelete} onCancel={() => setConfirmDelete(false)} />
      )}
      <Link href="/shipments" className="mb-4 inline-flex items-center gap-1.5 text-sm text-muted hover:text-white"><ArrowLeft size={16} aria-hidden /> Shipments</Link>
      <div className="mb-6 flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="font-mono text-2xl font-bold">{s.tracking_number}</h1>
          <p className="mt-1 text-sm text-muted">{s.description ?? "No description"}</p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <StatusBadge status={s.status} />
          <button className="btn-ghost" onClick={refresh} disabled={!!busy}><RefreshCw size={16} className={busy === "refresh" ? "animate-spin" : ""} aria-hidden /> Refresh</button>
          {!s.is_archived && <button className="btn-primary" onClick={markDone} disabled={!!busy}><Check size={16} aria-hidden /> {busy === "done" ? "Saving…" : "Mark as done"}</button>}
          <button className="btn-ghost text-red-300" onClick={() => setConfirmDelete(true)} disabled={!!busy}><Trash2 size={16} aria-hidden /> Delete</button>
        </div>
      </div>
      {actionError && <div className="mb-4"><ErrorBox message={actionError} /></div>}
      {s.last_error && <div className="mb-4"><ErrorBox message={`Last sync error: ${s.last_error}`} /></div>}
      {s.status === "DELIVERED" && !s.is_archived && (
        <div className="mb-4 flex flex-wrap items-center justify-between gap-3 rounded-xl border border-emerald-500/30 bg-emerald-500/10 px-4 py-3 text-sm">
          <span className="text-emerald-300">Delivered — mark it done to save the final details and free a Ship24 slot.</span>
          <button onClick={markDone} disabled={!!busy} className="btn-primary px-3 py-1.5"><Check size={15} aria-hidden /> Mark as done</button>
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-5">
        <div className="card p-6 lg:col-span-3">
          <h2 className="mb-5 font-display text-lg font-semibold">Tracking history</h2>
          <Timeline events={s.events ?? []} />
        </div>
        <div className="space-y-6 lg:col-span-2">
          <div className="card border-indigo/30 p-6">
            <div className="mb-3 flex items-center justify-between">
              <h2 className="flex items-center gap-2 font-display text-lg font-semibold"><Sparkles size={18} className="text-indigo" aria-hidden /> AI summary</h2>
              <button className="btn-ghost px-3 py-1.5" onClick={generate} disabled={!!busy}>{busy === "ai" ? "…" : ai ? "Regenerate" : "Generate"}</button>
            </div>
            {ai ? (
              <div className="space-y-2 text-sm">
                <p>{ai.summary}</p>
                <p className="text-muted"><span className="font-semibold text-slate-300">Delays:</span> {ai.delay_analysis}</p>
                <p className="text-muted"><span className="font-semibold text-slate-300">Outlook:</span> {ai.prediction}</p>
              </div>
            ) : <p className="text-sm text-muted">No summary yet.</p>}
          </div>
          <dl className="card divide-y divide-line text-sm">
            {fields.filter(([, v]) => v).map(([k, v]) => (
              <div key={k} className="flex justify-between gap-4 px-5 py-3"><dt className="text-muted">{k}</dt><dd className="text-right font-medium">{v}</dd></div>
            ))}
          </dl>
        </div>
      </div>
    </>
  );
}
