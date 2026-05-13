type OrvalRequest = {
  url: string;
  method?: string;
  signal?: AbortSignal;
};

export async function customFetch<T>(
  request: string | OrvalRequest,
  options?: RequestInit
): Promise<T> {
  const resolvedUrl = typeof request === "string" ? request : request.url;
  const resolvedMethod =
    typeof request === "string" ? options?.method : (request.method ?? options?.method);
  const resolvedSignal = typeof request === "string" ? options?.signal : request.signal;

  const response = await fetch(resolvedUrl, {
    ...options,
    method: resolvedMethod,
    signal: resolvedSignal,
    headers: {
      "Content-Type": "application/json",
      ...(options?.headers ?? {}),
    },
  });

  if (!response.ok) {
    throw new Error(`Request failed with status ${response.status}`);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}
