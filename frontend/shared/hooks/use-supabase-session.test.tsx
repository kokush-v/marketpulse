import { act, renderHook, waitFor } from "@testing-library/react";

import { useSupabaseSession } from "@/shared/hooks/use-supabase-session";

const mockClearLegacySessionStorage = jest.fn();
const mockGetCurrentSession = jest.fn();
const mockOnAuthStateChange = jest.fn();

jest.mock("@/shared/lib/auth", () => ({
  clearLegacySessionStorage: () => mockClearLegacySessionStorage(),
  getCurrentSession: () => mockGetCurrentSession(),
}));

jest.mock("@/shared/lib/supabase", () => ({
  SupabaseBrowserClient: {
    getInstance: () => ({
      auth: {
        onAuthStateChange: (...args: unknown[]) => mockOnAuthStateChange(...args),
      },
    }),
  },
}));

describe("useSupabaseSession", () => {
  let authStateChangeHandler: ((event: string, session: unknown) => void) | undefined;
  const unsubscribe = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    authStateChangeHandler = undefined;
    mockOnAuthStateChange.mockImplementation(
      (handler: (event: string, session: unknown) => void) => {
        authStateChangeHandler = handler;
        return {
          data: {
            subscription: { unsubscribe },
          },
        };
      },
    );
  });

  it("loads the initial Supabase session and cleans up its subscription", async () => {
    mockGetCurrentSession.mockResolvedValue({ access_token: "token" });

    const { result, unmount } = renderHook(() => useSupabaseSession());

    expect(result.current.isLoading).toBe(true);
    await waitFor(() => {
      expect(result.current.isAuthenticated).toBe(true);
    });
    expect(mockClearLegacySessionStorage).toHaveBeenCalledTimes(1);

    unmount();
    expect(unsubscribe).toHaveBeenCalledTimes(1);
  });

  it("updates when Supabase emits an auth-state change", async () => {
    mockGetCurrentSession.mockResolvedValue(null);

    const { result } = renderHook(() => useSupabaseSession());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });
    act(() => {
      authStateChangeHandler?.("SIGNED_IN", { access_token: "new-token" });
    });

    expect(result.current.isAuthenticated).toBe(true);
  });
});
