"use client";
import { useCallback, useEffect, useRef, useState } from "react";
import { X, RefreshCw } from "lucide-react";
import { ApiError, post } from "@/lib/api";
import type { Shipment } from "@/lib/types";

interface StartResp { session_id: string; captcha_image: string; tracking_number: string }
interface SubmitResp {
  status: "success" | "captcha_failed";
  captcha_image?: string;
  message?: string;
  shipment?: Shipment;
}

/**
 * In-app India Post CAPTCHA. The user solves the CAPTCHA here; the backend relays it
 * to the live India Post session. We never auto-solve it.
 */
export function CaptchaModal({
  trackingNumber,
  shipmentId,
  onClose,
  onSolved,
}: {
  trackingNumber: string;
  shipmentId?: number;
  onClose: () => void;
  onSolved: (shipment?: Shipment) => void;
}) {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [image, setImage] = useState<string | null>(null);
  const [answer, setAnswer] = useState("");
  const [phase, setPhase] = useState<"loading" | "ready" | "submitting" | "error">("loading");
  const [message, setMessage] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const start = useCallback(async () => {
    setPhase("loading");
    setMessage(null);
    setAnswer("");
    try {
      const d = await post<StartResp>("/tracking/captcha/start", { tracking_number: trackingNumber });
      setSessionId(d.session_id);
      setImage(d.captcha_image);
      setPhase("ready");
    } catch (e) {
      setMessage(e instanceof Error ? e.message : "Could not reach India Post.");
      setPhase("error");
    }
  }, [trackingNumber]);

  useEffect(() => { start(); }, [start]);
  useEffect(() => { if (phase === "ready") inputRef.current?.focus(); }, [phase, image]);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!sessionId || !answer.trim()) return;
    setPhase("submitting");
    setMessage(null);
    try {
      const d = await post<SubmitResp>("/tracking/captcha/submit", {
        session_id: sessionId, answer: answer.trim(), shipment_id: shipmentId,
      });
      if (d.status === "success") {
        onSolved(d.shipment);
        return;
      }
      // Wrong CAPTCHA — India Post handed back a fresh image.
      setImage(d.captcha_image ?? image);
      setAnswer("");
      setMessage(d.message ?? "That didn't go through — try the new image.");
      setPhase("ready");
    } catch (err) {
      const expired = err instanceof ApiError && err.status === 410;
      setMessage(err instanceof Error ? err.message : "Something went wrong.");
      setPhase(expired ? "error" : "ready");
      if (!expired) setAnswer("");
    }
  }

  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-black/70 p-4" role="dialog" aria-modal="true" aria-label="Solve CAPTCHA">
      <div className="card w-full max-w-sm p-6">
        <div className="mb-4 flex items-start justify-between">
          <div>
            <h2 className="font-display text-lg font-semibold">Verify to track</h2>
            <p className="mt-0.5 font-mono text-xs text-muted">{trackingNumber}</p>
          </div>
          <button onClick={onClose} aria-label="Close" className="text-muted hover:text-white"><X size={20} /></button>
        </div>

        <p className="mb-3 text-sm text-muted">
          India Post asks for a CAPTCHA on every lookup. Type what you see below.
        </p>

        <div className="mb-3 grid min-h-[72px] place-items-center rounded-xl border border-line bg-white p-2">
          {phase === "loading" ? (
            <span className="text-sm text-slate-500">Loading CAPTCHA…</span>
          ) : image ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img src={image} alt="CAPTCHA from India Post" className="h-[52px] w-auto" />
          ) : (
            <span className="text-sm text-slate-500">—</span>
          )}
        </div>

        {phase === "error" ? (
          <>
            {message && <p className="mb-3 text-sm text-red-300">{message}</p>}
            <div className="flex gap-2">
              <button onClick={start} className="btn-primary flex-1"><RefreshCw size={16} aria-hidden /> Start over</button>
              <button onClick={onClose} className="btn-ghost">Cancel</button>
            </div>
          </>
        ) : (
          <form onSubmit={submit} className="space-y-3">
            <div className="flex items-center gap-2">
              <input
                ref={inputRef}
                className="input font-mono"
                placeholder="Enter CAPTCHA"
                value={answer}
                autoComplete="off"
                autoCapitalize="characters"
                disabled={phase !== "ready"}
                onChange={(e) => setAnswer(e.target.value)}
              />
              <button type="button" onClick={start} disabled={phase === "submitting"} title="New CAPTCHA"
                className="btn-ghost shrink-0 px-3"><RefreshCw size={16} aria-hidden /></button>
            </div>
            {message && <p className="text-sm text-amber-400">{message}</p>}
            <button className="btn-primary w-full" disabled={phase !== "ready" || !answer.trim()}>
              {phase === "submitting" ? "Tracking…" : "Track"}
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
