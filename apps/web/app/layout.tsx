import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: {
    default: "JOBFORGE — Find. Qualify. Apply. Advance.",
    template: "%s · JOBFORGE",
  },
  description:
    "An open, free-first, human-in-the-loop career operating system by Sifuna Codex. Discover jobs, qualify by real skills, apply deliberately, advance toward a financial goal.",
  applicationName: "JOBFORGE",
  authors: [{ name: "Sifuna Codex" }],
  openGraph: {
    title: "JOBFORGE — Find. Qualify. Apply. Advance.",
    description: "Human-in-the-loop career advancement. No fake applications, ever.",
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" data-theme="dark">
      <body className="min-h-screen bg-ink text-zinc-200 antialiased">{children}</body>
    </html>
  );
}
