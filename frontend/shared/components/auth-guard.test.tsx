import { render, screen, waitFor } from "@testing-library/react";

import { AuthGuard } from "@/shared/components/auth-guard";

const mockReplace = jest.fn();
const mockUsePathname = jest.fn();
const mockUseSupabaseSession = jest.fn();

jest.mock("next/navigation", () => ({
  usePathname: () => mockUsePathname(),
  useRouter: () => ({
    replace: mockReplace,
  }),
}));

jest.mock("@/shared/hooks/use-supabase-session", () => ({
  useSupabaseSession: () => mockUseSupabaseSession(),
}));

describe("AuthGuard", () => {
  beforeEach(() => {
    mockReplace.mockReset();
    mockUsePathname.mockReset();
    mockUseSupabaseSession.mockReset();

    mockUsePathname.mockReturnValue("/alerts");
  });

  it("renders protected content when Supabase has a session", async () => {
    mockUseSupabaseSession.mockReturnValue({
      isAuthenticated: true,
      isLoading: false,
      session: { access_token: "token" },
    });

    render(
      <AuthGuard>
        <div>Protected content</div>
      </AuthGuard>,
    );

    await waitFor(() => {
      expect(screen.getByText("Protected content")).toBeInTheDocument();
    });
    expect(mockReplace).not.toHaveBeenCalled();
  });

  it("redirects unauthenticated users to sign-in with the current path", async () => {
    mockUseSupabaseSession.mockReturnValue({
      isAuthenticated: false,
      isLoading: false,
      session: null,
    });

    render(
      <AuthGuard>
        <div>Protected content</div>
      </AuthGuard>,
    );

    await waitFor(() => {
      expect(mockReplace).toHaveBeenCalledWith("/sign-in?next=%2Falerts");
    });
    expect(screen.getByText("Checking your session")).toBeInTheDocument();
  });
});
