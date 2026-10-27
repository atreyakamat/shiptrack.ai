const STYLES: Record<string, string> = {
  BOOKED: "bg-slate-500/15 text-slate-300",
  IN_TRANSIT: "bg-sky/15 text-sky",
  OUT_FOR_DELIVERY: "bg-indigo/15 text-indigo",
  DELIVERED: "bg-emerald-500/15 text-emerald-400",
  EXCEPTION: "bg-amber-500/15 text-amber-400",
  UNKNOWN: "bg-slate-500/15 text-slate-400",
};

export const statusLabel = (s: string) =>
  s.replace(/_/g, " ").toLowerCase().replace(/^\w/, (c) => c.toUpperCase());

export function StatusBadge({ status }: { status: string }) {
  return (
    <span className={`inline-flex rounded-full px-2.5 py-1 text-xs font-semibold ${STYLES[status] ?? STYLES.UNKNOWN}`}>
      {statusLabel(status)}
    </span>
  );
}
