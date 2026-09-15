import Link from "next/link";

export default function NotFound() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-3 bg-ink text-zinc-100">
      <p className="font-mono text-6xl font-black text-zinc-700">404</p>
      <h1 className="text-xl font-semibold">This page went AWOL.</h1>
      <p className="text-sm text-zinc-400">Like an unresponsive recruiter, here it is not.</p>
      <Link href="/" className="mt-2 rounded-lg bg-accent px-4 py-2 text-sm font-medium text-white hover:bg-accent-soft">
        Back to the Forge
      </Link>
    </main>
  );
}
