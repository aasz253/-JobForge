"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { api, ApiError, setToken } from "@/lib/api";

export default function RegisterPage() {
  const router = useRouter();
  const [form, setForm] = useState({ email: "", password: "", full_name: "" });
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setErr("");
    setBusy(true);
    try {
      const res = await api<{ access_token: string }>("/api/auth/register", {
        method: "POST",
        body: form,
      });
      setToken(res.access_token);
      router.push("/onboarding");
    } catch (x) {
      setErr(x instanceof ApiError ? x.message : "Could not reach the forge.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center px-4">
      <div className="w-full max-w-sm">
        <Link href="/" className="mb-8 block font-mono text-2xl font-bold tracking-tight text-zinc-100">
          JOB<span className="bg-gradient-to-r from-accent via-violet to-blush bg-clip-text text-transparent">FORGE</span>
        </Link>
        <div className="card">
          <h1 className="text-lg font-semibold text-zinc-100">Forge an account</h1>
          <p className="mt-1 text-sm text-zinc-400">
            Free-first, human-in-the-loop. No fake applications, ever.
          </p>
          <form onSubmit={submit} className="mt-6 space-y-4">
            {err && <div className="rounded-lg border border-ember/40 bg-ember/10 px-3 py-2 text-sm text-ember">{err}</div>}
            <div>
              <label className="label" htmlFor="full_name">Full name</label>
              <input id="full_name" type="text" required autoComplete="name" className="input" placeholder="Ada Lovelace" value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} />
            </div>
            <div>
              <label className="label" htmlFor="email">Email</label>
              <input id="email" type="email" required autoComplete="email" className="input" placeholder="you@forge.dev" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
            </div>
            <div>
              <label className="label" htmlFor="password">Password</label>
              <input id="password" type="password" required minLength={8} autoComplete="new-password" className="input" placeholder="Min 8 chars" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} />
            </div>
            <button type="submit" disabled={busy} className="btn btn-primary w-full">
              {busy ? "Forging…" : "Create account"}
            </button>
          </form>
          <p className="mt-4 text-center text-sm text-zinc-400">
            Already forging?{" "}
            <Link href="/login" className="font-medium text-accent hover:underline">Log in</Link>
          </p>
        </div>
      </div>
    </main>
  );
}
