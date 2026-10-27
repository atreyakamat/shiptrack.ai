"use client";
import { useState } from "react";
import { ErrorBox, Empty, Loading, PageHeader } from "@/components/ui";
import { post } from "@/lib/api";
import { useApi } from "@/lib/useApi";
import { formatDateTime } from "@/lib/format";
import type { AppNotification } from "@/lib/types";

export default function NotificationsPage() {
  const { data, error, loading, reload } = useApi<AppNotification[]>("/notifications");
  const [busy, setBusy] = useState(false);

  async function markAll() {
    setBusy(true);
    try { await post("/notifications/read-all"); await reload(); } finally { setBusy(false); }
  }

  return (
    <>
      <PageHeader title="Notifications" subtitle="Updates about your shipments"
        actions={<button className="btn-ghost" onClick={markAll} disabled={busy || !data?.length}>Mark all read</button>} />
      {error && <ErrorBox message={error} />}
      {loading && !data && <Loading />}
      {data && data.length === 0 && <Empty title="You're all caught up" body="Status changes and delivery alerts will show up here." />}
      {data && data.length > 0 && (
        <ul className="card divide-y divide-line">
          {data.map((n) => (
            <li key={n.id} className="px-5 py-4">
              <p className="text-sm">{n.message}</p>
              <p className="mt-1 text-xs text-muted">{n.notification_type.replace(/_/g, " ").toLowerCase()} · {formatDateTime(n.created_at)}</p>
            </li>
          ))}
        </ul>
      )}
    </>
  );
}
