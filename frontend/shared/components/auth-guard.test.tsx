import { render, screen, waitFor } from "@testing-library/react";

import { AuthGuard } from "@/shared/components/auth-guard";

const mockReplace = jest.fn();
const mockUsePathname = jest.fn();
const mockGetAccessToken = jest.fn();
const mockGetSessionEventName = jest.fn();
const mockOnAuthStateChange = jest.fn();

jest.mock("next/navigation", () => ({
  usePathname: () => mockUsePathname(),
  useRouter: () => ({
    replace: mockReplace,
  }),
}));

jest.mock("@/shared/lib/auth", () => ({
  getAccessToken: () => mockGetAccessToken(),
  getSessionEventName: () => mockGetSessionEventName(),
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

describe("AuthGuard", () => {
  beforeEach(() => {
    mockReplace.mockReset();
    mockUsePathname.mockReset();
    mockGetAccessToken.mockReset();
    mockGetSessionEventName.mockReset();
    mockOnAuthStateChange.mockReset();

    mockUsePathname.mockReturnValue("/alerts");
    mockGetSessionEventName.mockReturnValue("marketpulse:session-changed");
    mockOnAuthStateChange.mockReturnValue({
      data: {
        subscription: {
          unsubscribe: jest.fn(),
        },
      },
    });
  });

  it("renders protected content when an access token is present", async () => {
    mockGetAccessToken.mockReturnValue("token");

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
    mockGetAccessToken.mockReturnValue(null);

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
