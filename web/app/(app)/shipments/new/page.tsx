"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { ErrorBox, PageHeader } from "@/components/ui";
import { CaptchaModal } from "@/components/CaptchaModal";
import { api, post } from "@/lib/api";
import { detectCarrier, normalizeTrackingId } from "@/lib/carrier";
import type { Shipment } from "@/lib/types";

interface OcrResult { id: number; extracted_tracking_number: string | null; candidates: string[]; is_demo?: boolean }
type CreatedShipment = Shipment & { needs_captcha?: boolean };

export default function NewShipment() {
  const router = useRouter();
  const [trackingNumber, setTrackingNumber] = useState("");
  const [description, setDescription] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const carrier = detectCarrier(trackingNumber);
  const [ocr, setOcr] = useState<OcrResult | null>(null);
  const [pending, setPending] = useState<CreatedShipment | null>(null);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!carrier) {
      setError("That doesn't look like an India Post ID. Expected 2 letters, 9 digits, then IN (e.g. EM123456789IN).");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const tn = normalizeTrackingId(trackingNumber);
      const s = ocr
        ? await post<CreatedShipment>("/ocr/confirm", { document_id: ocr.id, tracking_number: tn, carrier: carrier.code })
        : await post<CreatedShipment>("/shipments", { tracking_number: tn, carrier: carrier.code, description: description || undefined });
      // In web mode the shipment is saved but needs an in-app CAPTCHA for its first lookup.
      if (s.needs_captcha) {
        setPending(s);
        setBusy(false);
        return;
      }
      router.push(`/shipments/${s.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not add shipment");
      setBusy(false);
    }
  }

  async function scan(file: File) {
    setBusy(true);
    setError(null);
    try {
      const fd = new FormData();
      fd.append("file", file);
      const r = await api<OcrResult>("/ocr", { method: "POST", body: fd });
      setOcr(r);
      setTrackingNumber(r.extracted_tracking_number ?? r.candidates[0] ?? "");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Scan failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="max-w-xl">
      {pending && (
        <CaptchaModal
          trackingNumber={pending.tracking_number}
          shipmentId={pending.id}
          onClose={() => router.push(`/shipments/${pending.id}`)}
          onSolved={() => router.push(`/shipments/${pending.id}`)}
        />
      )}
      <PageHeader title="Add shipment" subtitle="Paste an India Post tracking ID or scan a postal receipt" />
      <form onSubmit={submit} className="card space-y-4 p-6">
        <div>
          <label htmlFor="scan" className="label">Scan a receipt (PNG, JPG or PDF)</label>
          <input id="scan" type="file" accept=".png,.jpg,.jpeg,.pdf" className="input file:mr-3 file:rounded-lg file:border-0 file:bg-panel-2 file:px-3 file:py-1 file:text-slate-200"
            disabled={busy} onChange={(e) => e.target.files?.[0] && scan(e.target.files[0])} />
          {ocr?.is_demo && <p className="mt-2 text-xs text-amber-400">OCR is running in demo mode — the number below is simulated. Please verify it.</p>}
          {ocr && ocr.candidates.length > 1 && (
            <div className="mt-2 flex flex-wrap gap-2">
              {ocr.candidates.map((c) => <button type="button" key={c} onClick={() => setTrackingNumber(c)} className="btn-ghost px-3 py-1 font-mono text-xs">{c}</button>)}
            </div>
          )}
        </div>
        <div>
          <label htmlFor="tn" className="label">Tracking number</label>
          <input id="tn" required className="input font-mono" placeholder="EM100000002IN" value={trackingNumber} onChange={(e) => setTrackingNumber(e.target.value)} />
          <p className="mt-1.5 text-xs text-muted">{trackingNumber ? (carrier ? `Detected: ${carrier.label}` : "Not a recognised India Post ID yet") : "We detect the carrier from the ID. Currently India Post."}</p>
        </div>
        {!ocr && (
          <div>
            <label htmlFor="desc" className="label">Description (optional)</label>
            <input id="desc" className="input" placeholder="Documents for the bank" value={description} onChange={(e) => setDescription(e.target.value)} />
          </div>
        )}
        {error && <ErrorBox message={error} />}
        {busy && <p className="text-xs text-muted" role="status">Looking this up. If an India Post browser window opened, enter the CAPTCHA there and press TRACK (up to 90 seconds).</p>}
        <button className="btn-primary w-full" disabled={busy || !trackingNumber}>{busy ? "Working…" : "Add shipment"}</button>
      </form>
    </div>
  );
}
