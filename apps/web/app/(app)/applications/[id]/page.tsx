"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { api } from "@/lib/api";
import { timeAgo } from "@/lib/format";
import Spinner from "@/components/Spinner";
import ScoreBar from "@/components/ScoreBar";

export default function ApplicationDetailPage() {
  const { id } = useParams();
  const [a, setA] = useState<any>(null);
  const [err, setErr] = useState("");
  const [note, setNote] = useState("");

  useEffect(() => {
    api<any>(`/api/applications/${id}`)
      .then((app) => {
        setA(app);
        setNote(app?.notes || "");
      })
      .catch((e: any) => setErr(e?.message || "Application not found."));
  }, [id]);

  async function addFollowup(e: React.FormEvent) {
    e.preventDefault();
    const fd = new FormData(e.currentTarget as HTMLFormElement);
    try {
      const f = await api<any>("/api/followups", {
        method: "POST",
        body: { application_id: Number(id), kind: fd.get("kind"), note: fd.get("note"), due_on: fd.get("due_on") || null },
      });
      setA({ ...a, followups: [...(a?.followups || []), f] });
    } catch (x: any) {
      setErr(x?.message || "Could not add follow-up.");
    }
  }

  async function saveNote() {
    await api(`/api/applications/${id}`, { method: "PATCH", body: { notes: note } });
  }

  if (err) return <div className="card text-sm text-ember">{err}</div>;
  if (!a) return <Spinner label="Loading application…" />;

  const score = a.job_fit_score != null ? Math.min(Math.round(a.job_fit_score + (a.skills_matched?.length || 0) * 2), 100) : null;

  return (
    <div className="space-y-6">
      <section className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <div className="pill border-accent/30 text-accent">{a.status}</div>
          <h1 className="mt-3 text-2xl font-bold text-zinc-100">{a.job_title}</h1>
          <div className="mt-1 text-sm text-zinc-500">{a.company} · {a.job_location || "—"}</div>
          <div className="mt-adjacent text-xs text-zinc-600">Created {timeAgo(a.created_at)}</div>
        </div>
        {score != null && <ScoreBar score={score} />}
      </section>

      <section className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <Mini label="Score" value={score != null ? `${score}` : "—"} />
        <Mini label="Skills" value={`${a.skills_matched?.length || 0}`} />
        <Mini label="Active" value={a.is_active ? "Yes" : "No"} />
        <Mini label="Note saved" value={note ? "Yes" : "No"} />
      </section>

      {a.job_id && (
        <section className="flex items-center justify-between rounded-xl border border-zinc-800 bg-ink p-4">
          <span className="text-sm text-zinc-300">Tailor your CV and cover letter for this one.</span>
          <Link href={`/jobs/${a.job_id}`} className="btn btn-primary">Open job →</Link>
        </section>
      )}

      <section className="card">
        <h2 className="text-sm font-semibold text-zinc-300">Follow-ups</h2>
        <form onSubmit={addFollowup} className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-[auto_auto_1fr_auto]">
          <select name="kind" className="input">
            {["PROGRESS_UPDATE", "RESUME", "INTERVIEW", "RECRUITER_EMAIL", "RELEVANT_EXPERIENCE", "PITCH"].map((k) => (
              <option key={k} value={k} className="bg-ink">{k.replace(/_/g, " ")}</option>
            ))}
          </select>
          <input name="due_on" type="date" className="input" aria-label="Due on" />
          <input name="note" className="input" placeholder="Remind me when…" />
          <button className="btn btn-primary">Schedule</button>
        </form>
        <div className="mt-4 space-y-2">
          {(a.followups || []).map((f: any) => (
            <div key={f.id} className="flex items-center justify-between rounded-lg border border-zinc-800 bg-ink px-3 py-2 text-sm">
              <div className="min-w-0">
                <span className="pill border-zinc-700 text-zinc-400">{f.kind?.replace(/_/g, " ")}</span>
                <span className="ml-2 text-zinc-300">{f.note}</span>
              </div>
              <span className="ml-3 shrink-0 text-xs text-zinc-500">{f.due_on ? (f.done ? "done" : "due") : ""}</span>
            </div>
          ))}
          {(a.followups || []).length === 0 && <div className="text-sm text-zinc-600">No follow-ups yet. The follow-up engine is what wins offers.</div>}
        </div>
      </section>

      <section className="card">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-semibold text-zinc-300">Notes</h2>
          <button className="btn btn-ghost" onClick={saveNote}>Save</button>
        </div>
        <textarea rows={4} className="input mt-3" value={note} onChange={(e) => setNote(e.target.value)} placeholder="Sparks from the application — interviewer names, salary band, links…" />
      </section>
    </div>
  );
}

function Mini({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-zinc-800 bg-ink p-3">
      <div className="text-[11px] uppercase tracking-wider text-zinc-500">{label}</div>
      <div className="mt-1 font-mono text-lg font-semibold text-zinc-100">{value}</div>
    </div>
  );
}
