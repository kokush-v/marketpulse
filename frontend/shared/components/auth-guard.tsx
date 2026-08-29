"use client";

import { useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";

import { Spinner } from "@/shared/components/ui/spinner";
import { useSupabaseSession } from "@/shared/hooks/use-supabase-session";

export function AuthGuard({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const { isAuthenticated, isLoading } = useSupabaseSession();

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.replace(`/sign-in?next=${encodeURIComponent(pathname)}`);
    }
  }, [isAuthenticated, isLoading, pathname, router]);

  if (isLoading || !isAuthenticated) {
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
