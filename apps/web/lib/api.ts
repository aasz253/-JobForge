const BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface ApiOptions {
  token?: string;
  method?: string;
  body?: unknown;
  tokenType?: "Bearer" | "OAuth";
  externalOAuth?: boolean;
}

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

function detailOf(d: unknown): string {
  if (typeof d === "string") return d;
  if (d && typeof d === "object") {
    const o = d as Record<string, unknown>;
    if (typeof o.detail === "string") return o.detail;
    if (Array.isArray(o.detail)) {
      return (o.detail as unknown[])
        .map((x: unknown) => {
          if (typeof x === "string") return x;
          const item = x as Record<string, unknown>;
          const msg = typeof item.msg === "string" ? item.msg : "";
          if (msg && !Array.isArray(item.loc)) return msg;
          const loc = Array.isArray(item.loc) ? (item.loc as (string | number)[]).slice(1).join(".") : "";
          return loc ? `${loc}: ${msg}` : msg;
        })
        .filter(Boolean)
        .join("; ");
    }
  }
  return String(d);
}

let _token: string | null = null;
function token(): string {
  if (_token) return _token;
  if (typeof window === "undefined") return "";
  try {
    return localStorage.getItem("jobforge_token") || "";
  } catch {
    return "";
  }
}

export function setToken(t: string | null) {
  _token = t;
  if (typeof window === "undefined") return;
  try {
    if (t) localStorage.setItem("jobforge_token", t);
    else localStorage.removeItem("jobforge_token");
  } catch {
    /* storage unavailable */
  }
}

export function getToken(): string {
  return token();
}

export async function api<T = unknown>(path: string, opts: ApiOptions = {}): Promise<T> {
  const method = opts.method || "GET";
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  const t = opts.token || token();
  if (t) headers.Authorization = `Bearer ${t}`;
  const res = await fetch(`${BASE}${path}`, {
    method,
    headers,
    body: opts.body !== undefined ? JSON.stringify(opts.body) : undefined,
    cache: "no-store",
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      detail = detailOf(await res.json());
    } catch {
      /* keep status text */
    }
    throw new ApiError(res.status, detail || res.statusText);
  }
  if (res.status === 204 || res.status === 205) return undefined as T;
  const text = await res.text();
  return (text ? JSON.parse(text) : undefined) as T;
}
