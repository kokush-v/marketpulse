"use client";

import { useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";

import { getAccessToken } from "@/shared/lib/auth";

export function AuthGuard({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const [isChecking, setIsChecking] = useState(true);

  useEffect(() => {
    const token = getAccessToken();
    if (!token) {
      router.replace(`/sign-in?next=${encodeURIComponent(pathname)}`);
      return;
    }
    setIsChecking(false);
  }, [pathname, router]);

  if (isChecking) {
    return <main className="mx-auto flex min-h-screen max-w-3xl items-center px-6">Checking session...</main>;
  }

  return <>{children}</>;
}
