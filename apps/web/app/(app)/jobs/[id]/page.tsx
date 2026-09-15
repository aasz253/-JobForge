"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { api } from "@/lib/api";
import Spinner from "@/components/Spinner";
import ScoreBar from "@/components/ScoreBar";
import Stat from "@/components/Stat";

export default function JobDetailPage() {
  const { id } = useParams();
  const [job, setJob] = useState<any>(null);
  const [score, setScore] = useState<any>(null);
  const [err, setErr] = useState("");

  useEffect(() => {
    api<any>(`/api/jobs/${id}`)
      .then(setJob)
      .catch((e: any) => setErr(e?.message || "Job not found"));
    api<any>(`/api/jobs/${id}/score`)
      .then(setScore)
      .catch(() => {});
  }, [id]);

  if (err) return <div className="card text-sm text-ember">{err}</div>;
  if (!job) return <Spinner label="Forging job details…" />;

  const s = score?.score ?? 0;
  const band = s >= 80 ? "Qualified" : s >= 60 ? "Borderline" : "Cold";
  const bandColor = s >= 80 ? "text-success" : s >= 60 ? "text-ember" : "text-zinc-500";

  return (
    <div className="space-y-6">
      <section className="card">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
          <div className="min-w-0">
            <div className="text-xs text-zinc-500">{job.source?.toUpperCase()} · {job.location || "Remote"}</div>
            <h1 className="mt-1 text-xl font-bold text-zinc-100">{job.title}</h1>
            <div className="mt-1 text-sm text-zinc-400">{job.company}</div>
            <div className="mt-3 flex flex-wrap gap-4 text-sm">
              <div className="text-zinc-500">
                Band: <span className={`font-semibold ${bandColor}`}>{band}</span>
              </div>
              <div className="text-zinc-500">
                Score: <span className="font-semibold text-zinc-200">{Math.round(s)}</span>
              </div>
            </div>
          </div>
          <div className="flex shrink-0 flex-col items-end gap-2">
            <ScoreBar score={s} />
            <div className="flex gap-2">
              <a
                href={job.application_url || job.url}
                target="_blank"
                rel="noopener noreferrer"
                className="btn btn-ghost"
              >
                Original post
              </a>
              <Link href={`/applications/new?job_id=${job.id}`} className="btn btn-primary">
                Start application
              </Link>
            </div>
          </div>
        </div>
      </section>

      {score?.breakdown && (
        <section className="card">
          <h2 className="text-sm font-semibold text-zinc-300">Score breakdown</h2>
          <div className="mt-4 grid grid-cols-2 gap-3 md:grid-cols-3">
            {Object.entries(score.breakdown).map(([k, v]: any) => (
              <div key={k} className="rounded-lg border border-zinc-800 bg-ink px-3 py-2">
                <div className="text-xs capitalize text-zinc-500">{k.replace(/_/g, " ")}</div>
                <div className="mt-0.5 font-mono text-lg font-semibold text-zinc-200">{v}</div>
              </div>
            ))}
          </div>
        </section>
      )}

      <section className="card">
        <h2 className="text-sm font-semibold text-zinc-300">Details</h2>
        <div className="prose prose-invert mt-3 max-w-none whitespace-pre-wrap text-sm leading-relaxed text-zinc-400">
          {job.description || "No description provided."}
        </div>
        {job.skills_matched && job.skills_matched.length > 0 && (
          <div className="mt-5">
            <div className="text-xs text-zinc-500">Skills that piqued the anvil</div>
            <div className="mt-2 flex flex-wrap gap-1.5">
              {job.skills_matched.map((sk: string) => (
                <span key={sk} className="pill border-success/30 text-success">{sk}</span>
              ))}
            </div>
          </div>
        )}
      </section>
    </div>
  );
}
