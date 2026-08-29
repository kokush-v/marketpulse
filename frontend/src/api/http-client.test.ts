import { customFetch } from "@/src/api/http-client";

const mockClearSession = jest.fn();
const mockGetCurrentSession = jest.fn();
const mockRefreshSession = jest.fn();

jest.mock("@/shared/lib/auth", () => ({
  clearSession: () => mockClearSession(),
  getCurrentSession: () => mockGetCurrentSession(),
}));

jest.mock("@/shared/lib/supabase", () => ({
  SupabaseBrowserClient: {
    getInstance: () => ({
      auth: {
        refreshSession: () => mockRefreshSession(),
      },
    }),
  },
}));

function response(status: number, payload: unknown = { ok: true }): Response {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: jest.fn().mockResolvedValue(payload),
  } as unknown as Response;
}

function authorizationHeader(call: unknown[]): string | null {
  const options = call[1] as RequestInit;
  return new Headers(options.headers).get("Authorization");
}

describe("customFetch authentication recovery", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    window.history.replaceState({}, "", "/sign-in");
    mockClearSession.mockResolvedValue(undefined);
    mockGetCurrentSession.mockResolvedValue({ access_token: "expired-token" });
  });

  it("refreshes a rejected Supabase session and retries once", async () => {
    const fetchMock = jest
      .fn()
      .mockResolvedValueOnce(response(401, { detail: "Expired token" }))
      .mockResolvedValueOnce(response(200, { value: "recovered" }));
    global.fetch = fetchMock;
    mockRefreshSession.mockResolvedValue({
      data: { session: { access_token: "fresh-token" } },
      error: null,
    });

    await expect(customFetch<{ value: string }>("/auth/me")).resolves.toEqual({
      value: "recovered",
    });

    expect(fetchMock).toHaveBeenCalledTimes(2);
    expect(authorizationHeader(fetchMock.mock.calls[0])).toBe("Bearer expired-token");
    expect(authorizationHeader(fetchMock.mock.calls[1])).toBe("Bearer fresh-token");
    expect(mockClearSession).not.toHaveBeenCalled();
  });

  it("clears the session when Supabase cannot refresh it", async () => {
    global.fetch = jest.fn().mockResolvedValue(response(401, { detail: "Expired token" }));
    mockRefreshSession.mockResolvedValue({
      data: { session: null },
      error: new Error("Refresh failed"),
    });

    await expect(customFetch("/auth/me")).rejects.toMatchObject({ status: 401 });

    expect(mockRefreshSession).toHaveBeenCalledTimes(1);
    expect(mockClearSession).toHaveBeenCalledTimes(1);
  });

  it("does not retry again when the refreshed request remains unauthorized", async () => {
    const fetchMock = jest.fn().mockResolvedValue(response(401, { detail: "Unauthorized" }));
    global.fetch = fetchMock;
    mockRefreshSession.mockResolvedValue({
      data: { session: { access_token: "fresh-token" } },
      error: null,
    });

    await expect(customFetch("/auth/me")).rejects.toMatchObject({ status: 401 });

    expect(fetchMock).toHaveBeenCalledTimes(2);
    expect(mockRefreshSession).toHaveBeenCalledTimes(1);
    expect(mockClearSession).toHaveBeenCalledTimes(1);
  });

  it("shares one in-flight refresh across concurrent unauthorized requests", async () => {
    let resolveRefresh: ((value: unknown) => void) | undefined;
    mockRefreshSession.mockReturnValue(
      new Promise((resolve) => {
        resolveRefresh = resolve;
      }),
    );
    const fetchMock = jest.fn().mockImplementation((_url: string, options: RequestInit) => {
      const token = new Headers(options.headers).get("Authorization");
      return Promise.resolve(
        token === "Bearer fresh-token"
          ? response(200, { recovered: true })
          : response(401, { detail: "Expired token" }),
      );
    });
    global.fetch = fetchMock;

    const firstRequest = customFetch("/auth/me");
    const secondRequest = customFetch("/assistant/conversations");

    await Promise.resolve();
    await Promise.resolve();
    expect(mockRefreshSession).toHaveBeenCalledTimes(1);

    resolveRefresh?.({
      data: { session: { access_token: "fresh-token" } },
      error: null,
    });

    await expect(Promise.all([firstRequest, secondRequest])).resolves.toEqual([
      { recovered: true },
      { recovered: true },
    ]);
    expect(mockRefreshSession).toHaveBeenCalledTimes(1);
    expect(mockClearSession).not.toHaveBeenCalled();
  });
});
