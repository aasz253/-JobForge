"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import Spinner from "@/components/Spinner";
import Stat from "@/components/Stat";

export default function ProfilePage() {
  const [d, setD] = useState<any>(null);
  const [err, setErr] = useState("");
  const [form, setForm] = useState({ headline: "", location: "", bio: "", skills: "" });

  useEffect(() => {
    api<any>("/api/profile")
      .then((p: any) => {
        setD(p);
        setForm({
          headline: p?.headline || "",
          location: p?.location || "",
          bio: p?.bio || "",
          skills: (p?.skills || []).join(", "),
        });
      })
      .catch((e: any) => setErr(e?.message || "Could not load profile."));
  }, []);

  async function save(e: React.FormEvent) {
    e.preventDefault();
    setErr("");
    try {
      await api("/api/profile", {
        method: "PUT",
        body: {
          ...form,
          skills: form.skills.split(",").map((s) => s.trim()).filter(Boolean),
        },
      });
    } catch (x: any) {
      setErr(x?.message || "Could not save profile.");
    }
  }

  if (err && !d) return <div className="card text-sm text-ember">{err}</div>;
  if (!d) return <Spinner label="Tempering profile…" />;

  return (
    <div className="space-y-6">
      <section>
        <h1 className="text-xl font-bold text-zinc-100">Profile</h1>
        <p className="mt-1 text-sm text-zinc-500">
          Your craft, in your words. Used to qualify jobs — never used to auto-apply.
        </p>
      </section>

      <section className="grid grid-cols-2 gap-3 md:grid-cols-4">
        <Stat label="Headline" value={d?.headline || "—"} sub={d?.location || "No location"} />
        <Stat label="Name" value={d?.full_name || "—"} sub={d?.email || ""} />
        <Stat label="Skills" value={d?.skills?.length || 0} tone="accent" sub="on file" />
        <Stat label="Cf. target salary" value={d?.salary_expectation_min || "—"} tone="ember" />
      </section>

      <form onSubmit={save} className="card space-y-4">
        <div>
          <label className="label" htmlFor="headline">Headline</label>
          <input id="headline" className="input" value={form.headline} onChange={(e) => setForm({ ...form, headline: e.target.value })} placeholder="Backend engineer · FastAPI & Go" />
        </div>
        <div>
          <label className="label" htmlFor="location">Location</label>
          <input id="location" className="input" value={form.location} onChange={(e) => setForm({ ...form, location: e.target.value })} placeholder="Nairobi · hybrid-friendly" />
        </div>
        <div>
          <label className="label" htmlFor="bio">Bio</label>
          <textarea id="bio" rows={4} className="input" value={form.bio} onChange={(e) => setForm({ ...form, bio: e.target.value })} placeholder="What you build, who you serve, what you're after." />
        </div>
        <div>
          <label className="label" htmlFor="skills">Skills</label>
          <textarea id="skills" rows={2} className="input" value={form.skills} onChange={(e) => setForm({ ...form, skills: e.target.value })} placeholder="Python, FastAPI, PostgreSQL, React" />
        </div>
        <div className="flex items-center gap-3">
          <button className="btn btn-primary">Save profile</button>
          {err && <span className="text-sm text-ember">{err}</span>}
        </div>
      </form>
    </div>
  );
}
