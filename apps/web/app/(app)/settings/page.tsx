"use client";

import { useState } from "react";
import { api, setToken } from "@/lib/api";

const prefs = [
  { k: "notify_daily_digest", label: "Daily digest" },
  { k: "notify_score_updates", label: "Score updates" },
  { k: "notify_followup_due", label: "Follow-up reminders" },
  { k: "autosync_skill_scores", label: "Re-score after profile changes" },
];

export default function SettingsPage() {
  const [s, setS] = useState<any>({ notify_daily_digest: true });
  const [msg, setMsg] = useState("");

  async function save() {
    setMsg("");
    try {
      await api("/api/settings", { method: "PUT", body: s });
      setMsg("Saved.");
    } catch (e: any) {
      setMsg(e?.message || "Could not save settings.");
    }
  }

  return (
    <div className="space-y-8">
      <section>
        <h1 className="text-xl font-bold text-zinc-100">Settings</h1>
        <p className="mt-0.5 text-sm text-zinc-500">Inbox nudges, not spam. Everything can be silenced.</p>
      </section>

      <section className="card">
        <h2 className="text-sm font-semibold text-zinc-300">Notifications</h2>
        <div className="mt-4 space-y-2.5">
          {prefs.map((p) => (
            <label key={p.k} className="flex items-center gap-3 text-sm text-zinc-300">
              <input
                type="checkbox"
                className="h-4 w-4 rounded border-zinc-700 bg-ink-light checked:bg-accent"
                checked={!!s[p.k]}
                onChange={(e) => setS({ ...s, [p.k]: e.target.checked })}
              />
              {p.label}
            </label>
          ))}
        </div>
        <div className="mt-7 flex items-center gap-3">
          <button className="btn btn-primary" onClick={save}>
            Save settings
          </button>
          {msg && <span className="text-sm text-success">{msg}</span>}
        </div>
      </section>

      <section className="card border-ember/20">
        <h2 className="text-sm font-semibold text-zinc-300">Danger zone</h2>
        <p className="mt-1 text-xs text-zinc-500">
          Deleting wipes your jobs, applications and progress. There is no undo.
        </p>
        <button
          className="mt-4 btn btn-danger"
          onClick={async () => {
            if (!confirm("Delete your entire JOBFORGE account and data?")) return;
            await api("/api/auth/me", { method: "DELETE" });
            setToken(null);
            location.href = "/";
          }}
        >
          Delete account
        </button>
      </section>
    </div>
  );
}
