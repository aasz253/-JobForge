"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import Spinner from "@/components/Spinner";
import { timeAgo } from "@/lib/format";

const statuses = [
  { v: "discovered", label: "Shipment" },
  { v: "qualifying", label: "Qualifying" },
  { v: "ready", label: "Ready" },
  { v: "applied", label: "Applied" },
  { v: "followup", label: "Follow-ups" },
  { v: "interview", label: "Interviews" },
  { v: "offer", label: "Offers" },
  { v: "accepted", label: "Accepted" },
  { v: "rejected", label: "Closed" },
];

const statusDot: Record<string, string> = {
  applied: "bg-content",
  followup: "bg-amber",
  interview: "bg-ember",
  offer: "bg-emerald",
  accepted: "bg-emerald",
  rejected: "bg-zinc-600",
};

export default function ApplicationsPage() {
  const [apps, setApps] = useState<any[]>([]);
  const [jobs, setJobs] = useState<any[]>([]);
  const [err, setErr] = useState("");

  useEffect(() => {
    api<any[]>("/api/applications")
      .then(setApps)
      .catch((e: any) => setErr(e?.message || "Could not load applications."));
    api<{ items: any[]; total: number }>("/api/jobs")
      .then((d) => setJobs(d.items))
      .catch(() => {});
  }, []);

  async function create(jobId: number) {
    try {
      await api("/api/applications", { method: "POST", body: { job_id: jobId } });
    } catch (e: any) {
      alert(e?.message || "Could not create application");
    }
  }

  const columns = statuses.filter((s) => !["qualifying", "ready"].includes(s.v));
  const byStatus = (v: string) => apps.filter((a) => a.status === v);

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-xl font-bold text-zinc-100">Applications</h1>
        <p className="mt-0.5 text-sm text-zinc-500">Every submission started, owned, and followed up by you — never auto-sent.</p>
      </header>

      {err && <div className="card text-sm text-ember">{err}</div>}
      {!err && apps.length === 0 && (
        <div className="card text-sm text-zinc-400">
          Nothing shipped yet. <Link href="/jobs" className="text-accent hover:underline">Start an application from a qualified job →</Link>
        </div>
      )}

      <section className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-5">
        {columns.map((c) => {
          const list = byStatus(c.v);
          return (
            <div key={c.v} className="rounded-xl border border-ink-lightest bg-ink-light p-2">
              <div className="mb-2 flex items-center gap-1.5 px-1 text-[11px] font-semibold uppercase tracking-wide text-zinc-500">
                <span className={`h-1.5 w-1.5 rounded-full ${statusDot[c.v] || "bg-zinc-700"}`} />
                {c.label}
              </div>
              <div className="space-y-1.5">
                {list.map((a) => (
                  <Link key={a.id} href={`/applications/${a.id}`} className="block rounded-lg border border-ink-lightest bg-ink px-2.5 py-2 text-xs text-zinc-300 transition hover:border-zinc-700">
                    <div className="truncate font-medium">{a.job_title || "Untitled job"}</div>
                    <div className="mt-0.5 truncate text-[11px] text-zinc-500">{a.company}</div>
                    <div className="mt-0.5 text-[10px] text-zinc-600">{timeAgo(a.updated_at || a.created_at)}</div>
                  </Link>
                ))}
                {list.length === 0 && <div className="px-1 py-3 text-center text-[11px] text-zinc-700">—</div>}
              </div>
            </div>
          );
        })}
      </section>
    </div>
  );
}
