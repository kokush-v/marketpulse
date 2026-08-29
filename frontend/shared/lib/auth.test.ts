import {
  applySession,
  clearLegacySessionStorage,
  clearSession,
  getAccessToken,
  hasSession,
} from "@/shared/lib/auth";

const mockGetSession = jest.fn();
const mockSetSession = jest.fn();
const mockSignOut = jest.fn();

jest.mock("@/shared/lib/supabase", () => ({
  SupabaseBrowserClient: {
    getInstance: () => ({
      auth: {
        getSession: (...args: unknown[]) => mockGetSession(...args),
        setSession: (...args: unknown[]) => mockSetSession(...args),
        signOut: (...args: unknown[]) => mockSignOut(...args),
      },
    }),
  },
}));

describe("Supabase-backed auth state", () => {
  beforeEach(() => {
    mockGetSession.mockReset();
    mockSetSession.mockReset();
    mockSignOut.mockReset();
    localStorage.clear();
  });

  it("reads the access token from the Supabase session instead of legacy storage", async () => {
    localStorage.setItem("mp_access_token", "stale-token");
    mockGetSession.mockResolvedValue({
      data: { session: { access_token: "supabase-token" } },
      error: null,
    });

    await expect(getAccessToken()).resolves.toBe("supabase-token");
    await expect(hasSession()).resolves.toBe(true);
  });

  it("removes legacy MarketPulse token copies", () => {
    localStorage.setItem("mp_access_token", "access-token");
    localStorage.setItem("mp_refresh_token", "refresh-token");

    clearLegacySessionStorage();

    expect(localStorage.getItem("mp_access_token")).toBeNull();
    expect(localStorage.getItem("mp_refresh_token")).toBeNull();
  });

  it("keeps Supabase authoritative when applying a backend session", async () => {
    localStorage.setItem("mp_access_token", "legacy-access-token");
    localStorage.setItem("mp_refresh_token", "legacy-refresh-token");
    mockSetSession.mockResolvedValue({
      data: { session: { access_token: "supabase-token" } },
      error: null,
    });

    await applySession({
      access_token: "access-token",
      refresh_token: "refresh-token",
      token_type: "bearer",
      expires_in: 3600,
    });

    expect(mockSetSession).toHaveBeenCalledWith({
      access_token: "access-token",
      refresh_token: "refresh-token",
    });
    expect(localStorage.getItem("mp_access_token")).toBeNull();
    expect(localStorage.getItem("mp_refresh_token")).toBeNull();
  });

  it("clears the Supabase session and legacy token copies on sign-out", async () => {
    localStorage.setItem("mp_access_token", "legacy-access-token");
    localStorage.setItem("mp_refresh_token", "legacy-refresh-token");
    mockSignOut.mockResolvedValue({ error: null });

    await clearSession();

    expect(mockSignOut).toHaveBeenCalledTimes(1);
    expect(localStorage.getItem("mp_access_token")).toBeNull();
    expect(localStorage.getItem("mp_refresh_token")).toBeNull();
  });
});
