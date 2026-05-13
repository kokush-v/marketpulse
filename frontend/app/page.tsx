import Link from "next/link";

import { Button } from "@/shared/components/ui/button";

export default function HomePage() {
  return (
    <main className="mx-auto flex min-h-screen max-w-3xl flex-col items-start justify-center gap-6 px-6">
      <h1 className="text-3xl font-semibold">MarketPulse Foundation Ready</h1>
      <p className="text-slate-600">
        Frontend baseline is initialized with App Router, Tailwind, shadcn, TanStack Query, and Orval.
      </p>
      <div className="flex gap-3">
        <Button asChild>
          <Link href="/sign-in">Open Sign In</Link>
        </Button>
        <Button variant="outline" asChild>
          <Link href="/dashboard">Open Dashboard</Link>
        </Button>
      </div>
    </main>
  );
}
