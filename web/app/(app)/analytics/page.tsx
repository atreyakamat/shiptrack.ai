"use client";
import { Bar, BarChart, CartesianGrid, Cell, Line, LineChart, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { Download } from "lucide-react";
import { Empty, ErrorBox, Loading, PageHeader, Stat } from "@/components/ui";
import { statusLabel } from "@/components/StatusBadge";
import { getToken } from "@/lib/api";
import { useApi } from "@/lib/useApi";
import type { Analytics } from "@/lib/types";

const COLORS = ["#38bdf8", "#818cf8", "#c084fc", "#34d399", "#fbbf24", "#94a3b8"];
const tip = { contentStyle: { background: "#0b1226", border: "1px solid #1e293b", borderRadius: 12 }, itemStyle: { color: "#f8fafc" } };

function Panel({ title, children }: { title: string; children: React.ReactNode }) {
  return <div className="card p-5"><h2 className="mb-4 font-display text-base font-semibold">{title}</h2><div className="h-64">{children}</div></div>;
}

async function exportCsv() {
  const res = await fetch("/api/analytics/export", { headers: { Authorization: `Bearer ${getToken()}` } });
  if (!res.ok) throw new Error("Export failed");
  const url = URL.createObjectURL(await res.blob());
  const a = Object.assign(document.createElement("a"), { href: url, download: "shiptrack_export.csv" });
  a.click();
  URL.revokeObjectURL(url);
}

export default function AnalyticsPage() {
  const { data, error, loading } = useApi<Analytics>("/analytics");
  if (loading && !data) return <Loading />;
  if (error || !data) return <ErrorBox message={error ?? "No data"} />;
  const { overview: o } = data;
  const status = data.by_status.map((d) => ({ name: statusLabel(d.status), value: d.count }));

  return (
    <>
      <PageHeader title="Analytics" subtitle="Delivery performance"
        actions={<button className="btn-ghost" onClick={() => exportCsv().catch((e) => alert(e.message))}><Download size={16} aria-hidden /> Export CSV</button>} />
      {o.total === 0 ? <Empty title="Nothing to analyse yet" body="Add a few shipments and come back." /> : (
        <>
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <Stat label="Shipments" value={o.total} />
            <Stat label="Delivery rate" value={`${o.delivery_rate}%`} />
            <Stat label="Avg. transit (days)" value={o.avg_time} />
            <Stat label="Needs attention" value={o.delayed} />
          </div>
          <div className="mt-6 grid gap-6 lg:grid-cols-2">
            <Panel title="By status">
              <ResponsiveContainer><PieChart><Pie data={status} dataKey="value" nameKey="name" innerRadius={55} outerRadius={90} paddingAngle={2} label>
                {status.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} stroke="none" />)}</Pie><Tooltip {...tip} /></PieChart></ResponsiveContainer>
            </Panel>
            <Panel title="Shipments over time">
              <ResponsiveContainer><LineChart data={data.shipments_over_time}><CartesianGrid stroke="#1e293b" /><XAxis dataKey="period" stroke="#94a3b8" fontSize={12} /><YAxis allowDecimals={false} stroke="#94a3b8" fontSize={12} /><Tooltip {...tip} /><Line dataKey="count" stroke="#38bdf8" strokeWidth={2} dot={false} /></LineChart></ResponsiveContainer>
            </Panel>
            <Panel title="Most common locations">
              <ResponsiveContainer><BarChart data={data.common_locations.slice(0, 6)} layout="vertical" margin={{ left: 40 }}><CartesianGrid stroke="#1e293b" /><XAxis type="number" allowDecimals={false} stroke="#94a3b8" fontSize={12} /><YAxis type="category" dataKey="location" width={120} stroke="#94a3b8" fontSize={11} /><Tooltip {...tip} /><Bar dataKey="count" fill="#818cf8" radius={[0, 6, 6, 0]} /></BarChart></ResponsiveContainer>
            </Panel>
            <Panel title="Avg. delivery days by carrier">
              <ResponsiveContainer><BarChart data={data.avg_delivery_by_carrier}><CartesianGrid stroke="#1e293b" /><XAxis dataKey="carrier" stroke="#94a3b8" fontSize={12} /><YAxis stroke="#94a3b8" fontSize={12} /><Tooltip {...tip} /><Bar dataKey="avg_days" fill="#c084fc" radius={[6, 6, 0, 0]} /></BarChart></ResponsiveContainer>
            </Panel>
          </div>
        </>
      )}
    </>
  );
}
