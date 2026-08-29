import type { Session } from "@supabase/supabase-js";

import { clearSession, getCurrentSession } from "@/shared/lib/auth";
import { SupabaseBrowserClient } from "@/shared/lib/supabase";

type OrvalRequest = {
  url: string;
  method?: string;
  signal?: AbortSignal;
  headers?: HeadersInit;
  data?: unknown;
  params?: Record<string, unknown>;
};

type ApiErrorPayload = {
  code?: string;
  message?: string;
  retryable?: boolean;
  retry_after_seconds?: number;
  detail?: string | { message?: string };
};

export class ApiRequestError extends Error {
  constructor(
    message: string,
    public readonly status: number,
    public readonly code?: string,
    public readonly retryable = false,
    public readonly retryAfterSeconds?: number,
  ) {
    super(message);
    this.name = "ApiRequestError";
  }
}

let refreshSessionPromise: Promise<Session | null> | null = null;
let clearSessionPromise: Promise<void> | null = null;

async function refreshSession(): Promise<Session | null> {
  if (!refreshSessionPromise) {
    const supabase = SupabaseBrowserClient.getInstance();
    refreshSessionPromise = supabase.auth
      .refreshSession()
      .then(({ data, error }) => (error ? null : data.session))
      .catch(() => null)
      .finally(() => {
        refreshSessionPromise = null;
      });
  }

  return refreshSessionPromise;
}

async function transitionToSignIn(): Promise<void> {
  clearSessionPromise ??= clearSession().catch(() => undefined);
  const pendingClear = clearSessionPromise;
  await pendingClear;
  if (clearSessionPromise === pendingClear) {
    clearSessionPromise = null;
  }

  if (window.location.pathname !== "/sign-in") {
    window.location.href = "/sign-in";
  }
}

function resolveApiUrl(url: string): string {
  if (/^https?:\/\//i.test(url)) {
    return url;
  }

  const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL;
  if (!baseUrl) {
    return url;
  }

  const normalizedBase = baseUrl.replace(/\/+$/, "");
  const normalizedPath = url.startsWith("/") ? url : `/${url}`;
  return `${normalizedBase}${normalizedPath}`;
}

function appendQueryParams(url: string, params?: Record<string, unknown>): string {
  if (!params) {
    return url;
  }

  const target = new URL(url, "http://localhost");
  for (const [key, value] of Object.entries(params)) {
    if (value === undefined || value === null) {
      continue;
    }

    if (Array.isArray(value)) {
      for (const item of value) {
        target.searchParams.append(key, String(item));
      }
      continue;
    }

    target.searchParams.set(key, String(value));
  }

  if (/^https?:\/\//i.test(url)) {
    return target.toString();
  }

  return `${target.pathname}${target.search}`;
}

function toDefinedHeaderEntries(headers?: HeadersInit): [string, string][] {
  if (!headers) {
    return [];
  }

  const normalized = new Headers(headers);
  return Array.from(normalized.entries()).filter(([, value]) => value !== "undefined");
}

export async function customFetch<T>(
  request: string | OrvalRequest,
  options?: RequestInit
): Promise<T> {
  const resolvedUrl = typeof request === "string" ? request : request.url;
  const resolvedMethod =
    typeof request === "string" ? options?.method : request.method ?? options?.method;
  const resolvedSignal = typeof request === "string" ? options?.signal : request.signal;
  const requestHeaders = typeof request === "string" ? undefined : request.headers;
  const requestBody =
    typeof request === "string" ? options?.body : request.data !== undefined ? JSON.stringify(request.data) : options?.body;
  const resolvedParams = typeof request === "string" ? undefined : request.params;
  const targetUrl = appendQueryParams(resolveApiUrl(resolvedUrl), resolvedParams);
  const isBrowser = typeof window !== "undefined";
  const session = isBrowser ? await getCurrentSession() : null;

  const sendRequest = (accessToken: string | null): Promise<Response> => {
    const headers = new Headers({
      "Content-Type": "application/json",
    });

    for (const [key, value] of toDefinedHeaderEntries(requestHeaders)) {
      headers.set(key, value);
    }

    for (const [key, value] of toDefinedHeaderEntries(options?.headers)) {
      headers.set(key, value);
    }

    if (accessToken) {
      headers.set("Authorization", `Bearer ${accessToken}`);
    }

    return fetch(targetUrl, {
      ...options,
      method: resolvedMethod,
      signal: resolvedSignal,
      body: requestBody,
      headers,
    });
  };

  let response = await sendRequest(session?.access_token ?? null);

  if (response.status === 401 && isBrowser && session) {
    const refreshedSession = await refreshSession();
    if (refreshedSession?.access_token) {
      response = await sendRequest(refreshedSession.access_token);
    }

    if (!refreshedSession?.access_token || response.status === 401) {
      await transitionToSignIn();
    }
  }

  if (!response.ok) {
    let message = `Request failed with status ${response.status}`;
    let payload: ApiErrorPayload | undefined;
    try {
      payload = (await response.json()) as ApiErrorPayload | undefined;

      if (payload?.message) {
        message = payload.message;
      } else if (typeof payload?.detail === "string") {
        message = payload.detail;
      } else if (payload?.detail && typeof payload.detail === "object" && payload.detail.message) {
        message = payload.detail.message;
      }
    } catch {
      // Keep the default status-based error message when the payload is not JSON.
    }

    throw new ApiRequestError(
      message,
      response.status,
      payload?.code,
      payload?.retryable ?? false,
      payload?.retry_after_seconds,
    );
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}
