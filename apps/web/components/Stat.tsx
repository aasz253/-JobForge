export default function Stat({ label, value, sub, tone = "default" }: { label: string; value: React.ReactNode; sub?: string; tone?: "default" | "accent" | "ember" }) {
  const colors = { default: "text-zinc-100", accent: "text-accent", ember: "text-ember" };
  return (
    <div className="rounded-xl border border-ink-lightest bg-ink-light p-4 shadow-panel">
      <div className="text-[11px] uppercase tracking-wider text-zinc-400">{label}</div>
      <div className={`mt-1 text-2xl font-semibold tabular-nums ${colors[tone]}`}>{value}</div>
      {sub && <div className="mt-0.5 text-xs text-zinc-500">{sub}</div>}
    </div>
  );
}
