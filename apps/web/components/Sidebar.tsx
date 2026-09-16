"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { LogoutButton } from "./client";

const nav = [
  { href: "/dashboard", label: "Overview" },
  { href: "/jobs", label: "Jobs" },
  { href: "/applications", label: "Applications" },
  { href: "/finance", label: "Goal & Finance" },
  { href: "/profile", label: "Profile" },
  { href: "/settings", label: "Settings" },
];

export default function Sidebar() {
  const path = usePathname();
  return (
    <aside className="flex w-56 flex-col gap-1 border-r border-ink-lightest bg-ink px-3 py-5">
      <Link href="/" className="mb-6 px-2 font-mono text-lg font-bold tracking-tight text-zinc-100">
        JOB<span className="bg-gradient-to-r from-accent via-violet to-blush bg-clip-text text-transparent">FORGE</span>
      </Link>
      <nav className="flex flex-col gap-0.5">
        {nav.map((n) => {
          const active = path === n.href || (n.href !== "/dashboard" && path.startsWith(n.href));
          return (
            <Link key={n.href} href={n.href} className={`rounded-lg px-3 py-2 text-sm font-medium transition-colors ${active ? "bg-ink-lighter text-accent" : "text-zinc-400 hover:bg-ink-lighter hover:text-zinc-200"}`}>
              {n.label}
            </Link>
          );
        })}
      </nav>
      <div className="mt-auto px-2 text-[10px] text-zinc-500">Find. Qualify. Apply. Advance.<br />by Sifuna Codex</div>
      <div className="mt-2 px-2"><LogoutButton /></div>
    </aside>
  );
}
