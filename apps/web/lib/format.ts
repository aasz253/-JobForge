export function formatMoney(n: number | string | null | undefined, currency = "KSh"): string {
  const v = typeof n === "number" ? n : Number(n || 0);
  return `${currency} ${v.toLocaleString("en-US", { maximumFractionDigits: 0 })}`;
}

export function formatDate(iso?: string | null): string {
  if (!iso) return "—";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" });
}

export function timeAgo(iso?: string | null): string {
  if (!iso) return "—";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  const s = Math.round((Date.now() - d.getTime()) / 1000);
  if (s < 60) return "just now";
  const m = Math.round(s / 60);
  if (m < 60) return `${m}m ago`;
  const h = Math.round(m / 60);
  if (h < 24) return `${h}h ago`;
  const days = Math.round(h / 24);
  return `${days}d ago`;
}

export function pct(n: number | string | null | undefined): number {
  const v = typeof n === "number" ? n : Number(n || 0);
  return Math.max(0, Math.min(100, Math.round(v)));
}
