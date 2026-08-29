"use client";

import { useEffect, useState } from "react";

import type { Session } from "@supabase/supabase-js";

import { clearLegacySessionStorage, getCurrentSession } from "@/shared/lib/auth";
import { SupabaseBrowserClient } from "@/shared/lib/supabase";

type SupabaseSessionState = {
  session: Session | null;
  isAuthenticated: boolean;
  isLoading: boolean;
};

export function useSupabaseSession(): SupabaseSessionState {
  const [session, setSession] = useState<Session | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let active = true;
    let receivedAuthEvent = false;

    clearLegacySessionStorage();

    const supabase = SupabaseBrowserClient.getInstance();
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, nextSession) => {
      receivedAuthEvent = true;
      if (active) {
        setSession(nextSession);
        setIsLoading(false);
      }
    });

    void getCurrentSession().then((initialSession) => {
      if (active && !receivedAuthEvent) {
        setSession(initialSession);
        setIsLoading(false);
      }
    });

    return () => {
      active = false;
      subscription.unsubscribe();
    };
  }, []);

  return {
    session,
    isAuthenticated: Boolean(session?.access_token),
    isLoading,
  };
}
