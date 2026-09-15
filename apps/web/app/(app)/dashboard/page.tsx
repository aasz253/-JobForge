"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import Stat from "@/components/Stat";
import ScoreBar from "@/components/ScoreBar";
import Spinner from "@/components/Spinner";

export default function DashboardPage() {
  const [d, setD] = useState<any>(null);
  const [err, setErr] = useState("");

  useEffect(() => {
    api<any>("/api/dashboard")
      .then(setD)
      .catch((e: any) => setErr(e?.message || "Could not load dashboard"));
  }, []);

  if (err) return <div className="text-ember">{err}</div>;
  if (!d) return <Spinner label="Forging your overview…" />;

  return (
    <div className="space-y-8">
      <section>
        <h1 className="text-2xl font-bold text-zinc-100">The Forge</h1>
        <p className="mt-1 text-sm text-zinc-500">
          Discover → Qualify → Apply → Advance. Deliberately.
        </p>
      </section>

      <section className="grid grid-cols-2 gap-3 md:grid-cols-4">
        <Stat label="Jobs discovered" value={d.jobs_discovered} />
        <Stat label="Qualified" value={d.qualified_jobs} tone="accent" />
        <Stat label="Applied / week" value={d.applications_this_week} />
        <Stat label="Interviews" value={d.interviews} tone="ember" />
      </section>

      <section className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <div className="card">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold text-zinc-300">Mission progress</h2>
            <span className="text-xs text-zinc-500">{d.mission?.percent ?? 0}%</span>
          </div>
          <div className="mt-3 overflow-hidden rounded-full bg-ink-lightest">
            <div
              className="h-2 rounded-full bg-accent transition-all"
              style={{ width: `${d.mission?.percent ?? 0}%` }}
            />
          </div>
          <div className="mt-4 space-y-2 text-sm">
            {Object.entries(d.mission?.targets || {}).map(([k, target]) => (
              <div key={k} className="flex items-center justify-between text-zinc-400">
                <span className="capitalize">{k.replace(/_/g, " ")}</span>
                <span className="text-zinc-300">
                  <span className="font-semibold">{(d.mission?.counts || {})[k] || 0}</span>
                  <span className="text-zinc-600"> / {String(target)}</span>
                </span>
              </div>
            ))}
          </div>
        </div>

        <div className="card">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold text-zinc-300">Financial goal</h2>
            <Link href="/finance" className="text-xs text-accent hover:underline">
              Adjust →
            </Link>
          </div>
          <div className="mt-3 flex items-end justify-between">
            <div>
              <div className="font-mono text-2xl font-bold text-zinc-100">
                {d.mission?.counts ? "" : ""}
                {d.financial_goal_currency} {Number(d.financial_goal_amount || 0).toLocaleString()}
              </div>
              <div className="mt-1 text-xs text-zinc-500">
                Earned {d.financial_goal_currency} {Number(d.current_income || 0).toLocaleString()} ·{" "}
                {d.financial_progress}% of goal
              </div>
            </div>
          </div>
          <div className="mt-4">
            <ScoreBar score={d.financial_progress} />
          </div>
        </div>
      </section>

      <section>
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-sm font-semibold text-zinc-300">Top qualified jobs</h2>
          <Link href="/jobs" className="text-xs text-accent hover:underline">
            Browse all →
          </Link>
        </div>
        <div className="space-y-2">
          {(d.top_jobs || []).slice(0, 5).map((j: any) => (
            <Link
              key={j.id}
              href={`/jobs/${j.id}`}
              className="flex items-center justify-between rounded-lg border border-zinc-800 bg-ink-light px-4 py-3 transition hover:border-zinc-700"
            >
              <div className="min-w-0">
                <div className="truncate text-sm font-medium text-zinc-200">{j.title}</div>
                <div className="mt-0.5 truncate text-xs text-zinc-500">
                  {j.company} · {j.location || "Remote"}
                </div>
              </div>
              <ScoreBar score={j.score ?? 0} />
            </Link>
          ))}
          {(d.top_jobs || []).length === 0 && (
            <p className="text-sm text-zinc-600">
              No jobs yet —{" "}
              <Link href="/jobs" className="text-accent hover:underline">
                forge your pipeline
              </Link>
              .
            </p>
          )}
        </div>
      </section>
    </div>
  );
}
