"use client";

import { useRouter } from "next/navigation";

import { Button } from "@/shared/components/ui/button";
import { clearSession } from "@/shared/lib/auth";

export default function DashboardPage() {
  const router = useRouter();

  async function onSignOut() {
    await clearSession();
    router.replace("/sign-in");
  }

  return (
    <main className="mx-auto flex min-h-screen max-w-3xl flex-col justify-center gap-4 px-6">
      <h1 className="text-2xl font-semibold">Dashboard</h1>
      <p className="text-slate-600">You are authenticated.</p>
      <Button onClick={onSignOut}>Sign Out</Button>
    </main>
  );
}
