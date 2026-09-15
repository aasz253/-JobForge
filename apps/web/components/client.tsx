"use client";

import { useRouter } from "next/navigation";
import { createContext, useContext, useEffect, useState } from "react";
import { api, getToken, setToken } from "@/lib/api";

export interface User {
  id: number;
  email: string;
  full_name: string;
  is_active: boolean;
}

export const AppCtx = createContext<{ user: User | null; refreshUsr: () => void }>({ user: null, refreshUsr: () => {} });
export const useApp = () => useContext(AppCtx);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const router = useRouter();
  async function refreshUsr() {
    const t = getToken();
    if (!t) { setUser(null); return; }
    try {
      const u = await api<User>("/api/auth/me", { token: t });
      setUser(u);
    } catch {
      setToken(null);
      setUser(null);
      router.push("/login");
    }
  }
  useEffect(() => { refreshUsr(); /* eslint-disable-next-line */ }, []);
  return <AppCtx.Provider value={{ user, refreshUsr }}>{children}</AppCtx.Provider>;
}

export function LogoutButton() {
  const router = useRouter();
  return (
    <button
      onClick={async () => {
        setToken(null);
        router.push("/login");
      }}
      className="rounded-md border border-ink-lightest px-3 py-1.5 text-sm text-ember hover:bg-ember/10 font-medium"
    >
      Sign out
    </button>
  );
}
