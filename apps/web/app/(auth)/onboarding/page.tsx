"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

export default function OnboardingPage() {
  const router = useRouter();
  const [step, setStep] = useState<"avatar" | "skills" | "done">("avatar");
  const [skills, setSkills] = useState("");

  async function submit() {
    await fetch("/api/quickstart", { method: "POST" });
    setStep("done");
  }

  return (
    <main className="flex min-h-screen items-center justify-center px-4">
      <div className="w-full max-w-md space-y-4">
        <h1 className="font-mono text-lg font-bold text-zinc-100">First, forge yourself.</h1>

        {step === "avatar" && (
          <div className="card space-y-3">
            <p className="text-sm text-zinc-400">Logo / avatar — optional but builds the shelf. You can add one later.</p>
            <button
              className="btn btn-primary w-full"
              onClick={() => {
                setStep("skills");
                router.push("/onboarding?skills=1");
              }}
            >
              Skip for now →
            </button>
          </div>
        )}

        {step === "skills" && (
          <div className="card space-y-3">
            <p className="text-sm text-zinc-400">
              Type the skills you actually use, comma-separated. The anvil will qualify jobs against them.
            </p>
            <input
              className="input"
              placeholder="Python, FastAPI, PostgreSQL, React"
              value={skills}
              onChange={(e) => setSkills(e.target.value)}
            />
            <button className="btn btn-primary w-full" onClick={submit}>
              Hammer them in →
            </button>
          </div>
        )}

        {step === "done" && (
          <div className="card space-y-3">
            <p className="text-sm text-zinc-300">
              The forge is lit. Never auto-apply: it&apos;s you who decides.
            </p>
            <button className="btn btn-primary w-full" onClick={() => router.push("/dashboard")}>
              Enter the forge →
            </button>
          </div>
        )}
      </div>
    </main>
  );
}
