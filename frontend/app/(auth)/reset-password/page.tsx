"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";
import { Mail } from "lucide-react";

import { resetPasswordAuthResetPasswordPost } from "@/src/api/generated/auth/auth";
import { Button } from "@/shared/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/shared/components/ui/card";
import { Input } from "@/shared/components/ui/input";
import { Label } from "@/shared/components/ui/label";
import { hasSession } from "@/shared/lib/auth";

export default function ResetPasswordPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (hasSession()) {
      router.replace("/dashboard");
    }
  }, [router]);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setMessage(null);

    try {
      await resetPasswordAuthResetPasswordPost({
        email,
        redirect_to: `${window.location.origin}/update-password`,
      });
      setMessage("Password reset email sent.");
    } catch {
      setError("Failed to send password reset email");
    }
  }

  return (
    <main className="relative flex min-h-screen items-center justify-center overflow-hidden bg-[radial-gradient(circle_at_top,_#e2e8f0_0%,_#f8fafc_40%,_#ffffff_75%)] px-6 py-12">
      <Card className="w-full max-w-md">
        <CardHeader>
          <p className="mb-1 text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">MarketPulse</p>
          <CardTitle>Reset password</CardTitle>
          <CardDescription>We will email you a secure reset link.</CardDescription>
        </CardHeader>
        <CardContent>
          <form className="flex flex-col gap-3" onSubmit={onSubmit}>
            <Label htmlFor="email">Email</Label>
            <div className="relative">
              <Mail className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
              <Input id="email" type="email" placeholder="you@company.com" value={email} onChange={(event) => setEmail(event.target.value)} className="pl-9" required />
            </div>

            {error ? <p className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p> : null}
            {message ? <p className="rounded-md border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-700">{message}</p> : null}

            <Button type="submit" className="mt-1 h-11 rounded-lg">Send reset link</Button>
          </form>

          <Link href="/sign-in" className="mt-5 inline-block text-sm text-slate-600 hover:text-slate-900">Back to sign in</Link>
        </CardContent>
      </Card>
    </main>
  );
}
