import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Find. Qualify. Apply. Advance.",
  description:
    "JOBFORGE is a free-first, human-in-the-loop career operating system by the Sifuna Codex. Discover jobs, judge them honestly by real skills, qualify deliberately, apply only with your approval, and measure progress toward a financial goal.",
};

export default function HomePage() {
  return (
    <div className="min-h-screen">
      {/* Hero */}
      <section className="relative overflow-hidden border-b border-zinc-800/70">
        <div
          className="pointer-events-none absolute inset-0 opacity-60"
          style={{
            background:
              "radial-gradient(600px 320px at 20% -10%, rgba(47,129,247,0.14), transparent 60%), radial-gradient(520px 300px at 85% 20%, rgba(248,81,73,0.08), transparent 55%)",
          }}
        />
        <header className="relative mx-auto flex max-w-6xl items-center justify-between px-6 py-5">
          <a href="/" className="font-mono text-xl font-bold tracking-tight text-zinc-100">
            JOB<span className="text-accent">FORGE</span>
          </a>
          <nav className="flex items-center gap-6 text-sm text-zinc-400">
            <a className="hidden hover:text-zinc-200 sm:block" href="#ethics">Ethics</a>
            <a className="hidden hover:text-zinc-200 sm:block" href="#phases">The Plan</a>
            <a href="/login" className="hover:text-zinc-200">Log in</a>
            <a href="/register" className="btn btn-primary">Get started</a>
          </nav>
        </header>

        <div className="relative mx-auto max-w-5xl px-6 pb-24 pt-16 text-center">
          <p className="mx-auto mb-4 w-fit rounded-full border border-zinc-800 bg-ink-light px-3 py-1 text-xs font-medium text-zinc-400">
            ⚒ An open career operating system · Sifuna Codex
          </p>
          <h1 className="mx-auto max-w-3xl text-4xl font-bold leading-tight tracking-tight text-zinc-50 sm:text-6xl">
            Forge a career with{" "}
            <span className="bg-gradient-to-r from-accent to-accent-soft bg-clip-text text-transparent">
              deliberate intent
            </span>
            .
          </h1>
          <p className="mx-auto mt-5 max-w-2xl text-base leading-relaxed text-zinc-400 sm:text-lg">
            Discover jobs. Judge them honestly against your real skills. Qualify
            deliberately. Apply only when <em className="text-zinc-200 not-italic">you</em> say so —
            and advance toward a financial goal you set. No fake CVs, no spam, no
            auto-submits. Ever.
          </p>
          <div className="mt-9 flex items-center justify-center gap-3">
            <a href="/register" className="btn btn-primary px-6 py-2.5 text-base">
              Start the forge
            </a>
            <a
              href="https://github.com/sifunacodex/JOBFORGE"
              className="btn btn-ghost px-6 py-2.5 text-base"
            >
              Read the code
            </a>
          </div>
          <div className="mx-auto mt-14 grid max-w-3xl grid-cols-1 gap-3 sm:grid-cols-3">
            {[
              ["Mission", "KSh 1,000,000 goal · your goal, your pace"],
              ["Process", "Discover → Qualify → Apply → Advance"],
              ["Guardrails", "Human-in-the-loop, injection-safe, audit-logged"],
            ].map(([k, v]) => (
              <div key={k} className="rounded-xl border border-zinc-800 bg-ink-light p-4 text-left">
                <div className="text-sm font-semibold text-zinc-200">{k}</div>
                <div className="mt-1 text-xs leading-relaxed text-zinc-500">{v}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Ethics */}
      <section id="ethics" className="mx-auto max-w-5xl px-6 py-20">
        <h2 className="text-center text-2xl font-bold text-zinc-100 sm:text-3xl">
          Security is a feature, not an afterthought.
        </h2>
        <p className="mx-auto mt-3 max-w-2xl text-center text-sm leading-relaxed text-zinc-400">
          Employers' job descriptions and AI-generated analysis are treated as
          untrusted input. JobForge runs rule-based scoring first — it works fully
          offline, at zero AI cost — and layers AI on top only when you configure it.
          Submissions are never sent without a human gate.
        </p>
        <div className="mt-10 grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {[
            ["🔒", "Prompt-injection defense", "Job text can't rewrite your rules."],
            ["🛡️", "Human-in-the-loop", "Every submission needs your approval."],
            ["🔑", "No secret leaks", "Tokens hashed, secrets encrypted, audit-logged."],
            ["🧩", "Free-first scoring", "Rule-based engine, no paid API required."],
          ].map(([icon, title, desc]) => (
            <div key={title} className="rounded-xl border border-zinc-800 bg-ink-light p-5">
              <div className="text-2xl">{icon}</div>
              <div className="mt-3 text-sm font-semibold text-zinc-200">{title}</div>
              <div className="mt-1 text-xs leading-relaxed text-zinc-500">{desc}</div>
            </div>
          ))}
        </div>
      </section>

      {/* Phases */}
      <section id="phases" className="border-t border-zinc-800/60 bg-ink-light/40 py-20">
        <div className="mx-auto max-w-5xl px-6">
          <h2 className="text-center text-2xl font-bold text-zinc-100 sm:text-3xl">The Roadmap</h2>
          <p className="mx-auto mt-3 max-w-2xl text-center text-sm text-zinc-400">
            One forge at a time. Confirmed so far: sources, scoring, analysis, applications,
            follow-ups, financial goal, profile, dashboard — all live in the API.
          </p>
          <div className="mt-10 space-y-2">
            {([
              ["Phase 1 — Core", "Job sources, rule-based scoring, applications, finance goal, profile, auth.", true],
              ["Phase 2 — Intelligence", "AI analysis, CV tailoring, cover letters, email intelligence, GitHub sync, interview prep.", true],
              ["Phase 3 — Where the money is", "Recruiter outreach, follow-up engine, technical content, offers, DeFI income stream.", true],
              ["Phase 4 — Scale", "Full pipeline automation with human gates, analytics & reporting, mobile-first web.", false],
            ] as const).map(([title, desc, done]: readonly [string, string, boolean]) => (
              <div key={title} className="flex items-start gap-3 rounded-xl border border-zinc-800 bg-ink p-4">
                <span
                  className={`mt-0.5 flex h-5 w-5 items-center justify-center rounded-full text-[11px] ${
                    done ? "bg-success/20 text-success" : "border border-zinc-700 text-zinc-600"
                  }`}
                >
                  {done ? "✓" : "·"}
                </span>
                <div>
                  <div className="text-sm font-semibold text-zinc-200">{title}</div>
                  <div className="mt-0.5 text-xs leading-relaxed text-zinc-500">{desc}</div>
                </div>
              </div>
            ))}
          </div>
          <p className="mt-10 text-center text-xs text-zinc-600">
            Made with deliberate intent by the Sifuna Codex. Financial goal: KSh 1,000,000.
          </p>
        </div>
      </section>
    </div>
  );
}
