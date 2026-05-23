"use client";

import { useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";

import { Spinner } from "@/shared/components/ui/spinner";
import { getAccessToken, getSessionEventName } from "@/shared/lib/auth";
import { SupabaseBrowserClient } from "@/shared/lib/supabase";

export function AuthGuard({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const [isChecking, setIsChecking] = useState(true);

  useEffect(() => {
    const redirectToSignIn = () => {
      router.replace(`/sign-in?next=${encodeURIComponent(pathname)}`);
    };

    const evaluateSession = () => {
      const token = getAccessToken();
      if (!token) {
        setIsChecking(true);
        redirectToSignIn();
        return;
      }

      setIsChecking(false);
    };

    evaluateSession();

    const supabase = SupabaseBrowserClient.getInstance();
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, session) => {
      if (!session?.access_token) {
        setIsChecking(true);
        redirectToSignIn();
        return;
      }

      setIsChecking(false);
    });

    const handleStorage = (event: StorageEvent) => {
      if (event.key === null || event.key.startsWith("mp_")) {
        evaluateSession();
      }
    };
    const handleSessionEvent = () => {
      evaluateSession();
    };

    window.addEventListener("storage", handleStorage);
    window.addEventListener(getSessionEventName(), handleSessionEvent);

    return () => {
      subscription.unsubscribe();
      window.removeEventListener("storage", handleStorage);
      window.removeEventListener(getSessionEventName(), handleSessionEvent);
    };
  }, [pathname, router]);

  if (isChecking) {
    return (
      <main className="flex min-h-screen w-full items-center justify-center bg-background px-6">
        <div className="flex w-full max-w-sm flex-col items-center justify-center text-center">
          <div className="flex size-14 items-center justify-center rounded-full border border-border/50 bg-muted/30">
            <Spinner className="size-6 text-muted-foreground" />
          </div>
          <div className="mt-5 space-y-2">
            <h2 className="text-base font-semibold tracking-tight text-foreground">Checking your session</h2>
            <p className="text-sm leading-6 text-muted-foreground">
              Getting your workspace ready...
            </p>
          </div>
        </div>
      </main>
    );
  }

  return <>{children}</>;
}
