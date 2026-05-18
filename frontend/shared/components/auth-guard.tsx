"use client";

import { useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";

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
    return <main className="mx-auto flex min-h-screen max-w-3xl items-center px-6">Checking session...</main>;
  }

  return <>{children}</>;
}
