import type { TrackingEvent } from "@/lib/types";
import { formatDateTime } from "@/lib/format";

export function Timeline({ events }: { events: TrackingEvent[] }) {
  if (!events.length) return <p className="text-sm text-muted">No tracking events yet. Try refreshing.</p>;
  // Newest first, regardless of the order the API returns them in.
  const sorted = [...events].sort(
    (a, b) => new Date(b.event_timestamp ?? b.created_at).getTime() - new Date(a.event_timestamp ?? a.created_at).getTime(),
  );
  return (
    <ol className="relative ml-2 border-l border-line">
      {sorted.map((e, i) => (
        <li key={e.id} className="relative pb-6 pl-6 last:pb-0">
          <span className={`absolute -left-[5px] top-1.5 h-2.5 w-2.5 rounded-full ${i === 0 ? "bg-sky ring-4 ring-sky/20" : "bg-slate-600"}`} />
          <p className="text-sm font-semibold">{e.status}</p>
          <p className="text-sm text-muted">{[e.location, formatDateTime(e.event_timestamp)].filter(Boolean).join(" · ")}</p>
          {e.description && <p className="mt-1 text-sm text-slate-300">{e.description}</p>}
        </li>
      ))}
    </ol>
  );
}
