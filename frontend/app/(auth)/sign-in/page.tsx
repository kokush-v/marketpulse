"use client";

import { Suspense } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";
import { LockKeyhole, Mail } from "lucide-react";
import { FcGoogle } from "react-icons/fc";

import { signInAuthSignInPost } from "@/src/api/generated/auth/auth";
import { Button } from "@/shared/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/shared/components/ui/card";
import { Input } from "@/shared/components/ui/input";
import { Label } from "@/shared/components/ui/label";
import { Separator } from "@/shared/components/ui/separator";
import { applySession, hasSession } from "@/shared/lib/auth";
import { SupabaseBrowserClient } from "@/shared/lib/supabase";

function SignInPageContent() {
	const router = useRouter();
	const searchParams = useSearchParams();
	const next = searchParams.get("next") || "/dashboard";
	const [email, setEmail] = useState("");
	const [password, setPassword] = useState("");
	const [error, setError] = useState<string | null>(null);
	const [loading, setLoading] = useState(false);

	useEffect(() => {
		if (hasSession()) {
			router.replace(next);
		}
	}, [next, router]);

	async function onSubmit(event: FormEvent<HTMLFormElement>) {
		event.preventDefault();
		setLoading(true);
		setError(null);

		try {
			const session = await signInAuthSignInPost({ email, password });
			if (!session.access_token || !session.refresh_token || !session.token_type || !session.expires_in) {
				throw new Error("Sign in response did not include a usable session");
			}
			await applySession({
				access_token: session.access_token,
				refresh_token: session.refresh_token,
				token_type: session.token_type,
				expires_in: session.expires_in,
			});
			router.replace(next);
		} catch {
			setError("Sign in failed");
		} finally {
			setLoading(false);
		}
	}

	async function onGoogleSignIn() {
		setError(null);
		try {
			const supabase = SupabaseBrowserClient.getInstance();
			const callbackUrl = new URL("/auth/callback", window.location.origin);
			callbackUrl.searchParams.set("next", next);

			const { error } = await supabase.auth.signInWithOAuth({
				provider: "google",
				options: {
					redirectTo: callbackUrl.toString(),
				},
			});

			if (error) {
				throw error;
			}
		} catch {
			setError("Google sign in failed");
		}
	}

	return (
		<main className="relative flex min-h-screen items-center justify-center overflow-hidden bg-gradient-to-b from-background via-background to-background/80 px-6 py-12">
			<Card className="w-full max-w-md border-border/30">
				<CardHeader>
					<p className="mb-1 text-xs font-semibold uppercase tracking-[0.22em] text-muted-foreground/70">
						MarketPulse
					</p>
					<CardTitle>Sign in to your account</CardTitle>
					<CardDescription>Track markets, alerts, and watchlists in one place.</CardDescription>
				</CardHeader>
				<CardContent>
					<form className="flex flex-col gap-3" onSubmit={onSubmit}>
						<Label htmlFor="email">Email</Label>
						<div className="relative">
							<Mail className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
							<Input
								id="email"
								type="email"
								placeholder="you@company.com"
								value={email}
								onChange={(event) => setEmail(event.target.value)}
								className="pl-9"
								required
							/>
						</div>

						<Label className="mt-1" htmlFor="password">
							Password
						</Label>
						<div className="relative">
							<LockKeyhole className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
							<Input
								id="password"
								type="password"
								placeholder="••••••••"
								value={password}
								onChange={(event) => setPassword(event.target.value)}
								className="pl-9"
								required
							/>
						</div>

						{error ? (
							<p className="rounded-lg border border-destructive/30 bg-destructive/10 px-3 py-2 text-sm text-destructive/80">
								{error}
							</p>
						) : null}

						<Button type="submit" disabled={loading} className="mt-1 h-11 rounded-lg">
							{loading ? "Signing in..." : "Sign In"}
						</Button>
					</form>

					<div className="my-4 flex items-center gap-3 text-xs text-slate-400">
						<Separator className="flex-1" />
						<span>OR</span>
						<Separator className="flex-1" />
					</div>

					<Button
						type="button"
						variant="outline"
						onClick={onGoogleSignIn}
						className="h-11 w-full gap-2 rounded-lg border-border/30">
						<FcGoogle className="h-4 w-4" />
						Continue with Google
					</Button>

					<div className="mt-5 flex flex-wrap gap-4 text-sm text-slate-600">
						<Link href="/sign-up" className="hover:text-slate-900">
							Create account
						</Link>
						<Link href="/reset-password" className="hover:text-slate-900">
							Forgot password?
						</Link>
					</div>
				</CardContent>
			</Card>
		</main>
	);
}

export default function SignInPage() {
	return (
		<Suspense
			fallback={<main className="mx-auto flex min-h-screen max-w-3xl items-center px-6">Loading sign in...</main>}>
			<SignInPageContent />
		</Suspense>
	);
}
