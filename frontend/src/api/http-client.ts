import { clearSession, getAccessToken } from "@/shared/lib/auth";

type OrvalRequest = {
  url: string;
  method?: string;
  signal?: AbortSignal;
  headers?: HeadersInit;
  data?: unknown;
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
  const targetUrl = resolveApiUrl(resolvedUrl);
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
    throw new Error(`Request failed with status ${response.status}`);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}
