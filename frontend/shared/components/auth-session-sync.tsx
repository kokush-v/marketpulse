"use client";

import { useEffect } from "react";

import { saveSupabaseSession } from "@/shared/lib/auth";
import { SupabaseBrowserClient } from "@/shared/lib/supabase";

export function AuthSessionSync() {
  useEffect(() => {
    const supabase = SupabaseBrowserClient.getInstance();

    void supabase.auth.getSession().then(({ data }) => {
      saveSupabaseSession(data.session);
    });

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, session) => {
      saveSupabaseSession(session);
    });

    return () => {
      subscription.unsubscribe();
    };
  }, []);

  return null;
}
