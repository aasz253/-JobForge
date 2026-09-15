"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import Stat from "@/components/Stat";
import ScoreBar from "@/components/ScoreBar";
import Spinner from "@/components/Spinner";
import { formatMoney } from "@/lib/format";

export default function FinancePage() {
  const [d, setD] = useState<any>(null);
  const [err, setErr] = useState("");
  const [goal, setGoal] = useState({ target_amount: 1_000_000, currency: "KSh" });
  const [income, setIncome] = useState({ amount: 0, currency: "KSh", category: "EMPLOYMENT", description: "", recorded_on: "" });

  function reload() {
    api<any>("/api/dashboard").then(setD).catch((e: any) => setErr(e?.message || "Could not load finance."));
  }
  useEffect(reload, []);

  async function saveGoal(e: React.FormEvent) {
    e.preventDefault();
    await api<void>("/api/financial-goal", { method: "PUT", body: goal });
    reload();
  }
  async function addIncome(e: React.FormEvent) {
    e.preventDefault();
    await api("/api/income", { method: "POST", body: income });
    setIncome({ amount: 0, currency: "KSh", category: "EMPLOYMENT", description: "", recorded_on: "" });
    reload();
  }

  if (err) return <div className="text-ember">{err}</div>;
  if (!d) return <Spinner label="Forging financials…" />;

  return (
    <div className="space-y-8">
      <section>
        <h1 className="text-2xl font-bold text-zinc-100">Financial goal</h1>
        <p className="mt-1 text-sm text-zinc-500">Every KSh recorded moves the mission.</p>
      </section>

      <section className="grid grid-cols-2 gap-3 md:grid-cols-4">
        <Stat label="Goal" value={`${d.financial_goal_currency} ${formatMoney(d.financial_goal_amount)}`} tone="accent" />
        <Stat label="Earned" value={`${d.financial_goal_currency} ${formatMoney(d.current_income)}`} />
        <Stat label="Progress" value={`${d.financial_progress}%`} tone="ember" />
        <Stat label="Remaining" value={`${d.financial_goal_currency} ${formatMoney(Math.max((d.financial_goal_amount || 0) - (d.current_income || 0), 0))}`} />
      </section>
      <ScoreBar score={d.financial_progress} />

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <form onSubmit={saveGoal} className="card space-y-4">
          <h2 className="text-sm font-semibold text-zinc-300">Set your target</h2>
          <div>
            <label className="label" htmlFor="target">Target amount</label>
            <input id="target" type="number" min={1} step={1000} className="input" value={goal.target_amount} onChange={(e) => setGoal({ ...goal, target_amount: +e.target.value })} />
          </div>
          <div>
            <label className="label" htmlFor="currency">Currency</label>
            <input id="currency" maxLength={12} className="input" value={goal.currency} onChange={(e) => setGoal({ ...goal, currency: e.target.value })} />
          </div>
          <button className="btn btn-primary">Save goal</button>
        </form>

        <form onSubmit={addIncome} className="card space-y-4">
          <h2 className="text-sm font-semibold text-zinc-300">Record income</h2>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label" htmlFor="amount">Amount</label>
              <input id="amount" type="number" min={1} step={0.01} required className="input" value={income.amount} onChange={(e) => setIncome({ ...income, amount: +e.target.value })} />
            </div>
            <div>
              <label className="label" htmlFor="cur">Currency</label>
              <input id="cur" maxLength={12} className="input" value={income.currency} onChange={(e) => setIncome({ ...income, currency: e.target.value })} />
            </div>
          </div>
          <div>
            <label className="label" htmlFor="cat">Category</label>
            <select id="cat" className="input" value={income.category} onChange={(e) => setIncome({ ...income, category: e.target.value })}>
              {["EMPLOYMENT", "FREELANCE", "INTERNSHIP", "CONSULTING", "STIPEND", "OTHER"].map((c) => (
                <option key={c} value={c} className="bg-ink">{c}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="label" htmlFor="desc">Description</label>
            <input id="desc" maxLength={300} className="input" placeholder="e.g. Employment — Ada Labs" value={income.description} onChange={(e) => setIncome({ ...income, description: e.target.value })} />
          </div>
          <div>
            <label className="label" htmlFor="date">Recorded on</label>
            <input id="date" type="date" className="input" value={income.recorded_on} onChange={(e) => setIncome({ ...income, recorded_on: e.target.value })} />
          </div>
          <button className="btn btn-ghost">Add income</button>
        </form>
      </div>

      <section className="card">
        <h2 className="text-sm font-semibold text-zinc-300">Mission target breakdown</h2>
        <div className="mt-4 grid grid-cols-2 gap-2 md:grid-cols-4">
          {Object.entries(d.mission?.targets || {}).map(([k, target]) => (
            <div key={k} className="rounded-lg bg-ink-light px-3 py-2.5 text-sm">
              <div className="truncate text-zinc-500">{k.replace(/_/g, " ")}</div>
              <div className="mt-1">
                <span className="font-mono font-semibold text-zinc-200">{(d.mission?.counts || {})[k] || 0}</span>
                <span className="text-zinc-600"> / {String(target)}</span>
              </div>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
