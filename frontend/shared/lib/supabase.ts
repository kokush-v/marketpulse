"use client";

import { createClient, type SupabaseClient } from "@supabase/supabase-js";

export class SupabaseBrowserClient {
  private static instance: SupabaseClient | null = null;

  static getInstance(): SupabaseClient {
    if (SupabaseBrowserClient.instance) {
      return SupabaseBrowserClient.instance;
    }

    const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
    const supabasePublishableKey = process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY;

    if (!supabaseUrl || !supabasePublishableKey) {
      throw new Error("Supabase environment variables are not configured");
    }

    SupabaseBrowserClient.instance = createClient(supabaseUrl, supabasePublishableKey, {
      auth: {
        detectSessionInUrl: false,
        flowType: "pkce",
      },
    });

    return SupabaseBrowserClient.instance;
  }
}
