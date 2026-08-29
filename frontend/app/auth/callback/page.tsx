"use client";

import { Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";

import { syncUserAuthSyncUserPost } from "@/src/api/generated/auth/auth";
import { SupabaseBrowserClient } from "@/shared/lib/supabase";

function AuthCallbackPageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const next = searchParams.get("next") || "/dashboard";
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function completeGoogleAuth() {
      const code = searchParams.get("code");
      if (!code) {
        setError("Missing OAuth code");
        return;
      }

      try {
        const supabase = SupabaseBrowserClient.getInstance();
        const { error: exchangeError } = await supabase.auth.exchangeCodeForSession(code);
        if (exchangeError) {
          throw exchangeError;
        }

        const {
          data: { session },
        } = await supabase.auth.getSession();

        if (!session?.access_token) {
          throw new Error("Supabase session was not created");
        }

        await syncUserAuthSyncUserPost({
          headers: {
            Authorization: `Bearer ${session.access_token}`,
          },
        });

        if (!cancelled) {
          router.replace(next.startsWith("/") ? next : "/dashboard");
        }
      } catch {
        if (!cancelled) {
          setError("Google sign in failed");
        }
      }
    }

    void completeGoogleAuth();

    return () => {
      cancelled = true;
    };
  }, [next, router, searchParams]);

  return (
    <main className="mx-auto flex min-h-screen max-w-3xl flex-col items-center justify-center gap-3 px-6 text-center">
      <h1 className="text-2xl font-semibold">Finalizing sign in</h1>
      <p className="text-slate-600">
        {error ?? "We are confirming your Google session and preparing your workspace."}
      </p>
    </main>
  );
}

export default function AuthCallbackPage() {
  return (
    <Suspense
      fallback={
        <main className="mx-auto flex min-h-screen max-w-3xl flex-col items-center justify-center gap-3 px-6 text-center">
          <h1 className="text-2xl font-semibold">Finalizing sign in</h1>
          <p className="text-slate-600">
            We are confirming your Google session and preparing your workspace.
          </p>
        </main>
      }
    >
      <AuthCallbackPageContent />
    </Suspense>
  );
}
