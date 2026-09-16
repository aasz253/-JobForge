"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import Spinner from "@/components/Spinner";
import ScoreBar from "@/components/ScoreBar";

export default function JobsPage() {
  const [jobs, setJobs] = useState<any[]>([]);
  const [total, setTotal] = useState(0);
  const [err, setErr] = useState("");
  const [q, setQ] = useState("");

  useEffect(() => {
    api<{ items: any[]; total: number }>("/api/jobs")
      .then((d) => {
        setJobs(d.items);
        setTotal(d.total);
      })
      .catch((e: any) => setErr(e?.message || "Could not list jobs"));
  }, []);

  const filtered = (q ? jobs.filter((j) => (j.title + " " + j.company + " " + j.location).toLowerCase().includes(q.toLowerCase())) : jobs);

  return (
    <div className="space-y-6">
      <section className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-xl font-bold text-zinc-100">Jobs</h1>
          <p className="mt-0.5 text-sm text-zinc-500">
            {total} discovered · sorted by qualification score
          </p>
        </div>
        <div className="flex gap-2">
          <input
            className="input max-w-[180px]"
            placeholder="Search jobs"
            value={q}
            onChange={(e) => setQ(e.target.value)}
          />
          <Link href="/jobs/import" className="btn btn-primary whitespace-nowrap">
            + Import
          </Link>
        </div>
      </section>

      {err && <div className="card text-sm text-ember">{err}</div>}
      {!err && jobs.length === 0 && <div className="card text-sm text-zinc-400">No jobs yet. Import one to begin.</div>}

      <div className="space-y-2">
        {filtered.map((j) => (
          <Link
            key={j.id}
            href={`/jobs/${j.id}`}
            className="flex flex-col gap-2 rounded-xl border border-zinc-800 bg-ink-light px-4 py-3.5 transition hover:border-zinc-700 sm:flex-row sm:items-center sm:justify-between"
          >
            <div className="min-w-0">
              <div className="truncate text-sm font-semibold text-zinc-200">{j.title}</div>
              <div className="mt-0.5 truncate text-xs text-zinc-500">
                {j.company} · {j.location || "Remote"}
              </div>
            </div>
            <div className="flex shrink-0 items-center gap-3">
              <span className="pill border-cember/30 text-ember">
                {j.source?.toUpperCase()}
              </span>
              {typeof j.score === "number" && <ScoreBar score={j.score} />}
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}
