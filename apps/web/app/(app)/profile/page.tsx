"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import Spinner from "@/components/Spinner";
import Stat from "@/components/Stat";

interface Skill {
  id: number;
  name: string;
}

export default function ProfilePage() {
  const [d, setD] = useState<any>(null);
  const [user, setUser] = useState<any>(null);
  const [skills, setSkills] = useState<Skill[]>([]);
  const [err, setErr] = useState("");
  const [saved, setSaved] = useState(false);
  const [form, setForm] = useState({ name: "", headline: "", location: "", bio: "", skills: "" });

  useEffect(() => {
    Promise.all([
      api<any>("/api/auth/me"),
      api<any>("/api/profile"),
      api<Skill[]>("/api/skills"),
    ])
      .then(([u, p, sk]) => {
        setUser(u);
        setD(p);
        setSkills(sk);
        setForm({
          name: u?.full_name || "",
          headline: p?.headline || "",
          location: p?.city || p?.country || "",
          bio: p?.summary || "",
          skills: (sk || []).map((s) => s.name).join(", "),
        });
      })
      .catch((e: any) => setErr(e?.message || "Could not load profile."));
  }, []);

  async function save(e: React.FormEvent) {
    e.preventDefault();
    setErr("");
    setSaved(false);
    try {
      await api("/api/profile", {
        method: "PUT",
        body: {
          full_name: form.name,
          headline: form.headline,
          city: form.location,
          summary: form.bio,
        },
      });
      const wanted = form.skills.split(",").map((s) => s.trim()).filter(Boolean);
      const current = new Set(skills.map((s) => s.name));
      for (const s of skills) {
        if (!wanted.includes(s.name)) await api(`/api/skills/${s.id}`, { method: "DELETE" });
      }
      for (const name of wanted) {
        if (!current.has(name)) {
          await api("/api/skills", { method: "POST", body: { name, category: "other", proficiency: "", evidence: "" } });
        }
      }
      const sk = await api<Skill[]>("/api/skills");
      setSkills(sk);
      setSaved(true);
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
        <Stat label="Headline" value={d?.headline || "—"} sub={d?.city || "No location"} />
        <Stat label="Name" value={user?.full_name || "—"} sub={user?.email || ""} />
        <Stat label="Skills" value={skills.length} tone="accent" sub="on file" />
        <Stat label="Cf. target salary" value={d?.salary_expectation_min || "—"} tone="ember" />
      </section>

      <form onSubmit={save} className="card space-y-4">
        <div>
          <label className="label" htmlFor="name">Name</label>
          <input id="name" className="input" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} placeholder="Ada Lovelace" />
        </div>
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
          {saved && <span className="text-sm text-success">Saved</span>}
          {err && <span className="text-sm text-ember">{err}</span>}
        </div>
      </form>
    </div>
  );
}