"use client";

import type { Session } from "@supabase/supabase-js";

import { SupabaseBrowserClient } from "@/shared/lib/supabase";

const ACCESS_TOKEN_KEY = "mp_access_token";
const REFRESH_TOKEN_KEY = "mp_refresh_token";
const SESSION_EVENT_NAME = "marketpulse:session-changed";

export type SessionPayload = {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
};

function persistSession(session: SessionPayload): void {
  localStorage.setItem(ACCESS_TOKEN_KEY, session.access_token);
  localStorage.setItem(REFRESH_TOKEN_KEY, session.refresh_token);
  dispatchSessionEvent();
}

function dispatchSessionEvent(): void {
  if (typeof window === "undefined") {
    return;
  }

  window.dispatchEvent(new Event(SESSION_EVENT_NAME));
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

  saveSupabaseSession(data.session);
}

export function saveSupabaseSession(session: Session | null): void {
  if (!session?.access_token || !session.refresh_token) {
    clearStoredSession();
    return;
  }

  persistSession({
    access_token: session.access_token,
    refresh_token: session.refresh_token,
    token_type: session.token_type,
    expires_in: session.expires_in,
  });
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

    const {
      data: { session },
    } = await supabase.auth.getSession();
    saveSupabaseSession(session);

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
    clearStoredSession();
  }
}

export function clearStoredSession(): void {
  localStorage.removeItem(ACCESS_TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
  dispatchSessionEvent();
}

export function getAccessToken(): string | null {
  return localStorage.getItem(ACCESS_TOKEN_KEY);
}

export function getRefreshToken(): string | null {
  return localStorage.getItem(REFRESH_TOKEN_KEY);
}

export function hasSession(): boolean {
  return Boolean(getAccessToken());
}

export function getSessionEventName(): string {
  return SESSION_EVENT_NAME;
}
