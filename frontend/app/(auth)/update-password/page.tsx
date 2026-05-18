"use client";

import { useRouter } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";
import { LockKeyhole } from "lucide-react";

import { updatePasswordAuthUpdatePasswordPost } from "@/src/api/generated/auth/auth";
import { Button } from "@/shared/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/shared/components/ui/card";
import { Input } from "@/shared/components/ui/input";
import { Label } from "@/shared/components/ui/label";
import {
  clearSession,
  getAccessToken,
  getRefreshToken,
  restoreRecoverySessionFromUrl,
} from "@/shared/lib/auth";

export default function UpdatePasswordPage() {
  const router = useRouter();
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isHydrating, setIsHydrating] = useState(true);

  useEffect(() => {
    let cancelled = false;

    async function hydrateRecoverySession() {
      try {
        await restoreRecoverySessionFromUrl();
      } catch {
        if (!cancelled) {
          setError("Failed to restore reset session");
        }
      } finally {
        if (!cancelled) {
          setIsHydrating(false);
        }
      }
    }

    void hydrateRecoverySession();

    return () => {
      cancelled = true;
    };
  }, []);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setMessage(null);

    const accessToken = getAccessToken();
    const refreshToken = getRefreshToken();
    if (!accessToken || !refreshToken) {
      setError("Missing active session");
      return;
    }

    try {
      await updatePasswordAuthUpdatePasswordPost(
        { password },
        {
          headers: {
            Authorization: `Bearer ${accessToken}`,
            "X-Refresh-Token": refreshToken,
          },
        }
      );
      await clearSession();
      router.replace("/sign-in");
    } catch {
      setError("Failed to update password");
    }
  }

  return (
    <main className="relative flex min-h-screen items-center justify-center overflow-hidden bg-[radial-gradient(circle_at_top,_#e2e8f0_0%,_#f8fafc_40%,_#ffffff_75%)] px-6 py-12">
      <Card className="w-full max-w-md">
        <CardHeader>
          <p className="mb-1 text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">MarketPulse</p>
          <CardTitle>Set new password</CardTitle>
          <CardDescription>Choose a strong new password for your account.</CardDescription>
        </CardHeader>
        <CardContent>
          {isHydrating ? (
            <p className="mb-4 rounded-md border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-700">
              Restoring your reset session...
            </p>
          ) : null}
          <form className="flex flex-col gap-3" onSubmit={onSubmit}>
            <Label htmlFor="password">New password</Label>
            <div className="relative">
              <LockKeyhole className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
              <Input id="password" type="password" placeholder="At least 8 symbols" value={password} onChange={(event) => setPassword(event.target.value)} className="pl-9" required />
            </div>

            {error ? <p className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p> : null}
            {message ? <p className="rounded-md border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-700">{message}</p> : null}

            <Button type="submit" className="mt-1 h-11 rounded-lg" disabled={isHydrating}>
              {isHydrating ? "Preparing..." : "Update password"}
            </Button>
          </form>
        </CardContent>
      </Card>
    </main>
  );
}
