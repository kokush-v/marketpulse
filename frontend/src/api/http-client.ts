import { clearSession, getAccessToken } from "@/shared/lib/auth";

type OrvalRequest = {
  url: string;
  method?: string;
  signal?: AbortSignal;
  headers?: HeadersInit;
  data?: unknown;
  params?: Record<string, unknown>;
};

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
  const accessToken = typeof window !== "undefined" ? getAccessToken() : null;
  const headers = new Headers({
    "Content-Type": "application/json",
  });

  if (accessToken) {
    headers.set("Authorization", `Bearer ${accessToken}`);
  }

  for (const [key, value] of toDefinedHeaderEntries(requestHeaders)) {
    headers.set(key, value);
  }

  for (const [key, value] of toDefinedHeaderEntries(options?.headers)) {
    headers.set(key, value);
  }

  const response = await fetch(targetUrl, {
    ...options,
    method: resolvedMethod,
    signal: resolvedSignal,
    body: requestBody,
    headers,
  });

  if (!response.ok) {
    if (response.status === 401 && typeof window !== "undefined") {
      await clearSession();
      window.location.href = "/sign-in";
    }

    let message = `Request failed with status ${response.status}`;
    try {
      const payload = (await response.json()) as
        | { message?: string; detail?: string | { message?: string } }
        | undefined;

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

    throw new Error(message);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}
