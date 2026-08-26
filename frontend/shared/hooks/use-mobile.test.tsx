import { act, renderHook } from "@testing-library/react";

import { useIsMobile } from "@/shared/hooks/use-mobile";

type MatchMediaController = {
  setMatches: (matches: boolean, width: number) => void;
};

function installMatchMedia(initialWidth: number): MatchMediaController {
  let listener: ((event: MediaQueryListEvent) => void) | null = null;

  Object.defineProperty(window, "innerWidth", {
    configurable: true,
    writable: true,
    value: initialWidth,
  });

  Object.defineProperty(window, "matchMedia", {
    configurable: true,
    writable: true,
    value: jest.fn().mockImplementation((query: string) => ({
      matches: initialWidth < 768,
      media: query,
      onchange: null,
      addEventListener: (_event: string, callback: (event: MediaQueryListEvent) => void) => {
        listener = callback;
      },
      removeEventListener: jest.fn(),
      addListener: jest.fn(),
      removeListener: jest.fn(),
      dispatchEvent: jest.fn(),
    })),
  });

  return {
    setMatches(matches: boolean, width: number) {
      window.innerWidth = width;
      listener?.({ matches } as MediaQueryListEvent);
    },
  };
}

describe("useIsMobile", () => {
  it("returns true for widths below the mobile breakpoint", () => {
    installMatchMedia(640);

    const { result } = renderHook(() => useIsMobile());

    expect(result.current).toBe(true);
  });

  it("updates when the media query match state changes", () => {
    const controller = installMatchMedia(1024);

    const { result } = renderHook(() => useIsMobile());
    expect(result.current).toBe(false);

    act(() => {
      controller.setMatches(true, 640);
    });

    expect(result.current).toBe(true);
  });
});
