"use client";

import type { Session } from "@supabase/supabase-js";

import { SupabaseBrowserClient } from "@/shared/lib/supabase";

const LEGACY_ACCESS_TOKEN_KEY = "mp_access_token";
const LEGACY_REFRESH_TOKEN_KEY = "mp_refresh_token";

export type SessionPayload = {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
};

export function clearLegacySessionStorage(): void {
  if (typeof window === "undefined") {
    return;
  }

  localStorage.removeItem(LEGACY_ACCESS_TOKEN_KEY);
  localStorage.removeItem(LEGACY_REFRESH_TOKEN_KEY);
}

export async function applySession(session: SessionPayload): Promise<void> {
  const supabase = SupabaseBrowserClient.getInstance();
  const { data, error } = await supabase.auth.setSession({
    access_token: session.access_token,
    refresh_token: session.refresh_token,
  });

  if (error) {
    throw error;
  }
  if (!data.session) {
    throw new Error("Supabase did not establish a session");
  }

  clearLegacySessionStorage();
}

export async function restoreRecoverySessionFromUrl(): Promise<boolean> {
  if (typeof window === "undefined") {
    return false;
  }

  const params = new URLSearchParams(window.location.search);
  const code = params.get("code");
  if (code) {
    const supabase = SupabaseBrowserClient.getInstance();
    const { error } = await supabase.auth.exchangeCodeForSession(code);
    if (error) {
      throw error;
    }

    clearLegacySessionStorage();

    window.history.replaceState({}, document.title, window.location.pathname);
    return true;
  }

  const hash = window.location.hash.startsWith("#")
    ? window.location.hash.slice(1)
    : window.location.hash;
  if (!hash) {
    return false;
  }

  const hashParams = new URLSearchParams(hash);
  const accessToken = hashParams.get("access_token");
  const refreshToken = hashParams.get("refresh_token");
  if (!accessToken || !refreshToken) {
    return false;
  }

  await applySession({
    access_token: accessToken,
    refresh_token: refreshToken,
    token_type: hashParams.get("token_type") ?? "bearer",
    expires_in: Number(hashParams.get("expires_in") ?? 3600),
  });

  const nextUrl = `${window.location.pathname}${window.location.search}`;
  window.history.replaceState({}, document.title, nextUrl);
  return true;
}

export async function clearSession(): Promise<void> {
  const supabase = SupabaseBrowserClient.getInstance();
  try {
    await supabase.auth.signOut();
  } finally {
    clearLegacySessionStorage();
  }
}

export async function getCurrentSession(): Promise<Session | null> {
  const supabase = SupabaseBrowserClient.getInstance();
  const {
    data: { session },
    error,
  } = await supabase.auth.getSession();

  if (error) {
    return null;
  }

  return session;
}

export async function getAccessToken(): Promise<string | null> {
  return (await getCurrentSession())?.access_token ?? null;
}

export async function hasSession(): Promise<boolean> {
  return Boolean(await getCurrentSession());
}
