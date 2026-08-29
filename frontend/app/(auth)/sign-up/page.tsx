"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";
import { LockKeyhole, Mail } from "lucide-react";
import { FcGoogle } from "react-icons/fc";

import { signUpAuthSignUpPost } from "@/src/api/generated/auth/auth";
import { Button } from "@/shared/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/shared/components/ui/card";
import { Input } from "@/shared/components/ui/input";
import { Label } from "@/shared/components/ui/label";
import { Separator } from "@/shared/components/ui/separator";
import { applySession } from "@/shared/lib/auth";
import { useSupabaseSession } from "@/shared/hooks/use-supabase-session";
import { SupabaseBrowserClient } from "@/shared/lib/supabase";

export default function SignUpPage() {
	const router = useRouter();
	const [email, setEmail] = useState("");
	const [password, setPassword] = useState("");
	const [message, setMessage] = useState<string | null>(null);
	const [error, setError] = useState<string | null>(null);
	const { isAuthenticated } = useSupabaseSession();

	useEffect(() => {
		if (isAuthenticated) {
			router.replace("/dashboard");
		}
	}, [isAuthenticated, router]);

	async function onSubmit(event: FormEvent<HTMLFormElement>) {
		event.preventDefault();
		setError(null);
		setMessage(null);

		try {
			const session = await signUpAuthSignUpPost({ email, password });
			if (session.access_token && session.refresh_token && session.token_type && session.expires_in) {
				await applySession({
					access_token: session.access_token,
					refresh_token: session.refresh_token,
					token_type: session.token_type,
					expires_in: session.expires_in,
				});
				router.replace("/dashboard");
				return;
			}

			if (session.requires_email_verification) {
				setMessage("Account created. Check your inbox to verify your email before signing in.");
				return;
			}

			setError("Sign up completed without a usable session");
		} catch {
			setError("Sign up failed");
		}
	}

	async function onGoogleSignIn() {
		setError(null);
		try {
			const supabase = SupabaseBrowserClient.getInstance();
			const { error } = await supabase.auth.signInWithOAuth({
				provider: "google",
				options: {
					redirectTo: `${window.location.origin}/auth/callback?next=${encodeURIComponent("/dashboard")}`,
				},
			});

			if (error) {
				throw error;
			}
		} catch {
			setError("Google sign up failed");
		}
	}

	return (
		<main className="relative flex min-h-screen items-center justify-center overflow-hidden bg-gradient-to-b from-background via-background to-background/80 px-6 py-12">
			<Card className="w-full max-w-md border-border/30">
				<CardHeader>
					<p className="mb-1 text-xs font-semibold uppercase tracking-[0.22em] text-muted-foreground/70">
						MarketPulse
					</p>
					<CardTitle>Create your account</CardTitle>
					<CardDescription>Start tracking your own market workspace.</CardDescription>
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
								placeholder="At least 8 symbols"
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
						{message ? (
							<p className="rounded-lg border border-emerald-500/30 bg-emerald-500/10 px-3 py-2 text-sm text-emerald-600 dark:text-emerald-400">
								{message}
							</p>
						) : null}

						<Button type="submit" className="mt-1 h-11 rounded-lg">
							Sign Up
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
						className="h-11 w-full gap-2 rounded-lg border-slate-300">
						<FcGoogle className="h-4 w-4" />
						Continue with Google
					</Button>

					<Link href="/sign-in" className="mt-5 inline-block text-sm text-slate-600 hover:text-slate-900">
						Already have an account?
					</Link>
				</CardContent>
			</Card>
		</main>
	);
}
